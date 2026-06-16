from __future__ import annotations

import argparse
import logging
import sys
from typing import Final

import serial
import serial.tools.list_ports

from .model import SerialSettings
from .runtime import ProxyRuntime

try:
    import termios
except ImportError:  # pragma: no cover - exercised on Windows
    TERMIOS_ERROR_TYPES: Final[tuple[type[BaseException], ...]] = ()
else:
    TERMIOS_ERROR_TYPES = (termios.error,)

SERIAL_OPEN_ERRORS = (serial.SerialException, OSError, *TERMIOS_ERROR_TYPES)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HB Peak P1 smart serial proxy")
    parser.add_argument("--real-port")
    parser.add_argument("--artisan-port")
    parser.add_argument("--cropster-port")
    parser.add_argument("--real-protocol", choices=["modbus", "tc4"], default="modbus")
    parser.add_argument("--real-baud", type=int, default=115200)
    parser.add_argument("--real-modbus-bt-register", type=int, default=0)
    parser.add_argument("--real-modbus-et-register", type=int, default=3)
    parser.add_argument("--real-modbus-exhaust-register", type=int, default=3)
    parser.add_argument("--real-modbus-inlet-register", type=int, default=1)
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--stale-after", type=float, default=5.0)
    parser.add_argument("--cropster-register-bt", type=int, default=0)
    parser.add_argument("--cropster-register-exhaust", type=int, default=3)
    parser.add_argument("--cropster-register-3-source", choices=["exhaust", "et"], default="exhaust")
    parser.add_argument("--cropster-hold-last-for", type=float, default=60.0)
    parser.add_argument("--no-auto-reconnect", dest="auto_reconnect", action="store_false")
    parser.set_defaults(auto_reconnect=True)
    parser.add_argument("--reconnect-after-failures", type=int, default=3)
    parser.add_argument("--reconnect-delay", type=float, default=2.0)
    parser.add_argument("--virtual-reconnect-delay", type=float, default=2.0)
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--log-frames")
    return parser


def iter_port_descriptions() -> list[str]:
    descriptions: list[str] = []
    for port in serial.tools.list_ports.comports():
        details = " ".join(part for part in [port.device, port.description, port.hwid] if part)
        descriptions.append(details)
    return descriptions


def check_serial_port(port: str, baudrate: int, timeout: float) -> None:
    with serial.serial_for_url(
        port,
        baudrate=baudrate,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=timeout,
    ):
        return None


def _looks_like_driver_config_error(exc: BaseException) -> bool:
    return getattr(exc, "errno", None) == 22 or "Invalid argument" in str(exc)


def print_serial_error(prefix: str, exc: BaseException) -> None:
    print(f"{prefix}: {exc}")
    print("visible ports:")
    for description in iter_port_descriptions():
        print(description)
    if _looks_like_driver_config_error(exc):
        print(
            "hint: macOS reported a USB serial driver configuration error. "
            "Close Artisan/Cropster/proxy processes, unplug the Peak P1 USB cable, "
            "wait a few seconds, then plug it back in."
        )


def _require_ports(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    missing = [
        name
        for name in ["real_port", "artisan_port", "cropster_port"]
        if getattr(args, name) in {None, ""}
    ]
    if missing:
        parser.error("missing required ports: " + ", ".join("--" + name.replace("_", "-") for name in missing))


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    if args.list_ports:
        for description in iter_port_descriptions():
            print(description)
        return 0

    _require_ports(args, parser)

    if args.dry_run:
        try:
            check_serial_port(args.real_port, args.real_baud, 0.4)
            check_serial_port(args.artisan_port, 115200, 0.4)
            check_serial_port(args.cropster_port, 115200, 0.4)
        except SERIAL_OPEN_ERRORS as exc:
            print_serial_error("dry run failed", exc)
            return 2
        print("dry run ok")
        return 0

    runtime = ProxyRuntime(
        real_settings=SerialSettings(args.real_port, baudrate=args.real_baud),
        artisan_settings=SerialSettings(args.artisan_port),
        cropster_settings=SerialSettings(args.cropster_port),
        poll_interval=args.poll_interval,
        stale_after=args.stale_after,
        frame_log_path=args.log_frames,
        real_protocol=args.real_protocol,
        real_modbus_bt_register=args.real_modbus_bt_register,
        real_modbus_et_register=args.real_modbus_et_register,
        real_modbus_exhaust_register=args.real_modbus_exhaust_register,
        real_modbus_inlet_register=args.real_modbus_inlet_register,
        cropster_bt_register=args.cropster_register_bt,
        cropster_exhaust_register=args.cropster_register_exhaust,
        cropster_register_3_source=args.cropster_register_3_source,
        cropster_hold_last_for=args.cropster_hold_last_for,
        auto_reconnect=args.auto_reconnect,
        reconnect_after_failures=args.reconnect_after_failures,
        reconnect_delay=args.reconnect_delay,
        virtual_reconnect_delay=args.virtual_reconnect_delay,
    )
    try:
        runtime.run()
    except KeyboardInterrupt:
        runtime.stop()
        return 0
    except SERIAL_OPEN_ERRORS as exc:
        runtime.stop()
        print_serial_error("proxy startup failed", exc)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
