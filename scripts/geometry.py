"""Node shapes, slot positions and wire shapes, computed the same way the frontend (litegraph) does.
Python standard library only.

Behaviour checked against positions the frontend produces:
- The title bar is 30px above pos. The rectangle a node occupies is [x, y - 30, w, h + 30].
- Slots of inputs without a widget, and outputs, sit at y = pos.y + (k + 0.7) x 20 (k is the index among
  inputs without a widget, or among outputs). Inputs are at x = pos.x + 10, outputs at x = pos.x + w + 1 - 10.
- Widgets start at y = rows x 20 + 6 (rows = max(inputs without a widget, outputs, 1)).
  A normal widget is 24 high. Growable widgets (multiline text, etc.) share the remaining height.
- The slot of an input that has a widget is at that widget's y + 10.
- A wire (spline) is a cubic Bezier whose control points are offset horizontally by distance x 0.25 from each end.
"""

TITLE = 30
SLOT = 20
WIDGET = 24
GROWABLE = {"customtext", "textarea", "multiline"}


NO_TITLE_TYPES = {"Reroute"}  # nodes drawn without a title bar (the frontend gives Reroute no title)


def title_height(n):
    return 0 if n.get("type") in NO_TITLE_TYPES else TITLE


def rect(n):
    """Rectangle a node occupies (including the title bar): (x0, y0, x1, y1)"""
    x, y = n["pos"]
    w, h = n["size"]
    return (x, y - title_height(n), x + w, y + h)


def _rows(n):
    socket_inputs = [i for i in n.get("inputs") or [] if not i.get("widget")]
    return max(len(socket_inputs), len(n.get("outputs") or []), 1)


def widget_layout(n, widget_names, growable=()):
    """{widget name: (top y, height)} relative to the node's pos. widget_names is in drawing order."""
    start = _rows(n) * SLOT + 6
    body = n["size"][1]
    fixed = sum(WIDGET for w in widget_names if w not in growable)
    n_grow = sum(1 for w in widget_names if w in growable)
    grow_h = max(WIDGET, (body - start - fixed) / n_grow) if n_grow else 0
    out, y = {}, start
    for w in widget_names:
        h = grow_h if w in growable else WIDGET
        out[w] = (y, h)
        y += h
    return out


def input_pos(n, name, widget_names=None, growable=()):
    x, y = n["pos"]
    ins = n.get("inputs") or []
    inp = next((i for i in ins if i["name"] == name), None)
    if inp is None:
        return None
    if inp.get("widget") and widget_names:
        lay = widget_layout(n, widget_names, growable)
        wname = (inp.get("widget") or {}).get("name", name)
        if wname in lay:
            return (x + SLOT / 2, y + lay[wname][0] + SLOT / 2)
    sockets = [i for i in ins if not i.get("widget")]
    k = sockets.index(inp) if inp in sockets else len(sockets)
    return (x + SLOT / 2, y + (k + 0.7) * SLOT)


def output_pos(n, slot):
    x, y = n["pos"]
    return (x + n["size"][0] + 1 - SLOT / 2, y + (slot + 0.7) * SLOT)


def spline(a, b, steps=24):
    """Points along a wire. a is the output position, b the input position."""
    dist = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
    c1 = (a[0] + dist * 0.25, a[1])
    c2 = (b[0] - dist * 0.25, b[1])
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        pts.append((u ** 3 * a[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * b[0],
                    u ** 3 * a[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * b[1]))
    return pts


def _seg_hits_rect(p, q, r):
    """Whether segment pq passes through the inside of rectangle r (Liang-Barsky)."""
    x0, y0, x1, y1 = r
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pk, qk in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pk == 0:
            if qk < 0:
                return False
        else:
            t = qk / pk
            if pk < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
            if t0 > t1:
                return False
    return True


def wire_hits(points, r, margin=2):
    """Whether a wire (points) passes through rectangle r (shrunk slightly inward)."""
    x0, y0, x1, y1 = r
    inner = (x0 + margin, y0 + margin, x1 - margin, y1 - margin)
    return any(_seg_hits_rect(points[i], points[i + 1], inner) for i in range(len(points) - 1))
