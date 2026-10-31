"""Application configuration loaded from environment variables."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
_FAQ_FILE = Path(os.environ.get("FAQ_FILE", PROJECT_ROOT / "data" / "faqs.json"))
if not _FAQ_FILE.is_absolute():
    _FAQ_FILE = PROJECT_ROOT / _FAQ_FILE


def _read_float(name, default):
    value = os.environ.get(name, str(default))
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a number.") from error


def _read_int(name, default):
    value = os.environ.get(name, str(default))
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer.") from error


class Config:
    """Default settings for the local FAQ chatbot."""

    FAQ_FILE = _FAQ_FILE
    SIMILARITY_THRESHOLD = _read_float("CHATBOT_SIMILARITY_THRESHOLD", 0.30)
    AMBIGUITY_MARGIN = _read_float("CHATBOT_AMBIGUITY_MARGIN", 0.05)
    MAX_MESSAGE_LENGTH = _read_int("CHATBOT_MAX_MESSAGE_LENGTH", 500)
    MAX_CONTENT_LENGTH = _read_int("CHATBOT_MAX_CONTENT_LENGTH", 16 * 1024)
    DEBUG = os.environ.get("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes"}

    @classmethod
    def validate(cls):
        """Fail early with useful messages when settings are invalid."""
        if not 0 <= cls.SIMILARITY_THRESHOLD <= 1:
            raise ValueError("CHATBOT_SIMILARITY_THRESHOLD must be between 0 and 1.")
        if not 0 <= cls.AMBIGUITY_MARGIN <= 1:
            raise ValueError("CHATBOT_AMBIGUITY_MARGIN must be between 0 and 1.")
        if cls.MAX_MESSAGE_LENGTH < 1:
            raise ValueError("CHATBOT_MAX_MESSAGE_LENGTH must be at least 1.")
        if cls.MAX_CONTENT_LENGTH < 1:
            raise ValueError("CHATBOT_MAX_CONTENT_LENGTH must be at least 1.")


Config.validate()