#!/usr/bin/env python3
"""
针对你的烘焙机 (192.168.10.100:1053, Modbus TCP) 的精确数据读取脚本。

完全复现操控电脑的轮询模式：
  - 每 3 秒读一次 HR[0..10] 和 HR[11..27]
  - 持续显示每个寄存器的值变化
  - 自动识别哪些寄存器是温度（变化的）、哪些是设定值（稳定的）

用法:
  python3 roaster_sniff.py                    # 默认 192.168.10.100:1053
  python3 roaster_sniff.py --host 192.168.10.100 --port 1053
  python3 roaster_sniff.py --count 20         # 读 20 轮后停
  python3 roaster_sniff.py --log data.txt     # 同时写日志
"""

from __future__ import annotations
import argparse
import socket
import struct
import sys
import time
from collections import defaultdict


HOST = "192.168.10.100"
PORT = 1053
UNIT = 1

# 操控电脑读的两个块
BLOCK_A = (0, 11)    # HR[0..10]
BLOCK_B = (11, 17)   # HR[11..27]


def read_holding_registers(host: str, port: int, unit: int,
                           start: int, count: int, timeout: float = 2.0):
    """读 Modbus 保持寄存器, 返回 int 列表或错误字符串。"""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            # MBAP: txn=1, proto=0, length=6, unit
            # PDU: func=3 (read HR), start, count
            req = struct.pack(">HHHB", 1, 0, 6, unit) + struct.pack(">BHH", 3, start, count)
            s.sendall(req)
            resp = s.recv(1024)
            if len(resp) < 9:
                return f"短响应 ({len(resp)}B)"
            txn, proto, length, unit_r = struct.unpack(">HHHB", resp[:7])
            func = resp[7]
            if func & 0x80:
                return f"Modbus 异常 code={resp[8]}"
            byte_count = resp[8]
            regs = [struct.unpack(">H", resp[i:i+2])[0]
                    for i in range(9, 9 + byte_count, 2)]
            return regs
    except ConnectionRefusedError:
        return "连接被拒 (端口没开或 IP 冲突)"
    except socket.timeout:
        return "超时 (设备不响应)"
    except OSError as e:
        return f"网络错误: {e}"


def fmt_val(v: int) -> str:
    """格式化单个寄存器值, 多种解读。"""
    # 16-bit signed
    v_signed = v - 65536 if v >= 32768 else v
    # 0.1°C 解读
    c1 = v_signed / 10.0
    # 0.01 解读
    c2 = v_signed / 100.0
    return f"{v:5d} (s={v_signed:6d}, /10={c1:7.1f}, /100={c2:8.2f})"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="针对 192.168.10.100:1053 烘焙机的 Modbus 数据读取",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--unit", type=int, default=UNIT)
    ap.add_argument("--count", type=int, default=0, help="读几轮 (0=无限, Ctrl+C 停)")
    ap.add_argument("--interval", type=float, default=3.0, help="轮询间隔秒")
    ap.add_argument("--log", help="同时写日志到这个文件")
    args = ap.parse_args()

    log_fp = open(args.log, "a", encoding="utf-8") if args.log else None

    print(f"\n=== 烘焙机数据读取 {args.host}:{args.port} unit={args.unit} ===")
    print(f"轮询: HR[0..10] + HR[11..27], 间隔 {args.interval}s")
    print(f"停止: Ctrl+C\n")

    # 跟踪每个寄存器的变化次数 (用于识别温度 vs 设定值)
    history: dict[int, list[int]] = defaultdict(list)
    round_num = 0

    try:
        while args.count == 0 or round_num < args.count:
            round_num += 1
            ts = time.strftime("%H:%M:%S")
            print(f"\n--- 第 {round_num} 轮 @ {ts} ---")

            all_regs: dict[int, int] = {}
            for label, (start, count) in [("A HR[0..10]", BLOCK_A), ("B HR[11..27]", BLOCK_B)]:
                result = read_holding_registers(args.host, args.port, args.unit,
                                                start, count)
                if isinstance(result, str):
                    print(f"  {label}: ✗ {result}")
                    if log_fp:
                        log_fp.write(f"[{ts}] round={round_num} block={label} ERROR: {result}\n")
                        log_fp.flush()
                else:
                    # 展示每个寄存器
                    for i, v in enumerate(result):
                        addr = start + i
                        all_regs[addr] = v
                        history[addr].append(v)
                    vals_str = " ".join(f"[{start+i}]={v}" for i, v in enumerate(result))
                    print(f"  {label}: {vals_str}")
                    if log_fp:
                        log_fp.write(f"[{ts}] round={round_num} block={label}: {result}\n")
                        log_fp.flush()

            if args.count == 0 or round_num < args.count:
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n\n停止。")

    # 汇总: 哪些寄存器在变 (温度类), 哪些稳定 (设定值类)
    print("\n" + "=" * 70)
    print("寄存器变化分析 (区分温度/设定值):")
    print("=" * 70)
    print(f"{'地址':<6} {'采样次数':<10} {'最小值':<10} {'最大值':<10} {'变化次数':<10} {'解读'}")
    print("-" * 70)
    for addr in sorted(history.keys()):
        vals = history[addr]
        if not vals:
            continue
        unique_count = len(set(vals))
        v_min, v_max = min(vals), max(vals)
        # 变化多 = 可能是温度; 稳定 = 可能是设定值/状态
        if unique_count <= 1:
            kind = "稳定 (设定值/常量)"
        elif unique_count <= 3:
            kind = "少量变化 (状态位?)"
        else:
            kind = "★ 频繁变化 (温度/实时值)"
        print(f"HR[{addr:<3}] {len(vals):<10} {v_min:<10} {v_max:<10} {unique_count:<10} {kind}")

    if log_fp:
        log_fp.close()
        print(f"\n日志已写入: {args.log}")


if __name__ == "__main__":
    main()
