import logging
import re
import os
import tempfile
from typing import Dict, Optional

logger = logging.getLogger(__name__)

try:
    import yt_dlp
except Exception:
    yt_dlp = None

try:
    import requests
except Exception:
    requests = None

# Optional env vars to help yt-dlp authenticate for age-restricted / gated videos
YTDLP_COOKIES_FROM_BROWSER = os.getenv("YTDLP_COOKIES_FROM_BROWSER")
YTDLP_COOKIEFILE = os.getenv("YTDLP_COOKIEFILE")


def _ensure_requests_available() -> None:
    if requests is None:
        raise ValueError("requests is required. Install with `pip install requests`")


YOUTUBE_URL_RE = re.compile(r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/")


def validate_youtube_url(url: str) -> bool:
    return bool(YOUTUBE_URL_RE.match(url))


def probe_metadata(url: str, cookiefile: Optional[str] = None) -> Dict:
    """Return metadata dict using yt-dlp extract_info (no download).

    Raises ValueError if yt_dlp is not available or extraction fails.
    """
    if yt_dlp is None:
        raise ValueError("yt-dlp is required. Install with `pip install yt-dlp`")

    ydl_opts = {"quiet": True, "nocheckcertificate": True}
    # cookiefile arg overrides env vars if provided
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
    elif YTDLP_COOKIEFILE:
        ydl_opts["cookiefile"] = YTDLP_COOKIEFILE
    elif YTDLP_COOKIES_FROM_BROWSER:
        ydl_opts["cookiesfrombrowser"] = YTDLP_COOKIES_FROM_BROWSER

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        msg = str(e)
        if "Sign in to confirm you're not a bot" in msg or "Sign in to confirm" in msg:
            raise ValueError(
                "yt-dlp requires authentication for this video. Export YouTube cookies and set YTDLP_COOKIEFILE or set YTDLP_COOKIES_FROM_BROWSER (e.g. 'chrome'). See https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp"
            )
        raise
    return info


def fetch_captions_text(info: Dict) -> Optional[str]:
    """Fetch available subtitles (prefer human subtitles) and return plain text.

    Returns None if no captions found.
    """
    # subtitles dict example: info.get('subtitles', {lang: [{ 'ext': 'vtt', 'url': '...' }]})
    subs = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}

    source = None
    if subs:
        source = subs
    elif auto:
        source = auto

    if not source:
        return None

    # choose first language available and prefer vtt or srt
    for lang, formats in source.items():
        if not formats:
            continue
        # prefer vtt then srt then any
        chosen = None
        for f in formats:
            if f.get("ext") == "vtt":
                chosen = f
                break
        if chosen is None:
            for f in formats:
                if f.get("ext") == "srt":
                    chosen = f
                    break
        if chosen is None:
            chosen = formats[0]

        url = chosen.get("url")
        if not url:
            continue

        try:
            _ensure_requests_available()
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                continue
            text = resp.text
            # remove VTT cues or SRT timestamps
            lines = []
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                # skip timestamp lines
                if re.match(r"^[0-9]{1,2}:", line) or re.match(r"^[0-9]+\s+-->", line):
                    continue
                # skip WEBVTT header
                if line.lower().startswith("webvtt"):
                    continue
                if re.match(r"^\d+$", line):
                    continue
                lines.append(line)

            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Failed to fetch captions URL: {e}")
            continue

    return None


def download_video(
    url: str, out_dir: Optional[str] = None, cookiefile: Optional[str] = None
) -> str:
    """Download video to a temporary file and return local path.

    Uses yt-dlp to fetch best video+audio muxed when possible.
    Prefer download_audio for transcription tasks.
    """
    if yt_dlp is None:
        raise ValueError("yt-dlp is required. Install with `pip install yt-dlp`")

    if out_dir is None:
        out_dir = tempfile.mkdtemp(prefix="ytdl_")
    os.makedirs(out_dir, exist_ok=True)

    outtmpl = os.path.join(out_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestvideo[ext=mp4]+bestaudio/best",
        "quiet": True,
        "merge_output_format": "mp4",
    }
    # cookiefile arg overrides env vars if provided
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
    elif YTDLP_COOKIEFILE:
        ydl_opts["cookiefile"] = YTDLP_COOKIEFILE
    elif YTDLP_COOKIES_FROM_BROWSER:
        ydl_opts["cookiesfrombrowser"] = YTDLP_COOKIES_FROM_BROWSER

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if not os.path.exists(filename):
            alt = os.path.splitext(filename)[0] + ".mp4"
            if os.path.exists(alt):
                filename = alt

    return filename


def download_audio(
    url: str,
    out_dir: Optional[str] = None,
    max_duration: int = 600,
    cookiefile: Optional[str] = None,
) -> str:
    """Download audio only (m4a/mp3/wav) for transcription. Enforces max duration in seconds."""
    if yt_dlp is None:
        raise ValueError("yt-dlp is required. Install with `pip install yt-dlp`")

    if out_dir is None:
        out_dir = tempfile.mkdtemp(prefix="ytdl_audio_")
    os.makedirs(out_dir, exist_ok=True)

    outtmpl = os.path.join(out_dir, "%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "quiet": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "noplaylist": True,
        "max_downloads": 1,
        "match_filter": (
            lambda info, *, max_duration=max_duration: (
                None
                if info.get("duration", 0) <= max_duration
                else f"Reject: duration {info.get('duration', 0)} > {max_duration}s"
            )
        ),
    }

    # cookiefile arg overrides env vars if provided
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
    elif YTDLP_COOKIEFILE:
        ydl_opts["cookiefile"] = YTDLP_COOKIEFILE
    elif YTDLP_COOKIES_FROM_BROWSER:
        ydl_opts["cookiesfrombrowser"] = YTDLP_COOKIES_FROM_BROWSER

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        duration = info.get("duration", 0)
        if duration > max_duration:
            raise ValueError(f"Video too long: {duration}s > {max_duration}s allowed")
        filename = ydl.prepare_filename(info)
        filename = os.path.splitext(filename)[0] + ".wav"
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Audio file not found after download: {filename}")
    return filename
