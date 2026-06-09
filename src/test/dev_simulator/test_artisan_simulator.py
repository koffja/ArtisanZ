"""Tests for the dev simulator CLI entry point."""

from __future__ import annotations

from dev_simulator.artisan_simulator import build_server, build_spec, parse_args


class TestBuildSpec:
    def test_charge_time_override_applies_to_spec(self) -> None:
        args = parse_args(["--preset", "custom", "--charge-t", "10"])

        spec = build_spec(args)

        assert spec.charge_t == 10.0


class TestBuildServer:
    def test_empty_path_falls_back_to_websocket(self) -> None:
        args = parse_args(["--path", "", "--noise-model", "none"])

        server = build_server(args)

        assert server.path == "WebSocket"

    def test_slash_only_path_falls_back_to_websocket(self) -> None:
        args = parse_args(["--path", "////", "--noise-model", "none"])

        server = build_server(args)

        assert server.path == "WebSocket"
