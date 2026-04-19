"""Domain models."""

from __future__ import annotations

from dataclasses import dataclass
import time


@dataclass(frozen=True, slots=True)
class TrackInfo:
    """Normalized currently-playing track metadata."""

    track_id: str
    title: str
    artists: tuple[str, ...]
    cover_url: str | None
    album_id: str | None = None
    duration_ms: int | None = None
    progress_ms: int | None = None
    is_playing: bool = True

    @property
    def artist_line(self) -> str:
        return ", ".join(self.artists)

    @property
    def cache_key(self) -> str:
        return self.album_id or self.track_id

    def remaining_seconds(self) -> float | None:
        if self.duration_ms is None or self.progress_ms is None:
            return None
        return max(self.duration_ms - self.progress_ms, 0) / 1000.0

    def ends_at_timestamp(self, reference_time: float | None = None) -> float | None:
        remaining = self.remaining_seconds()
        if remaining is None:
            return None
        base_time = time.time() if reference_time is None else reference_time
        return base_time + remaining
