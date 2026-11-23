"""ArtisanZ's Morandi palette for the button styles upstream generates in styles.py."""
import re

import pytest

from artisanlib.gui_theme import artisan_event_button_style
from artisanlib.styles import (
    artisan_sv_minus_push_button_style,
    artisan_sv_plus_push_button_style,
    push_button_style,
)

# upstream's button colours; none of them may survive in a generated style
UPSTREAM_BUTTON_COLOURS = frozenset({
    '#4c97c3', '#3979ae', '#147bb3', '#116d98', '#116999', '#cc0f50', '#c70d49',
    '#d4336a', '#43a7cf', '#1985ba', '#db5785', '#e480a2', '#64b7d8', '#85cae1',
})


def _declarations(stylesheet: str) -> dict[str, dict[str, str]]:
    """Map pseudo-state -> {property: value} for a QPushButton stylesheet."""
    out: dict[str, dict[str, str]] = {}
    state = ''
    for line in stylesheet.split('\n'):
        header = re.match(r'\s*QPushButton([^{]*)\{', line)
        if header is not None:
            state = header.group(1).strip() or 'normal'
        declaration = re.match(r'\s*(color|background-color):\s*([^;]+);', line)
        if declaration is not None:
            out.setdefault(state, {})[declaration.group(1)] = declaration.group(2).strip()
    return out


def _upstream_colours_left(stylesheet: str) -> set[str]:
    return {c.lower() for c in re.findall(r'#[0-9A-Fa-f]{6}\b', stylesheet)} & UPSTREAM_BUTTON_COLOURS


def test_event_button_style_uses_flat_morandi_colors() -> None:
    style = artisan_event_button_style(60, 30, 3, 11, 12)

    assert 'qlineargradient' not in style
    assert 'background-color: #B4685C' in style
    assert 'background-color: #E3ECEE' in style
    assert 'background-color: #EEF3EA' in style
    assert 'border-radius: 8px' in style
    assert 'min-width: 60px' in style
    assert 'font-size: 11pt' in style
    assert '{min_width}' not in style
    assert not _upstream_colours_left(style)


@pytest.mark.parametrize(
    ('button', 'normal', 'pressed', 'hovered'),
    [
        ('OFF', '#4E7180', '#3E5A66', '#5E889A'),
        ('ON', '#A76557', '#865146', '#BE7D6C'),
        ('STOP', '#4E7180', '#3E5A66', '#5E889A'),
        ('RESET', '#4E7180', '#3E5A66', '#5E889A'),
        ('PID', '#4E7180', '#3E5A66', '#5E889A'),
        ('PIDactive', '#A76557', '#865146', '#BE7D6C'),
    ],
)
@pytest.mark.parametrize('simulator', [False, True])
def test_main_buttons_use_the_morandi_palette(
    button: str, simulator: bool, normal: str, pressed: str, hovered: str
) -> None:
    style = push_button_style(simulator, button, 40, 120, 14, 24)
    declarations = _declarations(style)

    # OFF, ON and STOP are painted buttons in regular mode and white buttons with
    # coloured text in simulator mode, so the palette colour is whichever property
    # the state paints
    for state, expected in (('normal', normal), (':pressed', pressed), (':hover:!pressed', hovered)):
        assert expected in declarations[state].values(), (state, declarations[state])
    assert not _upstream_colours_left(style)


@pytest.mark.parametrize(
    ('style_function', 'normal', 'pressed', 'hovered'),
    [
        (artisan_sv_plus_push_button_style, '#C18A6B', '#9A6E55', '#D1A082'),
        (artisan_sv_minus_push_button_style, '#90A1A8', '#738185', '#A6B5BB'),
    ],
)
def test_sv_buttons_are_flat_morandi(
    style_function: object, normal: str, pressed: str, hovered: str
) -> None:
    style = style_function(40, 14, 24)  # type: ignore[operator]
    declarations = _declarations(style)

    assert 'qlineargradient' not in style
    assert declarations['normal']['background-color'] == normal
    assert declarations[':pressed']['background-color'] == pressed
    assert declarations[':hover:!pressed']['background-color'] == hovered
    assert not _upstream_colours_left(style)
