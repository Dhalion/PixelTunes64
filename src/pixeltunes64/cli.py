"""Command-line entry point."""

from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from typing import Sequence

from .app import PixelTunes64App
from .config import AppConfig, load_environment_file
from .errors import PixelTunesError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Display Spotify cover art on a RGB matrix.")
    parser.add_argument("--env-file", default=".env", help="Path to the environment file.")
    parser.add_argument("--poll-interval", type=float, help="Polling interval in seconds.")
    parser.add_argument("--log-level", help="Logging level.")
    parser.add_argument("--display-width", type=int, help="Rendered image width.")
    parser.add_argument("--display-height", type=int, help="Rendered image height.")
    parser.add_argument("--matrix-rows", type=int, help="RGB matrix row count.")
    parser.add_argument("--matrix-cols", type=int, help="RGB matrix column count.")
    parser.add_argument("--chain-length", type=int, help="RGB matrix chain length.")
    parser.add_argument("--parallel", type=int, help="RGB matrix parallel count.")
    parser.add_argument("--brightness", type=int, help="Matrix brightness (0-100).")
    parser.add_argument("--hardware-mapping", help="RGB matrix hardware mapping.")
    parser.add_argument("--gpio-slowdown", type=int, help="GPIO slowdown value.")
    parser.add_argument("--pwm-bits", type=int, help="PWM bit depth.")
    parser.add_argument(
        "--disable-hardware-pulsing",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable hardware pulsing.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    app = None
    try:
        args = build_parser().parse_args(argv)
        load_environment_file(args.env_file)

        config = AppConfig.from_env()
        config = _apply_cli_overrides(config, args)
        logging.basicConfig(
            level=getattr(logging, config.log_level, logging.INFO),
            format="%(levelname)s %(name)s: %(message)s",
        )
        app = PixelTunes64App(config=config)
        app.run()
    except KeyboardInterrupt:
        return 0
    except PixelTunesError as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 1
    finally:
        if app is not None:
            app.close()
    return 0


def _apply_cli_overrides(config: AppConfig, args: argparse.Namespace) -> AppConfig:
    matrix = config.matrix
    matrix_overrides = {}
    if args.display_width is not None:
        matrix_overrides["display_width"] = args.display_width
    if args.display_height is not None:
        matrix_overrides["display_height"] = args.display_height
    if args.matrix_rows is not None:
        matrix_overrides["rows"] = args.matrix_rows
    if args.matrix_cols is not None:
        matrix_overrides["cols"] = args.matrix_cols
    if args.chain_length is not None:
        matrix_overrides["chain_length"] = args.chain_length
    if args.parallel is not None:
        matrix_overrides["parallel"] = args.parallel
    if args.brightness is not None:
        matrix_overrides["brightness"] = max(1, min(args.brightness, 100))
    if args.hardware_mapping is not None:
        matrix_overrides["hardware_mapping"] = args.hardware_mapping
    if args.gpio_slowdown is not None:
        matrix_overrides["gpio_slowdown"] = args.gpio_slowdown
    if args.pwm_bits is not None:
        matrix_overrides["pwm_bits"] = args.pwm_bits
    if args.disable_hardware_pulsing is not None:
        matrix_overrides["disable_hardware_pulsing"] = args.disable_hardware_pulsing

    updated_matrix = replace(matrix, **matrix_overrides) if matrix_overrides else matrix
    updated_config = config.with_updates(
        poll_interval_seconds=args.poll_interval,
        log_level=args.log_level.upper() if args.log_level else None,
        matrix=updated_matrix,
    )
    return updated_config


if __name__ == "__main__":
    raise SystemExit(main())
