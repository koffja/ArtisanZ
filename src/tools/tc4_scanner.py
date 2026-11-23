#!/usr/bin/env python3
"""
TC4 channel & firmware capability scanner for ArtisanZ.

独立诊断工具:在不开 ArtisanZ 的情况下,直接对 TC4 板做"通道扫描"
和"固件能力探测",帮你判断:
  1. chan1~chan4 哪些通道实际接了热电偶(温度落在合理区间);
  2. 当前固件是否支持硬件 PID(发 PID;ON 后 READ 回包字段数会从 3 变成 6);
  3. 如果支持 PID,当前 Heater / Fan / SV 的实时值是多少。

协议实现严格对齐 artisanlib/comm.py:6950 的 ARDUINOTC4temperature(),
以及 pid_control.py:1495+ 的 PID;ON / PID;LIMIT / PID;SV 控制命令,
确保扫描结果与 ArtisanZ 主程序读到的一致。

默认串口参数取自 includes/Machines/HB/Model_S.aset (115200/8N1/timeout 0.4)。

用法:
    .venv/bin/python tools/tc4_scanner.py                 # 自动选择第一个 USB 串口
    .venv/bin/python tools/tc4_scanner.py -p /dev/cu.usbserial-310
    .venv/bin/python tools/tc4_scanner.py --no-pid        # 只扫通道,不发 PID;ON(只读固件安全)
    .venv/bin/python tools/tc4_scanner.py --control       # 额外发 PID;SV 试探写控制(默认关闭,需显式开启)
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass

import serial
import serial.tools.list_ports


# ─────────────────────────────────────────────────────────────────────────────
# 常量(对齐 comm.py / Model_S.aset)
# ─────────────────────────────────────────────────────────────────────────────
HB_MODEL_S_BAUDRATE = 115200      # Model_S.aset:baudrate
HB_MODEL_S_BYTESIZE = 8           # Model_S.aset:bytesize
HB_MODEL_S_PARITY = "N"           # Model_S.aset:parity
HB_MODEL_S_STOPBITS = 1           # Model_S.aset:stopbits
HB_MODEL_S_TIMEOUT = 0.4          # Model_S.aset:timeout

READ_SETTLE_SEC = 0.1             # comm.py:6997/7040 写后等 0.1s 再读
PORT_OPEN_SETTLE_SEC = 1.0        # comm.py:2737 打开后等 1s(Arduino DTR 复位)
RETRIES = 2                       # 单次读失败重试次数

# TC4 合理温度区间(摄氏度)。低于此值视为"未接热电偶"(对应 comm.py 的 -1 哨兵)
REALISTIC_TEMP_MIN = -20.0
REALISTIC_TEMP_MAX = 400.0


def _looks_like_temp(s: str) -> bool:
    """判断字符串是否像一个温度数值(用于探测固件类型)。"""
    try:
        v = float(s)
        return -50.0 <= v <= 500.0
    except (ValueError, TypeError):
        return False


@dataclass
class ChannelReading:
    channel: int                  # 1..4
    temp_c: float                 # 读到的温度,-1 表示无效
    raw: str                      # READ 原始回包(诊断用)

    @property
    def is_realistic(self) -> bool:
        return REALISTIC_TEMP_MIN <= self.temp_c <= REALISTIC_TEMP_MAX

    @property
    def status(self) -> str:
        if self.temp_c == -1:
            return "NO_DATA  (固件返回 -1,该通道可能未启用)"
        if not self.is_realistic:
            return f"OUT_OF_RANGE  (温度异常:{self.temp_c}°C,可能未接热电偶或断线)"
        return f"OK  实测 {self.temp_c:.1f}°C"


# ─────────────────────────────────────────────────────────────────────────────
# 底层串口收发(严格对齐 artisanlib/comm.py:6950 的命令序列)
# ─────────────────────────────────────────────────────────────────────────────
class TC4:
    """TC4 串口通信封装,行为与 artisanlib/comm.py ARDUINOTC4temperature 一致。"""

    def __init__(self, port: str, baudrate: int = HB_MODEL_S_BAUDRATE,
                 bytesize: int = HB_MODEL_S_BYTESIZE, parity: str = HB_MODEL_S_PARITY,
                 stopbits: int = HB_MODEL_S_STOPBITS, timeout: float = HB_MODEL_S_TIMEOUT,
                 verbose: bool = True) -> None:
        self.verbose = verbose
        # 重要:对齐 artisanlib/comm.py:2729 openport + 2749 confport
        #   1) 先建 Serial 对象不打开,设 exclusive=True(comm.py:2758 非 Windows 必须),
        #      否则 macOS DriverKit dext 会拒绝后续 tcsetattr;
        #   2) open() 后 Arduino 因 DTR 复位,需 sleep(1) 才能通信(comm.py:2737)。
        self.sp = serial.Serial(exclusive=True)  # 先不绑端口
        self.sp.port = port
        self.sp.baudrate = baudrate
        self.sp.bytesize = bytesize
        self.sp.parity = parity
        self.sp.stopbits = stopbits
        self.sp.timeout = timeout
        self.sp.open()
        # Arduino 复位等待 —— 这是之前脚本失败的根本原因
        time.sleep(PORT_OPEN_SETTLE_SEC)
        # 打开时清缓冲,模拟 comm.py:6967
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._initialized = False
        self.firmware_kind: str = "unknown"   # initialize() 会改成 "minimal" 或 "full"
        self._log(f"已打开 {port} @ {baudrate}/{bytesize}{parity}{stopbits} timeout={timeout}s "
                  f"(exclusive=True, 等 {PORT_OPEN_SETTLE_SEC}s 复位)")

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"    {msg}", file=sys.stderr)

    def close(self) -> None:
        try:
            self.sp.close()
        except Exception:
            pass

    # ── 协议层 ────────────────────────────────────────────────────────────
    def _w(self, cmd: str) -> None:
        """发送 ASCII 命令(不带换行,调用方自己加)。对齐 comm.py:6995 str2cmd。"""
        self.sp.write(cmd.encode("utf-8"))

    def _readline(self) -> str:
        """读一行,去掉结尾 \\r\\n。对齐 comm.py:7000 [:-2]。"""
        try:
            line = self.sp.readline().decode("utf-8", "ignore")
        except Exception:
            return ""
        # comm.py 用 [:-2] 去掉 \r\n;空行就返回空
        return line[:-2] if len(line) >= 2 else line.strip()

    def _send_expect_ok(self, cmd: str, label: str) -> bool:
        """
        发送一条命令并读回包。对齐 comm.py:6995-7004。

        判定规则(经实测,这块固件是 aArtisanQ_PID 的握手协议变体):
          - 回包以 '#' 开头 → 标准握手,通过(对应 comm.py:7003 的判定)
          - 回包为空(无确认)→ 不直接判定失败,返回 False 但由调用方
            通过后续 READ 是否有数据来二次判断(这块固件 CHAN 静默接受)
          - 回包是其他内容 → 失败
        """
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._w(cmd + "\n")
        self.sp.flush()
        time.sleep(READ_SETTLE_SEC)
        result = self._readline()
        self._log(f"Tx={cmd!r:30s}  Rx={result!r}")
        if len(result) == 0:
            # 静默:不一定是失败,调用方需后续 READ 二次确认
            return False
        if result.startswith("#"):
            return True
        print(f"  ✗ {label} 失败:固件回非 '#' 内容(rx={result!r})")
        return False

    # ── 初始化(对齐 comm.py:6966-7033)────────────────────────────────────
    def initialize(self, units: str = "C", filt: list[int] | None = None) -> bool:
        """
        探测固件类型并初始化。filt 默认 [70,70,70,70] 取自 comm.py:366。

        三种固件路径(经实测区分):
          A) full_ack:aArtisanQ_PID 完整固件,CHAN/UNITS/FILT 回 '#' 确认。
          B) silent_ack:CHAN 命令被静默接受(无回包),但后续 READ 返回选定通道数据。
             这是 HB Model S 实测的固件类型 —— 功能完整,只是握手不回 '#'。
             注意:第一次 READ 可能因为通道未激活返回 0,必须先发 CHAN 才有数据。
          C) minimal:只认 READ,CHAN 完全无效,回包固定(罕见)。

        成功后设 self._initialized=True,并记录固件类型到 self.firmware_kind。
        """
        if filt is None:
            filt = [70, 70, 70, 70]
        # 路径 A:标准 '#' 握手
        if self._send_expect_ok("CHAN;0000", "CHAN 初始化"):
            return self._initialize_full(units, filt)
        # 路径 B/C 区分:发 CHAN;1200 再 READ,看是否有非零温度
        # (纯 READ 不发 CHAN 时,这块固件会回 0,所以必须用 CHAN 激活)
        print("  CHAN 未回 '#',探测是否为静默接受模式(发 CHAN;1200 + READ)...")
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._w("CHAN;1200\n")
        self.sp.flush()
        time.sleep(READ_SETTLE_SEC)
        _ack = self._readline()  # 通常是空
        probe_temps = self._read_channels_only()
        self._log(f"CHAN;1200 + READ 探测 = {probe_temps}")
        if probe_temps and any(t not in (0, -1) for t in probe_temps[1:]):
            # 通道被激活,有真实温度 → silent_ack 模式
            self.firmware_kind = "silent_ack"
            self._initialized = True
            print("  ✓ 检测到【静默握手固件】:CHAN 被接受(不回 '#'),READ 返回真实温度")
            print(f"    CHAN;1200 探测回包:{[round(t,1) for t in probe_temps]}")
            print("    UNITS/FILT 命令同理静默接受,跳过显式握手")
            return True
        # 没有真实温度 → 可能是真·最小固件,或通道确实没接热电偶
        if probe_temps:
            self.firmware_kind = "minimal"
            self._initialized = True
            print("  ⚠ 检测到【最小/无数据固件】:CHAN;1200 后 READ 仍无真实温度")
            print(f"    回包:{[round(t,1) for t in probe_temps]}")
            print("    可能原因:固件不认 CHAN,或 chan1/2 未接热电偶")
            return True
        print("  ✗ READ 无任何数据。检查波特率/接线/固件。")
        return False

    def _read_channels_only(self) -> list[float]:
        """只发 READ 并解析(不配合 CHAN),供探测用。"""
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._w("READ\n")
        self.sp.flush()
        time.sleep(READ_SETTLE_SEC)
        line = self.sp.readline().decode("utf-8", "ignore")
        line = line[:-2] if len(line) >= 2 else line.strip()
        parts = [("-1" if el.strip() == "" else el) for el in line.rsplit(",")]
        out: list[float] = []
        for p in parts:
            try:
                out.append(float(p))
            except Exception:
                out.append(-1.0)
        return out

    def _initialize_full(self, units: str, filt: list[int]) -> bool:
        """aArtisanQ_PID 完整固件握手:CHAN/UNITS/FILT。"""
        if not self._send_expect_ok(f"UNITS;{units}", "UNITS 设单位"):
            return False
        filt_str = ",".join(str(f) for f in filt)
        if not self._send_expect_ok(f"FILT;{filt_str}", "FILT 滤波"):
            return False
        self.firmware_kind = "full"
        self._initialized = True
        print("  ✓ TC4 初始化成功(aArtisanQ_PID 完整固件,对应 ArtisanZ 'TC4 initialized')")
        return True

    def _raw_read(self) -> str:
        """直接发 READ 返回一行(不解析)。给探测用。"""
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._w("READ\n")
        self.sp.flush()
        time.sleep(READ_SETTLE_SEC)
        return self._readline()

    # ── 单通道读(对齐 comm.py:7034-7042 READ 流程)──────────────────────
    def read_channels(self, channels: str) -> list[float]:
        """
        发 CHAN;<channels> 选通道再 READ,返回解析后的温度浮点列表。
        channels 为 4 位字符串,如 '3400'(ARC 主设备用法,comm.py:1859)。
        返回值里 -1 代表固件未填(对应 comm.py:7042 把空串替换为 -1)。

        固件类型行为:
          full / silent_ack:发 CHAN 选通道(静默模式下不要求 '#' 回包)
          minimal:CHAN 被忽略,READ 回固件固有顺序
        """
        # full 和 silent_ack 都发 CHAN(full 要求 '#',silent_ack 静默接受)
        if self.firmware_kind in ("full", "silent_ack"):
            self.sp.reset_input_buffer()
            self.sp.reset_output_buffer()
            self._w(f"CHAN;{channels}\n")
            self.sp.flush()
            time.sleep(READ_SETTLE_SEC)
            _ack = self._readline()  # full 模式可能是 '#...',silent_ack 为空
        # READ
        return self._read_channels_only()

    # ── PID 试探(对齐 pid_control.py:1495-1508)───────────────────────────
    def probe_pid_capability(self) -> dict[str, object]:
        """
        发 PID;LIMIT;0;100 + PID;ON,然后 READ,看回包字段数:
          - 3 个字段(ambient,ET,BT):固件不支持 PID,或 PID 没真正打开
          - 6 个字段(多了 Heater,Fan,SV):固件支持硬件 PID
        完成后会发 PID;OFF 恢复,保证扫描无副作用。
        """
        result: dict[str, object] = {"supports_pid": False, "fields": [], "heater": None,
                                      "fan": None, "sv": None, "raw": ""}
        # 不在主循环里乱开 PID;先用 LIMIT 设保守范围
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._w("PID;LIMIT;0;100\n")
        self.sp.flush()
        time.sleep(READ_SETTLE_SEC)
        ack = self._readline()
        self._log(f"Tx='PID;LIMIT;0;100'  Rx={ack!r}")
        # PID;ON
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._w("PID;ON\n")
        self.sp.flush()
        time.sleep(0.3)  # PID;ON 后给固件多点时间(比 0.1s 保守)
        ack = self._readline()
        self._log(f"Tx='PID;ON'  Rx={ack!r}")
        # READ 看字段数(对应 comm.py:7049-7051 注释)
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._w("READ\n")
        self.sp.flush()
        time.sleep(READ_SETTLE_SEC)
        line = self.sp.readline().decode("utf-8", "ignore")
        line = line[:-2] if len(line) >= 2 else line.strip()
        result["raw"] = line
        parts = [el.strip() for el in line.rsplit(",")]
        result["fields"] = parts
        self._log(f"PID 模式 READ 回包字段数={len(parts)}: {parts}")
        if len(parts) >= 6:
            result["supports_pid"] = True
            try:
                result["heater"] = float(parts[3])
            except Exception:
                pass
            try:
                result["fan"] = float(parts[4])
            except Exception:
                pass
            try:
                result["sv"] = float(parts[5])
            except Exception:
                pass
        # 务必关 PID,恢复无副作用状态(对齐 pid_control.py:1550 PID;OFF)
        self.sp.reset_input_buffer()
        self.sp.reset_output_buffer()
        self._w("PID;OFF\n")
        self.sp.flush()
        time.sleep(READ_SETTLE_SEC)
        _ = self._readline()
        return result


# ─────────────────────────────────────────────────────────────────────────────
# 扫描逻辑
# ─────────────────────────────────────────────────────────────────────────────
def scan_channels(tc4: TC4) -> list[ChannelReading]:
    """
    扫描通道接入情况。固件类型决定扫描方式:

      full / silent_ack:对 chan1~chan4 逐个发 CHAN;<chan>000 → READ,
        第 1 位即该通道温度。这是 HB Model S 实测的路径。
      minimal:CHAN 被忽略,READ 永远回固件固有顺序。改为多次 READ 看字段。
    """
    print("\n[1/2] 扫描通道接入情况")
    readings: list[ChannelReading] = []
    if tc4.firmware_kind in ("full", "silent_ack"):
        kind_label = "完整握手('#')" if tc4.firmware_kind == "full" else "静默握手(无 '#')"
        print(f"      ({kind_label}固件:CHAN;<chan>000 → READ,读第 2 位 = 通道温度)")
        print("      (回包格式 [ambient, chan_temp, chan_temp, units],ambient 在第 1 位)")
        print("      对每个通道采样 3 次取末值,排除首次激活延迟:")
        for chan in range(1, 5):
            temps: list[float] = []
            last_raw = ""
            # 采样 3 次:首次可能因刚激活读数不稳,取后两次验证一致性
            # 注意:READ 回包格式 [ambient, chan_val, chan_val, units]
            #       所以通道温度在 temps[1],不是 temps[0](后者是 ambient)
            samples_this_chan: list[float] = []
            for _attempt in range(3):
                temps = tc4.read_channels(f"{chan}000")
                last_raw = ",".join(f"{t:.1f}" for t in temps) if temps else "(无回包)"
                if temps and len(temps) >= 2 and temps[1] != -1:
                    samples_this_chan.append(temps[1])
                time.sleep(0.3)
            if not samples_this_chan:
                readings.append(ChannelReading(chan, -1.0, "(无回包)"))
                print(f"  chan{chan}: 无回包(检查接线和供电)")
                continue
            # 取最后一次有效读数作为代表
            val = samples_this_chan[-1]
            readings.append(ChannelReading(chan, val, last_raw))
            r = readings[-1]
            # 若多次采样差异大,提示不稳
            spread = max(samples_this_chan) - min(samples_this_chan) if len(samples_this_chan) > 1 else 0
            note = f"  (3次采样:{[round(x,1) for x in samples_this_chan]},波动{spread:.1f}°C)" if spread > 2 else ""
            print(f"  chan{chan}: {r.status}{note}")
        return readings
    # minimal 固件:READ 回包字段就是它支持的"通道"
    print("      (最小固件模式:READ 固定回 [ambient, ET, BT, ...],无法按通道选)")
    print("      连续 5 次 READ 看温度是否稳定/变化:")
    samples: list[list[float]] = []
    for i in range(5):
        temps = tc4.read_channels("0000")  # CHAN 参数被忽略
        if temps:
            samples.append(temps)
            label = _interpret_read_fields(temps)
            print(f"        #{i+1}: {[round(t,1) for t in temps]}  → {label}")
        time.sleep(0.5)
    if samples:
        last = samples[-1]
        names = ["ambient", "ET", "BT", "chan3/Heater?", "chan4/Fan?", "SV?"]
        for idx, t in enumerate(last):
            name = names[idx] if idx < len(names) else f"field{idx}"
            r = ChannelReading(idx + 1, t, f"field{idx}={t}")
            print(f"  field[{idx}] ({name}): {_temp_status(t)}")
            readings.append(r)
    return readings


def _temp_status(temp: float) -> str:
    """单温度值的状态描述(给最小固件字段展示用)。"""
    if temp == -1:
        return "NO_DATA"
    if not (REALISTIC_TEMP_MIN <= temp <= REALISTIC_TEMP_MAX):
        return f"OUT_OF_RANGE ({temp}°C,可能未接)"
    if 0 <= temp <= 1.5:
        return f"近 0°C ({temp}°C,可能未接热电偶)"
    return f"OK 实测 {temp:.1f}°C"


def _interpret_read_fields(temps: list[float]) -> str:
    """对最小固件 READ 回包字段数给出语义解读。"""
    n = len(temps)
    if n == 3:
        return "3 字段 = [ambient, ET, BT](aArtisan 早期只读固件)"
    if n == 4:
        return "4 字段 = [ambient, ET, BT, units] 或 [ambient, ET, BT, chan3]"
    if n >= 6:
        return f"{n} 字段 = 可能含 Heater/Fan/SV(支持硬件 PID!)"
    return f"{n} 字段"


def scan_pid(tc4: TC4) -> None:
    """
    探测固件 PID 能力。会发 PID;ON 再 PID;OFF,扫描完无副作用。
    """
    print("\n[2/2] 探测固件硬件 PID 能力")
    print("      (PID;ON 后 READ 回包从 3 字段→6 字段则支持,见 comm.py:7051)")
    res = tc4.probe_pid_capability()
    if res["supports_pid"]:
        print("  ✓ 固件支持硬件 PID(aArtisanQ_PID 或同源固件)")
        print(f"    当前 Heater={res['heater']}%  Fan={res['fan']}%  SV={res['sv']}°C")
        print(f"    原始回包: {res['raw']}")
        print("  → 在 ArtisanZ 里把 device 改成 19(Arduino TC4)+ 勾 PID 即可用火力控制")
    else:
        print("  ✗ 固件不支持硬件 PID(READ 回包字段数 < 6)")
        print(f"    原始回包: {res['raw']}")
        print("  → 若要火力控制,需烧录 aArtisanQ_PID 固件,或机器另接 MODBUS PID 板")


def probe_control_write(tc4: TC4) -> None:
    """
    显式 --control 时才执行:发 PID;SV 试探写控制。
    会短暂改 SV,但随后 PID;OFF 不会真的驱动火力(火力由 PID 算法在 PID;ON 时才输出)。
    """
    print("\n[3/3] 试探写控制(PID;SV)")
    print("      警告:此步会发 PID;SV;100。固件若支持,SV 会被设为 100°C。")
    print("            不会自动 PID;ON,因此不会真的驱动加热器。")
    # 先确保 PID 关
    tc4.sp.reset_input_buffer()
    tc4.sp.reset_output_buffer()
    tc4._w("PID;OFF\n")
    tc4.sp.flush()
    time.sleep(READ_SETTLE_SEC)
    _ = tc4._readline()
    # 发 SV
    tc4.sp.reset_input_buffer()
    tc4.sp.reset_output_buffer()
    tc4._w("PID;SV;100\n")
    tc4.sp.flush()
    time.sleep(READ_SETTLE_SEC)
    ack = tc4._readline()
    print(f"    Tx='PID;SV;100'  Rx={ack!r}")
    if ack.startswith("#"):
        print("  ✓ 写 SV 成功(固件确认 '#'),控制通道可用")
    else:
        print("  ✗ 写 SV 无效,固件可能不支持或未初始化")


def pick_port(explicit: str | None) -> str:
    if explicit:
        return explicit
    ports = list(serial.tools.list_ports.comports())
    # 优先选 USB Serial(CH340/CH341 是 TC4 板典型芯片)
    candidates = [p for p in ports if "USB" in (p.description or "").upper()
                  or p.vid in (0x1A86, 0x0403, 0x2341)]  # CH34x / FTDI / Arduino
    if not candidates:
        # 退而求其次:任何非 Bluetooth 的
        candidates = [p for p in ports if "bluetooth" not in (p.description or "").lower()]
    if not candidates:
        print("错误:未发现任何可用串口。请用 -p 显式指定。", file=sys.stderr)
        sys.exit(2)
    chosen = candidates[0]
    print(f"自动选择串口:{chosen.device}({chosen.description})")
    print(f"  其他可用串口:{[p.device for p in ports]}")
    return chosen.device


def main() -> int:
    ap = argparse.ArgumentParser(
        description="TC4 通道与固件能力扫描器(ArtisanZ 配套诊断工具)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("-p", "--port", help="串口设备路径(不填则自动选第一个 USB 串口)")
    ap.add_argument("-b", "--baudrate", type=int, default=HB_MODEL_S_BAUDRATE,
                    help=f"波特率(默认 {HB_MODEL_S_BAUDRATE},取自 Model_S.aset)")
    ap.add_argument("--units", default="C", choices=["C", "F"], help="温度单位")
    ap.add_argument("--no-pid", action="store_true",
                    help="只扫通道,不发 PID;ON(对只读固件最安全)")
    ap.add_argument("--control", action="store_true",
                    help="额外发 PID;SV;100 试探写控制(默认关闭)")
    ap.add_argument("-q", "--quiet", action="store_true", help="少打 Tx/Rx 调试日志")
    args = ap.parse_args()

    port = pick_port(args.port)

    print("\n=== TC4 扫描开始 ===")
    print(f"目标:{port} @ {args.baudrate}/8N1  单位={args.units}")
    print("参考:Model_S.aset 用 115200,Standard.aset 用 9600")

    tc4: TC4 | None = None
    try:
        tc4 = TC4(port, baudrate=args.baudrate, verbose=not args.quiet)
        # 初始化
        if not tc4.initialize(units=args.units):
            print("\n初始化失败。可能原因:")
            print("  1. 波特率不对(试试 -b 9600 或 -b 19200)")
            print("  2. 不是 TC4 固件(可能刷了其他固件)")
            print("  3. 接线/供电问题")
            return 1

        # 扫描通道
        readings = scan_channels(tc4)
        ok_channels = [r.channel for r in readings if r.is_realistic]
        print(f"\n  小结:实测接了热电偶的通道 = {ok_channels or '无'}")

        # 对照 Model_S.aset 当前配置的解读
        print("\n[对照] Model_S.aset 当前(device=126 ARC BT/ET)的通道映射:")
        print("  ARC_BTET  发 CHAN;3400 → chan3=BT, chan4=ET/Drum  (comm.py:1859)")
        print("  ARC_METIT 发 CHAN;1200 → chan1=MET/Exhaust, chan2=IT (comm.py:1875)")
        if tc4.firmware_kind == "minimal":
            print("  ⚠ 当前是【最小只读固件】,不认 CHAN 命令,ARC 的两路通道切换不会生效。")
            print("    建议改用 device=19(Arduino TC4)并配合通道下拉,或刷新固件为 aArtisanQ_PID。")
        elif tc4.firmware_kind == "silent_ack":
            print("  ✓ 当前【静默握手固件】认 CHAN 命令(只是不回 '#'),ARC 通道切换会生效。")
            print("    但 ArtisanZ 的 comm.py:7003 要求 CHAN 回 '#',否则抛 'Arduino could not")
            print("    set channels' 异常 → 实际连 ArtisanZ 主程序时这里可能报错。")
            print("    若 ArtisanZ 报该错,可在 comm.py:7003 放宽判定(空回包也算成功)。")
        else:
            print("  把上方实测结果跟这个映射对照,即可知道你机器的物理接线是否匹配。")

        # PID 探测
        if not args.no_pid:
            if tc4.firmware_kind == "minimal":
                print("\n[2/2] 跳过 PID 探测(最小固件不认 PID;ON 命令,必然不支持硬件 PID)")
                print("      → 若要火力控制,需烧录 aArtisanQ_PID 固件,或机器另接 MODBUS PID 板")
            else:
                scan_pid(tc4)  # full 和 silent_ack 都试(silent_ack 可能也静默支持)
        else:
            print("\n[2/2] 跳过 PID 探测(--no-pid)")

        # 写控制试探
        if args.control:
            if tc4.firmware_kind == "minimal":
                print("\n[3/3] 跳过写控制试探(最小固件不认 PID;SV 命令)")
            else:
                probe_control_write(tc4)  # silent_ack 也试,可能静默接受 PID;SV

        print("\n=== 扫描结束 ===")
        return 0
    except serial.SerialException as e:
        print(f"\n串口错误:{e}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("\n用户中断")
        return 130
    finally:
        if tc4 is not None:
            tc4.close()
            print("(串口已关闭)")


if __name__ == "__main__":
    sys.exit(main())
