"""Configuration loading and environment helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import os

from .errors import ConfigurationError


def load_environment_file(path: str | Path = ".env") -> None:
    """Load simple KEY=VALUE pairs from an env file if it exists."""

    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError(f"Environment variable {name} must be an integer.") from exc
    if parsed < minimum:
        raise ConfigurationError(f"Environment variable {name} must be >= {minimum}.")
    return parsed


def _env_float(name: str, default: float, minimum: float = 0.0) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ConfigurationError(f"Environment variable {name} must be a number.") from exc
    if parsed <= minimum:
        raise ConfigurationError(f"Environment variable {name} must be > {minimum}.")
    return parsed


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class SpotifyConfig:
    """Spotify API configuration."""

    client_id: str | None
    client_secret: str | None
    redirect_uri: str
    cache_path: str
    market: str
    scope: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "SpotifyConfig":
        scope = os.getenv(
            "SPOTIPY_SCOPE",
            "user-read-currently-playing user-read-playback-state",
        ).split()
        return cls(
            client_id=os.getenv("SPOTIPY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
            redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:9090"),
            cache_path=os.getenv("SPOTIPY_CACHE_PATH", ".cache"),
            market=os.getenv("SPOTIPY_MARKET", "DE"),
            scope=tuple(scope),
        )

    def validate(self) -> None:
        if not self.client_id or not self.client_secret:
            raise ConfigurationError(
                "SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET must be configured."
            )


@dataclass(frozen=True, slots=True)
class MatrixConfig:
    """RGB matrix hardware and output configuration."""

    display_width: int = 64
    display_height: int = 64
    rows: int = 64
    cols: int = 64
    chain_length: int = 1
    parallel: int = 1
    brightness: int = 60
    hardware_mapping: str = "regular"
    gpio_slowdown: int = 2
    pwm_bits: int = 11
    disable_hardware_pulsing: bool = True

    @classmethod
    def from_env(cls) -> "MatrixConfig":
        default_display_width = 64
        default_display_height = 64
        default_rows = 64
        default_cols = 64
        default_chain_length = 1
        default_parallel = 1
        default_brightness = 60
        default_hardware_mapping = "regular"
        default_gpio_slowdown = 2
        default_pwm_bits = 11
        default_disable_hardware_pulsing = True

        brightness = _env_int("MATRIX_BRIGHTNESS", default_brightness, minimum=1)
        return cls(
            display_width=_env_int("MATRIX_DISPLAY_WIDTH", default_display_width),
            display_height=_env_int("MATRIX_DISPLAY_HEIGHT", default_display_height),
            rows=_env_int("MATRIX_ROWS", default_rows),
            cols=_env_int("MATRIX_COLS", default_cols),
            chain_length=_env_int("MATRIX_CHAIN_LENGTH", default_chain_length),
            parallel=_env_int("MATRIX_PARALLEL", default_parallel),
            brightness=min(brightness, 100),
            hardware_mapping=os.getenv("MATRIX_HARDWARE_MAPPING", default_hardware_mapping),
            gpio_slowdown=_env_int("MATRIX_GPIO_SLOWDOWN", default_gpio_slowdown, minimum=0),
            pwm_bits=_env_int("MATRIX_PWM_BITS", default_pwm_bits),
            disable_hardware_pulsing=_env_bool(
                "MATRIX_DISABLE_HARDWARE_PULSING",
                default_disable_hardware_pulsing,
            ),
        )

    @property
    def display_size(self) -> tuple[int, int]:
        return self.display_width, self.display_height


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Top-level application configuration."""

    spotify: SpotifyConfig
    matrix: MatrixConfig
    album_cache_dir: Path = Path(".album-cache")
    poll_interval_seconds: float = 5.0
    restart_delay_seconds: float = 1.0
    max_restart_delay_seconds: float = 30.0
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            spotify=SpotifyConfig.from_env(),
            matrix=MatrixConfig.from_env(),
            album_cache_dir=Path(os.getenv("ALBUM_CACHE_DIR", ".album-cache")),
            poll_interval_seconds=_env_float("POLL_INTERVAL_SECONDS", 5.0, minimum=0.0),
            restart_delay_seconds=_env_float("RESTART_DELAY_SECONDS", 1.0, minimum=0.0),
            max_restart_delay_seconds=_env_float(
                "MAX_RESTART_DELAY_SECONDS",
                30.0,
                minimum=0.0,
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

    def with_updates(
        self,
        *,
        poll_interval_seconds: float | None = None,
        restart_delay_seconds: float | None = None,
        max_restart_delay_seconds: float | None = None,
        album_cache_dir: Path | None = None,
        log_level: str | None = None,
        matrix: MatrixConfig | None = None,
        spotify: SpotifyConfig | None = None,
    ) -> "AppConfig":
        return replace(
            self,
            poll_interval_seconds=self.poll_interval_seconds if poll_interval_seconds is None else poll_interval_seconds,
            restart_delay_seconds=self.restart_delay_seconds if restart_delay_seconds is None else restart_delay_seconds,
            max_restart_delay_seconds=(
                self.max_restart_delay_seconds
                if max_restart_delay_seconds is None
                else max_restart_delay_seconds
            ),
            album_cache_dir=self.album_cache_dir if album_cache_dir is None else album_cache_dir,
            log_level=self.log_level if log_level is None else log_level,
            matrix=self.matrix if matrix is None else matrix,
            spotify=self.spotify if spotify is None else spotify,
        )
