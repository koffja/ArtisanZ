---
phase: 1.28-report-graph-handoff
reviewed: 2026-07-23T14:34:28Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - src/artisanlib/plot_report_renderer.py
  - src/artisanlib/main.py
  - src/test/unitary/artisanlib/test_plot_report_renderer.py
  - docs/superpowers/plans/2026-07-23-gui-modernization-phase-1-28-report-graph-handoff.md
  - docs/superpowers/plans/2026-06-29-gui-modernization-roadmap.md
findings:
  critical: 0
  warning: 1
  info: 0
  total: 1
status: issues_found
---

# Phase 1.28: Code Review Report

**Reviewed:** 2026-07-23T14:34:28Z  
**Depth:** standard  
**Files Reviewed:** 5  
**Status:** issues_found  
**Verdict:** NEEDS PATCH

## Summary

Focused review covered renderer selection, `roastReport()` integration, report template compatibility, fallback behavior, i18n-sensitive snapshot flow, and roadmap/handoff claims. Matplotlib remains the default SVG path. Explicit PyQtGraph selection works. Saved `profile1.alog` export produced a nonblank PNG with 3826 sampled non-background pixels. Focused tests: `12 passed`; compile, Ruff, and diff checks passed.

One warning remains: a blank PyQtGraph PNG can be treated as a successful render, so the required Matplotlib fallback is not guaranteed for blank-output failures.

## Warnings

### WR-01: Blank PyQtGraph output bypasses fallback

**File:** `/Users/chengzhe/Projects/ArtisanZ/src/artisanlib/plot_report_renderer.py:68-75`

**Issue:** `export_pyqtgraph_report_graph()` returns `PyQtGraphSnapshotPngResult.sampled_non_background_pixel_count`, but `render_report_graph()` ignores it. The lower-level PNG saver accepts a successfully saved but blank pixmap and returns a zero non-background count without raising. The wrapper then returns the PNG as `backend='pyqtgraph'`, so `roastReport()` embeds a blank graph instead of using its Matplotlib fallback.

**Fix:** Validate the export evidence before returning success and raise inside the existing `try` block when the file is empty or has no non-background pixels, allowing the existing fallback path to run.

```python
            result = export_pyqtgraph_report_graph(
                source,
                pyqtgraph_path,
                width=width,
                height=height,
                use_opengl=use_opengl,
            )
            if result.byte_count <= 0 or result.sampled_non_background_pixel_count <= 0:
                raise RuntimeError('PyQtGraph report graph export was blank')
            return ReportGraphRenderResult('pyqtgraph', str(pyqtgraph_path))
```

---

_Reviewed: 2026-07-23T14:34:28Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
