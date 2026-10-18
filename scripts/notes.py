"""Model Note text and Markdown Note heights. Python standard library only.

- ``collect_models`` gathers the models a workflow uses: from each node's ``properties.models`` (file name,
  URL, folder) and from widget values that are model file names (for custom nodes the server does not know,
  from ``widgets_values``). ``properties.models`` entries are used only when the same file name is also a
  widget value of that node.
- ``FolderFinder`` looks up the ``ComfyUI/models`` folder of a file name through a running server
  (``/models/<folder>``).
- ``model_note_text`` writes the model list and the folder tree. Format: references/notes.md. URLs and
  sizes come only from ``properties.models`` or from what the agent passes; no URL is ever guessed.
- ``note_height`` estimates the height at which a MarkdownNote's body fits without a scroll bar in the
  legacy renderer and without the node growing in Nodes 2.0. The frontend does not let a MarkdownNote
  shrink below 210 x 88 (checked by loading notes into it).
"""

import json
import math
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fontmetrics as F  # noqa: E402

MODEL_EXT = (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".gguf", ".sft", ".onnx")
PURPLE = ("#323", "#535")
NOTE_W = 400
from layout_params import P  # noqa: E402  (tunable values; meaning and source in layout_params.json)
V_GAP = P["V_GAP"]
H_GAP = P["H_GAP"]
NOTE_MIN = (210, 88)   # the frontend does not let a MarkdownNote get smaller (width, height; same in legacy and Nodes 2.0)


def _widget_strings(n):
    """String widget values of a node. Looks at both ``widgets`` (by name; nodes whose type is known) and
    ``widgets_values`` (by position; the only source for custom nodes the server does not know).
    Returns [(widget name or None, value)]."""
    out = [(k, v) for k, v in (n.get("widgets") or {}).items() if isinstance(v, str)]
    wv = n.get("widgets_values")
    vals = wv.values() if isinstance(wv, dict) else (wv or [])
    seen = {v for _, v in out}
    out += [(None, v) for v in vals if isinstance(v, str) and v not in seen]
    return out


def collect_models(flat):
    """{name: {name, directory, url, size, nodes}} from properties.models and from model file names in widget values.
    ``nodes`` lists the (node type, widget name) pairs that hold the file name (used to find the folder)."""
    found = {}
    for n in flat["nodes"]:
        # Only properties.models entries whose file name is also a widget value of the node (the list can
        # contain unused models left over from a template)
        used = {_base(v) for _, v in _widget_strings(n)}
        for m in (n.get("properties") or {}).get("models") or []:
            if m.get("name") and _base(m["name"]) in used:
                found.setdefault(m["name"], {"name": m["name"], "directory": m.get("directory"),
                                             "url": m.get("url"), "size": None, "nodes": []})
        for k, v in _widget_strings(n):
            if v.lower().endswith(MODEL_EXT):
                e = found.setdefault(v, {"name": v, "directory": None, "url": None, "size": None, "nodes": []})
                e["nodes"].append((n.get("type"), k))
    return found


def _base(name):
    return _parts(name)[-1] if _parts(name) else name


def _get_json(server, path):
    try:
        with urllib.request.urlopen(server.rstrip("/") + path, timeout=20) as r:
            return json.load(r)
    except Exception:  # noqa: BLE001
        return None


class FolderFinder:
    """Look up the folder under ComfyUI/models for a model file name (only when a server is available).
    1. The folder whose /models/<folder> listing contains the file name.
    2. Otherwise, the folder whose listing equals the options (object_info) of the widget that holds the
       file name (empty listings are not compared).
    Folder names added by custom nodes (such as GGUF's unet_gguf) are mapped to the core folder that points
    to the same places (same path list in /internal/folder_paths, e.g. diffusion_models)."""

    def __init__(self, server, oi):
        self.server, self.oi = server, oi
        self.folders = _get_json(server, "/models") or []
        self.lists = {}
        self.paths = _get_json(server, "/internal/folder_paths") or {}

    def listing(self, folder):
        if folder not in self.lists:
            self.lists[folder] = _get_json(self.server, "/models/" + urllib.parse.quote(folder)) or []
        return self.lists[folder]

    def real(self, folder):
        mine = self.paths.get(folder)
        if not mine:
            return folder
        same = [k for k, v in self.paths.items() if set(v) == set(mine) and (k in self.folders or k == folder)]
        # Among names pointing to the same places, prefer one in DIR_ORDER (core folders, the model Note order); else keep it
        same.sort(key=lambda k: (DIR_ORDER.index(k) if k in DIR_ORDER else len(DIR_ORDER), k != folder, k))
        return same[0] if same else folder

    def options(self, ntype, widget):
        info = self.oi.get(ntype) or {}
        for sect in ("required", "optional"):
            for name, spec in ((info.get("input") or {}).get(sect) or {}).items():
                if widget is not None and name != widget:
                    continue
                if isinstance(spec, list) and spec and isinstance(spec[0], list):
                    yield spec[0]
                elif (isinstance(spec, list) and len(spec) > 1 and spec[0] == "COMBO"
                      and isinstance(spec[1], dict) and isinstance(spec[1].get("options"), list)):
                    yield spec[1]["options"]

    def find(self, m):
        hit = {self.real(f) for f in self.folders if m["name"] in self.listing(f)}
        if hit:
            # If several names point to the same places (clip_gguf and text_encoders, etc.), prefer one in DIR_ORDER
            return sorted(hit, key=lambda k: (DIR_ORDER.index(k) if k in DIR_ORDER else len(DIR_ORDER), k))[0]
        for ntype, widget in m.get("nodes") or []:
            for opts in self.options(ntype, widget):
                if not opts or not all(isinstance(x, str) for x in opts):
                    continue
                hit = [f for f in self.folders if set(self.listing(f)) == set(opts)]
                if len(hit) >= 1:
                    reals = {self.real(f) for f in hit}
                    if len(reals) == 1:
                        return reals.pop()
                # Options can include entries from outside the folder (VAELoader's taesd, etc.).
                # Take the largest folder whose whole listing is contained in the options
                sub = [f for f in self.folders if self.listing(f) and set(self.listing(f)) <= set(opts)]
                if sub:
                    best = max(len(self.listing(f)) for f in sub)
                    reals = {self.real(f) for f in sub if len(self.listing(f)) == best}
                    if len(reals) == 1:
                        return reals.pop()
        return None


# Folder order in the model Note (the order used in the example Notes; folders not listed come after, by name)
DIR_ORDER = ["checkpoints", "diffusion_models", "unet", "text_encoders", "clip", "clip_vision", "vae",
             "loras", "controlnet", "model_patches", "upscale_models", "latent_upscale_models"]


def _parts(name):
    return [x for x in name.replace("\\", "/").split("/") if x]


def _tree_lines(t, indent):
    out = []
    items = list(t.items())
    for k, (key, sub) in enumerate(items):
        last = k == len(items) - 1
        out.append(f"{indent}{'└──' if last else '├──'} {'📂' + key if sub is not None else key}")
        if sub is not None:
            out += _tree_lines(sub, indent + ("    " if last else "│   "))
    return out


def model_note_text(models):
    """Model Note text in the format of references/notes.md."""
    by_dir = {}
    for m in models:
        by_dir.setdefault(m["directory"] or "?", []).append(m)
    by_dir = dict(sorted(by_dir.items(), key=lambda kv: (DIR_ORDER.index(kv[0]) if kv[0] in DIR_ORDER
                                                         else len(DIR_ORDER), kv[0])))
    lines = ["## models", ""]
    for d, ms in by_dir.items():
        lines.append(f"- {d}")
        for m in ms:
            base = _parts(m["name"])[-1]
            label = f"[{base}]({m['url']})" if m.get("url") else base
            size = f" ({m['size']})" if m.get("size") else ""
            lines.append(f"  - {label}{size}")
    # Folder tree. Subfolders in a file name ("1.5/a.safetensors", "1.5\\a.safetensors") become nested entries
    tree = {}
    for d, ms in by_dir.items():
        top = tree
        for x in _parts(d) or [d]:    # a "/" in the folder name ("ultralytics/bbox") nests too
            top = top.setdefault(x + "/", {})
        for m in ms:
            t = top
            *sub, base = _parts(m["name"])
            for x in sub:
                t = t.setdefault(x + "/", {})
            t[base] = None
    lines += ["", "```text", "📂ComfyUI/", "└── 📂models/"]
    lines += _tree_lines(tree, "    ")
    lines.append("```")
    return "\n".join(lines)


# ---- MarkdownNote height estimate ----
# Matches the frontend's legacy rendering (tiptap, 10px Inter body, line-height normal; a 400-wide node has a
# 380-wide body). Height at which the body fits without scrolling = body height + 22 (DOM widget top/bottom margin).
# CJK lines use the line height of Windows' Meiryo (taller than Yu Gothic UI), erring on the side of no scroll bar.
# Widths follow from the node width nw (the offsets below are side margins, independent of the width).
MD_BODY = 20                # node width - body width
MD_PAD = 22                 # node height - body area height
MD_LIST_INDENT = 40         # indent per list level
MD_PRE = 22                 # body width - code block inner width (margin 5 + padding 5 + border 1, both sides)
MD_QUOTE = 58               # body width - blockquote inner width (left 10 + border 3 + padding 5, right 40)
MD_SIZE = {"p": 10, 1: 20, 2: 15, 3: 11.7, 4: 10, 5: 8.3, 6: 6.7}
_CLOSE = set("、。，．・：；？！）」』】〕〉》｝〟ゝゞーァィゥェォッャュョヮヵヶぁぃぅぇぉっゃゅょゎ々…‥"
             ".,:;!?)]}%")
_OPEN = set("（「『【〔〈《｛〝([{")
_ESCAPABLE = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _r(x):
    return int(x + 0.5)


def _line_h(size, wide=False, code=False, emoji=False):
    """Height of one line. Chrome rounds ascent and descent separately and adds them."""
    # Take the unrounded value (1.2109 x size, etc.) when larger (for environments that round differently)
    h = max(_r(0.96875 * size) + _r(0.2421875 * size), 1.2109375 * size)          # Inter
    if wide:
        h = max(h, _r(1.0601 * size) + _r(0.4399 * size), 1.5 * size)            # Meiryo
    if code:
        h += 2                                                 # inline code (monospace) makes the line taller
    if emoji:
        h = max(h, _r(0.96875 * size) + _r(0.2421875 * size) + 1)   # emoji (Segoe UI Emoji)
    return h


def _inline(s):
    """Strip inline Markdown formatting into [(char, is_bold, is_code)]."""
    out = []
    i, bold = 0, False
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s) and s[i + 1] in _ESCAPABLE:
            out.append((s[i + 1], bold, False))
            i += 2
            continue
        if c == "`":
            j = s.find("`", i + 1)
            if j > i:
                out += [(ch, False, True) for ch in s[i + 1:j]]
                i = j + 1
                continue
        if s.startswith("**", i):
            bold = not bold
            i += 2
            continue
        if c == "!" and s.startswith("![", i):
            j = s.find("](", i)
            k = s.find(")", j + 2) if j > 0 else -1
            if k > 0:
                i = k + 1
                continue
        if c == "[":
            j = s.find("](", i)
            k = s.find(")", j + 2) if j > 0 else -1
            if k > 0:
                out += [(ch, bold, False) for ch in s[i + 1:j]]
                i = k + 1
                continue
        if c == "*" and (i + 1 < len(s) and s[i + 1] not in " " or i > 0 and s[i - 1] not in " "):
            i += 1   # italic marker
            continue
        out.append((c, bold, False))
        i += 1
    return out


def _wrap(chars, width, size, bold=False, mono=False, code_pad=0):
    """Return, for each wrapped line, (has CJK, has inline code, has emoji).
    Breaks after a space, after "-", and before/after CJK characters (punctuation that cannot start a line
    stays with the previous character). A word longer than the width is cut.
    code_pad: sum of inline code's left and right padding (Vue), added to the width of the code's first char."""
    def w(k):
        ch, b, code = chars[k]
        pad = code_pad if code and (k == 0 or not chars[k - 1][2]) else 0
        return F.md_char_w(ch, size, bold or b, mono or code) + pad

    units, cur = [], []
    for k, (ch, b, code) in enumerate(chars):
        prev = chars[k - 1][0] if k else ""
        breakable = cur and (prev == " " or (prev == "-" and ch not in " -" and not ch.isdigit())
                             or ((F.is_wide(ch) or F.is_wide(prev)) and ch not in _CLOSE
                                 and prev not in _OPEN and ch != " "))
        if breakable:
            units.append(cur)
            cur = []
        cur.append(k)
    if cur:
        units.append(cur)

    lines, x, flags = [], 0.0, [False, False, False]

    def flag(k):
        ch, _, code = chars[k]
        flags[0] |= F.is_wide(ch)
        flags[1] |= code and not mono
        flags[2] |= F.is_emoji(ch)

    def newline():
        lines.append(tuple(flags))
        flags[:] = [False, False, False]

    for u in units:
        uw = sum(w(k) for k in u)
        tail = 0.0
        for k in reversed(u):
            if chars[k][0] != " ":
                break
            tail += w(k)
        if x > 0 and x + uw - tail > width:
            newline()
            x = 0.0
        if uw - tail > width:      # a word longer than the width: cut it
            for k in u:
                cw = w(k)
                if x > 0 and x + cw > width and chars[k][0] != " ":
                    newline()
                    x = 0.0
                x += cw
                flag(k)
            continue
        x += uw
        for k in u:
            flag(k)
    if x > 0 or not lines:
        newline()
    return lines


def _text_h(s, width, size=10, bold=False):
    return sum(_line_h(size, *f) for f in _wrap(_inline(s.strip()), width, size, bold))


_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])(\s+|$)(.*)$")
_FENCE_RE = re.compile(r"^\s{0,3}(```+|~~~+)")
_HR_RE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")


def _blocks(text):
    """Split Markdown into rough blocks. [(kind, content)]"""
    lines = text.replace("\t", "    ").split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        m = _FENCE_RE.match(ln)
        if m:
            fence, body = m.group(1), []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(fence[:3]):
                body.append(lines[i])
                i += 1
            out.append(("code", body))
            i += 1
            continue
        hm = re.match(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$", ln)
        if hm:
            out.append(("h", (len(hm.group(1)), hm.group(2))))
            i += 1
            continue
        if _HR_RE.match(ln):
            out.append(("hr", None))
            i += 1
            continue
        if ln.lstrip().startswith(">"):
            body = []
            while i < len(lines) and lines[i].strip() and lines[i].lstrip().startswith(">"):
                body.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append(("quote", " ".join(body)))
            continue
        if ln.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]) \
                and "-" in lines[i + 1]:
            rows = [ln]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.append(("table", [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]))
            continue
        if _LIST_RE.match(ln):
            items = []   # [(indent, text)]
            while i < len(lines):
                cur = lines[i]
                lm = _LIST_RE.match(cur)
                if lm:
                    items.append([len(lm.group(1)), lm.group(4)])
                elif cur.strip() and items and not _FENCE_RE.match(cur) and not cur.lstrip().startswith("#"):
                    items[-1][1] += " " + cur.strip()     # continuation line
                elif not cur.strip() and i + 1 < len(lines) and _LIST_RE.match(lines[i + 1]):
                    pass
                else:
                    break
                i += 1
            out.append(("list", items))
            continue
        body = []
        while i < len(lines) and lines[i].strip() and not (
                _FENCE_RE.match(lines[i]) or re.match(r"^\s{0,3}#{1,6}\s", lines[i]) or _HR_RE.match(lines[i])
                or lines[i].lstrip().startswith(">") or (body and _LIST_RE.match(lines[i]))):
            body.append(lines[i].strip())
            i += 1
        if not body:      # a line that matches nothing else
            body.append(ln.strip())
            i += 1
        out.append(("p", " ".join(body)))
    return out


def _list_tree(items):
    """Nest [(indent, text)] by indent. [[text, children]]"""
    def build(k, indent):
        tree = []
        while k < len(items) and items[k][0] >= indent:
            ind, txt = items[k]
            node = [txt, []]
            k += 1
            if k < len(items) and items[k][0] > ind:
                node[1], k = build(k, items[k][0])
            tree.append(node)
        return tree, k

    return build(0, items[0][0] if items else 0)[0]


def _legacy_list_h(tree, w):
    """List height (legacy). Each level is 40 narrower. 0 between items, 10 between an item's text and its nested list."""
    h = 0.0
    for txt, sub in tree:
        h += _text_h(txt, w - MD_LIST_INDENT) if txt.strip() else _line_h(10)
        if sub:
            h += 10 + _legacy_list_h(sub, w - MD_LIST_INDENT)
    return h


def _legacy_height(text, nw=NOTE_W):
    """Legacy (tiptap): node height at which the body of an nw-wide node fits without scrolling."""
    MD_W = nw - MD_BODY
    MD_PRE_W, MD_QUOTE_W = MD_W - MD_PRE, MD_W - MD_QUOTE
    y, prev_mb, last = 0.0, None, None
    for kind, v in _blocks(text):
        if kind == "p":
            mt = mb = 10
            h = _text_h(v, MD_W)
        elif kind == "h":
            size = MD_SIZE[v[0]]
            mt = mb = 0.67 * size
            h = _text_h(v[1], MD_W, size, bold=True)
        elif kind == "list":
            mt = mb = 10
            h = _legacy_list_h(_list_tree(v), MD_W)
        elif kind == "code":
            mt = mb = 5
            h = 12 + sum(_line_h(10, f[0]) for ln in (v or [""])
                         for f in _wrap([(c, False, False) for c in ln], MD_PRE_W, 10, mono=True))
        elif kind == "quote":
            mt = mb = 10
            h = _text_h(v, MD_QUOTE_W)
        elif kind == "hr":
            mt, mb, h = 5, 5, 2
        else:  # table
            mt = mb = 0
            ncol = max(len(r) for r in v)
            cw = MD_W / ncol - 11
            h = 1 + sum(11 + max(_text_h(c, cw) for c in r) for r in v)
        y += (0 if prev_mb is None else max(prev_mb, mt)) + h
        prev_mb, last = mb, kind
    if last is not None and last != "p":
        y += max(prev_mb, 10) + _line_h(10)    # when the last block is not a paragraph, the frontend adds an empty paragraph
    return math.ceil(y + MD_PAD)


# Nodes 2.0 (Vue) rendering: marked, 10px body, line-height 1.6 (16px), body width 376.
# Overflowing text makes the node grow instead of scrolling (overlapping the node below). Fits = body height + 18.
VUE_BODY = 24              # node width - body width
VUE_PAD = 18
VUE_LH = 16                # one body line (fixed line height, so the same for CJK)
VUE_CODE_LH = 18           # a line containing inline code (monospace with padding)
VUE_CODE_PAD = 12          # inline code left + right padding (0.375rem x 2)
VUE_SIZE = {1: 22 / 14 * 10, 2: 18 / 14 * 10, 3: 16 / 14 * 10, 4: 10, 5: 8.3, 6: 6.7}
VUE_LIST_INDENT = (32, 24)  # first level, second level and deeper


def _vue_text_h(s, width, size=10, bold=False, lh=None):
    return sum((lh or (VUE_CODE_LH if f[1] else VUE_LH))
               for f in _wrap(_inline(s.strip()), width, size, bold, code_pad=VUE_CODE_PAD))


def _vue_list_h(tree, w, depth=0):
    """List height (Vue). 8 between items (li margin), 0 between an item's text and its nested list."""
    w -= VUE_LIST_INDENT[min(depth, 1)]
    hs = []
    for txt, sub in tree:
        h = _vue_text_h(txt, w) if txt.strip() else VUE_LH
        if sub:
            h += _vue_list_h(sub, w, depth + 1)
        hs.append(h)
    return sum(hs) + 8 * (len(hs) - 1)


def _vue_height(text, nw=NOTE_W):
    """Nodes 2.0 (Vue): node height at which the body of an nw-wide node fits without the node growing."""
    VUE_W = nw - VUE_BODY
    y, prev_mb, last = 0.0, None, None
    for kind, v in _blocks(text):
        if kind == "p":
            mt, mb = 0, 5
            h = _vue_text_h(v, VUE_W)
        elif kind == "h":
            size = VUE_SIZE[v[0]]
            mt = mb = 0.67 * size
            h = _vue_text_h(v[1], VUE_W, size, bold=True, lh=1.2 * size)
        elif kind == "list":
            mt = mb = 8
            h = _vue_list_h(_list_tree(v), VUE_W)
        elif kind == "code":
            mt = mb = 16
            h = 32 + VUE_LH * max(1, len(v))    # no wrapping (long lines overflow sideways)
        elif kind == "quote":
            mt, mb = 0, 5
            h = _vue_text_h(v, VUE_W - 11)
        elif kind == "hr":
            mt, mb, h = 10, 10, 1
        else:  # table
            mt = mb = 0
            ncol = max(len(r) for r in v)
            cw = VUE_W / ncol - 16
            h = 2 + sum(16 + max(_vue_text_h(c, cw) for c in r) for r in v)
        y += (0 if prev_mb is None else max(prev_mb, mt)) + h
        prev_mb, last = mb, kind
    if last not in (None, "p"):
        y += prev_mb             # a final paragraph has no bottom margin; other blocks count theirs (no-scroll side)
    return math.ceil(y + VUE_PAD)


def note_height(text, nw=NOTE_W):
    """Height at which a MarkdownNote (width nw) fits its body in both legacy and Nodes 2.0, without scrolling or growing."""
    return max(_legacy_height(text, nw), _vue_height(text, nw))


