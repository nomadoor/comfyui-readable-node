"""Machine checks on the graph itself. Python standard library only.

- Types match: each link's output type and input type can be connected under the frontend's connection rules
- Required inputs are connected (an input that has a widget is fine, since the widget holds a value)
- All output nodes are still there (the ones passed as ``outputs``)
- The link records agree (inputs[].link, outputs[].links and links)
Wires passing behind nodes are checked by the canvas, not here.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comfy_schema  # noqa: E402


def _produced_types(oi):
    """Types some node outputs. Input types outside this set (VIEWPORT state, etc.) are values held by a dedicated frontend widget."""
    types = set()
    for info in oi.values():
        for t in info.get("output") or []:
            if isinstance(t, str):
                types.update(x.strip() for x in t.split(","))
    return types


def check_links(flat, oi, only=None):
    """Whether link types match. With ``only`` (a set of node ids), only links into or out of those nodes are checked (used by replace.py)."""
    problems = []
    nodes = {n["id"]: n for n in flat["nodes"]}
    for l in flat["links"]:
        if only is not None and l["origin_id"] not in only and l["target_id"] not in only:
            continue
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if o is None or t is None:
            problems.append(f"link {l['id']}: an end node is missing")
            continue
        outs = o.get("outputs") or []
        otype = outs[l["origin_slot"]].get("type") if l["origin_slot"] < len(outs) else None
        tin = next((i for i in t.get("inputs") or [] if i["name"] == l["target_input"]), None)
        if otype is None or tin is None:
            problems.append(f"link {l['id']}: output {l['origin_slot']} of {o['id']} or input {l['target_input']} of {t['id']} is missing")
            continue
        itype = tin.get("type")
        info = oi.get(t.get("type"))
        if info:
            for name, raw in comfy_schema.input_slots(info, t.get("widgets_values"), [i["name"] for i in t.get("inputs") or []]):
                if name == tin["name"]:
                    itype = raw
        # Matching either the defined type or the saved input type is enough (for dynamic inputs of custom nodes, the saved type is the real one)
        if not comfy_schema.is_valid_connection(otype, itype) and not comfy_schema.is_valid_connection(otype, tin.get("type")):
            problems.append(f"type mismatch: {otype} from {o['id']} {o.get('type')} -> {t['id']} {t.get('type')}.{tin['name']} ({itype})")
    return problems


def check(flat, oi, outputs=None):
    problems = check_links(flat, oi)
    produced = _produced_types(oi)
    nodes = {n["id"]: n for n in flat["nodes"]}
    for n in flat["nodes"]:
        info = oi.get(n.get("type"))
        if not info:
            continue
        req = (info.get("input") or {}).get("required") or {}
        widget_names = set(comfy_schema.widget_names(info, n.get("widgets_values")))
        linked = {i["name"] for i in n.get("inputs") or [] if i.get("link") is not None}
        # If a saved input has a widget, a dedicated frontend widget holds the value
        widget_names |= {i["name"] for i in n.get("inputs") or [] if i.get("widget")}
        for name, spec in req.items():
            if name in widget_names or name in linked:
                continue
            if spec[0] == "COMFY_AUTOGROW_V3":
                continue
            if len(spec) > 1 and isinstance(spec[1], dict) and spec[1].get("socketless"):
                continue  # widget without a socket
            if isinstance(spec[0], str) and spec[0] != "*" and not set(spec[0].split(",")) & produced:
                continue  # value of a dedicated widget (a type no node outputs)
            problems.append(f"required input not connected: {n['id']} {n.get('title') or n['type']}.{name}")
    for o in outputs or []:
        if o not in nodes:
            problems.append(f"output node {o} is missing")
    # Consistency of link records (do inputs[].link, outputs[].links and links say the same thing?)
    link_ids = {l["id"]: l for l in flat["links"]}
    for n in flat["nodes"]:
        if n.get("mode", 0) != 0:
            problems.append(f"kept node {n['id']} has mode {n.get('mode')}")
        for i in n.get("inputs") or []:
            l = link_ids.get(i.get("link")) if i.get("link") is not None else None
            if i.get("link") is not None and (l is None or l["target_id"] != n["id"] or l["target_input"] != i["name"]):
                problems.append(f"{n['id']}.{i['name']}: link {i.get('link')} does not match links")
        for k, o in enumerate(n.get("outputs") or []):
            for lid in o.get("links") or []:
                l = link_ids.get(lid)
                if l is None or l["origin_id"] != n["id"] or l["origin_slot"] != k:
                    problems.append(f"{n['id']} output {k}: link {lid} does not match links")
    return problems
