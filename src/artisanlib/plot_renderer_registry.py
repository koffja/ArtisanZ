from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
from typing import Literal


type RendererStability = Literal['stable', 'experimental']

REQUIRED_RENDERER_METHODS: tuple[str, ...] = (
    'set_snapshot',
    'update_live_frame',
    'reset_view',
    'export_view_state',
)


@dataclass(frozen=True, slots=True)
class RendererPluginSpec:
    renderer_id: str
    label: str
    description: str
    class_path: str
    dependencies: tuple[str, ...] = ()
    stability: RendererStability = 'experimental'

    def is_available(self) -> bool:
        return all(_module_available(module_name) for module_name in self.dependencies)


class RendererPluginRegistry:
    def __init__(self, plugins: tuple[RendererPluginSpec, ...] = ()) -> None:
        self._plugins: dict[str, RendererPluginSpec] = {}
        for plugin in plugins:
            self.register(plugin)

    def register(self, plugin: RendererPluginSpec) -> None:
        if plugin.renderer_id in self._plugins:
            raise ValueError(f'renderer plugin already registered: {plugin.renderer_id}')
        self._plugins[plugin.renderer_id] = plugin

    def get(self, renderer_id: str) -> RendererPluginSpec:
        try:
            return self._plugins[renderer_id]
        except KeyError as exc:
            raise KeyError(f'unknown renderer plugin: {renderer_id}') from exc

    def plugins(self, *, include_unavailable: bool = True) -> tuple[RendererPluginSpec, ...]:
        plugins = tuple(self._plugins[renderer_id] for renderer_id in sorted(self._plugins))
        if include_unavailable:
            return plugins
        return tuple(plugin for plugin in plugins if plugin.is_available())

    def load_renderer_class(self, renderer_id: str) -> type[object]:
        plugin = self.get(renderer_id)
        return load_renderer_class(plugin)


BUILTIN_RENDERER_PLUGINS: tuple[RendererPluginSpec, ...] = (
    RendererPluginSpec(
        renderer_id='matplotlib-snapshot',
        label='Matplotlib Snapshot',
        description='Compatibility renderer for Artisan matplotlib axes.',
        class_path='artisanlib.plot_matplotlib_adapter.MatplotlibSnapshotRenderer',
        dependencies=('matplotlib',),
        stability='stable',
    ),
    RendererPluginSpec(
        renderer_id='pyqtgraph-snapshot',
        label='PyQtGraph Snapshot',
        description='Experimental PyQtGraph renderer for benchmarked live-plot exploration.',
        class_path='artisanlib.plot_pyqtgraph_adapter.PyQtGraphSnapshotRenderer',
        dependencies=('pyqtgraph',),
        stability='experimental',
    ),
)


def create_default_renderer_registry() -> RendererPluginRegistry:
    return RendererPluginRegistry(BUILTIN_RENDERER_PLUGINS)


def load_renderer_class(plugin: RendererPluginSpec) -> type[object]:
    module_name, _, class_name = plugin.class_path.rpartition('.')
    if not module_name or not class_name:
        raise ValueError(f'invalid renderer class path: {plugin.class_path}')
    module = importlib.import_module(module_name)
    renderer_class = getattr(module, class_name)
    if not isinstance(renderer_class, type):
        raise TypeError(f'renderer class path does not resolve to a class: {plugin.class_path}')
    missing_methods = [
        method_name for method_name in REQUIRED_RENDERER_METHODS
        if not callable(getattr(renderer_class, method_name, None))
    ]
    if missing_methods:
        raise TypeError(
            f'renderer class does not implement LivePlotRenderer methods: {", ".join(missing_methods)}')
    return renderer_class


def _module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


__all__ = [
    'BUILTIN_RENDERER_PLUGINS',
    'REQUIRED_RENDERER_METHODS',
    'RendererPluginRegistry',
    'RendererPluginSpec',
    'RendererStability',
    'create_default_renderer_registry',
    'load_renderer_class',
]
