from __future__ import annotations

import pytest

from artisanlib import plot_renderer_registry
from artisanlib.plot_matplotlib_adapter import MatplotlibSnapshotRenderer
from artisanlib.plot_pyqtgraph_adapter import PyQtGraphSnapshotRenderer
from artisanlib.plot_renderer_factory import (
    RendererDependencyError,
    create_renderer,
    missing_renderer_dependencies,
)
from artisanlib.plot_renderer_registry import RendererPluginRegistry, RendererPluginSpec


class FakeCanvas:
    def draw_idle(self) -> None:
        pass


class FakeFigure:
    def __init__(self) -> None:
        self.canvas = FakeCanvas()


class FakeAxis:
    def __init__(self) -> None:
        self.figure = FakeFigure()

    def get_xlim(self) -> tuple[float, float]:
        return (0.0, 1.0)

    def get_ylim(self) -> tuple[float, float]:
        return (0.0, 1.0)

    def set_xlim(self, _minimum: float, _maximum: float) -> None:
        pass

    def set_ylim(self, _minimum: float, _maximum: float) -> None:
        pass


class FakePlot:
    def viewRange(self) -> list[list[float]]:  # noqa: N802
        return [[0.0, 1.0], [0.0, 1.0]]


def test_create_renderer_instantiates_builtin_matplotlib_renderer() -> None:
    renderer = create_renderer('matplotlib-snapshot', temperature_axis=FakeAxis())

    assert isinstance(renderer, MatplotlibSnapshotRenderer)


def test_create_renderer_instantiates_builtin_pyqtgraph_renderer() -> None:
    renderer = create_renderer('pyqtgraph-snapshot', temperature_plot=FakePlot())

    assert isinstance(renderer, PyQtGraphSnapshotRenderer)


def test_create_renderer_supports_external_registry_plugin() -> None:
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id='external-matplotlib',
            label='External Matplotlib',
            description='Renderer registered outside built-ins.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            dependencies=('matplotlib',),
            stability='experimental',
        ),
    ))

    renderer = create_renderer(
        'external-matplotlib',
        registry=registry,
        temperature_axis=FakeAxis())

    assert isinstance(renderer, MatplotlibSnapshotRenderer)


def test_create_renderer_rejects_missing_dependencies() -> None:
    plugin = RendererPluginSpec(
        renderer_id='missing',
        label='Missing',
        description='Renderer with missing dependency.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        dependencies=('definitely_missing_renderer_dependency',),
    )
    registry = RendererPluginRegistry((plugin,))

    with pytest.raises(RendererDependencyError, match='definitely_missing_renderer_dependency'):
        create_renderer('missing', registry=registry, temperature_axis=FakeAxis())


def test_create_renderer_checks_dependencies_before_loading_renderer_class(
        monkeypatch: pytest.MonkeyPatch) -> None:
    imported_modules: list[str] = []

    def fail_import(module_name: str) -> object:
        imported_modules.append(module_name)
        raise AssertionError(f'unexpected import: {module_name}')

    monkeypatch.setattr(plot_renderer_registry.importlib, 'import_module', fail_import)
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id='missing-before-import',
            label='Missing Before Import',
            description='Renderer whose module must not be imported when dependencies are missing.',
            class_path='unimported_renderer_module.Renderer',
            dependencies=('definitely_missing_renderer_dependency',),
        ),
    ))

    with pytest.raises(RendererDependencyError, match='definitely_missing_renderer_dependency'):
        create_renderer('missing-before-import', registry=registry)

    assert imported_modules == []


def test_create_renderer_rejects_unknown_renderer_id() -> None:
    with pytest.raises(KeyError, match='unknown renderer plugin'):
        create_renderer('unknown-renderer', temperature_axis=FakeAxis())


def test_missing_renderer_dependencies_reports_only_missing_modules() -> None:
    plugin = RendererPluginSpec(
        renderer_id='mixed',
        label='Mixed',
        description='Renderer with available and missing dependencies.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        dependencies=('matplotlib', 'definitely_missing_renderer_dependency'),
    )

    assert missing_renderer_dependencies(plugin) == ('definitely_missing_renderer_dependency',)
