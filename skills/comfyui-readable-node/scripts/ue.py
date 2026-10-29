"""Turn the implicit links of Anything Everywhere (the cg-use-everywhere custom node pack) into real links.

Called by flatten.py on each saved graph before subgraphs are expanded. The saved ``extra.ue_links`` is
not trusted (it is not refreshed on save), so the links are recomputed from the nodes.

Behaviour reproduced (matching version 7.8 of the pack):

* Broadcasters are active (mode 0) nodes whose type starts with "Anything Everywhere", plus
  "Seed Everywhere", "Prompts Everywhere", and ordinary nodes marked ``properties.ue_convert`` (they
  broadcast their own outputs, except those listed in ``output_not_broadcasting``).
* A broadcaster offers what is plugged into each of its inputs (looking through bypassed nodes), with a
  priority. Seed Everywhere offers its own INT; Prompts Everywhere sends its first input only to
  "positive"-like inputs and its second only to "negative"-like inputs.
* Receivers are the unconnected inputs of active, non-broadcasting nodes (an input whose upstream is cut
  by a bypass also counts). A widget input is a receiver only when ``widget_ue_connectable`` enables it
  (or, for saves older than 7.0, when the widget had been converted to a socket).
* A receiver takes the offer with the highest priority among those whose type matches and whose
  restrictions (group, colour, title / input / group regexes, repeated-type rules) allow it. A tie is
  left unconnected and reported.
* Seed Everywhere is replaced by a PrimitiveInt; flatten.py removes the other broadcasters afterwards.
"""

import re

import comfy_schema

REGEX_KEYS = ("title", "input", "prompt", "negative", "group")
SEED_INPUT_REGEX = "seed|seed"
POSITIVE_REGEX = r"(_|\b)pos(itive|_|\b)|positive"
NEGATIVE_REGEX = r"(_|\b)neg(ative|_|\b)|negative"
BYPASS, MUTE = 4, 2


def is_ue(node):
    t = node.get("type") or ""
    return t.startswith("Anything Everywhere") or t in ("Seed Everywhere", "Prompts Everywhere")


def _settings(node):
    """The node's UE settings in the 7.x shape (older saves keep them in other places)."""
    p = node.setdefault("properties", {})
    s = dict(p.get("ue_properties") or {})
    try:
        major = float(".".join(str(s.get("version") or "0").split(".")[:2]))
    except ValueError:
        major = 0.0
    if major < 7.0 and is_ue(node):
        wv = node.get("widgets_values") if isinstance(node.get("widgets_values"), list) else []
        if node.get("type") == "Seed Everywhere":
            wv = []          # its widget value is the seed, not a regex
        s = {"group_restricted": p.get("group_restricted", 0), "color_restricted": p.get("color_restricted", 0),
             "widget_ue_connectable": p.get("widget_ue_connectable") or {}, "input_ue_unconnectable": {},
             "title_regex": wv[0] if len(wv) > 0 else None, "input_regex": wv[1] if len(wv) > 1 else None,
             "group_regex": wv[2] if len(wv) > 2 else None}
    elif major < 7.0:
        s["widget_ue_connectable"] = s.get("widget_ue_connectable") or p.get("widget_ue_connectable") or {}
        s["input_ue_unconnectable"] = {}
    if node.get("type") == "Seed Everywhere":
        s["seed_inputs"] = True
        s["input_regex"] = s.get("input_regex") or SEED_INPUT_REGEX
    for k in REGEX_KEYS:
        if s.get(f"{k}_regex") == ".*":
            s[f"{k}_regex"] = None
    return s


def _compiled(settings, key):
    """(compiled regex, inverted) for a settings key, or None."""
    text = settings.get(f"{key}_regex")
    if not text:
        return None
    try:
        return re.compile(text), bool(settings.get(f"{key}_regex_invert"))
    except re.error:
        return None


def _passes(rx, text):
    return rx is None or bool(rx[0].search(text)) != rx[1]


class _Graph:
    """One saved graph (before expansion), seen the way the pack sees it."""

    def __init__(self, g):
        self.g, self.nodes, self.links, self.groups, self.order = g, g["nodes"], g["links"], g["groups"], g["order"]

    def connect(self, origin, target_id, input_name, ltype):
        target = self.nodes[target_id]
        ins = target.setdefault("inputs", [])
        idx = next((k for k, i in enumerate(ins) if i["name"] == input_name), None)
        if idx is None:   # a widget input dropped from the saved inputs; put it back first
            ins.append({"name": input_name, "type": ltype, "widget": {"name": input_name}, "link": None})
            idx = len(ins) - 1
        lid = max([0] + list(self.links)) + 1
        self.links[lid] = {"id": lid, "origin_id": origin[0], "origin_slot": origin[1],
                           "target_id": target_id, "target_slot": idx, "type": ltype}
        ins[idx]["link"] = lid
        src = self.nodes.get(origin[0])
        outs = (src or {}).get("outputs") or []
        if origin[1] < len(outs):
            if outs[origin[1]].get("links") is None:
                outs[origin[1]]["links"] = []
            outs[origin[1]]["links"].append(lid)

    def through_bypass(self, link):
        """Follow a link upstream through bypassed nodes; None when the chain is cut."""
        ltype = link["type"]
        while link is not None:
            if link["origin_id"] == "-10":
                return link
            parent = self.nodes.get(link["origin_id"])
            if parent is None:
                return None
            if parent.get("mode") != BYPASS:
                return link
            ins = parent.get("inputs") or []
            k = link["origin_slot"]
            lid = ins[k].get("link") if k < len(ins) and ins[k].get("type") == ltype else \
                next((i.get("link") for i in ins if i.get("type") == ltype), None)
            if lid is None:
                return None
            link = self.links.get(lid)
        return None

    def centre_in(self, node, bounding):
        pos, size = node.get("pos"), node.get("size")
        if not pos or not size:
            return False
        cx, cy = pos[0] + size[0] / 2, pos[1] - 30 + (size[1] + 30) / 2   # the bounding box includes the 30px title
        x, y, w, h = bounding
        return x <= cx <= x + w and y <= cy <= y + h

    def members(self, group):
        return [n for n in self.order if self.centre_in(self.nodes[n], group["bounding"])]

    def sends_to_disabled(self):
        """The pack's "connect to bypassed" option is not saved; infer it from the saved links."""
        return any(self.nodes.get(str(u.get("downstream")), {}).get("mode") in (MUTE, BYPASS)
                   for u in self.g["extra"].get("ue_links") or [])

    def pre7(self):
        """Is an active broadcaster older than 7.0 (widgets converted to sockets were receivers)?"""
        for n in self.nodes.values():
            if is_ue(n) and n.get("mode", 0) == 0:
                props = n.get("properties") or {}
                m = re.match(r"^(\d+)\.", str(props.get("ver") or (props.get("ue_properties") or {}).get("version") or ""))
                if m and int(m.group(1)) < 7:
                    return True
        return False


class _Offer:
    """One thing a broadcaster sends: a type, where it comes from, and the rules for who may take it."""

    def __init__(self, sender, ltype, origin, priority, settings, scope, pairing=None, seed=False):
        self.sender, self.type, self.origin, self.priority = sender, ltype, origin, priority
        self.title_rx = _compiled(settings, "title")
        self.input_rx = _compiled(settings, "input")
        self.string_to_combo = (settings.get("string_to_combo") or 0) > 0
        self.to_any = (settings.get("send_to_any") or 0) > 0
        self.scope = scope            # node ids allowed to receive, or None for all
        self.pairing = pairing        # (rule, name) for repeated types
        self.seed = seed

    def accepts(self, nid, node, inp):
        if self.origin[0] == nid:
            return False
        if self.pairing and not _paired(self.pairing, node, inp):
            return False
        t = inp.get("type")
        if t is None:
            if not self.seed:          # unknown type: only seeds go by name
                return False
        elif t != self.type and not (self.type == "STRING" and t == "COMBO" and self.string_to_combo) \
                and not (t == "*" and self.to_any):
            return False
        if self.scope is not None and nid not in self.scope:
            return False
        return _passes(self.title_rx, node.get("title") or node.get("type") or "") and \
            _passes(self.input_rx, inp.get("label") or inp.get("localized_name") or inp["name"])


def _paired(pairing, node, inp):
    rule, name = pairing
    tname = inp.get("label") or inp["name"]
    n = min(len(name), len(tname))
    return {0: tname == name, 1: tname[:n] == name[:n], 2: tname[len(tname) - n:] == name[len(name) - n:],
            3: node.get("title") == name, 4: bool(re.search(name, tname))}.get(rule, True)


def _scope(gv, nid, node, s):
    """Node ids this broadcaster may reach, from its group / colour / group-regex restrictions."""
    allowed = None
    by_group = s.get("group_restricted") or 0
    if by_group:
        mine = set()
        for g in gv.groups:
            m = gv.members(g)
            if nid in m:
                mine.update(m)
        allowed = list(mine) if by_group == 1 else [n for n in gv.order if n not in mine]
    by_colour = s.get("color_restricted") or 0
    if by_colour:
        pool = allowed if allowed is not None else gv.order
        allowed = [n for n in pool if (gv.nodes[n].get("color") == node.get("color")) == (by_colour == 1)]
    grx = _compiled(s, "group")
    if grx:
        inside = set()
        for g in gv.groups:
            if _passes(grx, g.get("title") or ""):
                inside.update(gv.members(g))
        allowed = [n for n in (allowed if allowed is not None else gv.order) if n in inside]
    return allowed


def _priority(node, s, repeated):
    if s.get("priority") is not None:
        return s["priority"]
    p = 10
    if node.get("type") in ("Seed Everywhere", "Prompts Everywhere"):
        p += 10
    if any(s.get(f"{k}_regex") for k in REGEX_KEYS) or repeated:
        p += 20
    if (s.get("group_restricted") or 0) > 0:
        p += 3
    if (s.get("color_restricted") or 0) > 0:
        p += 6
    return p


def _offers(gv, nid, node):
    s = _settings(node)
    scope = _scope(gv, nid, node, s)
    if s.get("seed_inputs"):
        return [_Offer(nid, "INT", (nid, 0), _priority(node, s, set()), s, scope, seed=True)]
    sources = []        # (the slot it is labelled by, the link it comes from)
    if (node.get("properties") or {}).get("ue_convert"):
        off = s.get("output_not_broadcasting") or {}
        for i, o in enumerate(node.get("outputs") or []):
            if not off.get(o.get("name")):
                sources.append((o, {"origin_id": nid, "origin_slot": i, "type": o.get("type")}))
    else:
        for inp in node.get("inputs") or []:
            l = gv.links.get(inp.get("link"))
            if l is not None:
                sources.append((inp, gv.through_bypass(l) or l))
    # a link saved with the wildcard type ('*': the broadcaster's input takes any type) carries the type of the output
    # it comes from, as the pack reads it
    typed = []
    for slot, l in sources:
        if l.get("type") in (None, "", "*"):
            o = gv.nodes.get(l["origin_id"]) or {}
            outs = o.get("outputs") or []
            t = outs[l["origin_slot"]].get("type") if isinstance(l["origin_slot"], int) and 0 <= l["origin_slot"] < len(outs) else None
            if t in (None, "", "*"):
                t = slot.get("label") or slot.get("name")
            l = dict(l, type=t)
        typed.append((slot, l))
    sources = typed
    counts = {}
    for _, l in sources:
        counts[l["type"]] = counts.get(l["type"], 0) + 1
    repeated = {t for t, c in counts.items() if c > 1}
    pri = _priority(node, s, repeated)
    offers = []
    for slot, l in sources:
        pairing = (s.get("repeated_type_rule") or 0, slot.get("label") or slot["name"]) \
            if l["type"] in repeated or s.get("apply_to_unrepeated") else None
        offers.append(_Offer(nid, l["type"], (l["origin_id"], l["origin_slot"]), pri, s, scope, pairing))
    if node.get("type") == "Prompts Everywhere":
        for k, o in enumerate(offers[:2]):
            o.input_rx = (re.compile(POSITIVE_REGEX if k == 0 else NEGATIVE_REGEX), False)
    return offers


def _receivers(f, node, s):
    """Inputs that may receive. Widget inputs enabled in widget_ue_connectable but missing from the save are added back."""
    ins = list(node.get("inputs") or [])
    have = {i["name"] for i in ins}
    info = f.oi.get(node.get("type")) or {}
    specs = {}
    for sec in ("required", "optional"):
        specs.update((info.get("input") or {}).get(sec) or {})
    for name, on in (s.get("widget_ue_connectable") or {}).items():
        if on and name not in have:
            t = (specs[name][0] if not isinstance(specs[name][0], list) else "COMBO") if name in specs else None
            ins.append({"name": name, "type": t, "widget": {"name": name}, "link": None, "restored": True})
    return ins


def _was_converted(f, node, inp):
    """In saves older than 7.0, only widgets converted to sockets are listed in inputs."""
    info = (f.oi or {}).get(node.get("type"))
    listed = [i for i in node.get("inputs") or [] if i.get("widget") and not i.get("restored")]
    if info:
        total = len([w for w in comfy_schema.widget_names(info, node.get("widgets_values"))
                     if w not in comfy_schema.NON_VALUE_WIDGETS])
    else:
        wv = node.get("widgets_values")
        total = len(wv) if isinstance(wv, list) else 0
    return inp in listed and len(listed) < total


def _links_for(f, gv):
    old = gv.pre7()
    to_disabled = gv.sends_to_disabled()
    if to_disabled:
        f.warn("Anything Everywhere: inferred from the saved links that the author also sent to bypassed / muted nodes (a guess)")
    live = [n for n in gv.order if gv.nodes[n].get("mode", 0) == 0 or (to_disabled and gv.nodes[n].get("mode") in (MUTE, BYPASS))]
    offers = []
    for nid in live:
        node = gv.nodes[nid]
        if node.get("mode", 0) == 0 and (is_ue(node) or (node.get("properties") or {}).get("ue_convert")):
            offers += _offers(gv, nid, node)
    if not offers:
        return []
    found = []
    for nid in live:
        node = gv.nodes[nid]
        if is_ue(node) or (node.get("properties") or {}).get("rejects_ue_links"):
            continue
        s = _settings(node)
        for inp in _receivers(f, node, s):
            if (node.get("type") or "").startswith("VHS_") and inp["name"] == "vae":
                continue          # VHS nodes refuse a broadcast VAE
            l = gv.links.get(inp.get("link"))
            if l is not None and (to_disabled or gv.through_bypass(l) is not None):
                continue          # already connected
            if inp.get("widget"):
                if not ((s.get("widget_ue_connectable") or {}).get(inp["name"]) or (old and _was_converted(f, node, inp))):
                    continue
            elif (s.get("input_ue_unconnectable") or {}).get(inp["name"]):
                continue
            ok = sorted((o for o in offers if o.accepts(nid, node, inp)), key=lambda o: -o.priority)
            if not ok:
                continue
            if len(ok) > 1 and ok[0].priority == ok[1].priority:
                f.warn(f"Anything Everywhere: {node.get('title') or node.get('type')} ({nid}).{inp['name']} has tied candidates; left unconnected")
                continue
            found.append((ok[0].origin, nid, inp["name"], ok[0].type))
    return found


def resolve(f):
    """Compute the links for each saved graph and add them (call before expanding subgraphs)."""
    f.ue_added = []
    for gid, g in f.graphs.items():
        gv = _Graph(g)
        for origin, nid, name, ltype in _links_for(f, gv):
            gv.connect(origin, nid, name, ltype)
            f.ue_added.append((gid, origin, nid, name))
        for nid in gv.order:
            node = gv.nodes[nid]
            if node.get("type") == "Seed Everywhere":
                node["type"] = "PrimitiveInt"
                if not node.get("outputs"):
                    node["outputs"] = [{"name": "INT", "type": "INT", "links": []}]
