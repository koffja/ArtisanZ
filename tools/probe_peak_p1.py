#!/usr/bin/env python3
"""probe_peak_p1.py — protocol auto-detection for HB PEAK-P1 (or any USB-serial roaster).

Probes an FTDI USB-serial port with BOTH protocol handshakes in parallel and
reports which one the device actually responds to:

  - Modbus RTU  (pymodbus 3.13.0, function 3 / 4, 0x01 0x03 ... binary frame)
  - TC4 ASCII   (pyserial  raw, "CHAN;1200\\n" expecting "#..." reply)

This is the only honest way to resolve the protocol question without vendor docs:
we let the device answer for itself.

After a positive match the script emits a paste-ready Artisan .aset (either
[Modbus] or [SerialPort]+[ArduinoPID] format) for the chosen device id.

Usage:
    python3 tools/probe_peak_p1.py                       # auto-detect on every FTDI port
    python3 tools/probe_peak_p1.py /dev/cu.usbserial-XXX  # one specific port
    python3 tools/probe_peak_p1.py --only-ftdi --json    # JSON report at end

Read-only: never writes function 5/6/15/16/22/23 (Modbus) nor OT1/DCFAN (TC4).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field

import serial
import serial.tools.list_ports



@dataclass
class ModbusResult:
    port: str
    baud: int
    device_id: int
    function: int
    register: int
    count: int
    parity: str
    stopbits: int
    raw: list[int]
    timeout: float

    @property
    def guessed_kind(self) -> str:
        if not self.raw:
            return "raw"
        lo, hi = min(self.raw), max(self.raw)
        if 0 <= lo and hi <= 100:
            return "percent"
        if 100 <= lo and hi <= 4000:
            return "temperature_x10"
        if 1000 <= lo and hi <= 50000 and (hi - lo) >= 50:
            return "temperature_x100"
        return "raw"

    @property
    def guessed_div(self) -> int:
        return {"percent": 0, "temperature_x10": 1, "temperature_x100": 2, "raw": 0}[self.guessed_kind]


@dataclass
class TC4Result:
    port: str
    baud: int
    init_response: str      # "#" + something OR ""
    read_response: str      # "t0,t1,t2,..." OR ""
    timeout: float


@dataclass
class PortReport:
    port: str
    modbus_hits: list[ModbusResult] = field(default_factory=list)
    tc4_hits: list[TC4Result] = field(default_factory=list)
    modbus_attempts: int = 0
    modbus_errors: int = 0
    tc4_attempts: int = 0
    tc4_errors: int = 0

    @property
    def verdict(self) -> str:
        if self.modbus_hits:
            return "Modbus RTU"
        if self.tc4_hits:
            return "TC4 (Arduino / Hottop)"
        return "no response (neither protocol)"



def _try_modbus(port: str, baud: int, device_id: int, function: int,
                register: int, count: int, parity: str, stopbits: int,
                timeout: float) -> ModbusResult | None:
    """Try a single Modbus RTU read. Returns ModbusResult on non-trivial data, else None."""
    try:
        from pymodbus.client import AsyncModbusSerialClient
        from pymodbus.framer import FramerType
        from pymodbus.pdu import ExceptionResponse
    except ImportError:
        return None
    import asyncio

    async def _one() -> ModbusResult | None:
        client = AsyncModbusSerialClient(
            framer=FramerType.RTU,
            port=port,
            baudrate=baud,
            bytesize=8,
            parity=parity,
            stopbits=stopbits,
            retries=0,
            timeout=timeout,
        )
        connected = await client.connect()
        if not connected:
            try:
                close_result = client.close()
                if close_result is not None and hasattr(close_result, "__await__"):
                    await close_result
            except Exception:
                pass
            return None
        try:
            if function == 3:
                res = await client.read_holding_registers(address=register, count=count, device_id=device_id)
            else:
                res = await client.read_input_registers(address=register, count=count, device_id=device_id)
            if res is None or isinstance(res, ExceptionResponse):
                return None
            if getattr(res, "isError", lambda: False)():
                return None
            regs = getattr(res, "registers", None)
            if regs is None:
                return None
            nontrivial = any((v != 0 and v != 0xFFFF) for v in regs)
            if not nontrivial:
                return None
            return ModbusResult(
                port=port, baud=baud, device_id=device_id, function=function,
                register=register, count=count, parity=parity, stopbits=stopbits,
                raw=list(regs), timeout=timeout,
            )
        finally:
            try:
                close_result = client.close()
                if close_result is not None and hasattr(close_result, "__await__"):
                    await close_result
            except Exception:
                pass

    try:
        return asyncio.run(_one())
    except Exception:
        return None


def probe_modbus(port: str, timeout: float = 0.3) -> tuple[list[ModbusResult], int, int]:
    """Sweep Modbus candidates. Returns (hits, attempts, errors)."""
    bauds = [9600, 19200, 38400, 115200]
    devices = [1, 2, 3, 25, 115, 116, 117, 126, 127, 128]
    functions = [3, 4]
    parities = ["N", "E"]
    hits: list[ModbusResult] = []
    attempts = 0
    errors = 0
    for baud in bauds:
        for parity in parities:
            for device_id in devices:
                for function in functions:
                    for register in (0, 10, 20, 30):
                        attempts += 1
                        res = _try_modbus(port, baud, device_id, function, register,
                                          count=10, parity=parity, stopbits=1, timeout=timeout)
                        if res is not None:
                            hits.append(res)
                            print(f"  [MODBUS HIT] {port} baud={baud} dev={device_id} func={function} "
                                  f"parity={parity} reg={register} raw={res.raw} -> {res.guessed_kind}")
                        else:
                            errors += 1
                        if len(hits) >= 8:
                            return hits, attempts, errors
    return hits, attempts, errors



def _try_tc4(port: str, baud: int, timeout: float) -> TC4Result | None:
    """Send CHAN;1200 then READ to a TC4-shaped device. Returns TC4Result on ACK."""
    try:
        with serial.Serial(port, baudrate=baud, bytesize=8, parity="N",
                           stopbits=1, timeout=timeout) as sp:
            sp.reset_input_buffer()
            sp.reset_output_buffer()
            sp.write(b"CHAN;1200\n")
            sp.flush()
            time.sleep(0.15)
            init_resp = sp.readline().decode("utf-8", "ignore").strip()
            if not init_resp.startswith("#"):
                return None
            sp.reset_input_buffer()
            sp.reset_output_buffer()
            sp.write(b"READ\n")
            sp.flush()
            time.sleep(0.15)
            read_resp = sp.readline().decode("utf-8", "ignore").strip()
            if not read_resp:
                return None
            parts = [p.strip() for p in read_resp.split(",")]
            if len(parts) < 3:
                return None
            try:
                for p in parts[:5]:
                    float(p)
            except ValueError:
                return None
            return TC4Result(port=port, baud=baud,
                             init_response=init_resp, read_response=read_resp,
                             timeout=timeout)
    except Exception:
        return None


def probe_tc4(port: str, timeout: float = 0.4) -> tuple[list[TC4Result], int, int]:
    """Sweep TC4 baudrates. Returns (hits, attempts, errors)."""
    bauds = [9600, 19200, 38400, 57600, 115200, 230400]
    hits: list[TC4Result] = []
    attempts = 0
    errors = 0
    for baud in bauds:
        attempts += 1
        res = _try_tc4(port, baud, timeout)
        if res is not None:
            hits.append(res)
            print(f"  [TC4 HIT]     {port} baud={baud}  init={res.init_response!r}  read={res.read_response!r}")
        else:
            errors += 1
    return hits, attempts, errors



def detect_ports(only_ftdi: bool = False) -> list[str]:
    """Return /dev/cu.* ports (de-duped by serial number). /dev/tty.* blocks on DCD."""
    FTDI_VID = 0x0403
    seen: set[str] = set()
    out: list[str] = []
    for p in serial.tools.list_ports.comports():
        if p.device.startswith("/dev/tty."):
            continue
        if p.device.endswith(".Bluetooth-Incoming-Port"):
            continue
        if only_ftdi and p.vid != FTDI_VID:
            continue
        key = p.serial_number or p.device
        if key in seen:
            continue
        seen.add(key)
        out.append(p.device)
    return out


def probe_port(port: str, modbus_timeout: float = 0.3, tc4_timeout: float = 0.4) -> PortReport:
    r = PortReport(port=port)
    if not os.path.exists(port):
        print(f"  [skip] {port}: device file missing", file=sys.stderr)
        return r
    if not os.access(port, os.R_OK | os.W_OK):
        print(f"  [skip] {port}: not R/W", file=sys.stderr)
        return r
    print(f"  -> probing {port} with Modbus RTU ...")
    r.modbus_hits, r.modbus_attempts, r.modbus_errors = probe_modbus(port, timeout=modbus_timeout)
    if not r.modbus_hits:
        print(f"  -> probing {port} with TC4 ASCII ...")
        r.tc4_hits, r.tc4_attempts, r.tc4_errors = probe_tc4(port, timeout=tc4_timeout)
    return r



def emit_artisan_config(reports: list[PortReport]) -> None:
    """Print a paste-ready .aset (or in-GUI fill instructions) for the winning protocol."""
    modbus_winner = next((r for r in reports if r.modbus_hits), None)
    tc4_winner = next((r for r in reports if r.tc4_hits), None)

    print()
    print("=" * 70)
    print("ARTISAN CONFIG (paste into the right place)")
    print("=" * 70)

    if modbus_winner:
        h = modbus_winner.modbus_hits[0]
        print(f"# Verdict: Modbus RTU on {modbus_winner.port}")
        print()
        print("# Drop this file at src/includes/Machines/HB/Peak_P1.aset")
        print("# then pick 'HB Peak P1' from Config -> Machine -> Setup.")
        print("[General]")
        print("roastertype_setup=HB Peak P1")
        print("Delay=2000")
        print()
        print("[Device]")
        print("id=29   # MODBUS (generic Modbus device slot)")
        print()
        print("[SerialPort]")
        print(f"comport={modbus_winner.port}")
        print(f"baudrate={h.baud}")
        print(f"parity={h.parity}")
        print("stopbits=1")
        print("timeout=0.4")
        print()
        print("[Modbus]")
        print(f"comport={modbus_winner.port}")
        print(f"baudrate={h.baud}")
        print(f"parity={h.parity}")
        print("stopbits=1")
        print("timeout=0.4")
        print(f"input1deviceId={h.device_id}")
        print(f"input1code={h.function}")
        print(f"input1register={h.register}")
        print(f"input1div={h.guessed_div}")
        print("input1mode=C")
        return

    if tc4_winner:
        h = tc4_winner.tc4_hits[0]
        print(f"# Verdict: TC4 / Arduino on {tc4_winner.port}")
        print()
        print("# In Artisan: Config -> Device -> pick 'Arduino TC4' (id=19).")
        print("# Then in the SerialPort tab set:")
        print(f"comport = {tc4_winner.port}")
        print(f"baudrate = {h.baud}")
        print("bytesize = 8")
        print("parity   = N")
        print("stopbits = 1")
        print("timeout  = 0.4")
        print()
        print("# Artisan will auto-run CHAN;1200 / UNITS;C / FILT;... on connect.")
        print("# First READ response we saw (t0,t1,t2[,t3,t4][,Heater,Fan,SV]):")
        print(f"# {h.read_response}")
        return

    print("# Neither protocol responded. Things to check:")
    print("#   1. Is the roaster plugged in AND powered on?")
    print("#   2. Is the USB cable data-capable (not charge-only)?")
    print("#   3. Try --baud 1200 2400 4800 if default rates miss.")
    print("#   4. The device might use a vendor-proprietary protocol. Paste a")
    print("#      hex/ASCII capture from 'minicom' or 'CoolTerm' and we can decode.")



def main() -> int:
    ap = argparse.ArgumentParser(
        description="Dual-protocol (Modbus RTU + TC4 ASCII) auto-detection for HB PEAK-P1.",
    )
    ap.add_argument("port", nargs="*", help="Port(s) to probe. Omit for auto-detect.")
    ap.add_argument("--only-ftdi", action="store_true", help="Restrict to FTDI (VID 0x0403) ports.")
    ap.add_argument("--modbus-timeout", type=float, default=0.3)
    ap.add_argument("--tc4-timeout", type=float, default=0.4)
    ap.add_argument("--json", action="store_true", help="Emit JSON report at end.")
    args = ap.parse_args()

    ports = list(args.port) if args.port else detect_ports(only_ftdi=args.only_ftdi)
    if not ports:
        print("No candidate ports. Plug the roaster in (or pass a port path).", file=sys.stderr)
        return 1

    print(f"Probing {len(ports)} port(s): {ports}")
    t0 = time.time()
    reports: list[PortReport] = []
    for port in ports:
        print(f"--- {port} ---")
        reports.append(probe_port(port, modbus_timeout=args.modbus_timeout, tc4_timeout=args.tc4_timeout))
    elapsed = time.time() - t0

    print()
    print("=" * 70)
    print(f"VERDICT  ({elapsed:.1f}s)")
    print("=" * 70)
    for r in reports:
        print(f"  {r.port}  -> {r.verdict}  "
              f"(modbus: {len(r.modbus_hits)} hits / {r.modbus_attempts} attempts, "
              f"tc4: {len(r.tc4_hits)} hits / {r.tc4_attempts} attempts)")

    emit_artisan_config(reports)

    if args.json:
        out = []
        for r in reports:
            out.append({
                "port": r.port,
                "verdict": r.verdict,
                "modbus_hits": [
                    {
                        "baud": h.baud, "device_id": h.device_id, "function": h.function,
                        "register": h.register, "count": h.count, "parity": h.parity,
                        "raw": h.raw, "guessed_kind": h.guessed_kind, "guessed_div": h.guessed_div,
                    }
                    for h in r.modbus_hits
                ],
                "tc4_hits": [
                    {
                        "baud": h.baud, "init_response": h.init_response, "read_response": h.read_response,
                    }
                    for h in r.tc4_hits
                ],
            })
        print()
        print("=== JSON ===")
        print(json.dumps(out, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    sys.exit(main())
