"""Provider clients for media databases."""

from .base import (
    APIError,
    AuthenticationError,
    BaseProviderClient,
    ProviderError,
    RateLimiter,
    RateLimitError,
)
from .fuzzy import (
    FilenameParser,
    FuzzyMatcher,
    MediaSearcher,
    ParsedFilename,
)
from .thetvdb import TheTVDBClient
from .tmdb import TMDBClient

__all__ = [
    "BaseProviderClient",
    "ProviderError",
    "APIError",
    "RateLimitError",
    "AuthenticationError",
    "RateLimiter",
    "TMDBClient",
    "TheTVDBClient",
    "FuzzyMatcher",
    "FilenameParser",
    "MediaSearcher",
    "ParsedFilename",
]
