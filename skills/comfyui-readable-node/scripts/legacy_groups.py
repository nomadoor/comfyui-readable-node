"""Expand legacy group nodes (``extra.groupNodes`` plus nodes typed ``workflow>Name``) into their inner nodes.

Legacy group nodes were removed from ComfyUI. The frontend still loads them by unpacking each instance
into its inner nodes. This module produces the same graph at the top level, so the reader can then
treat the workflow like any other.

How a group instance maps onto its inner nodes (the behaviour this module reproduces):

* The group exposes, in order: first every *socket* input of the inner nodes that is not fed from
  inside the group (inner nodes taken in index order), then every *widget* of the inner nodes that is
  not fed from inside the group. A widget that the inner node saved as a socket ("converted") is
  exposed after all plain widgets, ordered by node and then by its slot position.
* Exposed names are the input's own name, or its label/custom name. A name already taken gets the
  inner node's title (or type) as a prefix; if that is taken too, a running number is added.
* The instance's ``widgets_values`` follow the exposed widgets in order. A seed-like widget is followed
  by one extra value for its "control after generate" mode.
* The group exposes as outputs every inner output that is not consumed inside the group, plus the
  outputs listed in ``external``.
* An inner Reroute has a single input named after the type it carries.

Two deliberate differences from the frontend, both reported as warnings:

* A link from outside into an inner Reroute is kept. (The frontend looks the target slot up by name,
  and a Reroute's slot has no name, so the link is lost and the result cannot run.)
* A group that contains node types not installed in ComfyUI is still expanded, using the saved slots.
  (The frontend leaves such a group unexpanded.)
"""

import copy

import comfy_schema as CS

PREFIXES = ("workflow>", "workflow/")
SEED_NAMES = {"seed", "noise_seed"}


def _as_lists(links):
    return [l if isinstance(l, list) else [l["id"], l["origin_id"], l["origin_slot"], l["target_id"], l["target_slot"], l["type"]]
            for l in links or []]


class _Definition:
    """One group definition: who feeds whom inside it, and what it exposes."""

    def __init__(self, data, oi):
        self.data, self.oi = data, oi
        self.nodes = data.get("nodes") or []
        self.inner_links = [l for l in data.get("links") or [] if l[0] is not None]
        self.fed = {(l[2], l[3]) for l in self.inner_links}                 # (node index, input slot) fed inside
        self.consumed = {(l[0], l[1]) for l in self.inner_links}            # (node index, output slot) used inside
        self.external = {(int(e[0]), int(e[1])) for e in data.get("external") or [] if len(e) > 2 and e[2] is not None}
        self.missing = set()
        self.inputs, self.outputs = self._interface()

    # -- what an inner node looks like
    def _reroute_type(self, i):
        for l in self.inner_links:
            if l[0] == i:
                tgt = self.nodes[l[2]] if l[2] < len(self.nodes) else {}
                ins = tgt.get("inputs") or []
                if l[3] < len(ins) and ins[l[3]].get("type"):
                    return ins[l[3]]["type"]
        return next((l[5] for l in self.data.get("links") or [] if l[2] == i), "*")

    def _shape(self, i, node):
        """(inputs, number of outputs). inputs: [(name, spec, is_widget)]. None when the node is internal only."""
        kind = node.get("type")
        if kind == "Reroute":
            used_out = any(l[0] == i for l in self.inner_links)
            used_in = any(l[2] == i for l in self.inner_links)
            if used_out and used_in and (i, 0) not in self.external:
                return None, 0
            t = self._reroute_type(i)
            return [(t, [t, {"forceInput": True}], False)], 1
        info = self.oi.get(kind)
        if info:
            ins = []
            for name, spec, _ in CS.ordered_input_specs(info):
                t, opts = CS._spec_type_and_opts(spec)
                ins.append((name, spec, t in CS.WIDGET_TYPES and not opts.get("forceInput")))
            return ins, len(info.get("output") or [])
        self.missing.add(kind)
        return [(x.get("name"), [x.get("type"), {}], bool(x.get("widget"))) for x in node.get("inputs") or []], \
            len(node.get("outputs") or [])

    # -- what the group exposes
    def _interface(self):
        exposed, converted, outputs = [], [], []
        names = _Names(self.data)
        for i, node in enumerate(self.nodes):
            ins, n_out = self._shape(i, node)
            if ins is None:
                continue
            saved = node.get("inputs") or []
            saved_names = [x.get("name") for x in saved]
            # per node: plain widgets are named first, then sockets
            for name, spec, is_widget in ins:
                if not is_widget:
                    continue
                slot = next((k for k, x in enumerate(saved)
                             if x.get("name") == name and (x.get("widget") or {}).get("name") == name), None)
                if slot is None:
                    exposed.append(_Exposed(names.take(i, node, name), i, name, True, _has_control(name, spec)))
                else:
                    converted.append((i, slot, node, name, spec))
            for k, (name, spec, _) in enumerate(s for s in ins if not s[2]):
                slot = saved_names.index(name) if name in saved_names else k
                if (i, slot) not in self.fed:
                    exposed.append(_Exposed(names.take(i, node, name), i, name, False, False))
            for o in range(n_out):
                if (i, o) not in self.consumed or (i, o) in self.external:
                    outputs.append((i, o))
        # converted widgets come after everything else, by node and then by slot position
        for i, slot, node, name, spec in sorted(converted, key=lambda x: (x[0], x[1])):
            if (i, slot) not in self.fed:
                exposed.append(_Exposed(names.take(i, node, name), i, name, True, _has_control(name, spec)))
        return exposed, outputs


class _Exposed:
    __slots__ = ("name", "index", "inner", "widget", "control")

    def __init__(self, name, index, inner, widget, control):
        self.name, self.index, self.inner, self.widget, self.control = name, index, inner, widget, control


class _Names:
    """Hands out unique exposed names (see the module docstring)."""

    def __init__(self, data):
        self.config = data.get("config") or {}
        self.taken = {}

    def take(self, index, node, input_name):
        custom = ((self.config.get(str(index)) or {}).get("input") or {}).get(input_name, {}).get("name")
        label = next((x.get("label") for x in node.get("inputs") or [] if x.get("name") == input_name and x.get("label")), None)
        name = custom or label or input_name
        key = name
        if (node.get("type") == "PrimitiveNode" and node.get("title")) or name in self.taken:
            prefix = f"{node.get('title') or node.get('type')} "
            key = name = f"{prefix}{input_name}"
            if name in self.taken:
                name = f"{prefix}{self.taken[name]} {input_name}"
        self.taken[key] = self.taken.get(key, 1) + 1
        return name


def _has_control(name, spec):
    return name in SEED_NAMES or bool(CS._spec_type_and_opts(spec)[1].get("control_after_generate"))


def expand(raw, oi):
    """Return a copy of ``raw`` (a top-level workflow dict) with legacy group nodes expanded, and warnings."""
    groups = (raw.get("extra") or {}).get("groupNodes") or {}
    instances = [n for n in raw.get("nodes") or [] if isinstance(n.get("type"), str) and n["type"].startswith(PREFIXES)]
    if not groups or not instances:
        return raw, []
    raw = copy.deepcopy(raw)
    warnings = []
    links = _as_lists(raw.get("links"))
    ids = {"node": max([raw.get("last_node_id") or 0] + [n["id"] for n in raw["nodes"] if isinstance(n.get("id"), int)]) + 1,
           "link": max([raw.get("last_link_id") or 0] + [l[0] for l in links]) + 1}

    def add_link(o, os_, t, ts, typ):
        links.append([ids["link"], o, os_, t, ts, typ])
        ids["link"] += 1

    for g in instances:
        gname = next(g["type"][len(p):] for p in PREFIXES if g["type"].startswith(p))
        data = groups.get(gname)
        label = f"legacy group node {g['id']} ({gname})"
        if not data:
            warnings.append(f"{label}: no definition in extra.groupNodes; not expanded")
            continue
        d = _Definition(copy.deepcopy(data), oi)
        if any(n.get("type") == "PrimitiveNode" for n in d.nodes):
            warnings.append(f"{label}: contains a Primitive node; not expanded")
            continue
        # place the inner nodes at the top level with new ids, keeping their layout around the instance
        new_id = {}
        gx, gy = (g.get("pos") or [0, 0])[:2]
        x0 = min((n.get("pos") or [0, 0])[0] for n in d.nodes)
        y0 = min((n.get("pos") or [0, 0])[1] for n in d.nodes)
        for i, n in enumerate(d.nodes):
            m = {k: v for k, v in n.items() if k != "index"}
            m["id"] = new_id[i] = ids["node"]
            ids["node"] += 1
            m["pos"] = [gx + (n.get("pos") or [0, 0])[0] - x0, gy + (n.get("pos") or [0, 0])[1] - y0]
            if g.get("mode"):
                m["mode"] = g["mode"]
            for inp in m.get("inputs") or []:
                inp["link"] = None
            for out in m.get("outputs") or []:
                out["links"] = []
            raw["nodes"].append(m)
        nodes = {n["id"]: n for n in raw["nodes"]}
        for l in d.inner_links:
            add_link(new_id[l[0]], l[1], new_id[l[2]], l[3], l[5])
        # widget values: one per exposed widget, two for a widget with a control mode
        vals = list(g.get("widgets_values") or [])
        vi = 0
        by_name = {}
        for e in d.inputs:
            by_name[e.name] = e
            if not e.widget:
                continue
            n = nodes[new_id[e.index]]
            info = oi.get(n.get("type"))
            nv = n.get("widgets_values")
            if vi < len(vals) and isinstance(nv, list):
                wnames = CS.widget_names(info, nv) if info else [x.get("name") for x in n.get("inputs") or [] if x.get("widget")]
                if e.inner in wnames:
                    j = wnames.index(e.inner)
                    while len(nv) <= j:
                        nv.append(None)
                    nv[j] = vals[vi]
                    if e.control and vi + 1 < len(vals) and j + 1 < len(nv):
                        nv[j + 1] = vals[vi + 1]
            vi += 2 if e.control else 1
        # links into the instance go to the inner input with that exposed name
        incoming = {l[0]: l for l in links if l[3] == g["id"]}
        for inp in g.get("inputs") or []:
            l = incoming.get(inp.get("link"))
            if l is None:
                continue
            e = by_name.get(inp.get("name"))
            if e is None:
                warnings.append(f"{label}: input {inp.get('name')} has no inner target; link dropped")
                continue
            n = nodes[new_id[e.index]]
            slots = [x.get("name") for x in n.get("inputs") or []]
            ts = slots.index(e.inner) if e.inner in slots else (0 if n.get("type") == "Reroute" else None)
            if ts is None:
                warnings.append(f"{label}: input {inp.get('name')} has no matching inner slot; link dropped")
                continue
            add_link(l[1], l[2], n["id"], ts, l[5])
        # links out of the instance come from the inner output at that position
        for l in [l for l in links if l[1] == g["id"]]:
            if l[2] >= len(d.outputs):
                warnings.append(f"{label}: output {l[2]} has no inner source; link dropped")
                continue
            idx, slot = d.outputs[l[2]]
            add_link(new_id[idx], slot, l[3], l[4], l[5])
        links = [l for l in links if g["id"] not in (l[1], l[3])]
        raw["nodes"] = [n for n in raw["nodes"] if n["id"] != g["id"]]
        msg = f"{label}: expanded into {len(d.nodes)} inner nodes (ids {min(new_id.values())}-{max(new_id.values())})"
        if d.missing:
            msg += f"; it contains node types not installed in ComfyUI ({', '.join(sorted(d.missing))}), which the frontend would leave unexpanded"
        warnings.append(msg)
    # rebuild each node's link bookkeeping from the link table
    nodes = {n["id"]: n for n in raw["nodes"]}
    for n in raw["nodes"]:
        for inp in n.get("inputs") or []:
            inp["link"] = None
        for out in n.get("outputs") or []:
            out["links"] = []
    for l in links:
        o, t = nodes.get(l[1]), nodes.get(l[3])
        if o and l[2] < len(o.get("outputs") or []):
            o["outputs"][l[2]]["links"].append(l[0])
        if t and l[4] < len(t.get("inputs") or []):
            t["inputs"][l[4]]["link"] = l[0]
    raw["links"] = links
    raw["last_node_id"] = ids["node"] - 1
    raw["last_link_id"] = ids["link"] - 1
    if isinstance(raw.get("state"), dict):
        raw["state"]["lastNodeId"] = ids["node"] - 1
        raw["state"]["lastLinkId"] = ids["link"] - 1
    return raw, warnings
