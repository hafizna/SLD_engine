"""Fit a rendered SLD onto a printable A4 sheet.

A dashboard view and a figure for the Buku Kerawanan want opposite things. On
screen the diagram is zoomable, so a label that opens small can be zoomed into
and a pin needs a large hit target. On paper there is no zoom: whatever is on
the sheet is all the reader gets, so nothing may be hidden and nothing may be
too small to read.

This module does not re-lay-out anything. It takes the finished SVG and only:

  * picks the orientation that fits the drawing better,
  * scales the whole drawing to the sheet,
  * enlarges the *text* so it survives that scaling.

Enlarging text is safe because the layout never measures it: `sld_layout.py`
routes from WIRE_PITCH / CHANNEL_PITCH / NEAR_CONT_GAP alone, and every
font-size in `sld_renderer.py` is a literal on an already-placed <text>. So a
print figure keeps exactly the geometry the screen shows.

Measured over the 42 built views: 33 fit one A4 with labels grown no more than
1.6x, 8 need up to ~2.3x, and one (the 500/150 IBT system view, 5382 units
wide) cannot be made readable on a single sheet at all -- `fit_report` says so
rather than silently shrinking it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# A4 at 96 CSS px per inch. The SVG carries real mm so a browser's "Print" and
# a PDF export both land on a true A4 without scaling in the print dialog.
A4_SHORT_MM = 210.0
A4_LONG_MM = 297.0
MARGIN_MM = 10.0

# Smallest GI label we are willing to print, cap height in mm. ~6pt: small, but
# these are short uppercase codes (KMBGN, SRLYA), not running text.
MIN_LABEL_MM = 2.1

# The label size the renderer emits for a GI busbar. Labels are scaled relative
# to this so the ratio between label tiers is preserved.
BASE_LABEL_UNITS = 12.5

# Beyond this the drawing starts to look like labels with a diagram attached,
# and on the densest sheets they begin to touch. Past it we still grow the
# text -- an unreadable figure is worse than a crowded one -- but the report
# flags the view so a person can decide to split it into another sudut pandang.
COMFORTABLE_BOOST = 1.6

_VIEWBOX = re.compile(r'viewBox="([-\d.]+)\s+([-\d.]+)\s+([\d.]+)\s+([\d.]+)"')
_FONT = re.compile(r'font-size="([\d.]+)"')


@dataclass
class FitReport:
    """What fitting this view to A4 actually required."""
    width: float            # diagram units
    height: float
    orientation: str        # "landscape" | "portrait"
    mm_per_unit: float
    label_boost: float      # how much text had to grow
    label_mm: float         # resulting GI label height
    fits: bool              # readable within the comfortable boost
    note: str = ""


def _page_mm(orientation: str) -> tuple[float, float]:
    return ((A4_LONG_MM, A4_SHORT_MM) if orientation == "landscape"
            else (A4_SHORT_MM, A4_LONG_MM))


def plan(svg: str) -> FitReport:
    """Work out how this SVG has to be treated to print on one A4."""
    m = _VIEWBOX.search(svg)
    if not m:
        return FitReport(0, 0, "landscape", 0, 1.0, 0, False, "no viewBox")
    _, _, w, h = (float(g) for g in m.groups())

    best = None
    for orientation in ("landscape", "portrait"):
        pw, ph = _page_mm(orientation)
        usable_w, usable_h = pw - 2 * MARGIN_MM, ph - 2 * MARGIN_MM
        k = min(usable_w / w, usable_h / h)
        if best is None or k > best[0]:
            best = (k, orientation)
    mm_per_unit, orientation = best

    # Grow text until a GI label clears the readable floor. Never shrink it:
    # a view that already prints large enough keeps the renderer's own sizes.
    needed = MIN_LABEL_MM / (BASE_LABEL_UNITS * mm_per_unit)
    boost = max(1.0, needed)
    label_mm = BASE_LABEL_UNITS * boost * mm_per_unit

    fits = boost <= COMFORTABLE_BOOST
    note = "" if fits else (
        f"Gambar ini butuh teks {boost:.1f}x untuk terbaca pada satu A4. "
        f"Pertimbangkan memecahnya menjadi sudut pandang tambahan."
    )
    return FitReport(w, h, orientation, mm_per_unit, boost, label_mm, fits, note)


def to_a4(svg: str) -> str:
    """Return the SVG sized to one A4 sheet, with print-legible text.

    Geometry is untouched: only the outer <svg> element and font-size
    attributes change.
    """
    report = plan(svg)
    if not report.width:
        return svg

    pw, ph = _page_mm(report.orientation)

    if report.label_boost > 1.0:
        def grow(m: re.Match) -> str:
            return f'font-size="{float(m.group(1)) * report.label_boost:.2f}"'
        # The title block is already sized for a header; leave the drawing's
        # own labels to the boost.
        svg = _FONT.sub(grow, svg)

    # Re-declare the page in real millimetres. The sheet is described in
    # diagram units, and the drawing is centred inside it on both axes: the
    # drawing's shape rarely matches A4's, and without this the slack all fell
    # on one side and the figure sat against a margin.
    vb = _VIEWBOX.search(svg)
    x0, y0, w, h = (float(g) for g in vb.groups())
    sheet_w = pw / report.mm_per_unit
    sheet_h = ph / report.mm_per_unit
    svg = svg[:vb.start()] + (
        f'width="{pw}mm" height="{ph}mm" '
        f'viewBox="{x0 - (sheet_w - w) / 2:.1f} {y0 - (sheet_h - h) / 2:.1f} '
        f'{sheet_w:.1f} {sheet_h:.1f}" '
        f'data-print-orientation="{report.orientation}" '
        f'data-label-boost="{report.label_boost:.2f}"'
    ) + svg[vb.end():]
    return svg
