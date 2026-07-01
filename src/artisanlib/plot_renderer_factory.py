from __future__ import annotations

import importlib.util
from typing import Any, cast

from artisanlib.plot_renderer_registry import (
    RendererPluginRegistry,
    RendererPluginSpec,
    create_default_renderer_registry,
)
from artisanlib.plot_snapshot import LivePlotRenderer


class RendererDependencyError(RuntimeError):
    pass


def missing_renderer_dependencies(plugin: RendererPluginSpec) -> tuple[str, ...]:
    return tuple(
        module_name for module_name in plugin.dependencies
        if importlib.util.find_spec(module_name) is None
    )


def create_renderer(
        renderer_id: str,
        *,
        registry: RendererPluginRegistry | None = None,
        **constructor_kwargs: Any) -> LivePlotRenderer:
    renderer_registry = registry or create_default_renderer_registry()
    plugin = renderer_registry.get(renderer_id)
    missing_dependencies = missing_renderer_dependencies(plugin)
    if missing_dependencies:
        raise RendererDependencyError(
            f'renderer plugin {renderer_id} missing dependencies: {", ".join(missing_dependencies)}')
    renderer_class = renderer_registry.load_renderer_class(renderer_id)
    return cast(LivePlotRenderer, renderer_class(**constructor_kwargs))


__all__ = [
    'RendererDependencyError',
    'create_renderer',
    'missing_renderer_dependencies',
]
