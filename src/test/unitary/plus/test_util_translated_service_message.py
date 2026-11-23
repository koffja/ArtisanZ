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

@pytest.mark.parametrize(
    ('source', 'translated', 'expected'),
    [
        # upstream v5 wording in an English UI
        ('Syncing with the artisan platform', 'Syncing with the artisan platform', 'Syncing with Cotrix'),
        ('artisan platform disconnected', 'artisan platform disconnected', 'Cotrix disconnected'),
        ('Browse to the artisan platform', 'Browse to the artisan platform', 'Browse to Cotrix'),
        ('Sign in to your artisan account', 'Sign in to your artisan account', 'Sign in to your Cotrix account'),
        ('An artisan account unlocks more features.', 'An artisan account unlocks more features.', 'A Cotrix account unlocks more features.'),
        ('Sign in to your artisan account', 'Sign in to your artisan account', 'Sign in to your Cotrix account'),
        # the same strings as upstream's artisan_zh_CN.ts renders them
        ('Syncing with the artisan platform', '与工匠平台同步', '与Cotrix同步'),
        ('Upload to the artisan platform', '上传至手工艺平台', '上传至Cotrix'),
        ("Couldn't connect to the artisan platform", '无法连接到工匠平台', '无法连接到Cotrix'),
        ('Sign in to your artisan account', '登录您的工匠账户', '登录您的Cotrix账户'),
    ],
)
def test_replaces_upstream_v5_wording_with_display_name(
    qapp: object, source: str, translated: str, expected: str
) -> None:
    """Upstream v5 says "artisan platform" / "artisan account"; every rendering becomes Cotrix."""
    from plus.util import translatedServiceMessage

    with patch('plus.util.QApplication') as mock_qapp:
        mock_qapp.translate.return_value = translated
        result = translatedServiceMessage(source, context='Tooltip')

        assert result == expected
        mock_qapp.translate.assert_called_once_with('Tooltip', source)


def _routed_service_sources() -> set[str]:
    """Source strings passed to translatedServiceMessage() in plus/ and the core package."""
    import re
    from pathlib import Path

    src = Path(__file__).parents[3]
    core = next(p for p in src.iterdir() if p.is_dir() and (p / 'main.py').exists())
    sources: set[str] = set()
    call = re.compile(r"translatedServiceMessage\(\s*(['\"])(.*?)\1", re.S)
    for folder in (src / 'plus', core):
        for path in folder.rglob('*.py'):
            sources.update(m.group(2) for m in call.finditer(path.read_text(encoding='utf-8')))
    return sources


def test_zh_cn_renderings_of_routed_strings_are_all_covered_by_the_needles(qapp: object) -> None:
    """A routed string whose zh_CN translation mentions the service must be swapped.

    Upstream is free to pick a new Chinese rendering of the service name. This test
    reads the shipped artisan_zh_CN.ts so such a change fails here instead of
    silently showing the upstream brand in the Chinese UI.
    """
    import xml.etree.ElementTree as ET
    from pathlib import Path

    import re

    from plus import service_identity

    ts = ET.parse(Path(__file__).parents[3] / 'translations' / 'artisan_zh_CN.ts').getroot()
    zh: dict[str, str] = {}
    for message in ts.iter('message'):
        source, translation = message.find('source'), message.find('translation')
        if source is not None and source.text and translation is not None and translation.text:
            zh[source.text] = translation.text

    substitutions = service_identity.brand_substitutions()
    ungrammatical = re.compile(r'\b[tT]he Cotrix\b|\bAn Cotrix\b|\ba an\b|\bA a\b')
    # ways the service name shows up in Chinese or untranslated text
    brand_marks = ('artisan', '工匠', '手工艺', 'Artisan')
    uncovered = []
    for source in sorted(_routed_service_sources()):
        # English: the swap must not leave a dangling article
        swapped = source
        for needle, replacement in substitutions:
            swapped = swapped.replace(needle, replacement)
        if ungrammatical.search(swapped):
            uncovered.append((source, source, swapped))
        translated = zh.get(source)
        if translated is None:
            continue
        swapped = translated
        for needle, replacement in substitutions:
            swapped = swapped.replace(needle, replacement)
        if any(mark in swapped for mark in brand_marks):
            uncovered.append((source, translated, swapped))

    assert uncovered == [], 'service wording not covered by service_identity.brand_substitutions()'
