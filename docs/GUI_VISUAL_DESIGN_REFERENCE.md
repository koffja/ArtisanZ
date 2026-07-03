# GUI Visual Design Reference

**Status:** Active reference for ArtisanZ Qt Widgets/PyQtGraph visual modernization.

## Direction

ArtisanZ should keep Artisan's dense professional workflow, but move the surface language away from heavy native desktop chrome. The target is a light Morandi palette, flat controls, readable numeric instruments, and graph overlays that are visible without becoming decorative noise.

## Palette

- Main surface: warm off-white or very light green-gray, not pure gray.
- Panel surface: slightly lifted light surface with low-contrast border.
- Primary action: muted green/teal.
- Destructive or stop action: muted clay red.
- Informational accent: controlled cyan/blue, used sparingly.
- Disabled text: low-contrast gray-green.

Avoid glossy gradients, native 3D bevels, heavy shadows, and saturated single-hue screens.

## Dialog Controls

- `QComboBox` must reserve enough right padding for the arrow button. Selected text must never touch or hide under the arrow area.
- Combo popups must use a flat list surface, compact vertical padding, and a clear selected row color.
- Combo arrows should look flat and quiet. Avoid the default raised platform-specific arrow button.
- Combo and spinbox arrows should use explicit flat SVG assets from `src/includes/Icons/`; do not emulate arrows with CSS border triangles because Qt stylesheets do not render them like browsers.
- `QSpinBox`, `QDoubleSpinBox`, `QTimeEdit`, and `QDateEdit` must reserve enough right padding for step buttons. Numeric text must remain fully visible at minimum width.
- Dialog polish should expand old fixed-width controls when legacy code sets widths that are too narrow for modern padding.

Implementation anchor: `artisanlib.gui_theme.apply_modern_dialog_polish()` and `modern_application_stylesheet()`.

## Graph Grid

- Grid visibility follows the existing Axes dialog settings: `time_grid` and `temp_grid`.
- When enabled, PyQtGraph must draw major grid lines only, using the configured time/temperature step values.
- Grid style, width, and opacity must follow the existing Axes dialog controls. Solid, dashed, dash-dot, and dotted styles must map to the visible PyQtGraph grid pen.
- Do not use PyQtGraph's dense default minor-grid look on the main roast chart.
- Grid color should be visible on the light roast canvas but lower priority than curves, events, and guide lines.

Implementation anchor: `artisanlib.plot_pyqtgraph_widget.PyQtGraphMajorGridItem`.

## Phase Backgrounds

- Phase temperature bands follow Artisan's existing `watermarksflag` behavior.
- Bands must render on the initial empty PyQtGraph surface as soon as the renderer target is created.
- Bands must remain behind curves, grid, events, guide lines, and labels.
- Default opacity should be high enough to inspect, but not compete with curve colors.
- Completed-roast development time ranges are separate from horizontal temperature phase bands. Preserve the vertical development block from first crack start to drop when the required event indexes exist.
- Completed roasts should show top phase summaries with duration, percentage, and BT delta. These summaries are analytical context, not decoration.

Implementation anchor: `tgraphcanvas.sync_pyqtgraph_static_overlays_from_canvas()` plus the renderer static overlay snapshot path.

## LCD Telemetry

- Avoid nested card/value-block compositions that can visually separate or misalign.
- Long metric titles should wrap within a fixed-width telemetry column rather than widening the column into the graph.
- Numeric value surfaces should align to their container and keep enough padding for segmented-digit fonts.

## Roast Analysis Overlays

- Main roast events such as CHARGE, DRY, FCs, and DROP must include BT temperature when available.
- Event labels should follow Artisan's original analytical annotation structure: data point marker, leader line, temperature text, and event/time text. Do not reduce main roast events to unlabeled or label-only vertical guide lines.
- Turning point is a first-class main event when `markTPflag` and a valid TP index exist. The PyQtGraph path must show TP with elapsed time and BT temperature, not only CHARGE/DRY/FCs/DROP.
- The right-bottom legend is part of the analytical surface. It should include visible ET/BT and RoR curves while skipping projection/background helper curves unless a future mode explicitly exposes them.
- RoR curves must use sufficient line weight and z-order to stay visible on the right-axis overlay. Saved-profile RoR data should be masked to the same visible segment as the original Matplotlib path and the right axis must include visible RoR values instead of clipping them out.
- Completed-roast phase summary bars should be visually strong enough to read at a glance. First-phase BT rise uses TP-to-DRY temperature delta when TP is available; do not use CHARGE-to-DRY because that can produce a misleading negative value during the turning-point dip.
- Top toolbar graph/navigation icons should come from project-owned flat SVG assets before falling back to Matplotlib resources. Avoid heavy legacy MPL bitmap icons in the modern theme.

## Review Checklist

- Open the Axes dialog and verify combo popup text is not clipped.
- Verify width/opaqueness spinboxes show all digits without overlap with step buttons.
- Enable both grid checkboxes and confirm the main chart shows only major grid lines.
- Enable phase watermarks and confirm phase bands appear before live samples arrive.
- Capture a PyQtGraph smoke screenshot after any renderer or theme change.
