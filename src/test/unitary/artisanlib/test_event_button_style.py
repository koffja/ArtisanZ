from artisanlib.event_button_style import artisan_event_button_style


def test_event_button_style_uses_flat_colors() -> None:
    assert 'qlineargradient' not in artisan_event_button_style
    assert 'background-color: #A76557' in artisan_event_button_style
    assert 'border-radius: 6px' in artisan_event_button_style
