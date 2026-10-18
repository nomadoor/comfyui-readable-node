"""Read a workflow JSON (UI format) and bring every graph into the same shape. Python standard library only.

The shape:
    graphs = {"root": G, "<subgraph uuid>": G, ...}
    G = {
        "nodes": {id(str): node(dict, as saved, with the id turned into a str)},
        "order": [id, ...],              # order of the nodes array (used when matching Set/Get)
        "links": {link_id(int): {"id", "origin_id"(str), "origin_slot", "target_id"(str), "target_slot", "type"}},
        "groups": [...], "inputs": [...], "outputs": [...],  # inputs/outputs only for subgraphs
        "extra": {...},
    }

Pitfalls when reading (behaviour matched to the frontend):
- Top-level links are 6-element arrays; links inside subgraphs are objects. In version 1 workflows the
  top-level links are objects too.
- A subgraph's input node is -10, its output node -20.
- Nested definitions are gathered into one list.
- In exported and PNG workflows, widget inputs are packed and target_slot is off. Inputs are matched to
  links through node.inputs[k].link, not target_slot (input_link_map).
- With extra.workflowRendererVersion == "Vue", coordinates are scaled by 1.2. Both nodes and groups are scaled back.
"""

import json

SUBGRAPH_INPUT_ID = "-10"
SUBGRAPH_OUTPUT_ID = "-20"
VUE_SCALE = 1.2


def _link_from_array(a):
    return {"id": a[0], "origin_id": str(a[1]), "origin_slot": a[2],
            "target_id": str(a[3]), "target_slot": a[4], "type": a[5] if len(a) > 5 else "*"}


def _link_from_object(o):
    return {"id": o["id"], "origin_id": str(o["origin_id"]), "origin_slot": o["origin_slot"],
            "target_id": str(o["target_id"]), "target_slot": o["target_slot"], "type": o.get("type", "*")}


def _normalize_graph(raw, scale):
    nodes, order = {}, []
    for n in raw.get("nodes") or []:
        n = dict(n)
        n["id"] = str(n["id"])
        if scale != 1.0:
            if n.get("pos"):
                n["pos"] = [n["pos"][0] / scale, n["pos"][1] / scale]
            if n.get("size"):
                n["size"] = [n["size"][0] / scale, n["size"][1] / scale]
        nodes[n["id"]] = n
        order.append(n["id"])
    groups = []
    for grp in raw.get("groups") or []:
        grp = dict(grp)
        if scale != 1.0 and grp.get("bounding"):
            grp["bounding"] = [v / scale for v in grp["bounding"]]
        groups.append(grp)
    links = {}
    for l in raw.get("links") or []:
        if l is None:
            continue
        link = _link_from_array(l) if isinstance(l, list) else _link_from_object(l)
        links[link["id"]] = link
    return {
        "nodes": nodes, "order": order, "links": links,
        "groups": groups,
        "inputs": raw.get("inputs") or [], "outputs": raw.get("outputs") or [],
        "extra": raw.get("extra") or {},
        "name": raw.get("name"),
    }


def _collect_definitions(raw, out):
    for sg in ((raw.get("definitions") or {}).get("subgraphs") or []):
        if sg["id"] not in out:
            out[sg["id"]] = sg
        _collect_definitions(sg, out)


def load(path_or_dict):
    raw = path_or_dict
    if not isinstance(raw, dict):
        with open(raw, encoding="utf-8") as f:
            raw = json.load(f)
    if "nodes" not in raw:
        raise ValueError("not a UI-format workflow (no nodes). If it is in API format, open it in ComfyUI and save it again")
    extra = raw.get("extra") or {}
    scale = VUE_SCALE if extra.get("workflowRendererVersion") == "Vue" else 1.0
    defs = {}
    _collect_definitions(raw, defs)
    graphs = {"root": _normalize_graph(raw, scale)}
    for sid, sg in defs.items():
        # A subgraph uses its own extra first and falls back to the top level (as the frontend does)
        sv = (sg.get("extra") or {}).get("workflowRendererVersion")
        sscale = scale if sv is None else (VUE_SCALE if sv == "Vue" else 1.0)
        graphs[sid] = _normalize_graph(sg, sscale)
    _dedupe_subgraph_node_ids(raw, graphs)
    return {"raw": raw, "graphs": graphs, "version": raw.get("version")}


def _dedupe_subgraph_node_ids(raw, graphs):
    """When a node id inside a subgraph collides with the top level or another subgraph, the frontend gives it
    a new id on load. Do the same, so that execution ids match."""
    state = raw.get("state") or {}
    last = state.get("lastNodeId", raw.get("last_node_id", 0)) or 0
    used = set(graphs["root"]["order"])
    used_num = {int(i) for i in used if i.lstrip("-").isdigit()}
    remaps = {}
    for gid, g in graphs.items():
        if gid == "root":
            continue
        remap = {}
        for nid in list(g["order"]):
            if nid in used:
                while True:
                    last += 1
                    if last not in used_num:
                        break
                new = str(last)
                remap[nid] = new
                used.add(new)
                used_num.add(last)
            else:
                used.add(nid)
                if nid.lstrip("-").isdigit():
                    used_num.add(int(nid))
                    last = max(last, int(nid))
        if not remap:
            continue
        remaps[gid] = remap
        g["order"] = [remap.get(n, n) for n in g["order"]]
        nodes = {}
        for nid, n in g["nodes"].items():
            n["id"] = remap.get(nid, nid)
            nodes[n["id"]] = n
        g["nodes"] = nodes
        for l in g["links"].values():
            l["origin_id"] = remap.get(l["origin_id"], l["origin_id"])
            l["target_id"] = remap.get(l["target_id"], l["target_id"])
    for g in graphs.values():
        for n in g["nodes"].values():
            remap = remaps.get(n.get("type"))
            proxy = (n.get("properties") or {}).get("proxyWidgets")
            if remap and isinstance(proxy, list):
                for e in proxy:
                    if isinstance(e, list) and str(e[0]) in remap:
                        e[0] = remap[str(e[0])]


def input_link_map(node):
    """{input name: link id} (only inputs that have a link)."""
    return {i["name"]: i["link"] for i in node.get("inputs") or [] if i.get("link") is not None}


def input_index(node, name):
    for k, i in enumerate(node.get("inputs") or []):
        if i["name"] == name:
            return k
    return None


def target_input_name(graph, link):
    """Name of the input a link goes into, looked up from the node's inputs[].link rather than target_slot."""
    node = graph["nodes"].get(link["target_id"])
    if node is None:
        return None
    for i in node.get("inputs") or []:
        if i.get("link") == link["id"]:
            return i["name"]
    # A link that no input of the node refers to is dropped. When two links go into the same input,
    # the frontend keeps the one the input refers to.
    return None
