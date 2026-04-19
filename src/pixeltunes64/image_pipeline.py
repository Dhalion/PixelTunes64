"""Album-art loading and rendering helpers."""

from __future__ import annotations

import logging
from io import BytesIO
from pathlib import Path
from textwrap import wrap
from urllib.error import URLError
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .errors import CoverArtError
from .models import TrackInfo


class CoverArtProcessor:
    """Download and prepare cover art or fallback status frames."""

    def __init__(
        self,
        timeout_seconds: float = 10.0,
        cache_dir: str | Path = ".album-cache",
        logger: logging.Logger | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._cache_dir = Path(cache_dir)
        self._logger = logger or logging.getLogger(__name__)
        self._cache_enabled = True
        self._ensure_cache_dir()

    def render_track(self, track: TrackInfo, display_size: tuple[int, int]) -> Image.Image:
        if self._cache_enabled:
            cached = self._load_cached_image(track.cache_key, display_size)
            if cached is not None:
                return cached

        if track.cover_url:
            image = self._fit_image(self._download_image(track.cover_url), display_size)
            if self._cache_enabled:
                self._store_cached_image(track.cache_key, display_size, image)
            return image
        return self.render_message(
            title=track.title,
            subtitle=track.artist_line or "Spotify",
            display_size=display_size,
            accent=(120, 180, 255),
        )

    def render_idle(self, display_size: tuple[int, int]) -> Image.Image:
        return self.render_message(
            title="Paused",
            subtitle="Nothing is playing",
            display_size=display_size,
            accent=(255, 196, 90),
        )

    def render_error(self, message: str, display_size: tuple[int, int]) -> Image.Image:
        return self.render_message(
            title="Spotify error",
            subtitle=message,
            display_size=display_size,
            accent=(255, 120, 120),
        )

    def render_message(
        self,
        *,
        title: str,
        subtitle: str,
        display_size: tuple[int, int],
        accent: tuple[int, int, int],
    ) -> Image.Image:
        image = Image.new("RGB", display_size, color=(10, 10, 12))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        width, height = display_size
        self._draw_centered_text(draw, width, height, title, subtitle, font, accent)
        return image

    def _download_image(self, url: str) -> Image.Image:
        request = Request(url, headers={"User-Agent": "PixelTunes64/1.0"})
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                data = response.read()
        except URLError as exc:
            raise CoverArtError(f"Unable to download cover art from {url}.") from exc
        try:
            return Image.open(BytesIO(data)).convert("RGB")
        except OSError as exc:
            raise CoverArtError("Spotify returned an invalid image.") from exc

    @staticmethod
    def _fit_image(image: Image.Image, display_size: tuple[int, int]) -> Image.Image:
        return ImageOps.fit(
            image.convert("RGB"),
            display_size,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )

    def _cache_path(self, cache_key: str, display_size: tuple[int, int]) -> Path:
        width, height = display_size
        return self._cache_dir / f"{cache_key}_{width}x{height}.png"

    def _ensure_cache_dir(self) -> None:
        try:
            created = not self._cache_dir.exists()
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            if created:
                self._cache_dir.chmod(0o777)
        except OSError as exc:
            self._disable_cache(f"Cover art cache unavailable at {self._cache_dir}: {exc}")

    def _load_cached_image(self, cache_key: str, display_size: tuple[int, int]) -> Image.Image | None:
        try:
            cache_path = self._cache_path(cache_key, display_size)
            if not cache_path.exists():
                return None
            with Image.open(cache_path) as cached:
                return cached.convert("RGB")
        except OSError as exc:
            self._disable_cache(f"Cover art cache read failed: {exc}")
            return None

    def _store_cached_image(self, cache_key: str, display_size: tuple[int, int], image: Image.Image) -> None:
        try:
            self._ensure_cache_dir()
            cache_path = self._cache_path(cache_key, display_size)
            temp_path = cache_path.with_suffix(".tmp")
            image.convert("RGB").save(temp_path, format="PNG")
            temp_path.replace(cache_path)
        except OSError as exc:
            self._disable_cache(f"Cover art cache write failed: {exc}")

    def _disable_cache(self, message: str) -> None:
        if self._cache_enabled:
            self._logger.warning("%s; continuing without cache.", message)
            self._cache_enabled = False

    @staticmethod
    def _draw_centered_text(
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        title: str,
        subtitle: str,
        font: ImageFont.ImageFont,
        accent: tuple[int, int, int],
    ) -> None:
        title_lines = CoverArtProcessor._wrap_text(title, max_chars=max(8, width // 6))
        subtitle_lines = CoverArtProcessor._wrap_text(subtitle, max_chars=max(10, width // 5))
        lines: list[tuple[str, tuple[int, int, int]]] = [
            *( (line, accent) for line in title_lines ),
            *( (line, (220, 220, 220)) for line in subtitle_lines ),
        ]
        if not lines:
            return

        spacing = 2
        bbox_heights = []
        for line, _color in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            bbox_heights.append(bbox[3] - bbox[1])
        total_height = sum(bbox_heights) + spacing * (len(lines) - 1)
        current_y = max((height - total_height) // 2, 0)

        for (line, color), line_height in zip(lines, bbox_heights, strict=True):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = max((width - line_width) // 2, 0)
            draw.text((x, current_y), line, font=font, fill=color)
            current_y += line_height + spacing

    @staticmethod
    def _wrap_text(text: str, max_chars: int) -> list[str]:
        cleaned = " ".join(text.split())
        if not cleaned:
            return []
        return wrap(cleaned, width=max_chars) or [cleaned]
