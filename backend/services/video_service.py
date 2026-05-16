import logging
import cv2
from typing import Dict, List, Tuple
import os
import numpy as np

logger = logging.getLogger(__name__)


class VideoService:
    """
    Video processing service
    Extracts frames and text from video files
    """

    @staticmethod
    def get_video_info(video_path: str) -> Dict:
        """
        Get video metadata (duration, fps, resolution, etc.)

        Args:
            video_path: Path to video file

        Returns:
            Dict with video information
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                return {"success": False, "error": "Could not open video"}

            # Get video properties
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration_seconds = frame_count / fps if fps > 0 else 0

            cap.release()

            logger.info(
                f"Video info: {frame_count} frames, {fps} FPS, {width}x{height}, {duration_seconds:.1f}s"
            )

            return {
                "success": True,
                "frame_count": frame_count,
                "fps": fps,
                "width": width,
                "height": height,
                "duration_seconds": duration_seconds,
                "duration_readable": f"{int(duration_seconds // 60)}m {int(duration_seconds % 60)}s",
            }

        except Exception as e:
            logger.error(f"Failed to get video info: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def extract_frames(
        video_path: str,
        sample_rate: int = 5,
        max_frames: int = 30,
        target_height: int = 480,
    ) -> Tuple[bool, List[str], Dict]:
        """
        Extract frames from video at regular intervals

        Args:
            video_path: Path to video file
            sample_rate: Extract every Nth frame (e.g., 5 = every 5th frame)
            max_frames: Maximum number of frames to extract
            target_height: Resize frames to this height

        Returns:
            Tuple: (success, frame_paths, metadata)
        """
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                return False, [], {"error": "Could not open video"}

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # Create temp frames directory
            frames_dir = os.path.join(os.path.dirname(video_path), "temp_frames")
            os.makedirs(frames_dir, exist_ok=True)

            frame_paths = []
            frame_count = 0
            extracted_count = 0

            logger.info(
                f"Extracting frames from {video_path} (sample_rate={sample_rate}, max={max_frames})"
            )

            while True:
                ret, frame = cap.read()

                if not ret:
                    break

                # Extract every Nth frame
                if frame_count % sample_rate == 0 and extracted_count < max_frames:
                    try:
                        # Resize frame
                        h, w = frame.shape[:2]
                        ratio = target_height / h
                        new_w = int(w * ratio)
                        resized_frame = cv2.resize(frame, (new_w, target_height))

                        # Save frame
                        frame_path = os.path.join(
                            frames_dir, f"frame_{extracted_count:04d}.jpg"
                        )
                        cv2.imwrite(
                            frame_path, resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
                        )
                        frame_paths.append(frame_path)
                        extracted_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to save frame {frame_count}: {str(e)}")
                        continue

                frame_count += 1

            cap.release()

            metadata = {
                "total_frames": total_frames,
                "extracted_frames": extracted_count,
                "fps": fps,
                "sample_rate": sample_rate,
                "frames_dir": frames_dir,
            }

            logger.info(f"Extracted {extracted_count} frames from video")

            return True, frame_paths, metadata

        except Exception as e:
            logger.error(f"Frame extraction failed: {str(e)}")
            return False, [], {"error": str(e)}

    @staticmethod
    def cleanup_frames(frames_dir: str) -> bool:
        """
        Delete temporary frame directory

        Args:
            frames_dir: Directory containing frames

        Returns:
            bool: Success status
        """
        try:
            import shutil

            if os.path.exists(frames_dir):
                shutil.rmtree(frames_dir)
                logger.info(f"Cleaned up frames directory: {frames_dir}")
                return True
            return True
        except Exception as e:
            logger.warning(f"Failed to cleanup frames: {str(e)}")
            return False

    @staticmethod
    def detect_scene_changes(
        frame_paths: List[str], threshold: float = 0.5
    ) -> List[int]:
        """
        Detect significant scene changes in frames
        Returns indices of frames with scene changes

        Args:
            frame_paths: List of frame file paths
            threshold: Change detection threshold (0-1)

        Returns:
            List of frame indices with scene changes
        """
        try:
            if len(frame_paths) < 2:
                return []

            scene_change_indices = [0]  # First frame always included

            prev_frame = cv2.imread(frame_paths[0])
            prev_hist = cv2.calcHist(
                [prev_frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
            )
            prev_hist = cv2.normalize(prev_hist, prev_hist).flatten()

            for idx in range(1, len(frame_paths)):
                frame = cv2.imread(frame_paths[idx])
                hist = cv2.calcHist(
                    [frame], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
                )
                hist = cv2.normalize(hist, hist).flatten()

                # Compute histogram similarity
                similarity = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)

                if similarity > threshold:
                    scene_change_indices.append(idx)

                prev_hist = hist

            logger.info(f"Detected {len(scene_change_indices)} scene changes")
            return scene_change_indices

        except Exception as e:
            logger.error(f"Scene change detection failed: {str(e)}")
            return []
