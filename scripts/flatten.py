"""Expand subgraphs and wireless connections into a flat graph. Python standard library only.

What it does:
- Expands subgraphs. Inner node ids take the "outer:inner" form, the same as the frontend's execution ids.
- Writes promoted widget values (the instance's widgets_values, or the older proxyWidgets) into the inner nodes.
- Turns wireless connections back into links: KJNodes Set/Get, Easy-Use set/get, Anything Everywhere.
- Removes legacy Reroute nodes (core, rgthree) and reconnects their links. Native reroutes (display only) are dropped.
- Removes nodes that only change other nodes' mode, such as rgthree's Muter / Bypasser (their effect is
  already in the saved modes).

What it does not do: muted and bypassed nodes are kept (whether to split them off is the agent's call).
PrimitiveNode is a visible link, so it is kept (replacing it with a typed value node, or moving the value back
into a widget, is done by replace.py).
What it drops: positions, sizes, colours, groups, subgraph nesting, and titles the author gave (only the
meaning is taken, so the old layout does not bias the new one).
Anything Everywhere's group and colour restrictions are still computed on the original graph, before
anything is dropped (ue.py).
Group names and author titles are not used for layout; they are kept separately in author_words as
material for Notes (not attached to nodes).

Shape of the flat graph:
    {"nodes": [node, ...], "links": [link, ...], "warnings": [...], "author_words": {...}}
    node: the original node dict without layout information (pos, size, color, bgcolor, title, flags, order,
          slot labels), plus
        "id": execution id (str), "scope": path of the graph it belonged to ("" is the top level),
        "widgets": {name: value} or null (type unknown), "widgets_exact": whether the positional mapping is exact,
        "pack": "core" / "custom:<dir>" / "frontend" / "unknown"
    node["inputs"][k]["link"] and node["outputs"][k]["links"] refer to link ids of the flat graph.
    link: {"id", "origin_id", "origin_slot", "target_id", "target_input"(name), "type"}
    author_words: the author's words (material for Notes; not used for layout)
        "titles":    [{"id", "type", "title"}]  titles the author gave (ones equal to the display name or type are left out)
        "groups":    [{"title", "scope", "nodes": [id, ...]}]  groups and the nodes that were in them
                     (as in the frontend, nodes whose rectangle centre lies in the group; nested groups both count)
        "subgraphs": [{"scope", "title", "nodes": [id, ...]}]  subgraph titles (instance title or definition name) and their nodes
        nodes lists only nodes left after expansion (Reroutes and Set/Get are gone).

Mode handling (differs from the frontend):
- The frontend does not stop the contents of a nested subgraph node that is muted or bypassed (only the top
  level is stopped). Here the instance's mode is copied to inner nodes at any depth (to match the author's intent).
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comfy_schema  # noqa: E402
import read_workflow as rw  # noqa: E402

REROUTE_TYPES = {"Reroute", "Reroute (rgthree)"}
SET_TYPES = {"SetNode": "kj", "easy setNode": "easy"}
GET_TYPES = {"GetNode": "kj", "easy getNode": "easy"}
MODE_CONTROL_TYPES = {
    "Fast Groups Muter (rgthree)", "Fast Groups Bypasser (rgthree)", "Fast Muter (rgthree)",
    "Fast Bypasser (rgthree)", "Mute / Bypass Relay (rgthree)", "Mute / Bypass Repeater (rgthree)",
    "Random Unmuter (rgthree)", "Node Collector (rgthree)", "Bookmark (rgthree)", "Fast Actions Button (rgthree)",
}
UE_PREFIX = "Anything Everywhere"
# Layout information to drop (only the meaning is kept)
LAYOUT_KEYS = ("pos", "size", "color", "bgcolor", "title", "flags", "order", "shape", "boxcolor")
SLOT_LAYOUT_KEYS = ("label", "pos", "slot_index")
UE_TYPES = {"Prompts Everywhere", "Seed Everywhere"}


class Flattener:
    def __init__(self, wf, object_info):
        self.wf = wf
        self.graphs = wf["graphs"]
        self.oi = object_info
        self.nodes = {}  # execution id -> node
        self.order = []
        self.links = {}
        self.next_link = 1
        self.warnings = []

    # ---- basics ----
    def warn(self, msg):
        self.warnings.append(msg)

    def is_instance(self, node):
        return node.get("type") in self.graphs and node.get("type") != "root"

    @staticmethod
    def eid(path, nid):
        return ":".join(list(path) + [str(nid)])

    def add_link(self, origin_id, origin_slot, target_id, target_input, ltype):
        lid = self.next_link
        self.next_link += 1
        self.links[lid] = {"id": lid, "origin_id": origin_id, "origin_slot": origin_slot,
                           "target_id": target_id, "target_input": target_input, "type": ltype}
        return lid

    # ---- expanding subgraphs ----
    def collect_nodes(self, gid, path, inherited_mode):
        g = self.graphs[gid]
        for nid in g["order"]:
            node = g["nodes"][nid]
            if self.is_instance(node):
                mode = node.get("mode", 0)
                mode = inherited_mode if mode == 0 else mode
                self.collect_nodes(node["type"], path + [nid], mode)
                continue
            n = json.loads(json.dumps(node))
            n["id"] = self.eid(path, nid)
            n["scope"] = ":".join(path)
            if inherited_mode and n.get("mode", 0) == 0:
                n["mode"] = inherited_mode
                # A branch muted or bypassed as a whole subgraph. The frontend bypasses it at the instance's inputs
                # and outputs; here each inner node is stopped, and marked so the agent can tell it is one branch
                n["mode_from_subgraph"] = path[-1] if path else None
            for i in n.get("inputs") or []:
                i["link"] = None
            for o in n.get("outputs") or []:
                o["links"] = []
            n["pack"] = comfy_schema.pack_of(n.get("type"), self.oi)
            self.nodes[n["id"]] = n
            self.order.append(n["id"])

    def resolve_origin(self, gid, path, origin_id, origin_slot):
        """Map an output end inside graph gid (at path) to an output end of a real node in the flat graph.
        Returns (execution id, slot) or None."""
        g = self.graphs[gid]
        if origin_id == rw.SUBGRAPH_INPUT_ID:
            # a subgraph input: follow the link into the outer instance's input
            if not path:
                return None
            parent_path, inst_id = path[:-1], path[-1]
            parent_gid = self.scope_gid[":".join(parent_path)]
            inst = self.graphs[parent_gid]["nodes"][inst_id]
            sg_input = g["inputs"][origin_slot] if origin_slot < len(g["inputs"]) else None
            if sg_input is None:
                return None
            link_id = rw.input_link_map(inst).get(sg_input["name"])
            if link_id is None:
                return None
            link = self.graphs[parent_gid]["links"].get(link_id)
            if link is None:
                return None
            return self.resolve_origin(parent_gid, parent_path, link["origin_id"], link["origin_slot"])
        node = g["nodes"].get(origin_id)
        if node is None:
            return None
        if self.is_instance(node):
            # The inner link feeding a subgraph output is the first one, in links order, listed in the output's linkIds
            # (a link's target_slot can be broken)
            sg = self.graphs[node["type"]]
            cands = []
            if origin_slot < len(sg["outputs"]):
                ids = set(sg["outputs"][origin_slot].get("linkIds") or [])
                cands = [l for l in sg["links"].values() if l["id"] in ids]  # first in links order
            if not cands:
                cands = [l for l in sg["links"].values()
                         if l["target_id"] == rw.SUBGRAPH_OUTPUT_ID and l["target_slot"] == origin_slot]
            if cands:
                link = cands[0]
                return self.resolve_origin(node["type"], path + [origin_id], link["origin_id"], link["origin_slot"])
            return None
        return (self.eid(path, origin_id), origin_slot)

    def build_links(self):
        for scope, gid in self.scope_gid.items():
            path = scope.split(":") if scope else []
            g = self.graphs[gid]
            for link in g["links"].values():
                tnode = g["nodes"].get(link["target_id"])
                if tnode is None or self.is_instance(tnode):
                    continue  # links into -20 or into an instance are resolved from the inside / outside
                target_name = rw.target_input_name(g, link)
                origin = self.resolve_origin(gid, path, link["origin_id"], link["origin_slot"])
                if origin is None or target_name is None:
                    continue
                tid = self.eid(path, link["target_id"])
                self.connect(origin, tid, target_name, link["type"])

    def connect(self, origin, target_id, target_name, ltype):
        oid, oslot = origin
        if oid not in self.nodes or target_id not in self.nodes:
            return None
        tnode = self.nodes[target_id]
        idx = rw.input_index(tnode, target_name)
        if idx is None:
            return None
        onode = self.nodes[oid]
        outs = onode.get("outputs") or []
        if oslot >= len(outs):
            return None
        old = tnode["inputs"][idx].get("link")
        if old is not None:
            self.disconnect(old)
        lid = self.add_link(oid, oslot, target_id, target_name, ltype)
        tnode["inputs"][idx]["link"] = lid
        outs[oslot].setdefault("links", []).append(lid)
        return lid

    def disconnect(self, lid):
        link = self.links.pop(lid, None)
        if link is None:
            return
        t = self.nodes.get(link["target_id"])
        if t:
            for i in t.get("inputs") or []:
                if i.get("link") == lid:
                    i["link"] = None
        o = self.nodes.get(link["origin_id"])
        if o:
            outs = o.get("outputs") or []
            if link["origin_slot"] < len(outs):
                ls = outs[link["origin_slot"]].get("links") or []
                if lid in ls:
                    ls.remove(lid)

    def remove_node(self, nid):
        n = self.nodes.get(nid)
        if n is None:
            return
        for i in n.get("inputs") or []:
            if i.get("link") is not None:
                self.disconnect(i["link"])
        for o in n.get("outputs") or []:
            for lid in list(o.get("links") or []):
                self.disconnect(lid)
        del self.nodes[nid]
        self.order.remove(nid)

    def map_scopes(self):
        """scope (path string) -> graph id."""
        self.scope_gid = {"": "root"}

        def walk(gid, path):
            for nid in self.graphs[gid]["order"]:
                node = self.graphs[gid]["nodes"][nid]
                if self.is_instance(node):
                    p = path + [nid]
                    self.scope_gid[":".join(p)] = node["type"]
                    walk(node["type"], p)
        walk("root", [])

    # ---- widget values ----
    def widget_map(self, node):
        return comfy_schema.map_widget_values(node.get("type"), node.get("widgets_values"), self.oi,
                                              node.get("widgets_values_named"))

    def set_widget(self, nid, name, value):
        node = self.nodes.get(nid)
        if node is None:
            return False
        wv = node.get("widgets_values")
        if isinstance(wv, dict):
            wv[name] = value
            return True
        info = self.oi.get(node.get("type"))
        if info is None or not isinstance(wv, list):
            self.warn(f"{nid} {node.get('type')}: cannot write a value to widget {name} (type unknown)")
            return False
        names = comfy_schema.widget_names(info, wv)
        if name not in names or names.index(name) >= len(wv):
            self.warn(f"{nid} {node.get('type')}: position of widget {name} unknown")
            return False
        wv[names.index(name)] = value
        named = node.get("widgets_values_named")
        if isinstance(named, dict) and name in named:
            named[name] = value
        return True

    def push_value(self, gid, path, node_id, input_name, value, vtype=None):
        """Put a widget value into input input_name of node_id in graph gid. For an instance, push it inside.
        When it reaches an input without a widget (PreviewAny.source, etc.), add a Primitive node that outputs
        the value and connect it (the frontend writes the value straight into the prompt; the flat graph shows it as a link)."""
        node = self.graphs[gid]["nodes"].get(node_id)
        if node is None:
            return
        if self.is_instance(node):
            sg = self.graphs[node["type"]]
            for k, sgi in enumerate(sg["inputs"]):
                if sgi["name"] != input_name:
                    continue
                for link in sg["links"].values():
                    if link["origin_id"] == rw.SUBGRAPH_INPUT_ID and link["origin_slot"] == k:
                        tname = rw.target_input_name(sg, link)
                        tnode = sg["nodes"].get(link["target_id"])
                        if tnode is None or tname is None:
                            continue
                        self.push_value(node["type"], path + [node_id], link["target_id"], tname, value, sgi.get("type"))
            return
        nid = self.eid(path, node_id)
        if any(i["name"] == input_name and i.get("widget") for i in node.get("inputs") or []) or \
                input_name in comfy_schema.widget_names(self.oi.get(node.get("type")) or {}, node.get("widgets_values")):
            self.set_widget(nid, input_name, value)
        else:
            self.add_value_source(nid, input_name, value, vtype)

    def apply_promoted_widgets(self):
        for scope, gid in self.scope_gid.items():
            if not scope:
                continue
            path = scope.split(":")
            parent_gid = self.scope_gid[":".join(path[:-1])]
            inst = self.graphs[parent_gid]["nodes"][path[-1]]
            values = inst.get("widgets_values")
            values = values if isinstance(values, list) else []
            linked = rw.input_link_map(inst)
            proxy = (inst.get("properties") or {}).get("proxyWidgets")
            sg = self.graphs[gid]
            if proxy and values:
                for (entry, value) in zip(proxy, values):
                    src, wname = str(entry[0]), entry[1]
                    wname = re.sub(r"^\d+:\s*", "", wname)
                    if src == "-1":
                        if wname not in linked:
                            self.push_value(parent_gid, path[:-1], path[-1], wname, value)
                    elif src in sg["nodes"]:
                        self.push_value(gid, path, src, wname, value)
                continue
            # Newer form: only the subgraph inputs that have a widget, in the definition's input order.
            # The instance's inputs can be packed by Export, so the definition's inputs are used.
            widget_inputs = [i for i in sg["inputs"] if self.subgraph_input_has_widget(gid, i)]
            if values and len(widget_inputs) != len(values):
                self.warn(f"subgraph {scope}: number of promoted widgets ({len(widget_inputs)}) does not match number of values ({len(values)})")
            for k, sgi in enumerate(widget_inputs):
                if sgi["name"] in linked:
                    continue
                if k < len(values):
                    # the frontend applies null values too
                    value = values[k]
                else:
                    # without a value on the instance, the subgraph input takes the current value of the first widget it feeds (as the frontend does)
                    found, value = self.first_target_widget_value(gid, path, sgi)
                    if not found:
                        continue
                self.push_value(parent_gid, path[:-1], path[-1], sgi["name"], value)

    def first_target_widget_value(self, gid, path, sg_input):
        sg = self.graphs[gid]
        for lid in sg_input.get("linkIds") or []:
            link = sg["links"].get(lid)
            if link is None:
                continue
            tnode = sg["nodes"].get(link["target_id"])
            tname = rw.target_input_name(sg, link)
            if tnode is None or tname is None:
                continue
            if self.is_instance(tnode):
                inner = next((i for i in self.graphs[tnode["type"]]["inputs"] if i["name"] == tname), None)
                if inner is not None:
                    found, v = self.first_target_widget_value(tnode["type"], path + [link["target_id"]], inner)
                    if found:
                        return True, v
                continue
            mapping = self.widget_map(self.nodes.get(self.eid(path, link["target_id"])) or {})[0] or {}
            if tname in mapping:
                return True, mapping[tname]
        return False, None

    PRIMITIVE_FOR = {"INT": "PrimitiveInt", "FLOAT": "PrimitiveFloat", "STRING": "PrimitiveStringMultiline",
                     "BOOLEAN": "PrimitiveBoolean"}

    def add_value_source(self, target_id, input_name, value, vtype):
        """Add and connect a Primitive node that outputs the value, to pass a value to an input without a widget."""
        if target_id not in self.nodes:
            return
        tnode = self.nodes[target_id]
        idx = rw.input_index(tnode, input_name)
        if idx is not None and tnode["inputs"][idx].get("link") is not None:
            return  # already linked (e.g. the same value pushed twice)
        ptype = self.PRIMITIVE_FOR.get(vtype)
        if ptype is None:
            self.warn(f"{target_id}: no core node can pass value {value!r} to input {input_name} (type {vtype})")
            return
        nid = f"{target_id}~{input_name}"
        wv = [value, "fixed"] if ptype == "PrimitiveInt" else [value]
        n = {"id": nid, "type": ptype, "mode": 0,
             "inputs": [], "outputs": [{"name": vtype, "type": vtype, "links": []}],
             "widgets_values": wv, "properties": {}, "scope": tnode["scope"],
             "added_by": "promoted widget value of a subgraph", "pack": "core"}
        self.nodes[nid] = n
        self.order.insert(self.order.index(target_id), nid)
        self.connect((nid, 0), target_id, input_name, vtype)

    def subgraph_input_has_widget(self, gid, sg_input):
        """Whether the (first found) target of a subgraph input is an input with a widget (as the frontend decides it)."""
        sg = self.graphs[gid]
        for lid in sg_input.get("linkIds") or []:
            link = sg["links"].get(lid)
            if link is None:
                continue
            tnode = sg["nodes"].get(link["target_id"])
            tname = rw.target_input_name(sg, link)
            if tnode is None or tname is None:
                continue
            if self.is_instance(tnode):
                inner = next((i for i in self.graphs[tnode["type"]]["inputs"] if i["name"] == tname), None)
                if inner is not None and self.subgraph_input_has_widget(tnode["type"], inner):
                    return True
                continue
            if any(i["name"] == tname and i.get("widget") for i in tnode.get("inputs") or []):
                return True
            info = self.oi.get(tnode.get("type"))
            if info and tname in comfy_schema.widget_names(info, tnode.get("widgets_values")):
                return True  # a widget input, missing from inputs because Export packed them
        return False

    # ---- wireless and virtual nodes ----
    def resolve_reroutes(self):
        for nid in [n for n in self.order if self.nodes[n].get("type") in REROUTE_TYPES]:
            muted = self.nodes[nid].get("mode") == 2
            self.bridge(nid, 0, cut=muted, reason="Reroute is muted" if muted else None)

    def bridge(self, nid, in_slot, cut=False, source_override=None, reason=None):
        """Reconnect the output links of virtual node nid to the upstream of input in_slot, then remove nid.
        When they cannot be reconnected, leave cut_by (what cut the link) on the downstream inputs.
        Whether it is a muted branch is the agent's call."""
        n = self.nodes[nid]
        src = source_override
        if src is None and not cut:
            ins = n.get("inputs") or []
            if in_slot < len(ins) and ins[in_slot].get("link") is not None:
                l = self.links[ins[in_slot]["link"]]
                src = (l["origin_id"], l["origin_slot"])
        outgoing = [self.links[l] for o in n.get("outputs") or [] for l in (o.get("links") or [])]
        self.remove_node(nid)
        if src is None:
            for l in outgoing:
                t = self.nodes.get(l["target_id"])
                idx = rw.input_index(t, l["target_input"]) if t else None
                if idx is not None:
                    t["inputs"][idx]["cut_by"] = {"type": n.get("type"), "id": nid, "mode": n.get("mode", 0),
                                                  "reason": reason or "no upstream"}
            return
        for l in outgoing:
            self.connect(src, l["target_id"], l["target_input"], l["type"])

    def resolve_set_get(self):
        sets = {}
        for nid in self.order:
            n = self.nodes[nid]
            kind = SET_TYPES.get(n.get("type"))
            if kind:
                name = (n.get("widgets_values") or [None])[0]
                sets.setdefault((kind, name), []).append(nid)
        for nid in [n for n in self.order if self.nodes[n].get("type") in GET_TYPES]:
            n = self.nodes[nid]
            kind = GET_TYPES[n["type"]]
            name = (n.get("widgets_values") or [None])[0]
            cands = sets.get((kind, name), [])
            setter = self._pick_setter(n["scope"], cands, kind)
            src, reason = None, None
            if n.get("mode", 0) in (2, 4):
                reason = "Get is muted or bypassed"
            elif setter is None:
                reason = "no Set with the same name"
                self.warn(f"Get {name!r} ({nid}): {reason}")
            else:
                ins = self.nodes[setter].get("inputs") or []
                if ins and ins[0].get("link") is not None:
                    l = self.links[ins[0]["link"]]
                    src = (l["origin_id"], l["origin_slot"])
                else:
                    reason = "the Set's input is not connected"
                    self.warn(f"Get {name!r} ({nid}): {reason}")
            self.bridge(nid, 0, cut=src is None, source_override=src, reason=reason)
        # Links from the Set node's own output (which passes its input through) are also reconnected to the
        # source of the Set's input before the Set is removed (as the frontend does)
        for ids in sets.values():
            for nid in ids:
                if nid in self.nodes:
                    muted = self.nodes[nid].get("mode", 0) == 2
                    self.bridge(nid, 0, cut=muted, reason="Set is muted" if muted else None)

    def _pick_setter(self, scope, cands, kind):
        same = [c for c in cands if self.nodes[c]["scope"] == scope]
        if same:
            return same[0]
        if kind == "easy":
            return None
        parts = scope.split(":") if scope else []
        ancestors = [":".join(parts[:k]) for k in range(len(parts) - 1, -1, -1)]
        in_anc = [c for c in cands if self.nodes[c]["scope"] in ancestors]
        if len(in_anc) == 1:
            return in_anc[0]
        if len(in_anc) > 1:
            self.warn(f"Set name used more than once in ancestor graphs: {[self.nodes[c].get('widgets_values') for c in in_anc]}")
        return None

    def remove_mode_controllers(self):
        for nid in [n for n in self.order if self.nodes[n].get("type") in MODE_CONTROL_TYPES]:
            self.remove_node(nid)

    # ---- Anything Everywhere ----
    def resolve_anything_everywhere(self):
        import ue
        ue.resolve(self)

    def remove_ue_nodes(self):
        import ue
        for nid in [n for n in self.order if ue.is_ue(self.nodes[n])]:
            self.remove_node(nid)

    # ---- the author's words (material for Notes) ----
    def collect_author_words(self):
        """Collect group names and author titles from the original graph (which still has positions). Not used for layout."""
        titles, groups, subgraphs = [], [], []
        for scope, gid in self.scope_gid.items():
            path = scope.split(":") if scope else []
            g = self.graphs[gid]
            for nid in g["order"]:
                node = g["nodes"][nid]
                t = node.get("title")
                if not t or self.is_instance(node):
                    continue
                info = self.oi.get(node.get("type")) or {}
                if t in (node.get("type"), info.get("display_name")):
                    continue  # default title (not one the author gave)
                titles.append({"id": self.eid(path, nid), "type": node.get("type"), "title": t})
            for grp in g.get("groups") or []:
                b = grp.get("bounding")
                if not b or len(b) < 4:
                    continue
                members = []
                for nid in g["order"]:
                    c = self._node_centre(g["nodes"][nid])
                    if c and b[0] <= c[0] <= b[0] + b[2] and b[1] <= c[1] <= b[1] + b[3]:
                        members.append(self.eid(path, nid))
                groups.append({"title": grp.get("title") or "", "scope": scope, "members": members})
            if scope:
                parent = self.graphs[self.scope_gid[":".join(path[:-1])]]
                inst = parent["nodes"][path[-1]]
                t = inst.get("title") or g.get("name") or ""
                subgraphs.append({"scope": scope, "title": t, "name": g.get("name") or "", "members": [scope]})
        self.author_words = {"titles": titles, "groups": groups, "subgraphs": subgraphs}

    @staticmethod
    def _xy(v):
        if isinstance(v, dict):
            return [v.get("0", 0), v.get("1", 0)]
        return list(v) if isinstance(v, (list, tuple)) and len(v) >= 2 else None

    def _node_centre(self, node):
        """Centre of a node's rectangle (including the title bar), the way the frontend decides which nodes are in a group.
        A collapsed node's width depends on its title's text width, which cannot be measured here, so the
        frontend's default collapsed width (80) is used."""
        pos, size = self._xy(node.get("pos")), self._xy(node.get("size"))
        if pos is None or size is None:
            return None
        th = 0 if node.get("type") in REROUTE_TYPES else 30
        if (node.get("flags") or {}).get("collapsed"):
            w, h = 80, th
        else:
            w, h = size[0], size[1] + th
        return (pos[0] + w / 2, pos[1] - th + h / 2)

    def finish_author_words(self):
        """Rewrite into ids of nodes left after expansion (an instance becomes all its inner nodes)."""
        aw = self.author_words

        def expand(ids):
            out = []
            for i in ids:
                if i in self.nodes:
                    out.append(i)
                else:
                    out += [n for n in self.order if n.startswith(i + ":")]
            return [n for n in dict.fromkeys(out) if n in self.nodes]
        aw["titles"] = [t for t in aw["titles"] if t["id"] in self.nodes]
        for key in ("groups", "subgraphs"):
            for grp in aw[key]:
                grp["nodes"] = expand(grp.pop("members"))
        return aw

    def run(self):
        self.map_scopes()
        self.collect_author_words()
        # UE is resolved on the saved graph (subgraph nodes can be receivers, and Get / Reroute outputs can be sources)
        self.resolve_anything_everywhere()
        self.collect_nodes("root", [], 0)
        self.build_links()
        self.apply_promoted_widgets()
        self.remove_ue_nodes()
        self.resolve_reroutes()
        self.resolve_set_get()
        self.remove_mode_controllers()
        for nid in self.order:
            n = self.nodes[nid]
            n["widgets"], n["widgets_exact"] = self.widget_map(n)
            # The size of a custom node that is not installed in ComfyUI cannot be computed. Keep only the size
            # it had when the author opened it with the node installed (saved in the original workflow), so the
            # layout never makes it smaller than that (position and colour are still dropped)
            size = self._xy(n.get("size"))
            if size and n.get("type") not in self.oi and n.get("type") not in REROUTE_TYPES \
                    and not (n.get("flags") or {}).get("collapsed"):
                n["orig_size"] = size
            for key in LAYOUT_KEYS:
                n.pop(key, None)
            for slot in (n.get("inputs") or []) + (n.get("outputs") or []):
                for key in SLOT_LAYOUT_KEYS:
                    slot.pop(key, None)
        return {
            "nodes": [self.nodes[n] for n in self.order],
            "links": sorted(self.links.values(), key=lambda l: l["id"]),
            "warnings": self.warnings,
            "author_words": self.finish_author_words(),
        }


def flatten(wf, object_info):
    return Flattener(wf, object_info).run()
