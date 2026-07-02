from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
import os

from artisanlib.plot_renderer_plugin_loader import build_runtime_registry
from artisanlib.plot_renderer_registry import RendererPluginRegistry, RendererPluginSpec


ARTISANZ_RENDERER_ID = 'ARTISANZ_RENDERER_ID'
DEFAULT_RENDERER_ID = 'pyqtgraph-snapshot'
DEFAULT_RENDERER_LABEL = 'PyQtGraph Snapshot'
MATPLOTLIB_RENDERER_ID = 'matplotlib-snapshot'
MATPLOTLIB_RENDERER_LABEL = 'Matplotlib Snapshot'

type RendererFallbackReason = Literal[
    'unknown',
    'unavailable',
    'default_unavailable',
    'selection_error',
]


@dataclass(frozen=True, slots=True)
class RendererSelection:
    requested_renderer_id: str
    renderer_id: str
    plugin: RendererPluginSpec
    registry: RendererPluginRegistry
    fallback_reason: RendererFallbackReason | None = None

    @property
    def used_fallback(self) -> bool:
        return self.fallback_reason is not None


class RendererSelectionError(RuntimeError):
    pass


def configured_renderer_id(
        *,
        env: Mapping[str, str] | None = None,
        default_renderer_id: str = DEFAULT_RENDERER_ID) -> str:
    runtime_env = os.environ if env is None else env
    renderer_id = runtime_env.get(ARTISANZ_RENDERER_ID, '').strip()
    return renderer_id or default_renderer_id


def select_renderer(
        *,
        registry: RendererPluginRegistry | None = None,
        env: Mapping[str, str] | None = None,
        default_renderer_id: str = DEFAULT_RENDERER_ID) -> RendererSelection:
    renderer_registry = registry or build_runtime_registry(env=env)
    requested_renderer_id = configured_renderer_id(env=env, default_renderer_id=default_renderer_id)
    plugin = _get_available_plugin(renderer_registry, requested_renderer_id)
    if plugin is not None:
        return RendererSelection(
            requested_renderer_id=requested_renderer_id,
            renderer_id=requested_renderer_id,
            plugin=plugin,
            registry=renderer_registry,
        )

    fallback_reason = _fallback_reason(renderer_registry, requested_renderer_id)
    default_plugin = _get_available_plugin(renderer_registry, default_renderer_id)
    if default_plugin is not None:
        return RendererSelection(
            requested_renderer_id=requested_renderer_id,
            renderer_id=default_renderer_id,
            plugin=default_plugin,
            registry=renderer_registry,
            fallback_reason=fallback_reason,
        )

    fallback_plugin = _first_available_plugin(renderer_registry)
    if fallback_plugin is None:
        raise RendererSelectionError('no available renderer plugins')
    return RendererSelection(
        requested_renderer_id=requested_renderer_id,
        renderer_id=fallback_plugin.renderer_id,
        plugin=fallback_plugin,
        registry=renderer_registry,
        fallback_reason='default_unavailable',
    )


def available_renderer_ids(registry: RendererPluginRegistry) -> tuple[str, ...]:
    return tuple(plugin.renderer_id for plugin in registry.plugins(include_unavailable=False))


def _get_available_plugin(
        registry: RendererPluginRegistry,
        renderer_id: str) -> RendererPluginSpec | None:
    try:
        plugin = registry.get(renderer_id)
    except KeyError:
        return None
    return plugin if plugin.is_available() else None


def _fallback_reason(
        registry: RendererPluginRegistry,
        renderer_id: str) -> RendererFallbackReason:
    try:
        plugin = registry.get(renderer_id)
    except KeyError:
        return 'unknown'
    return 'unavailable' if not plugin.is_available() else 'unknown'


def _first_available_plugin(registry: RendererPluginRegistry) -> RendererPluginSpec | None:
    plugins = registry.plugins(include_unavailable=False)
    return plugins[0] if plugins else None


__all__ = [
    'ARTISANZ_RENDERER_ID',
    'DEFAULT_RENDERER_ID',
    'DEFAULT_RENDERER_LABEL',
    'MATPLOTLIB_RENDERER_ID',
    'MATPLOTLIB_RENDERER_LABEL',
    'RendererFallbackReason',
    'RendererSelection',
    'RendererSelectionError',
    'available_renderer_ids',
    'configured_renderer_id',
    'select_renderer',
]
