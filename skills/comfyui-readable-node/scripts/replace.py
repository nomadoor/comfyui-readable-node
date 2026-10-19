"""Replace outdated nodes in a flat graph, in place. Python standard library only.

What the code replaces:
1. Nodes in ComfyUI's official replacement list (GET /api/node_replacements), exactly as the list says.
   - The list is fetched from the same server as object_info. With a saved object_info file there is no list,
     and step 1 is skipped (the caller reports it).
   - If the replacement is itself in the list, it is replaced again. If the replacement is deprecated, it shows
     up among the deprecated nodes (the agent decides).
2. Replacement by a newer node with the same computation (SAME_COMPUTATION). Only pairs whose computation was
   checked to be the same in the ComfyUI source.
2b. Replacement of a custom node by a core node that does the same job (CORE_REPLACEMENTS: Image Comparer (rgthree)
   by ImageCompare). Recorded with by "core_node".

How list entries are read (behaviour matched to ComfyUI's server and frontend):
- input_mapping: {"new_id", "old_id"} copies an old input (a link or a widget value) to a new input.
  {"new_id", "set_value"} sets a value. Inputs not listed are not copied (the new node's default is used and
  the link is cut).
- A "parent.child" new_id is a DynamicCombo child widget (resize_type.multiplier) or an Autogrow input
  (images.image0). It is written the same way as widget and input names in the flat graph, so it is copied as is.
  (The frontend's replacement skips new_ids containing ".", so replacing in the frontend loses values such as
  scale_by. The server's apply_replacements copies them; this module does the same as the server.)
- output_mapping: {"old_idx", "new_idx"}. Links from outputs not listed are cut. null keeps the same output index.
- If input_mapping and output_mapping are both null, inputs, widgets and outputs with the same names are copied
  (as the frontend's default mapping does).
- old_widget_ids: names for the positions of the old node's widgets_values. Used when the old type is not in
  object_info (e.g. a replacement that fixes a typo in a node name).

A replaced node keeps its id, mode and properties (properties["Node name for S&R"] becomes the new type).
Each replacement is recorded:
    {"id", "from", "to", "by": "node_replacements" / "same_computation" / "core_node" (also "primitive" for 3 and
     "same_loader" for 4 below), "set_value": {input: value} (values set by the list),
     "dropped_values": {old widget: value} (values not copied), "dropped_links": [descriptions of cut links]}

After replacing, the types of links into and out of replaced nodes are checked with validate.py; failures
become warnings.

3. The frontend's PrimitiveNode (an untyped value node; deprecated). Its behaviour, matched to the frontend:
   it writes its value into the widget it is connected to. Numbers and combos get a control widget ("fixed"
   by default when the target input has no control_after_generate; seed-like inputs use that input's control).
   widgets_values is [value, control, (filter for combos)].
   - Connected to one widget of one node: the value goes back into that widget and the PrimitiveNode is removed.
     When control is not "fixed", the target's control widget gets the value too; if the target has none, the
     value cannot be moved back (the next case applies). It is not moved back either when the target's widget
     order is not certain (unknown type, or widgets_exact is false).
   - Connected to two or more: replaced by a typed core value node (PRIMITIVE_TYPED; same value, same links).
     PrimitiveInt has a control widget (the spec's control_after_generate "fixed" becomes both the widget name
     and its default), so the control is copied. PrimitiveFloat, PrimitiveString and PrimitiveBoolean have no
     control, so they are used only when the control is "fixed". STRING becomes PrimitiveStringMultiline when
     any target input is multiline.
   - No core node outputs a COMBO value (CustomCombo outputs STRING and INT), so a COMBO connected to two or
     more is kept, with a warning.
   Recorded as {"id", "from": "PrimitiveNode", "to": value node type or null, "by": "primitive",
   "into": [{"id", "widget"}] (where the value went), "value", "control"}.

4. Duplicate loaders (two or more loaders with the same type, the same widget values and the same mode) are
   merged into one, and the links come from the one kept.
   - A loader is a node with no linked inputs whose widget values include a model file name (MODEL_EXT).
     Value nodes without inputs (PrimitiveInt, ImpactInt, etc.) are not merged: equal values can mean
     different things (width and height).
   - The one kept is the first in the flat graph. properties.models of removed nodes are added to it.
     Node ids in the author's words (author_words) groups are rewritten to the one kept.
   - Recorded as {"id": kept id, "from": type, "to": type, "by": "same_loader",
     "merged": [{"id", "title"}] (the ones merged and removed)}.

Not replaced here (the agent decides):
- Deprecated nodes (deprecated: true in object_info). Check the successor in the source comments, description
  and display name. If the number or meaning of inputs and outputs differs, the links need redoing.
- Nodes that do not meet the SAME_COMPUTATION conditions (with the reason).
"""

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comfy_schema  # noqa: E402
import validate  # noqa: E402

TOTAL_PIXELS_UNIT = 1024 * 1024


def _total_pixels_ok(node):
    """Whether ImageScaleToTotalPixels computes the same as ResizeImageMaskNode's "scale total pixels".
    In ComfyUI, ImageScaleToTotalPixels uses total = megapixels * 1024 * 1024 and sets width and height to
    round(... / resolution_steps) * resolution_steps; scale_total_pixels uses total = int(megapixels * 1024 * 1024).
    They agree only when resolution_steps is 1 and megapixels * 1024 * 1024 is an integer. Returns (same, reason)."""
    w = node.get("widgets") or {}
    linked = {i["name"] for i in node.get("inputs") or [] if i.get("link") is not None}
    if "resolution_steps" in linked or "megapixels" in linked:
        return False, "resolution_steps or megapixels comes in through a link (value unknown)"
    if w.get("resolution_steps") != 1:
        return False, f"resolution_steps is {w.get('resolution_steps')} (the computation is the same only when it is 1)"
    mp = w.get("megapixels")
    if not isinstance(mp, (int, float)) or float(mp) * TOTAL_PIXELS_UNIT != int(float(mp) * TOTAL_PIXELS_UNIT):
        return False, f"megapixels {mp} x 1024 x 1024 is not an integer (the new node truncates with int, so width and height can be off by 1px)"
    return True, None


# Replacements by a newer node with the same computation. The official list already replaces a node of the
# same family (ImageScaleBy) with ResizeImageMaskNode. That the computation is the same was checked in the ComfyUI source:
# - ImageScale.upscale (nodes.py) and scale_dimensions (comfy_extras/nodes_post_processing.py) do the same thing
#   (if width or height is 0 it follows from the aspect ratio; crop is passed to common_upscale). The crop default
#   is disabled in the old node and center in the new one, so the value is always copied.
# - ImageScaleToMaxDimension.execute (comfy_extras/nodes_images.py) and scale_longer_dimension do the same thing.
# - ImageScaleToTotalPixels is the same only under the conditions in _total_pixels_ok.
SAME_COMPUTATION = {
    # ControlNetApplySD3 ("Apply Controlnet with VAE", deprecated with no successor named) and ControlNetApplyAdvanced
    # (nodes.py) run the same body: same inputs and outputs by name, vae optional in the newer node, extra_concat empty.
    "ControlNetApplySD3": {"new_node_id": "ControlNetApplyAdvanced", "input_mapping": None, "output_mapping": None},
    "ImageScale": {
        "new_node_id": "ResizeImageMaskNode",
        "input_mapping": [
            {"new_id": "input", "old_id": "image"},
            {"new_id": "resize_type", "set_value": "scale dimensions"},
            {"new_id": "resize_type.width", "old_id": "width"},
            {"new_id": "resize_type.height", "old_id": "height"},
            {"new_id": "resize_type.crop", "old_id": "crop"},
            {"new_id": "scale_method", "old_id": "upscale_method"},
        ],
        "output_mapping": [{"old_idx": 0, "new_idx": 0}],
    },
    "ImageScaleToMaxDimension": {
        "new_node_id": "ResizeImageMaskNode",
        "input_mapping": [
            {"new_id": "input", "old_id": "image"},
            {"new_id": "resize_type", "set_value": "scale longer dimension"},
            {"new_id": "resize_type.longer_size", "old_id": "largest_size"},
            {"new_id": "scale_method", "old_id": "upscale_method"},
        ],
        "output_mapping": [{"old_idx": 0, "new_idx": 0}],
    },
    "ImageScaleToTotalPixels": {
        "new_node_id": "ResizeImageMaskNode",
        "input_mapping": [
            {"new_id": "input", "old_id": "image"},
            {"new_id": "resize_type", "set_value": "scale total pixels"},
            {"new_id": "resize_type.megapixels", "old_id": "megapixels"},
            {"new_id": "scale_method", "old_id": "upscale_method"},
        ],
        "output_mapping": [{"old_idx": 0, "new_idx": 0}],
        "condition": _total_pixels_ok,
        "drops_ok": {"resolution_steps"},  # replaced only when it is 1, so dropping it changes nothing
    },
}


# Custom nodes replaced by a core node that does the same job (recorded with by "core_node").
# - Image Comparer (rgthree) and ImageCompare (Compare Images, comfy_extras/nodes_image_compare.py) both only show
#   image_a and image_b side by side with a slider; neither has outputs. The links into image_a and image_b are kept.
#   rgthree's widget holds the images of the last run, not the author's values, so it is not copied (old_widget_ids is empty).
#   ImageCompare's compare_view is a socketless widget that saves no value: a workflow the frontend saves has only the
#   image_a and image_b inputs and widgets_values [], so the compare_view slot is not made (no_socket).
CORE_REPLACEMENTS = {
    "Image Comparer (rgthree)": {
        "new_node_id": "ImageCompare",
        "input_mapping": [
            {"new_id": "image_a", "old_id": "image_a"},
            {"new_id": "image_b", "old_id": "image_b"},
        ],
        "output_mapping": [],
        "old_widget_ids": [],
        "no_socket": {"compare_view"},
    },
}


# Model file extensions (same as notes.py). A node with no linked inputs and such a widget value counts as a loader
MODEL_EXT = (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".gguf", ".sft", ".onnx")


# PrimitiveNode output type -> typed core value node (comfy_extras/nodes_primitive.py)
PRIMITIVE_TYPED = {"INT": "PrimitiveInt", "FLOAT": "PrimitiveFloat", "STRING": "PrimitiveString",
                   "BOOLEAN": "PrimitiveBoolean"}


def load_replacements(source):
    """source is a URL (the same server as object_info, e.g. http://127.0.0.1:8188) or the path of a saved JSON."""
    if source.startswith("http://") or source.startswith("https://"):
        url = source.rstrip("/")
        for tail in ("/object_info", "/api/object_info"):
            if url.endswith(tail):
                url = url[: -len(tail)]
        if not url.endswith("/api/node_replacements"):
            url += "/api/node_replacements"
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    with open(source, encoding="utf-8") as f:
        return json.load(f)


class Replacer:
    def __init__(self, flat, oi, replacements):
        self.flat = flat
        self.oi = oi
        self.repl = replacements or {}
        self.nodes = {n["id"]: n for n in flat["nodes"]}
        self.links = {l["id"]: l for l in flat["links"]}
        self.records = []
        self.warnings = []

    def old_values(self, node, entry):
        """{widget name: value} of the old node: flatten's mapping if the type is in object_info, else by old_widget_ids positions."""
        if node.get("type") in self.oi and node.get("widgets") is not None:
            return dict(node["widgets"])
        wv = node.get("widgets_values")
        if isinstance(wv, dict):
            return dict(wv)
        ids = entry.get("old_widget_ids")
        if ids is None and entry.get("input_mapping") is None and entry.get("output_mapping") is None:
            # as the frontend's default mapping does: the new node's widget names are applied to the old widgets_values positions
            ids = comfy_schema.widget_names(self.oi[entry["new_node_id"]], wv)
        if not isinstance(wv, list) or not ids:
            return {}
        return {name: wv[k] for k, name in enumerate(ids) if k < len(wv)}

    def replace(self, nid, entry, by):
        node = self.nodes[nid]
        new_type = entry["new_node_id"]
        info = self.oi.get(new_type)
        if info is None:
            self.warnings.append(f"{nid} {node['type']}: replacement {new_type} is not in object_info; not replaced")
            return False
        old_vals = self.old_values(node, entry)
        in_map, out_map = entry.get("input_mapping"), entry.get("output_mapping")
        named, set_value, moves = {}, {}, {}
        if in_map is None and out_map is None:
            new_widgets = set(comfy_schema.widget_names(info, []))
            for name, v in old_vals.items():
                if name in new_widgets or name in ("control_after_generate",):
                    named[name] = v
            new_inputs = {n for n, _ in comfy_schema.input_slots(info, [], [i["name"] for i in node.get("inputs") or []])}
            moves = {i["name"]: i["name"] for i in node.get("inputs") or [] if i["name"] in new_inputs}
            new_out_names = info.get("output_name") or []
            out_pairs = {k: new_out_names.index(o.get("name")) for k, o in enumerate(node.get("outputs") or [])
                         if o.get("name") in new_out_names}
        else:
            for m in in_map or []:
                if "set_value" in m:
                    named[m["new_id"]] = m["set_value"]
                    set_value[m["new_id"]] = m["set_value"]
                elif "old_id" in m:
                    if m["old_id"] in old_vals:
                        named[m["new_id"]] = old_vals[m["old_id"]]
                    moves[m["old_id"]] = m["new_id"]
            out_pairs = None if out_map is None else {m["old_idx"]: m["new_idx"] for m in out_map}
        values = comfy_schema.build_widgets_values(info, named)
        saved = [moves[i["name"]] for i in node.get("inputs") or []
                 if i.get("link") is not None and i["name"] in moves]
        inputs, outputs = comfy_schema.new_node_slots(info, values, saved)
        inputs = [i for i in inputs if i["name"] not in (entry.get("no_socket") or ())]
        # outputs: when indices stay the same (out_pairs is None), the node cannot be replaced if the new node lacks that output (as in the frontend)
        old_outs = node.get("outputs") or []
        for k, o in enumerate(old_outs):
            if o.get("links") and out_pairs is None and k >= len(outputs):
                self.warnings.append(f"{nid} {node['type']} → {new_type}: cannot keep the links of output {k}; not replaced")
                return False
        dropped_links = []
        # move input links
        new_in = {i["name"]: i for i in inputs}
        for i in node.get("inputs") or []:
            lid = i.get("link")
            if lid is None:
                continue
            target = moves.get(i["name"])
            l = self.links.get(lid)
            if target is None or target not in new_in or l is None:
                dropped_links.append(f"link into input {i['name']} (from {l['origin_id'] if l else '?'})")
                self._disconnect(lid)
                continue
            new_in[target]["link"] = lid
            l["target_input"] = target
        # move output links
        for k, o in enumerate(old_outs):
            new_k = k if out_pairs is None else out_pairs.get(k)
            for lid in list(o.get("links") or []):
                l = self.links.get(lid)
                if l is None:
                    continue
                if new_k is None or new_k >= len(outputs):
                    dropped_links.append(f"link from output {k} ({o.get('name')}) (to {l['target_id']}.{l['target_input']})")
                    self._disconnect(lid)
                    continue
                l["origin_slot"] = new_k
                outputs[new_k]["links"].append(lid)
                if outputs[new_k]["type"] == "*":
                    outputs[new_k]["type"] = o.get("type") or "*"  # MATCHTYPE: the old output's type (set by what it connects to)
        used_old = {m.get("old_id") for m in in_map or []} if in_map is not None or out_map is not None else set(named)
        dropped_values = {k: v for k, v in old_vals.items()
                          if k not in used_old and k not in (entry.get("drops_ok") or ())
                          and k not in comfy_schema.NON_VALUE_WIDGETS}
        props = dict(node.get("properties") or {})
        if "Node name for S&R" in props:
            props["Node name for S&R"] = new_type
        old_type = node["type"]
        node.update({"type": new_type, "inputs": inputs, "outputs": outputs, "widgets_values": values,
                     "properties": props, "pack": comfy_schema.pack_of(new_type, self.oi)})
        node.pop("widgets_values_named", None)
        node["widgets"], node["widgets_exact"] = comfy_schema.map_widget_values(new_type, values, self.oi)
        rec = {"id": nid, "from": old_type, "to": new_type, "by": by}
        if set_value and by == "node_replacements":
            rec["set_value"] = set_value  # not recorded for same-computation replacements (there it only selects the computation)
        if dropped_values:
            rec["dropped_values"] = dropped_values
        if dropped_links:
            rec["dropped_links"] = dropped_links
        self.records.append(rec)
        return True

    def _disconnect(self, lid):
        l = self.links.pop(lid, None)
        if l is None:
            return
        self.flat["links"] = [x for x in self.flat["links"] if x["id"] != lid]
        for n in (self.nodes.get(l["origin_id"]), self.nodes.get(l["target_id"])):
            if n is None:
                continue
            for i in n.get("inputs") or []:
                if i.get("link") == lid:
                    i["link"] = None
            for o in n.get("outputs") or []:
                if lid in (o.get("links") or []):
                    o["links"].remove(lid)

    # ---- PrimitiveNode ----
    def _target_spec(self, node, widget):
        info = self.oi.get(node.get("type"))
        return comfy_schema.widget_spec(info, widget, node.get("widgets") or {}) if info else None

    def _set_widget(self, node, name, value):
        """Write a widget value. False if the widget order is not certain."""
        info = self.oi.get(node.get("type"))
        wv = node.get("widgets_values")
        if info is None or not node.get("widgets_exact") or not isinstance(wv, list):
            return False
        names = comfy_schema.widget_names(info, wv)
        if name not in names or names.index(name) >= len(wv):
            return False
        wv[names.index(name)] = value
        node["widgets"], node["widgets_exact"] = comfy_schema.map_widget_values(node["type"], wv, self.oi)
        return True

    @staticmethod
    def _control_of(info, names, widget, values):
        """Name of the control widget right after widget (None if there is none). A control widget has no spec."""
        if widget not in names:
            return None
        k = names.index(widget)
        nxt = names[k + 1] if k + 1 < len(names) else None
        if nxt is None or nxt in comfy_schema.NON_VALUE_WIDGETS:
            return None
        return nxt if comfy_schema.widget_spec(info, nxt, values) is None else None

    def replace_primitive(self, nid):
        node = self.nodes[nid]
        wv = node.get("widgets_values") or []
        if not wv:
            return
        value = wv[0]
        control = wv[1] if len(wv) > 1 else "fixed"
        outs = node.get("outputs") or []
        lids = [lid for o in outs for lid in (o.get("links") or []) if lid in self.links]
        if not lids:
            return  # not connected anywhere
        targets = []
        for lid in lids:
            l = self.links[lid]
            t = self.nodes.get(l["target_id"])
            inp = next((i for i in (t.get("inputs") or []) if i["name"] == l["target_input"]), None) if t else None
            targets.append((l, t, (inp.get("widget") or {}).get("name") if inp else None))
        ltype = outs[0].get("type") if outs else None
        rec = {"id": nid, "from": "PrimitiveNode", "by": "primitive", "value": value, "control": control}
        if len(targets) == 1 and targets[0][2]:
            l, t, wname = targets[0]
            info = self.oi.get(t.get("type"))
            names = comfy_schema.widget_names(info, t.get("widgets_values")) if info else []
            ctrl = self._control_of(info, names, wname, t.get("widgets") or {}) if info else None
            if (control == "fixed" or ctrl) and self._set_widget(t, wname, value):
                if ctrl and control is not None:
                    self._set_widget(t, ctrl, control)
                self._disconnect(l["id"])
                self._remove_node(nid)
                self.records.append(dict(rec, to=None, into=[{"id": t["id"], "widget": wname}]))
                return
        new_type = PRIMITIVE_TYPED.get(ltype)
        if new_type == "PrimitiveString" and any(
                ((self._target_spec(t, w) or [None, {}])[1:2] or [{}])[0].get("multiline") for _, t, w in targets if t and w):
            new_type = "PrimitiveStringMultiline"
        info = self.oi.get(new_type) if new_type else None
        if info is None:
            self.warnings.append(f"{nid} PrimitiveNode ({ltype}): no typed value node exists; kept")
            return
        names = comfy_schema.widget_names(info, [])
        named = {"value": value}
        if len(names) > 1:
            named[names[1]] = control  # PrimitiveInt's control (the widget is named "fixed")
        elif control not in (None, "fixed"):
            self.warnings.append(f"{nid} PrimitiveNode: control is {control!r} but {new_type} has no control; kept")
            return
        values = comfy_schema.build_widgets_values(info, named)
        inputs, outputs = comfy_schema.new_node_slots(info, values)
        for l, _, _ in targets:
            l["origin_slot"] = 0
            outputs[0]["links"].append(l["id"])
        props = dict(node.get("properties") or {})
        props.pop("Run widget replace on values", None)
        props["Node name for S&R"] = new_type
        node.update({"type": new_type, "inputs": inputs, "outputs": outputs, "widgets_values": values,
                     "properties": props, "pack": comfy_schema.pack_of(new_type, self.oi)})
        node["widgets"], node["widgets_exact"] = comfy_schema.map_widget_values(new_type, values, self.oi)
        self.records.append(dict(rec, to=new_type))

    def _remove_node(self, nid):
        n = self.nodes.pop(nid)
        for i in n.get("inputs") or []:
            if i.get("link") is not None:
                self._disconnect(i["link"])
        for o in n.get("outputs") or []:
            for lid in list(o.get("links") or []):
                self._disconnect(lid)
        self.flat["nodes"] = [x for x in self.flat["nodes"] if x["id"] != nid]

    # ---- duplicate loaders ----
    def _is_loader(self, node):
        if node.get("type") in comfy_schema.VIRTUAL_TYPES or node.get("type") in comfy_schema.NOTE_TYPES:
            return False
        if any(i.get("link") is not None for i in node.get("inputs") or []):
            return False
        wv = node.get("widgets_values")
        vals = wv.values() if isinstance(wv, dict) else (wv or [])
        return any(isinstance(v, str) and v.lower().endswith(MODEL_EXT) for v in vals)

    def merge_same_loaders(self):
        groups = {}
        for n in self.flat["nodes"]:
            if self._is_loader(n):
                key = (n["type"], json.dumps(n.get("widgets_values"), sort_keys=True, ensure_ascii=False), n.get("mode", 0))
                groups.setdefault(key, []).append(n["id"])
        remap = {}
        for ids in groups.values():
            if len(ids) < 2:
                continue
            keep = self.nodes[ids[0]]
            merged = []
            for nid in ids[1:]:
                dup = self.nodes[nid]
                for k, o in enumerate(dup.get("outputs") or []):
                    for lid in list(o.get("links") or []):
                        l = self.links.get(lid)
                        if l is None or k >= len(keep.get("outputs") or []):
                            continue
                        l["origin_id"] = keep["id"]
                        keep["outputs"][k]["links"] = list(keep["outputs"][k].get("links") or []) + [lid]
                    o["links"] = []
                models = (dup.get("properties") or {}).get("models") or []
                if models:
                    props = keep.setdefault("properties", {})
                    have = {m.get("name") for m in props.get("models") or []}
                    props["models"] = list(props.get("models") or []) + [m for m in models if m.get("name") not in have]
                merged.append({"id": nid, "title": dup.get("title") or dup["type"]})
                remap[nid] = keep["id"]
                self._remove_node(nid)
            self.records.append({"id": keep["id"], "from": keep["type"], "to": keep["type"], "by": "same_loader",
                                 "merged": merged})
        if remap:
            aw = self.flat.get("author_words") or {}
            for key in ("groups", "subgraphs"):
                for g in aw.get(key) or []:
                    seen, out = set(), []
                    for i in g.get("nodes") or []:
                        i = remap.get(i, i)
                        if i not in seen:
                            seen.add(i)
                            out.append(i)
                    g["nodes"] = out
            if aw.get("titles"):
                aw["titles"] = [t for t in aw["titles"] if t.get("id") not in remap]

    def run(self):
        for nid in [n for n, x in self.nodes.items() if x.get("type") == "PrimitiveNode"]:
            self.replace_primitive(nid)
        for nid in list(self.nodes):
            seen = set()
            while True:
                node = self.nodes[nid]
                t = node["type"]
                if t in seen:
                    break
                seen.add(t)
                if t in self.repl and self.repl[t]:
                    # use the first entry, as the server does
                    if not self.replace(nid, self.repl[t][0], "node_replacements"):
                        break
                    continue
                entry = SAME_COMPUTATION.get(t)
                if entry and t in self.oi:
                    cond = entry.get("condition")
                    if cond is None or cond(node)[0]:
                        self.replace(nid, entry, "same_computation")
                elif t in CORE_REPLACEMENTS:
                    self.replace(nid, CORE_REPLACEMENTS[t], "core_node")
                break
        self.merge_same_loaders()
        replaced = {r["id"] for r in self.records}
        if replaced:
            for p in validate.check_links(self.flat, self.oi, only=replaced):
                self.warnings.append("link after replacement: " + p)
        return self.records, self.warnings


def describe(r):
    """One-line description of a replacement record."""
    if r.get("by") == "same_loader":
        ms = ", ".join(f"{m['id']} {m['title']}" for m in r.get("merged") or [])
        return f"merged identical loaders into {r['id']} {r['from']} ← {ms} (links now come from {r['id']})"
    to = r["to"] or "value moved back into " + ", ".join(f"{x['id']}.{x['widget']}" for x in r.get("into") or [])
    return f"{r['id']} {r['from']} → {to} ({r['by']})"
