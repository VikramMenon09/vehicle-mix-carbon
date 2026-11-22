"""Small set of vector drawing primitives for the research paper."""

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph

W, H = 612, 792
LEFT, RIGHT = 56, 556
INK = colors.HexColor("#192B30")
MUTED = colors.HexColor("#495C61")
GREEN = colors.HexColor("#006A62")
OCHRE = colors.HexColor("#A44C21")
RULE = colors.HexColor("#ABBAB9")
LIGHT = colors.HexColor("#EAF2F0")
GRID = colors.HexColor("#DFE6E5")
PAPER = colors.white


def text(c, x, y, value, font="Helvetica", size=10, color=INK, align="left"):
    c.setFillColor(color)
    c.setFont(font, size)
    draw = {"left": c.drawString, "right": c.drawRightString, "center": c.drawCentredString}
    draw[align](x, H - y, str(value))


def line(c, x1, y1, x2, y2, color=RULE, width=0.6, dash=None):
    c.saveState()
    c.setStrokeColor(color)
    c.setLineWidth(width)
    if dash:
        c.setDash(dash)
    c.line(x1, H - y1, x2, H - y2)
    c.restoreState()


def block(c, x, y, width, height, color):
    c.setFillColor(color)
    c.rect(x, H - y - height, width, height, fill=1, stroke=0)


class Page:
    def __init__(self, canvas, number, section):
        self.c = canvas
        self.y = 66
        self.number = number
        text(canvas, LEFT, 34, "ENVIRONMENTAL ECONOMICS", "Helvetica-Bold", 8.4, GREEN)
        text(canvas, RIGHT, 34, section.upper(), "Helvetica", 8.4, MUTED, "right")
        line(canvas, LEFT, 44, RIGHT, 44)
        line(canvas, LEFT, 746, RIGHT, 746)
        text(canvas, LEFT, 763, "Vehicle mix and tailpipe emissions   /   November 2026", size=8.1, color=MUTED)
        text(canvas, RIGHT, 763, number, "Helvetica-Bold", 8.7, GREEN, "right")

    def para(self, value, *, font="Times-Roman", size=12.4, leading=17.0, gap=9, color=INK,
             indent=0, width=None):
        style = ParagraphStyle("body", fontName=font, fontSize=size, leading=leading,
                               textColor=color, alignment=TA_LEFT, splitLongWords=False)
        p = Paragraph(value, style)
        _, height = p.wrap(width or (RIGHT - LEFT - indent), 2000)
        p.drawOn(self.c, LEFT + indent, H - self.y - height)
        self.y += height + gap

    def heading(self, value):
        self.para(value, font="Times-Bold", size=28, leading=30, gap=16)

    def subhead(self, value):
        self.para(value, font="Helvetica-Bold", size=13.8, leading=17.2, gap=6, color=GREEN)

    def caption(self, value):
        self.para(value, font="Helvetica", color=MUTED, size=9, leading=12.2, gap=12)

    def figure_title(self, label, title):
        self.para(label.upper(), font="Helvetica-Bold", color=GREEN, size=8.5, leading=10, gap=4)
        self.para(title, font="Helvetica-Bold", size=13.3, leading=16.4, gap=8)

    def table(self, headings, rows, widths, *, row_height=23, header_height=26):
        """One left-aligned label column followed by right-aligned numeric columns."""
        c, top = self.c, self.y
        edges = [LEFT]
        for width in widths:
            edges.append(edges[-1] + width)
        assert abs(edges[-1] - RIGHT) < 0.1
        block(c, LEFT, top, RIGHT - LEFT, header_height, LIGHT)
        for i, label in enumerate(headings):
            x = edges[i] + 8 if i == 0 else edges[i + 1] - 8
            text(c, x, top + header_height / 2 + 3, label, "Helvetica-Bold", 9.0, INK,
                 "left" if i == 0 else "right")
        y = top + header_height
        for row in rows:
            for i, value in enumerate(row):
                x = edges[i] + 8 if i == 0 else edges[i + 1] - 8
                text(c, x, y + row_height / 2 + 3.6, value, "Helvetica", 10.0, INK,
                     "left" if i == 0 else "right")
            y += row_height
            line(c, LEFT, y, RIGHT, y, GRID)
        self.y = y + 7

    def finish(self):
        if self.y > 742:
            raise ValueError(f"Page {self.number} reaches {self.y:.1f}pt; move content above footer.")
        self.c.showPage()
