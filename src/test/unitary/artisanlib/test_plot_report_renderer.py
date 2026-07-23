from __future__ import annotations

from types import SimpleNamespace

from artisanlib.plot_report_renderer import render_report_graph, report_graph_renderer_id


def test_report_graph_renderer_defaults_to_matplotlib() -> None:
    assert report_graph_renderer_id(SimpleNamespace(), env_value=None) == 'matplotlib'


def test_report_graph_renderer_accepts_explicit_pyqtgraph_aliases() -> None:
    assert report_graph_renderer_id(SimpleNamespace(report_graph_renderer='pyqtgraph')) == 'pyqtgraph'
    assert report_graph_renderer_id(SimpleNamespace(), env_value='pyqtgraph-snapshot') == 'pyqtgraph'


def test_report_graph_renderer_source_override_wins_over_environment() -> None:
    source = SimpleNamespace(report_graph_renderer='matplotlib')

    assert report_graph_renderer_id(source, env_value='pyqtgraph') == 'matplotlib'


def test_report_graph_renderer_unknown_values_fall_back_to_matplotlib() -> None:
    assert report_graph_renderer_id(SimpleNamespace(), env_value='unknown') == 'matplotlib'


def test_render_report_graph_uses_matplotlib_by_default(tmp_path) -> None:
    saved: list[str] = []

    result = render_report_graph(
        SimpleNamespace(),
        tmp_path,
        matplotlib_export=saved.append,
    )

    assert result.backend == 'matplotlib'
    assert result.path.endswith('roastlog-graph.svg')
    assert saved == [result.path]
    assert result.fallback_reason is None


def test_render_report_graph_falls_back_after_pyqtgraph_failure(tmp_path, monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise RuntimeError('simulated renderer failure')

    monkeypatch.setattr('artisanlib.plot_report_renderer.export_pyqtgraph_report_graph', fail)
    saved: list[str] = []

    result = render_report_graph(
        SimpleNamespace(report_graph_renderer='pyqtgraph'),
        tmp_path,
        matplotlib_export=saved.append,
    )

    assert result.backend == 'matplotlib'
    assert result.path.endswith('roastlog-graph.svg')
    assert saved == [result.path]
    assert result.fallback_reason == 'RuntimeError: simulated renderer failure'


def test_render_report_graph_falls_back_after_blank_pyqtgraph_output(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        'artisanlib.plot_report_renderer.export_pyqtgraph_report_graph',
        lambda *_args, **_kwargs: SimpleNamespace(
            byte_count=42,
            sampled_non_background_pixel_count=0,
        ),
    )
    saved: list[str] = []

    result = render_report_graph(
        SimpleNamespace(report_graph_renderer='pyqtgraph'),
        tmp_path,
        matplotlib_export=saved.append,
    )

    assert result.backend == 'matplotlib'
    assert saved == [result.path]
    assert result.fallback_reason == 'RuntimeError: PyQtGraph report graph export was blank'
