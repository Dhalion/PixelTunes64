"""Project-specific exceptions."""


class PixelTunesError(RuntimeError):
    """Base class for application errors."""


class ConfigurationError(PixelTunesError):
    """Raised when required configuration is missing or invalid."""


class SpotifyServiceError(PixelTunesError):
    """Raised when Spotify playback information cannot be read."""


class CoverArtError(PixelTunesError):
    """Raised when cover art cannot be downloaded or processed."""


class MatrixDisplayError(PixelTunesError):
    """Raised when the RGB matrix backend cannot be created or updated."""
