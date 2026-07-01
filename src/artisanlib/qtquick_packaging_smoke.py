from __future__ import annotations

import importlib
import os
import re
import sys
from pathlib import Path
from typing import Final


QTQUICK_HIDDEN_IMPORTS: Final[tuple[str, ...]] = (
    'PyQt6.QtQml',
    'PyQt6.QtQuick',
    'PyQt6.QtQuickWidgets',
)

PHANTOM_QTQUICK_HIDDEN_IMPORTS: Final[tuple[str, ...]] = (
    'PyQt6.QtQmlMeta',
    'PyQt6.QtQmlModels',
    'PyQt6.QtQmlWorkerScript',
)

PYINSTALLER_SPEC_NAMES: Final[tuple[str, ...]] = (
    'artisan-linux.spec',
    'artisan-mac.spec',
    'artisan-win.spec',
)


def default_src_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def pyinstaller_version() -> str:
    pyinstaller = importlib.import_module('PyInstaller')
    return str(pyinstaller.__version__)


def import_qtquick_modules() -> dict[str, str]:
    return {
        module_name: str(getattr(importlib.import_module(module_name), '__file__', 'built-in'))
        for module_name in QTQUICK_HIDDEN_IMPORTS
    }


def spec_contains_string_literal(spec_text: str, value: str) -> bool:
    return re.search(rf'(?<![\w.])["\']{re.escape(value)}["\'](?![\w.])', spec_text) is not None


def validate_pyinstaller_qtquick_specs(src_dir: Path | None = None) -> None:
    src_path = src_dir or default_src_dir()
    for spec_name in PYINSTALLER_SPEC_NAMES:
        spec_text = (src_path / spec_name).read_text(encoding='utf-8')
        missing = [
            module_name for module_name in QTQUICK_HIDDEN_IMPORTS
            if not spec_contains_string_literal(spec_text, module_name)
        ]
        if missing:
            raise RuntimeError(f'{spec_name} missing QtQuick hidden imports: {", ".join(missing)}')
        phantom = [
            module_name for module_name in PHANTOM_QTQUICK_HIDDEN_IMPORTS
            if spec_contains_string_literal(spec_text, module_name)
        ]
        if phantom:
            raise RuntimeError(f'{spec_name} contains phantom PyQt hidden imports: {", ".join(phantom)}')


def run_qtquick_widget_smoke() -> tuple[int, int]:
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

    from PyQt6.QtWidgets import QApplication

    from artisanlib.ui_workspaces import WorkspaceMode
    from artisanlib.workspace_status_model import (
        WorkspaceStatusModel,
        create_workspace_status_widget,
    )

    _app = QApplication.instance() or QApplication([])
    model = WorkspaceStatusModel(WorkspaceMode.QC_ANALYSIS)
    widget = create_workspace_status_widget(model)
    try:
        if widget.status() != widget.Status.Ready:
            errors = '; '.join(error.toString() for error in widget.errors())
            raise RuntimeError(f'QQuickWidget failed to load Workspace Status QML: {errors}')
        if widget.rootObject() is None:
            raise RuntimeError('QQuickWidget loaded without a root object')
        return widget.minimumWidth(), widget.minimumHeight()
    finally:
        widget.deleteLater()


def main() -> int:
    try:
        version = pyinstaller_version()
        validate_pyinstaller_qtquick_specs()
        module_files = import_qtquick_modules()
        width, height = run_qtquick_widget_smoke()
    except Exception as exc: # pylint: disable=broad-except
        print(f'QtQuick packaging smoke failed: {exc}', file=sys.stderr)
        return 1

    print(f'PyInstaller {version}')
    for module_name, module_file in module_files.items():
        print(f'{module_name}: {module_file}')
    print(f'Workspace Status QML widget: ready {width}x{height}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
