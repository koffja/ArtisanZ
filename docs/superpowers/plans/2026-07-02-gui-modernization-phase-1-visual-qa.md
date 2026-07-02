# GUI Modernization Phase 1 Visual QA

**Goal:** Re-check the refreshed Widgets main screen after the guarded PyQtGraph embed work, with special focus on LCD spacing/padding, renderer-status chrome, and graph readability.

## Captures

| Scenario | Command Shape | Evidence | Result |
| --- | --- | --- | --- |
| Default historical-profile redraw | `QT_QPA_PLATFORM=offscreen`, default renderer, `profile1.alog` loaded by absolute path | `/tmp/artisanz-phase1-qa-default-profile-abs.png` and `/tmp/artisanz-phase1-qa-default-profile-abs-perf.jsonl` | Historical profile, LCD stack, workspace status dock, and renderer status are visible. LCD cards keep inter-item spacing and the value surfaces remain bottom-aligned. |
| Guarded PyQtGraph live simulator | `QT_QPA_PLATFORM=offscreen`, `ARTISANZ_RENDERER_ID=pyqtgraph-snapshot`, 20s simulator recording | `/tmp/artisanz-pyqtgraph-live-final.png` and `/tmp/artisanz-pyqtgraph-live-final-perf.jsonl` | PyQtGraph surface is nonblank, uses the light UI background, and receives live ET/BT/RoR frame updates. |
| Guarded PyQtGraph native window | Native macOS window, `ARTISANZ_RENDERER_ID=pyqtgraph-snapshot`, 12s simulator recording | `/tmp/artisanz-pyqtgraph-realwindow-final.png` and `/tmp/artisanz-pyqtgraph-realwindow-final-perf.jsonl` | Native-window capture confirms the LCD stack keeps padding, spacing, and bottom-aligned value blocks outside the offscreen backend. |

## Observations

- The earlier LCD defect was not reintroduced: each card has visible outer padding, inter-card spacing, and the colored value block sits flush with the lower content area rather than floating away from the border.
- The PyQtGraph graph surface required a light-theme pass after the first software-rendered capture exposed a dark plot area. Current captures align the plot background, axis pens, and grid with the refreshed Widgets palette.
- The OpenGL embed path is still not promoted. In this environment, a guarded OpenGL target produced a blank graph, consistent with the earlier `QOpenGLWidget` capability probe. Software PyQtGraph is the current guarded path.
- Full language/state coverage still needs a real-device or longer manual session for event-heavy START recording, language switching, and device-specific LCD labels.

## Metrics

| Scenario | Key Metrics |
| --- | --- |
| Default historical-profile redraw | `redraw max=236.974ms avg=152.126ms`; `redraw_keep_view max=171.558ms avg=139.569ms`; `updateBackground max=128.589ms avg=83.509ms`; `updategraphics max=0.007ms avg=0.002ms` |
| Guarded PyQtGraph offscreen live simulator | `redraw max=155.610ms avg=100.076ms`; `updateBackground max=110.425ms avg=51.544ms`; `updategraphics max=41.895ms avg=3.903ms`; `sample_processing max=4.912ms avg=2.389ms` |
| Guarded PyQtGraph native-window live simulator | `redraw max=118.040ms avg=81.885ms`; `updateBackground max=80.907ms avg=38.028ms`; `updategraphics max=37.760ms avg=4.839ms`; `sample_processing max=7.377ms avg=2.897ms` |

## Follow-Up

- Keep Matplotlib as default until PyQtGraph receives longer simulator/device coverage for event markers, background profiles, projections, phases, and export/analysis compatibility.
- Treat OpenGL as pending hardware validation, not as a shipped acceleration claim.
- Continue Phase 3/4 work using the new renderer boundary and workspace chrome rather than editing the LCD surfaces again unless a screenshot exposes a concrete defect.
