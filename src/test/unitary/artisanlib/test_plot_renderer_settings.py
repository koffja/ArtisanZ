from __future__ import annotations

from pathlib import Path

from artisanlib.plot_renderer_factory_smoke import build_factory_smoke_snapshot, smoke_renderer_factory
from artisanlib.plot_renderer_plugin_loader import (
    ARTISANZ_RENDERER_PLUGIN_PATH,
)
from artisanlib.plot_renderer_registry import (
    RendererPluginRegistry,
    RendererPluginSpec,
    create_default_renderer_registry,
)
from artisanlib.plot_renderer_settings import (
    ARTISANZ_RENDERER_ID,
    DEFAULT_RENDERER_ID,
    RendererSelectionError,
    available_renderer_ids,
    configured_renderer_id,
    select_renderer,
)


def test_configured_renderer_id_defaults_to_matplotlib_snapshot() -> None:
    assert configured_renderer_id(env={}) == DEFAULT_RENDERER_ID


def test_configured_renderer_id_reads_trimmed_env_override() -> None:
    assert configured_renderer_id(env={ARTISANZ_RENDERER_ID: ' pyqtgraph-snapshot '}) == (
        'pyqtgraph-snapshot'
    )


def test_select_renderer_uses_available_requested_builtin() -> None:
    selection = select_renderer(env={ARTISANZ_RENDERER_ID: 'pyqtgraph-snapshot'})

    assert selection.requested_renderer_id == 'pyqtgraph-snapshot'
    assert selection.renderer_id == 'pyqtgraph-snapshot'
    assert selection.plugin.renderer_id == 'pyqtgraph-snapshot'
    assert selection.registry.get('pyqtgraph-snapshot').renderer_id == 'pyqtgraph-snapshot'
    assert selection.fallback_reason is None
    assert not selection.used_fallback


def test_select_renderer_falls_back_to_default_for_unknown_id() -> None:
    selection = select_renderer(env={ARTISANZ_RENDERER_ID: 'unknown-renderer'})

    assert selection.requested_renderer_id == 'unknown-renderer'
    assert selection.renderer_id == DEFAULT_RENDERER_ID
    assert selection.plugin.renderer_id == DEFAULT_RENDERER_ID
    assert selection.registry.get(DEFAULT_RENDERER_ID).renderer_id == DEFAULT_RENDERER_ID
    assert selection.fallback_reason == 'unknown'
    assert selection.used_fallback


def test_select_renderer_falls_back_to_default_for_unavailable_id() -> None:
    registry = create_default_renderer_registry()
    registry.register(RendererPluginSpec(
        renderer_id='missing-renderer',
        label='Missing Renderer',
        description='Renderer with an unavailable dependency.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('definitely_missing_renderer_dependency',),
    ))

    selection = select_renderer(
        registry=registry,
        env={ARTISANZ_RENDERER_ID: 'missing-renderer'},
    )

    assert selection.requested_renderer_id == 'missing-renderer'
    assert selection.renderer_id == DEFAULT_RENDERER_ID
    assert selection.fallback_reason == 'unavailable'


def test_select_renderer_treats_bad_dotted_dependency_as_unavailable() -> None:
    registry = create_default_renderer_registry()
    registry.register(RendererPluginSpec(
        renderer_id='bad-dotted-dependency-renderer',
        label='Bad Dotted Dependency Renderer',
        description='Renderer with a dependency whose parent module is unavailable.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('definitely_missing_renderer_parent.child',),
    ))

    selection = select_renderer(
        registry=registry,
        env={ARTISANZ_RENDERER_ID: 'bad-dotted-dependency-renderer'},
    )

    assert selection.renderer_id == DEFAULT_RENDERER_ID
    assert selection.fallback_reason == 'unavailable'


def test_available_renderer_ids_lists_only_available_plugins() -> None:
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id='available-renderer',
            label='Available Renderer',
            description='Renderer with no dependency gate.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
        ),
        RendererPluginSpec(
            renderer_id='missing-renderer',
            label='Missing Renderer',
            description='Renderer with a missing dependency.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('definitely_missing_renderer_dependency',),
        ),
    ))

    assert available_renderer_ids(registry) == ('available-renderer',)


def test_select_renderer_can_drive_filesystem_plugin_factory_smoke(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        'filesystem_selection.py',
        """
from artisanlib.plot_renderer_registry import RendererPluginSpec


def register_renderer_plugins():
    return (RendererPluginSpec(
        renderer_id='filesystem-selection',
        label='Filesystem Selection',
        description='Filesystem plugin selected through ARTISANZ_RENDERER_ID.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('matplotlib',),
    ),)
""",
    )
    env = {
        ARTISANZ_RENDERER_ID: 'filesystem-selection',
        ARTISANZ_RENDERER_PLUGIN_PATH: str(tmp_path),
    }
    selection = select_renderer(env=env)
    result = smoke_renderer_factory(
        selection.renderer_id,
        snapshot=build_factory_smoke_snapshot(point_count=16, event_count=2),
        registry=selection.registry,
    )

    assert selection.renderer_id == 'filesystem-selection'
    assert selection.fallback_reason is None
    assert result.renderer_id == 'filesystem-selection'
    assert result.temperature_item_count == 4
    assert result.ror_item_count == 2
    assert result.event_item_count == 4


def test_select_renderer_uses_available_alternative_when_default_is_missing() -> None:
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id='available-renderer',
            label='Available Renderer',
            description='Renderer with no dependency gate.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
        ),
    ))

    selection = select_renderer(registry=registry, env={ARTISANZ_RENDERER_ID: 'unknown-renderer'})

    assert selection.renderer_id == 'available-renderer'
    assert selection.plugin.renderer_id == 'available-renderer'
    assert selection.fallback_reason == 'default_unavailable'


def test_select_renderer_uses_available_alternative_when_default_is_unavailable() -> None:
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id=DEFAULT_RENDERER_ID,
            label='Unavailable Default',
            description='Default renderer with a missing dependency.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('definitely_missing_renderer_dependency',),
        ),
        RendererPluginSpec(
            renderer_id='available-renderer',
            label='Available Renderer',
            description='Renderer with no dependency gate.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
        ),
    ))

    selection = select_renderer(registry=registry, env={ARTISANZ_RENDERER_ID: 'unknown-renderer'})

    assert selection.renderer_id == 'available-renderer'
    assert selection.fallback_reason == 'default_unavailable'


def test_select_renderer_raises_when_no_renderer_is_available() -> None:
    registry = RendererPluginRegistry((
        RendererPluginSpec(
            renderer_id=DEFAULT_RENDERER_ID,
            label='Unavailable Default',
            description='Default renderer with a missing dependency.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('definitely_missing_renderer_dependency',),
        ),
    ))

    try:
        select_renderer(registry=registry, env={ARTISANZ_RENDERER_ID: 'unknown-renderer'})
    except RendererSelectionError as exc:
        assert str(exc) == 'no available renderer plugins'
    else:
        raise AssertionError('expected RendererSelectionError')


def _write_plugin(directory: Path, filename: str, body: str) -> Path:
    plugin_file = directory / filename
    plugin_file.write_text(body.lstrip(), encoding='utf-8')
    return plugin_file
