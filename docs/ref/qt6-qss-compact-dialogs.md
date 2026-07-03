# Qt 6 QSS Compact Dialog Reference

> Reference document for QSS styling decisions in ArtisanZ gui_theme.py.
> Based on Qt 6.11 official docs, KDE Breeze metrics, and production PyQt6 app analysis (2024-2026).

## Qt 6.5-6.11 QSS Status

**No new QSS sizing features in Qt 6.5-6.11.** The QSS engine is frozen. All size control must come from:
1. QSS `padding` / `min-width` / `min-height` (for widget-internal spacing)
2. `QLayout.setContentsMargins()` + `setSpacing()` (for layout-level spacing) — **cannot be done via QSS**
3. `qproperty-` syntax (escape hatch for Q_PROPERTY values)

### Known Limitations
- `QWidget` does NOT support the box model (padding/margin) — only `QFrame` subclasses do
- `QLayout` objects cannot be styled via QSS (QTBUG-22862, unresolved since 2010)
- `width`/`height` in QSS only work on subcontrols, not on widgets themselves

## Reference Values: KDE Breeze / Fusion (The Standard)

| Metric | Breeze | Fusion | Source |
|---|---|---|---|
| Top-level dialog margin | 10px | 11px | `Layout_TopLevelMarginWidth` |
| Child layout margin | 6px | 9px | `Layout_ChildMarginWidth` |
| Default spacing | 6px | 6px | `Layout_DefaultSpacing` |
| Button internal margin | 6px | 6px | `Button_MarginWidth` |
| Frame width | 2px | 2px | `Frame_FrameWidth` |
| Frame radius | 3px | 2-4px | `Frame_FrameRadius` |

Source: [Breeze metrics](https://invent.kde.org/plasma/breeze/-/commit/21db1883bf51c8cc9c257be59ee9d57f2cb087b6), [KDE-devel thread](https://mail.kde.org/pipermail/kde-devel/2023-December/002268.html)

## Production App Reference Values

| App | QLineEdit padding | QPushButton padding | QComboBox padding | Source |
|---|---|---|---|---|
| KDE Breeze | 3px 6px | 6px | 3px 6px + drop-down width:16px | breezestyle.cpp |
| QGIS Night Mapping | 1px | 3px 5px | 1px 0px 1px 3px | QGIS repo |
| Spyder | 4px 8px | 5px 12px | 4px 8px | stylesheet.py |
| QDarkStyleSheet | 2px | 4px 8px | 2px | darkstyle.qss |
| Qt 6.11 official example | — | 6px | — | stylesheet-examples.html |

## ArtisanZ Compact Dialog Target Values

### Python Layer (apply_modern_dialog_polish)

| Parameter | Old Value | New Value | Rationale |
|---|---|---|---|
| Root layout margin | 14 | 8 | Breeze: 10, we go slightly tighter |
| Root layout spacing | 10 | 6 | Breeze default |
| GroupBox layout margin | 10 | 6 | Breeze child margin |
| GroupBox layout spacing | 8 | 6 | Breeze default |
| Tab layout margin | 10 | 6 | Same as group |
| Nested layout margin | 8 | 6 | Same |
| ComboBox min-width | 104 | 72 | Reduced from "always wide" to "reasonable minimum" |
| LineEdit min-width | 110 | 72 | Same |
| SpinBox min-width | 110 | 72 | Same |

### QSS Layer (modern_application_stylesheet)

| Widget | Old Padding | New Padding | Old min-height | New min-height |
|---|---|---|---|---|
| QGroupBox (dialog) | 10px 8px 8px 8px | 6px 6px 6px 6px | — | — |
| QGroupBox margin-top | 14px | 10px | — | — |
| QLineEdit/QComboBox/QSpinBox | 5px 8px | 3px 6px | 23px | 22px |
| QComboBox right padding | 32px | 22px | — | — |
| QComboBox drop-down width | 28px | 20px | — | — |
| QSpinBox padding-right | 32px | 18px | — | — |
| QSpinBox button width | 20px | 16px | — | — |
| QPushButton (dialog) | 6px 12px | 4px 10px | 24px | 22px |
| QPushButton (non-dialog) | 4px 9px | 4px 9px (no change) | — | — |
| QCheckBox min-height | 24px | 20px | — | — |

## Anti-Patterns to Avoid

1. **Double-stacking**: QSS `padding` + `setContentsMargins()` on same widget = 2× intended gap
2. **QWidget padding**: Only QFrame subclasses support box model
3. **QSS on QLayout**: Never worked, never will (QTBUG-22862)
4. **Excessive padding-right on QComboBox/QSpinBox**: 32px for a 16-20px subcontrol wastes 12-16px
5. **Touch-sized min-heights on desktop**: 24px is touch-target size; desktop needs 20-22px

## Key Sources

- [Qt 6.11 Style Sheet Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [Qt 6.11 Style Sheet Examples](https://doc.qt.io/qt-6.11/stylesheet-examples.html)
- [KDE Breeze metrics](https://invent.kde.org/plasma/breeze/-/commit/21db1883bf51c8cc9c257be59ee9d57f2cb087b6)
- [KDAB "Say No to Qt Style Sheets"](https://www.kdab.com/say-no-to-qt-style-sheets/)
- [QGIS Night Mapping theme](https://github.com/qgis/QGIS/blob/master/resources/themes/Night%20Mapping/style.qss)
- [QDarkStyleSheet](https://github.com/ColinDuquesnoy/QDarkStyleSheet)
- [QTBUG-22862: QLayout cannot be styled](https://bugreports.qt.io/browse/QTBUG-22862)
