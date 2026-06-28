import json

from artisanlib.performance_report import PerfMetric, format_metric_report, load_metrics, main


def test_load_metrics_reads_jsonl(tmp_path) -> None:
    source = tmp_path / 'gui-perf.jsonl'
    source.write_text(
        '\n'.join(
            [
                json.dumps(
                    {
                        'name':'canvas.updategraphics',
                        'count':4,
                        'total_ms':20.0,
                        'avg_ms':5.0,
                        'max_ms':8.0,
                    }
                ),
                '',
            ]
        ),
        encoding='utf-8',
    )

    metrics = load_metrics(source)

    assert len(metrics) == 1
    assert metrics[0].name == 'canvas.updategraphics'
    assert metrics[0].count == 4
    assert metrics[0].total_ms == 20.0
    assert metrics[0].avg_ms == 5.0
    assert metrics[0].max_ms == 8.0


def test_format_metric_report_sorts_and_limits() -> None:
    report = format_metric_report(
        [
            PerfMetric(
                name='canvas.sample_processing',
                count=3,
                total_ms=12.0,
                avg_ms=4.0,
                max_ms=5.0,
            ),
            PerfMetric(
                name='canvas.redraw',
                count=1,
                total_ms=80.0,
                avg_ms=80.0,
                max_ms=80.0,
            ),
        ],
        sort_by='max_ms',
        limit=1,
    )

    assert report == [
        'metric                       count     total_ms      avg_ms      max_ms',
        '-----------------------------------------------------------------------',
        'canvas.redraw                       1       80.000      80.000      80.000',
    ]


def test_empty_metric_report() -> None:
    assert format_metric_report([]) == ['No GUI performance metrics found.']


def test_main_prints_report(tmp_path, capsys) -> None:
    source = tmp_path / 'gui-perf.jsonl'
    source.write_text(
        json.dumps(
            {
                'name':'canvas.updateBackground',
                'count':2,
                'total_ms':3.0,
                'avg_ms':1.5,
                'max_ms':2.0,
            }
        ),
        encoding='utf-8',
    )

    assert main([str(source), '--sort-by', 'avg_ms', '--limit', '1']) == 0

    output = capsys.readouterr().out
    assert 'canvas.updateBackground' in output
    assert '1.500' in output
