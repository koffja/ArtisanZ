from artisanlib.event_button_style import artisan_event_button_style


def test_event_button_style_uses_flat_colors() -> None:
    assert 'qlineargradient' not in artisan_event_button_style
    assert 'background-color: #B4685C' in artisan_event_button_style
    assert 'background-color: #E3ECEE' in artisan_event_button_style
    assert 'background-color: #EEF3EA' in artisan_event_button_style
    assert 'border-radius: 8px' in artisan_event_button_style
