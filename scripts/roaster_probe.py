#!/usr/bin/env python3
"""
烘焙机协议探测脚本 (Roaster Protocol Probe)
============================================

用途：当你不知道烘焙机的 IP、端口、协议时，把这台电脑接到烘焙机所在的
      局域网，跑这个脚本，自动找出烘焙机并判断它用什么协议通信。

零依赖：只用 Python 标准库 (socket / struct / concurrent.futures / argparse)
        不需要 pymodbus / scapy / nmap，复制到任何机器都能跑。

覆盖的协议指纹（基于 ArtisanZ 源码）：
  - Modbus TCP   (标准 502 端口, MBAP 头 00 00 00 00 00 06 <unit> <func>)
  - Santoker TCP (8080/20001 端口, 帧头 EE A5, 命令头 02 04, RTU CRC)
  - 通用 TCP 服务发现 (其他自定义协议的兜底)

用法：
  # 1. 自动探测整个网段（推荐先跑这个）
  python3 roaster_probe.py scan 192.168.10.0/24

  # 2. 已知 IP，深入测试某个设备
  python3 roaster_probe.py probe 192.168.10.2

  # 3. 已知 IP+端口，作为客户端持续读取数据（验证用）
  python3 roaster_probe.py read 192.168.10.2 502 --modbus --unit 1

  # 4. 监听模式（让烘焙机主动连过来，用于发现它是不是 server）
  python3 roaster_probe.py listen 0.0.0.0 9000

注意：
  - 本脚本只做"读取"和"探测"，不发送任何控制命令（不会误触发加热/下豆）。
  - 所有 Modbus 操作都是 Read Holding Registers (func 3)，只读不写。
"""

from __future__ import annotations

import argparse
import ipaddress
import socket
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# ============================================================
# 颜色输出（兼容关闭）
# ============================================================
class C:
    """ANSI 颜色，非 TTY 时自动退化。"""
    def __init__(self) -> None:
        self._ok = sys.stdout.isatty()
    def _w(self, s: str, c: str) -> str:
        return f"{c}{s}\033[0m" if self._ok else s
    def red(self, s: str) -> str:    return self._w(s, "\033[31m")
    def green(self, s: str) -> str:  return self._w(s, "\033[32m")
    def yellow(self, s: str) -> str: return self._w(s, "\033[33m")
    def blue(self, s: str) -> str:   return self._w(s, "\033[34m")
    def cyan(self, s: str) -> str:   return self._w(s, "\033[36m")
    def bold(self, s: str) -> str:   return self._w(s, "\033[1m")

c = C()


def hexdump(data: bytes, prefix: str = "    ") -> str:
    """十六进制 + ASCII dump，方便看原始字节。"""
    if not data:
        return f"{prefix}(empty)"
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{prefix}{i:04x}  {hex_part:<48}  {ascii_part}")
    return "\n".join(lines)


# ============================================================
# 协议指纹：Modbus TCP
# ============================================================

def modbus_crc16(data: bytes) -> int:
    """Modbus RTU CRC-16（用于 Santoker 校验，也用于 RTU over TCP）。"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


def build_modbus_tcp_read(unit: int, func: int, start: int, count: int,
                          transaction_id: int = 0x0001) -> bytes:
    """
    构造 Modbus TCP 读请求。
    MBAP header: transaction(2) + protocol(2,固定0) + length(2) + unit(1)
    PDU: func(1) + start_addr(2) + quantity(2)
    """
    protocol_id = 0x0000
    pdu = struct.pack(">BHH", func, start, count)
    length = len(pdu) + 1  # +1 for unit id
    mbap = struct.pack(">HHHB", transaction_id, protocol_id, length, unit)
    return mbap + pdu


def parse_modbus_tcp_response(resp: bytes, expected_txn: int | None = None,
                              requested_func: int | None = None,
                              requested_count: int | None = None) -> dict | None:
    """
    严格解析 Modbus TCP 响应。
    做完整的协议一致性校验，避免把 SSH/HTTP banner 误判为 Modbus。
    """
    # Modbus TCP 最小响应长度: MBAP(7) + func(1) = 8; 读响应还要 byte_count(1)
    if len(resp) < 9:
        return None
    try:
        txn, proto, length, unit = struct.unpack(">HHHB", resp[:7])
        func = resp[7]

        # === 严格一致性校验（防止误判）===
        # 1. protocol id 必须为 0 (Modbus)
        if proto != 0x0000:
            return None
        # 2. transaction id 应该回显我们发的（如果调用方提供了）
        if expected_txn is not None and txn != expected_txn:
            return None
        # 3. length 字段要和实际 payload 对得上
        #    length 字段 = unit(1) + func(1) + 后续数据
        if length + 6 != len(resp) and len(resp) < length + 6:
            # 实际包可能比 length 多（粘包）或正好；不能比 length 声明的少
            return None

        if func & 0x80:  # 异常响应
            if len(resp) < 9:
                return None
            exc_code = resp[8]
            # 异常响应的 length 必须是 3 (unit + func + exc_code)
            if length != 3:
                return None
            # 异常 func 应该回显请求 func + 0x80
            if requested_func is not None and (func & 0x7F) != requested_func:
                return None
            return {
                "ok": False,
                "type": "modbus_exception",
                "func": func & 0x7F,
                "exception_code": exc_code,
                "exception_name": MODBUS_EXCEPTIONS.get(exc_code, f"unknown({exc_code})"),
            }

        # 正常读响应
        byte_count = resp[8]
        # 4. byte_count 必须是偶数（寄存器是 16-bit）
        if byte_count % 2 != 0:
            return None
        # 5. byte_count 要和 requested_count 对得上 (count*2)
        if requested_count is not None and byte_count != requested_count * 2:
            return None
        # 6. func 必须是已知读功能码 (1/2/3/4)
        if func not in (1, 2, 3, 4):
            return None
        # 7. length 字段 = unit(1) + func(1) + byte_count(1) + data
        if length != 3 + byte_count:
            return None

        reg_values = []
        for i in range(9, 9 + byte_count, 2):
            if i + 1 < len(resp):
                reg_values.append(struct.unpack(">H", resp[i:i+2])[0])
        return {
            "ok": True,
            "type": "modbus",
            "func": func,
            "byte_count": byte_count,
            "registers": reg_values,
        }
    except (struct.error, IndexError):
        return None


MODBUS_EXCEPTIONS = {
    1: "Illegal Function",
    2: "Illegal Data Address",
    3: "Illegal Data Value",
    4: "Slave Device Failure",
    5: "Acknowledge",
    6: "Slave Device Busy",
    8: "Memory Parity Error",
    10: "Gateway Path Unavailable",
    11: "Gateway Target No Response",
}


def try_modbus_tcp(host: str, port: int = 502, unit: int = 1,
                   timeout: float = 1.0) -> dict | None:
    """
    尝试以 Modbus TCP 客户端身份连接 host:port。
    发一个 Read Holding Registers (func 3) 读寄存器 0~9。
    返回 dict 包含识别结果，或 None。

    使用非默认 transaction_id + 严格响应校验，避免把 SSH/HTTP banner
    误判为 Modbus。
    """
    import random
    txn = random.randint(0x1000, 0x7FFF)  # 非默认 0x0001, 防止偶合
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            # 读前 10 个保持寄存器 (Holding Register, func 3)
            req = build_modbus_tcp_read(unit, 3, 0, 10, transaction_id=txn)
            s.sendall(req)
            resp = s.recv(1024)
            if not resp:
                return None
            parsed = parse_modbus_tcp_response(
                resp, expected_txn=txn, requested_func=3, requested_count=10,
            )
            if parsed is None:
                return {"ok": False, "type": "modbus_malformed", "raw": resp}
            parsed["host"] = host
            parsed["port"] = port
            parsed["unit"] = unit
            return parsed
    except (OSError, ConnectionError):
        return None


# ============================================================
# 协议指纹：Santoker (自定义 TCP, 0xEE 0xA5 帧头)
# ============================================================

SANTOKER_HEADER_WIFI = b"\xEE\xA5"
SANTOKER_HEADER_BT = b"\xEE\xB5"
SANTOKER_CODE_HEADER = b"\x02\x04"


def build_santoker_query() -> bytes:
    """
    构造一个 Santoker 查询包（基于 ArtisanZ santoker.py 帧格式）。
    帧结构: HEADER(2) + CODE_HEADER(2) + LEN(2) + DATA + CRC(2)
    我们发一个最小的"读状态"查询（LEN=0 的心跳/查询）。
    注意：Santoker 协议需要正确的命令字才能拿到有意义的数据。
          这里先发握手探测包，确认服务器是不是 Santoker。
    """
    header = SANTOKER_HEADER_WIFI
    code_header = SANTOKER_CODE_HEADER
    data = b""  # 空数据查询
    data_len = struct.pack(">H", len(data))
    crc = modbus_crc16(code_header + data_len + data)
    return header + code_header + data_len + data + struct.pack(">H", crc)


def parse_santoker_response(resp: bytes) -> dict | None:
    """
    尝试按 Santoker 帧格式解析响应。
    返回 None 表示"不是 Santoker"（帧头不匹配）；
    返回 ok=False dict 表示"是 Santoker 但帧内容有问题"。
    """
    # Santoker 最小帧: HEADER(2) + CODE(2) + LEN(2) + CRC(2) = 8 字节
    if len(resp) < 8:
        return None
    # 检查帧头（不匹配就返回 None, 而不是 malformed）
    if resp[:2] == SANTOKER_HEADER_WIFI:
        header_name = "WIFI(EE A5)"
    elif resp[:2] == SANTOKER_HEADER_BT:
        header_name = "BT(EE B5)"
    else:
        return None
    if resp[2:4] != SANTOKER_CODE_HEADER:
        return {"ok": False, "type": "santoker_bad_code", "raw": resp}
    try:
        data_len = struct.unpack(">H", resp[4:6])[0]
        data = resp[6:6+data_len]
        crc_recv = struct.unpack(">H", resp[6+data_len:8+data_len])[0] if len(resp) >= 8+data_len else 0
        crc_calc = modbus_crc16(resp[2:6+data_len])
        return {
            "ok": True,
            "type": "santoker",
            "header": header_name,
            "data_len": data_len,
            "data": data,
            "crc_ok": crc_recv == crc_calc,
        }
    except (struct.error, IndexError):
        return None


def try_santoker(host: str, port: int = 8080, timeout: float = 1.0) -> dict | None:
    """
    尝试以 Santoker 客户端身份连接。
    - 帧头 EE A5 / EE B5 匹配但内容异常 → 返回 ok=False dict（疑似 Santoker）
    - 响应根本不是 Santoker（如 SSH/HTTP banner）→ 返回 None（明确不是）
    """
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall(build_santoker_query())
            try:
                resp = s.recv(1024)
            except socket.timeout:
                return None  # 连得上但不回应，不算 Santoker
            if not resp:
                return None
            parsed = parse_santoker_response(resp)
            if parsed is None:
                # 帧头都不匹配，明确不是 Santoker
                return None
            parsed["host"] = host
            parsed["port"] = port
            return parsed
    except (OSError, ConnectionError):
        return None


# ============================================================
# 通用 TCP 探测（兜底，识别未知协议）
# ============================================================

# 常见烘焙机/PLC 端口（基于 ArtisanZ + 业界经验）
COMMON_PORTS = {
    502:   "Modbus TCP (标准)",
    8080:  "Santoker / HTTP-alt / 自定义",
    20001: "Santoker (默认 AP 模式)",
    23:    "Telnet (老式 PLC 调试)",
    80:    "HTTP (Web 配置界面)",
    443:   "HTTPS",
    4840:  "OPC UA",
    502:   "Modbus",
    47808: "BACnet",
    9100:  "打印/自定义",
    3000:  "Node-RED / Grafana",
    8888:  "自定义",
    8000:  "HTTP-alt",
    5555:  "调试",
}


def tcp_connect_probe(host: str, port: int, timeout: float = 0.8) -> bool:
    """TCP connect 探测端口是否开放。"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionError):
        return False


def grab_banner(host: str, port: int, timeout: float = 1.0,
                payload: bytes = b"") -> bytes | None:
    """
    连接后发送 payload，抓取返回的 banner / 响应。
    payload 为空则被动等待 banner。
    """
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            if payload:
                s.sendall(payload)
            try:
                return s.recv(4096)
            except socket.timeout:
                return b""  # 连上了但没回应
    except (OSError, ConnectionError):
        return None


def fingerprint_port(host: str, port: int, timeout: float = 1.0) -> dict:
    """对一个开放端口做协议指纹识别。"""
    info: dict = {"port": port, "open": True, "protocols": []}

    # 1. Modbus TCP（任何端口都可能跑，不限于 502）
    if port in (502, 1502, 10502) or True:
        for unit in (1, 0, 247, 100):
            r = try_modbus_tcp(host, port, unit=unit, timeout=timeout)
            if r and r.get("ok"):
                info["protocols"].append({
                    "name": "Modbus TCP",
                    "detail": r,
                    "unit_found": unit,
                })
                break
            elif r and r.get("type") == "modbus_exception":
                info["protocols"].append({
                    "name": "Modbus TCP (异常响应, 说明是 Modbus 但参数不对)",
                    "detail": r,
                })
                break

    # 2. Santoker（端口不固定，对所有开放端口都试一次；
    #    但 Santoker 帧头 EE A5 极特殊，不会和别的协议冲突）
    r = try_santoker(host, port, timeout=timeout)
    if r and r.get("ok"):
        info["protocols"].append({"name": "Santoker", "detail": r})
    elif r and r.get("ok") is False and "santoker" in str(r.get("type", "")):
        # 帧头匹配但内容异常 → 几乎确定是 Santoker，只是参数没对上
        info["protocols"].append({
            "name": "Santoker (帧头匹配, 内容异常)",
            "detail": r,
        })

    # 3. 通用 banner grab
    banner = grab_banner(host, port, timeout=timeout)
    if banner:
        info["banner"] = banner
        # HTTP 识别
        if banner[:5] in (b"HTTP/", b"http/"):
            info["protocols"].append({"name": "HTTP", "detail": "Web 配置界面"})
        # 识别首字节特征
        if len(banner) >= 2:
            head = banner[:2]
            if head == b"\xEE\xA5":
                info["protocols"].append({"name": "Santoker-like (EE A5)", "detail": banner})
            elif head == b"\xEE\xB5":
                info["protocols"].append({"name": "Santoker-BT (EE B5)", "detail": banner})

    return info


# ============================================================
# 命令：scan — 网段扫描
# ============================================================

def cmd_scan(cidr: str, ports: list[int] | None = None, timeout: float = 0.8) -> None:
    """扫描整个网段，找出开放端口和设备指纹。"""
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError as e:
        print(c.red(f"网段格式错误: {e}"))
        sys.exit(2)

    if ports is None:
        ports = sorted(COMMON_PORTS.keys())

    print(c.bold(f"\n=== 扫描网段 {cidr} ({net.num_addresses} 个地址) ==="))
    print(c.cyan(f"探测端口: {ports}"))
    print(c.cyan(f"超时: {timeout}s （慢的话可以调小）\n"))

    hosts_up: list[str] = []
    host_details: dict[str, list[dict]] = {}

    # 第 1 阶段：并发主机发现
    # 直接用目标端口集探活（不限于 80/443），避免漏掉只开 502/8080 的 IoT 设备
    print(c.yellow(f"阶段 1/2: 主机发现 (TCP 探测端口 {ports}) ..."))
    t0 = time.time()

    def host_alive(h: str) -> tuple[str, bool]:
        # 先试目标端口集合里的几个代表端口
        for p in ports:
            if tcp_connect_probe(h, p, timeout=timeout):
                return h, True
        # 再试常见探活端口（80/443/22/139）
        for p in (80, 443, 22, 139):
            if tcp_connect_probe(h, p, timeout=timeout):
                return h, True
        return h, False

    with ThreadPoolExecutor(max_workers=64) as ex:
        futs = {ex.submit(host_alive, str(ip)): str(ip) for ip in net.hosts()}
        for fut in as_completed(futs):
            h, alive = fut.result()
            if alive:
                hosts_up.append(h)
                print(f"  {c.green('[UP]')} {h}")

    if not hosts_up:
        print(c.red("\n没有发现任何活动主机。可能原因："))
        print("  - 你电脑不在该网段（用 ifconfig 检查）")
        print("  - 路由器开了 AP 隔离 (AP Isolation)")
        print("  - 设备防火墙不响应 TCP connect（部分 PLC 会这样）")
        print(c.yellow("\n建议改用 probe 命令直接试具体 IP："))
        print("  python3 roaster_probe.py probe <烘焙机IP>")
        return

    print(f"\n{c.green(f'发现 {len(hosts_up)} 台主机')}, 耗时 {time.time()-t0:.1f}s")

    # 第 2 阶段：对存活主机扫常见 PLC 端口
    print(c.yellow("\n阶段 2/2: 端口扫描 + 协议指纹 ..."))
    for h in sorted(hosts_up, key=lambda x: tuple(map(int, x.split('.')))):
        open_ports = []
        for port in ports:
            if tcp_connect_probe(h, port, timeout=timeout):
                open_ports.append(port)
        if open_ports:
            host_details[h] = []
            for port in open_ports:
                info = fingerprint_port(h, port, timeout=timeout)
                host_details[h].append(info)
            print(f"\n{c.bold(c.green(h))} 开放端口: {open_ports}")
            for info in host_details[h]:
                proto_str = ", ".join(p["name"] for p in info.get("protocols", [])) or "未知"
                port_label = COMMON_PORTS.get(info["port"], "")
                print(f"  :{c.cyan(str(info['port']))} {port_label} → {proto_str}")
                if "banner" in info:
                    print(c.blue(f"      banner:"))
                    print(hexdump(info["banner"], prefix="        "))
                for p in info.get("protocols", []):
                    if "detail" in p and isinstance(p["detail"], dict):
                        d = p["detail"]
                        if d.get("type") == "modbus" and d.get("registers"):
                            print(c.green(f"      Modbus 寄存器[0..]: {d['registers']}"))
                        elif d.get("type") == "santoker":
                            print(c.green(f"      Santoker 响应数据: {d.get('data', b'').hex()}"))

    # 汇总
    print(c.bold(f"\n=== 扫描完成 ==="))
    print(f"存活主机: {len(hosts_up)}")
    plcs = []
    for h, infos in host_details.items():
        for info in infos:
            for p in info.get("protocols", []):
                if p["name"].startswith(("Modbus", "Santoker")):
                    plcs.append((h, info["port"], p["name"]))
    if plcs:
        print(c.green(f"\n识别到的烘焙机/PLC:"))
        for h, port, name in plcs:
            print(f"  {c.bold(h)}:{port} → {name}")
        print(c.yellow("\n下一步：用 probe 命令深入测试"))
        for h, port, name in plcs:
            print(f"  python3 roaster_probe.py probe {h}")
    else:
        print(c.yellow("没自动识别出 Modbus/Santoker。"))
        print("可能协议特殊。建议用 listen 模式被动等待，或在操控电脑上抓包。")


# ============================================================
# 命令：probe — 深度测试单个设备
# ============================================================

def cmd_probe(host: str, timeout: float = 1.5) -> None:
    """对单个 IP 做深度测试：全端口扫描 + 协议识别。"""
    print(c.bold(f"\n=== 深度探测 {host} ==="))

    # 1. 全端口扫描（重点扫 PLC 常见 + 自定义）
    target_ports = sorted(set(list(COMMON_PORTS.keys()) + [
        22, 80, 443, 502, 23, 4840, 9100, 8000, 8080, 8081, 8888,
        3000, 5000, 5555, 20001, 20002, 47808, 1502, 10502, 1234, 6666,
    ]))
    print(c.cyan(f"扫描 {len(target_ports)} 个常见端口 (timeout={timeout}s) ..."))

    open_ports: list[int] = []
    for port in target_ports:
        if tcp_connect_probe(host, port, timeout=timeout):
            open_ports.append(port)
            print(f"  {c.green('[OPEN]')} :{port} {COMMON_PORTS.get(port, '')}")

    if not open_ports:
        print(c.red(f"\n{host} 上这些端口都没开放。"))
        print("可能原因：")
        print("  1. IP 错了（烘焙机不是这个 IP）")
        print("  2. 烘焙机不在线/没开机")
        print("  3. 烘焙机用非常规端口")
        print(c.yellow("\n建议："))
        print("  - 用 scan 命令扫整个网段找出真实 IP")
        print("  - 或用 listen 模式：python3 roaster_probe.py listen 0.0.0.0 9000")
        return

    print(c.green(f"\n开放端口: {open_ports}"))

    # 2. 对每个开放端口做协议指纹
    print(c.bold(f"\n--- 协议指纹识别 ---"))
    for port in open_ports:
        print(f"\n{c.bold(f'端口 :')}{c.cyan(str(port))}")
        info = fingerprint_port(host, port, timeout=timeout * 1.5)

        if "banner" in info:
            print(f"  {c.blue('Banner (前 64 字节):')}")
            print(hexdump(info["banner"][:64], prefix="    "))

        if info.get("protocols"):
            for p in info["protocols"]:
                print(f"  {c.green('协议')}: {c.bold(p['name'])}")
                if "detail" in p:
                    d = p["detail"]
                    if isinstance(d, dict):
                        if d.get("type") == "modbus":
                            print(f"    {c.green('✓ 确认 Modbus TCP!')}")
                            print(f"    寄存器[0..{len(d.get('registers',[]))-1}]: {d.get('registers')}")
                            print(f"    字节序: 默认 big-endian (网络序)")
                            print(f"    {c.yellow('下一步:')}")
                            print(f"      python3 roaster_probe.py read {host} {port} --modbus --unit {d.get('unit', 1)}")
                        elif d.get("type") == "santoker":
                            print(f"    {c.green('✓ 确认 Santoker 协议!')}")
                            print(f"    响应数据 hex: {d.get('data', b'').hex()}")
                            print(f"    CRC 校验: {'OK' if d.get('crc_ok') else 'BAD'}")
        else:
            print(f"  {c.yellow('未识别协议（可能是自定义二进制协议）')}")
            print(f"  建议：Wireshark 抓这个端口的包分析")


# ============================================================
# 命令：read — 作为客户端持续读数据
# ============================================================

def cmd_read(host: str, port: int, modbus: bool, santoker: bool,
             unit: int, count: int, interval: float) -> None:
    """作为客户端持续读数据（验证用，只读不写）。"""
    print(c.bold(f"\n=== 持续读取 {host}:{port} ==="))
    print(f"协议: {'Modbus TCP' if modbus else 'Santoker' if santoker else '未知'}")
    print(f"读 {count} 次, 间隔 {interval}s (Ctrl+C 停止)\n")

    for i in range(count) if count > 0 else range(999999):
        ts = time.strftime("%H:%M:%S")
        if modbus:
            r = try_modbus_tcp(host, port, unit=unit, timeout=2.0)
            if r and r.get("ok"):
                regs = r.get("registers", [])
                print(f"[{ts}] regs[0..{len(regs)-1}]: {regs}")
                # 尝试解释寄存器含义（温度常见 0.1°C 单位）
                if len(regs) >= 2:
                    # 尝试 big-endian 16-bit
                    bt_raw = regs[0]
                    et_raw = regs[1] if len(regs) > 1 else 0
                    for label, val in (("r0", regs[0]), ("r1", regs[1] if len(regs)>1 else 0)):
                        for scale, unit_str in ((1, ""), (0.1, "°C?"), (0.01, "")):
                            pass
                    print(f"        可能解读: r0={bt_raw} (÷10={bt_raw/10:.1f}°C?)  r1={et_raw} (÷10={et_raw/10:.1f}°C?)")
            elif r:
                print(f"[{ts}] {c.red('异常')}: {r}")
            else:
                print(f"[{ts}] {c.red('无响应')}")
        elif santoker:
            r = try_santoker(host, port, timeout=2.0)
            if r and r.get("ok"):
                print(f"[{ts}] data: {r.get('data', b'').hex()}")
            else:
                print(f"[{ts}] {c.red('无响应')}: {r}")
        if i < (count - 1 if count > 0 else 999998):
            time.sleep(interval)


# ============================================================
# 命令：listen — 被动监听
# ============================================================

def cmd_listen(host: str, port: int, duration: float) -> None:
    """
    监听模式：开一个 TCP 服务器，等烘焙机主动连过来。
    适用于烘焙机是 client 模式（push 数据）的情况。
    """
    print(c.bold(f"\n=== 监听模式 {host}:{port} ==="))
    print(f"持续 {duration}s (Ctrl+C 提前停止)")
    print(c.yellow("提示：如果烘焙机是 server 模式，这个模式不会收到连接。"))
    print(c.yellow("      此模式用于发现烘焙机是否会主动连接外部服务器。\n"))

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((host, port))
    except OSError as e:
        print(c.red(f"无法绑定 {host}:{port}: {e}"))
        sys.exit(2)
    srv.listen(5)
    srv.settimeout(1.0)
    print(f"{c.green('监听中...')}")

    t0 = time.time()
    conns = []
    try:
        while time.time() - t0 < duration:
            try:
                conn, addr = srv.accept()
                conns.append((conn, addr))
                print(f"\n{c.bold(c.green(f'收到连接!'))} 来自 {addr[0]}:{addr[1]}")
                conn.settimeout(2.0)
                try:
                    data = conn.recv(4096)
                    if data:
                        print(f"  {c.blue('首包数据:')}")
                        print(hexdump(data, prefix="    "))
                        # 尝试协议识别
                        if data[:2] == b"\xEE\xA5":
                            print(f"  {c.green('→ Santoker 帧头!')}")
                        elif len(data) >= 7 and data[2:4] == b"\x00\x00":
                            print(f"  {c.yellow('→ 可能是 Modbus TCP MBAP 头')}")
                except socket.timeout:
                    print(f"  (连接建立但无数据)")
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print(c.yellow("\n手动停止"))
    finally:
        for conn, _ in conns:
            conn.close()
        srv.close()
    if not conns:
        print(c.yellow("\n监听期间没有收到任何连接。"))
        print("烘焙机很可能是 server 模式（被动等连接），用 scan/probe 主动找它。")


# ============================================================
# 命令：relay — 冒充烘焙机，dump 操控电脑的请求
# ============================================================

def _try_classify(data: bytes) -> str:
    """给一段字节打个协议猜测标签。"""
    if not data:
        return ""
    if data[:2] == b"\xEE\xA5":
        return " ← Santoker 帧头 (WIFI)"
    if data[:2] == b"\xEE\xB5":
        return " ← Santoker 帧头 (BT)"
    if len(data) >= 7:
        try:
            txn, proto = struct.unpack(">HH", data[:4])
            if proto == 0x0000 and len(data) >= 12:
                func = data[7]
                if func in (1, 2, 3, 4, 5, 6, 15, 16):
                    return f" ← 可能 Modbus TCP (func={func})"
        except struct.error:
            pass
    # 纯 ASCII?
    printable = sum(1 for b in data if 32 <= b < 127 or b in (9, 10, 13))
    if printable == len(data) and len(data) > 0:
        return f" ← ASCII: {data[:40]!r}"
    return ""


def cmd_relay(listen_host: str, listen_port: int, duration: float,
              dump_file: str | None) -> None:
    """
    冒充烘焙机：在 listen_host:listen_port 开 TCP 服务，把连进来的客户端
    发来的原始数据全部 dump 出来。

    适用场景：你已经把自己的电脑 IP 设成烘焙机 IP，操控电脑会主动连过来。
    这个模式用来抓操控电脑发出的请求字节（握手、查询、控制命令），
    从而反推烘焙机的私有协议。

    注意：这个模式只 dump，不回应任何业务数据（除了 TCP ACK）。
          所以操控电脑可能会反复重试连接、报通信错误——这是正常的。
    """
    import threading

    print(c.bold(f"\n=== 冒充烘焙机：监听 {listen_host}:{listen_port} ==="))
    print(f"持续 {duration}s (Ctrl+C 提前停止)")
    print(c.yellow("\n使用方法:"))
    print("  1. 把本机 IP 设成烘焙机的 IP（已经做过）")
    print(f"  2. 在操控电脑上做你平时做的操作（连接、读数、控制）")
    print("  3. 这里会实时显示操控电脑发来的每个字节\n")

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind((listen_host, listen_port))
    except OSError as e:
        print(c.red(f"无法绑定 {listen_host}:{listen_port}: {e}"))
        if listen_port < 1024:
            print(c.yellow("提示：<1024 是特权端口，需要 sudo 或换高端口"))
        sys.exit(2)
    srv.listen(5)
    srv.settimeout(1.0)
    print(f"{c.green('监听中... 等操控电脑连接')}\n")

    dump_fp = open(dump_file, "ab") if dump_file else None
    if dump_fp:
        # 写一个简单的 header
        dump_fp.write(f"=== relay dump start {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n".encode())
        print(c.blue(f"原始数据同时写入: {dump_file}\n"))

    lock = threading.Lock()
    pkt_counter = [0]

    def handle_conn(conn: socket.socket, addr: tuple, conn_id: int) -> None:
        peer = f"{addr[0]}:{addr[1]}"
        with lock:
            print(f"{c.bold(c.green(f'#{conn_id} 连接来自 {peer}'))}  @ {time.strftime('%H:%M:%S')}")
        conn.settimeout(2.0)
        try:
            while True:
                try:
                    data = conn.recv(4096)
                except socket.timeout:
                    continue
                except (ConnectionError, OSError):
                    break
                if not data:
                    break
                with lock:
                    pkt_counter[0] += 1
                    n = pkt_counter[0]
                    ts = time.strftime("%H:%M:%S.")
                    ms = f"{int((time.time()%1)*1000):03d}"
                    label = _try_classify(data)
                    print(f"[{ts}{ms}] {c.cyan(f'#{conn_id}')} "
                          f"{c.bold(f'← RECV {len(data)}B')}{label}")
                    print(hexdump(data, prefix="      "))
                    if dump_fp:
                        dump_fp.write(f"--- pkt #{n} from {peer} "
                                      f"len={len(data)} ---\n".encode())
                        dump_fp.write(hexdump(data, prefix="").encode() + b"\n")
                        dump_fp.flush()
        except Exception as e:
            with lock:
                print(f"  {c.red(f'#{conn_id} 异常: {e}')}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
            with lock:
                print(f"  {c.yellow(f'#{conn_id} 连接关闭')}")

    t0 = time.time()
    conn_counter = 0
    threads: list[threading.Thread] = []
    try:
        while time.time() - t0 < duration:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            conn_counter += 1
            th = threading.Thread(
                target=handle_conn, args=(conn, addr, conn_counter), daemon=True,
            )
            th.start()
            threads.append(th)
    except KeyboardInterrupt:
        print(c.yellow("\n手动停止"))
    finally:
        srv.close()
        # 等线程结束
        for th in threads:
            th.join(timeout=2.0)
        if dump_fp:
            dump_fp.write(f"=== relay dump end, {pkt_counter[0]} packets ===\n".encode())
            dump_fp.close()
    print(f"\n{c.bold('汇总')}: 共 {conn_counter} 次连接, {pkt_counter[0]} 个数据包")
    if pkt_counter[0] == 0:
        print(c.yellow("\n没有收到任何数据。检查:"))
        print("  - 操控电脑有没有在操作（点连接/读数）")
        print(f"  - 操控电脑是不是在连 {listen_host}:{listen_port}")
        print("  - 你的本机 IP 是不是真的设成了烘焙机 IP")


# ============================================================
# 主入口
# ============================================================

def main() -> None:
    ap = argparse.ArgumentParser(
        description="烘焙机协议探测脚本（零依赖，纯 Python 标准库）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s scan 192.168.10.0/24          # 扫整个网段找烘焙机
  %(prog)s probe 192.168.10.100          # 深度测试某个 IP
  %(prog)s read 192.168.10.100 502 --modbus --unit 1 # Modbus 持续读
  %(prog)s read 192.168.10.100 8080 --santoker       # Santoker 持续读
  %(prog)s listen 0.0.0.0 9000           # 被动监听
  %(prog)s relay 0.0.0.0 1053 --dump relay.txt       # 冒充烘焙机，抓操控电脑的请求
""".strip(),
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_scan = sub.add_parser("scan", help="扫网段找烘焙机")
    p_scan.add_argument("cidr", help="网段，如 192.168.10.0/24")
    p_scan.add_argument("--ports", help="自定义端口，逗号分隔，如 502,8080")
    p_scan.add_argument("--timeout", type=float, default=0.8, help="超时秒数")

    p_probe = sub.add_parser("probe", help="深度测试单个 IP")
    p_probe.add_argument("host", help="目标 IP")
    p_probe.add_argument("--timeout", type=float, default=1.5)

    p_read = sub.add_parser("read", help="作为客户端持续读数据")
    p_read.add_argument("host")
    p_read.add_argument("port", type=int)
    g = p_read.add_mutually_exclusive_group(required=True)
    g.add_argument("--modbus", action="store_true", help="用 Modbus TCP")
    g.add_argument("--santoker", action="store_true", help="用 Santoker")
    p_read.add_argument("--unit", type=int, default=1, help="Modbus unit/slave id")
    p_read.add_argument("--count", type=int, default=10, help="读几次 (0=无限)")
    p_read.add_argument("--interval", type=float, default=1.0, help="间隔秒")

    p_listen = sub.add_parser("listen", help="被动监听")
    p_listen.add_argument("host", help="绑定地址，0.0.0.0=全部")
    p_listen.add_argument("port", type=int)
    p_listen.add_argument("--duration", type=float, default=60.0)

    p_relay = sub.add_parser("relay",
        help="冒充烘焙机：开服务监听，dump 操控电脑发来的请求")
    p_relay.add_argument("host", help="绑定地址，0.0.0.0=全部")
    p_relay.add_argument("port", type=int,
        help="烘焙机的服务端口，已知是 1053")
    p_relay.add_argument("--duration", type=float, default=120.0)
    p_relay.add_argument("--dump", help="把原始数据也写入这个文件")

    args = ap.parse_args()

    if args.cmd == "scan":
        ports = None
        if args.ports:
            ports = [int(x) for x in args.ports.split(",")]
        cmd_scan(args.cidr, ports, args.timeout)
    elif args.cmd == "probe":
        cmd_probe(args.host, args.timeout)
    elif args.cmd == "read":
        cmd_read(args.host, args.port, args.modbus, args.santoker,
                 args.unit, args.count, args.interval)
    elif args.cmd == "listen":
        cmd_listen(args.host, args.port, args.duration)
    elif args.cmd == "relay":
        cmd_relay(args.host, args.port, args.duration, args.dump)


if __name__ == "__main__":
    main()
