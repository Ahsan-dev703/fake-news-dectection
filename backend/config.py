import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    # Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # Upload settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "backend/uploads")
    MAX_CONTENT_LENGTH = int(
        os.getenv("MAX_CONTENT_LENGTH", 500 * 1024 * 1024)
    )  # 500MB
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv", "flv", "wmv"}
    MAX_IMAGE_SIZE = int(os.getenv("MAX_IMAGE_SIZE", 50 * 1024 * 1024))  # 50MB
    MAX_VIDEO_SIZE = int(os.getenv("MAX_VIDEO_SIZE", 500 * 1024 * 1024))  # 500MB

    # OCR settings
    OCR_ENGINE = os.getenv("OCR_ENGINE", "easyocr")  # easyocr or tesseract
    OCR_LANGUAGES = ["en"]
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE", 0.3))

    # Video processing
    VIDEO_SAMPLE_RATE = int(
        os.getenv("VIDEO_SAMPLE_RATE", 5)
    )  # Extract every Nth frame
    VIDEO_MAX_FRAMES = int(os.getenv("VIDEO_MAX_FRAMES", 30))  # Process max 30 frames
    VIDEO_RESIZE_HEIGHT = int(os.getenv("VIDEO_RESIZE_HEIGHT", 480))

    # Model settings
    MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")
    PREDICTION_CONFIDENCE_THRESHOLD = float(os.getenv("PRED_THRESHOLD", 0.5))

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://yourdomain.com")


def get_config():
    """Get config based on environment"""
    env = os.getenv("FLASK_ENV", "development")
    return ProductionConfig() if env == "production" else DevelopmentConfig()
