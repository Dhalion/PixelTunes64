"""RGB matrix display adapter."""

from __future__ import annotations

from typing import Protocol

from PIL import Image

from .config import MatrixConfig
from .errors import MatrixDisplayError

try:  # pragma: no cover - optional runtime dependency
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
except ImportError:  # pragma: no cover - optional runtime dependency
    RGBMatrix = None
    RGBMatrixOptions = None


class MatrixDisplay(Protocol):
    def show(self, image: Image.Image) -> None: ...
    def clear(self) -> None: ...
    def close(self) -> None: ...


class RGBMatrixDisplay:
    """Display images on a Raspberry Pi RGB matrix."""

    def __init__(self, config: MatrixConfig) -> None:
        self._config = config
        self._matrix = self._create_matrix()

    def _create_matrix(self):
        if RGBMatrix is None or RGBMatrixOptions is None:
            raise MatrixDisplayError(
                "rgbmatrix is required at runtime. Install dependencies before starting the app."
            )

        options = RGBMatrixOptions()
        options.rows = self._config.rows
        options.cols = self._config.cols
        options.chain_length = self._config.chain_length
        options.parallel = self._config.parallel
        options.brightness = self._config.brightness
        options.hardware_mapping = self._config.hardware_mapping
        options.gpio_slowdown = self._config.gpio_slowdown
        options.pwm_bits = self._config.pwm_bits
        options.disable_hardware_pulsing = self._config.disable_hardware_pulsing

        try:
            return RGBMatrix(options=options)
        except OSError as exc:
            raise MatrixDisplayError("RGB matrix hardware could not be initialized.") from exc

    def show(self, image: Image.Image) -> None:
        frame = image.convert("RGB")
        frame.thumbnail((self._matrix.width, self._matrix.height), Image.Resampling.LANCZOS)
        self._matrix.SetImage(frame)

    def clear(self) -> None:
        self._matrix.Clear()

    def close(self) -> None:
        self.clear()
