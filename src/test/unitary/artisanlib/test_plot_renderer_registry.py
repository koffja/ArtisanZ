from __future__ import annotations

import pytest

from artisanlib import plot_renderer_registry
from artisanlib.plot_matplotlib_adapter import MatplotlibSnapshotRenderer
from artisanlib.plot_pyqtgraph_adapter import PyQtGraphSnapshotRenderer
from artisanlib.plot_renderer_registry import (
    BUILTIN_RENDERER_PLUGINS,
    RendererPluginRegistry,
    RendererPluginSpec,
    create_default_renderer_registry,
    load_renderer_class,
)


def test_default_renderer_registry_exposes_builtin_renderers() -> None:
    registry = create_default_renderer_registry()

    assert tuple(plugin.renderer_id for plugin in registry.plugins()) == (
        'matplotlib-snapshot',
        'pyqtgraph-snapshot',
    )
    assert registry.get('matplotlib-snapshot').stability == 'stable'
    assert registry.get('matplotlib-snapshot').surface == 'matplotlib-axis'
    assert registry.get('pyqtgraph-snapshot').stability == 'experimental'
    assert registry.get('pyqtgraph-snapshot').surface == 'pyqtgraph-plot'


def test_default_renderer_registry_loads_builtin_renderer_classes() -> None:
    registry = create_default_renderer_registry()

    assert registry.load_renderer_class('matplotlib-snapshot') is MatplotlibSnapshotRenderer
    assert registry.load_renderer_class('pyqtgraph-snapshot') is PyQtGraphSnapshotRenderer


def test_renderer_registry_rejects_duplicate_plugin_ids() -> None:
    plugin = BUILTIN_RENDERER_PLUGINS[0]

    with pytest.raises(ValueError, match='already registered'):
        RendererPluginRegistry((plugin, plugin))


def test_renderer_registry_supports_external_plugin_registration() -> None:
    registry = create_default_renderer_registry()
    plugin = RendererPluginSpec(
        renderer_id='external-renderer',
        label='External Renderer',
        description='Renderer provided outside the built-in registry.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('matplotlib',),
        stability='experimental',
    )

    registry.register(plugin)

    assert registry.get('external-renderer') == plugin
    assert registry.load_renderer_class('external-renderer') is MatplotlibSnapshotRenderer


def test_renderer_registry_filters_unavailable_plugins() -> None:
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id='available',
            label='Available',
            description='Uses an installed dependency.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('matplotlib',),
        ),
        RendererPluginSpec(
            renderer_id='missing',
            label='Missing',
            description='Uses a missing dependency.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('definitely_missing_renderer_dependency',),
        ),
    ))

    assert tuple(plugin.renderer_id for plugin in registry.plugins(include_unavailable=False)) == (
        'available',
    )


def test_renderer_registry_availability_filter_does_not_import_dependencies(
        monkeypatch: pytest.MonkeyPatch) -> None:
    imported_modules: list[str] = []

    def fail_import(module_name: str) -> object:
        imported_modules.append(module_name)
        raise AssertionError(f'unexpected import: {module_name}')

    monkeypatch.setattr(plot_renderer_registry.importlib, 'import_module', fail_import)
    monkeypatch.setattr(
        plot_renderer_registry.importlib.util,
        'find_spec',
        lambda module_name: object() if module_name == 'available_dependency' else None)
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id='available',
            label='Available',
            description='Uses an installed dependency.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('available_dependency',),
        ),
        RendererPluginSpec(
            renderer_id='missing',
            label='Missing',
            description='Uses a missing dependency.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('missing_dependency',),
        ),
    ))

    assert tuple(plugin.renderer_id for plugin in registry.plugins(include_unavailable=False)) == (
        'available',
    )
    assert imported_modules == []


def test_load_renderer_class_rejects_invalid_class_paths() -> None:
    with pytest.raises(ValueError, match='invalid renderer class path'):
        load_renderer_class(RendererPluginSpec(
            renderer_id='invalid',
            label='Invalid',
            description='Invalid class path.',
            class_path='MissingClassName',
            surface='matplotlib-axis',
        ))


def test_load_renderer_class_rejects_non_class_targets() -> None:
    with pytest.raises(TypeError, match='does not resolve to a class'):
        load_renderer_class(RendererPluginSpec(
            renderer_id='function',
            label='Function',
            description='Function target.',
            class_path='artisanlib.plot_renderer_registry.create_default_renderer_registry',
            surface='matplotlib-axis',
        ))


def test_load_renderer_class_rejects_classes_without_renderer_methods() -> None:
    with pytest.raises(TypeError, match='does not implement LivePlotRenderer methods'):
        load_renderer_class(RendererPluginSpec(
            renderer_id='registry',
            label='Registry',
            description='Class target that is not a renderer.',
            class_path='artisanlib.plot_renderer_registry.RendererPluginRegistry',
            surface='matplotlib-axis',
        ))
