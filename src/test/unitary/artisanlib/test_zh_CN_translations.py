"""ArtisanZ ships zh_CN complete: no English string may reach the Chinese UI untranslated."""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path


def _catalog() -> Path:
    return Path(__file__).parents[3] / 'translations' / 'artisan_zh_CN.ts'


def _unfinished_english_messages() -> list[tuple[str, str]]:
    untranslated: list[tuple[str, str]] = []
    for context in ET.parse(_catalog()).getroot().iter('context'):
        name = context.find('name')
        for message in context.iter('message'):
            source, translation = message.find('source'), message.find('translation')
            if source is None or source.text is None or translation is None:
                continue
            if translation.get('type') != 'unfinished':
                continue
            # sources that are Chinese already need no translation
            if all(ord(character) < 128 for character in source.text.strip()):
                untranslated.append((name.text if name is not None else '', source.text))
    return sorted(set(untranslated))


def test_zh_CN_has_no_untranslated_english_strings() -> None:
    """A new string (from ArtisanZ or from an upstream sync) has to be translated, not shipped in English."""
    assert _unfinished_english_messages() == []


def test_compiled_zh_CN_catalog_translates_artisanz_strings() -> None:
    """The shipped .qm carries the translations of the .ts."""
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PyQt6.QtCore import QCoreApplication, QTranslator

    app = QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator(app)

    assert translator.load(str(_catalog().with_suffix('.qm')))

    assert translator.translate('Menu', 'Roast Control') == '烘焙控制'
    assert translator.translate('Menu', 'Workspace Status') == '工作区状态'
    assert translator.translate('Label', 'Compare Roasts') == '对比烘焙记录'
    assert translator.translate('Message', 'Need at least 2 comparison roasts') == '至少需要 2 条对比烘焙记录'
