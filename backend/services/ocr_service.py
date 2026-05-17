import logging
from typing import Dict, List, Tuple
import easyocr
from PIL import Image
import io
import hashlib
import json
import os

logger = logging.getLogger(__name__)


class OCRService:
    """
    Optical Character Recognition service
    Extracts text from images with a small cache and GPU autodetection
    """

    _reader = None  # Singleton reader instance
    _cache = {}  # in-memory cache: image_hash -> result
    _cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "ocr_cache")

    @classmethod
    def initialize(cls, languages=None):
        """
        Initialize OCR reader (called once on startup)

        Args:
            languages: List of language codes (e.g., ['en', 'es'])
        """
        if cls._reader is None:
            try:
                if languages is None:
                    languages = ["en"]

                # autodetect GPU availability for easyocr
                gpu = False
                try:
                    import torch

                    gpu = torch.cuda.is_available()
                except Exception:
                    gpu = False

                logger.info(
                    f"Initializing EasyOCR reader for languages: {languages} (gpu={gpu})"
                )

                cls._reader = easyocr.Reader(languages, gpu=gpu)
                # Ensure cache dir exists
                os.makedirs(cls._cache_dir, exist_ok=True)
                logger.info("OCR reader initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OCR reader: {str(e)}")
                raise

    @staticmethod
    def _hash_bytes(b: bytes) -> str:
        return hashlib.sha256(b).hexdigest()

    @classmethod
    def _load_from_disk_cache(cls, h: str):
        path = os.path.join(cls._cache_dir, f"{h}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    @classmethod
    def _save_to_disk_cache(cls, h: str, data: Dict):
        path = os.path.join(cls._cache_dir, f"{h}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    @classmethod
    def extract_text(cls, image_path: str, confidence_threshold: float = 0.3) -> Dict:
        """
        Extract text from image file. Uses an internal cache keyed by image bytes hash.
        """
        if cls._reader is None:
            cls.initialize()

        try:
            with open(image_path, "rb") as f:
                b = f.read()

            h = cls._hash_bytes(b)

            # check in-memory cache
            if h in cls._cache:
                return cls._cache[h]

            # check disk cache
            disk = cls._load_from_disk_cache(h)
            if disk:
                cls._cache[h] = disk
                return disk

            logger.info(f"Extracting text from image: {image_path}")

            # Convert to PIL Image and use readtext on image object for consistent behavior
            image = Image.open(io.BytesIO(b))
            results = cls._reader.readtext(image)

            if not results:
                res = {
                    "success": True,
                    "text": "",
                    "confidence": 0.0,
                    "text_count": 0,
                    "raw_results": [],
                }
                cls._cache[h] = res
                cls._save_to_disk_cache(h, res)
                return res

            filtered_results = [r for r in results if r[2] >= confidence_threshold]
            extracted_text = "\n".join([r[1] for r in filtered_results])

            avg_confidence = (
                sum([r[2] for r in filtered_results]) / len(filtered_results)
                if filtered_results
                else 0
            )

            res = {
                "success": True,
                "text": extracted_text,
                "confidence": avg_confidence,
                "text_count": len(filtered_results),
                "raw_results": [
                    {"text": r[1], "confidence": r[2], "bbox": r[0]}
                    for r in filtered_results
                ],
            }

            cls._cache[h] = res
            cls._save_to_disk_cache(h, res)
            logger.info(f"Extracted {len(filtered_results)} text regions from image")
            return res

        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return {"success": False, "error": str(e), "text": "", "confidence": 0.0}

    @classmethod
    def extract_text_from_bytes(
        cls, image_bytes: bytes, confidence_threshold: float = 0.3
    ) -> Dict:
        if cls._reader is None:
            cls.initialize()

        try:
            h = cls._hash_bytes(image_bytes)

            if h in cls._cache:
                return cls._cache[h]

            disk = cls._load_from_disk_cache(h)
            if disk:
                cls._cache[h] = disk
                return disk

            image = Image.open(io.BytesIO(image_bytes))
            logger.info(
                f"Extracting text from image bytes (size: {len(image_bytes)} bytes)"
            )

            results = cls._reader.readtext(image)

            if not results:
                res = {"success": True, "text": "", "confidence": 0.0, "text_count": 0}
                cls._cache[h] = res
                cls._save_to_disk_cache(h, res)
                return res

            filtered_results = [r for r in results if r[2] >= confidence_threshold]
            extracted_text = "\n".join([r[1] for r in filtered_results])

            avg_confidence = (
                sum([r[2] for r in filtered_results]) / len(filtered_results)
                if filtered_results
                else 0
            )

            res = {
                "success": True,
                "text": extracted_text,
                "confidence": avg_confidence,
                "text_count": len(filtered_results),
            }

            cls._cache[h] = res
            cls._save_to_disk_cache(h, res)
            logger.info(f"Extracted {len(filtered_results)} text regions")
            return res

        except Exception as e:
            logger.error(f"OCR extraction from bytes failed: {str(e)}")
            return {"success": False, "error": str(e), "text": "", "confidence": 0.0}
