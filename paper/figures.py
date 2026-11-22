"""Publication figures drawn as PDF vectors from the generated result tables."""

from paper.layout import GREEN, GRID, INK, LEFT, MUTED, OCHRE, RIGHT, H, block, line, text


def annual_paths(page, rows):
    c, top = page.c, page.y
    x0, x1, label_x = LEFT + 36, RIGHT - 118, RIGHT - 105
    y0, y1 = top + 13, top + 153
    y = lambda value: y1 - (value - 280) / 130 * (y1 - y0)
    x = lambda year: x0 + (year - 2010) / 13 * (x1 - x0)
    for rate in (280, 310, 340, 370, 400):
        line(c, x0, y(rate), x1, y(rate), GRID)
        text(c, x0 - 7, y(rate) + 3, rate, size=8.8, color=MUTED, align="right")
    for year in (2010, 2013, 2016, 2019, 2023):
        text(c, x(year), y1 + 15, year, size=8.8, color=MUTED, align="center")
    series = (("fixed_2010_mix_g_per_mile", OCHRE, "2010 mix", [4, 3]),
              ("actual_g_per_mile", GREEN, "Actual mix", None))
    for key, color, label, dash in series:
        points = [(x(int(r["year"])), y(float(r[key]))) for r in rows]
        path = c.beginPath()
        path.moveTo(points[0][0], H - points[0][1])
        for px, py in points[1:]:
            path.lineTo(px, H - py)
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(2.2)
        c.setLineJoin(1)
        if dash:
            c.setDash(dash)
        c.drawPath(path)
        c.restoreState()
        px, py = points[-1]
        c.setFillColor(color)
        c.circle(px, H - py, 2.7, fill=1, stroke=0)
        end = float(rows[-1][key])
        text(c, label_x, py + 3, f"{label}   {end:.1f}", "Helvetica-Bold", 10.0, color)
    page.y = y1 + 27


def change_bars(page, within, mix, net):
    c, top = page.c, page.y
    x0, x1 = LEFT + 100, RIGHT - 35
    x = lambda value: x0 + (value + 120) / 160 * (x1 - x0)
    items = (("Within types", within, GREEN), ("Production mix", mix, OCHRE),
             ("Net change", net, INK))
    line(c, x(0), top + 2, x(0), top + 91, MUTED, 0.8)
    for i, (name, value, color) in enumerate(items):
        mid = top + 17 + i * 30
        text(c, LEFT, mid + 3, name, size=10.2)
        block(c, min(x(0), x(value)), mid - 6.5, abs(x(value) - x(0)), 13, color)
        text(c, x(value) + (5 if value > 0 else -5), mid + 3, f"{value:+.1f}",
             "Helvetica-Bold", 9.4, color, "left" if value > 0 else "right")
    text(c, x(0), top + 104, "0", size=8.2, color=MUTED, align="center")
    page.y = top + 113
