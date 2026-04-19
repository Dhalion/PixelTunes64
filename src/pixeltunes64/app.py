"""Application orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from threading import Event
from collections.abc import Callable

from .config import AppConfig
from .errors import CoverArtError, MatrixDisplayError, SpotifyServiceError
from .image_pipeline import CoverArtProcessor
from .matrix import MatrixDisplay, RGBMatrixDisplay
from .models import TrackInfo
from .spotify import SpotifyService


@dataclass(slots=True)
class PlaybackState:
    """Compact state used to avoid unnecessary redraws."""

    mode: str
    track_id: str | None


@dataclass(slots=True)
class RuntimeComponents:
    """Per-session components that can be rebuilt after failures."""

    spotify: SpotifyService
    display: MatrixDisplay


class PixelTunes64App:
    """Coordinate Spotify polling, cover-art rendering, and matrix output."""

    def __init__(
        self,
        config: AppConfig | None = None,
        spotify_service: SpotifyService | None = None,
        cover_art_processor: CoverArtProcessor | None = None,
        display: MatrixDisplay | None = None,
        logger: logging.Logger | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self._config = config or AppConfig.from_env()
        self._logger = logger or logging.getLogger(__name__)
        self._cover_art = cover_art_processor or CoverArtProcessor(
            cache_dir=self._config.album_cache_dir,
            logger=self._logger,
        )
        self._sleep_fn = sleep_fn or time.sleep
        self._runtime: RuntimeComponents | None = None
        self._last_state: PlaybackState | None = None
        self._spotify_service = spotify_service
        self._display = display

    def poll_once(self) -> float:
        """Fetch playback state once and update the display when needed."""

        runtime = self._ensure_runtime()
        display_size = self._config.matrix.display_size

        try:
            track = runtime.spotify.current_track()
        except SpotifyServiceError as exc:
            error_state = PlaybackState(mode="error", track_id=None)
            if error_state != self._last_state:
                self._show_frame(runtime, self._cover_art.render_error(str(exc), display_size))
                self._last_state = error_state
            return self._config.poll_interval_seconds

        state = self._state_for(track)
        if state != self._last_state:
            frame = self._render_frame(track, display_size)
            self._show_frame(runtime, frame)
            if track is None:
                self._logger.info("Spotify playback idle.")
            else:
                self._logger.info("Now playing: %s - %s", track.artist_line, track.title)
            self._last_state = state

        return self._poll_delay(track)

    def run(self, stop_event: Event | None = None) -> None:
        """Run forever and rebuild runtime components after critical failures."""

        restart_delay = self._config.restart_delay_seconds
        while not self._should_stop(stop_event):
            try:
                self._runtime = self._build_runtime()
                self._last_state = None
                self._run_session(stop_event)
                return
            except KeyboardInterrupt:
                raise
            except Exception:
                self._logger.exception(
                    "Critical error in runtime; restarting in %.1f seconds.",
                    restart_delay,
                )
                if self._should_stop(stop_event):
                    return
                self._sleep(restart_delay, stop_event)
                restart_delay = min(
                    max(restart_delay * 2, self._config.restart_delay_seconds),
                    self._config.max_restart_delay_seconds,
                )
            finally:
                self._close_runtime()

    def close(self) -> None:
        self._close_runtime()

    def _build_runtime(self) -> RuntimeComponents:
        spotify = self._spotify_service or SpotifyService(self._config.spotify, logger=self._logger)
        display = self._display or RGBMatrixDisplay(self._config.matrix)
        return RuntimeComponents(spotify=spotify, display=display)

    def _ensure_runtime(self) -> RuntimeComponents:
        if self._runtime is None:
            self._runtime = self._build_runtime()
        return self._runtime

    def _close_runtime(self) -> None:
        if self._runtime is None:
            return
        try:
            self._runtime.display.close()
        except Exception:
            self._logger.exception("Failed to close the RGB matrix cleanly.")
        finally:
            self._runtime = None

    def _run_session(self, stop_event: Event | None) -> None:
        while not self._should_stop(stop_event):
            delay = self.poll_once()
            self._sleep(delay, stop_event)

    def _render_frame(self, track: TrackInfo | None, display_size: tuple[int, int]):
        if track is None:
            return self._cover_art.render_idle(display_size)
        try:
            return self._cover_art.render_track(track, display_size)
        except CoverArtError as exc:
            self._logger.warning("Cover art could not be prepared: %s", exc)
            return self._cover_art.render_error(str(exc), display_size)

    def _show_frame(self, runtime: RuntimeComponents, frame: object) -> None:
        try:
            runtime.display.show(frame)
        except Exception as exc:
            raise MatrixDisplayError("RGB matrix update failed.") from exc

    def _poll_delay(self, track: TrackInfo | None) -> float:
        if track is None:
            return self._config.poll_interval_seconds
        remaining = track.remaining_seconds()
        if remaining is None:
            return self._config.poll_interval_seconds
        return max(0.1, min(self._config.poll_interval_seconds, remaining))

    @staticmethod
    def _state_for(track: TrackInfo | None) -> PlaybackState:
        if track is None:
            return PlaybackState(mode="idle", track_id=None)
        return PlaybackState(mode="track", track_id=track.track_id)

    def _sleep(self, seconds: float, stop_event: Event | None = None) -> None:
        if stop_event is None:
            self._sleep_fn(seconds)
        else:
            stop_event.wait(seconds)

    @staticmethod
    def _should_stop(stop_event: Event | None) -> bool:
        return stop_event is not None and stop_event.is_set()
