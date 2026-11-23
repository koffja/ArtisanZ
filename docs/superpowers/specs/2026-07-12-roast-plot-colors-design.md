# Roast Plot Colors Design

## Goal

Improve the PyQtGraph roast plot so BT remains blue, background curves are readable without becoming heavy, and phase summary bars are lighter and thinner.

## Approved Design

- Disable the default BT temperature gradient and render BT with the configured solid blue color (`#3A7CA5` by default).
- Raise the application default background opacity from `0.20` to `0.35`, while preserving an explicit user-selected opacity.
- Restrict curve shadows to named temperature/RoR curves. Background curves and phase summary bars must not receive the black shadow pen.
- Reduce phase summary bar width from `14` to `10` and use a slightly stronger light fill so the bar remains visible without a thick dark outline.

## Scope

The active PyQtGraph path is the only rendering path in scope. Matplotlib compatibility code is not changed. Regression tests cover BT pen selection, background opacity defaults, shadow filtering, and phase summary pen styling.
