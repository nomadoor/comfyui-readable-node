"""Build the report page: one self-contained HTML file that steps through what was done on the canvas.

The canvas keeps, for every command, the state before it (``<name>.hist/``) and the command text (``history``).
canvas.py turns them into data (``report_page``): for each canvas the drawing of every state, the check problems at
that point, and the words of each command with the names of the nodes they mention. This module writes the sentences
(Japanese for ja, English for every other language code) and the page: the nodes drawn on one <canvas> as the
ComfyUI canvas draws them (title, slots, widgets, wires, groups), a timeline on which the nodes move smoothly from one step to the next, a switch to the
original workflow, and a panel that says what each step did and which problems it made or solved.
No external scripts: everything is inline. The Latin font is inside the page; Japanese text uses Zen Kaku Gothic New
from Google Fonts when online, and the machine's font otherwise.

``build(canvases, original, lang)`` returns the HTML text.
"""

import base64
import html
import json
import re
from pathlib import Path

LANGS = ("en", "ja")   # the languages the page's own sentences are written in; any other code gets English

# wire colours of the frontend's dark palette (the same as render.py)
LINK_COLORS = {
    "MODEL": "#B39DDB", "CLIP": "#FFD500", "VAE": "#FF6E6E", "CONDITIONING": "#FFA931", "LATENT": "#FF9CF9",
    "IMAGE": "#64B5F6", "MASK": "#81C784", "CONTROL_NET": "#6EE7B7", "CLIP_VISION": "#A8DADC",
    "CLIP_VISION_OUTPUT": "#ad7452", "NOISE": "#B0B0B0", "GUIDER": "#66FFFF", "SAMPLER": "#ECB4B4",
    "SIGMAS": "#CDFFCD", "STYLE_MODEL": "#C2FFAE", "TAESD": "#DCC274", "INT": "#8fc3c3", "FLOAT": "#aaee88",
    "STRING": "#99bb88", "BOOLEAN": "#c9a0dc", "AUDIO": "#ea9999", "VIDEO": "#7fb2e5",
}

# the page's parts: always English
CHROME = {
    "title": "Readable Node report", "brand": "ComfyUI Readable Node", "theme": {"system": "System", "light": "Light", "dark": "Dark"},
    "original": "Original", "rebuilt": "Rebuilt", "compare": "Compare with the original workflow (O)",
    "walk": "Walkthrough", "walk_title": "Walk through the finished workflow part by part (W)",
    "prev_part": "Previous part", "next_part": "Next part", "walk_whole": "The whole workflow (no part chosen)",
    "prev": "Previous step", "play": "Play", "pause": "Pause", "next": "Next step",
    "speed": "Speed", "step": "Step", "zoom_in": "Zoom in", "zoom_out": "Zoom out", "fit": "Fit",
    "follow": "Follow changes", "problems": "problems",
    "moved": "moved", "added": "added", "changed": "changed", "removed": "removed",
    "legend": "rebuilt / original", "legend_one": "rebuilt", "unplaced_title": "Nodes not placed yet",
    "help_title": "Keys and mouse",
    "help": [["← →", "previous / next step"], ["Space", "play / pause"], ["Home End", "first / last step"], ["O", "original / rebuilt"], ["W", "walkthrough on / off (← → move by part, Esc the whole workflow)"],
             ["drag the bar", "go to a step"], ["drag", "move the view"], ["wheel, pinch", "zoom"], ["0  F", "fit"],
             ["click a problem", "show its nodes"], ["Esc", "clear the selected problem"]],
    "empty": "Nothing is placed on the canvas yet.",
    "counts": {"overlaps": "overlaps", "wires behind nodes": "wires behind nodes", "crossings": "crossings",
               "non-horizontal wires": "non-horizontal wires", "unplaced": "unplaced",
               "backward wires that cannot be kept": "backward wires to fix"},
}

# the side panel: in the user's language
UI = {
    "en": {
        "original_note": "The workflow as its author saved it, in the author's positions. Press O or Rebuilt to go back.",
        "original_note_api": "The original was in API format, which has no positions. It is shown as ComfyUI places it when it opens the file. Press O or Rebuilt to go back.",
        "appeared": "New at this step", "solved": "Solved at this step", "all_problems": "All problems at this step",
        "details": "Details", "command": "Command", "commands": "Commands",
        "keys_note": {"moved": "position changed", "added": "on the canvas for the first time", "changed": "size or contents changed", "removed": "gone at this step (shown faint)", "behind": "the dashed wire runs behind the node in the red dashed outline"},
        "units": {"moved": "moved", "added": "placed", "changed": "changed", "removed": "removed", "behind": "behind"},
        "show_all": "Show all", "show_less": "Show less",
        "empty": "Nothing is placed on the canvas yet.",
        "counts": CHROME["counts"],
    },
    "ja": {
        "original_note": "作者が保存したままの workflow です（位置も作者のもの）。O か「組み直し」で戻ります。",
        "original_note_api": "元は API 形式で、位置がありません。ComfyUI がこのファイルを開いたときと同じ並べ方で表示しています。O か「組み直し」で戻ります。",
        "appeared": "この手で出た問題", "solved": "この手で消えた問題", "all_problems": "この時点の問題すべて",
        "details": "詳しく", "command": "命令", "commands": "命令",
        "keys_note": {"moved": "位置が変わった", "added": "この手で初めて置いた", "changed": "大きさや中身が変わった", "removed": "この手でなくなった（薄く表示）", "behind": "点線の線が、赤い点線で囲んだノードの裏を通っている"},
        "units": {"moved": "動かした", "added": "置いた", "changed": "変えた", "removed": "消した", "behind": "裏を通る"},
        "show_all": "すべて見る", "show_less": "たたむ",
        "empty": "キャンバスにはまだ何も置かれていません。",
        "counts": {"overlaps": "重なり", "wires behind nodes": "ノードの裏を通る線", "crossings": "交差",
                   "non-horizontal wires": "水平でない線", "unplaced": "未配置",
                   "backward wires that cannot be kept": "直すべき逆向きの線"},
    },
}

COLOR_JA = {"red": "赤", "brown": "茶", "green": "緑", "blue": "青", "pale_blue": "水色", "cyan": "シアン",
            "purple": "紫", "yellow": "黄", "black": "黒", "none": "なし"}


def _esc(s):
    """A label inside a [[...]] reference (the page splits references on | and ]])."""
    return str(s).replace("|", "¦").replace("]]", "] ]")


class Say:
    """Sentences about one command. References to nodes are written [[n:id|name]] (several: [[m:id,id|label]]);
    the page turns them into chips that point at the nodes."""

    def __init__(self, lang, x=None):
        self.ja = lang == "ja"
        self.x = x or {"names": {}, "before": {}, "blocks": {}, "groups": []}

    def L(self, en, ja):
        return ja if self.ja else en

    def node(self, i, before=False, slot=None):
        names = self.x.get("before" if before else "names") or {}
        nm = names.get(i) or (self.x.get("names") or {}).get(i)
        if nm is None:
            return f"{i}.{slot}" if slot else str(i)
        if nm == "Reroute":
            slot = None   # a Reroute has one input and one output; their names say nothing
        return f"[[n:{i}|{_esc(nm)}{' · ' + _esc(slot) if slot else ''}]]"

    def unit(self, tok):
        blocks = self.x.get("blocks") or {}
        if tok in blocks and tok not in (self.x.get("names") or {}):
            return f"[[m:{','.join(blocks[tok])}|{_esc(self.L('block ', 'ブロック ') + tok)}]]"
        return self.node(tok)

    def port(self, tok):
        if "." not in tok:
            return self.unit(tok)
        i, p = tok.split(".", 1)
        return self.node(i, slot=p)

    def join(self, items):
        items = list(items)
        if not items:
            return ""
        if self.ja:
            return "、".join(items)
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]

    def many(self, toks, limit=4, fn=None, d=None):
        fn = fn or self.unit
        toks = list(toks)
        parts = [fn(t) for t in toks[:limit]]
        more = len(toks) - limit
        if more > 0 and d is not None:
            d += [fn(t) for t in toks]
            return ("、".join(parts) + f" ほか {more} 個") if self.ja else (", ".join(parts) + f" and {more} more")
        return self.join(parts)

    def wire(self, a, b):
        return f"{self.port(a)} → {self.port(b)}"


def _opts(args, keyed=(), flags=()):
    pos, opt = [], {}
    k = 0
    while k < len(args):
        a = args[k]
        if a in keyed and k + 1 < len(args):
            opt[a] = args[k + 1]
            k += 2
            continue
        if a in flags:
            opt[a] = True
        else:
            pos.append(a)
        k += 1
    return pos, opt


def _gap(S, opt):
    return S.L(f", gap {opt['gap']} px", f"、間隔 {opt['gap']} px") if "gap" in opt else ""


def explain(x, lang):
    """{"s": one sentence, "d": details} for one command."""
    S = Say(lang, x)
    toks = x.get("toks") or []
    if not toks:
        return {"s": "", "d": []}
    cmd, a = toks[0], toks[1:]
    d = []
    fn = _EXPLAIN.get(cmd)
    try:
        s = fn(S, a, x, d) if fn else None
    except (IndexError, KeyError, ValueError):
        s = None
    if s is None:
        s = S.L("Ran ", "命令を実行しました: ") + " ".join(toks)
    return {"s": s, "d": d}


def _x_put(S, a, x, d):
    unit, how = a[0], a[1]
    if how == "origin":
        return S.L(f"Placed {S.unit(unit)} at the top-left (0, 0)", f"{S.unit(unit)} を左上 (0, 0) に置きました")
    pos, opt = _opts(a[2:], keyed=("gap",))
    ref = pos[0]
    align = pos[1] if len(pos) > 1 else None
    u, r = S.unit(unit), S.unit(ref)
    where_en = {"right": "to the right of", "left": "to the left of", "below": "below", "above": "above"}[how]
    where_ja = {"right": "の右", "left": "の左", "below": "の下", "above": "の上"}[how]
    al_en = {"top": ", tops aligned", "bottom": ", bottoms aligned", "middle": ", centred vertically",
             "wire": " and made the wire between them horizontal", "left": ", left edges aligned",
             "right": ", right edges aligned", "center": ", centred horizontally"}
    al_ja = {"top": "上端をそろえて", "bottom": "下端をそろえて", "middle": "上下の真ん中をそろえて",
             "wire": "間の線が水平になる高さで", "left": "左端をそろえて", "right": "右端をそろえて", "center": "左右の真ん中をそろえて"}
    if align is None:
        # put right|left without a word: the canvas made the wire horizontal when the two are wired, otherwise aligned the tops
        align = ("wire" if x.get("wired") else "top") if how in ("right", "left") else "left"
    if S.ja:
        g = f"（間隔 {opt['gap']} px）" if "gap" in opt else ""
        return f"{u} を {r} {where_ja}に、{al_ja.get(align, '')}置きました{g}"
    return f"Placed {u} {where_en} {r}{al_en.get(align, '')}{_gap(S, opt)}"


def _x_row(S, a, x, d):
    pos, opt = _opts(a, keyed=("right", "gap"))
    units = [p for p in pos if p not in ("top", "wire")]
    # without top or wire, the canvas makes the wire horizontal between wired neighbours and aligns the tops of the others
    w = x.get("wired")
    wire = "wire" in pos or (isinstance(w, list) and w and all(w))
    some = "top" not in pos and not wire and isinstance(w, list) and any(w)
    start = (S.L(f", starting to the right of {S.unit(opt['right'])}", f"（{S.unit(opt['right'])} の右から）")) if "right" in opt else ""
    if S.ja:
        tail = "。線は水平にしました" if wire else ("。線でつながる隣どうしは線を水平に、ほかは上端をそろえました" if some else "")
        return f"{S.many(units, 4, d=d)} を左から右へ一列に並べました{start}{tail}"
    tail = ", with horizontal wires" if wire else (", wires horizontal between wired neighbours and tops aligned elsewhere" if some else "")
    return f"Lined up {S.many(units, 4, d=d)} in one row from left to right{start}{tail}"


def _x_stack(S, a, x, d):
    pos, opt = _opts(a, keyed=("below", "gap"))
    units = [p for p in pos if p not in ("left", "right")]
    side = "right" if "right" in pos else "left"
    start = S.L(f", starting below {S.unit(opt['below'])}", f"（{S.unit(opt['below'])} の下から）") if "below" in opt else ""
    if S.ja:
        return f"{S.many(units, 4, d=d)} を上から下へ一列に積みました（{'右端' if side == 'right' else '左端'}をそろえて）{start}"
    return f"Stacked {S.many(units, 4, d=d)} in one column from top to bottom, {side} edges aligned{start}"


def _x_align(S, a, x, d):
    edge, units = a[0], a[1:]
    en = {"top": "top edges", "bottom": "bottom edges", "left": "left edges", "right": "right edges",
          "middle": "vertical centres", "center": "horizontal centres"}
    ja = {"top": "上端", "bottom": "下端", "left": "左端", "right": "右端", "middle": "上下の真ん中", "center": "左右の真ん中"}
    if S.ja:
        return f"{S.many(units[1:])} の{ja[edge]}を {S.unit(units[0])} にそろえました"
    return f"Aligned the {en[edge]} of {S.many(units[1:])} to {S.unit(units[0])}"


def _x_inputs(S, a, x, d):
    return S.L(f"Put the nodes that feed {S.node(a[0])} in one right-aligned column on its left",
               f"{S.node(a[0])} につながるノードを、その左に右端をそろえて一列に置きました")


def _x_shape(S, a, x, d):
    pos, opt = _opts(a, keyed=("right", "below", "left", "above", "gap"))
    where = next((k for k in ("right", "below", "left", "above") if k in opt), None)
    w_en = f", {where} of {S.unit(opt[where])}" if where else ""
    w_ja = f"（{S.unit(opt[where])} の{ {'right': '右', 'left': '左', 'below': '下', 'above': '上'}[where]}に）" if where else ""
    return S.L(f"Laid out {S.unit(pos[1])} in the same shape as {S.unit(pos[0])}{w_en}",
               f"{S.unit(pos[1])} を {S.unit(pos[0])} と同じ形に並べました{w_ja}")


def _x_level(S, a, x, d):
    pos, opt = _opts(a, keyed=("move",))
    mv = opt.get("move") or pos[1].split(".", 1)[0]
    return S.L(f"Moved {S.unit(mv)} so the wire {S.wire(pos[0], pos[1])} is horizontal",
               f"線 {S.wire(pos[0], pos[1])} が水平になるように {S.unit(mv)} を動かしました")


def _x_width(S, a, x, d):
    return S.L(f"Gave {S.many(a)} the same width (the widest)", f"{S.many(a)} の幅を、いちばん広いものにそろえました")


def _x_move(S, a, x, d):
    units, dx, dy = a[:-2], a[-2], a[-1]
    return S.L(f"Moved {S.many(units)} by ({dx}, {dy})", f"{S.many(units)} を ({dx}, {dy}) ずらしました")


def _x_gap(S, a, x, d):
    hv = a[3] if len(a) > 3 else "h"
    if S.ja:
        return f"{S.unit(a[0])} と {S.unit(a[1])} の{'横' if hv == 'h' else '縦'}の間隔を {a[2]} px にしました"
    return f"Set the {'horizontal' if hv == 'h' else 'vertical'} gap between {S.unit(a[0])} and {S.unit(a[1])} to {a[2]} px"


def _x_block(S, a, x, d):
    members = [m for t in a[1:] for m in (x.get("blocks", {}).get(t) if t in x.get("blocks", {}) and t not in x.get("names", {}) else [t])]
    return S.L(f"Made block “{a[0]}” of {S.many(a[1:])} (they move together)",
               f"{S.many(a[1:])} をブロック「{a[0]}」にまとめました（一緒に動きます）") if members else None


def _x_unblock(S, a, x, d):
    return S.L(f"Removed block “{a[0]}”", f"ブロック「{a[0]}」をやめました")


def _x_group(S, a, x, d):
    pos, opt = _opts(a, keyed=("color",))
    col = opt.get("color")
    c = S.L(f" in {col}", f"（色 {col}）") if col else ""
    return S.L(f"Made group “{pos[0]}” around {S.many(pos[1:])}{c}", f"{S.many(pos[1:])} を囲むグループ「{pos[0]}」を作りました{c}")


def _x_ungroup(S, a, x, d):
    return S.L(f"Removed group “{a[0]}”", f"グループ「{a[0]}」をやめました")


def _x_group_align(S, a, x, d):
    q = [S.L(f"“{t}”", f"「{t}」") for t in a]
    return S.L(f"Aligned the top and bottom edges of groups {S.join(q)}", f"グループ {S.join(q)} の上端と下端をそろえました")


def _x_color(S, a, x, d):
    c, ids = a[0], a[1:]
    if c == "none":
        return S.L(f"Removed the colour of {S.many(ids)}", f"{S.many(ids)} の色を外しました")
    return S.L(f"Coloured {S.many(ids)} {c.replace('_', ' ')}", f"{S.many(ids)} を{COLOR_JA.get(c, c)}にしました")


def _x_rail(S, a, x, d):
    k = a.index("to")
    head, targets = a[:k], a[k + 1:]
    spec = head[1]
    h_en = {"above": f"above {S.unit(head[2])}" if len(head) > 2 else "", "below": f"below {S.unit(head[2])}" if len(head) > 2 else "",
            "level": f"at the height of {S.port(head[2])}" if len(head) > 2 else "", "out": "at the height of the output"}
    h_ja = {"above": f"{S.unit(head[2])} の上" if len(head) > 2 else "", "below": f"{S.unit(head[2])} の下" if len(head) > 2 else "",
            "level": f"{S.port(head[2])} の高さ" if len(head) > 2 else "", "out": "出力と同じ高さ"}
    if S.ja:
        return f"{S.port(head[0])} を、{h_ja.get(spec, spec)}を通るレール（Reroute の列）で {S.many(targets, 4, S.port)} へ運びました"
    return f"Carried {S.port(head[0])} to {S.many(targets, 4, S.port)} along a rail (a line of Reroutes) {h_en.get(spec, spec)}"


def _x_note(S, a, x, d):
    pos, opt = _opts(a, keyed=("gap", "width"))
    f, how, ref = pos[0], pos[1], pos[2]
    nid = f.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
    w_ja = {"right": "右", "left": "左", "below": "下", "above": "上"}.get(how, how)
    return S.L(f"Placed the Note {S.node(nid)} {how if how in ('below', 'above') else 'to the ' + how + ' of'} {S.unit(ref)}",
               f"Note {S.node(nid)} を {S.unit(ref)} の{w_ja}に置きました")


def _x_copy(S, a, x, d):
    if len(a) > 2:
        d += [S.node(t) for t in a]
        return S.L(f"Copied {len(a)} nodes from the original workflow", f"元の workflow からノードを {len(a)} 個写しました")
    return S.L(f"Copied {S.many(a)} from the original workflow", f"元の workflow から {S.many(a)} を写しました")


def _x_add(S, a, x, d):
    t = a[0]
    if len(a) > 1:
        return S.L(f"Added a new {t} node ({S.node(a[1])})", f"新しい {t} ノードを足しました（{S.node(a[1])}）")
    return S.L(f"Added a new {t} node", f"新しい {t} ノードを足しました")


def _x_set(S, a, x, d):
    vals = []
    for kv in a[1:]:
        k, _, v = kv.partition("=")
        v = v if len(v) <= 60 else v[:60] + "…"
        vals.append(f"{k} = {v}")
    return S.L(f"Set values on {S.node(a[0])}: {'; '.join(vals)}", f"{S.node(a[0])} の値を変えました: {'、'.join(vals)}")


def _x_link(S, a, x, d):
    pairs = [(a[i], a[i + 1]) for i in range(0, len(a) - 1, 2)]
    if len(pairs) == 1:
        return S.L(f"Connected {S.wire(*pairs[0])}", f"{S.wire(*pairs[0])} をつなぎました")
    d += [S.wire(p, q) for p, q in pairs]
    return S.L(f"Connected {len(pairs)} wires", f"線を {len(pairs)} 本つなぎました")


def _x_unlink(S, a, x, d):
    return S.L(f"Disconnected {S.many(a, 4, S.port)}", f"{S.many(a, 4, S.port)} の線を外しました")


def _x_rm(S, a, x, d):
    who = S.many(a, 4, lambda t: S.node(t, before=True), d)
    return S.L(f"Removed {who}", f"{who} を消しました")


def _x_mode(S, a, x, d):
    m, ids = a[0], a[1:]
    if S.ja:
        return {"on": f"{S.many(ids)} を有効に戻しました", "bypass": f"{S.many(ids)} をバイパスにしました（入力をそのまま通します）",
                "mute": f"{S.many(ids)} をミュートにしました（実行しません）"}.get(m)
    return {"on": f"Turned {S.many(ids)} back on", "bypass": f"Bypassed {S.many(ids)} (passes its input through)",
            "mute": f"Muted {S.many(ids)} (does not run)"}.get(m)


def _x_title(S, a, x, d):
    t = " ".join(a[1:])
    return S.L(f"Renamed {S.node(a[0], before=True)} to “{t}”", f"{S.node(a[0], before=True)} の題名を「{t}」にしました")


def _x_layout(S, a, x, d):
    f = a[0].replace("\\", "/").rsplit("/", 1)[-1]
    n = x.get("lines")
    for ln in x.get("notes") or []:
        d.append(note_text(ln, S))
    if n is not None:
        return S.L(f"Applied the layout plan {f} ({n} lines) and placed everything again",
                   f"配置の計画 {f}（{n} 行）を当てて、全部を置き直しました")
    return S.L(f"Applied the layout plan {f} and placed everything again", f"配置の計画 {f} を当てて、全部を置き直しました")


def _x_walk(S, a, x, d):
    return S.L("Wrote the walkthrough (see Walkthrough)", "解説を書きました（Walkthrough で見られます）")


def _x_new(S, a, x, d):
    if len(a) >= 3 and a[1] == "from":
        return S.L(f"Started this canvas as a copy of canvas “{a[2]}”", f"キャンバス「{a[2]}」の写しから始めました")
    return S.L(f"Made canvas “{a[0]}”", f"キャンバス「{a[0]}」を作りました")


_EXPLAIN = {"put": _x_put, "row": _x_row, "stack": _x_stack, "align": _x_align, "inputs": _x_inputs, "shape": _x_shape,
            "level": _x_level, "width": _x_width, "move": _x_move, "gap": _x_gap, "block": _x_block, "unblock": _x_unblock,
            "group": _x_group, "ungroup": _x_ungroup, "group-align": _x_group_align, "color": _x_color, "rail": _x_rail,
            "note": _x_note, "copy": _x_copy, "add": _x_add, "set": _x_set, "link": _x_link, "unlink": _x_unlink, "rm": _x_rm,
            "mode": _x_mode, "title": _x_title, "layout": _x_layout, "new": _x_new, "walk": _x_walk}

BUILD_CMDS = {"copy": ("copied {n} nodes", "ノードを {n} 個写し"), "add": ("added {n} new nodes", "新しいノードを {n} 個足し"),
              "set": ("set values {n} times", "値を {n} 回変え"), "link": ("connected {n} wires", "線を {n} 本つなぎ"),
              "unlink": ("disconnected {n} wires", "線を {n} 本外し"), "rm": ("removed {n} nodes", "ノードを {n} 個消し"),
              "title": ("named {n} nodes", "ノード {n} 個に題名を付け"), "mode": ("changed the mode of {n} nodes", "ノード {n} 個の mode を変え")}


def build_summary(xs, lang):
    """One sentence for several commands that did not change the drawing (building the graph before it is placed)."""
    S = Say(lang)
    count = {}
    for x in xs:
        toks = x.get("toks") or [""]
        c = toks[0]
        n = {"copy": len(toks) - 1, "add": 1, "set": 1, "link": (len(toks) - 1) // 2, "unlink": len(toks) - 1,
             "rm": len(toks) - 1, "title": 1, "mode": len(toks) - 2}.get(c, 1)
        count[c] = count.get(c, 0) + n
    parts = []
    for c, (en, ja) in BUILD_CMDS.items():
        if count.get(c):
            parts.append((ja if S.ja else en).format(n=count[c]))
    other = sum(v for c, v in count.items() if c not in BUILD_CMDS)
    if S.ja:
        head = f"{len(xs)} 個の命令でノードと線を組み立てました（絵の上ではまだ何も動いていません）"
        return head + ("。" + "、".join(parts) + "ました" if parts else "") + (f"。ほかの命令 {other} 個" if other else "")
    head = f"Built nodes and wires with {len(xs)} commands (nothing moved on the drawing yet)"
    return head + (": " + ", ".join(parts) if parts else "") + (f"; {other} other commands" if other else "")


# ---- problems and notes in plain words. Each pattern is one kind of check line (canvas.py's check rules).

_W = r"([\w:~]+)\.(.*?) → ([\w:~]+)\.([^\s,;()]*)"


def _wire_m(S, m, k=1):
    return S.wire(f"{m.group(k)}.{m.group(k + 1)}", f"{m.group(k + 2)}.{m.group(k + 3)}")


def _ids(S, s, limit=6):
    return S.many(s.split(), limit, S.node)


PROBLEMS = [
    ("unplaced", r"^unplaced (\d+): (.*)$",
     lambda S, m: S.L(f"{m.group(1)} nodes are not placed yet: {_ids(S, m.group(2))}", f"まだ置いていないノードが {m.group(1)} 個あります: {_ids(S, m.group(2))}")),
    ("overlap", r"^overlap: (\S+) and (\S+)$",
     lambda S, m: S.L(f"{S.node(m.group(1))} and {S.node(m.group(2))} overlap", f"{S.node(m.group(1))} と {S.node(m.group(2))} が重なっています")),
    ("narrow", r"^narrow gap \((horizontal|vertical) (\d+)px, min (\d+)\): (\S+) and (\S+)$",
     lambda S, m: S.L(f"{S.node(m.group(4))} and {S.node(m.group(5))} are too close ({m.group(1)} gap {m.group(2)} px, at least {m.group(3)})",
                      f"{S.node(m.group(4))} と {S.node(m.group(5))} の間が狭すぎます（{'横' if m.group(1) == 'horizontal' else '縦'} {m.group(2)} px、最低 {m.group(3)} px）")),
    ("hidden", r"^wire behind a node: " + _W + r" \((\S+)\) passes behind (\S+)$",
     lambda S, m: S.L(f"The {m.group(5)} wire {_wire_m(S, m)} passes behind {S.node(m.group(6))}",
                      f"{m.group(5)} の線 {_wire_m(S, m)} が {S.node(m.group(6))} の裏を通っています")),
    ("cross", r"^crossing \(product wire\): " + _W + " and " + _W + "$",
     lambda S, m: S.L(f"Wires cross: {_wire_m(S, m)} and {_wire_m(S, m, 5)}", f"線が交差しています: {_wire_m(S, m)} と {_wire_m(S, m, 5)}")),
    ("cross", r"^crossings between tool wires: (\d+)",
     lambda S, m: S.L(f"{m.group(1)} crossings between tool wires (VAE, CLIP, values…; reduce them if possible)",
                      f"道具の線（VAE、CLIP、値など）どうしの交差が {m.group(1)} か所あります（できれば減らす）")),
    ("tilt", r"^non-horizontal wire \((\S+), input at ([+-]?\d+)px\): " + _W + "$",
     lambda S, m: S.L(f"The {m.group(1)} wire {_wire_m(S, m, 3)} is not horizontal ({m.group(2)} px)",
                      f"{m.group(1)} の線 {_wire_m(S, m, 3)} が水平ではありません（{m.group(2)} px）")),
    ("back", r"^backward wire that may be allowed .*: " + _W + "$",
     lambda S, m: S.L(f"The wire {_wire_m(S, m)} runs backwards (may be allowed)", f"線 {_wire_m(S, m)} が逆向きです（許される場合があります）")),
    ("back", r"^backward wire \(cannot be kept.*\): " + _W + "$",
     lambda S, m: S.L(f"The wire {_wire_m(S, m)} runs backwards (must be fixed)", f"線 {_wire_m(S, m)} が逆向きです（直す必要があります）")),
    ("align", r"^(\S+) \S+: right edges of the sources wired directly into it are not aligned",
     lambda S, m: S.L(f"The nodes feeding {S.node(m.group(1))} are not aligned on their right edges",
                      f"{S.node(m.group(1))} につながるノードの右端がそろっていません")),
    ("space", r"^empty band across everything \((\d+)px tall, min (\d+)\)",
     lambda S, m: S.L(f"An empty band {m.group(1)} px tall runs across the whole canvas (more than {m.group(2)})",
                      f"全体を横切る {m.group(1)} px の空きがあります（{m.group(2)} px より広い）")),
    ("align", r"^stacked nodes differ in width by (\d+)px .*: (\S+) and (\S+)$",
     lambda S, m: S.L(f"{S.node(m.group(2))} and {S.node(m.group(3))} are stacked but differ in width by {m.group(1)} px",
                      f"縦に並んだ {S.node(m.group(2))} と {S.node(m.group(3))} の幅が {m.group(1)} px 違います")),
    ("align", r"^value nodes side by side have unaligned tops \((\d+)px\): (\S+) and (\S+)$",
     lambda S, m: S.L(f"The value nodes {S.node(m.group(2))} and {S.node(m.group(3))} side by side have tops {m.group(1)} px apart",
                      f"横に並んだ値のノード {S.node(m.group(2))} と {S.node(m.group(3))} の上端が {m.group(1)} px ずれています")),
    ("order", r"^(vae|clip) loader (\S+) is above the model loader (\S+):",
     lambda S, m: S.L(f"{S.node(m.group(2))} sits above the model loader {S.node(m.group(3))} (loaders go model first, then vae and clip)",
                      f"{S.node(m.group(2))} が model の loader {S.node(m.group(3))} より上にあります（loader は上から model、その下に vae と clip）")),
    ("order", r"^vae loader (\S+) is used only by VAE Decode and sits below the sampler (\S+):",
     lambda S, m: S.L(f"{S.node(m.group(1))} is used only by VAE Decode but sits below the sampler {S.node(m.group(2))}",
                      f"VAE Decode にだけ使う {S.node(m.group(1))} が、サンプラー {S.node(m.group(2))} より下にあります")),
    ("space", r"^(\S+) is directly below (\S+) \((sampler|image|value-sized)\), which grows in ComfyUI",
     lambda S, m: S.L(f"{S.node(m.group(1))} is directly below {S.node(m.group(2))}, which grows in ComfyUI",
                      f"{S.node(m.group(1))} が、ComfyUI で伸びる {S.node(m.group(2))} の真下にあります")),
    ("order", r"^(\S+) is above its source (\S+) .*: (\S+)$",
     lambda S, m: S.L(f"{S.node(m.group(3))} sits above its source {S.node(m.group(2))}", f"{S.node(m.group(3))} が入力元 {S.node(m.group(2))} より上にあります")),
    ("space", r"^gap inside a column \((\d+)px tall, min (\d+)\): nothing between (\S+) and (\S+)$",
     lambda S, m: S.L(f"An empty {m.group(1)} px gap inside a column, between {S.node(m.group(3))} and {S.node(m.group(4))}",
                      f"列の中で {S.node(m.group(3))} と {S.node(m.group(4))} の間が {m.group(1)} px 空いています")),
    ("space", r"^wide gap to a wired neighbour \((\d+)px, standard gap (\d+)\): (\S+) → (\S+)$",
     lambda S, m: S.L(f"{S.node(m.group(3))} and its wired neighbour {S.node(m.group(4))} are {m.group(1)} px apart (standard {m.group(2)})",
                      f"つながった隣どうしの {S.node(m.group(3))} と {S.node(m.group(4))} が {m.group(1)} px 離れています（標準 {m.group(2)} px）")),
    ("reroute", r"^consecutive Reroutes .*: (\S+) → (\S+)$",
     lambda S, m: S.L(f"Two Reroutes in a row ({S.node(m.group(1))} → {S.node(m.group(2))}); one is enough",
                      f"Reroute が二つ続いています（{S.node(m.group(1))} → {S.node(m.group(2))}）。一つで足ります")),
    ("align", r"^model Note top edge is not aligned .*: (\S+)$",
     lambda S, m: S.L(f"The model Note {S.node(m.group(1))} is not level with the top of the workflow",
                      f"モデルの Note {S.node(m.group(1))} の上端が、workflow 全体の上端とそろっていません")),
    ("space", r"^uneven spacing in a row \((.*): gaps (.*)\)$",
     lambda S, m: S.L(f"Uneven gaps in the row {S.many(m.group(1).split(' → '), 4, S.node)} ({m.group(2)} px)",
                      f"一列の {S.many(m.group(1).split(' → '), 4, S.node)} の間隔がそろっていません（{m.group(2)} px）")),
    ("reroute", r"^Reroute connected to nothing: (\S+)$",
     lambda S, m: S.L(f"{S.node(m.group(1))} is connected to nothing", f"{S.node(m.group(1))} が何にもつながっていません")),
    ("reroute", r"^Reroute doing nothing \(a direct wire from (\S+) .*\): (\S+)$",
     lambda S, m: S.L(f"{S.node(m.group(2))} does nothing: a direct wire from {S.node(m.group(1))} would be horizontal and clear",
                      f"{S.node(m.group(2))} は要りません: {S.node(m.group(1))} からじかにつないでも水平で、何の裏も通りません")),
    ("reroute", r"^rail needs no raising Reroute \((\S+)\) if drawn at the output height: output of (\S+)",
     lambda S, m: S.L(f"The rail from {S.node(m.group(2))} needs no raising Reroute ({S.node(m.group(1))}) at the output height",
                      f"{S.node(m.group(2))} からのレールは、出力の高さで引けば持ち上げの Reroute（{S.node(m.group(1))}）が要りません")),
    ("reroute", r"^rail with a single target.*: (\S+) → ([\w:~]+)\.(\S+)$",
     lambda S, m: S.L(f"The rail from {S.node(m.group(1))} has one target ({S.port(m.group(2) + '.' + m.group(3))}); a direct wire is clear",
                      f"{S.node(m.group(1))} からのレールの行き先は一つ（{S.port(m.group(2) + '.' + m.group(3))}）で、じかにつないでも何の裏も通りません")),
    ("reroute", r"^rails too close or overlapping \(vertical gap (\d+)px, min (\d+)\): rail of (\S+) and rail of (\S+)(?: \(outputs \d+ and \d+\))?$",
     lambda S, m: S.L(f"The rails of {S.node(m.group(3))} and {S.node(m.group(4))} are {m.group(1)} px apart (at least {m.group(2)})",
                      f"{S.node(m.group(3))} と {S.node(m.group(4))} のレールが近すぎます（{m.group(1)} px、最低 {m.group(2)} px）")),
    ("order", r"^rail order differs from loader order .*: rail of (\S+) and rail of (\S+)$",
     lambda S, m: S.L(f"The rails of {S.node(m.group(1))} and {S.node(m.group(2))} run in the reverse order of the loaders",
                      f"{S.node(m.group(1))} と {S.node(m.group(2))} のレールが、ローダーの並びと逆の順に通っています")),
    ("reroute", r"^raising Reroute right of a loader \((\S+)\): .*: (\S+)$",
     lambda S, m: S.L(f"{S.node(m.group(2))} could sit at the rail height, so the raising Reroute {S.node(m.group(1))} is not needed",
                      f"{S.node(m.group(2))} をレールの高さに置けば、持ち上げの Reroute（{S.node(m.group(1))}）は要りません")),
    ("order", r"^loader rail runs below its targets .*: rail of (\S+)$",
     lambda S, m: S.L(f"The rail of {S.node(m.group(1))} runs below the nodes it feeds (model, vae and clip rails go above)",
                      f"{S.node(m.group(1))} のレールが、配る先のノードより下を通っています（model、vae、clip のレールは上に）")),
    ("group", r'^wire over the title of group "(.*)": ' + _W + "$",
     lambda S, m: S.L(f"The wire {_wire_m(S, m, 2)} runs over the title of group “{m.group(1)}”",
                      f"線 {_wire_m(S, m, 2)} がグループ「{m.group(1)}」の題名の上を通っています")),
    ("group", r'^node over the title of group "(.*)": (\S+)$',
     lambda S, m: S.L(f"{S.node(m.group(2))} covers the title of group “{m.group(1)}”", f"{S.node(m.group(2))} がグループ「{m.group(1)}」の題名にかかっています")),
    ("group", r'^node overlapping group "(.*)" but not in it: (\S+)$',
     lambda S, m: S.L(f"{S.node(m.group(2))} overlaps group “{m.group(1)}” but is not in it", f"{S.node(m.group(2))} がグループ「{m.group(1)}」に入っていないのに重なっています")),
    ("group", r'^groups overlap: "(.*)" and "(.*)"$',
     lambda S, m: S.L(f"Groups “{m.group(1)}” and “{m.group(2)}” overlap", f"グループ「{m.group(1)}」と「{m.group(2)}」が重なっています")),
    ("graph", r"^type mismatch: (\S+) from (\S+) .*-> ([\w:~]+) \S+\.(\S+) \((\S+)\)$",
     lambda S, m: S.L(f"Type mismatch: {m.group(1)} from {S.node(m.group(2))} goes into {S.port(m.group(3) + '.' + m.group(4))} ({m.group(5)})",
                      f"型が合いません: {S.node(m.group(2))} の {m.group(1)} が {S.port(m.group(3) + '.' + m.group(4))}（{m.group(5)}）に入っています")),
    ("graph", r"^required input not connected: ([\w:~]+) .*\.([^.]+)$",
     lambda S, m: S.L(f"The required input {m.group(2)} of {S.node(m.group(1))} is not connected",
                      f"{S.node(m.group(1))} の必須の入力 {m.group(2)} がつながっていません")),
]
PROBLEMS = [(k, re.compile(p), f) for k, p, f in PROBLEMS]


def problem_text(p, lang):
    """{"t": plain sentence, "k": kind} for one check line. p carries the node names found in it."""
    S = Say(lang, {"names": p.get("names") or {}, "before": {}, "blocks": {}})
    for kind, rx, fn in PROBLEMS:
        m = rx.search(p["r"])
        if m:
            try:
                return {"t": fn(S, m), "k": kind}
            except (IndexError, KeyError):
                break
    return {"t": p["r"], "k": "other"}


NOTES = [
    (r"^made horizontal: " + _W + "$", lambda S, m: S.L(f"made the wire {_wire_m(S, m)} horizontal", f"線 {_wire_m(S, m)} を水平にしました")),
    (r"^no wire between (\S+) and (\S+): aligned their tops instead$",
     lambda S, m: S.L(f"no wire between {S.unit(m.group(1))} and {S.unit(m.group(2))}, so their tops were aligned instead",
                      f"{S.unit(m.group(1))} と {S.unit(m.group(2))} の間に線がないので、上端をそろえました")),
    (r"^(\S+) was not placed: put it at the origin",
     lambda S, m: S.L(f"{S.unit(m.group(1))} was not placed yet, so it went to the top-left (0, 0)",
                      f"{S.unit(m.group(1))} はまだ置かれていなかったので、左上 (0, 0) に置きました")),
    (r"^sources of (\S+) in one right-aligned column on its left \((.*)\): (.*)$",
     lambda S, m: S.L(f"put the nodes feeding {S.node(m.group(1))} ({_ids(S, m.group(3), 4)}) in a column on its left"
                      + (", positive wire horizontal" if "positive" in m.group(2) else ", centred on the column"),
                      f"{S.node(m.group(1))} につながる {_ids(S, m.group(3), 4)} を左に一列で置きました"
                      + ("（positive の線を水平に）" if "positive" in m.group(2) else "（列の真ん中に合わせて）"))),
    (r"^(\S+) in the same shape as (\S+): ", lambda S, m: S.L(f"laid out {S.unit(m.group(1))} in the same shape as {S.unit(m.group(2))}",
                                                               f"{S.unit(m.group(1))} を {S.unit(m.group(2))} と同じ形に並べました")),
    (r"^not moved, no node of the same type in (\S+): (.*)$",
     lambda S, m: S.L(f"{_ids(S, m.group(2))} did not move (no node of the same type in {S.unit(m.group(1))})",
                      f"{_ids(S, m.group(2))} は動かしていません（{S.unit(m.group(1))} に同じ型のノードがない）")),
    (r"^width (\S+): (\d+) (?:→|->) (\d+)", lambda S, m: S.L(f"width of {S.node(m.group(1))}: {m.group(2)} → {m.group(3)} px",
                                                          f"{S.node(m.group(1))} の幅: {m.group(2)} → {m.group(3)} px")),
    (r"^size (\S+): \[(\d+), (\d+)\] → \[(\d+), (\d+)\]", lambda S, m: S.L(
        f"size of {S.node(m.group(1))}: {m.group(2)}×{m.group(3)} → {m.group(4)}×{m.group(5)}",
        f"{S.node(m.group(1))} の大きさ: {m.group(2)}×{m.group(3)} → {m.group(4)}×{m.group(5)}")),
    (r"^added input: ([\w:~]+)\.(\S+)$", lambda S, m: S.L(f"added the input {m.group(2)} to {S.node(m.group(1))}",
                                                         f"{S.node(m.group(1))} に入力 {m.group(2)} を足しました")),
    (r"^block (\S+): (.*)$", lambda S, m: S.L(f"block “{m.group(1)}”: {len(m.group(2).split())} nodes",
                                               f"ブロック「{m.group(1)}」: ノード {len(m.group(2).split())} 個")),
    (r'^group "(.*)": (.*?)  frame', lambda S, m: S.L(f"group “{m.group(1)}” around {len(m.group(2).split())} nodes",
                                                     f"グループ「{m.group(1)}」: ノード {len(m.group(2).split())} 個を囲む")),
    (r"^aligned top and bottom edges: ", lambda S, m: S.L("aligned the top and bottom edges of the groups", "グループの上端と下端をそろえました")),
    (r"^color (\S+): (\S+)$", lambda S, m: S.L(f"coloured {S.node(m.group(1))} {m.group(2).replace('_', ' ')}",
                                               f"{S.node(m.group(1))} を{COLOR_JA.get(m.group(2), m.group(2))}にしました")),
    (r"^title (\S+): (.*)$", lambda S, m: S.L(f"titled {S.node(m.group(1))} “{m.group(2)}”", f"{S.node(m.group(1))} の題名を「{m.group(2)}」にしました")),
    (r"^Note (\S+): width (\d+), height (\d+)$", lambda S, m: S.L(f"placed the Note {S.node(m.group(1))} ({m.group(2)} × {m.group(3)})",
                                                                   f"Note {S.node(m.group(1))} を置きました（{m.group(2)} × {m.group(3)}）")),
    (r"^rail (\S+): height (-?\d+), Reroutes (.*), targets (.*)$", lambda S, m: S.L(
        f"rail from {S.port(m.group(1))} at height {m.group(2)}: "
        + ("no Reroutes (all wired directly)" if m.group(3).startswith("none") else f"Reroutes {_ids(S, m.group(3), 4)}")
        + f", to {S.many(m.group(4).split(), 4, S.port)}",
        f"{S.port(m.group(1))} からのレール（高さ {m.group(2)}）: "
        + ("Reroute なし（すべてじかにつないだ）" if m.group(3).startswith("none") else f"Reroute {_ids(S, m.group(3), 4)}")
        + f"、行き先 {S.many(m.group(4).split(), 4, S.port)}")),
    (r"^too close to another rail; height shifted to (-?\d+)$", lambda S, m: S.L(
        f"moved the rail to height {m.group(1)}, away from another rail", f"ほかのレールに近すぎたので、高さ {m.group(1)} にずらしました")),
    (r"^drawn at the output height (-?\d+) instead of (\S+), since nothing is in the way$", lambda S, m: S.L(
        f"drew the rail at the output height ({m.group(1)}) instead of {m.group(2)}, since nothing is in the way",
        f"じゃまがないので、{m.group(2)} ではなく出力の高さ（{m.group(1)}）でレールを引きました")),
]
NOTES = [(re.compile(p), f) for p, f in NOTES]


def note_text(line, S):
    """One per-line note of a layout run ("line k: message") in plain words."""
    m = re.match(r"^line (\d+): (.*)$", line)
    k, msg = (m.group(1), m.group(2)) if m else (None, line)
    out = msg
    for rx, fn in NOTES:
        mm = rx.search(msg)
        if mm:
            try:
                out = fn(S, mm)
            except (IndexError, KeyError):
                pass
            break
    if k is None:
        return out
    return S.L(f"Line {k}: {out}", f"{k} 行目: {out}")


# ---- the page

def build(canvases, original, lang="en"):
    """canvases: [{name, defs, nodes, wires, groups, problems, steps, walk}] as canvas.py's report_page makes them;
    original: {nodes, wires, groups, defs} of the source workflow, or None.
    lang: the user's language code (any code; it becomes <html lang>). The sentences are in it when it is in LANGS,
    in English otherwise."""
    code = str(lang or "en").strip() or "en"
    lang = code if code in LANGS else "en"
    out = []
    for c in canvases:
        steps = []
        for st in c["steps"]:
            ex = [explain(x, lang) for x in st["x"]]
            if st["kind"] == "build":
                say, det = build_summary(st["x"], lang), [e["s"] for e in ex]
            else:
                say, det = ex[0]["s"], ex[0]["d"] + [e["s"] for e in ex[1:]]
            steps.append({"kind": st["kind"], "c": st["c"], "s": say, "d": det, "v": st["v"], "p": st["p"],
                          "counts": st["counts"]})
        probs = []
        for p in c["problems"]:
            t = problem_text(p, lang)
            probs.append({"t": t["t"], "k": t["k"], "ids": p["ids"], "w": p["w"]})
        out.append({"name": c["name"], "defs": c["defs"], "nodes": c["nodes"], "wires": c["wires"], "groups": c["groups"],
                    "problems": probs, "steps": steps, "walk": c.get("walk")})
    data = json.dumps({"lang": lang, "ui": UI[lang], "chrome": CHROME, "colors": LINK_COLORS, "canvases": out, "original": original},
                      ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    title = html.escape(CHROME["title"])
    return (PAGE.replace("%LANG%", html.escape(code, quote=True)).replace("%TITLE%", title).replace("%STYLE%", _font_face() + STYLE)
            .replace("%DATA%", data).replace("%SCRIPT%", SCRIPT))


FONT_FILE = Path(__file__).with_name("fonts") / "PlusJakartaSans-latin.woff2"   # SIL OFL 1.1, see fonts/


def _font_face():
    """Plus Jakarta Sans (Latin) inside the page; Japanese comes from Google Fonts, or the machine's font without a network."""
    if not FONT_FILE.is_file():
        return ""
    data = base64.b64encode(FONT_FILE.read_bytes()).decode("ascii")
    return ("@font-face{font-family:'Plus Jakarta Sans';font-style:normal;font-weight:200 800;font-display:swap;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');unicode-range:U+0000-00FF,U+2000-206F,U+2190-2193,U+2212}}\n")


ICONS = {
    "prev": '<path d="M15 5l-8 7 8 7"/>',
    "play": '<path d="M8 5v14l11-7z" class="fill"/>',
    "next": '<path d="M9 5l8 7-8 7"/>',
    "minus": '<path d="M5 12h14"/>', "plus": '<path d="M12 5v14M5 12h14"/>',
    "fit": '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
    "map": '<path d="M3 7l6-3 6 3 6-3v13l-6 3-6-3-6 3z"/><path d="M9 4v13M15 7v13"/>',
    "follow": '<circle cx="12" cy="12" r="3"/><path d="M12 2v4M12 18v4M2 12h4M18 12h4"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    "system": '<rect x="3" y="4.5" width="18" height="12" rx="2"/><path d="M9 20h6M12 16.5V20"/>',
    "help": '<path d="M8.5 8.8a3.6 3.6 0 1 1 4.6 3.4c-.7.3-1.1.9-1.1 1.6v.9"/><circle cx="12" cy="18.6" r="1.1" class="fill"/>',
}


def _icon(name):
    return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


ACCENT = "#ff5a1f"   # the one colour that marks "now" (the needle, the current step, the moved nodes)

STYLE = """
:root{--bg:#000;--tile:#1c1c1e;--tile2:#2c2c2e;--text:#d1d1d6;--muted:#7c7c80;--faint:#48484a;--head:#f5f5f7;
--accent:%ACCENT%;--good:#5fbf7a;--bad:#ff6b5f;--warn:#e0b25c;
--cv-bg:#121214;--cv-dot:#2a2a2d;--node-bg:#353535;--node-title:#2c2c2c;--node-text:#c8c8c8;--slot-text:#a8a8a8;
--w-bg:#222;--w-text:#dddddd;--w-label:#999;--casing:rgba(0,0,0,.6);--shadow:rgba(0,0,0,.45);--mix:100;--wmix:100;--gop:.2;
--font:"Plus Jakarta Sans","Zen Kaku Gothic New","Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans CJK JP","Yu Gothic UI",system-ui,sans-serif;
--mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;--code:var(--mono),"Zen Kaku Gothic New","Hiragino Sans","Noto Sans CJK JP";--r-lg:22px;--r-md:16px;--ease:cubic-bezier(.2,.8,.2,1);color-scheme:dark}
@media (prefers-color-scheme:light){:root:not([data-theme=dark]){--bg:#e2dfe5;--tile:#f4f2f6;--tile2:#e8e6eb;--text:#3a3a3c;
--muted:#7c7a80;--faint:#c7c6cb;--head:#1d1d1f;--good:#1f7a3e;--bad:#c4321f;--warn:#a8670f;
--cv-bg:#f6f5f8;--cv-dot:#d4d2d8;--node-bg:#ffffff;--node-title:#e9e9ec;--node-text:#222;--slot-text:#4a4a52;
--w-bg:#f0f0f2;--w-text:#1a1a1a;--w-label:#6a6a72;--casing:rgba(255,255,255,.9);--shadow:rgba(0,0,0,.12);--mix:30;--wmix:70;--gop:.1;color-scheme:light}}
:root[data-theme=light]{--bg:#e2dfe5;--tile:#f4f2f6;--tile2:#e8e6eb;--text:#3a3a3c;--muted:#7c7a80;--faint:#c7c6cb;--head:#1d1d1f;
--good:#1f7a3e;--bad:#c4321f;--warn:#a8670f;--cv-bg:#f6f5f8;--cv-dot:#d4d2d8;--node-bg:#fff;--node-title:#e9e9ec;--node-text:#222;
--slot-text:#4a4a52;--w-bg:#f0f0f2;--w-text:#1a1a1a;--w-label:#6a6a72;--casing:rgba(255,255,255,.9);--shadow:rgba(0,0,0,.12);
--mix:30;--wmix:70;--gop:.1;color-scheme:light}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{background:var(--bg);color:var(--text);font:14px/1.55 var(--font);overflow:hidden}
button{font:inherit;color:inherit;border:0;background:none;padding:0;cursor:pointer}
[hidden]{display:none!important}
.icon{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.icon .fill{fill:currentColor;stroke:none}
.app{height:100%;display:grid;grid-template-columns:minmax(0,1fr) 372px;grid-template-rows:auto minmax(0,1fr);gap:0 10px;padding:0 10px 10px}
/* header: the name and the tabs over the canvas column, the theme switch over the side panel; no space above it */
.top{grid-column:1/-1;display:grid;grid-template-columns:subgrid;height:48px}
.top .lead{display:flex;align-items:stretch;gap:12px;min-width:0}
.top .name{flex:none;align-self:center;font-size:13px;font-weight:700;color:var(--head);padding-left:6px;white-space:nowrap}
.seg.theme{justify-self:end;align-self:center;padding:2px}
.seg.theme .knob{top:2px;bottom:2px}
.seg.theme button{display:grid;place-items:center;width:28px;height:24px;padding:0}
.seg.theme .icon{width:15px;height:15px}

.stage{display:flex;flex-direction:column;gap:10px;min-width:0;min-height:0}
/* segmented switch: a dark capsule with a light capsule on the chosen item */
.seg{position:relative;display:inline-flex;padding:4px;border-radius:999px;background:var(--tile2);gap:2px;max-width:100%;overflow-x:auto;scrollbar-width:none}
.seg::-webkit-scrollbar{display:none}
.seg button{height:32px;padding:0 16px;border-radius:999px;font-size:13px;font-weight:600;color:var(--muted);white-space:nowrap;transition:background .15s var(--ease),color .15s}
.seg button:hover{color:var(--head)}
.seg button{position:relative;z-index:1}
.seg button[aria-pressed=true]{color:var(--bg)}
.seg .knob{position:absolute;top:4px;bottom:4px;left:0;border-radius:999px;background:var(--head);pointer-events:none;transition:transform .25s var(--ease),width .25s var(--ease)}
/* workflow tabs, like a browser's: the chosen tab has the canvas colour and runs into the canvas below */
.tabs{display:flex;align-items:flex-end;gap:2px;min-width:0;padding:0 10px;overflow-x:auto;overflow-y:hidden;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tabs button{position:relative;flex:none;height:40px;padding:0 16px 8px;border-radius:9px 9px 0 0;font-size:12px;font-weight:600;color:var(--muted);white-space:nowrap}
.tabs button:hover{color:var(--text)}
.tabs button[aria-pressed=true]{background:var(--cv-bg);color:var(--head)}
.tabs button[aria-pressed=true]::before,.tabs button[aria-pressed=true]::after{content:"";position:absolute;bottom:0;width:9px;height:9px}
.tabs button[aria-pressed=true]::before{left:-9px;background:radial-gradient(circle at 0 0,transparent 9px,var(--cv-bg) 9.5px)}
.tabs button[aria-pressed=true]::after{right:-9px;background:radial-gradient(circle at 100% 0,transparent 9px,var(--cv-bg) 9.5px)}
#view{position:relative;flex:1;min-height:0;overflow:hidden;background:var(--cv-bg);border-radius:var(--r-lg);cursor:grab;touch-action:none;user-select:none}
#view.drag{cursor:grabbing}
#cv{position:absolute;inset:0;width:100%;height:100%;display:block}
#seg{position:absolute;left:12px;bottom:12px;z-index:2}
.tools{position:absolute;right:12px;bottom:12px;display:flex;gap:2px;padding:4px;border-radius:999px;background:var(--tile2);z-index:2}
.tool{display:grid;place-items:center;width:32px;height:32px;border-radius:999px;color:var(--text)}
.tool:hover{background:var(--faint);color:var(--head)}
.tool[aria-pressed=true]{background:var(--head);color:var(--bg)}
.tool.off{opacity:.35;pointer-events:none}
.empty{position:absolute;inset:0;display:grid;place-items:center;color:var(--muted);pointer-events:none;font-size:13px;padding:24px;text-align:center}
.ntip{position:absolute;pointer-events:none;padding:4px 10px;border-radius:999px;font-size:12px;background:var(--tile2);color:var(--head);white-space:nowrap;z-index:3}
.ntip small{color:var(--muted);margin-left:6px}
.help{position:absolute;right:12px;bottom:56px;max-width:300px;padding:12px 16px;border-radius:var(--r-md);font-size:12px;line-height:1.75;
background:var(--tile2);color:var(--text);z-index:3}
.help b{color:var(--head);font-weight:600;font-family:var(--mono);font-size:11.5px;margin-right:6px}
/* the deck: play, step, and the timeline, all one height */
.deckwrap{position:relative;flex:none}
.deck{display:flex;align-items:center;gap:6px;flex:none;height:32px}
.deck.off{opacity:.35;pointer-events:none}
.round{display:grid;place-items:center;width:32px;height:32px;border-radius:8px;background:var(--tile);color:var(--text);flex:none}
.round:hover{background:var(--tile2);color:var(--head)}
.round .icon{width:16px;height:16px;display:block}
#playicon{display:grid;place-items:center}
.speed{height:32px;width:44px;padding:0;text-align:center;border-radius:8px;background:var(--tile);font-size:12px;font-weight:600;color:var(--text);font-variant-numeric:tabular-nums;flex:none}
.speed:hover{background:var(--tile2);color:var(--head)}
.bar{position:relative;flex:1;min-width:0;height:32px;border-radius:8px;background:var(--tile);cursor:pointer;touch-action:none;user-select:none}
.bar .in{position:absolute;top:0;bottom:0;left:10px;right:10px}
.spark{position:absolute;left:0;bottom:5px;width:100%;height:20px;overflow:visible}
.spark path{fill:var(--faint);fill-opacity:.55;stroke:none}
.tk{position:absolute;bottom:0;width:1px;height:4px;background:var(--faint)}
.ph{position:absolute;top:5px;bottom:5px;width:2px;margin-left:-1px;border-radius:1px;background:var(--accent);pointer-events:none}
.tip{position:absolute;bottom:40px;transform:translateX(-50%);padding:5px 10px;border-radius:8px;font-size:12px;
background:var(--tile2);color:var(--text);pointer-events:none;white-space:nowrap;z-index:5}
.tip b{color:var(--head);font-weight:700;margin-right:6px}
/* the walkthrough: the parts in processing order instead of the timeline (same height as the deck) */
.walkbar{display:flex;align-items:center;gap:6px;height:32px}
.wparts{flex:1;min-width:0;height:32px;display:flex;gap:4px;overflow:hidden}
.wpart{min-width:0;height:32px;padding:0 10px;border-radius:8px;background:var(--tile);font-size:12px;font-weight:600;color:var(--muted);
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:background .15s var(--ease),color .15s}
.wpart:hover{color:var(--head)}
.wpart[aria-current=true]{background:var(--head);color:var(--bg)}
.wwhole[aria-pressed=true]{background:var(--head);color:var(--bg)}
.wtitle{font-size:19px;font-weight:600;line-height:1.35;color:var(--head);margin:2px 8px 6px}
.wbody{margin:0 8px;font-size:13.5px;line-height:1.7;color:var(--text)}
.wbody p{margin:0 0 6px}
/* bullets: the walkthrough text and the lists of the side panel */
.wbody ul,ul.plain{list-style:none;margin:0;padding:0}
.wbody li,ul.plain li{position:relative;padding:2px 0 2px 14px}
.wbody li::before,ul.plain li::before{content:"";position:absolute;left:2px;top:12px;width:4px;height:4px;border-radius:50%;background:var(--muted)}
.wbody ul ul{padding-left:14px}
.wbody ul ul li::before{background:none;border:1px solid var(--muted);width:3px;height:3px}
.wbody code{font:12px var(--code);background:var(--tile);border-radius:4px;padding:1px 5px;color:var(--head)}
.wbody b{color:var(--head);font-weight:600}
/* the side panel */
aside{display:flex;flex-direction:column;min-height:0;gap:10px}
.phead{display:flex;flex-direction:column;gap:10px;flex:none}
.ptop{display:flex;align-items:flex-end;justify-content:flex-end;gap:12px;padding:6px 6px 0;height:40px}
.stepno{font-size:13px;font-weight:600;color:var(--muted);font-variant-numeric:tabular-nums;white-space:nowrap}
.stepno b{display:inline-block;text-align:right;font-size:22px;font-weight:600;color:var(--head)}
.lab{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.legend{font-size:10.5px;font-weight:500;letter-spacing:.02em;color:var(--faint);text-align:right;padding:0 8px;height:17px;line-height:17px;white-space:nowrap;overflow:hidden}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px 8px}
.pill-tile{display:flex;align-items:center;justify-content:space-between;gap:8px;min-width:0;padding:13px 18px 13px 22px;border-radius:999px;background:var(--tile)}
.pt{min-width:0}
.pill-tile .v{font-size:22px;font-weight:300;line-height:1.15;color:var(--head);font-variant-numeric:tabular-nums;white-space:nowrap}
.pill-tile .was{font-size:15px;color:var(--muted)}
.pill-tile .lab{font-size:9.5px;letter-spacing:.03em;color:var(--muted);margin-top:2px}
.pill-tile svg{flex:none;width:18px;height:18px;fill:none;stroke:var(--muted);stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.pill-tile svg .f{fill:var(--muted);fill-opacity:.3}
.keys{display:grid;grid-template-columns:auto auto 1fr;align-items:center;gap:7px 10px;padding:4px 8px 2px;font-size:11.5px}
.keys>span{cursor:default}
.keys .sw{width:14px;height:10px;border-radius:3px;border:2px solid}
.keys .sw.removed{border:0;background:var(--faint);opacity:.45}
.keys .sw.behind{border:1.5px dashed var(--bad)}
.keys .d{line-height:1.45}
.keys .k{color:var(--text)}.keys .d{color:var(--muted)}
.pbody{flex:1;min-height:0;overflow-y:scroll;scrollbar-gutter:stable;scrollbar-width:thin;scrollbar-color:var(--tile2) transparent;padding:4px 4px 24px 6px}
.pbody::-webkit-scrollbar{width:8px}.pbody::-webkit-scrollbar-thumb{background:var(--tile2);border-radius:4px}.pbody::-webkit-scrollbar-track{background:transparent}
.say{font-size:13.5px;line-height:1.6;color:var(--text);margin:4px 0 10px}
h3{font-size:11px;font-weight:600;color:var(--muted);margin:16px 0 4px;padding:0 8px;display:flex;gap:6px}
h3 .c{color:var(--text)}
ul.plain li{padding:3px 0 3px 14px;font-size:13px}
.more{color:var(--head);padding:4px 0;font-size:12px;font-weight:600}
.quiet{color:var(--muted);font-size:13px;margin:6px 0}
.probs{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
.probs button{display:flex;align-items:baseline;gap:8px;width:100%;text-align:left;border-radius:8px;padding:3px 8px;font-size:11.5px;line-height:1.55;color:var(--muted)}
.probs button>span:last-child{min-width:0}
.probs button:hover,.probs button[aria-pressed=true]{color:var(--text)}
.probs button:hover{background:var(--tile)}
.probs button[aria-pressed=true]{background:var(--tile2)}
.probs .dot{flex:none;width:5px;height:5px;border-radius:50%;transform:translateY(-1px);background:var(--bad);opacity:.7}
.probs .good .dot{background:var(--good)}
details{margin-top:10px}
details{padding:0 8px}details>summary{cursor:pointer;color:var(--muted);font-size:11px;font-weight:600;list-style:none;display:flex;align-items:center;gap:8px}
details>summary::before{content:"";width:6px;height:6px;border-right:1.5px solid currentColor;border-bottom:1.5px solid currentColor;transform:rotate(-45deg);transition:transform .15s}
details[open]>summary::before{transform:rotate(45deg)}
details>summary::-webkit-details-marker{display:none}
pre.cmd{font:12px/1.6 var(--code);color:var(--text);background:var(--tile);border-radius:12px;padding:10px 12px;margin:8px 0 0;
white-space:pre-wrap;word-break:break-word;max-height:260px;overflow:auto}
.ref{color:inherit;cursor:pointer}
.ref:hover{color:var(--head);text-decoration:underline;text-decoration-color:var(--faint);text-underline-offset:3px}
.ref small{color:var(--faint);font-weight:400;margin-left:3px;font-size:.85em}
.say .ref{color:var(--head)}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
@media (max-width:900px){
body{overflow:auto;height:auto}
.app{display:flex;flex-direction:column;height:auto}
.top{display:flex;justify-content:space-between;gap:10px}
#panel{margin-top:10px}
.stage{height:72vh;min-height:440px}
.pbody{overflow:visible}
}
""".replace("%ACCENT%", ACCENT)

PAGE = """<!doctype html>
<html lang="%LANG%"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%TITLE%</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<style>%STYLE%</style></head>
<body>
<main class="app">
<header class="top"><div class="lead"><span class="name" id="brand"></span><nav class="tabs" id="tabs" role="tablist"></nav></div>
<div class="seg theme" id="theme"><button data-v="light">""" + _icon("sun") + """</button><button data-v="dark">""" + _icon("moon") + """</button><button data-v="system">""" + _icon("system") + """</button></div></header>
<section class="stage">
<div id="view"><canvas id="cv"></canvas>
<div class="seg" id="seg"><button id="sOrig" aria-pressed="false"></button><button id="sNew" aria-pressed="true"></button><button id="sWalk" aria-pressed="false" hidden></button></div>
<div class="empty" id="empty" hidden></div><div class="ntip" id="ntip" hidden></div>
<div class="tools"><button class="tool" id="zout">""" + _icon("minus") + """</button><button class="tool" id="zin">""" + _icon("plus") + """</button>
<button class="tool" id="fit">""" + _icon("fit") + """</button><button class="tool" id="follow" aria-pressed="false">""" + _icon("follow") + """</button>
<button class="tool" id="helpb" aria-pressed="false">""" + _icon("help") + """</button></div><div class="help" id="help" hidden></div></div>
<div class="deckwrap"><div class="deck" id="transport">
<button class="round" id="play"><span id="playicon">""" + _icon("play") + """</span></button>
<button class="round" id="prev">""" + _icon("prev") + """</button><button class="round" id="next">""" + _icon("next") + """</button>
<div class="bar" id="bar"><div class="in" id="barin"><svg class="spark" id="spark" preserveAspectRatio="none"></svg><div id="ticks"></div><div class="ph" id="ph"></div></div></div>
<button class="speed" id="speed">2×</button>
</div><div class="walkbar" id="walkbar" hidden><button class="round" id="wprev">""" + _icon("prev") + """</button>
<button class="round wwhole" id="wwhole" aria-pressed="true">""" + _icon("map") + """</button>
<div class="wparts" id="wparts"></div><button class="round" id="wnext">""" + _icon("next") + """</button></div>
<div class="tip" id="tip" hidden></div></div>
</section>
<aside id="panel" aria-live="polite">
<div class="phead">
<div class="ptop"><div class="stepno" id="kpos"></div></div>
<div class="grid" id="tiles"></div>
<div class="legend" id="legend"></div>
<div class="keys" id="keys"></div>
</div>
<div class="pbody" id="pbody"></div>
</aside>
</main>
<script type="application/json" id="data">%DATA%</script>
<script>%SCRIPT%</script>
</body></html>
"""

SCRIPT = r"""
'use strict';
const D = JSON.parse(document.getElementById('data').textContent), U = D.ui, X = D.chrome;   // U: the side panel, X: the rest of the page (English)
const $ = id => document.getElementById(id);
const ICON_PLAY = $('playicon').innerHTML;
const ICON_PAUSE = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14M16 5v14"/></svg>';
const TITLE = 30, SLOT = 20, WIDGET = 24, SPEEDS = [0.5, 1, 2, 4];
const view = $('view'), cv = $('cv'), ctx = cv.getContext('2d');
// the canvas is drawn in the frontend's font (Inter), as ComfyUI draws it; the page's own text uses --font
const FONT = 'Inter, "Segoe UI", Arial, "Zen Kaku Gothic New", "Hiragino Sans", "Noto Sans CJK JP", sans-serif';
let ci = 0, t = 0, k = -1, orig = false, follow = false, sel = null, hover = null, speed = 2;
let inWalk = false, partNo = 0, walkFrom = false;   // the walkthrough: on or off, the part shown (0: the whole workflow), and whether it was entered from the original
let wbarOf = -1;   // the canvas whose part cells are in the walkthrough bar
let W = 0, H = 0, DPR = 1, queued = false, playing = null, tween = null;
const cams = {}, tOf = {}, bboxCache = {};

function C(){ return D.canvases[ci]; }
function walkOf(){ return inWalk ? C().walk : null; }
function curPart(){ const w = walkOf(); return w && partNo > 0 ? w.parts[partNo - 1] : null; }
function N(){ return C().steps.length; }
function el(tag, cls, text){ const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; }

// ---------- colours (read from the CSS variables, so the drawing follows the light and dark themes)
const TH = {};
const probe = document.createElement('canvas').getContext('2d'), rgbCache = new Map(), mixCache = new Map();
function rgb(c){
  let v = rgbCache.get(c); if (v) return v;
  probe.fillStyle = '#000'; probe.fillStyle = c; const s = probe.fillStyle;
  if (s[0] === '#') v = [parseInt(s.slice(1, 3), 16), parseInt(s.slice(3, 5), 16), parseInt(s.slice(5, 7), 16), 1];
  else { const m = s.match(/[\d.]+/g).map(Number); v = [m[0], m[1], m[2], m.length > 3 ? m[3] : 1]; }
  rgbCache.set(c, v); return v;
}
function mix(a, b, p){
  const key = a + '|' + b + '|' + p; let v = mixCache.get(key); if (v) return v;
  const x = rgb(a), y = rgb(b), q = 1 - p;
  v = `rgba(${Math.round(x[0] * p + y[0] * q)},${Math.round(x[1] * p + y[1] * q)},${Math.round(x[2] * p + y[2] * q)},${x[3] * p + y[3] * q})`;
  mixCache.set(key, v); return v;
}
function readTheme(){
  const cs = getComputedStyle(document.documentElement);
  for (const n of ['cv-bg', 'cv-dot', 'node-bg', 'node-title', 'node-text', 'slot-text', 'w-bg', 'w-text', 'w-label', 'casing', 'shadow',
                   'accent', 'good', 'bad', 'warn', 'head', 'muted']) TH[n] = cs.getPropertyValue('--' + n).trim();
  TH.mix = parseFloat(cs.getPropertyValue('--mix')) / 100; TH.wmix = parseFloat(cs.getPropertyValue('--wmix')) / 100;
  TH.gop = parseFloat(cs.getPropertyValue('--gop'));
  mixCache.clear(); request();
}
if (document.fonts) document.fonts.ready.then(() => { widthCache.clear(); cutCache.clear(); wrapCache.clear(); request(); });
matchMedia('(prefers-color-scheme: light)').addEventListener('change', readTheme);
function wcol(type){ return mix(D.colors[type] || D.colors[String(type).toUpperCase()] || '#9aa59a', '#000', TH.wmix); }

// ---------- text (widths measured once and kept)
const mctx = document.createElement('canvas').getContext('2d'), widthCache = new Map(), cutCache = new Map(), wrapCache = new Map();
function tw(s, px, wt){
  const key = px + '|' + (wt || 400) + '|' + s; let v = widthCache.get(key);
  if (v === undefined){ mctx.font = `${wt || 400} ${px}px ${FONT}`; v = mctx.measureText(s).width; widthCache.set(key, v); }
  return v;
}
function cut(s, px, maxw, wt){
  s = String(s); maxw = Math.round(maxw); if (maxw <= px) return '';
  const key = px + '|' + (wt || 400) + '|' + maxw + '|' + s; let v = cutCache.get(key); if (v !== undefined) return v;
  if (tw(s, px, wt) <= maxw) v = s;
  else { let lo = 0, hi = s.length; while (lo < hi){ const m = (lo + hi + 1) >> 1; if (tw(s.slice(0, m) + '…', px, wt) <= maxw) lo = m; else hi = m - 1; }
    v = lo ? s.slice(0, lo) + '…' : ''; }
  if (cutCache.size > 50000) cutCache.clear();
  cutCache.set(key, v); return v;
}
function wrap(s, px, maxw, maxLines){
  maxw = Math.round(maxw); const key = px + '|' + maxw + '|' + maxLines + '|' + s; let v = wrapCache.get(key); if (v) return v;
  v = []; mctx.font = `400 ${px}px ${FONT}`;
  outer: for (const para of String(s).split('\n')){
    let line = '', lw = 0;
    for (const ch of para){ const cw = mctx.measureText(ch).width; if (lw + cw > maxw && line){ v.push(line); line = ''; lw = 0; if (v.length >= maxLines) break outer; } line += ch; lw += cw; }
    v.push(line); if (v.length >= maxLines) break;
  }
  if (wrapCache.size > 5000) wrapCache.clear();
  wrapCache.set(key, v); return v;
}

// ---------- states: the state after each step, and the state between two steps (for smooth movement)
function stateOf(c, i){ const st = c.steps[i]; return {nodes: c.nodes[st.v[0]], wires: c.wires[st.v[1]], groups: c.groups[st.v[2]], defs: c.defs}; }
const idMaps = new WeakMap();
function byId(list, key){ let m = idMaps.get(list); if (!m){ m = new Map(list.map(x => [x[key], x])); idMaps.set(list, m); } return m; }
const diffs = new WeakMap();
function diffOf(c, i){
  let per = diffs.get(c); if (!per){ per = []; diffs.set(c, per); }
  if (per[i]) return per[i];
  const cur = stateOf(c, i), prev = i > 0 ? stateOf(c, i - 1).nodes : [];
  const pm = byId(prev, 0), cm = byId(cur.nodes, 0);
  const moved = new Set(), added = new Set(), changed = new Set(), removed = [];
  for (const n of cur.nodes){
    const p = pm.get(n[0]);
    if (!p) added.add(n[0]);
    else if (p[1] !== n[1] || p[2] !== n[2]) moved.add(n[0]);
    else if (p[3] !== n[3] || p[4] !== n[4] || p[5] !== n[5]) changed.add(n[0]);
  }
  for (const p of prev) if (!cm.has(p[0])) removed.push(p);
  return per[i] = {moved, added, changed, removed};
}
const lerp = (a, b, e) => a + (b - a) * e;
function still(A){ return {nodes: A.nodes.map(x => [x, 1]), wires: A.wires.map(x => [x, 1]), groups: A.groups.map(x => [x, 1]), defs: A.defs}; }
function fixedState(){
  // the state shown when it does not follow the timeline: the original, or the finished workflow in the walkthrough
  if (orig) return D.original || {nodes: [], wires: [], groups: [], defs: []};
  if (inWalk) return stateOf(C(), N() - 1);
  return null;
}
function frame(){
  // what is drawn now: lists of [item, opacity]
  const S = fixedState(); if (S) return still(S);
  const c = C(), n = N(), i = Math.max(0, Math.min(n - 1, Math.floor(t + 1e-6))), f = t - i;
  const A = stateOf(c, i);
  if (f < 1e-3 || i >= n - 1) return still(A);
  const B = stateOf(c, i + 1), e = Math.min(1, f);   // linear: the nodes move as steadily as the playhead
  const out = {nodes: [], wires: [], groups: [], defs: c.defs};
  const an = byId(A.nodes, 0), bn = byId(B.nodes, 0);
  for (const p of A.nodes) if (!bn.has(p[0])) out.nodes.push([p, 1 - e]);
  for (const q of B.nodes){ const p = an.get(q[0]);
    out.nodes.push(p ? [[q[0], lerp(p[1], q[1], e), lerp(p[2], q[2], e), lerp(p[3], q[3], e), lerp(p[4], q[4], e), q[5]], 1] : [q, e]); }
  const aw = byId(A.wires, 5), bw = byId(B.wires, 5);
  for (const p of A.wires) if (!bw.has(p[5])) out.wires.push([p, 1 - e]);
  for (const q of B.wires){ const p = aw.get(q[5]);
    out.wires.push(p ? [[lerp(p[0], q[0], e), lerp(p[1], q[1], e), lerp(p[2], q[2], e), lerp(p[3], q[3], e), q[4], q[5]], 1] : [q, e]); }
  const ag = byId(A.groups, 0), bg = byId(B.groups, 0);
  for (const p of A.groups) if (!bg.has(p[0])) out.groups.push([p, 1 - e]);
  for (const q of B.groups){ const p = ag.get(q[0]);
    out.groups.push(p ? [[q[0], lerp(p[1], q[1], e), lerp(p[2], q[2], e), lerp(p[3], q[3], e), lerp(p[4], q[4], e), q[5]], 1] : [q, e]); }
  return out;
}

// ---------- drawing (as the ComfyUI canvas draws it). One canvas, redrawn only when something changed.
function request(){ if (!queued){ queued = true; requestAnimationFrame(draw); } }
function rr(x, y, w, h, r){ ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, h, r); else ctx.rect(x, y, w, h); }
function text(s, x, y, px, color, wt, align){ ctx.font = `${wt || 400} ${px}px ${FONT}`; ctx.fillStyle = color; ctx.textAlign = align || 'left'; ctx.fillText(s, x, y); }
function wirePath(w){
  const [x0, y0, x1, y1] = w, d = Math.hypot(x1 - x0, y1 - y0) * 0.25;
  ctx.beginPath(); ctx.moveTo(x0, y0); ctx.bezierCurveTo(x0 + d, y0, x1 - d, y1, x1, y1);
}
function dot(x, y, type, linked){
  ctx.beginPath(); ctx.arc(x, y, 4.6, 0, 6.2832);
  if (linked){ ctx.fillStyle = wcol(type); ctx.fill(); }
  else { ctx.fillStyle = TH['node-bg']; ctx.fill(); ctx.lineWidth = 1.6; ctx.strokeStyle = wcol(type); ctx.stroke(); }
}
function fmt(v){ if (v === null || v === undefined) return ''; if (typeof v === 'boolean') return v ? 'true' : 'false'; return String(v); }
function nodeBox(n, def){ const tt = def && def.rr ? 0 : TITLE; return [n[1], n[2] - tt, n[1] + n[3], n[2] + n[4]]; }
function drawNode(n, def, lod){
  const [, x, y, w, h] = n;
  if (def.rr){
    rr(x, y, w, h, h / 2); ctx.fillStyle = TH['node-bg']; ctx.fill();
    if (lod > 1){ const ty = (def.o[0] || ['', '*'])[1]; dot(x + SLOT / 2, y + 0.7 * SLOT, ty, true); dot(x + w + 1 - SLOT / 2, y + 0.7 * SLOT, ty, true); }
    return;
  }
  const body = def.bg ? mix(def.bg, TH['node-bg'], TH.mix) : TH['node-bg'], head = def.c ? mix(def.c, TH['node-title'], TH.mix) : TH['node-title'];
  if (lod > 0){ rr(x + 2, y - TITLE + 4, w, h + TITLE, 9); ctx.fillStyle = TH.shadow; ctx.fill(); }
  rr(x, y - TITLE, w, h + TITLE, 8); ctx.fillStyle = body; ctx.fill();
  rr(x, y - TITLE, w, TITLE, [8, 8, 0, 0]); ctx.fillStyle = head; ctx.fill();
  if (def.m === 4){ rr(x, y - TITLE, w, h + TITLE, 8); ctx.fillStyle = 'rgba(208,64,224,.22)'; ctx.fill(); }
  if (lod < 1) return;
  ctx.beginPath(); ctx.arc(x + 15, y - TITLE / 2, 4.5, 0, 6.2832); ctx.fillStyle = TH['slot-text']; ctx.globalAlpha *= .55; ctx.fill(); ctx.globalAlpha /= .55;
  text(cut(def.n, 14, w - 36, 500), x + 28, y - 10, 14, TH['node-text'], 500);
  if (lod < 2) return;
  if (def.note !== undefined){
    const lines = wrap(String(def.note).replace(/^#+\s*/gm, '').replace(/\*\*/g, ''), 12.5, w - 24, Math.max(1, Math.floor((h - 16) / 18)));
    lines.forEach((s, j) => text(s, x + 12, y + 20 + j * 18, 12.5, TH['node-text']));
    return;
  }
  const ins = def.i || [], outs = def.o || [], rows = Math.max(ins.length, outs.length, 1);
  ins.forEach((s, j) => { const cy = y + (j + 0.7) * SLOT; dot(x + SLOT / 2, cy, s[1], s[2]); text(cut(s[0], 12, w / 2 - 24), x + 20, cy + 4, 12, TH['slot-text']); });
  outs.forEach((s, j) => { const cy = y + (j + 0.7) * SLOT; dot(x + w + 1 - SLOT / 2, cy, s[1], true); text(cut(s[0], 12, w / 2 - 24), x + w - 20, cy + 4, 12, TH['slot-text'], 400, 'right'); });
  const ws = def.w || [], start = rows * SLOT + 6, nGrow = ws.filter(r => r[1] === 'area').length;
  const growH = nGrow ? Math.max(WIDGET, (h - start - WIDGET * (ws.length - nGrow)) / nGrow) : 0;
  let wy = y + start;
  for (const [name, kind, val, linked] of ws){
    const rh = kind === 'area' ? growH : WIDGET, top = wy; wy += rh;
    if (top + rh > y + h + 1) continue;
    if (linked){ dot(x + SLOT / 2, top + SLOT / 2, '*', true); text(cut(name, 12, w - 40), x + 20, top + 14, 12, TH['slot-text']); continue; }
    const bx = x + 15, bw = w - 30, by = top + 2, bh = rh - 4;
    rr(bx, by, bw, bh, kind === 'area' ? 6 : bh / 2); ctx.fillStyle = TH['w-bg']; ctx.fill();
    const cy = by + bh / 2 + 4;
    if (kind === 'area'){
      wrap(fmt(val), 12, bw - 16, Math.max(1, Math.floor((bh - 10) / 16))).forEach((s, j) => text(s, bx + 8, by + 16 + j * 16, 12, TH['w-text']));
    } else if (kind === 'btn'){
      text(cut(name, 12, bw - 16), bx + bw / 2, cy, 12, TH['w-label'], 400, 'center');
    } else {
      const arrows = kind === 'num' || kind === 'combo', pad = arrows ? 20 : 10;
      if (arrows){ text('‹', bx + 9, cy, 14, TH['w-label'], 400, 'center'); text('›', bx + bw - 9, cy, 14, TH['w-label'], 400, 'center'); }
      let right = bx + bw - pad;
      if (kind === 'bool'){
        const on = val === true, tx = bx + bw - 30;
        rr(tx, by + bh / 2 - 6, 22, 12, 6); ctx.fillStyle = on ? TH.accent : TH['w-label']; ctx.fill();
        ctx.beginPath(); ctx.arc(on ? tx + 16 : tx + 6, by + bh / 2, 4.2, 0, 6.2832); ctx.fillStyle = '#fff'; ctx.fill();
        right = tx - 8;
      }
      const room = bw - pad * 2, labW = name ? Math.min(tw(name, 12) + 8, room * 0.55) : 0;
      if (name) text(cut(name, 12, labW), bx + pad, cy, 12, TH['w-label']);
      text(cut(fmt(val), 12, right - (bx + pad + labW) - 4), right, cy, 12, TH['w-text'], 400, 'right');
    }
  }
  if (def.img && y + h - wy > 40){ rr(x + 10, wy + 4, w - 20, y + h - wy - 12, 6); ctx.fillStyle = TH['w-bg']; ctx.globalAlpha *= .5; ctx.fill(); ctx.globalAlpha /= .5; }
}
function ring(n, def, color, width, pad, dash){
  const [x0, y0, x1, y1] = nodeBox(n, def), p = pad || 4;
  rr(x0 - p, y0 - p, x1 - x0 + 2 * p, y1 - y0 + 2 * p, def && def.rr ? (y1 - y0) / 2 + p : 11);
  ctx.lineWidth = width; ctx.strokeStyle = color; ctx.setLineDash(dash || []); ctx.stroke(); ctx.setLineDash([]);
}
function strokeWire(w, color, width, casing, dash){
  wirePath(w);
  if (casing){ ctx.lineWidth = casing; ctx.strokeStyle = TH.casing; ctx.setLineDash([]); ctx.stroke(); }
  ctx.lineWidth = width; ctx.strokeStyle = color; ctx.setLineDash(dash || []); ctx.stroke(); ctx.setLineDash([]);
}
let F = null;   // the frame last drawn (for hit tests)
function draw(){
  queued = false;
  const c = cam(); F = frame();
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.clearRect(0, 0, W, H);
  // the dot grid
  let step = 20 * c.s; while (step < 9) step *= 5;
  const r = Math.max(0.6, Math.min(1.4, c.s * 1.3)); ctx.fillStyle = TH['cv-dot'];
  for (let gx = ((c.tx % step) + step) % step; gx < W; gx += step) for (let gy = ((c.ty % step) + step) % step; gy < H; gy += step) ctx.fillRect(gx - r, gy - r, r * 2, r * 2);
  ctx.setTransform(DPR * c.s, 0, 0, DPR * c.s, DPR * c.tx, DPR * c.ty);
  const vx0 = -c.tx / c.s, vy0 = -c.ty / c.s, vx1 = (W - c.tx) / c.s, vy1 = (H - c.ty) / c.s;
  const vis = b => b[2] >= vx0 && b[0] <= vx1 && b[3] >= vy0 && b[1] <= vy1;
  const lod = c.s >= 0.33 ? 2 : c.s >= 0.18 ? 1 : 0, defs = F.defs;
  const part = curPart();   // in the walkthrough, the part shown is bright and the rest faint, as a selected problem is
  const selIds = sel ? new Set(sel.ids) : part ? new Set(part.lit) : null, selW = sel ? new Set(sel.w) : part ? new Set(part.w) : null;
  ctx.textBaseline = 'alphabetic';
  for (const [g, a] of F.groups){
    const [title, x, y, w, h, col] = g; if (!vis([x, y, x + w, y + h])) continue;
    ctx.globalAlpha = a * TH.gop; rr(x, y, w, h, 6); ctx.fillStyle = col; ctx.fill();
    ctx.globalAlpha = a * Math.min(1, TH.gop * 1.4); rr(x, y, w, 34, [6, 6, 0, 0]); ctx.fill();
    if (lod > 0){ ctx.globalAlpha = a * .9; text(cut(title, 22, w - 24, 600), x + 12, y + 25, 22, TH['node-text'], 600); }
  }
  const lw = Math.max(2.6, 1.2 / c.s);
  for (const [w, a] of F.wires){
    const d = Math.hypot(w[2] - w[0], w[3] - w[1]) * 0.25;
    if (!vis([Math.min(w[0], w[2] - d), Math.min(w[1], w[3]), Math.max(w[0] + d, w[2]), Math.max(w[1], w[3])])) continue;
    ctx.globalAlpha = a * (selW && !selW.has(w[5]) ? .22 : 1);
    strokeWire(w, wcol(w[4]), lw, lod > 0 ? lw + 2.9 : 0);
  }
  const d = orig || inWalk ? null : diffOf(C(), k);
  if (d && t === k) for (const p of d.removed){ if (!vis(nodeBox(p, defs[p[5]]))) continue; ctx.globalAlpha = .25; drawNode(p, defs[p[5]], Math.min(lod, 1)); }
  for (const [n, a] of F.nodes){
    const def = defs[n[5]]; if (!def || !vis(nodeBox(n, def))) continue;
    ctx.globalAlpha = a * (selIds && !selIds.has(n[0]) ? .22 : 1) * (def.m === 2 ? .45 : 1);
    drawNode(n, def, lod);
  }
  ctx.globalAlpha = 1;
  // what this step did and the problems at this step, drawn above the nodes
  const at = new Map(F.nodes.map(([n]) => [n[0], n])), wk = new Map(F.wires.map(([w]) => [w[5], w]));
  const sw = 1 / Math.min(1, c.s);
  if (!orig && !inWalk){
    const c0 = C();
    for (const pi of c0.steps[k].p){
      const p = c0.problems[pi]; if (p.k !== 'hidden') continue;
      const strong = sel && sel.p === p;
      for (const key of p.w){ const w = wk.get(key); if (w) strokeWire(w, wcol(w[4]), (strong ? 3.2 : 2.2) * sw, (strong ? 7 : 5) * sw, [7 * sw, 5 * sw]); }
      const n = at.get(p.ids[p.ids.length - 1]); if (n){ ctx.globalAlpha = .6; ring(n, defs[n[5]], TH.bad, 1.2 * sw, 3, [6 * sw, 4 * sw]); ctx.globalAlpha = 1; }
    }
    if (d && !sel) for (const [set, col] of [[d.moved, TH.accent], [d.added, TH.good], [d.changed, TH.warn]])
      for (const id of set){ const n = at.get(id); if (n){ ctx.globalAlpha = .75; ring(n, defs[n[5]], col, 1.5 * sw, 4); ctx.globalAlpha = 1; } }
  }
  if (sel){
    for (const key of sel.w){ const w = wk.get(key); if (w) strokeWire(w, wcol(w[4]), 3.4 * sw, 8 * sw); }
    for (const id of sel.ids){ const n = at.get(id); if (n) ring(n, defs[n[5]], TH.bad, 3.5 * sw, 6); }
  }
  if (part && !sel) for (const id of part.ids){ const n = at.get(id); if (n) ring(n, defs[n[5]], TH.accent, 2.2 * sw, 6); }
  if (hover) for (const id of hover){ const n = at.get(id); if (n) ring(n, defs[n[5]], TH.head, 3 * sw, 8); }
  $('empty').hidden = F.nodes.length > 0;
}

// ---------- camera: one frame per canvas, moved only by the viewer (or by "follow changes")
function camKey(){ return orig ? '\u0000orig' : inWalk ? '\u0001walk' + C().name : C().name; }
function bboxOfNodes(list, defs){
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const n of list){ const b = nodeBox(n, defs[n[5]]); x0 = Math.min(x0, b[0]); y0 = Math.min(y0, b[1]); x1 = Math.max(x1, b[2]); y1 = Math.max(y1, b[3]); }
  return x0 === Infinity ? null : [x0, y0, x1, y1];
}
function union(a, b){ return !a ? b : !b ? a : [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[2], b[2]), Math.max(a[3], b[3])]; }
function frameBox(){
  const key = camKey(); if (bboxCache[key] !== undefined) return bboxCache[key];
  let b = null;
  const add = st => { b = union(b, bboxOfNodes(st.nodes, st.defs)); for (const g of st.groups) b = union(b, [g[1], g[2], g[1] + g[3], g[2] + g[4]]); };
  const S = fixedState();
  if (S) add(S);
  else { const c = C(), seen = new Set(); c.steps.forEach((s, i) => { const v = s.v.join(','); if (!seen.has(v)){ seen.add(v); add(stateOf(c, i)); } }); }
  return bboxCache[key] = b;
}
function fitCam(b, maxS){
  const w = W || 800, h = H || 500;
  if (!b) return {s: 1, tx: w / 2, ty: h / 2};
  const pad = 40, top = 64, s = Math.max(0.03, Math.min(maxS || 1, (w - pad * 2) / Math.max(1, b[2] - b[0]), (h - pad - top) / Math.max(1, b[3] - b[1])));
  return {s, tx: w / 2 - (b[0] + b[2]) / 2 * s, ty: top + (h - pad - top) / 2 - (b[1] + b[3]) / 2 * s};
}
function cam(){ const key = camKey(); return cams[key] || (cams[key] = fitCam(frameBox())); }
function setCam(c){ cams[camKey()] = c; request(); }
let camAnim = null;
function animateCam(to){
  const from = Object.assign({}, cam()), key = camKey(), t0 = performance.now(), dur = 420;
  if (camAnim) cancelAnimationFrame(camAnim);
  const ease = x => 1 - Math.pow(1 - x, 3);
  const tick = now => { const x = Math.min(1, (now - t0) / dur), e = ease(x);
    cams[key] = {s: lerp(from.s, to.s, e), tx: lerp(from.tx, to.tx, e), ty: lerp(from.ty, to.ty, e)};
    request(); camAnim = x < 1 ? requestAnimationFrame(tick) : null; };
  camAnim = requestAnimationFrame(tick);
}
function showBox(b, force){
  // brings b into view if it is not (keeps the zoom unless b does not fit)
  if (!b) return;
  const c = cam(), m = 40, top = 64;
  const sx0 = b[0] * c.s + c.tx, sy0 = b[1] * c.s + c.ty, sx1 = b[2] * c.s + c.tx, sy1 = b[3] * c.s + c.ty;
  if (!force && sx0 >= m && sy0 >= top && sx1 <= W - m && sy1 <= H - m) return;
  const s = Math.min(c.s, (W - 2 * m) / Math.max(1, b[2] - b[0]), (H - m - top) / Math.max(1, b[3] - b[1]));
  animateCam({s, tx: W / 2 - (b[0] + b[2]) / 2 * s, ty: top + (H - m - top) / 2 - (b[1] + b[3]) / 2 * s});
}
function zoomAt(f, px, py){
  const c = cam(), s = Math.max(0.03, Math.min(4, c.s * f)), q = s / c.s;
  setCam({s, tx: px - (px - c.tx) * q, ty: py - (py - c.ty) * q});
}
function idsBox(ids){
  const set = new Set(ids), f = frame();
  return bboxOfNodes(f.nodes.map(x => x[0]).filter(n => set.has(n[0])), f.defs);
}
function resize(){
  const r = view.getBoundingClientRect(); DPR = window.devicePixelRatio || 1; W = r.width; H = r.height;
  cv.width = Math.round(W * DPR); cv.height = Math.round(H * DPR); request();
}
new ResizeObserver(resize).observe(view);

// ---------- pan and zoom (mouse, wheel, touch); the name of the node under the pointer
const ptrs = new Map(); let panStart = null, moved = false;
view.addEventListener('wheel', e => {
  e.preventDefault(); const r = view.getBoundingClientRect();
  zoomAt(Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.0015)), e.clientX - r.left, e.clientY - r.top);
}, {passive: false});
view.addEventListener('pointerdown', e => {
  if (e.target.closest('.tools,.seg')) return;
  view.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]); moved = false;
  panStart = {c: Object.assign({}, cam()), pts: new Map(ptrs)}; view.classList.add('drag'); $('ntip').hidden = true;
});
function nodeAt(px, py){
  if (!F) return null; const c = cam(), x = (px - c.tx) / c.s, y = (py - c.ty) / c.s;
  for (let j = F.nodes.length - 1; j >= 0; j--){ const n = F.nodes[j][0], b = nodeBox(n, F.defs[n[5]]); if (x >= b[0] && x <= b[2] && y >= b[1] && y <= b[3]) return n; }
  return null;
}
view.addEventListener('pointermove', e => {
  const r = view.getBoundingClientRect();
  if (!ptrs.has(e.pointerId)){
    if (e.pointerType !== 'mouse' || e.target !== cv) return;
    const n = nodeAt(e.clientX - r.left, e.clientY - r.top), tip = $('ntip');
    if (!n){ tip.hidden = true; return; }
    const def = F.defs[n[5]]; tip.textContent = def.n; const sm = el('small', null, '#' + n[0] + (def.t !== def.n ? ' · ' + def.t : '')); tip.appendChild(sm);
    tip.style.left = (e.clientX - r.left + 14) + 'px'; tip.style.top = (e.clientY - r.top + 16) + 'px'; tip.hidden = false; return;
  }
  ptrs.set(e.pointerId, [e.clientX, e.clientY]);
  const c0 = panStart.c, P0 = [...panStart.pts.values()], P = [...ptrs.values()];
  if (P.length >= 2 && P0.length >= 2){
    const d0 = Math.hypot(P0[0][0] - P0[1][0], P0[0][1] - P0[1][1]) || 1, d1 = Math.hypot(P[0][0] - P[1][0], P[0][1] - P[1][1]);
    const m0 = [(P0[0][0] + P0[1][0]) / 2 - r.left, (P0[0][1] + P0[1][1]) / 2 - r.top], m1 = [(P[0][0] + P[1][0]) / 2 - r.left, (P[0][1] + P[1][1]) / 2 - r.top];
    const s = Math.max(0.03, Math.min(4, c0.s * d1 / d0)), q = s / c0.s;
    setCam({s, tx: m1[0] - (m0[0] - c0.tx) * q, ty: m1[1] - (m0[1] - c0.ty) * q}); moved = true;
  } else {
    const p0 = panStart.pts.get(e.pointerId); if (!p0) return;
    const dx = e.clientX - p0[0], dy = e.clientY - p0[1]; if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
    setCam({s: c0.s, tx: c0.tx + dx, ty: c0.ty + dy});
  }
});
view.addEventListener('pointerleave', () => { $('ntip').hidden = true; });
function endPtr(e){
  if (!ptrs.has(e.pointerId)) return; ptrs.delete(e.pointerId);
  panStart = {c: Object.assign({}, cam()), pts: new Map(ptrs)};
  if (!ptrs.size){ view.classList.remove('drag'); if (!moved && sel){ sel = null; request(); panel(); }
    else if (!moved && inWalk){   // in the walkthrough, a click on a node goes to its part
      const r = view.getBoundingClientRect(), n = nodeAt(e.clientX - r.left, e.clientY - r.top);
      const j = n ? walkOf().parts.findIndex(q => q.ids.includes(n[0])) : -1; if (j >= 0 && j + 1 !== partNo) goPart(j + 1); } }
}
view.addEventListener('pointerup', endPtr); view.addEventListener('pointercancel', endPtr);
$('zin').onclick = () => zoomAt(1.25, W / 2, H / 2);
$('zout').onclick = () => zoomAt(0.8, W / 2, H / 2);
$('fit').onclick = () => animateCam(fitCam(frameBox()));
$('follow').onclick = () => { if (inWalk) return; follow = !follow; $('follow').setAttribute('aria-pressed', String(follow)); if (follow) followChanges(); };
function followChanges(){
  if (orig) return; const d = diffOf(C(), k), st = stateOf(C(), k);
  const ids = new Set([...d.moved, ...d.added, ...d.changed]);
  if (ids.size) showBox(bboxOfNodes(st.nodes.filter(n => ids.has(n[0])), st.defs));
}

const KEYS = ['crossings', 'non-horizontal wires', 'wires behind nodes', 'overlaps'];
const OC = D.original && D.original.counts, ONE = D.canvases.length === 1;
const sum4 = cnt => KEYS.reduce((a, key) => a + (cnt[key] || 0), 0);
function fill(tpl, v){ return tpl.replace(/\{(\w+)\}/g, (m, key) => v[key]); }
const MICON = {
  'crossings': '<path d="M3 6c7 0 11 12 18 12M3 18c7 0 11-12 18-12"/>',
  'non-horizontal wires': '<circle class="f" cx="5" cy="18" r="2"/><circle class="f" cx="19" cy="6" r="2"/><path d="M6.6 16.8 17.4 7.2"/>',
  'wires behind nodes': '<rect class="f" x="7" y="5" width="10" height="14" rx="2"/><path d="M2 12h3M19 12h3"/>',
  'overlaps': '<rect class="f" x="3" y="4" width="11" height="10" rx="2"/><rect class="f" x="10" y="10" width="11" height="10" rx="2"/>',
};

// ---------- the side panel: numbers and pictures that stay in place; the words scroll below
function rich(parent, s){
  const re = /\[\[(n|m):([^|\]]*)\|(.*?)\]\]/g; let last = 0, m;
  while ((m = re.exec(s))){
    if (m.index > last) parent.appendChild(document.createTextNode(s.slice(last, m.index)));
    const ids = m[2].split(','), sp = el('span', 'ref', m[3]);
    if (m[1] === 'n' && ids[0].length <= 8) sp.appendChild(el('small', null, '#' + ids[0]));
    sp.title = ids.length > 1 ? ids.length + ' nodes' : '#' + ids[0];
    sp.onmouseenter = () => { hover = ids; request(); };
    sp.onmouseleave = () => { hover = null; request(); };
    sp.onclick = e => { e.stopPropagation(); showBox(idsBox(ids), false); };
    parent.appendChild(sp); last = re.lastIndex;
  }
  if (last < s.length) parent.appendChild(document.createTextNode(s.slice(last)));
  return parent;
}
function list(parent, items, limit){
  const ul = el('ul', 'plain'); parent.appendChild(ul);
  const put = n => { ul.innerHTML = ''; items.slice(0, n).forEach(s => ul.appendChild(rich(el('li'), s))); };
  put(limit);
  if (items.length > limit){
    const b = el('button', 'more', `${U.show_all} (${items.length})`); let open = false;
    b.onclick = () => { open = !open; put(open ? items.length : limit); b.textContent = open ? U.show_less : `${U.show_all} (${items.length})`; };
    parent.appendChild(b);
  }
}
function probItems(ul, items, cls){
  for (const p of items){
    const li = el('li', cls), b = el('button'); b.appendChild(el('span', 'dot')); b.appendChild(rich(el('span'), p.t));
    b.setAttribute('aria-pressed', String(!!(sel && sel.p === p)));
    b.onclick = e => { if (e.target.closest('.ref')) return; sel = sel && sel.p === p ? null : {p, ids: p.ids, w: p.w}; request(); panel(); if (sel) showBox(idsBox(p.ids), false); };
    li.appendChild(b); ul.appendChild(li);
  }
}
const real = (c, x) => c.problems[x].k !== 'info';

// the tiles are made once per canvas and only their numbers and bars change, so nothing on the panel jumps
let T = null;
function makeTiles(){
  // one small capsule per problem: the number now and in the original, and what it counts
  const grid = $('tiles'); grid.innerHTML = '';
  T = {m: {}};
  for (const key of KEYS){
    const t = el('div', 'pill-tile'), txt = el('div', 'pt'), v = el('div', 'v'), now = el('span', 'now'), was = el('span', 'was');
    v.append(now, was); txt.append(v, el('div', 'lab', U.counts[key]));
    const ic = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); ic.setAttribute('viewBox', '0 0 24 24'); ic.innerHTML = MICON[key];
    t.append(txt, ic); grid.appendChild(t); T.m[key] = {now, was};
  }
  // what the coloured outlines on the canvas mean; pointing at one lights up those nodes of this step
  const keys = $('keys'); keys.innerHTML = '';
  for (const key of ['moved', 'added', 'changed', 'removed', 'behind']){
    const sw = el('span', 'sw ' + key), k1 = el('span', 'k', U.units[key]), d1 = el('span', 'd', U.keys_note[key]);
    if (key !== 'removed' && key !== 'behind') sw.style.borderColor = `var(--${{moved: 'accent', added: 'good', changed: 'warn'}[key]})`;
    const on = () => { if (orig || key === 'behind') return; const d = diffOf(C(), k); hover = key === 'removed' ? d.removed.map(r => r[0]) : [...d[key]]; request(); };
    for (const e of [sw, k1, d1]){ e.onmouseenter = on; e.onmouseleave = () => { hover = null; request(); }; }
    keys.append(sw, k1, d1);
  }
}
function updateTiles(){
  const c = C(), cnt = c.steps[k].counts, cmp = OC && ONE;
  $('legend').textContent = cnt.unplaced ? `${X.unplaced_title} ${cnt.unplaced}` : cmp ? X.legend : X.legend_one;
  for (const key of KEYS){
    const m = T.m[key];
    m.now.textContent = cnt.unplaced ? '—' : (cnt[key] || 0);
    m.was.textContent = cmp ? ` / ${OC[key] || 0}` : '';
  }
}
function stepNo(){
  // the step, or in the walkthrough the part; nothing in the original or the whole workflow (hidden, not emptied: the row keeps its height)
  const K = $('kpos'), n = inWalk ? walkOf().parts.length : N(), num = el('b', null, String(inWalk ? partNo : k + 1));
  K.style.visibility = orig || (inWalk && !partNo) ? 'hidden' : '';
  num.style.minWidth = String(n).length + 'ch'; K.replaceChildren(num, ` / ${n}`);
}
function panel(){
  if (!T) makeTiles();
  stepNo(); updateTiles();
  for (const id of ['tiles', 'legend', 'keys']) $(id).hidden = inWalk;
  const B = $('pbody'); B.innerHTML = '';
  if (inWalk){ walkPanel(B); return; }
  if (orig){ B.appendChild(el('p', 'quiet', D.original && D.original.api ? U.original_note_api : U.original_note)); return; }
  const c = C(), st = c.steps[k];
  if (st.kind !== 'layout'){ const say = el('p', 'say'); rich(say, st.s); B.appendChild(say); }
  const cur = new Set(st.p.filter(x => real(c, x))), prev = new Set(k > 0 ? c.steps[k - 1].p.filter(x => real(c, x)) : []);
  const added = [...cur].filter(x => !prev.has(x)), gone = [...prev].filter(x => !cur.has(x));
  if (added.length){ const h = el('h3', null, U.appeared); h.appendChild(el('span', 'c', String(added.length))); B.appendChild(h);
    const ul = el('ul', 'probs'); B.appendChild(ul); probItems(ul, added.map(x => c.problems[x]), 'bad'); }
  if (gone.length){ const det = el('details'), ul = el('ul', 'probs'); det.appendChild(el('summary', null, `${U.solved} ${gone.length}`)); ul.style.marginTop = '8px';
    det.appendChild(ul); probItems(ul, gone.map(x => c.problems[x]), 'good'); B.appendChild(det); }
  if (st.d.length){ const det = el('details'); det.appendChild(el('summary', null, `${U.details} ${st.d.length}`)); list(det, st.d, 50); B.appendChild(det); }
  const all = el('details'); all.appendChild(el('summary', null, `${U.all_problems} ${cur.size}`));
  const box = el('ul', 'probs'); box.style.marginTop = '8px'; all.appendChild(box);
  all.ontoggle = () => { if (all.open && !box.childNodes.length) probItems(box, [...cur].map(x => c.problems[x]), 'bad'); };
  B.appendChild(all);
  const raw = el('details'); raw.appendChild(el('summary', null, st.c.length > 1 ? `${U.commands} ${st.c.length}` : U.command));
  raw.appendChild(el('pre', 'cmd', st.c.join('\n'))); B.appendChild(raw);
  B.scrollTop = 0;
}

// ---------- the timeline: the whole run from the first step to the last, and a line where we are now.
// The grey area is the number of the four problems at each step, so the steps that made or solved problems show.
// ---------- the walkthrough: the finished workflow, part by part in processing order (written by the agent that rebuilt it)
function inline(parent, text){
  // `code` and **bold** inside a line; everything else is plain text (the split puts the marked pieces at the odd places)
  text.split(/(`[^`]+`|\*\*[^*]+\*\*)/).forEach((m, j) => {
    if (j % 2 === 0){ if (m) parent.appendChild(document.createTextNode(m)); }
    else if (m[0] === '`') parent.appendChild(el('code', null, m.slice(1, -1)));
    else parent.appendChild(el('b', null, m.slice(2, -2)));
  });
}
function mdLite(parent, text){
  // lines: a plain line is a paragraph; "- " is a bullet. A deeper indent than the bullet above nests it one level, however
  // deep the indent is; the same indent as an open list goes on in that list
  const stack = [];   // the open lists, outermost first: {ul, indent}
  const top = () => stack[stack.length - 1];
  for (const raw of (text || '').split('\n')){
    const m = raw.match(/^(\s*)[-*] (.*)$/);
    if (!m){ stack.length = 0; if (raw.trim()){ const p = el('p'); inline(p, raw.trim()); parent.appendChild(p); } continue; }
    const indent = m[1].replace(/\t/g, '  ').length;
    let closed = null;
    while (stack.length && top().indent > indent) closed = stack.pop();
    if (closed && (!stack.length || top().indent < indent)) stack.push(closed);   // between two levels: stays in the list just closed
    else if (!stack.length || top().indent < indent){
      const ul = el('ul'); (stack.length ? (top().ul.lastElementChild || top().ul) : parent).appendChild(ul); stack.push({ul, indent});
    }
    const li = el('li'); inline(li, m[2]); top().ul.appendChild(li);
  }
}
function walkPanel(B){
  const w = walkOf(), P = curPart();
  if (P){ B.appendChild(el('div', 'wtitle', P.title)); const body = el('div', 'wbody'); mdLite(body, P.text); B.appendChild(body); }
  else B.appendChild(el('div', 'wtitle', w.intro || C().name));
  B.scrollTop = 0;
}
function walkbar(){
  // the parts in processing order, each its own cell; the map button before them shows the whole workflow (no part).
  // The cells are made once per canvas and only the current one changes, so the focus stays on the cell pressed
  const B = $('wparts');
  if (wbarOf !== ci){
    wbarOf = ci; B.innerHTML = '';
    walkOf().parts.forEach((q, i) => {
      const n = [...q.title].length, b = el('button', 'wpart', q.title);
      b.style.flex = `${n + 2} 1 0`; if (n <= 4) b.style.minWidth = 'max-content';   // widths in proportion to the titles; a short one is never cut
      b.title = q.title; b.onclick = () => goPart(i + 1); B.appendChild(b);
    });
  }
  $('wwhole').setAttribute('aria-pressed', String(partNo === 0));
  B.querySelectorAll('button').forEach((b, i) => b.setAttribute('aria-current', String(partNo === i + 1)));
}
function goPart(j, again){
  // again: draw and frame the part even if it is the one shown (entering the walkthrough, another canvas)
  const w = walkOf(); if (!w) return;
  const to = Math.max(0, Math.min(w.parts.length, j));
  if (to === partNo && to !== j && !again) return;   // past the first or the last part: the view stays as the viewer left it
  partNo = to; sel = null; hover = null;
  walkbar(); panel(); request();
  const P = curPart(); animateCam(fitCam(P ? idsBox(P.lit) : frameBox(), 1));   // close in on the part (no closer than 1:1)
}
function segState(){
  $('sOrig').setAttribute('aria-pressed', String(orig)); $('sNew').setAttribute('aria-pressed', String(!orig && !inWalk));
  $('sWalk').setAttribute('aria-pressed', String(inWalk));
}
function setWalk(v, toOrig){
  // toOrig: on leaving, go to the original (true) or the rebuilt workflow (false); left out, back to where the walkthrough was entered from
  if (v && !C().walk) return;
  stop(); if (tween){ cancelAnimationFrame(tween.raf); tween = null; } setT(Math.round(t));
  if (v) walkFrom = orig; else if (toOrig !== undefined) walkFrom = toOrig;
  inWalk = v; orig = v ? false : walkFrom && !!D.original; sel = null; hover = null; partNo = 0;
  segState(); timeline(); marks();
  if (v) goPart(0, true); else { panel(); request(); }
}
$('wprev').onclick = () => goPart(partNo - 1); $('wnext').onclick = () => goPart(partNo + 1);
$('wwhole').onclick = () => goPart(0);

function frac(v){ return v / Math.max(1, N() - 1); }
function timeline(){
  $('ticks').innerHTML = ''; $('spark').innerHTML = ''; T = null;
  $('transport').hidden = inWalk; $('walkbar').hidden = !inWalk;
  $('follow').classList.toggle('off', inWalk); $('follow').setAttribute('aria-disabled', String(inWalk));   // faded in place, so the tools do not move
  if (inWalk){ walkbar(); return; }
  $('transport').classList.toggle('off', orig);
  if (orig) return;
  const c = C(), n = N(), vals = c.steps.map(st => st.counts.unplaced ? 0 : sum4(st.counts)), mx = Math.max(1, ...vals);
  c.steps.forEach((st, i) => { const e = el('i', 'tk'); e.style.left = (frac(i) * 100) + '%'; $('ticks').appendChild(e); });
  const X0 = i => frac(i) * 1000, Y = v => 20 - v / mx * 20;
  let d = `M0,20 L0,${Y(vals[0])}`;
  vals.forEach((v, i) => { d += ` L${X0(i)},${Y(v)}`; if (i < n - 1) d += ` L${X0(i + 1)},${Y(v)}`; });
  d += ` L1000,${Y(vals[n - 1])} L1000,20 Z`;
  $('spark').setAttribute('viewBox', '0 0 1000 20'); $('spark').innerHTML = `<path d="${d}"/>`;
}
function marks(){ if (!orig) $('ph').style.left = (frac(t) * 100) + '%'; }
function setT(v){
  const n = N(); t = Math.max(0, Math.min(n - 1, v));
  if (Math.abs(t - Math.round(t)) < 1e-4) t = Math.round(t);
  const nk = Math.max(0, Math.min(n - 1, Math.ceil(t - 1e-4)));
  if (nk !== k){ k = nk; tOf[ci] = k; sel = null; hover = null; panel(); if (follow) followChanges(); }
  marks(); request();
}
function tweenTo(target, dur){
  if (tween) cancelAnimationFrame(tween.raf);
  const from = t, t0 = performance.now();
  if (Math.abs(target - from) > 1.01 || !dur){ tween = null; setT(target); return; }
  const tick = now => { const x = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - x, 3); setT(from + (target - from) * e); tween = x < 1 ? {raf: requestAnimationFrame(tick)} : null; };
  tween = {raf: requestAnimationFrame(tick)};
}
// press or drag anywhere on the bar to go there; on release it settles on the nearest step
const bar = $('bar'); let scrub = false;
function tAt(clientX){ const r = $('barin').getBoundingClientRect(); return Math.max(0, Math.min(1, (clientX - r.left) / r.width)) * (N() - 1); }
bar.addEventListener('pointerdown', e => { if (orig) return; stop(); if (tween) cancelAnimationFrame(tween.raf); scrub = true; bar.setPointerCapture(e.pointerId); setT(tAt(e.clientX)); });
bar.addEventListener('pointermove', e => {
  if (orig) return; const v = tAt(e.clientX);
  if (scrub){ setT(v); $('tip').hidden = true; return; }
  const i = Math.round(v), st = C().steps[i], d = diffOf(C(), i), tip = $('tip');
  tip.innerHTML = ''; tip.appendChild(el('b', null, `${X.step} ${i + 1}`));
  const parts = [['moved', d.moved.size], ['added', d.added.size], ['changed', d.changed.size], ['removed', d.removed.length]].filter(x => x[1]).map(([key, n]) => `${X[key]} ${n}`);
  parts.push(st.counts.unplaced ? `${st.counts.unplaced} ${X.counts.unplaced}` : `${sum4(st.counts)} ${X.problems}`);
  tip.appendChild(document.createTextNode(parts.join(' · ')));
  const r = $('barin').getBoundingClientRect(), wr = bar.parentElement.parentElement.getBoundingClientRect();
  tip.style.left = Math.max(140, Math.min(wr.width - 140, r.left - wr.left + frac(i) * r.width)) + 'px'; tip.hidden = false;
});
function endScrub(){ if (!scrub) return; scrub = false; tweenTo(Math.round(t), 180); }
bar.addEventListener('pointerup', endScrub); bar.addEventListener('pointercancel', endScrub);
bar.addEventListener('pointerleave', () => { $('tip').hidden = true; });

// ---------- playing: the line moves at a steady speed, and the canvas moves with it
const STEP_MS = 1200;
function stop(){
  if (playing){ cancelAnimationFrame(playing.raf); playing = null; }
  $('playicon').innerHTML = ICON_PLAY; $('play').title = X.play; $('play').setAttribute('aria-label', X.play);
}
function play(){
  if (playing) return stop();
  if (orig) return;
  if (tween){ cancelAnimationFrame(tween.raf); tween = null; }
  if (t >= N() - 1) setT(0);
  $('playicon').innerHTML = ICON_PAUSE; $('play').title = X.pause; $('play').setAttribute('aria-label', X.pause);
  playing = {last: performance.now()};
  const tick = now => {
    const p = playing; if (!p) return;
    const v = t + (now - p.last) / (STEP_MS / speed); p.last = now;
    if (v >= N() - 1){ setT(N() - 1); return stop(); }
    setT(v); p.raf = requestAnimationFrame(tick);
  };
  playing.raf = requestAnimationFrame(tick);
}
function stepBy(dv){ stop(); const target = dv > 0 ? Math.floor(t + 1e-4) + 1 : Math.ceil(t - 1e-4) - 1; tweenTo(target, 420); }
$('prev').onclick = () => stepBy(-1);
$('next').onclick = () => stepBy(1);
$('play').onclick = play;
$('speed').onclick = () => { speed = SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length]; $('speed').textContent = speed + '×'; };
document.addEventListener('keydown', e => {
  if (e.target.closest && e.target.closest('input,textarea')) return;
  if (inWalk && ['ArrowLeft', 'ArrowRight', 'Home', 'End', ' ', 'Escape'].includes(e.key)){
    e.preventDefault(); if (e.key === 'ArrowLeft') goPart(partNo - 1); else if (e.key === 'ArrowRight') goPart(partNo + 1);
    else if (e.key === 'Home' || e.key === 'Escape') goPart(0); else if (e.key === 'End') goPart(walkOf().parts.length); return; }
  if (e.key === 'w' || e.key === 'W'){ setWalk(!inWalk); return; }
  if (e.key === 'ArrowLeft'){ e.preventDefault(); $('prev').click(); }
  else if (e.key === 'ArrowRight'){ e.preventDefault(); $('next').click(); }
  else if (e.key === ' '){ e.preventDefault(); play(); }
  else if (e.key === 'Home'){ e.preventDefault(); stop(); tweenTo(0); }
  else if (e.key === 'End'){ e.preventDefault(); stop(); tweenTo(N() - 1); }
  else if (e.key === 'o' || e.key === 'O'){ setOrig(!orig); }
  else if (e.key === '+' || e.key === '='){ $('zin').click(); }
  else if (e.key === '-'){ $('zout').click(); }
  else if (e.key === '0' || e.key === 'f'){ $('fit').click(); }
  else if (e.key === 'Escape' && sel){ sel = null; request(); panel(); }
});

// ---------- canvases and the original
function tabs(){
  const B = $('tabs');
  if (D.canvases.length < 2){ B.hidden = true; return; }
  if (B.querySelector('button')){ B.querySelectorAll('button').forEach((b, j) => b.setAttribute('aria-pressed', String(j === ci))); return; }
  D.canvases.forEach((c, j) => { const b = el('button', null, c.name); b.setAttribute('role', 'tab'); b.setAttribute('aria-pressed', String(j === ci));
    b.onclick = () => { stop(); ci = j; sel = null; showAll(tOf[j] || 0); }; B.appendChild(b); });
}
function setOrig(v){
  if (!D.original) return; stop(); orig = v; inWalk = false; sel = null; hover = null;
  segState(); timeline(); panel(); marks(); request();
}
function showAll(at){
  $('sWalk').hidden = !C().walk; $('seg').hidden = !D.original && !C().walk;
  if (inWalk && !C().walk){ inWalk = false; segState(); }   // this canvas has no walkthrough: show its rebuilt workflow
  partNo = 0; tabs(); timeline(); k = -1; setT(at === undefined ? t : at); if (inWalk) goPart(0, true);
}
$('sOrig').textContent = X.original; $('sNew').textContent = X.rebuilt; $('seg').title = X.compare;
$('sWalk').textContent = X.walk; $('sWalk').title = X.walk_title;
$('sOrig').hidden = !D.original;
$('sOrig').onclick = () => inWalk ? setWalk(false, true) : setOrig(true);
$('sNew').onclick = () => inWalk ? setWalk(false, false) : setOrig(false);
$('sWalk').onclick = () => setWalk(true);
for (const [id, key] of [['prev', 'prev'], ['next', 'next'], ['zin', 'zoom_in'], ['zout', 'zoom_out'], ['fit', 'fit'], ['follow', 'follow'],
                         ['play', 'play'], ['speed', 'speed'], ['wprev', 'prev_part'], ['wnext', 'next_part'], ['wwhole', 'walk_whole'], ['helpb', 'help_title']]){
  $(id).title = X[key]; $(id).setAttribute('aria-label', X[key]);
}
$('empty').textContent = X.empty;
for (const [key, text] of X.help){ const row = el('div'); row.append(el('b', null, key), ' ' + text); $('help').appendChild(row); }
$('helpb').onclick = () => { const open = $('help').hidden; $('help').hidden = !open; $('helpb').setAttribute('aria-pressed', String(open)); };
if (!D.canvases.length){ D.canvases.push({name: '', defs: [], nodes: [[]], wires: [[]], groups: [[]], problems: [], steps: [{kind: 'cmd', c: [], s: U.empty, d: [], v: [0, 0, 0], p: [], counts: {}}]}); }
// light, dark, or as the system says; the choice is kept in this browser
function setTheme(v){
  if (v === 'light' || v === 'dark') document.documentElement.dataset.theme = v; else delete document.documentElement.dataset.theme;
  for (const b of $('theme').children) b.setAttribute('aria-pressed', String(b.dataset.v === (v || 'system')));
  try { localStorage.setItem('rn-theme', v || 'system'); } catch (e) {}
  readTheme();
}
for (const b of $('theme').children){ b.title = X.theme[b.dataset.v]; b.setAttribute('aria-label', X.theme[b.dataset.v]); b.onclick = () => setTheme(b.dataset.v); }
$('brand').textContent = X.brand;
let theme0 = 'system'; try { theme0 = localStorage.getItem('rn-theme') || 'system'; } catch (e) {}
setTheme(theme0); resize(); showAll(0);
// the light capsule of a switch slides to the chosen item
function knob(seg, now){
  const on = seg.querySelector('button[aria-pressed=true]'); let k = seg.querySelector('.knob');
  if (!k){ k = el('span', 'knob'); seg.prepend(k); now = true; }
  k.hidden = !on; if (!on) return;
  if (now) k.style.transition = 'none';
  k.style.width = on.offsetWidth + 'px'; k.style.transform = `translateX(${on.offsetLeft}px)`;
  if (now){ k.offsetWidth; k.style.transition = ''; }
}
for (const seg of document.querySelectorAll('.seg')){
  knob(seg, true);
  new MutationObserver(() => knob(seg)).observe(seg, {subtree: true, attributes: true, attributeFilter: ['aria-pressed']});
}
const reknob = () => document.querySelectorAll('.seg').forEach(s => knob(s, true));
addEventListener('resize', reknob); if (document.fonts) document.fonts.ready.then(reknob);
"""
