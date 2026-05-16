import os
import logging
from werkzeug.utils import secure_filename
from config import Config

logger = logging.getLogger(__name__)


class FileValidator:
    """Validates uploaded files"""

    @staticmethod
    def get_file_extension(filename):
        """Extract file extension"""
        return filename.rsplit(".", 1)[1].lower() if "." in filename else ""

    @staticmethod
    def validate_image(file, filename):
        """
        Validate image file

        Args:
            file: FileStorage object
            filename: Original filename

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check filename
        if not filename:
            return False, "No filename provided"

        filename = secure_filename(filename)
        if not filename:
            return False, "Invalid filename"

        # Check extension
        ext = FileValidator.get_file_extension(filename)
        if ext not in Config.ALLOWED_IMAGE_EXTENSIONS:
            return (
                False,
                f"Image extension must be one of {Config.ALLOWED_IMAGE_EXTENSIONS}",
            )

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > Config.MAX_IMAGE_SIZE:
            return (
                False,
                f"Image size exceeds {Config.MAX_IMAGE_SIZE / (1024*1024):.0f}MB limit",
            )

        if file_size == 0:
            return False, "File is empty"

        return True, None

    @staticmethod
    def validate_video(file, filename):
        """
        Validate video file

        Args:
            file: FileStorage object
            filename: Original filename

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check filename
        if not filename:
            return False, "No filename provided"

        filename = secure_filename(filename)
        if not filename:
            return False, "Invalid filename"

        # Check extension
        ext = FileValidator.get_file_extension(filename)
        if ext not in Config.ALLOWED_VIDEO_EXTENSIONS:
            return (
                False,
                f"Video extension must be one of {Config.ALLOWED_VIDEO_EXTENSIONS}",
            )

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > Config.MAX_VIDEO_SIZE:
            return (
                False,
                f"Video size exceeds {Config.MAX_VIDEO_SIZE / (1024*1024):.0f}MB limit",
            )

        if file_size == 0:
            return False, "File is empty"

        return True, None

    @staticmethod
    def save_file(file, upload_folder, new_filename):
        """
        Save file to upload folder

        Args:
            file: FileStorage object
            upload_folder: Destination folder
            new_filename: New filename

        Returns:
            str: Path to saved file
        """
        try:
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, new_filename)
            file.save(filepath)
            logger.info(f"File saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise


class TextPreprocessor:
    """Preprocess extracted text"""

    @staticmethod
    def clean_ocr_text(text):
        """
        Clean and preprocess OCR-extracted text

        Args:
            text: Raw OCR text

        Returns:
            str: Cleaned text
        """
        if not text:
            return ""

        # Remove extra whitespace
        text = " ".join(text.split())

        # Basic cleaning
        text = text.strip()

        return text

    @staticmethod
    def aggregate_text(text_list):
        """
        Aggregate multiple text chunks

        Args:
            text_list: List of text strings

        Returns:
            str: Combined text
        """
        # Filter empty strings
        text_list = [t.strip() for t in text_list if t.strip()]

        # Join with space
        return " ".join(text_list)


class ErrorHandler:
    """Centralized error handling"""

    @staticmethod
    def format_error_response(error_code, error_message, details=None):
        """Format error response"""
        response = {"success": False, "error": error_message, "error_code": error_code}
        if details:
            response["details"] = details
        return response

    @staticmethod
    def format_success_response(data, message="Success"):
        """Format success response"""
        return {"success": True, "message": message, "data": data}


# Error codes
class ErrorCodes:
    INVALID_FILE = "INVALID_FILE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    OCR_FAILED = "OCR_FAILED"
    VIDEO_PROCESSING_FAILED = "VIDEO_PROCESSING_FAILED"
    PREDICTION_FAILED = "PREDICTION_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"
