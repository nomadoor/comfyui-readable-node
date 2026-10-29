"""Initial node size (the size a node has when it is created in ComfyUI), computed as the frontend does.

Checked against the sizes the frontend gives when it creates every node type:
- width = max(input + output label widths + 40 (+5 if both exist), widget label width + 104,
              30 + title width + 9.9, 140 (210 with widgets)), plus 60 more with widgets.
- A multiline text widget (customtext) is 50 high. With one, the node is at least 400 wide and 200 high.
- height = rows x 20 + sum(widget height + 4) + 8 (with widgets) + 6. A normal widget is 20 high.
Text widths come from fontmetrics.py (measured in Inter on the frontend).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comfy_schema  # noqa: E402
import fontmetrics as F  # noqa: E402

MULTILINE_MIN_W = 400
MULTILINE_H = 50
MULTILINE_MIN_H = 200
# Nodes with a multiline widget that have no reason to be large. Instead of the 400 x 200 they get when
# created, use the smallest size that fits the contents (the lower width bound is min_width; see sizes in readable-form.md)
COMPACT_TYPES = {"StringFormat", "ComfyMathExpression"}


def _label(info, name):
    for sec in ("required", "optional"):
        sp = ((info.get("input") or {}).get(sec) or {}).get(name)
        if sp and len(sp) > 1 and isinstance(sp[1], dict) and sp[1].get("display_name"):
            return sp[1]["display_name"]
    return name


def _multiline(info):
    out = set()
    for nm, spec, _ in comfy_schema.ordered_input_specs(info):
        if spec[0] == "STRING" and len(spec) > 1 and isinstance(spec[1], dict) and spec[1].get("multiline"):
            out.add(nm)
    return out


def default_size(n, oi, title=None):
    """Initial size of node n (a flat-graph or UI-format node). None if the type is unknown."""
    info = oi.get(n.get("type"))
    if info is None:
        return None
    title = title or n.get("title") or info.get("display_name") or n.get("type")
    widgets = comfy_schema.widget_names(info, n.get("widgets_values"))
    ins = n.get("inputs") or []
    sock = [i for i in ins if not i.get("widget")]
    winp = [i for i in ins if i.get("widget")]
    outs = n.get("outputs") or []
    # (a type with measured heights, AUTOGROW_ROWS, takes them below instead)
    room = 0 if n.get("type") in AUTOGROW_ROWS else autogrow_room(info, sock)
    rows = max(len(sock) + room, len(outs), 1)
    iw = max([F.label_width(i.get("label") or _label(info, i["name"])) for i in sock] or [0])
    ow = max([F.label_width(o.get("label") or o.get("name") or "") for o in outs] or [0])
    # widget labels: from the widget inputs the node has (from the widget names if Export packed them)
    wl = [i.get("label") or _label(info, i["name"]) for i in winp] or [_label(info, w) for w in widgets
                                                                      if w not in ("control_after_generate", "upload")]
    ww = max([F.label_width(x) for x in wl] or [0])
    ww = ww + 42 + 2 * (15 + 6 + 10) if ww else 0
    w = max(iw + ow + 40 + (5 if iw and ow else 0), ww, 30 + F.title_width(title) + 9.9,
            140 * (1.5 if widgets else 1))
    if widgets:
        w += 60
    multi = _multiline(info)
    compact = n.get("type") in COMPACT_TYPES
    if multi & set(widgets) and not compact:
        w = max(w, MULTILINE_MIN_W)
    h = rows * 20
    if widgets:
        h += sum((MULTILINE_H if x in multi else 20) + 4 for x in widgets) + 8
    h += 6
    if multi & set(widgets) and not compact:
        h = max(h, MULTILINE_MIN_H)
    if n.get("type") in AUTOGROW_ROWS:
        # Autogrow inputs (values.a, b, ...) grow with the number connected. Heights measured from the frontend
        # (0 connected: 128, 1-3: 148, then +20 per link from 4: 188, 5: 208, 6: 228); sized for AUTOGROW_ASSUMED at least
        k = max(AUTOGROW_ASSUMED, sum(1 for i in ins if not i.get("widget") and i.get("link") is not None))
        h = max(h, 128 if k == 0 else 148 if k <= 3 else 148 + 20 * (k - 2))
    if n.get("type") in AUDIO_UI_TYPES:
        # the audio player (62px) the frontend adds; with other widgets it overlaps the 8px gap between them
        h += AUDIO_UI_H - 8 if widgets else AUDIO_UI_H
    return [round(w, 1), round(h, 1)]


# Nodes the frontend adds an audio player to. The height was measured from the frontend
AUDIO_UI_TYPES = {"LoadAudio", "SaveAudio", "PreviewAudio", "SaveAudioMP3", "SaveAudioOpus", "SaveAudioAdvanced"}
AUDIO_UI_H = 62
AUTOGROW_ROWS = {"ComfyMathExpression"}
# An Autogrow input (image_1, image_2, ... added as they are connected) is sized as if this many were connected, with
# the empty one the frontend adds after them: more than three are rarely connected (the skill author)
AUTOGROW_ASSUMED = 3


def autogrow_room(info, sock):
    """Rows to add so every Autogrow input of the node has room for AUTOGROW_ASSUMED connected inputs and the empty
    one after them (no more than its max)."""
    add = 0
    for name, spec, _ in comfy_schema.ordered_input_specs(info):
        if not (isinstance(spec, (list, tuple)) and spec and spec[0] == "COMFY_AUTOGROW_V3"):
            continue
        tpl = (spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}).get("template") or {}
        cap = len(tpl["names"]) if tpl.get("names") else tpl.get("max", 100)
        have = sum(1 for i in sock if str(i.get("name", "")).startswith(name + "."))
        add += max(0, min(cap, AUTOGROW_ASSUMED + 1) - have)
    return add


# Nodes 2.0 draws nodes at least 225px wide (the frontend's minimum node width).
# Even where the legacy renderer allows narrower, 225px is the lower bound so both look the same.
MIN_NODE_WIDTH = 225
# The legacy renderer cuts the title with "..." when the node is narrower than the title width + 30 on each side.
# At exactly +60 (Conditioning Zero Out, 144 + 60 = 204px) it was still cut, so 10px of margin is added.
TITLE_PAD = 70


def title_fits_width(title):
    """Width at which the whole title is visible without being cut."""
    return F.title_width(title) + TITLE_PAD


def min_width(title):
    """Lower bound of a node's width: the larger of the full-title width and the Nodes 2.0 minimum width."""
    return max(MIN_NODE_WIDTH, title_fits_width(title))


def estimate_unknown(n):
    """Size estimate for a node whose type is unknown (a custom node that is not installed). If the original
    workflow saved a size, the canvas does not go below it (orig_size from flatten.py).
    The number of widgets is the length of widgets_values."""
    sock = [i for i in n.get("inputs") or [] if not i.get("widget")]
    rows = max(len(sock), len(n.get("outputs") or []), 1)
    wv = n.get("widgets_values")
    vals = list(wv) if isinstance(wv, list) else (list(wv.values()) if isinstance(wv, dict) else [])
    k = len(vals)
    w = 140 * (1.5 if k else 1) + (60 if k else 0)
    # the frontend shows one UNKNOWN widget per value: strings longer than 20 characters are multiline (62px), others 24px
    multi = [v for v in vals if isinstance(v, str) and len(v) > 20]
    single = k - len(multi)
    h = rows * 20 + 6 + len(multi) * UNKNOWN_MULTILINE_H + (single * 24 + 8 if single else 0)
    return [w, h]


UNKNOWN_MULTILINE_H = 62   # measured from the frontend (MelBandRoFormerModelLoader not installed: 88 = 26 + 62)
