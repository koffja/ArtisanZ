#!/usr/bin/env python3
"""
烘焙机寄存器"受控实验"工具。

工作原理:
  1. 记录当前所有寄存器的基线值
  2. 提示你在烘焙机上做一个动作 (调风门、改火力、启动...)
  3. 持续读取, 找出哪个寄存器发生了变化
  4. 这样就能精确锁定 "这个动作对应哪个寄存器"

用法:
  python3 roaster_diff.py
"""

from __future__ import annotations
import socket
import struct
import sys
import time

HOST = "192.168.10.100"
PORT = 1053
UNIT = 1
TOTAL_REGS = 28  # HR[0..27]


def read_all_regs(host: str = HOST, port: int = PORT, unit: int = UNIT,
                  timeout: float = 2.0) -> list[int] | None:
    """读取 HR[0..27] 全部 28 个寄存器。"""
    regs: list[int] = []
    for start, count in [(0, 11), (11, 17)]:
        try:
            with socket.create_connection((host, port), timeout=timeout) as s:
                s.settimeout(timeout)
                req = struct.pack(">HHHB", 1, 0, 6, unit) + struct.pack(">BHH", 3, start, count)
                s.sendall(req)
                resp = s.recv(1024)
                if len(resp) < 9 or resp[7] & 0x80:
                    return None
                byte_count = resp[8]
                for i in range(9, 9 + byte_count, 2):
                    regs.append(struct.unpack(">H", resp[i:i+2])[0])
        except OSError:
            return None
    return regs


def show_diff(baseline: list[int], current: list[int], label: str = "") -> list[int]:
    """对比基线, 显示变化的寄存器。"""
    changed = []
    print(f"\n  变化 ({label}):" if label else "\n  变化:")
    any_change = False
    for addr in range(min(len(baseline), len(current))):
        if baseline[addr] != current[addr]:
            any_change = True
            changed.append(addr)
            delta = current[addr] - baseline[addr]
            print(f"    HR[{addr:2}] = {baseline[addr]:5} → {current[addr]:5}  "
                  f"(Δ={delta:+})")
    if not any_change:
        print(f"    (没有寄存器变化)")
    return changed


def main() -> None:
    print(f"\n=== 烘焙机寄存器受控实验 ({HOST}:{PORT}) ===")
    print("这个工具帮你精确锁定每个寄存器对应什么物理量。\n")

    # 测连通
    test = read_all_regs()
    if test is None:
        print(f"✗ 连不上 {HOST}:{PORT}")
        print("  检查烘焙机是否在线、你的 IP 是否和 .100 冲突")
        sys.exit(1)
    print(f"✓ 连接成功, 当前 HR[0..27]:")
    for i, v in enumerate(test):
        marker = " ← 有值" if v != 0 else ""
        print(f"    HR[{i:2}] = {v:5}{marker}")

    while True:
        print("\n" + "=" * 60)
        print("请按提示操作烘焙机。每个实验可以重复多次以提高置信度。")
        print("=" * 60)

        # 1. 记录基线
        print("\n[步骤1] 不要动烘焙机, 让它稳定几秒...")
        time.sleep(2)
        baseline = read_all_regs()
        if baseline is None:
            print("✗ 读取失败"); continue
        print(f"  基线已记录 ({time.strftime('%H:%M:%S')})")
        for i, v in enumerate(baseline):
            if v != 0:
                print(f"    HR[{i:2}] = {v}")

        # 2. 等待用户操作
        action = input("\n[步骤2] 现在去做一个动作 (如: 调风门到50%→"
                       "回车开始监控, 或输入动作描述: ").strip()
        if not action:
            action = "(用户操作)"
        print(f"\n  监控中... 做你的动作, 按 Ctrl+C 结束本次实验")
        print(f"  动作: {action}")

        # 3. 持续监控, 找变化
        seen_changes: dict[int, list] = {i: [] for i in range(TOTAL_REGS)}
        try:
            t0 = time.time()
            while time.time() - t0 < 30:
                cur = read_all_regs()
                if cur is None:
                    time.sleep(0.5); continue
                changed = show_diff(baseline, cur, label=f"+{int(time.time()-t0)}s")
                for addr in changed:
                    seen_changes[addr].append(cur[addr])
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\n  结束监控")

        # 4. 总结这次实验
        print("\n[结果] 这次动作影响的寄存器:")
        for addr, vals in seen_changes.items():
            if vals:
                unique = sorted(set(vals))
                print(f"  HR[{addr:2}] 变化值序列: {vals}")
                print(f"         唯一值: {unique}")
                print(f"         → 这个寄存器很可能对应: {action}")

        again = input("\n再做一次实验? (y/N): ").strip().lower()
        if again != 'y':
            print("\n实验结束。把上面的结果发给分析。")
            break


if __name__ == "__main__":
    main()
