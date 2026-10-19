"""Draw a preview picture (PNG) so the agent can look at the layout and correct its decisions.
Python standard library only.

Draws groups, nodes (colour, title bar, id and title) and wires (the same spline as the frontend, coloured by type).
Wires passing behind a node are drawn as thick white lines, so the check result can be seen.
Text uses a 5x7 bitmap font (capital letters, digits, symbols). Lower case is drawn as capitals; characters
outside the font (CJK, etc.) are left out of titles, and anything else unknown becomes "?".
Node ids are drawn as passed in ``names`` (the canvas ids), or as the workflow's ids otherwise.
"""

import json
import struct
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comfy_schema  # noqa: E402
import geometry as G  # noqa: E402
import write_workflow  # noqa: E402

BG = (32, 32, 32)
NODE_BG = (53, 53, 53)
NODE_TITLE = (51, 51, 51)
BORDER = (90, 90, 90)
TEXT = (230, 230, 230)
HIT = (255, 255, 255)  # marks a wire passing behind a node: white, unlike any type colour (to tell it from VAE red)
# wire colours of the frontend's dark palette
LINK_COLORS = {
    "MODEL": "#B39DDB", "CLIP": "#FFD500", "VAE": "#FF6E6E", "CONDITIONING": "#FFA931", "LATENT": "#FF9CF9",
    "IMAGE": "#64B5F6", "MASK": "#81C784", "CONTROL_NET": "#6EE7B7", "CLIP_VISION": "#A8DADC",
    "CLIP_VISION_OUTPUT": "#ad7452", "NOISE": "#B0B0B0", "GUIDER": "#66FFFF", "SAMPLER": "#ECB4B4",
    "SIGMAS": "#CDFFCD", "STYLE_MODEL": "#C2FFAE", "TAESD": "#DCC274",
}
DEFAULT_LINK = "#99AA99"

# 5x7 bitmap. 5 characters per row; "#" is a dot.
FONT_SRC = {
    "A": ".###.#...##...########...##...##...#", "B": "####.#...##...#####.#...##...#####.",
    "C": ".###.#...##....#....#....#...#.###.", "D": "####.#...##...##...##...##...#####.",
    "E": "######....#....####.#....#....#####", "F": "######....#....####.#....#....#....",
    "G": ".###.#...##....#.####...##...#.####", "H": "#...##...##...#######...##...##...#",
    "I": ".###...#....#....#....#....#...###.", "J": "..###...#....#....#....##..#..##..",
    "K": "#...##..#.#.#..##...#.#..#..#.#...#", "L": "#....#....#....#....#....#....#####",
    "M": "#...###.###.#.##...##...##...##...#", "N": "#...###..##.#.##..###...##...##...#",
    "O": ".###.#...##...##...##...##...#.###.", "P": "####.#...##...#####.#....#....#....",
    "Q": ".###.#...##...##...##.#.##..#..##.#", "R": "####.#...##...#####.#.#..#..#.#...#",
    "S": ".####.....#.....###.....#....#####.", "T": "#####..#....#....#....#....#....#..",
    "U": "#...##...##...##...##...##...#.###.", "V": "#...##...##...##...##...#.#.#...#..",
    "W": "#...##...##...##.#.##.#.##.#.#.#.#.", "X": "#...##...#.#.#...#...#.#.#...##...#",
    "Y": "#...##...#.#.#...#....#....#....#..", "Z": "#####....#...#...#...#...#....#####",
    "0": ".###.#...##..###.#.###..##...#.###.", "1": "..#...##....#....#....#....#...###.",
    "2": ".###.#...#....#...#...#...#...#####", "3": "#####...#...#.....#....##...#.###.",
    "4": "...#...##..#.#.#..#.#####...#....#.", "5": "######....####.....#....##...#.###.",
    "6": "..##..#...#....####.#...##...#.###.", "7": "#####....#...#...#...#....#....#...",
    "8": ".###.#...##...#.###.#...##...#.###.", "9": ".###.#...##...#.####....#...#..##..",
    " ": "." * 35, ".": "." * 25 + "..#....#..", ",": "." * 20 + "..#....#...#.....",
    ":": ".....##...##.......##...##........", "-": "..........#####....................",
    "_": "." * 30 + "#####", "(": "...#...#...#....#....#.....#.....#.", ")": ".#.....#.....#....#....#...#...#...",
    "/": "....#....#...#...#...#....#....#...", "+": ".......#....#..#####..#....#.......",
    "[": ".###..#....#....#....#....#....###.", "]": ".###....#....#....#....#....#..###.",
    "&": ".##..#..#.#.#...#...#.#.#.#..#..#.#", "'": "..#....#...#......................",
    "?": ".###.#...#....#...#...#.........#..", "!": "..#....#....#....#....#.........#..",
    "#": ".#.#..#.#.#####.#.#.#####.#.#..#.#.", "%": "##...##..#...#...#...#...#..##...##",
    "=": "..........#####.....#####..........", "<": "...#...#...#...#.....#.....#.....#.",
    ">": ".#.....#.....#.....#...#...#...#...", "*": ".......#.#.#.#.###.#.#.#.#.........",
    "|": "..#....#....#....#....#....#....#..", "~": "...........#.#.#.#................",
    "@": ".###.#...##.####.#.##.###....#.###.", "\"": ".#.#..#.#..........................",
    "^": "..#...#.#.#...#....................", "$": "..#...####.#....###....#.####...#..",
}
# glyphs easier to check when written row by row (avoids miscounting)
FONT_ROWS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    ",": [".....", ".....", ".....", ".....", "..#..", "..#..", ".#..."],
    ":": [".....", "..#..", "..#..", ".....", "..#..", "..#..", "....."],
    "'": ["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."],
    "~": [".....", ".....", ".#.#.", "#.#..", ".....", ".....", "....."],
}
for ch, rows in FONT_ROWS.items():
    assert all(len(r) == 5 for r in rows) and len(rows) == 7, ch
    FONT_SRC[ch] = "".join(rows)
FONT = {}
for ch, bits in FONT_SRC.items():
    assert len(bits) == 35, ch
    FONT[ch] = [bits[r * 5:(r + 1) * 5] for r in range(7)]


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ascii_part(s):
    """Keep only characters the picture can draw (letters, digits, symbols). Drop CJK etc. and collapse the spaces left behind."""
    t = "".join(ch if ch.upper() in FONT or ch == " " else " " for ch in s)
    return " ".join(t.split()).strip(" :：-")

class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def rect(self, x0, y0, x1, y1, c):
        x0, y0 = max(0, int(x0)), max(0, int(y0))
        x1, y1 = min(self.w, int(x1)), min(self.h, int(y1))
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def frame(self, x0, y0, x1, y1, c, t=1):
        self.rect(x0, y0, x1, y0 + t, c)
        self.rect(x0, y1 - t, x1, y1, c)
        self.rect(x0, y0, x0 + t, y1, c)
        self.rect(x1 - t, y0, x1, y1, c)

    def dot(self, x, y, r, c):
        self.rect(x - r, y - r, x + r + 1, y + r + 1, c)

    def line(self, p, q, r, c):
        n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]))) + 1
        for i in range(n + 1):
            t = i / n
            self.dot(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t, r, c)

    def text(self, x, y, s, c, scale=1, max_w=None):
        cx = x
        for ch in s.upper():
            if max_w is not None and cx + 5 * scale > x + max_w:
                break
            g = FONT.get(ch, FONT["?"])
            for r, row in enumerate(g):
                for k, b in enumerate(row):
                    if b == "#":
                        self.rect(cx + k * scale, y + r * scale, cx + (k + 1) * scale, y + (r + 1) * scale, c)
            cx += 6 * scale

    def png(self):
        raw = b"".join(b"\x00" + bytes(self.px[y * self.w * 3:(y + 1) * self.w * 3]) for y in range(self.h))

        def chunk(t, d):
            return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def widget_info(n, oi):
    info = oi.get(n.get("type"))
    if not info:
        return [], set()
    names = comfy_schema.widget_names(info, n.get("widgets_values"))
    grow = set()
    for nm, spec, _ in comfy_schema.ordered_input_specs(info):
        if spec[0] == "STRING" and len(spec) > 1 and isinstance(spec[1], dict) and spec[1].get("multiline"):
            grow.add(nm)
    return names, grow


def wires(wf, oi):
    """[(link id, type, points)]. Points are in canvas coordinates."""
    nodes = {n["id"]: n for n in wf["nodes"]}
    out = []
    for l in wf["links"]:
        lid, o, os_, t, ts, typ = l[:6]
        on, tn = nodes.get(o), nodes.get(t)
        if not on or not tn or ts >= len(tn.get("inputs") or []):
            continue
        names, grow = widget_info(tn, oi)
        b = G.input_pos(tn, tn["inputs"][ts]["name"], names, grow)
        a = G.output_pos(on, os_)
        if a and b:
            out.append((lid, typ, G.spline(a, b)))
    return out


def wire_node_hits(wf, oi):
    """Where a wire passes behind a node: [(link id, node id)]. The wire's own end nodes are excluded."""
    nodes = wf["nodes"]
    ends = {l[0]: (l[1], l[3]) for l in wf["links"]}
    hits = []
    for lid, _, pts in wires(wf, oi):
        for n in nodes:
            if n["id"] in ends.get(lid, ()) or n.get("type") in ("Reroute",):
                continue
            if G.wire_hits(pts, G.rect(n)):
                hits.append((lid, n["id"]))
    return hits


def render(wf, oi, max_width=2400, max_height=2400, names=None):
    rects = [G.rect(n) for n in wf["nodes"]] + [
        (g["bounding"][0], g["bounding"][1], g["bounding"][0] + g["bounding"][2], g["bounding"][1] + g["bounding"][3])
        for g in wf.get("groups") or []]
    if not rects:
        return Canvas(10, 10, BG)
    x0 = min(r[0] for r in rects) - 40
    y0 = min(r[1] for r in rects) - 40
    x1 = max(r[2] for r in rects) + 40
    y1 = max(r[3] for r in rects) + 40
    s = min(1.0, max_width / (x1 - x0), max_height / (y1 - y0))
    cv = Canvas(int((x1 - x0) * s) + 1, int((y1 - y0) * s) + 1, BG)

    def P(p):
        return ((p[0] - x0) * s, (p[1] - y0) * s)

    for g in wf.get("groups") or []:
        bx, by, bw, bh = g["bounding"]
        col = hex_rgb(g.get("color") or "#3f789e")
        dim = tuple(int(v * 0.35 + 32 * 0.65) for v in col)
        a, b = P((bx, by)), P((bx + bw, by + bh))
        cv.rect(a[0], a[1], b[0], b[1], dim)
        cv.rect(a[0], a[1], b[0], a[1] + 30 * s, tuple(int(v * 0.6) for v in col))
        cv.text(a[0] + 4, a[1] + 3, ascii_part(g.get("title") or "") or "GROUP", TEXT, 1, max_w=b[0] - a[0] - 8)
    hit_links = {lid for lid, _ in wire_node_hits(wf, oi)}
    width = max(1, round(1.5 * s))
    for lid, typ, pts in wires(wf, oi):
        col = HIT if lid in hit_links else hex_rgb(LINK_COLORS.get(typ, DEFAULT_LINK))
        r = width + 1 if lid in hit_links else width
        sp = [P(p) for p in pts]
        for i in range(len(sp) - 1):
            cv.line(sp[i], sp[i + 1], r // 2 if r > 1 else 0, col)
    tscale = 2 if s >= 0.75 else 1
    for n in wf["nodes"]:
        rx0, ry0, rx1, ry1 = G.rect(n)
        a, b = P((rx0, ry0)), P((rx1, ry1))
        body = hex_rgb(n["bgcolor"]) if n.get("bgcolor") else NODE_BG
        head = hex_rgb(n["color"]) if n.get("color") else NODE_TITLE
        cv.rect(a[0], a[1], b[0], b[1], body)
        cv.frame(a[0], a[1], b[0], b[1], BORDER)
        if G.title_height(n) == 0:
            continue
        cv.rect(a[0] + 1, a[1] + 1, b[0] - 1, a[1] + G.TITLE * s, head)
        # The picture font has only Latin letters and digits (no CJK glyphs). A CJK title shows its Latin part, or the type name
        label = f"{(names or {}).get(n['id'], n['id'])} {ascii_part(n.get('title') or '') or n.get('type')}"
        cv.text(a[0] + 4, a[1] + max(2, (G.TITLE * s - 7 * tscale) / 2), label, TEXT, tscale, max_w=b[0] - a[0] - 8)
    return cv
