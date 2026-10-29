"""Write a flat graph as a workflow JSON that ComfyUI can open (UI format, version 0.4). Python standard library only.

- A node keeps its number; a node without one (a Reroute the canvas made, an id from a subgraph) gets a number after
  them, the same in every export (``fixed``). The mapping from the old ids is returned as ``ids``.
- Links are 6-element arrays [id, origin_id, origin_slot, target_id, target_slot, type]; target_slot is the
  index in the target's inputs.
- widgets_values are written as the positional array (values rewritten while reading are already in it).
- Working keys of the flat graph (scope, widgets, pack, cut_by, etc.) are not written.
- Only the groups passed in are written (the original groups lose their meaning once the layout changes).
"""

import json

NODE_WORK_KEYS = {"scope", "widgets", "widgets_exact", "pack", "from_subgraph", "mode_from_subgraph", "added_by",
                  "widgets_values_named", "orig_size", "note_near"}
INPUT_WORK_KEYS = {"cut_by", "restored"}


def write(flat, groups=None, fixed=None):
    """fixed: {id: number} given to nodes without a number in earlier exports. It is kept and added to, so such a node
    keeps its number from one export to the next (a Note writer or a reviewer names the same node)."""
    fixed = {} if fixed is None else fixed
    order = [n["id"] for n in flat["nodes"]]
    # a node keeps its number when it has one (the ids the canvas and its messages use), so whoever reads the exported
    # workflow names the same nodes; a node with a name instead of a number (a Reroute the canvas made, a node added
    # under a name) gets a free number after them
    ids, used = {}, set()
    for old in order:
        s = str(old)
        if s.isdigit() and int(s) > 0 and int(s) not in used:
            ids[old] = int(s)
            used.add(int(s))
    for old in order:
        n = fixed.get(str(old))
        if old not in ids and n is not None and n not in used:
            ids[old] = n
            used.add(n)
    nxt = max(list(used) + list(fixed.values()), default=0)
    for old in order:
        if old not in ids:
            nxt += 1
            ids[old] = nxt
            fixed[str(old)] = nxt
    link_ids = {l["id"]: k + 1 for k, l in enumerate(flat["links"])}
    nodes_out = []
    for k, n in enumerate(flat["nodes"]):
        m = {key: v for key, v in n.items() if key not in NODE_WORK_KEYS}
        m["id"] = ids[n["id"]]
        m["order"] = k
        # mode is kept as is (e.g. nodes left bypassed as an option for the user)
        m["mode"] = n.get("mode", 0) or 0
        m["flags"] = m.get("flags") or {}
        ins = []
        for i in n.get("inputs") or []:
            j = {key: v for key, v in i.items() if key not in INPUT_WORK_KEYS}
            j["link"] = link_ids.get(i.get("link")) if i.get("link") is not None else None
            ins.append(j)
        m["inputs"] = ins
        outs = []
        for o in n.get("outputs") or []:
            p = dict(o)
            p["links"] = [link_ids[x] for x in o.get("links") or [] if x in link_ids]
            outs.append(p)
        m["outputs"] = outs
        nodes_out.append(m)
    by_id = {n["id"]: n for n in flat["nodes"]}
    links_out = []
    for l in flat["links"]:
        t = by_id[l["target_id"]]
        slot = next(k for k, i in enumerate(t.get("inputs") or []) if i["name"] == l["target_input"])
        links_out.append([link_ids[l["id"]], ids[l["origin_id"]], l["origin_slot"], ids[l["target_id"]], slot,
                          l.get("type") or "*"])
    wf = {
        "last_node_id": max(ids.values(), default=0),
        "last_link_id": len(links_out),
        "nodes": nodes_out,
        "links": links_out,
        "groups": groups or [],
        "config": {},
        "extra": {"ds": {"scale": 1, "offset": [0, 0]}},
        "version": 0.4,
    }
    return wf, {str(k): v for k, v in ids.items()}
