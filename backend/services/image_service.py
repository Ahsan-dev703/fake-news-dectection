import logging
from typing import Dict, Tuple
import cv2
from PIL import Image
import numpy as np
import io

logger = logging.getLogger(__name__)


class ImageService:
    """
    Image processing service
    Handles image validation, resizing, and analysis
    """

    @staticmethod
    def get_image_info(image_path: str) -> Dict:
        """
        Get image metadata (dimensions, format, etc.)

        Args:
            image_path: Path to image file

        Returns:
            Dict with image information
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                return {
                    "success": True,
                    "width": width,
                    "height": height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": None,
                }
        except Exception as e:
            logger.error(f"Failed to get image info: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def resize_image(image_path: str, max_height: int = 1080) -> Tuple[bool, str]:
        """
        Resize image to max height while maintaining aspect ratio
        (Useful for OCR optimization - larger text is easier to read)

        Args:
            image_path: Path to image file
            max_height: Maximum height in pixels

        Returns:
            Tuple: (success, message)
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size

                if height <= max_height:
                    logger.info(
                        f"Image already smaller than {max_height}px, skipping resize"
                    )
                    return True, "Image size OK"

                # Calculate new dimensions
                ratio = max_height / height
                new_width = int(width * ratio)

                # Resize using high-quality filter
                resized_img = img.resize(
                    (new_width, max_height), Image.Resampling.LANCZOS
                )

                # Save back
                resized_img.save(image_path, quality=95, optimize=True)

                logger.info(f"Image resized to {new_width}x{max_height}")
                return True, f"Resized to {new_width}x{max_height}"

        except Exception as e:
            logger.error(f"Image resize failed: {str(e)}")
            return False, str(e)

    @staticmethod
    def optimize_for_ocr(image_path: str) -> Tuple[bool, str]:
        """
        Optimize image for OCR (improve contrast, denoise)

        Args:
            image_path: Path to image file

        Returns:
            Tuple: (success, message)
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return False, "Could not read image"

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply denoising (bilateral filter preserves edges)
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)

            # Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)

            # Threshold to binary (helps with text extraction)
            _, binary = cv2.threshold(
                enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )

            # Convert back to BGR for saving
            result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

            # Save optimized image
            cv2.imwrite(image_path, result)

            logger.info(f"Image optimized for OCR")
            return True, "Image optimized"

        except Exception as e:
            logger.error(f"OCR optimization failed: {str(e)}")
            return False, str(e)

    @staticmethod
    def detect_image_manipulation(image_path: str) -> Dict:
        """
        Simple image manipulation detection using frequency analysis
        (Deepfakes often have different frequency signatures)

        Args:
            image_path: Path to image

        Returns:
            Dict with manipulation score (0-1, higher = more likely manipulated)
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return {"success": False, "error": "Could not read image"}

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Compute Laplacian variance (blurry images = lower variance)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = laplacian.var()

            # Compute color consistency
            b, g, r = cv2.split(img)
            color_consistency = (
                1
                - np.abs(
                    (np.mean(b) - np.mean(g))
                    + (np.mean(g) - np.mean(r))
                    + (np.mean(r) - np.mean(b))
                )
                / 765.0
            )

            # Simple heuristic: combination of factors
            blur_score = min(1.0, 1.0 - (variance / 1000.0))
            manipulation_score = blur_score * 0.6 + (1 - color_consistency) * 0.4

            return {
                "success": True,
                "manipulation_score": min(1.0, max(0.0, manipulation_score)),
                "blur_variance": variance,
                "color_consistency": color_consistency,
                "interpretation": (
                    "Likely deepfake" if manipulation_score > 0.7 else "Appears genuine"
                ),
            }

        except Exception as e:
            logger.error(f"Image manipulation detection failed: {str(e)}")
            return {"success": False, "error": str(e)}
