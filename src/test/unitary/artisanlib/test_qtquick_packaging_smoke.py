from __future__ import annotations

import importlib
import os
from pathlib import Path
import subprocess
import sys

import pytest

from artisanlib.qtquick_packaging_smoke import (
    QTQUICK_HIDDEN_IMPORTS,
    import_qtquick_modules,
    pyinstaller_version,
    spec_contains_string_literal,
    validate_pyinstaller_qtquick_specs,
)


def test_qtquick_packaging_smoke_imports_real_modules() -> None:
    module_files = import_qtquick_modules()

    assert set(module_files) == set(QTQUICK_HIDDEN_IMPORTS)
    for module_name, module_file in module_files.items():
        importlib.import_module(module_name)
        assert module_file


def test_qtquick_packaging_smoke_validates_platform_specs() -> None:
    src_dir = Path(__file__).parents[3]

    validate_pyinstaller_qtquick_specs(src_dir)


def test_qtquick_packaging_smoke_detects_missing_hidden_import(tmp_path: Path) -> None:
    for spec_name in ('artisan-linux.spec', 'artisan-mac.spec', 'artisan-win.spec'):
        (tmp_path / spec_name).write_text("'PyQt6.QtQml'\n'PyQt6.QtQuick'\n", encoding='utf-8')

    with pytest.raises(RuntimeError, match='missing QtQuick hidden imports'):
        validate_pyinstaller_qtquick_specs(tmp_path)


def test_qtquick_packaging_smoke_matches_hidden_imports_exactly() -> None:
    spec_text = "'PyQt6.QtQml'\n'PyQt6.QtQuickWidgets'\n"

    assert spec_contains_string_literal(spec_text, 'PyQt6.QtQuickWidgets') is True
    assert spec_contains_string_literal(spec_text, 'PyQt6.QtQuick') is False


def test_qtquick_packaging_smoke_detects_phantom_hidden_import(tmp_path: Path) -> None:
    spec_text = "\n".join((
        "'PyQt6.QtQml'",
        "'PyQt6.QtQuick'",
        "'PyQt6.QtQuickWidgets'",
    ))
    for spec_name in ('artisan-linux.spec', 'artisan-mac.spec', 'artisan-win.spec'):
        (tmp_path / spec_name).write_text(spec_text, encoding='utf-8')
    (tmp_path / 'artisan-mac.spec').write_text(
        f"{spec_text}\n'PyQt6.QtQmlModels'\n",
        encoding='utf-8')

    with pytest.raises(RuntimeError, match='phantom PyQt hidden imports'):
        validate_pyinstaller_qtquick_specs(tmp_path)


def test_qtquick_packaging_smoke_runs_widget_path() -> None:
    src_dir = Path(__file__).parents[3]
    env = os.environ.copy()
    env['QT_QPA_PLATFORM'] = 'offscreen'

    result = subprocess.run(
        [sys.executable, '-m', 'artisanlib.qtquick_packaging_smoke'],
        check=False,
        cwd=src_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=30)

    assert result.returncode == 0, result.stderr
    assert 'Workspace Status QML widget: ready 320x156' in result.stdout


def test_pyinstaller_is_available_for_packaging_smoke() -> None:
    assert pyinstaller_version()
