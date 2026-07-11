from __future__ import annotations

from artisanlib.plot_pyqtgraph_overlays import apply_shadow_pens


class FakePen:
    def __init__(self, width: int) -> None:
        self.width_value = width

    def color(self) -> object:
        return object()


class FakePyQtGraph:
    @staticmethod
    def mkPen(_: str, *, width: int) -> FakePen:
        return FakePen(width)


class FakeDataItem:
    def __init__(self, name: str) -> None:
        self.opts = {'name': name, 'pen': {'width': 1}}
        self.shadow_pen: object | None = None

    def setShadowPen(self, pen: object | None) -> None:  # noqa: N802
        self.shadow_pen = pen


class FakePlot:
    def __init__(self, *items: FakeDataItem) -> None:
        self._items = items

    def listDataItems(self) -> list[FakeDataItem]:  # noqa: N802
        return list(self._items)


def test_apply_shadow_pens_skips_background_curves() -> None:
    foreground = FakeDataItem('BT')
    background = FakeDataItem('Background BT')
    phase_bar = FakeDataItem('')

    count = apply_shadow_pens(FakePlot(foreground, background, phase_bar), FakePyQtGraph)

    assert count == 1
    assert foreground.shadow_pen is not None
    assert background.shadow_pen is None
    assert phase_bar.shadow_pen is None
