"""Tests for the unified plus.util.translatedServiceMessage function.

Verifies that any source string containing 'artisan.plus' is post-processed
to replace it with the configured service display name (Cotrix).
"""
import sys
from unittest.mock import patch

import pytest


@pytest.fixture(scope='module')
def qapp() -> object:
    """Ensure QApplication exists for translate() calls."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_import_from_plus_util() -> None:
    """Function is importable from plus.util."""
    from plus.util import translatedServiceMessage
    assert callable(translatedServiceMessage)


def test_replaces_artisan_plus_with_display_name(qapp: object) -> None:
    """The literal 'artisan.plus' in source is replaced at runtime."""
    from plus.util import translatedServiceMessage
    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = 'Connect artisan.plus'
        result = translatedServiceMessage('Connect artisan.plus')
        assert result == 'Connect Cotrix'
        mock_qapp.translate.assert_called_once_with('Plus', 'Connect artisan.plus')


def test_default_context_is_plus(qapp: object) -> None:
    """Default context is 'Plus' (matches plus.controller legacy behavior)."""
    from plus.util import translatedServiceMessage
    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = 'x'
        translatedServiceMessage('x')
        mock_qapp.translate.assert_called_once_with('Plus', 'x')


def test_accepts_explicit_context(qapp: object) -> None:
    """Explicit context kwarg overrides default."""
    from plus.util import translatedServiceMessage
    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = 'x'
        translatedServiceMessage('x', context='Tooltip')
        mock_qapp.translate.assert_called_once_with('Tooltip', 'x')


def test_handles_translated_string_with_brand(qapp: object) -> None:
    """Replace operates on the TRANSLATED string, not just source."""
    from plus.util import translatedServiceMessage
    with patch('plus.util.QApplication') as mock_qapp:
        # Simulate zh_CN translation containing the literal
        mock_qapp.translate.return_value = '已连接到artisan.plus'
        result = translatedServiceMessage('Connected to artisan.plus')
        assert result == '已连接到Cotrix'


def test_no_artisan_plus_in_source_passes_through(qapp: object) -> None:
    """Strings without 'artisan.plus' are returned unchanged after translate."""
    from plus.util import translatedServiceMessage
    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = 'Hello World'
        assert translatedServiceMessage('Hello World') == 'Hello World'


@pytest.mark.skip(reason='requires full Artisan QApplication init')
def test_controller_reexports_same_function_as_util(qapp: object) -> None:
    """plus.controller.translatedServiceMessage is the same object as plus.util's.

    This protects the backward-compatibility re-export at plus/controller.py:47.
    """
    from plus.util import translatedServiceMessage as via_util
    from plus.controller import translatedServiceMessage as via_controller
    assert via_controller is via_util, (
        'plus.controller.translatedServiceMessage must be the same object as '
        'plus.util.translatedServiceMessage (re-export contract)'
    )
