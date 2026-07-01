from __future__ import annotations

from pathlib import Path
import os

import pytest

from artisanlib.plot_renderer_factory import create_renderer
from artisanlib.plot_renderer_factory_smoke import build_factory_smoke_snapshot, smoke_renderer_factory
from artisanlib.plot_renderer_plugin_loader import (
    ARTISANZ_RENDERER_PLUGIN_PATH,
    build_runtime_registry,
    discover_external_renderer_plugins,
)


def test_build_runtime_registry_loads_filesystem_plugin_and_smokes_external_id(
        tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        'filesystem_matplotlib.py',
        """
from artisanlib.plot_renderer_registry import RendererPluginSpec


def register_renderer_plugins():
    return (RendererPluginSpec(
        renderer_id='filesystem-matplotlib-smoke',
        label='Filesystem Matplotlib Smoke',
        description='Filesystem plugin that reuses the Matplotlib adapter.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('matplotlib',),
    ),)
""",
    )
    registry = build_runtime_registry(search_paths=(tmp_path,))
    snapshot = build_factory_smoke_snapshot(point_count=16, event_count=2)

    result = smoke_renderer_factory('filesystem-matplotlib-smoke', snapshot=snapshot, registry=registry)

    assert result.renderer_id == 'filesystem-matplotlib-smoke'
    assert result.temperature_item_count == 4
    assert result.ror_item_count == 2
    assert result.event_item_count == 4
    assert result.png_byte_count > 1000


def test_build_runtime_registry_keeps_plugin_module_importable_for_local_renderer_class(
        tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        'filesystem_stub.py',
        """
from artisanlib.plot_renderer_registry import RendererPluginSpec


class FilesystemStubRenderer:
    def __init__(self, **_kwargs):
        self.snapshot = None
        self.view_state = None

    def set_snapshot(self, snapshot):
        self.snapshot = snapshot

    def update_live_frame(self, snapshot):
        self.snapshot = snapshot

    def reset_view(self, view_state):
        self.view_state = view_state

    def export_view_state(self):
        return self.snapshot


def register_renderer_plugins():
    return (RendererPluginSpec(
        renderer_id='filesystem-stub',
        label='Filesystem Stub',
        description='Renderer class defined inside the external plugin file.',
        class_path=f'{__name__}.FilesystemStubRenderer',
        surface='matplotlib-axis',
        dependencies=(),
    ),)
""",
    )
    registry = build_runtime_registry(search_paths=(tmp_path,))

    renderer = create_renderer('filesystem-stub', registry=registry)
    renderer.set_snapshot('snapshot')

    assert renderer.__class__.__name__ == 'FilesystemStubRenderer'
    assert renderer.export_view_state() == 'snapshot'


def test_build_runtime_registry_reads_env_plugin_paths(
        tmp_path: Path) -> None:
    first_path = tmp_path / 'first'
    second_path = tmp_path / 'second'
    first_path.mkdir()
    second_path.mkdir()
    _write_plugin(
        second_path,
        'env_matplotlib.py',
        """
from artisanlib.plot_renderer_registry import RendererPluginSpec


def register_renderer_plugins():
    return (RendererPluginSpec(
        renderer_id='env-matplotlib',
        label='Env Matplotlib',
        description='Renderer plugin loaded from ARTISANZ_RENDERER_PLUGIN_PATH.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('matplotlib',),
    ),)
""",
    )
    env = {ARTISANZ_RENDERER_PLUGIN_PATH: os.pathsep.join((str(first_path), str(second_path)))}

    registry = build_runtime_registry(env=env)

    assert registry.get('env-matplotlib').label == 'Env Matplotlib'


def test_build_runtime_registry_without_env_uses_builtins_only() -> None:
    registry = build_runtime_registry(env={})

    assert tuple(plugin.renderer_id for plugin in registry.plugins()) == (
        'matplotlib-snapshot',
        'pyqtgraph-snapshot',
    )


def test_bad_plugin_file_warns_and_does_not_break_builtins(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        'bad_plugin.py',
        """
def register_renderer_plugins():
    raise RuntimeError('broken plugin')
""",
    )

    with pytest.warns(RuntimeWarning, match='failed to register plugins'):
        registry = build_runtime_registry(search_paths=(tmp_path,))

    assert registry.get('matplotlib-snapshot').renderer_id == 'matplotlib-snapshot'


def test_duplicate_renderer_id_warns_and_keeps_builtins(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        'duplicate_builtin.py',
        """
from artisanlib.plot_renderer_registry import RendererPluginSpec


def register_renderer_plugins():
    return (RendererPluginSpec(
        renderer_id='matplotlib-snapshot',
        label='Duplicate Builtin',
        description='External plugin colliding with a built-in id.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        surface='matplotlib-axis',
        dependencies=('matplotlib',),
    ),)
""",
    )

    with pytest.warns(RuntimeWarning, match='renderer plugin already registered'):
        registry = build_runtime_registry(search_paths=(tmp_path,))

    assert registry.get('matplotlib-snapshot').label == 'Matplotlib Snapshot'


def test_discover_external_renderer_plugins_skips_files_without_hook_without_importing(
        tmp_path: Path) -> None:
    marker_file = tmp_path / 'side_effect_marker'
    _write_plugin(
        tmp_path,
        'not_a_plugin.py',
        f"""
from pathlib import Path

Path({str(marker_file)!r}).write_text('executed', encoding='utf-8')
PLUGIN_NAME = "ignored"
""",
    )

    assert discover_external_renderer_plugins((tmp_path,)) == ()
    assert not marker_file.exists()


def test_import_time_failure_warns_and_keeps_builtins(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        'import_failure.py',
        """
def register_renderer_plugins():
    return ()


raise RuntimeError('boom during import')
""",
    )

    with pytest.warns(RuntimeWarning, match='failed to import plugin'):
        registry = build_runtime_registry(search_paths=(tmp_path,))

    assert registry.get('matplotlib-snapshot').renderer_id == 'matplotlib-snapshot'


def test_non_callable_hook_warns_and_keeps_builtins(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        'non_callable_hook.py',
        """
def register_renderer_plugins():
    return ()


register_renderer_plugins = 'not callable'
""",
    )

    with pytest.warns(RuntimeWarning, match='not callable'):
        registry = build_runtime_registry(search_paths=(tmp_path,))

    assert registry.get('matplotlib-snapshot').renderer_id == 'matplotlib-snapshot'


def test_discover_external_renderer_plugins_warns_on_invalid_entries(tmp_path: Path) -> None:
    _write_plugin(
        tmp_path,
        'invalid_entry.py',
        """
from artisanlib.plot_renderer_registry import RendererPluginSpec


def register_renderer_plugins():
    return (
        'invalid',
        RendererPluginSpec(
            renderer_id='valid-entry',
            label='Valid Entry',
            description='Valid plugin spec returned after an invalid entry.',
            class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
            surface='matplotlib-axis',
            dependencies=('matplotlib',),
        ),
    )
""",
    )

    with pytest.warns(RuntimeWarning, match='non-RendererPluginSpec'):
        plugins = discover_external_renderer_plugins((tmp_path,))

    assert tuple(plugin.renderer_id for plugin in plugins) == ('valid-entry',)


def _write_plugin(directory: Path, filename: str, body: str) -> Path:
    plugin_file = directory / filename
    plugin_file.write_text(body.lstrip(), encoding='utf-8')
    return plugin_file
