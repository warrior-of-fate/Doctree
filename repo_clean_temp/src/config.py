"""Global configuration and constants for pdf-topic-scanner."""

# Heading score thresholds for classification (IMPROVED - lowered for better detection)
HEADING_SCORE_THRESHOLDS = {
    "H1": 0.75,   # Slightly lowered from 0.8
    "H2": 0.50,   # Significantly lowered from 0.6 (was missing H2s)
    "H3": 0.35,   # Slightly lowered from 0.4
    "BODY": 0.0
}

# PDF parsing defaults
Y_TOLERANCE = 5  # units for grouping words into lines
PAGE_WIDTH = 612  # standard US Letter width in points

# Feature engineering parameters
MIN_HEADING_LENGTH = 3  # Minimum characters for heading
MAX_HEADING_WORDS = 15  # Maximum words for heading (increased from 10)
AVG_BODY_WORD_COUNT = 12  # Expected avg words per body line
