"""Language detection for documents."""

import structlog
from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

logger = structlog.get_logger()

# Make langdetect deterministic
DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    """Detect the language of a text string.

    Args:
        text: Text to analyze.

    Returns:
        ISO 639-1 language code (e.g. "en", "it", "ru").
        Returns "en" as fallback if detection fails.
    """
    sample = text[:5000]

    try:
        language_code = detect(sample)
    except LangDetectException:
        logger.warning("language_detection_failed", fallback="en")
        return "en"

    logger.debug("language_detected", language=language_code)
    return language_code
