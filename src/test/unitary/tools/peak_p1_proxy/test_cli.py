import serial
import pytest
import tools.peak_p1_proxy.cli as cli
from tools.peak_p1_proxy.cli import build_parser, main


def test_parser_accepts_required_ports() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "--real-port",
            "COM5",
            "--artisan-port",
            "COM10",
            "--cropster-port",
            "COM12",
        ]
    )

    assert args.real_port == "COM5"
    assert args.artisan_port == "COM10"
    assert args.cropster_port == "COM12"
    assert args.real_protocol == "modbus"


def test_list_ports_returns_zero_without_required_ports(monkeypatch, capsys) -> None:
    monkeypatch.setattr("tools.peak_p1_proxy.cli.iter_port_descriptions", lambda: ["COM5 Peak P1"])

    exit_code = main(["--list-ports"])

    assert exit_code == 0
    assert "COM5 Peak P1" in capsys.readouterr().out


def test_dry_run_calls_port_checker(monkeypatch, capsys) -> None:
    checked: list[str] = []
    monkeypatch.setattr(
        "tools.peak_p1_proxy.cli.check_serial_port",
        lambda port, baudrate, timeout: checked.append(port),
    )

    exit_code = main(
        [
            "--real-port",
            "COM5",
            "--artisan-port",
            "COM10",
            "--cropster-port",
            "COM12",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert checked == ["COM5", "COM10", "COM12"]
    assert "dry run ok" in capsys.readouterr().out


def test_dry_run_can_open_pyserial_loop_urls(capsys) -> None:
    exit_code = main(
        [
            "--real-port",
            "loop://",
            "--artisan-port",
            "loop://",
            "--cropster-port",
            "loop://",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert "dry run ok" in capsys.readouterr().out


def test_dry_run_reports_visible_ports_on_open_failure(monkeypatch, capsys) -> None:
    def fail_open(port: str, baudrate: int, timeout: float) -> None:
        raise serial.SerialException(f"could not open {port}")

    monkeypatch.setattr("tools.peak_p1_proxy.cli.check_serial_port", fail_open)
    monkeypatch.setattr("tools.peak_p1_proxy.cli.iter_port_descriptions", lambda: ["COM5 FT232R"])

    exit_code = main(
        [
            "--real-port",
            "missing-port",
            "--artisan-port",
            "loop://",
            "--cropster-port",
            "loop://",
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "dry run failed" in output
    assert "missing-port" in output
    assert "COM5 FT232R" in output


def test_dry_run_reports_termios_errors_without_traceback(monkeypatch, capsys) -> None:
    def fail_open(port: str, baudrate: int, timeout: float) -> None:
        raise OSError(22, "Invalid argument")

    monkeypatch.setattr("tools.peak_p1_proxy.cli.check_serial_port", fail_open)
    monkeypatch.setattr("tools.peak_p1_proxy.cli.iter_port_descriptions", lambda: ["COM5 FT232R"])

    exit_code = main(
        [
            "--real-port",
            "/dev/cu.usbserial-AV0LY3SU",
            "--artisan-port",
            "loop://",
            "--cropster-port",
            "loop://",
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "dry run failed" in output
    assert "Invalid argument" in output
    assert "visible ports:" in output
    assert "COM5 FT232R" in output
    assert "USB serial driver" in output


def test_dry_run_reports_platform_termios_errors_without_traceback(monkeypatch, capsys) -> None:
    termios = pytest.importorskip("termios")

    def fail_open(port: str, baudrate: int, timeout: float) -> None:
        raise termios.error(22, "Invalid argument")

    monkeypatch.setattr("tools.peak_p1_proxy.cli.check_serial_port", fail_open)
    monkeypatch.setattr("tools.peak_p1_proxy.cli.iter_port_descriptions", lambda: ["COM5 FT232R"])

    exit_code = main(
        [
            "--real-port",
            "/dev/cu.usbserial-AV0LY3SU",
            "--artisan-port",
            "loop://",
            "--cropster-port",
            "loop://",
            "--dry-run",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "dry run failed" in output
    assert "Invalid argument" in output
    assert "COM5 FT232R" in output


def test_runtime_reports_serial_startup_errors_without_traceback(monkeypatch, capsys) -> None:
    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            return None

        def run(self) -> None:
            raise OSError(22, "Invalid argument")

        def stop(self) -> None:
            return None

    monkeypatch.setattr(cli, "ProxyRuntime", FakeRuntime)
    monkeypatch.setattr("tools.peak_p1_proxy.cli.iter_port_descriptions", lambda: ["COM5 FT232R"])

    exit_code = main(
        [
            "--real-port",
            "/dev/cu.usbserial-AV0LY3SU",
            "--artisan-port",
            "loop://",
            "--cropster-port",
            "loop://",
            "--no-auto-reconnect",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 2
    assert "proxy startup failed" in output
    assert "Invalid argument" in output
    assert "COM5 FT232R" in output


def test_main_passes_cropster_mapping_options_to_runtime(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeRuntime:
        def __init__(self, **kwargs) -> None:
            captured.update(kwargs)

        def run(self) -> None:
            captured["ran"] = True

        def stop(self) -> None:
            captured["stopped"] = True

    monkeypatch.setattr(cli, "ProxyRuntime", FakeRuntime)

    exit_code = main(
        [
            "--real-port",
            "COM5",
            "--artisan-port",
            "COM10",
            "--cropster-port",
            "COM12",
            "--cropster-register-bt",
            "2",
            "--cropster-register-exhaust",
            "5",
            "--cropster-register-3-source",
            "et",
            "--cropster-hold-last-for",
            "30",
            "--real-protocol",
            "tc4",
            "--no-auto-reconnect",
            "--reconnect-after-failures",
            "5",
            "--reconnect-delay",
            "0.75",
            "--virtual-reconnect-delay",
            "0.5",
        ]
    )

    assert exit_code == 0
    assert captured["real_protocol"] == "tc4"
    assert captured["cropster_bt_register"] == 2
    assert captured["cropster_exhaust_register"] == 5
    assert captured["cropster_register_3_source"] == "et"
    assert captured["cropster_hold_last_for"] == 30.0
    assert captured["auto_reconnect"] is False
    assert captured["reconnect_after_failures"] == 5
    assert captured["reconnect_delay"] == 0.75
    assert captured["virtual_reconnect_delay"] == 0.5
    assert captured["ran"] is True
