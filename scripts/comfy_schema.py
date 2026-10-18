"""Knowledge about node types (from /object_info). Python standard library only.

- Loading object_info (from a server, or from a saved file)
- The widget order (which widgets_values position has which name), built by the same rules as the frontend
- Whether two types can be connected (same rule as the frontend)
- Whether a node is core (decided by python_module)

Rules matched to the frontend's behaviour:
- Inputs are ordered input_order.required -> input_order.optional -> the rest
- An input becomes a widget when its type is a widget type and it is not forceInput
- INT with control_after_generate, or named seed / noise_seed, is followed by 1 control widget
- FLOAT with control_after_generate is followed by 1, COMBO by 2 (including control_filter_list)
- If there is an *_upload input, an upload widget comes last
- For a DynamicCombo, the child widgets of the selected option follow the parent, named "parent.child"
Widgets added by frontend extensions (VHS, etc.) cannot be known from object_info. Then the order does not
match, and map_widget_values reports the mapping as not exact.
"""

import json
import urllib.request

# Widget types the frontend registers itself. Widget types added by extensions are not included.
WIDGET_TYPES = {
    "INT", "FLOAT", "BOOLEAN", "STRING", "COMBO", "MARKDOWN", "COLOR",
    "COMFY_DYNAMICCOMBO_V3", "IMAGEUPLOAD", "CURVE",
}
UPLOAD_FLAGS = ("image_upload", "video_upload", "audio_upload", "animated_image_upload", "file_upload")
SEED_NAMES = ("seed", "noise_seed")

# Frontend-only nodes (never executed): core ones and commonly used custom nodes.
VIRTUAL_TYPES = {
    "Note", "MarkdownNote", "Reroute", "PrimitiveNode",
    "SetNode", "GetNode",  # KJNodes
    "easy setNode", "easy getNode",  # Easy-Use
    "Reroute (rgthree)", "Fast Groups Muter (rgthree)", "Fast Groups Bypasser (rgthree)",
    "Fast Muter (rgthree)", "Fast Bypasser (rgthree)", "Mute / Bypass Relay (rgthree)",
    "Mute / Bypass Repeater (rgthree)", "Random Unmuter (rgthree)", "Node Collector (rgthree)",
    "Bookmark (rgthree)", "Label (rgthree)", "Fast Actions Button (rgthree)",
    "PresetText|pysssss", "VHS_SelectLatest",
}
NOTE_TYPES = {"Note", "MarkdownNote", "Label (rgthree)"}
# Widgets that hold no value (frontend controls; dropping them in a replacement changes nothing)
NON_VALUE_WIDGETS = {"control_filter_list", "upload"}


def load_object_info(source):
    """source is a URL (http://...) or the path of a saved JSON."""
    if source.startswith("http://") or source.startswith("https://"):
        url = source.rstrip("/")
        if not url.endswith("/object_info"):
            url += "/object_info"
        with urllib.request.urlopen(url, timeout=120) as r:
            return json.load(r)
    with open(source, encoding="utf-8") as f:
        return json.load(f)


def _spec_type_and_opts(spec):
    t = spec[0]
    opts = spec[1] if len(spec) > 1 and isinstance(spec[1], dict) else {}
    if isinstance(t, list):
        t = "COMBO"
    if opts.get("widgetType"):
        t = opts["widgetType"]
    return t, opts


def ordered_input_specs(info):
    """Return (name, spec, optional) in the same order the frontend orders input specs."""
    out = []
    order = info.get("input_order") or {}
    for sec in ("required", "optional"):
        specs = (info.get("input") or {}).get(sec) or {}
        seen = set()
        for name in order.get(sec) or []:
            if name in specs:
                out.append((name, specs[name], sec == "optional"))
                seen.add(name)
        for name, spec in specs.items():
            if name not in seen:
                out.append((name, spec, sec == "optional"))
    return out


def _widgets_for_spec(name, spec, values, i):
    """Names of the widgets one input spec creates. values[i:] are the saved values (used for the DynamicCombo choice).
    Returns (names, consumed); ([], 0) for an input that does not become a widget."""
    t, opts = _spec_type_and_opts(spec)
    if opts.get("forceInput"):
        return [], 0
    if t not in WIDGET_TYPES:
        return [], 0
    names = [name]
    if t == "INT" and (opts.get("control_after_generate") or name in SEED_NAMES):
        names.append(_control_name(opts))
    elif t == "FLOAT" and opts.get("control_after_generate"):
        names.append(_control_name(opts))
    elif t == "COMBO" and opts.get("control_after_generate"):
        names += [_control_name(opts), "control_filter_list"]
    if t == "COMFY_DYNAMICCOMBO_V3":
        options = opts.get("options") or []
        chosen = values[i] if i < len(values) else None
        child = None
        for o in options:
            if o.get("key") == chosen:
                child = o
        if child is None and options:
            child = options[0]
        if child:
            j = i + 1
            for sub_name, sub_spec, _ in ordered_input_specs({"input": child.get("inputs") or {}}):
                sub = _widgets_for_spec(f"{name}.{sub_name}", sub_spec, values, j)
                names += sub[0]
                j += len(sub[0])
    return names, len(names)


def _control_name(opts):
    # If the spec value is a string, the control widget is named after that string (as in the frontend)
    v = opts.get("control_after_generate")
    return v if isinstance(v, str) else "control_after_generate"


def widget_names(info, values=None):
    """From one node's object_info, build the list of names matching the widgets_values positions.
    Passing values (the saved widgets_values) applies the DynamicCombo choice."""
    values = values if isinstance(values, list) else []
    names = []
    upload = False
    for name, spec, _ in ordered_input_specs(info):
        sub, _ = _widgets_for_spec(name, spec, values, len(names))
        names += sub
        opts = _spec_type_and_opts(spec)[1]
        upload = upload or (bool(sub) and any(opts.get(f) for f in UPLOAD_FLAGS))
    if upload:
        # The upload widget is added by an extension after the node is created, so it comes last
        names.append("upload")
    return names


def input_slots(info, values=None, saved_names=None):
    """Input order of a node the frontend creates from the current definition (checked against the frontend):
    - inputs without a widget (including forceInput and Autogrow's "group.name") first, inputs with a widget after
    - a DynamicCombo's child inputs come before the parent's input
    - upload comes last
    Bypass picks its input from this order, not from the saved inputs. Returns [(name, type)].
    saved_names (names of the saved inputs) tell how far an Autogrow has grown."""
    values = values if isinstance(values, list) else []
    saved_names = saved_names or []
    sockets, widgets, upload = [], [], False

    def add(name, spec, j):
        nonlocal upload
        t, opts = _spec_type_and_opts(spec)
        raw_t = spec[0] if not isinstance(spec[0], list) else "COMBO"
        if raw_t == "COMFY_AUTOGROW_V3":
            sockets.extend(_autogrow(name, opts, saved_names))
            return 0
        if t in WIDGET_TYPES and not opts.get("forceInput"):
            used = 1
            children = []
            if t == "COMFY_DYNAMICCOMBO_V3":
                chosen = values[j] if j < len(values) else None
                options = opts.get("options") or []
                child = next((o for o in options if o.get("key") == chosen), options[0] if options else None)
                k = j + 1
                for sub_name, sub_spec, _ in ordered_input_specs({"input": (child or {}).get("inputs") or {}}):
                    before_w = len(widgets)
                    k += add(f"{name}.{sub_name}", sub_spec, k)
                    children += widgets[before_w:]
                    del widgets[before_w:]
                used = k - j
            widgets.extend(children)
            widgets.append((name, raw_t))
            upload = upload or any(opts.get(f) for f in UPLOAD_FLAGS)
            return used + (1 if t == "INT" and (opts.get("control_after_generate") or name in SEED_NAMES) else 0) \
                + (1 if t == "FLOAT" and opts.get("control_after_generate") else 0) \
                + (2 if t == "COMBO" and opts.get("control_after_generate") else 0)
        if raw_t == "COMFY_MATCHTYPE_V3":
            raw_t = (opts.get("template") or {}).get("allowed_types", "*")
        sockets.append((name, raw_t))
        return 0

    j = 0
    for name, spec, _ in ordered_input_specs(info):
        j += add(name, spec, j)
    out = sockets + widgets
    if upload:
        out.append(("upload", "IMAGEUPLOAD"))
    return out


def _autogrow(name, opts, saved_names):
    tpl = opts.get("template") or {}
    tin = (tpl.get("input") or {}).get("required") or {}
    ttype = next(iter(tin.values()))[0] if tin else "*"
    saved = [n for n in saved_names if n.startswith(name + ".")]
    if saved:
        return [(n, ttype) for n in saved]
    count = max(1, (tpl.get("min") or 0) + 1)
    names = tpl.get("names")
    prefix = tpl.get("prefix") or (next(iter(tin)) if len(tin) == 1 else "input")
    return [(f"{name}.{names[k] if names and k < len(names) else prefix + str(k)}", ttype) for k in range(count)]


def default_value(spec):
    t, opts = _spec_type_and_opts(spec)
    if "default" in opts:
        return opts["default"]
    if isinstance(spec[0], list):
        return spec[0][0] if spec[0] else None
    if t == "COMBO":
        o = opts.get("options") or []
        return o[0] if o else None
    if t == "COMFY_DYNAMICCOMBO_V3":
        o = opts.get("options") or []
        return o[0].get("key") if o else None
    return {"INT": 0, "FLOAT": 0.0, "BOOLEAN": False, "STRING": ""}.get(t)


def map_widget_values(node_type, widgets_values, object_info, named=None):
    """Turn widgets_values into {name: value}. Returns (mapping, exact).

    - If widgets_values_named is given, use it (exact).
    - Otherwise map by position (as the frontend does on load). If fewer values were saved, the rest get
      the spec defaults. When the counts differ, the result is "not exact" (an old save, or an extension
      that adds widgets).
    - If the type is unknown, (None, False)."""
    if isinstance(named, dict) and named:
        return dict(named), True
    if isinstance(widgets_values, dict):
        return dict(widgets_values), True
    info = object_info.get(node_type)
    if info is None or not isinstance(widgets_values, list):
        return None, False
    names = widget_names(info, widgets_values)
    mapping = dict(zip(names, widgets_values))
    for n in names[len(widgets_values):]:
        # Nested widgets (DynamicCombo children, "format.codec.encoding", etc.) are also filled with the default
        # of the selected option's spec (as the frontend does, when an old save lacks the child values)
        spec = widget_spec(info, n, mapping)
        if spec is not None:
            mapping[n] = default_value(spec)
    return mapping, len(names) == len(widgets_values)


def is_valid_connection(a, b):
    """Same connection rule as the frontend (LiteGraph)."""
    if a in ("", "*"):
        a = 0
    if b in ("", "*"):
        b = 0
    if not a or not b or a == b or (a == -1 and b == -1):
        return True
    a, b = str(a).lower(), str(b).lower()
    if "," not in a and "," not in b:
        return a == b
    return any(x == y for x in a.split(",") for y in b.split(","))


def pack_of(node_type, object_info):
    """"core" / "custom:<dir>" / "frontend" / "unknown"."""
    info = object_info.get(node_type)
    if info is None:
        return "frontend" if node_type in VIRTUAL_TYPES else "unknown"
    mod = info.get("python_module") or ""
    if mod.startswith("custom_nodes."):
        return "custom:" + mod.split(".", 1)[1]
    return "core"


# ---- Creating new nodes (replacements, swapping in Load Image) ----

def widget_spec(info, name, named=None):
    """Spec of a widget name (DynamicCombo children are "parent.child"). named is the current {name: value}
    (which option is selected). None for widgets without a spec, such as control widgets."""
    named = named or {}
    specs = {n: spec for n, spec, _ in ordered_input_specs(info)}
    if name in specs:
        return specs[name]
    if "." not in name:
        return None
    parent, child = name.split(".", 1)
    pspec = specs.get(parent)
    if pspec is None or _spec_type_and_opts(pspec)[0] != "COMFY_DYNAMICCOMBO_V3":
        return None
    options = _spec_type_and_opts(pspec)[1].get("options") or []
    chosen = named.get(parent, default_value(pspec))
    opt = next((o for o in options if o.get("key") == chosen), options[0] if options else None)
    sub = {n: s for n, s, _ in ordered_input_specs({"input": (opt or {}).get("inputs") or {}})}
    return widget_spec({"input": {"required": sub}}, child, {k.split(".", 1)[1]: v for k, v in named.items()
                                                             if k.startswith(parent + ".")}) if "." in child else sub.get(child)


def build_widgets_values(info, named):
    """Build widgets_values in the frontend's order from {name: value}. Missing names get default values.
    - Only the selected option's DynamicCombo children are listed (repeated until the choice settles).
    - Control widgets default to "randomize" (the frontend default; a setting can change it), upload to
      "image" (as in a saved Load Image)."""
    values = []
    for _ in range(5):
        names = widget_names(info, values)
        cur = {}
        new = []
        for nm in names:
            if nm in named:
                v = named[nm]
            elif nm == "upload":
                v = "image"
            elif nm == "control_filter_list":
                v = ""
            else:
                spec = widget_spec(info, nm, {**cur, **named})
                if spec is not None:
                    v = default_value(spec)
                else:
                    # control widget: the previous widget spec's control_after_generate if it is a string (as in the frontend)
                    prev = widget_spec(info, names[names.index(nm) - 1], {**cur, **named}) if names.index(nm) else None
                    c = _spec_type_and_opts(prev)[1].get("control_after_generate") if prev else None
                    v = c if isinstance(c, str) else "randomize"
            cur[nm] = v
            new.append(v)
        if new == values:
            break
        values = new
    return values


def new_node_slots(info, values, saved_names=None):
    """The same inputs and outputs as a node newly created in the frontend (same order).
    Inputs with a widget get "widget": {"name"}. MATCHTYPE outputs are typed "*" (set by what they connect to)."""
    wnames = set(widget_names(info, values))
    inputs = []
    for name, t in input_slots(info, values, saved_names):
        if isinstance(t, list):
            t = "COMBO"
        i = {"name": name, "type": t, "link": None}
        if name in wnames:
            i["widget"] = {"name": name}
        inputs.append(i)
    outputs = []
    names = info.get("output_name") or []
    for k, t in enumerate(info.get("output") or []):
        if isinstance(t, list):
            t = "COMBO"
        if t == "COMFY_MATCHTYPE_V3":
            t = "*"
        outputs.append({"name": names[k] if k < len(names) else t, "type": t, "links": []})
    return inputs, outputs
