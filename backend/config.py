"""
Centralized configuration for StadiumIQ backend.
Contains magic numbers, constants, and thresholds used across the application.
"""

# Gemini Configuration
GEMINI_MODEL = "gemini-1.5-flash-latest"
SYSTEM_PROMPT_MAX_LENGTH = 5000

# Cache Configuration
CACHE_TTL_SECONDS = 300  # 5 minutes

# Rate Limiting
DEFAULT_RATE_LIMIT = "20/minute"

# Application Settings
VERSION = "1.1.0"
MAX_QUERY_LENGTH = 500
