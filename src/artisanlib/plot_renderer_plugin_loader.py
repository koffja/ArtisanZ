from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
import ast
import hashlib
import importlib.util
import os
import sys
import warnings

from artisanlib.plot_renderer_registry import (
    RendererPluginRegistry,
    RendererPluginSpec,
    create_default_renderer_registry,
)


ARTISANZ_RENDERER_PLUGIN_PATH = 'ARTISANZ_RENDERER_PLUGIN_PATH'


def discover_external_renderer_plugins(
        search_paths: Sequence[str | os.PathLike[str]]) -> tuple[RendererPluginSpec, ...]:
    plugins: list[RendererPluginSpec] = []
    for search_path in search_paths:
        directory = Path(search_path)
        if not directory.is_dir():
            continue
        for plugin_file in sorted(directory.glob('*.py')):
            if plugin_file.name.startswith('_'):
                continue
            plugins.extend(_load_renderer_plugins_from_file(plugin_file))
    return tuple(plugins)


def build_runtime_registry(
        *,
        search_paths: Sequence[str | os.PathLike[str]] | None = None,
        env: Mapping[str, str] | None = None) -> RendererPluginRegistry:
    registry = create_default_renderer_registry()
    for plugin in discover_external_renderer_plugins(_resolve_search_paths(search_paths, env)):
        try:
            registry.register(plugin)
        except ValueError as exc:
            _warn_plugin_registration_failure(plugin, str(exc))
    return registry


def _resolve_search_paths(
        search_paths: Sequence[str | os.PathLike[str]] | None,
        env: Mapping[str, str] | None) -> tuple[str | os.PathLike[str], ...]:
    if search_paths is not None:
        return tuple(search_paths)
    runtime_env = os.environ if env is None else env
    configured_paths = runtime_env.get(ARTISANZ_RENDERER_PLUGIN_PATH, '')
    return tuple(path for path in configured_paths.split(os.pathsep) if path)


def _load_renderer_plugins_from_file(plugin_file: Path) -> tuple[RendererPluginSpec, ...]:
    if not _defines_register_renderer_plugins(plugin_file):
        return ()

    module_name = _module_name_for_plugin_file(plugin_file)
    spec = importlib.util.spec_from_file_location(module_name, plugin_file)
    if spec is None or spec.loader is None:
        _warn_plugin_failure(plugin_file, 'could not create import spec')
        return ()

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - exercised through concrete exception types
        sys.modules.pop(module_name, None)
        _warn_plugin_failure(plugin_file, f'failed to import plugin: {exc}')
        return ()

    register_plugins = getattr(module, 'register_renderer_plugins', None)
    if register_plugins is None:
        sys.modules.pop(module_name, None)
        return ()
    if not callable(register_plugins):
        sys.modules.pop(module_name, None)
        _warn_plugin_failure(plugin_file, 'register_renderer_plugins is not callable')
        return ()

    try:
        plugins = _validated_plugin_specs(plugin_file, register_plugins())
    except Exception as exc:  # pragma: no cover - exercised through concrete exception types
        sys.modules.pop(module_name, None)
        _warn_plugin_failure(plugin_file, f'failed to register plugins: {exc}')
        return ()
    if not plugins:
        sys.modules.pop(module_name, None)
    return plugins


def _defines_register_renderer_plugins(plugin_file: Path) -> bool:
    try:
        tree = ast.parse(plugin_file.read_text(encoding='utf-8'), filename=str(plugin_file))
    except (OSError, SyntaxError) as exc:
        _warn_plugin_failure(plugin_file, f'could not inspect plugin: {exc}')
        return False
    return any(
        isinstance(node, ast.FunctionDef) and node.name == 'register_renderer_plugins'
        for node in tree.body
    )


def _validated_plugin_specs(
        plugin_file: Path,
        plugin_specs: RendererPluginSpec | Iterable[object]) -> tuple[RendererPluginSpec, ...]:
    raw_plugins = (plugin_specs,) if isinstance(plugin_specs, RendererPluginSpec) else tuple(plugin_specs)
    valid_plugins: list[RendererPluginSpec] = []
    for plugin in raw_plugins:
        if isinstance(plugin, RendererPluginSpec):
            valid_plugins.append(plugin)
        else:
            _warn_plugin_failure(plugin_file, f'ignored non-RendererPluginSpec entry: {plugin!r}')
    return tuple(valid_plugins)


def _module_name_for_plugin_file(plugin_file: Path) -> str:
    safe_stem = ''.join(character if character.isalnum() else '_' for character in plugin_file.stem)
    digest = hashlib.sha256(str(plugin_file.resolve()).encode('utf-8')).hexdigest()[:12]
    return f'_artisanz_renderer_plugin_{safe_stem}_{digest}'


def _warn_plugin_failure(plugin_file: Path, message: str) -> None:
    warnings.warn(
        f'ignored renderer plugin {plugin_file}: {message}',
        RuntimeWarning,
        stacklevel=2,
    )


def _warn_plugin_registration_failure(plugin: RendererPluginSpec, message: str) -> None:
    warnings.warn(
        f'ignored renderer plugin {plugin.renderer_id}: {message}',
        RuntimeWarning,
        stacklevel=2,
    )


__all__ = [
    'ARTISANZ_RENDERER_PLUGIN_PATH',
    'build_runtime_registry',
    'discover_external_renderer_plugins',
]
