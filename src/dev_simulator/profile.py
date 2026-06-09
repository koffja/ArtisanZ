"""Synthetic roast profile generator for the dev simulator."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List, Literal


@dataclass(frozen=True)
class RoastSpec:
    charge_t: float = 0.0
    charge_bt: float = 180.0
    charge_et: float = 190.0
    turn_t: float = 90.0
    turn_bt: float = 95.0
    turn_et: float = 180.0
    dry_t: float = 300.0
    dry_bt: float = 152.0
    dry_et: float = 170.0
    fcs_t: float = 570.0
    fcs_bt: float = 193.0
    fcs_et: float = 205.0
    fce_t: float = 645.0
    fce_bt: float = 202.0
    fce_et: float = 212.0
    scs_t: float = 765.0
    scs_bt: float = 215.0
    scs_et: float = 222.0
    drop_t: float = 780.0
    drop_bt: float = 218.0
    drop_et: float = 224.0
    sample_hz: int = 10
    noise_std: float = 0.3
    noise_model: Literal["gaussian", "ar1", "none"] = "ar1"

    def __post_init__(self) -> None:
        _validate_finite(self.charge_t, self.charge_bt, self.charge_et)
        _validate_finite(self.turn_t, self.turn_bt, self.turn_et)
        _validate_finite(self.dry_t, self.dry_bt, self.dry_et)
        _validate_finite(self.fcs_t, self.fcs_bt, self.fcs_et)
        _validate_finite(self.fce_t, self.fce_bt, self.fce_et)
        _validate_finite(self.scs_t, self.scs_bt, self.scs_et)
        _validate_finite(self.drop_t, self.drop_bt, self.drop_et)
        _validate_node_times(
            ("charge_t", self.charge_t),
            ("turn_t", self.turn_t),
            ("dry_t", self.dry_t),
            ("fcs_t", self.fcs_t),
            ("fce_t", self.fce_t),
            ("scs_t", self.scs_t),
            ("drop_t", self.drop_t),
        )


def _validate_finite(*values: float) -> None:
    for v in values:
        if not math.isfinite(v):
            raise ValueError(f"RoastSpec field must be finite, got {v}")


def _validate_node_times(*nodes: tuple[str, float]) -> None:
    previous_name, previous_t = nodes[0]
    if previous_t < 0.0:
        raise ValueError(f"{previous_name} must be non-negative: {previous_t}")
    for name, t in nodes[1:]:
        if t <= previous_t:
            raise ValueError(
                f"{name} must be later than {previous_name}: {t} <= {previous_t}"
            )
        previous_name, previous_t = name, t


def _cosine_ease(t: float, t0: float, t1: float, v0: float, v1: float) -> float:
    if t1 == t0:
        return v0
    frac = (t - t0) / (t1 - t0)
    frac = max(0.0, min(1.0, frac))
    return v0 + (v1 - v0) * (1.0 - math.cos(math.pi * frac)) / 2.0


def apply_noise(
    n: int,
    model: str,
    std: float,
    alpha: float = 0.85,
) -> List[float]:
    if model == "none":
        return [0.0] * n
    if model == "gaussian":
        return [random.gauss(0.0, std) for _ in range(n)]
    if model == "ar1":
        if n == 0:
            return []
        sigma = std * math.sqrt(1.0 - alpha * alpha)
        result: List[float] = [random.gauss(0.0, std)]
        for _ in range(1, n):
            result.append(alpha * result[-1] + random.gauss(0.0, sigma))
        return result
    raise ValueError(f"Unknown noise model: {model!r}")


def _interpolate_nodes(
    nodes: List[tuple[float, float]],
    sample_hz: int,
    end_time: float,
) -> List[float]:
    result: List[float] = []
    step = 1.0 / sample_hz
    t = 0.0
    node_idx = 0
    while t <= end_time + step * 0.5:
        while node_idx < len(nodes) - 1 and nodes[node_idx + 1][0] <= t:
            node_idx += 1
        if node_idx >= len(nodes) - 1:
            result.append(nodes[-1][1])
        else:
            t0, v0 = nodes[node_idx]
            t1, v1 = nodes[node_idx + 1]
            result.append(_cosine_ease(t, t0, t1, v0, v1))
        t += step
    return result


def _clamp(values: List[float], lo: float, hi: float) -> List[float]:
    return [max(lo, min(hi, v)) for v in values]


def generate_profile(spec: RoastSpec) -> dict:
    bt_nodes: list[tuple[float, float]] = [
        (spec.charge_t, spec.charge_bt),
        (spec.turn_t, spec.turn_bt),
        (spec.dry_t, spec.dry_bt),
        (spec.fcs_t, spec.fcs_bt),
        (spec.fce_t, spec.fce_bt),
        (spec.scs_t, spec.scs_bt),
        (spec.drop_t, spec.drop_bt),
    ]
    et_nodes: list[tuple[float, float]] = [
        (spec.charge_t, spec.charge_et),
        (spec.turn_t, spec.turn_et),
        (spec.dry_t, spec.dry_et),
        (spec.fcs_t, spec.fcs_et),
        (spec.fce_t, spec.fce_et),
        (spec.scs_t, spec.scs_et),
        (spec.drop_t, spec.drop_et),
    ]

    bt = _interpolate_nodes(bt_nodes, spec.sample_hz, spec.drop_t)
    et = _interpolate_nodes(et_nodes, spec.sample_hz, spec.drop_t)

    if spec.noise_model != "none":
        noise_et = apply_noise(len(et), spec.noise_model, spec.noise_std)
        noise_bt = apply_noise(len(bt), spec.noise_model, spec.noise_std)
        et = [e + n for e, n in zip(et, noise_et)]
        bt = [b + n for b, n in zip(bt, noise_bt)]

    et = _clamp(et, 0.0, 500.0)
    bt = _clamp(bt, 0.0, 500.0)

    step_ms = 1000.0 / spec.sample_hz
    timex = [i * step_ms for i in range(len(et))]

    return {"timex": timex, "temp1": et, "temp2": bt, "mode": "C"}
