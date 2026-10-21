"""Turn an API-format workflow (the prompt: {id: {"class_type", "inputs", "_meta"}}) into a UI-format workflow, the way
the frontend opens one: app.loadApiJson creates the nodes and wires, then graph.arrange() places them.
Python standard library only.

An API-format workflow has no positions, sizes, groups, Notes or bypassed nodes. The positions made here are the ones
ComfyUI gives when it opens the file, so the original view shows what the user sees there.

Behaviour matched to the frontend (loadApiJson, then graph.arrange() and computeExecutionOrder):
- Nodes are created in the order of Object.keys: integer-like ids in ascending order first, then the others in file order.
  An id with ":" (a node from inside a subgraph) becomes the same id with "_".
- The title is _meta.title (written only when it differs from the display name, as the frontend saves it).
- Values that are not [id, slot] go into the widgets (keyed by name for the types that save them that way, VHS_ and so on); [id, slot] become wires, in the order of the inputs.
- arrange(): one column per level (1 + the longest path from a node with no wired input), from x = 100, each column
  as wide as its widest node (at least 100) + 100. In a column, from y = 100 + 30, each node height + 100 + 30 down.
  The order in a column is the topological order (a queue from the nodes with no wired input, outputs in slot order).
Differs from the frontend: a node type that is not in object_info keeps its wires (the frontend shows a placeholder
without outputs, so its wires are lost); its outputs are made from the slots the wires use.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comfy_schema as CS  # noqa: E402
import nodesize  # noqa: E402

MARGIN = 100            # LGraph.arrange default margin
TITLE_H = 30            # LiteGraph.NODE_TITLE_HEIGHT
FRONTEND_MIN = json.loads((Path(__file__).resolve().parent / "frontend_min_sizes.json").read_text(encoding="utf-8"))["sizes"]


def is_api(raw):
    """True for an API-format workflow: no "nodes", and every value is a node with class_type."""
    if not isinstance(raw, dict) or "nodes" in raw or not raw:
        return False
    return all(isinstance(v, dict) and "class_type" in v for v in raw.values())


def _js_key_order(keys):
    """The order of Object.keys: array-index-like keys ascending, then the rest in insertion order."""
    def is_index(k):
        return k.isdigit() and str(int(k)) == k and int(k) < 2 ** 32 - 1
    return sorted([k for k in keys if is_index(k)], key=int) + [k for k in keys if not is_index(k)]


def _unwrap(v):
    """unwrapExportedWidgetValue: {"__value__": [...]} is how the export wraps a list value."""
    if isinstance(v, dict) and "__value__" in v and (v.get("__type__") == "CURVE" or isinstance(v["__value__"], list)):
        return v["__value__"]
    return v


def _is_link(v):
    return isinstance(v, list) and len(v) == 2 and isinstance(v[1], int) and not isinstance(v[1], bool)


def to_ui(api, oi):
    """Returns the UI-format workflow (dict) and a list of warnings."""
    warns = []
    keys = _js_key_order(list(api.keys()))
    taken = {k for k in keys if ":" not in k}
    new_id = {}
    for k in keys:
        if ":" not in k:
            new_id[k] = k
            continue
        cand = k.replace(":", "_")
        while cand in taken:
            cand += "_"
        taken.add(cand)
        new_id[k] = cand

    nodes, by = [], {}
    for k in keys:
        data = api[k]
        t = data["class_type"]
        info = oi.get(t)
        named = {nm: _unwrap(v) for nm, v in (data.get("inputs") or {}).items() if not _is_link(v)}
        nid = int(new_id[k]) if new_id[k].isdigit() else new_id[k]
        n = {"id": nid, "type": t, "pos": [0, 0], "size": [0, 0], "flags": {}, "order": 0, "mode": 0,
             "properties": {"Node name for S&R": t}}
        if info:
            values = CS.build_widgets_values(info, named)
            n["widgets_values"] = CS.saved_widgets_values(t, info, named)
            n["inputs"], n["outputs"] = CS.new_node_slots(info, values)
            unknown = [nm for nm in named if nm not in CS.widget_names(info, values)]
            if unknown:
                warns.append(f"{k} {t}: values for widgets the current definition does not have were dropped: {', '.join(unknown)}")
        else:
            warns.append(f"{k} {t}: not in object_info (its outputs are made from the wires that use them)")
            n["widgets_values"] = list(named.values())
            n["inputs"] = [{"name": nm, "type": "*", "link": None} for nm, v in (data.get("inputs") or {}).items() if _is_link(v)]
            n["outputs"] = []
        title = (data.get("_meta") or {}).get("title")
        shown = (info or {}).get("display_name") or t
        if title and title != shown:
            n["title"] = title
        nodes.append(n)
        by[k] = n

    # outputs of unknown types: as many as the highest slot a wire uses
    for k in keys:
        for v in (api[k].get("inputs") or {}).values():
            if _is_link(v) and str(v[0]) in by and not oi.get(by[str(v[0])]["type"]):
                outs = by[str(v[0])]["outputs"]
                while len(outs) <= v[1]:
                    outs.append({"name": f"output {len(outs)}", "type": "*", "links": []})

    links, lid = [], 0
    for k in keys:
        tgt = by[k]
        for nm, v in (api[k].get("inputs") or {}).items():
            if not _is_link(v):
                continue
            src = by.get(str(v[0]))
            if src is None or v[1] >= len(src["outputs"]):
                warns.append(f"{k}.{nm}: the wire from {v[0]} slot {v[1]} has no source and was dropped")
                continue
            slot = next((i for i, x in enumerate(tgt["inputs"]) if x["name"] == nm), None)
            if slot is None:
                warns.append(f"{k}.{nm}: {tgt['type']} has no input of this name; the wire from {v[0]} was dropped")
                continue
            old = tgt["inputs"][slot].get("link")
            if old is not None:
                links = [l for l in links if l[0] != old]
                for o in (x for n in nodes for x in n["outputs"]):
                    if old in o["links"]:
                        o["links"].remove(old)
            lid += 1
            otype = src["outputs"][v[1]]["type"]
            links.append([lid, src["id"], v[1], tgt["id"], slot, otype if otype != "*" else tgt["inputs"][slot]["type"]])
            src["outputs"][v[1]]["links"].append(lid)
            tgt["inputs"][slot]["link"] = lid

    for n in nodes:
        size = nodesize.default_size(n, oi, title=n.get("title"))
        if size is None:
            size = nodesize.estimate_unknown(n)
        fm = FRONTEND_MIN.get(n["type"])
        if fm:
            size = [max(size[0], fm[0]), max(size[1], fm[1])]
        n["size"] = [round(size[0]), round(size[1])]
    _arrange(nodes, links)
    for i, n in enumerate(nodes):
        n["order"] = i
    ints = [n["id"] for n in nodes if isinstance(n["id"], int)]
    ui = {"last_node_id": max(ints or [0]), "last_link_id": lid, "nodes": nodes, "links": links,
          "groups": [], "config": {}, "extra": {"api_format": True}, "version": 0.4}
    return ui, warns


def _arrange(nodes, links):
    """LGraph.arrange(): see the module docstring."""
    by = {n["id"]: n for n in nodes}
    lk = {l[0]: l for l in links}
    level, remaining, queue = {}, {}, []
    for n in nodes:
        num = sum(1 for i in n["inputs"] if i.get("link") is not None)
        if num == 0:
            queue.append(n["id"])
            level[n["id"]] = 1
        else:
            level[n["id"]] = 0
            remaining[n["id"]] = num
    order, done, visited = [], set(), set()
    while queue:
        nid = queue.pop(0)
        order.append(nid)
        done.add(nid)
        for o in by[nid]["outputs"]:
            for l in o["links"]:
                if l in visited or l not in lk:
                    continue
                t = lk[l][3]
                if not level[t] or level[t] <= level[nid]:
                    level[t] = level[nid] + 1
                visited.add(l)
                remaining[t] -= 1
                if remaining[t] == 0:
                    queue.append(t)
    order += [n["id"] for n in nodes if n["id"] not in done]   # loops
    columns = {}
    for nid in order:
        columns.setdefault(level[nid] or 1, []).append(by[nid])
    x = MARGIN
    for c in sorted(columns):
        widest, y = 100, MARGIN + TITLE_H
        for n in columns[c]:
            n["pos"] = [x, y]
            widest = max(widest, n["size"][0])
            y += n["size"][1] + MARGIN + TITLE_H
        x += widest + MARGIN
