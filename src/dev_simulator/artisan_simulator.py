"""CLI entry point for the ArtisanZ temperature simulator."""

from __future__ import annotations

import argparse
import asyncio
import logging
from dataclasses import replace
from typing import Any

from dev_simulator.event_scheduler import EventScheduler
from dev_simulator.profile import RoastSpec, generate_profile
from dev_simulator.ws_server import AsyncServer

_log = logging.getLogger(__name__)


def default_events() -> list[tuple[float, dict[str, Any]]]:
    """Return the default 6-event roast schedule from the design spec."""
    return [
        (0.0, {"pushMessage": "startRoasting"}),
        (300.0, {"pushMessage": "addEvent", "data": {"event": "colorChangeEvent"}}),
        (570.0, {"pushMessage": "addEvent", "data": {"event": "firstCrackBeginningEvent"}}),
        (645.0, {"pushMessage": "addEvent", "data": {"event": "firstCrackEndEvent"}}),
        (765.0, {"pushMessage": "addEvent", "data": {"event": "secondCrackBeginningEvent"}}),
        (780.0, {"pushMessage": "endRoasting"}),
    ]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="ArtisanZ synthetic BT/ET WebSocket simulator")
    parser.add_argument("--preset", choices=("light", "medium", "dark", "custom"), default="medium")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9090)
    parser.add_argument("--path", default="WebSocket")
    parser.add_argument("--start-mode", choices=("auto", "manual"), default="auto")
    parser.add_argument("--noise-std", type=float, default=0.3)
    parser.add_argument("--noise-model", choices=("gaussian", "ar1", "none"), default="ar1")
    parser.add_argument(
        "--fixed-step-ms",
        type=float,
        default=None,
        help="Advance simulated time by this many milliseconds per getData request.",
    )
    parser.add_argument("--log-level", choices=("debug", "info", "warning", "error"), default="info")

    parser.add_argument("--charge-bt", type=float)
    parser.add_argument("--charge-t", type=float)
    parser.add_argument("--turn-bt", type=float)
    parser.add_argument("--dry-bt", type=float)
    parser.add_argument("--fcs-bt", type=float)
    parser.add_argument("--fce-bt", type=float)
    parser.add_argument("--scs-bt", type=float)
    parser.add_argument("--drop-bt", type=float)

    parser.add_argument("--turn-t", type=float)
    parser.add_argument("--dry-t", type=float)
    parser.add_argument("--fcs-t", type=float)
    parser.add_argument("--fce-t", type=float)
    parser.add_argument("--scs-t", type=float)
    parser.add_argument("--drop-t", type=float)
    return parser.parse_args(argv)


def build_spec(args: argparse.Namespace) -> RoastSpec:
    """Build a RoastSpec from preset defaults plus CLI overrides."""
    spec = _preset_spec(args.preset)
    overrides = {
        "charge_bt": args.charge_bt,
        "charge_t": args.charge_t,
        "turn_bt": args.turn_bt,
        "dry_bt": args.dry_bt,
        "fcs_bt": args.fcs_bt,
        "fce_bt": args.fce_bt,
        "scs_bt": args.scs_bt,
        "drop_bt": args.drop_bt,
        "turn_t": args.turn_t,
        "dry_t": args.dry_t,
        "fcs_t": args.fcs_t,
        "fce_t": args.fce_t,
        "scs_t": args.scs_t,
        "drop_t": args.drop_t,
    }
    clean_overrides = {key: value for key, value in overrides.items() if value is not None}
    return replace(
        spec,
        **clean_overrides,
        noise_std=args.noise_std,
        noise_model=args.noise_model,
    )


def _preset_spec(preset: str) -> RoastSpec:
    if preset in {"medium", "custom"}:
        return RoastSpec()
    if preset == "light":
        return RoastSpec(
            dry_t=285.0,
            fcs_t=540.0,
            fce_t=615.0,
            scs_t=735.0,
            drop_t=750.0,
            dry_bt=150.0,
            fcs_bt=190.0,
            fce_bt=199.0,
            scs_bt=210.0,
            drop_bt=212.0,
            dry_et=168.0,
            fcs_et=203.0,
            fce_et=209.0,
            scs_et=218.0,
            drop_et=220.0,
        )
    if preset == "dark":
        return RoastSpec(
            dry_t=315.0,
            fcs_t=600.0,
            fce_t=690.0,
            scs_t=810.0,
            drop_t=825.0,
            dry_bt=154.0,
            fcs_bt=196.0,
            fce_bt=206.0,
            scs_bt=218.0,
            drop_bt=222.0,
            dry_et=172.0,
            fcs_et=208.0,
            fce_et=216.0,
            scs_et=226.0,
            drop_et=230.0,
        )
    raise ValueError(f"Unknown preset: {preset!r}")


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def build_server(args: argparse.Namespace) -> AsyncServer:
    spec = build_spec(args)
    profile = generate_profile(spec)
    scheduler = EventScheduler(default_events(), start_mode=args.start_mode)
    path = args.path.strip("/") or "WebSocket"
    _log.info(
        "Generated %s preset profile: %d points, %.0fs duration",
        args.preset,
        len(profile["timex"]),
        spec.drop_t,
    )
    _log.info("ArtisanZ endpoint: ws://%s:%d/%s", args.host, args.port, path)
    _log.info("Noise: model=%s, std=%.2f°C", args.noise_model, args.noise_std)
    _log.info("Start mode: %s", args.start_mode)
    if args.fixed_step_ms is not None:
        _log.info("Fixed step: %.0fms per request", args.fixed_step_ms)
    return AsyncServer(
        profile=profile,
        scheduler=scheduler,
        host=args.host,
        port=args.port,
        path=path,
        noise_model=args.noise_model,
        noise_std=args.noise_std,
        fixed_step_ms=args.fixed_step_ms,
    )


async def run_with_fallback(args: argparse.Namespace) -> None:
    """Run the server, falling back to next available port on bind errors."""
    server = build_server(args)
    try:
        await server.run()
    except OSError as exc:
        if args.port != 9090:
            raise
        fallback_port = 8080
        _log.warning("Could not bind to port %d (%s); falling back to port %d", args.port, exc, fallback_port)
        fallback_args = argparse.Namespace(**vars(args))
        fallback_args.port = fallback_port
        await build_server(fallback_args).run()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    configure_logging(args.log_level)
    try:
        asyncio.run(run_with_fallback(args))
    except KeyboardInterrupt:
        _log.info("Server stopped")


if __name__ == "__main__":
    main()
