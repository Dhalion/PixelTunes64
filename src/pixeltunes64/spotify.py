"""Spotify API access."""

from __future__ import annotations

import os
import logging
from typing import Any

from .config import SpotifyConfig
from .errors import ConfigurationError, SpotifyServiceError
from .models import TrackInfo

os.environ.setdefault("SPOTIPY_ALLOW_INSECURE_TRANSPORT", "1")

try:
    import spotipy as _spotipy
    from spotipy.exceptions import SpotifyException as _SpotifyException
    from spotipy.oauth2 import SpotifyOAuth as _SpotifyOAuth
except ImportError:  # pragma: no cover - optional runtime dependency
    _spotipy = None

    class _SpotifyException(Exception):
        """Placeholder exception when spotipy is not installed."""

    _SpotifyOAuth = None

class SpotifyService:
    """Read the currently playing song from Spotify."""

    def __init__(self, config: SpotifyConfig, logger: logging.Logger | None = None) -> None:
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._client = self._create_client()

    def _create_client(self):
        if _spotipy is None or _SpotifyOAuth is None:
            raise ConfigurationError(
                "spotipy is required at runtime. Install dependencies before starting the app."
            )
        self._config.validate()
        try:
            auth_manager = _SpotifyOAuth(
                client_id=self._config.client_id,
                client_secret=self._config.client_secret,
                redirect_uri=self._config.redirect_uri,
                scope=" ".join(self._config.scope),
                cache_path=self._config.cache_path,
            )
            client = _spotipy.Spotify(auth_manager=auth_manager)
            user = client.current_user()
            self._logger.info(
                "Spotify authenticated%s",
                f" for {user.get('display_name') or user.get('id')}" if user else "",
            )
            return client
        except _SpotifyException as exc:
            raise SpotifyServiceError("Spotify authentication failed.") from exc

    def current_track(self) -> TrackInfo | None:
        try:
            playback = self._client.current_playback(market=self._config.market)
        except _SpotifyException as exc:
            raise SpotifyServiceError("Spotify playback lookup failed.") from exc

        if not playback or not playback.get("is_playing"):
            return None

        item = playback.get("item")
        if not item:
            return None

        artists = tuple(
            artist["name"]
            for artist in item.get("artists", [])
            if artist.get("name")
        )
        track = TrackInfo(
            track_id=item["id"],
            album_id=self._extract_album_id(item.get("album")),
            title=item.get("name", "Unknown track"),
            artists=artists,
            cover_url=self._extract_cover_url(item.get("album")),
            duration_ms=item.get("duration_ms"),
            progress_ms=playback.get("progress_ms"),
            is_playing=True,
        )
        self._logger.debug(
            "Spotify playback: %s - %s%s",
            track.artist_line,
            track.title,
            f" [album={track.album_id}]" if track.album_id else "",
        )
        return track

    @staticmethod
    def _extract_cover_url(album: Any) -> str | None:
        if not album:
            return None
        images = album.get("images") or []
        if not images:
            return None
        sorted_images = sorted(
            (image for image in images if image.get("url")),
            key=lambda image: image.get("width") or 0,
            reverse=True,
        )
        return sorted_images[0]["url"] if sorted_images else None

    @staticmethod
    def _extract_album_id(album: Any) -> str | None:
        if not album:
            return None
        return album.get("id")
