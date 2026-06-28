from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal

from artisanlib.performance import default_gui_perf_export_path


SortKey = Literal['count', 'total_ms', 'avg_ms', 'max_ms']


@dataclass(frozen=True)
class PerfMetric:
    name: str
    count: int
    total_ms: float
    avg_ms: float
    max_ms: float


def load_metrics(path: str | Path) -> list[PerfMetric]:
    metrics: list[PerfMetric] = []
    with Path(path).open(encoding='utf-8') as source:
        for line_number, line in enumerate(source, start=1):
            raw_line = line.strip()
            if not raw_line:
                continue
            row = json.loads(raw_line)
            metrics.append(_metric_from_row(row, line_number))
    return metrics


def format_metric_report(
    metrics: Sequence[PerfMetric],
    *,
    sort_by: SortKey = 'max_ms',
    limit: int | None = None,
) -> list[str]:
    if not metrics:
        return ['No GUI performance metrics found.']

    sorted_metrics = sorted(metrics, key=lambda metric: _sort_value(metric, sort_by), reverse=True)
    if limit is not None:
        sorted_metrics = sorted_metrics[:limit]

    lines = [
        'metric                       count     total_ms      avg_ms      max_ms',
        '-----------------------------------------------------------------------',
    ]
    for metric in sorted_metrics:
        lines.append(
            f'{metric.name:<28.28} '
            f'{metric.count:>8} '
            f'{metric.total_ms:>12.3f} '
            f'{metric.avg_ms:>11.3f} '
            f'{metric.max_ms:>11.3f}'
        )
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    metrics = load_metrics(args.path or default_gui_perf_export_path())
    lines = format_metric_report(metrics, sort_by=args.sort_by, limit=args.limit)
    for line in lines:
        print(line)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Summarize ArtisanZ GUI performance JSONL metrics.')
    parser.add_argument(
        'path',
        nargs='?',
        help='Path to ARTISANZ_GUI_PERF_FILE output. Defaults to the automatic temp-file path.',
    )
    parser.add_argument(
        '--sort-by',
        choices=('count', 'total_ms', 'avg_ms', 'max_ms'),
        default='max_ms',
        help='Metric column used for descending sort.',
    )
    parser.add_argument('--limit', type=int, default=None, help='Maximum number of rows to print.')
    return parser


def _metric_from_row(row: object, line_number: int) -> PerfMetric:
    if not isinstance(row, dict):
        raise ValueError(f'Line {line_number}: expected a JSON object.')
    name = row.get('name')
    if not isinstance(name, str) or not name:
        raise ValueError(f'Line {line_number}: expected non-empty string field "name".')
    return PerfMetric(
        name=name,
        count=int(_number_field(row, 'count', line_number)),
        total_ms=float(_number_field(row, 'total_ms', line_number)),
        avg_ms=float(_number_field(row, 'avg_ms', line_number)),
        max_ms=float(_number_field(row, 'max_ms', line_number)),
    )


def _number_field(row: dict[object, object], field_name: str, line_number: int) -> float:
    value = row.get(field_name)
    if not isinstance(value, int | float):
        raise ValueError(f'Line {line_number}: expected numeric field "{field_name}".')
    return float(value)


def _sort_value(metric: PerfMetric, sort_by: SortKey) -> float:
    if sort_by == 'count':
        return float(metric.count)
    if sort_by == 'total_ms':
        return metric.total_ms
    if sort_by == 'avg_ms':
        return metric.avg_ms
    return metric.max_ms


if __name__ == '__main__':
    raise SystemExit(main())
