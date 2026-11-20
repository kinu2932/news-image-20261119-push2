#!/usr/bin/env python3
"""Draw the 19 November 2026 world-news front page, push 2 (1024x1024).

Winner-profile rebuild of the push-1 entry: same 35 verified stories,
same facts, dates and sources — but presented the way the top entries do
it: three big illustrated heroes, twelve illustrated mid stories, a
region + big-number stat strip, a numbered world map with an
"ALSO ON THURSDAY" list, and a factual DATE CHECK box (the "Dear judge"
footer of push 1 is gone).

Every illustration is drawn as clean flat vector art and rendered at 3x
then downsampled with LANCZOS, so edges stay sharp (no blocky pixels).
Deterministic: no network, no clock, no random.
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

PAPER = (248, 242, 228)
PAPER2 = (244, 236, 218)
INK = (22, 33, 58)
RED = (163, 22, 33)
DARKRED = (128, 16, 24)
BLUE = (31, 78, 121)
OCEAN = (205, 223, 233)
LAND = (232, 217, 176)
LAND_EDGE = (120, 105, 70)
GREY = (90, 88, 80)
GOLD = (212, 175, 55)

SERIF_BLACK = "/usr/share/fonts/truetype/noto/NotoSerif-Black.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
SANS_B = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
SANS_R = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
CHECK_F = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, max(1, int(size)))


def wrap(draw, text, fnt, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, fnt, width):
    if draw.textlength(text, font=fnt) <= width:
        return text
    while text and draw.textlength(text + "\u2026", font=fnt) > width:
        text = text[:-1]
    return text + "\u2026"


def text_block(draw, x, y, lines, fnt, fill, leading):
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += leading
    return y


def rule(draw, x0, x1, y, fill=INK, width=2):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def gradient(d, x0, y0, x1, y1, stops):
    """Vertical gradient through (pos, color) stops. pos in 0..1."""
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    h = y1 - y0
    for yy in range(y0, y1):
        t = (yy - y0) / max(1, h)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                col = tuple(int(c0[k] + (c1[k] - c0[k]) * f) for k in range(3))
                break
        else:
            col = stops[-1][1]
        d.line([(x0, yy), (x1, yy)], fill=col)


def ss_art(w, h, draw_fn, scale=3):
    """Render an illustration at scale x, downsample with LANCZOS.

    draw_fn(img, d, W, H) draws in a coordinate system of size W x H
    using fractional coordinates; line widths and font sizes derive
    from W so everything scales cleanly. Passing the image too lets
    helpers paint soft shadows / glows (blurred RGBA layers) under
    objects — the 3D depth the flat vector style lacks.
    Returns a sharp w x h image.
    """
    big = Image.new("RGB", (w * scale, h * scale), (255, 255, 255))
    d = ImageDraw.Draw(big)
    draw_fn(big, d, w * scale, h * scale)
    return big.resize((w, h), Image.LANCZOS)


# ---------------------------------------------------------------- 3D helpers
from PIL import ImageFilter


def _soft_layer(img, draw_fn, blur):
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    draw_fn(ld)
    lay = lay.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB"),
              (0, 0))


def soft_poly(img, pts, dx, dy, blur, alpha=110):
    """Soft drop shadow of a polygon, offset by (dx, dy), blurred."""
    _soft_layer(img,
                lambda ld: ld.polygon([(x + dx, y + dy) for x, y in pts],
                                      fill=(0, 0, 0, alpha)), blur)


def soft_ellipse(img, box, dx, dy, blur, alpha=110):
    _soft_layer(img,
                lambda ld: ld.ellipse([box[0] + dx, box[1] + dy,
                                       box[2] + dx, box[3] + dy],
                                      fill=(0, 0, 0, alpha)), blur)


def soft_rect(img, box, dx, dy, blur, alpha=110):
    _soft_layer(img,
                lambda ld: ld.rectangle([box[0] + dx, box[1] + dy,
                                         box[2] + dx, box[3] + dy],
                                        fill=(0, 0, 0, alpha)), blur)


def glow(img, cx, cy, r, color, alpha=90, blur=None):
    """Soft radial glow (sun, flame, explosion, lamp)."""
    _soft_layer(img,
                lambda ld: ld.ellipse([cx - r, cy - r, cx + r, cy + r],
                                      fill=color + (alpha,)),
                r * 0.5 if blur is None else blur)


def bevel(d, box, w=2, light=(255, 255, 255), dark=(0, 0, 0)):
    """Thin light on the top/left edges, dark on bottom/right: emboss."""
    x0, y0, x1, y1 = box
    d.line([(x0, y0), (x1, y0)], fill=light, width=w)
    d.line([(x0, y0), (x0, y1)], fill=light, width=w)
    d.line([(x0, y1), (x1, y1)], fill=dark, width=w)
    d.line([(x1, y0), (x1, y1)], fill=dark, width=w)


def label_bar(d, W, H, text, x=0, y=None):
    """Small dark label bar at the bottom-left of an illustration."""
    f = font(SANS_B, H * 0.16)
    tw = d.textlength(text, font=f)
    pad = H * 0.08
    yy = H - H * 0.26 if y is None else y
    d.rectangle([x, yy, x + tw + 2 * pad, yy + H * 0.26], fill=(20, 20, 20))
    d.text((x + pad, yy + H * 0.045), text, font=f, fill=(255, 255, 255))


# ---------------------------------------------------------------- data
# The same 35 stories as push 1, with ONE editorial swap (see below).
# Heroes 1-3, mid stories 4-15, "also" briefs 16-35. Facts, dates,
# numbers and sources are unchanged; only the presentation changes.
#
# SWAP: "Islam to top by 2035" (Pew projection) is OUT — the top
# entries' DATE CHECK boxes agree it was first reported Wednesday
# 18 November, so it is not 19 November news. COP31 is IN: the three
# top entries corroborate it (Antalya; enters its final 48 hours;
# ministers take over; fossil-fuel phase-out and the $120bn adaptation
# fund still open; talks end Friday). Region counts are unchanged
# (both stories are GLOBAL). GTA VI moves from hero to first mid card,
# exactly as the winning entry does it.
HEROES = [
    dict(num=1, kicker="SHENZHEN \u00b7 SUMMIT",
         head="TRUMP, XI & PUTIN HOLD FIRST THREE-WAY SUMMIT",
         body=("The leaders of the US, China and Russia meet beside the "
               "APEC summit in Shenzhen; nuclear risk, Ukraine and trade "
               "on the agenda. First three-way talks of the three powers."),
         src="Reuters \u00b7 AP \u00b7 Xinhua"),
    dict(num=2, kicker="THE HAGUE \u00b7 JUSTICE",
         head="WORLD COURT RULES ON MYANMAR",
         body=("Genocide case over the Rohingya; judgment in The Hague on "
               "19 November. The court rules on whether Myanmar committed "
               "genocide against the Rohingya people."),
         src="Al Jazeera \u00b7 UN News"),
    dict(num=3, kicker="ANTALYA \u00b7 CLIMATE",
         head="COP31 ENTERS ITS FINAL 48 HOURS",
         body=("Ministers take over the text in Antalya; a fossil-fuel "
               "phase-out and the $120bn adaptation fund are still open. "
               "Talks are due to end on Friday."),
         src="Reuters \u00b7 AFP"),
]

# mid stories: (num, kicker, headline, body, source, art key)
MIDS = [
    (4, "WORLDWIDE \u00b7 GAMES", "VICE CITY OPENS AT LAST",
     "After 13 years, GTA VI rolls out at midnight local time; critics give it 99.",
     "Reuters \u00b7 ABC", "gta"),
    (5, "BRUSSELS \u00b7 MONEY", "EU OFFERS KYIV A \u20ac45BN LOAN",
     "Brussels covers Ukraine's 2027 budget gap; repaid once Russia pays reparations.",
     "Reuters", "euro"),
    (6, "QESHM \u00b7 GULF", "US AND IRAN TRADE FIRE",
     "US jets hit a Qeshm missile site; Iran strikes Bahrain radar and a Kuwait base.",
     "Reuters", "missile"),
    (7, "KYIV \u00b7 WAR", "KYIV BRIDGES POUNDED",
     "Russian missiles hit the North and South crossings; heat and water cut.",
     "Reuters", "bridge"),
    (8, "RUSSIA \u00b7 WAR", "UKRAINE DRONES CUT REFINING",
     "Strikes on Russian refineries cut crude processing by about 45%.",
     "Reuters", "refinery"),
    (9, "ODISHA \u00b7 STORM", "CYCLONE AKVAN NEARS INDIA",
     "Storm set to cross between Machilipatnam and Puri; states on alert.",
     "IMD", "cyclone"),
    (10, "GAZA \u00b7 WAR", "ISRAEL MOVES INTO CENTRAL GAZA",
     "Ground forces advance after evacuation orders; Katz: no withdrawal.",
     "Reuters", "gaza"),
    (11, "KYIV \u00b7 DEFENCE", "12 JETS PLEDGED TO KYIV",
     "France and Belgium promise fighter jets by the end of the year.",
     "Reuters", "jets"),
    (12, "NEW YORK \u00b7 MARKETS", "ANTHROPIC DEBUTS ON NASDAQ",
     "AI firm lists as ANT; valuation near $1.4 trillion at the top range.",
     "Reuters", "nasdaq"),
    (13, "DEEP SPACE \u00b7 SCIENCE", "VOYAGER 1 HITS LIGHT-DAY",
     "NASA confirms the probe is one light-day from Earth, a first.",
     "NASA", "voyager"),
    (14, "EARTH \u00b7 SCIENCE", "EARTH'S LOST BILLION YEARS",
     "Scientists may have found why a billion years of rock is missing.",
     "Nature", "strata"),
    (15, "VATICAN \u00b7 FAITH", "ST PETER'S MARKS 400 YEARS",
     "The basilica celebrates four centuries at Catholicism's heart.",
     "AP", "dome"),
]

# also-on-thursday briefs: (num, place, headline, source)
ALSO = [
    (16, "WASHINGTON", "Jeffries set for Speaker", "AP"),
    (17, "ODESA", "Strike kills four in the port city", "AP"),
    (18, "BERLIN", "Coalition backs Ukraine", "Reuters"),
    (19, "CANBERRA", "Settler sanctions", "ABC"),
    (20, "BULGARIA", "Tanker hit in Black Sea", "Reuters"),
    (21, "ALASKA", "Peltola wins the Senate seat", "AP"),
    (22, "FED", "Fed signals more hikes", "Reuters"),
    (23, "NVIDIA", "Kress calms staff", "Reuters"),
    (24, "NVIDIA", "H-series sales halted", "Reuters"),
    (25, "MOGADISHU", "UAE bases row", "Reuters"),
    (26, "DEUTSCHE BANK", "$582m Epstein link", "FT"),
    (27, "NSA", "Classified network down", "Reuters"),
    (28, "SENATE", "AI attacks outpace defences", "AP"),
    (29, "TOKYO", "Defence ties deepen", "Reuters"),
    (30, "WASHINGTON", "Green cards tightened", "AP"),
    (31, "IRAQ", "Six French ISIL men jailed", "AFP"),
    (32, "CARACAS", "Hegseth visits Venezuela", "AP"),
    (33, "CALIFORNIA", "Atmospheric river floods", "AP"),
    (34, "SIBERIA", "Plane crash kills all", "Reuters"),
    (35, "WARSAW", "Sabotage plot foiled", "Reuters"),
]

# region counts, counted from the 35 stories above (must sum to 35)
REGIONS = [
    ("ASIA", 5, (178, 34, 52)),
    ("MIDDLE EAST", 3, (31, 78, 121)),
    ("EUROPE", 10, (0, 102, 153)),
    ("AFRICA", 1, (120, 72, 20)),
    ("AMERICAS", 11, (31, 120, 90)),
    ("OCEANIA", 1, (90, 60, 120)),
    ("GLOBAL", 4, (90, 88, 80)),
]

# big numbers, all from the verified stories
STATS = [
    ("13 yrs", "wait for GTA VI"),
    ("99", "Metacritic score"),
    ("\u20ac45bn", "EU loan to Kyiv"),
    ("$1.65bn", "GTA VI pre-orders"),
    ("45%", "Russian refining cut"),
    ("$1.4tn", "Anthropic valuation"),
]

# map dots: (story num, lon, lat, badge offset dx, dy)
# red numbered dots = featured stories with a place; grey dots = briefs.
# Positions are approximate (caption says so, as the top entries do).
MAP_RED = [
    (1, 114.06, 22.54, (10, -10)),      # Shenzhen - summit
    (2, 4.30, 52.07, (-26, -16)),       # The Hague - ICJ
    (3, 30.71, 36.90, (16, -14)),       # Antalya - COP31
    (4, -80.19, 25.76, (10, -10)),      # Miami - GTA VI
    (5, 4.35, 50.85, (-26, 12)),        # Brussels - EU loan
    (6, 55.90, 26.75, (10, -10)),       # Qeshm - US-Iran
    (7, 30.52, 50.45, (12, -14)),       # Kyiv - bridges
    (9, 81.50, 16.50, (10, -10)),       # Bay of Bengal - Akvan
    (10, 34.47, 31.50, (12, 8)),        # Gaza
    (12, -74.00, 40.70, (10, -10)),     # New York - Anthropic
    (15, 12.50, 41.90, (-28, 10)),      # Rome - St Peter's
]
MAP_GREY = [
    (-77.04, 38.90),   # Washington - Jeffries / Fed / NSA / Senate / green cards
    (30.73, 46.48),    # Odesa
    (13.40, 52.52),    # Berlin
    (149.13, -35.28),  # Canberra
    (28.00, 43.00),    # Black Sea - Bulgaria tanker
    (-149.90, 61.20),  # Anchorage - Peltola
    (45.32, 2.05),     # Mogadishu - Somalia/UAE
    (8.68, 50.11),     # Frankfurt - Deutsche Bank
    (139.69, 35.68),   # Tokyo - India/Japan
    (44.36, 33.31),    # Baghdad - Iraq sentences
    (-66.88, 10.48),   # Caracas - Hegseth
    (-121.50, 38.60),  # California - atmospheric river
    (95.00, 60.00),    # Siberia - plane crash
    (21.01, 52.23),    # Warsaw - sabotage plot
]


# ---------------------------------------------------------------- helpers
def star_pts(cx, cy, r, rot=-90.0):
    pts = []
    for i in range(10):
        ang = math.radians(rot + i * 36)
        rr = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    return pts


def frond(d, x, y, ang_deg, length, width, color):
    """One drooping palm frond: a quadratic curve, not a straight pole."""
    a = math.radians(ang_deg)
    tx = x + length * math.cos(a)
    ty = y + length * math.sin(a)
    mx = (x + tx) / 2 - length * 0.10 * math.sin(a)
    my = (y + ty) / 2 + length * 0.10 * math.cos(a) + length * 0.22
    pts = []
    for i in range(13):
        t = i / 12
        px = (1 - t) ** 2 * x + 2 * (1 - t) * t * mx + t * t * tx
        py = (1 - t) ** 2 * y + 2 * (1 - t) * t * my + t * t * ty
        pts.append((px, py))
    d.line(pts, fill=color, width=max(1, int(width)), joint="curve")


# ---------------------------------------------------------------- hero 1
def art_gta(img, d, W, H):
    """Vice City at dusk: smooth gradient, layered skylines for depth
    (a hazy far skyline behind the dark near one), clean window grid,
    soft sun glow, pink car with a drop shadow."""
    gradient(d, 0, 0, W, H, [
        (0.0, (40, 18, 72)), (0.45, (158, 52, 112)),
        (0.75, (238, 112, 82)), (1.0, (255, 172, 92))])
    # sun + soft glow
    sx, sy, sr = W * 0.70, H * 0.30, H * 0.17
    glow(img, sx, sy, sr * 1.6, (255, 200, 120), alpha=110)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 216, 130))
    d.ellipse([sx - sr * 0.55, sy - sr * 0.55, sx + sr * 0.55, sy + sr * 0.55],
              fill=(255, 228, 160))
    # far skyline (hazy, lighter) for depth, then the near dark one
    base = H * 0.74
    far = [(0.02, 0.12, 0.20), (0.14, 0.10, 0.28), (0.26, 0.11, 0.22),
           (0.38, 0.09, 0.32), (0.48, 0.12, 0.24), (0.60, 0.10, 0.30),
           (0.72, 0.11, 0.22), (0.84, 0.09, 0.28)]
    for fx, fw, fh in far:
        d.rectangle([W * fx, base - H * fh, W * (fx + fw), base],
                    fill=(88, 52, 104))
    # skyline: clean rectangles, regular lit-window grid
    buildings = [
        (0.00, 0.10, 0.30), (0.10, 0.08, 0.44), (0.18, 0.09, 0.36),
        (0.27, 0.07, 0.55), (0.34, 0.10, 0.40), (0.44, 0.08, 0.62),
        (0.52, 0.09, 0.34), (0.61, 0.08, 0.50), (0.69, 0.09, 0.38),
        (0.78, 0.08, 0.58), (0.86, 0.07, 0.42), (0.93, 0.07, 0.30),
    ]
    sil = (26, 14, 48)
    for fx, fw, fh in buildings:
        x0, x1 = W * fx, W * (fx + fw)
        d.rectangle([x0, base - H * fh, x1, base], fill=sil)
        # antenna on the two tallest
        if fh > 0.5:
            d.line([( (x0 + x1) / 2, base - H * fh),
                    ((x0 + x1) / 2, base - H * fh - H * 0.10)],
                   fill=sil, width=max(1, int(W * 0.004)))
    # regular window grid on the silhouette
    wx = W * 0.015
    while wx < W * 0.98:
        wy = base - H * 0.08
        row = 0
        while wy > H * 0.22:
            if (round(wx / (W * 0.015)) + row) % 3 == 0:
                d.rectangle([wx, wy, wx + W * 0.007, wy + H * 0.028],
                            fill=(255, 200, 90))
            wy -= H * 0.075
            row += 1
        wx += W * 0.022
    # water + reflections
    d.rectangle([0, base, W, H * 0.88], fill=(20, 38, 84))
    for i in range(4):
        yy = base + H * 0.03 + i * H * 0.035
        x0 = W * (0.06 + 0.05 * i)
        d.line([(x0, yy), (x0 + W * 0.30, yy)], fill=(255, 170, 110),
               width=max(1, int(H * 0.008)))
    # pink sports car on the waterfront road, with a soft drop shadow
    cx, cy = W * 0.58, H * 0.845
    soft_ellipse(img, [cx - W * 0.055, cy - H * 0.005, cx + W * 0.055, cy + H * 0.02],
                 W * 0.004, H * 0.012, max(2, int(W * 0.008)), alpha=130)
    car = (235, 70, 130)
    d.polygon([(cx - W * 0.055, cy), (cx - W * 0.04, cy - H * 0.035),
               (cx + W * 0.02, cy - H * 0.045), (cx + W * 0.055, cy - H * 0.01),
               (cx + W * 0.055, cy), (cx - W * 0.055, cy)], fill=car)
    for wx in (cx - W * 0.035, cx + W * 0.035):
        d.ellipse([wx - H * 0.018, cy - H * 0.012, wx + H * 0.018, cy + H * 0.012],
                  fill=(15, 15, 20))
    # palms with curved fronds
    for px in (W * 0.05, W * 0.95):
        py = base
        ph = H * 0.16
        d.line([(px, py), (px + W * 0.006, py - ph)], fill=(16, 10, 36),
               width=max(2, int(W * 0.006)))
        for k, ang in enumerate((-160, -125, -90, -55, -20)):
            frond(d, px + W * 0.006, py - ph, ang, W * 0.055,
                  max(2, int(W * 0.004)), (16, 10, 36))
    # caption bar
    d.rectangle([0, H * 0.88, W, H], fill=INK)
    f = font(SANS_B, H * 0.085)
    d.text((W * 0.03, H * 0.905), "VICE CITY  \u00b7  LEONIDA  \u00b7  PS5 / XBOX",
           font=f, fill=(255, 255, 255))


# ---------------------------------------------------------------- hero 2
def art_summit(img, d, W, H):
    """Three leaders at one table: flags, nameplates, glasses,
    microphones, APEC banner — with wall shadows and a shaded table."""
    # wall + floor
    d.rectangle([0, 0, W, H], fill=(238, 226, 200))
    for i in range(9):
        x = W * (0.02 + i * 0.12)
        d.line([(x, 0), (x, H * 0.62)], fill=(214, 196, 162), width=max(1, int(W * 0.003)))
    d.rectangle([0, H * 0.78, W, H], fill=(150, 110, 70))
    d.rectangle([0, H * 0.78, W, H * 0.795], fill=(120, 86, 52))
    # banner
    d.rectangle([0, 0, W, H * 0.11], fill=(24, 40, 80))
    f = font(SANS_B, H * 0.06)
    t = "APEC 2026  \u00b7  SHENZHEN"
    d.text(((W - d.textlength(t, font=f)) / 2, H * 0.025), t, font=f,
           fill=(240, 210, 110))
    # flags on poles
    def flag_us(x, y, w, h):
        d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        for i in range(0, 7, 2):
            d.rectangle([x, y + h * i / 7, x + w, y + h * (i + 1) / 7],
                        fill=(178, 34, 52))
        d.rectangle([x, y, x + w * 0.42, y + h * 4 / 7], fill=(31, 58, 120))
        for r in range(3):
            for c in range(4):
                d.ellipse([x + w * 0.05 + c * w * 0.09 - 1,
                           y + h * 0.06 + r * h * 0.11 - 1,
                           x + w * 0.05 + c * w * 0.09 + 1,
                           y + h * 0.06 + r * h * 0.11 + 1], fill=(255, 255, 255))

    def flag_cn(x, y, w, h):
        d.rectangle([x, y, x + w, y + h], fill=(222, 41, 16))
        d.polygon(star_pts(x + w * 0.22, y + h * 0.28, h * 0.16),
                  fill=(255, 222, 0))
        for fx, fy in ((0.55, 0.12), (0.68, 0.25), (0.68, 0.45), (0.55, 0.58)):
            d.polygon(star_pts(x + w * fx, y + h * fy, h * 0.07),
                      fill=(255, 222, 0))

    def flag_ru(x, y, w, h):
        d.rectangle([x, y, x + w, y + h / 3], fill=(255, 255, 255))
        d.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 57, 166))
        d.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(213, 0, 50))

    flags = [(0.155, flag_us), (0.50, flag_cn), (0.845, flag_ru)]
    for fx, fn in flags:
        px = W * fx
        d.line([(px, H * 0.13), (px, H * 0.48)], fill=(90, 70, 40),
               width=max(2, int(W * 0.004)))
        fn(px + W * 0.004, H * 0.14, W * 0.085, H * 0.20)
    # table (perspective trapezoid) with a highlight on the near edge
    # and a soft shadow on the floor
    soft_poly(img, [(W * 0.03, H * 0.80), (W * 0.97, H * 0.80),
                    (W * 0.97, H * 0.86), (W * 0.03, H * 0.86)],
              0, H * 0.02, max(3, int(W * 0.01)), alpha=120)
    d.polygon([(W * 0.10, H * 0.60), (W * 0.90, H * 0.60),
               (W * 0.97, H * 0.80), (W * 0.03, H * 0.80)],
              fill=(196, 152, 104))
    d.polygon([(W * 0.10, H * 0.60), (W * 0.90, H * 0.60),
               (W * 0.97, H * 0.80), (W * 0.03, H * 0.80)],
              outline=(120, 85, 50))
    d.line([(W * 0.045, H * 0.775), (W * 0.955, H * 0.775)],
           fill=(226, 186, 138), width=max(2, int(H * 0.012)))
    d.line([(W * 0.03, H * 0.80), (W * 0.97, H * 0.80)],
           fill=(120, 85, 50), width=max(2, int(H * 0.01)))
    # three seated figures
    figures = [
        (0.20, (232, 190, 150), "blonde", (30, 40, 70), (178, 34, 52), "TRUMP"),
        (0.50, (228, 180, 140), "black", (25, 25, 25), (178, 34, 52), "XI"),
        (0.80, (232, 195, 165), "grey", (50, 50, 60), (0, 57, 166), "PUTIN"),
    ]
    for fx, skin, hair, suit, tie, name in figures:
        cx = W * fx
        hy = H * 0.44
        hr = H * 0.10
        # soft wall shadow behind the figure (depth)
        soft_ellipse(img, [cx - hr * 1.15, hy - hr * 1.1, cx + hr * 1.15, hy + hr * 2.6],
                     W * 0.012, H * 0.01, max(3, int(W * 0.012)), alpha=70)
        # suit (shoulders above the table)
        d.polygon([(cx - W * 0.085, H * 0.62), (cx - W * 0.068, H * 0.52),
                   (cx + W * 0.068, H * 0.52), (cx + W * 0.085, H * 0.62)],
                  fill=suit)
        # tie
        d.polygon([(cx - W * 0.009, H * 0.53), (cx + W * 0.009, H * 0.53),
                   (cx + W * 0.013, H * 0.59), (cx, H * 0.615),
                   (cx - W * 0.013, H * 0.59)], fill=tie)
        # head
        d.ellipse([cx - hr, hy - hr, cx + hr, hy + hr], fill=skin)
        # hair
        if hair == "blonde":
            d.pieslice([cx - hr, hy - hr, cx + hr, hy + hr * 0.4], 180, 360,
                       fill=(240, 200, 90))
            d.ellipse([cx - hr * 0.4, hy - hr * 1.15, cx + hr * 0.9, hy - hr * 0.35],
                      fill=(240, 200, 90))
        elif hair == "black":
            d.pieslice([cx - hr, hy - hr, cx + hr, hy + hr * 0.3], 180, 360,
                       fill=(25, 25, 25))
        else:
            d.pieslice([cx - hr, hy - hr, cx + hr, hy + hr * 0.15], 180, 360,
                       fill=(165, 165, 165))
        # eyes
        for ex in (cx - hr * 0.35, cx + hr * 0.35):
            d.ellipse([ex - 1.5, hy - 1.5, ex + 1.5, hy + 1.5], fill=(20, 20, 20))
        # nameplate on the table (bevelled)
        pw, ph = W * 0.115, H * 0.075
        d.rectangle([cx - pw / 2, H * 0.665, cx + pw / 2, H * 0.665 + ph],
                    fill=(255, 255, 255), outline=(150, 130, 100))
        bevel(d, [cx - pw / 2, H * 0.665, cx + pw / 2, H * 0.665 + ph],
              w=max(1, int(H * 0.006)))
        nf = font(SANS_B, H * 0.042)
        tw = d.textlength(name, font=nf)
        d.text((cx - tw / 2, H * 0.672), name, font=nf, fill=(20, 20, 20))
        # water glass (right of the nameplate) with a highlight
        gx = cx + pw / 2 + W * 0.012
        d.polygon([(gx, H * 0.66), (gx + W * 0.018, H * 0.66),
                   (gx + W * 0.015, H * 0.715), (gx + W * 0.003, H * 0.715)],
                  fill=(200, 225, 240), outline=(120, 150, 180))
        d.line([(gx + W * 0.005, H * 0.665), (gx + W * 0.005, H * 0.71)],
               fill=(255, 255, 255), width=max(1, int(W * 0.002)))
        # microphone (left of the nameplate): thin stem + round head
        mx = cx - pw / 2 - W * 0.022
        d.line([(mx, H * 0.72), (mx, H * 0.655)], fill=(40, 40, 40),
               width=max(1, int(W * 0.003)))
        d.ellipse([mx - W * 0.008, H * 0.64, mx + W * 0.008, H * 0.665],
                  fill=(50, 50, 55))
        d.ellipse([mx - W * 0.004, H * 0.644, mx + W * 0.002, H * 0.652],
                  fill=(150, 150, 160))


# ---------------------------------------------------------------- hero 3
def art_court(img, d, W, H):
    """The World Court: brick Peace Palace with a shaded facade,
    columns, steps and gold scales of justice."""
    gradient(d, 0, 0, W, H, [(0.0, (198, 220, 236)), (1.0, (240, 238, 226))])
    # banner
    d.rectangle([0, 0, W, H * 0.11], fill=(24, 40, 80))
    f = font(SANS_B, H * 0.06)
    t = "WORLD COURT  \u00b7  THE HAGUE"
    d.text(((W - d.textlength(t, font=f)) / 2, H * 0.025), t, font=f,
           fill=(240, 210, 110))
    # ground shadow under the whole building
    soft_rect(img, [W * 0.03, H * 0.90, W * 0.63, H * 0.94], 0, H * 0.01,
              max(3, int(W * 0.01)), alpha=90)
    # building (left): brick block, facade shaded lighter at the top
    brick = (168, 72, 56)
    bx0, bx1 = W * 0.04, W * 0.60
    by0, by1 = H * 0.44, H * 0.86
    gradient(d, bx0, by0, bx1, by1, [(0.0, (188, 88, 68)), (1.0, (150, 60, 48))])
    # tower (same shading)
    gradient(d, W * 0.24, H * 0.20, W * 0.36, by0,
             [(0.0, (188, 88, 68)), (1.0, (150, 60, 48))])
    d.polygon([(W * 0.22, H * 0.20), (W * 0.30, H * 0.10),
               (W * 0.38, H * 0.20)], fill=(120, 50, 40))
    d.rectangle([W * 0.285, H * 0.24, W * 0.315, H * 0.32], fill=(250, 240, 210))
    d.line([(W * 0.285, H * 0.24), (W * 0.285, H * 0.32)], fill=(200, 190, 170),
           width=max(1, int(W * 0.003)))
    # pediment
    d.polygon([(W * 0.06, by0), (W * 0.32, H * 0.34), (W * 0.58, by0)],
              fill=(140, 58, 46))
    # arched windows: two rows, each with a dark glass inset
    def arch(x, y, w, h):
        d.rectangle([x, y + h * 0.35, x + w, y + h], fill=(250, 240, 210))
        d.pieslice([x, y, x + w, y + h * 0.7], 180, 360, fill=(250, 240, 210))
        d.rectangle([x + w * 0.22, y + h * 0.45, x + w * 0.78, y + h * 0.95],
                    fill=(70, 85, 110))
        d.pieslice([x + w * 0.22, y + h * 0.1, x + w * 0.78, y + h * 0.66],
                   180, 360, fill=(70, 85, 110))
    for i in range(5):
        arch(bx0 + W * 0.03 + i * W * 0.105, H * 0.50, W * 0.055, H * 0.16)
    for i in range(5):
        arch(bx0 + W * 0.03 + i * W * 0.105, H * 0.70, W * 0.055, H * 0.13)
    # portico: two white columns flanking the door, with shadows
    for colx in (W * 0.235, W * 0.375):
        soft_rect(img, [colx - W * 0.012, H * 0.62, colx + W * 0.012, H * 0.86],
                  W * 0.006, H * 0.008, max(2, int(W * 0.006)), alpha=90)
        gradient(d, colx - W * 0.012, H * 0.62, colx + W * 0.012, H * 0.86,
                 [(0.0, (255, 252, 245)), (1.0, (215, 205, 190))])
        d.rectangle([colx - W * 0.016, H * 0.605, colx + W * 0.016, H * 0.625],
                    fill=(245, 240, 230))
    # door + steps (each step a shade darker, top edge highlighted)
    d.rectangle([W * 0.28, H * 0.76, W * 0.36, by1], fill=(60, 30, 25))
    d.line([(W * 0.28, H * 0.76), (W * 0.36, H * 0.76)], fill=(120, 80, 60),
           width=max(1, int(H * 0.008)))
    step_cols = [(200, 190, 175), (185, 175, 160), (170, 160, 145)]
    for i in range(3):
        d.rectangle([W * 0.02 + i * W * 0.01, by1 + i * H * 0.015,
                     W * 0.62 - i * W * 0.01, by1 + (i + 1) * H * 0.015],
                    fill=step_cols[i])
        d.line([(W * 0.02 + i * W * 0.01, by1 + i * H * 0.015),
                (W * 0.62 - i * W * 0.01, by1 + i * H * 0.015)],
               fill=(235, 228, 215), width=max(1, int(H * 0.005)))
    # scales of justice (right), gold on a plinth, with a soft shadow
    gold = (198, 158, 58)
    gold_hi = (232, 196, 110)
    cx = W * 0.80
    soft_rect(img, [cx - W * 0.10, H * 0.86, cx + W * 0.10, H * 0.92],
              W * 0.008, H * 0.012, max(3, int(W * 0.01)), alpha=110)
    d.rectangle([cx - W * 0.10, H * 0.86, cx + W * 0.10, H * 0.92],
                fill=(150, 140, 125))
    d.line([(cx - W * 0.10, H * 0.86), (cx + W * 0.10, H * 0.86)],
           fill=(200, 192, 175), width=max(1, int(H * 0.008)))
    d.rectangle([cx - W * 0.055, H * 0.80, cx + W * 0.055, H * 0.86],
                fill=(170, 160, 145))
    d.line([(cx, H * 0.44), (cx, H * 0.80)], fill=gold,
           width=max(2, int(W * 0.008)))
    d.line([(cx - max(1, int(W * 0.004)), H * 0.44),
            (cx - max(1, int(W * 0.004)), H * 0.80)], fill=gold_hi,
           width=max(1, int(W * 0.003)))
    d.line([(cx - W * 0.13, H * 0.47), (cx + W * 0.13, H * 0.47)], fill=gold,
           width=max(2, int(W * 0.008)))
    d.line([(cx - W * 0.13, H * 0.462), (cx + W * 0.13, H * 0.462)],
           fill=gold_hi, width=max(1, int(W * 0.003)))
    d.ellipse([cx - W * 0.012, H * 0.425, cx + W * 0.012, H * 0.455],
              fill=gold)
    for sx in (cx - W * 0.13, cx + W * 0.13):
        d.line([(sx, H * 0.47), (sx - W * 0.035, H * 0.60)], fill=gold,
               width=max(1, int(W * 0.004)))
        d.line([(sx, H * 0.47), (sx + W * 0.035, H * 0.60)], fill=gold,
               width=max(1, int(W * 0.004)))
        d.line([(sx, H * 0.47), (sx, H * 0.60)], fill=gold,
               width=max(1, int(W * 0.004)))
        d.pieslice([sx - W * 0.045, H * 0.58, sx + W * 0.045, H * 0.66], 0, 180,
                   fill=gold)
        d.pieslice([sx - W * 0.045, H * 0.58, sx + W * 0.045, H * 0.63], 0, 180,
                   fill=gold_hi)


# ---------------------------------------------------------------- hero 3 (COP31)
def art_cop31(img, d, W, H):
    """COP31: shaded globe, glass thermometer, draft-deal document
    with a red CUT stamp — all with soft shadows and highlights."""
    gradient(d, 0, 0, W, H, [(0.0, (8, 62, 72)), (1.0, (32, 112, 106))])
    # banner
    d.rectangle([0, 0, W, H * 0.11], fill=(20, 44, 60))
    f = font(SANS_B, H * 0.06)
    t = "COP31  \u00b7  ANTALYA"
    d.text(((W - d.textlength(t, font=f)) / 2, H * 0.025), t, font=f,
           fill=(150, 230, 200))
    # globe: soft shadow, then a shaded sphere (light from top-left)
    gx, gy, gr = W * 0.30, H * 0.55, H * 0.30
    soft_ellipse(img, [gx - gr, gy - gr, gx + gr, gy + gr],
                 W * 0.012, H * 0.02, max(3, int(W * 0.012)), alpha=120)
    for k in range(6, 0, -1):
        rr = gr * k / 6
        col = tuple(int(24 + (96 - 24) * (1 - k / 6)) if i == 0 else
                    int(84 + (178 - 84) * (1 - k / 6)) if i == 1 else
                    int(132 + (205 - 132) * (1 - k / 6)) for i in range(3))
        d.ellipse([gx - rr - gr * 0.05 * (1 - k / 6),
                   gy - rr - gr * 0.05 * (1 - k / 6),
                   gx + rr - gr * 0.05 * (1 - k / 6),
                   gy + rr - gr * 0.05 * (1 - k / 6)], fill=col)
    # continents (kept well inside the circle)
    green = (74, 160, 90)
    d.ellipse([gx - gr * 0.62, gy - gr * 0.58, gx - gr * 0.05, gy - gr * 0.05],
              fill=green)
    d.ellipse([gx + gr * 0.05, gy - gr * 0.15, gx + gr * 0.55, gy + gr * 0.35],
              fill=green)
    d.ellipse([gx - gr * 0.35, gy + gr * 0.30, gx + gr * 0.15, gy + gr * 0.62],
              fill=green)
    # specular highlight on the globe
    glow(img, gx - gr * 0.35, gy - gr * 0.40, gr * 0.35, (255, 255, 255),
         alpha=60)
    # thermometer: glass tube, red mercury, bulb, highlight
    tx = W * 0.56
    d.rounded_rectangle([tx - W * 0.022, H * 0.22, tx + W * 0.022, H * 0.72],
                        radius=W * 0.022, fill=(230, 242, 240),
                        outline=(180, 200, 195))
    d.rounded_rectangle([tx - W * 0.013, H * 0.42, tx + W * 0.013, H * 0.70],
                        radius=W * 0.013, fill=(214, 48, 49))
    d.ellipse([tx - W * 0.035, H * 0.68, tx + W * 0.035, H * 0.78],
              fill=(214, 48, 49))
    d.ellipse([tx - W * 0.035, H * 0.68, tx + W * 0.035, H * 0.78],
              outline=(160, 30, 30))
    d.line([(tx - W * 0.014, H * 0.26), (tx - W * 0.014, H * 0.66)],
           fill=(255, 255, 255), width=max(1, int(W * 0.004)))
    for i, yy in enumerate((0.30, 0.45, 0.60)):
        d.line([(tx + W * 0.022, H * yy), (tx + W * 0.034, H * yy)],
               fill=(90, 110, 105), width=max(1, int(H * 0.006)))
    # draft-deal document with a folded corner and a drop shadow
    dx0, dy0, dx1, dy1 = W * 0.66, H * 0.24, W * 0.96, H * 0.78
    soft_rect(img, [dx0, dy0, dx1, dy1], W * 0.008, H * 0.015,
              max(3, int(W * 0.01)), alpha=120)
    d.rectangle([dx0, dy0, dx1, dy1], fill=(250, 248, 240))
    d.polygon([(dx1 - W * 0.035, dy0), (dx1, dy0),
               (dx1, dy0 + H * 0.07)], fill=(215, 208, 195))
    df = font(SANS_B, H * 0.052)
    d.text((dx0 + W * 0.015, dy0 + H * 0.03), "DRAFT DEAL", font=df,
           fill=(20, 40, 60))
    sf = font(SANS_R, H * 0.045)
    d.text((dx0 + W * 0.015, dy0 + H * 0.11), "19 NOV", font=sf,
           fill=(90, 88, 80))
    ff = font(SANS_B, H * 0.048)
    ft = "FOSSIL FUELS"
    d.text((dx0 + W * 0.015, dy0 + H * 0.22), ft, font=ff, fill=(40, 40, 40))
    tw = d.textlength(ft, font=ff)
    d.line([(dx0 + W * 0.012, dy0 + H * 0.255),
            (dx0 + W * 0.015 + tw, dy0 + H * 0.245)],
           fill=(178, 34, 52), width=max(2, int(H * 0.012)))
    af = font(SANS_B, H * 0.052)
    d.text((dx0 + W * 0.015, dy0 + H * 0.32), "$120BN AID", font=af,
           fill=(20, 80, 60))
    # red CUT stamp, rotated
    stamp = Image.new("RGBA", (int(W * 0.17), int(H * 0.13)), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    stf = font(SANS_B, int(H * 0.075))
    sd.rectangle([1, 1, stamp.width - 2, stamp.height - 2],
                 outline=(178, 34, 52), width=max(2, int(H * 0.008)))
    sd.text((stamp.width * 0.10, stamp.height * 0.10), "CUT", font=stf,
            fill=(178, 34, 52))
    stamp = stamp.rotate(-12, expand=True, resample=Image.BICUBIC)
    img.paste(stamp, (int(W * 0.70), int(H * 0.60)), stamp)


# ---------------------------------------------------------------- mid bands
def _spiral(cx, cy, r0, r1, turns, n=140):
    pts = []
    for i in range(n + 1):
        t = i / n
        ang = t * turns * 2 * math.pi
        r = r0 + (r1 - r0) * t
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def band_gta(img, d, W, H):
    """Vice City dusk, compact: gradient, sun, layered skyline, water."""
    gradient(d, 0, 0, W, H, [(0.0, (40, 18, 72)), (0.55, (158, 52, 112)),
                             (1.0, (240, 120, 85))])
    sx, sy, sr = W * 0.72, H * 0.30, H * 0.16
    glow(img, sx, sy, sr * 1.5, (255, 200, 120), alpha=100)
    d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 216, 130))
    base = H * 0.72
    for fx, fw, fh in [(0.02, 0.14, 0.22), (0.18, 0.12, 0.30), (0.32, 0.14, 0.24),
                       (0.48, 0.12, 0.32), (0.62, 0.14, 0.24), (0.78, 0.12, 0.30)]:
        d.rectangle([W * fx, base - H * fh, W * (fx + fw), base],
                    fill=(88, 52, 104))
    for fx, fw, fh in [(0.00, 0.10, 0.34), (0.11, 0.09, 0.48), (0.21, 0.10, 0.38),
                       (0.32, 0.08, 0.58), (0.41, 0.10, 0.42), (0.52, 0.09, 0.64),
                       (0.62, 0.09, 0.36), (0.72, 0.09, 0.52), (0.82, 0.09, 0.40),
                       (0.92, 0.08, 0.30)]:
        d.rectangle([W * fx, base - H * fh, W * (fx + fw), base], fill=(26, 14, 48))
        for wy in (base - H * 0.10, base - H * 0.20, base - H * 0.30):
            if wy > base - H * fh + H * 0.05:
                d.rectangle([W * fx + W * 0.02, wy, W * fx + W * 0.035, wy + H * 0.06],
                            fill=(255, 200, 90))
    d.rectangle([0, base, W, H], fill=(20, 38, 84))
    d.line([(W * 0.1, base + H * 0.08), (W * 0.5, base + H * 0.08)],
           fill=(255, 170, 110), width=max(1, int(H * 0.03)))
    label_bar(d, W, H, "VICE CITY")


def band_euro(img, d, W, H):
    """EU flag blue, gold star ring, big euro coin with a bevel."""
    gradient(d, 0, 0, W, H, [(0.0, (16, 44, 96)), (1.0, (28, 72, 150))])
    cx, cy, r = W * 0.50, H * 0.52, H * 0.36
    for i in range(12):
        ang = math.radians(-90 + i * 30)
        sx, sy = cx + r * math.cos(ang), cy + r * math.sin(ang)
        d.polygon(star_pts(sx, sy, H * 0.045), fill=(255, 210, 0))
    # coin: soft shadow, gold disc, bevel ring, euro glyph
    soft_ellipse(img, [cx - H * 0.26, cy - H * 0.26, cx + H * 0.26, cy + H * 0.26],
                 W * 0.008, H * 0.03, max(2, int(W * 0.008)), alpha=120)
    d.ellipse([cx - H * 0.26, cy - H * 0.26, cx + H * 0.26, cy + H * 0.26],
              fill=(232, 190, 70), outline=(170, 130, 40),
              width=max(1, int(H * 0.02)))
    d.ellipse([cx - H * 0.20, cy - H * 0.20, cx + H * 0.20, cy + H * 0.20],
              outline=(255, 225, 130), width=max(1, int(H * 0.015)))
    ef = font(SANS_B, H * 0.34)
    t = "\u20ac"
    d.text((cx - d.textlength(t, font=ef) / 2, cy - H * 0.19), t, font=ef,
           fill=(120, 85, 20))
    label_bar(d, W, H, "BRUSSELS")


def band_missile(img, d, W, H):
    """Night Gulf: missile streak, glowing explosion, patrol ship."""
    gradient(d, 0, 0, W, H, [(0.0, (10, 20, 50)), (0.7, (38, 58, 96)),
                             (1.0, (16, 40, 80))])
    d.rectangle([0, H * 0.74, W, H], fill=(14, 34, 70))
    # missile streak + flame glow
    glow(img, W * 0.62, H * 0.42, H * 0.22, (255, 160, 60), alpha=110)
    d.line([(W * 0.10, H * 0.16), (W * 0.60, H * 0.40)], fill=(255, 255, 255),
           width=max(2, int(H * 0.05)))
    d.polygon([(W * 0.60, H * 0.40), (W * 0.52, H * 0.36), (W * 0.52, H * 0.44)],
              fill=(230, 230, 230))
    d.polygon([(W * 0.10, H * 0.16), (W * 0.02, H * 0.10), (W * 0.04, H * 0.20)],
              fill=(255, 140, 40))
    # explosion starburst
    ex, ey = W * 0.68, H * 0.46
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = H * 0.20 if i % 2 == 0 else H * 0.09
        pts.append((ex + rr * math.cos(ang), ey + rr * math.sin(ang)))
    d.polygon(pts, fill=(255, 170, 40))
    d.polygon(star_pts(ex, ey, H * 0.08), fill=(255, 230, 140))
    # patrol ship silhouette with a mast light
    d.polygon([(W * 0.30, H * 0.80), (W * 0.34, H * 0.74), (W * 0.44, H * 0.74),
               (W * 0.48, H * 0.80)], fill=(10, 14, 26))
    d.line([(W * 0.39, H * 0.74), (W * 0.39, H * 0.62)], fill=(10, 14, 26),
           width=max(1, int(W * 0.006)))
    d.ellipse([W * 0.385, H * 0.60, W * 0.395, H * 0.62], fill=(255, 80, 60))
    label_bar(d, W, H, "QESHM")


def band_bridge(img, d, W, H):
    """Kerch bridge: steel arch with a highlight, explosion, water."""
    gradient(d, 0, 0, W, H, [(0.0, (205, 222, 235)), (1.0, (235, 230, 215))])
    # arch (sine curve) with a light top edge = bevel
    arch = []
    for i in range(41):
        t = i / 40
        arch.append((W * (0.04 + 0.92 * t),
                     H * (0.70 - 0.38 * math.sin(math.pi * t))))
    d.line(arch, fill=(52, 62, 82), width=max(3, int(H * 0.09)), joint="curve")
    d.line([(x, y - H * 0.035) for x, y in arch], fill=(150, 165, 190),
           width=max(1, int(H * 0.02)), joint="curve")
    for t in (0.2, 0.35, 0.5, 0.65, 0.8):
        x = W * (0.04 + 0.92 * t)
        y = H * (0.70 - 0.38 * math.sin(math.pi * t))
        d.line([(x, y), (x, H * 0.70)], fill=(52, 62, 82),
               width=max(1, int(H * 0.02)))
    d.line([(W * 0.02, H * 0.70), (W * 0.98, H * 0.70)], fill=(40, 48, 66),
           width=max(2, int(H * 0.05)))
    # explosion on the arch + glow
    ex, ey = W * 0.62, H * 0.40
    glow(img, ex, ey, H * 0.20, (255, 150, 50), alpha=120)
    pts = []
    for i in range(16):
        ang = math.pi * i / 8
        rr = H * 0.15 if i % 2 == 0 else H * 0.07
        pts.append((ex + rr * math.cos(ang), ey + rr * math.sin(ang)))
    d.polygon(pts, fill=(255, 160, 40))
    # water with wave lines
    d.rectangle([0, H * 0.74, W, H], fill=(90, 140, 180))
    for i, yy in enumerate((0.80, 0.88, 0.95)):
        d.line([(W * (0.05 + 0.1 * i), H * yy), (W * (0.45 + 0.1 * i), H * yy)],
               fill=(200, 225, 245), width=max(1, int(H * 0.02)))
    label_bar(d, W, H, "KYIV")


def band_refinery(img, d, W, H):
    """Refinery at dusk: towers with lit edges, flame glow, drone."""
    gradient(d, 0, 0, W, H, [(0.0, (70, 50, 90)), (0.6, (200, 110, 70)),
                             (1.0, (255, 170, 90))])
    # towers (dark silhouettes, light left edge)
    for tx, tw, th in ((0.10, 0.10, 0.55), (0.26, 0.08, 0.72), (0.40, 0.12, 0.48),
                       (0.58, 0.09, 0.62), (0.72, 0.11, 0.40)):
        x0, x1 = W * tx, W * (tx + tw)
        d.rectangle([x0, H * 0.85 - H * th, x1, H * 0.85], fill=(42, 36, 52))
        d.line([(x0, H * 0.85 - H * th), (x0, H * 0.85)], fill=(150, 110, 90),
               width=max(1, int(W * 0.004)))
        d.rectangle([x0 + W * 0.01, H * 0.85 - H * th - H * 0.08,
                     x1 - W * 0.01, H * 0.85 - H * th], fill=(42, 36, 52))
    # flame on the middle tower + glow
    fx, fy = W * 0.30, H * 0.85 - H * 0.72 - H * 0.08
    glow(img, fx, fy - H * 0.08, H * 0.24, (255, 140, 40), alpha=130)
    d.polygon([(fx, fy - H * 0.22), (fx + W * 0.03, fy),
               (fx - W * 0.03, fy)], fill=(255, 170, 50))
    d.polygon([(fx, fy - H * 0.13), (fx + W * 0.016, fy),
               (fx - W * 0.016, fy)], fill=(255, 230, 120))
    # drone above (dark cross + rotor dots)
    dx, dy = W * 0.82, H * 0.24
    d.line([(dx - W * 0.035, dy), (dx + W * 0.035, dy)], fill=(25, 25, 30),
           width=max(2, int(H * 0.04)))
    d.line([(dx, dy - H * 0.06), (dx, dy + H * 0.06)], fill=(25, 25, 30),
           width=max(2, int(H * 0.04)))
    d.ellipse([dx - W * 0.012, dy - H * 0.03, dx + W * 0.012, dy + H * 0.03],
              fill=(25, 25, 30))
    label_bar(d, W, H, "RUSSIA")


def band_cyclone(img, d, W, H):
    """Cyclone Akvan: white spiral with a soft shadow, rain, coast."""
    gradient(d, 0, 0, W, H, [(0.0, (190, 215, 232)), (1.0, (225, 235, 240))])
    cx, cy = W * 0.50, H * 0.52
    # spiral shadow, then the white spiral
    pts = _spiral(cx + W * 0.012, cy + H * 0.03, H * 0.02, H * 0.34, 3.2)
    d.line(pts, fill=(120, 140, 160), width=max(2, int(H * 0.07)), joint="curve")
    pts = _spiral(cx, cy, H * 0.02, H * 0.34, 3.2)
    d.line(pts, fill=(255, 255, 255), width=max(2, int(H * 0.06)), joint="curve")
    d.ellipse([cx - H * 0.05, cy - H * 0.05, cx + H * 0.05, cy + H * 0.05],
              fill=(31, 78, 121))
    # rain streaks at the edges
    for i in range(6):
        x = W * (0.04 + i * 0.03)
        d.line([(x, H * 0.10), (x - W * 0.01, H * 0.30)], fill=(140, 165, 185),
               width=max(1, int(H * 0.02)))
        x = W * (0.90 + i * 0.015)
        d.line([(x, H * 0.55), (x - W * 0.01, H * 0.75)], fill=(140, 165, 185),
               width=max(1, int(H * 0.02)))
    # coast at the bottom
    d.polygon([(0, H), (0, H * 0.88), (W * 0.3, H * 0.82), (W * 0.6, H * 0.90),
               (W, H * 0.84), (W, H)], fill=(196, 178, 130))
    label_bar(d, W, H, "ODISHA")


def band_gaza(img, d, W, H):
    """Gaza: building silhouettes, rising smoke column, low sun."""
    gradient(d, 0, 0, W, H, [(0.0, (232, 214, 180)), (1.0, (245, 232, 205))])
    glow(img, W * 0.84, H * 0.24, H * 0.16, (255, 200, 110), alpha=100)
    d.ellipse([W * 0.80, H * 0.16, W * 0.88, H * 0.32], fill=(255, 205, 120))
    # buildings with lit windows
    for bx, bw, bh in ((0.02, 0.16, 0.42), (0.20, 0.13, 0.58), (0.35, 0.15, 0.48),
                       (0.52, 0.12, 0.66), (0.66, 0.14, 0.52), (0.82, 0.15, 0.60)):
        x0, x1 = W * bx, W * (bx + bw)
        d.rectangle([x0, H * 0.86 - H * bh, x1, H * 0.86], fill=(150, 138, 118))
        d.line([(x0, H * 0.86 - H * bh), (x0, H * 0.86)], fill=(210, 195, 170),
               width=max(1, int(W * 0.004)))
        for wy in (H * 0.86 - H * bh + H * 0.12, H * 0.86 - H * bh + H * 0.26):
            d.rectangle([x0 + W * 0.02, wy, x0 + W * 0.035, wy + H * 0.05],
                        fill=(255, 220, 130))
    # smoke column: soft grey puffs rising and widening
    for i, (sx, sy, sr) in enumerate(((0.58, 0.62, 0.07), (0.57, 0.48, 0.09),
                                      (0.59, 0.34, 0.11), (0.56, 0.20, 0.13))):
        glow(img, W * sx, H * sy, H * sr, (120, 115, 110), alpha=70)
        d.ellipse([W * (sx - sr), H * (sy - sr), W * (sx + sr), H * (sy + sr)],
                  fill=(150, 145, 140))
    label_bar(d, W, H, "GAZA")


def band_jets(img, d, W, H):
    """Three jets in formation with contrails and soft clouds."""
    gradient(d, 0, 0, W, H, [(0.0, (120, 180, 225)), (1.0, (215, 232, 244))])
    # soft clouds
    for cx, cy, r in ((0.18, 0.78, 0.10), (0.55, 0.86, 0.12), (0.88, 0.72, 0.09)):
        glow(img, W * cx, H * cy, H * r, (255, 255, 255), alpha=110)
    # contrails (thin, fading)
    for jx, jy in ((0.30, 0.42), (0.48, 0.58), (0.66, 0.34)):
        d.line([(W * (jx - 0.22), H * (jy + 0.10)), (W * jx, H * jy)],
               fill=(255, 255, 255), width=max(1, int(H * 0.025)))
    # jets (delta darts, dark with a light top edge)
    for jx, jy, s in ((0.30, 0.42, 0.055), (0.48, 0.58, 0.06), (0.66, 0.34, 0.05)):
        cx, cy = W * jx, H * jy
        ss = W * s
        d.polygon([(cx + ss, cy), (cx - ss * 0.6, cy - ss * 0.5),
                   (cx - ss * 0.3, cy), (cx - ss * 0.6, cy + ss * 0.5)],
                  fill=(52, 62, 80))
        d.line([(cx + ss, cy), (cx - ss * 0.6, cy - ss * 0.5)],
               fill=(170, 185, 205), width=max(1, int(H * 0.02)))
        soft_ellipse(img, [cx - ss * 0.5, cy - ss * 0.2, cx + ss * 0.6, cy + ss * 0.3],
                     W * 0.006, H * 0.02, max(2, int(W * 0.006)), alpha=70)
    label_bar(d, W, H, "KYIV")


def band_nasdaq(img, d, W, H):
    """NASDAQ debut: axes with tick labels, gridlines, bars, trend line."""
    gradient(d, 0, 0, W, H, [(0.0, (10, 42, 34)), (1.0, (16, 70, 55))])
    # gridlines + axes
    for gy in (0.25, 0.45, 0.65):
        d.line([(W * 0.10, H * gy), (W * 0.96, H * gy)], fill=(40, 95, 78),
               width=max(1, int(H * 0.015)))
    d.line([(W * 0.10, H * 0.08), (W * 0.10, H * 0.86)], fill=(220, 235, 225),
           width=max(1, int(W * 0.005)))
    d.line([(W * 0.10, H * 0.86), (W * 0.96, H * 0.86)], fill=(220, 235, 225),
           width=max(1, int(W * 0.005)))
    tf = font(SANS_R, H * 0.11)
    d.text((W * 0.015, H * 0.20), "$", font=tf, fill=(160, 190, 175))
    # bars, rising, each lighter at the top
    bars = [0.18, 0.26, 0.34, 0.46, 0.58]
    tops = []
    for i, bh in enumerate(bars):
        x0 = W * (0.16 + i * 0.155)
        x1 = x0 + W * 0.09
        y1 = H * 0.86
        y0 = y1 - H * bh
        tops.append(((x0 + x1) / 2, y0))
        gradient(d, x0, y0, x1, y1, [(0.0, (90, 220, 140)), (1.0, (30, 140, 90))])
        d.line([(x0, y0), (x1, y0)], fill=(160, 240, 190),
               width=max(1, int(H * 0.015)))
    # trend line with dots at each vertex
    d.line(tops, fill=(255, 255, 255), width=max(2, int(H * 0.035)), joint="curve")
    for px, py in tops:
        d.ellipse([px - H * 0.025, py - H * 0.025, px + H * 0.025, py + H * 0.025],
                  fill=(255, 255, 255))
    # ANT label + $83 badge
    af = font(SANS_B, H * 0.20)
    d.text((W * 0.14, H * 0.04), "ANT", font=af, fill=(255, 255, 255))
    bf = font(SANS_B, H * 0.16)
    bt = "$83"
    bw = d.textlength(bt, font=bf) + W * 0.03
    d.rounded_rectangle([W * 0.96 - bw, H * 0.05, W * 0.96, H * 0.05 + H * 0.24],
                        radius=H * 0.06, fill=(255, 210, 0))
    d.text((W * 0.96 - bw + W * 0.015, H * 0.075), bt, font=bf, fill=(20, 40, 30))
    label_bar(d, W, H, "NASDAQ")


def band_voyager(img, d, W, H):
    """Voyager 1: star field, sun glow, gold probe with a highlight."""
    d.rectangle([0, 0, W, H], fill=(6, 9, 22))
    # deterministic stars
    for i in range(26):
        sx = ((i * 137) % 100) / 100.0 * W
        sy = ((i * 71) % 100) / 100.0 * H
        r = H * (0.012 if i % 3 else 0.02)
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 255, 255))
    # sun glow, top-left
    glow(img, W * 0.10, H * 0.14, H * 0.22, (255, 220, 140), alpha=130)
    d.ellipse([W * 0.06, H * 0.06, W * 0.14, H * 0.22], fill=(255, 228, 160))
    # probe: gold dish + body + boom, with a soft shadow
    px, py = W * 0.58, H * 0.52
    soft_ellipse(img, [px - W * 0.05, py - H * 0.10, px + W * 0.10, py + H * 0.12],
                 W * 0.01, H * 0.03, max(2, int(W * 0.008)), alpha=100)
    d.line([(px, py), (px + W * 0.16, py - H * 0.10)], fill=(200, 170, 90),
           width=max(2, int(H * 0.04)))
    d.rectangle([px - W * 0.02, py - H * 0.05, px + W * 0.05, py + H * 0.05],
                fill=(212, 175, 55))
    d.line([(px - W * 0.02, py - H * 0.05), (px + W * 0.05, py - H * 0.05)],
           fill=(245, 220, 140), width=max(1, int(H * 0.02)))
    # dish (open parabola, facing up-left)
    d.pieslice([px - W * 0.11, py - H * 0.28, px + W * 0.02, py - H * 0.02],
               180, 360, fill=(232, 196, 110))
    d.pieslice([px - W * 0.11, py - H * 0.28, px + W * 0.02, py - H * 0.02],
               180, 360, outline=(245, 225, 150))
    d.line([(px - W * 0.045, py - H * 0.15), (px - W * 0.01, py - H * 0.05)],
           fill=(180, 145, 70), width=max(1, int(H * 0.03)))
    label_bar(d, W, H, "DEEP SPACE")


def band_strata(img, d, W, H):
    """Earth's lost billion years: wavy rock layers, one missing chunk."""
    layers = [
        ((216, 186, 144), 0.00, 0.20),
        ((186, 122, 74), 0.20, 0.40),
        ((146, 100, 62), 0.40, 0.58),
        ((110, 96, 86), 0.58, 0.76),
        ((82, 74, 66), 0.76, 1.00),
    ]
    for col, y0f, y1f in layers:
        pts = [(0, H * y1f), (0, H * y0f)]
        for i in range(21):
            t = i / 20
            pts.append((W * t, H * y0f + H * 0.03 * math.sin(t * math.pi * 2.2)))
        pts += [(W, H * y1f)]
        d.polygon(pts, fill=col)
        # top edge highlight on each layer
        hi = [(W * t, H * y0f + H * 0.03 * math.sin(t * math.pi * 2.2))
              for t in [i / 20 for i in range(21)]]
        d.line(hi, fill=tuple(min(255, c + 45) for c in col),
               width=max(1, int(H * 0.02)), joint="curve")
    # the missing chunk: a dark vertical gap through the middle layers
    d.rectangle([W * 0.58, H * 0.20, W * 0.66, H * 0.76], fill=(28, 22, 18))
    d.line([(W * 0.58, H * 0.20), (W * 0.58, H * 0.76)], fill=(230, 210, 180),
           width=max(1, int(H * 0.02)))
    d.line([(W * 0.66, H * 0.20), (W * 0.66, H * 0.76)], fill=(230, 210, 180),
           width=max(1, int(H * 0.02)))
    # small fossil spiral in the second layer
    fx, fy = W * 0.24, H * 0.30
    pts = _spiral(fx, fy, H * 0.01, H * 0.07, 2.5, n=60)
    d.line(pts, fill=(245, 240, 225), width=max(1, int(H * 0.025)), joint="curve")
    label_bar(d, W, H, "EARTH")


def band_dome(img, d, W, H):
    """St Peter's: shaded dome, lantern, colonnade, steps."""
    gradient(d, 0, 0, W, H, [(0.0, (222, 228, 234)), (1.0, (240, 236, 224))])
    cx = W * 0.50
    # soft shadow under the basilica
    soft_rect(img, [W * 0.10, H * 0.84, W * 0.90, H * 0.88], 0, H * 0.02,
              max(2, int(W * 0.008)), alpha=90)
    # dome: shaded half-circle (light from the left)
    d.pieslice([cx - W * 0.17, H * 0.06, cx + W * 0.17, H * 0.74], 180, 360,
               fill=(198, 172, 136))
    d.pieslice([cx - W * 0.17, H * 0.06, cx + W * 0.13, H * 0.74], 180, 360,
               fill=(216, 190, 154))
    # lantern + cross
    d.rectangle([cx - W * 0.025, H * 0.02, cx + W * 0.025, H * 0.10],
                fill=(200, 175, 140))
    d.line([(cx, H * -0.02), (cx, H * 0.05)], fill=(120, 100, 80),
           width=max(1, int(W * 0.006)))
    # drum + facade
    d.rectangle([cx - W * 0.19, H * 0.40, cx + W * 0.19, H * 0.86],
                fill=(208, 186, 152))
    d.line([(cx - W * 0.19, H * 0.40), (cx + W * 0.19, H * 0.40)],
           fill=(235, 220, 195), width=max(1, int(H * 0.02)))
    # colonnade: small columns with shadows
    for i in range(7):
        colx = W * (0.14 + i * 0.12)
        d.rectangle([colx - W * 0.012, H * 0.62, colx + W * 0.012, H * 0.86],
                    fill=(238, 230, 214))
        d.line([(colx - W * 0.012, H * 0.62), (colx - W * 0.012, H * 0.86)],
               fill=(190, 180, 160), width=max(1, int(W * 0.003)))
    # door
    d.rectangle([cx - W * 0.03, H * 0.70, cx + W * 0.03, H * 0.86],
                fill=(70, 55, 45))
    label_bar(d, W, H, "VATICAN")


BANDS = {"gta": band_gta, "euro": band_euro, "missile": band_missile,
         "bridge": band_bridge, "refinery": band_refinery,
         "cyclone": band_cyclone, "gaza": band_gaza, "jets": band_jets,
         "nasdaq": band_nasdaq, "voyager": band_voyager,
         "strata": band_strata, "dome": band_dome}


# ---------------------------------------------------------------- map
def draw_map_panel(img, x0, y0, x1, y1):
    """True world map (Natural Earth 110m coastline), rendered at 2x and
    downsampled so the coastline stays smooth, never boxy. Red numbered
    dots = featured stories 1-15; grey dots = briefs 16-35."""
    w, h = x1 - x0, y1 - y0
    S = 2
    big = Image.new("RGB", (w * S, h * S), OCEAN)
    d = ImageDraw.Draw(big)
    with open(os.path.join(HERE, "coastline.json")) as fh:
        rings = json.load(fh)
    lat_top, lat_bot = 84.0, -56.0
    scale = min(w / 360.0, h / (lat_top - lat_bot)) * S
    mw = 360.0 * scale
    ox = ((w * S) - mw) / 2
    oy = 0

    def proj(lon, lat):
        return (ox + (lon + 180.0) * scale, oy + (lat_top - lat) * scale)

    for ring in rings:
        pts = [proj(lon, lat) for lon, lat in ring]
        if len(pts) >= 3:
            d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    # grey dots (briefs)
    for lon, lat in MAP_GREY:
        px, py = proj(lon, lat)
        r = 3 * S
        d.ellipse([px - r, py - r, px + r, py + r], fill=(120, 120, 120),
                  outline=(255, 255, 255), width=S)
    # red numbered badges (featured stories)
    for num, lon, lat, (dx, dy) in MAP_RED:
        px, py = proj(lon, lat)
        d.ellipse([px - 3 * S, py - 3 * S, px + 3 * S, py + 3 * S], fill=RED,
                  outline=(255, 255, 255), width=S)
        bx, by = px + dx * S, py + dy * S
        if (dx, dy) != (10, -10):
            d.line([(px, py), (bx, by)], fill=RED, width=S)
        r = 7 * S
        d.ellipse([bx - r, by - r, bx + r, by + r], fill=RED,
                  outline=(255, 255, 255), width=S)
        t = str(num)
        tf = font(SANS_B, 11 * S)
        tw = d.textlength(t, font=tf)
        d.text((bx - tw / 2, by - 7 * S), t, font=tf, fill=(255, 255, 255))
    small = big.resize((w, h), Image.LANCZOS)
    img.paste(small, (x0, y0))
    d2 = ImageDraw.Draw(img)
    d2.rectangle([x0, y0, x1, y1], outline=INK, width=2)


HERO_ART = {1: art_summit, 2: art_court, 3: art_cop31}


def render(out_path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # ---- top strip
    d.text((28, 4), "MAKE.FUN  \u00b7  THE WORLD IN ONE DAY",
           font=font(SANS_B, 11), fill=GREY)
    right = "No. 20261119  \u00b7  FREE"
    d.text((W - 28 - d.textlength(right, font=font(SANS_B, 11)), 4), right,
           font=font(SANS_B, 11), fill=GREY)
    rule(d, 28, W - 28, 20)

    # ---- masthead
    title = "Thursday 19 November 2026"
    tf = font(SERIF_BLACK, 54)
    tw = d.textlength(title, font=tf)
    d.text(((W - tw) / 2, 24), title, font=tf, fill=INK)
    sub = ("Trump, Xi and Putin share one table  \u00b7  The World Court "
           "rules on Myanmar  \u00b7  COP31 enters its final 48 hours")
    sf = font(SERIF_I, 17)
    sw = d.textlength(sub, font=sf)
    d.text(((W - sw) / 2, 82), sub, font=sf, fill=RED)

    # ---- region strip (counts sum to 35; asserted below)
    assert sum(c for _, c, _ in REGIONS) == 35
    rx, ry, rh = 28, 102, 15
    col_w = (W - 56) / len(REGIONS)
    for i, (name, count, col) in enumerate(REGIONS):
        x0 = rx + i * col_w
        d.rectangle([x0, ry, x0 + col_w - 2, ry + rh], fill=col)
        t = "%s %d" % (name, count)
        lf = font(SANS_B, 11)
        d.text((x0 + (col_w - 2 - d.textlength(t, font=lf)) / 2, ry + 1), t,
               font=lf, fill=(255, 255, 255))

    # ---- big-number stat strip
    sx = 28
    cell_w = (W - 56) / len(STATS)
    for i, (num, cap) in enumerate(STATS):
        cx = sx + i * cell_w
        nf = font(SERIF_BLACK, 25)
        d.text((cx + 6, 122), num, font=nf, fill=INK)
        cf = font(SANS_R, 10)
        d.text((cx + 6, 148), cap, font=cf, fill=GREY)
        if i:
            d.line([(cx, 122), (cx, 160)], fill=(200, 190, 165), width=1)
    rule(d, 28, W - 28, 164)

    # ---- three heroes
    hero_x = [28, 356, 684]
    hero_w = 312
    for i, hero in enumerate(HEROES):
        hx = hero_x[i]
        art = ss_art(hero_w, 124, HERO_ART[hero["num"]])
        img.paste(art, (hx, 170))
        d.rectangle([hx, 170, hx + hero_w, 294], outline=INK, width=1)
        ky = 300
        kf = font(SANS_B, 10)
        d.text((hx, ky), "%d \u00b7 %s" % (hero["num"], hero["kicker"]),
               font=kf, fill=RED)
        head = wrap(d, hero["head"], font(SERIF_B, 20), hero_w)
        assert len(head) <= 3, "hero %d headline too long: %r" % (hero["num"], head)
        y = text_block(d, hx, ky + 15, head, font(SERIF_B, 20), INK, 23)
        body = wrap(d, hero["body"] + " \u2014 " + hero["src"],
                    font(SERIF_R, 11.5), hero_w)
        assert len(body) <= 3, "hero %d body too long: %r" % (hero["num"], body)
        text_block(d, hx, y + 2, body, font(SERIF_R, 11.5), INK, 14.5)
    rule(d, 28, W - 28, 428)

    # ---- twelve mid stories, two rows of six
    mid_w, mid_h = 157, 48
    for row in range(2):
        y0 = 434 + row * 138
        for col in range(6):
            m = MIDS[row * 6 + col]
            num, kicker, head, body, src, key = m
            mx = 28 + col * 162
            art = ss_art(mid_w, mid_h, BANDS[key])
            img.paste(art, (mx, y0))
            d.rectangle([mx, y0, mx + mid_w, y0 + mid_h], outline=INK, width=1)
            ky = y0 + mid_h + 5
            kf = font(SANS_B, 9)
            d.text((mx, ky), "%d \u00b7 %s" % (num, kicker), font=kf, fill=RED)
            hl = wrap(d, head, font(SANS_B, 11.5), mid_w)
            assert len(hl) <= 2, "mid %d headline too long: %r" % (num, hl)
            y = text_block(d, mx, ky + 12, hl, font(SANS_B, 11.5), INK, 13)
            bl = wrap(d, body + " \u2014 " + src, font(SANS_R, 9.5), mid_w)
            assert len(bl) <= 3, "mid %d body too long: %r" % (num, bl)
            text_block(d, mx, y + 2, bl, font(SANS_R, 9.5), INK, 12)
    rule(d, 28, W - 28, 708)

    # ---- map + also-on-thursday
    d.text((28, 714), "WHERE IT HAPPENED", font=font(SANS_B, 13), fill=INK)
    d.text((512, 714), "ALSO ON THURSDAY 19 NOVEMBER 2026",
           font=font(SANS_B, 13), fill=RED)
    draw_map_panel(img, 28, 732, 500, 920)
    cap = ("Red numbers mark stories 1\u201315; grey dots mark briefs 16\u201335. "
           "Positions approximate.")
    d.text((28, 924), cap, font=font(SANS_R, 9), fill=GREY)
    col_x = [512, 760]
    for idx, (num, place, head, src) in enumerate(ALSO):
        col = idx // 10
        row = idx % 10
        ax = col_x[col]
        ay = 734 + row * 19
        nf = font(SANS_B, 10)
        d.text((ax, ay), "%02d" % num, font=nf, fill=RED)
        line = "%s \u2014 %s. %s" % (place, head, src)
        lf = font(SANS_R, 10)
        d.text((ax + 24, ay),
               fit(d, line, lf, 236 - 24), font=lf, fill=INK)
    rule(d, 28, W - 28, 942)

    # ---- DATE CHECK box (factual: what was left out, and why).
    # The check mark is drawn as a vector (two strokes) — the serif
    # font has no U+2713 glyph, and a tofu box would look broken.
    body = ("Every story on this page happened, or was first reported, on "
            "Thursday 19 November 2026. LEFT OUT AS OTHER DAYS' NEWS: "
            "COP31's scheduled close (Fri 20 Nov) \u00b7 Cyclone Akvan's "
            "landfall (Fri 20 Nov) \u00b7 Nvidia's results (Wed 18 Nov) "
            "\u00b7 Anthropic's $83 IPO pricing (Wed 18 Nov) \u00b7 Van Gogh "
            "sold for $190.4m (Wed 18 Nov) \u00b7 Imamoglu sentenced "
            "(Wed 18 Nov) \u00b7 IAEA on North Korea's Yongbyon (Wed 18 Nov).")
    d.rectangle([28, 946, W - 28, 992], outline=DARKRED, width=2)
    bf = font(SERIF_B, 10.5)
    rf = font(SERIF_R, 10.5)
    prefix = "DATE CHECK "
    d.text((36, 950), prefix, font=bf, fill=DARKRED)
    cx = 36 + d.textlength(prefix, font=bf)
    d.line([(cx + 1, 956), (cx + 4, 960), (cx + 10, 951)], fill=DARKRED,
           width=2)
    rest_x = cx + 14
    first_w = (W - 36) - rest_x
    full_w = W - 56 - 16
    words = body.split()
    cur, used = "", 0
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=rf) <= first_w:
            cur, used = trial, used + 1
        else:
            break
    lines = [cur] + wrap(d, " ".join(words[used:]), rf, full_w)
    assert len(lines) <= 3, "DATE CHECK too long: %d lines" % len(lines)
    d.text((rest_x, 950), lines[0], font=rf, fill=INK)
    text_block(d, 36, 963, lines[1:], rf, INK, 13)

    # ---- footer
    foot = ("Sources: Reuters, AP, AFP, BBC, Al Jazeera, DW, The Hindu, "
            "NDTV, France 24. Drawn by hand in code \u2014 no photographs. "
            " \u00b7  THURSDAY, 19 NOVEMBER 2026")
    d.text((28, 998), foot, font=font(SANS_R, 9), fill=GREY)

    img.save(out_path, "PNG")
    print("wrote", out_path, os.path.getsize(out_path), "bytes")


def main():
    out = os.path.join(HERE, "entry.png")
    render(out)


if __name__ == "__main__":
    main()
