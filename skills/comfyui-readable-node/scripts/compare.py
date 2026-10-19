"""Compare the source workflow with the rebuilt workflows before handing them over. Python standard library only.

Reports, as plain facts, whether something changed that the rebuild did not mean to change. Every line is a
"difference", not necessarily an error. For each one: if it was changed on purpose, give the reason in the
report to the user; if not, fix it.

- Values: whether each widget value (strings and numbers) of the source's active (mode 0) nodes that reach an
  output appears somewhere in the rebuilt workflows (all versions are passed). A string that survives as part of
  another string is reported as "partly". Setting names from turning a custom node into core nodes, and things
  removed on purpose (saving metadata, etc.), show up too.
- User inputs: the number of nodes where the user supplies a file, like Load Image / Load Video / Load Audio
  (inputs with *_upload in object_info, or types whose name starts with Load(Image|Video|Audio), VHS_LoadVideo,
  etc.). The same file in separate source nodes counts as separate inputs. Counts are compared per version.
- Outputs: output node types of the source that no version has any more.
- Stopped nodes: for a type, fewer bypassed or muted nodes and more active ones (nodes cannot be matched one to
  one, so counts per type are compared).
- Model Note (only for written workflows): whether each rebuilt workflow has a model list (a Markdown Note with a
  "## models" line), and whether it lists every model file found in widget values.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notes import collect_models, _parts  # noqa: E402

SKIP_NAMES = {"control_after_generate", "upload"}
SKIP_TYPES = {"Note", "MarkdownNote", "Reroute", "PrimitiveNode"}
SKIP_STRINGS = {"randomize", "fixed", "increment", "decrement", "image", "", "None", "none"}
INPUT_NAME = re.compile(r"^(VHS_)?Load(Image|Video|Audio)")


def values_of(n):
    w = n.get("widgets")
    if isinstance(w, dict):
        return [(k, v) for k, v in w.items() if k not in SKIP_NAMES]
    wv = n.get("widgets_values")
    if isinstance(wv, list):
        return [(f"#{i}", v) for i, v in enumerate(wv)]
    if isinstance(wv, dict):
        return list(wv.items())
    return []


def keep(v):
    if isinstance(v, bool) or v is None:
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        return v.strip() not in SKIP_STRINGS
    return False


def norm(v):
    if isinstance(v, (int, float)):
        return ("n", round(float(v), 6))
    return ("s", v.strip())


def outputs_of(flat, oi):
    """Output nodes (output_node in object_info). A node of unknown type counts as an output if nothing consumes it."""
    consumers = {l["origin_id"] for l in flat["links"]}
    out = set()
    for n in flat["nodes"]:
        if n["type"] in SKIP_TYPES:
            continue
        info = oi.get(n["type"])
        if (info and info.get("output_node")) or (info is None and n["id"] not in consumers):
            out.add(n["id"])
    return out


def reaching(flat, oi):
    """Nodes that reach an output."""
    rev = {}
    for l in flat["links"]:
        rev.setdefault(l["target_id"], set()).add(l["origin_id"])
    seen, todo = set(), list(outputs_of(flat, oi))
    while todo:
        i = todo.pop()
        if i in seen:
            continue
        seen.add(i)
        todo += list(rev.get(i, ()))
    return seen


def upload_widget(ntype, oi):
    """For a node where the user supplies a file, the name of that widget; otherwise None."""
    info = oi.get(ntype)
    if info is None:
        return "#0" if INPUT_NAME.match(ntype) else None
    for sec in ("required", "optional"):
        for name, spec in ((info.get("input") or {}).get(sec) or {}).items():
            if isinstance(spec, list) and len(spec) > 1 and isinstance(spec[1], dict) \
                    and any(k.endswith("_upload") for k in spec[1]):
                return name
    return "#0" if INPUT_NAME.match(ntype) else None    # VHS_LoadVideo has no *_upload


def user_inputs(flat, oi, only=None):
    """{(type, file): number of nodes}."""
    count = {}
    for n in flat["nodes"]:
        if n.get("mode", 0) != 0 or (only is not None and n["id"] not in only):
            continue
        w = upload_widget(n["type"], oi)
        if w is None:
            continue
        vals = values_of(n)
        f = dict(vals).get(w) if w != "#0" else None
        if f is None and vals:
            f = vals[0][1]
        key = (n["type"], f if isinstance(f, str) else json.dumps(f, ensure_ascii=False))
        count[key] = count.get(key, 0) + 1
    return count


def model_note(flat):
    for n in flat["nodes"]:
        if n["type"] in ("MarkdownNote", "Note"):
            wv = n.get("widgets_values") or [""]
            text = wv[0] if isinstance(wv, list) and wv else ""
            if isinstance(text, str) and re.search(r"^## models\s*$", text, re.M):
                return text
    return None


def compare(src, outs, oi):
    """src: the source flat graph. outs: [(name, flat graph)]. Returns a list of fact lines."""
    lines = []
    live = reaching(src, oi)

    # values
    have, texts = set(), []
    for _, f in outs:
        for n in f["nodes"]:
            if n["type"] in SKIP_TYPES:
                continue
            for _, v in values_of(n):
                if keep(v):
                    have.add(norm(v))
                    if isinstance(v, str):
                        texts.append(v)
    for n in src["nodes"]:
        if n["type"] in SKIP_TYPES or n.get("mode", 0) != 0 or n["id"] not in live:
            continue
        for k, v in values_of(n):
            if not keep(v) or norm(v) in have:
                continue
            s = json.dumps(v, ensure_ascii=False)
            if isinstance(v, str) and any(v.strip() in t for t in texts):
                lines.append(f"value kept only partly: source {n['id']} {n['type']}.{k} = {s[:80]}")
            else:
                lines.append(f"value not found: source {n['id']} {n['type']}.{k} = {s[:120]}")

    # user inputs
    before = user_inputs(src, oi, only=live)
    after = {name: user_inputs(f, oi) for name, f in outs}
    for (t, f), k in sorted(before.items()):
        got = {name: c.get((t, f), 0) for name, c in after.items()}
        if not any(got.values()):
            lines.append(f"input missing from every version: {t} {f} (source had {k})")
            continue
        for name, c in got.items():
            if 0 < c < k:
                lines.append(f"fewer inputs: {name} has {c} of {t} {f} (source had {k}; separate inputs in the source even if the file is the same)")

    # mode: for a type, fewer bypassed / muted and more active (a stopped node now runs after the rebuild)
    def modes(f):
        c = {}
        for n in f["nodes"]:
            if n["type"] in SKIP_TYPES:
                continue
            k = c.setdefault(n["type"], [0, 0])
            k[0 if n.get("mode", 0) == 0 else 1] += 1
        return c
    m0 = modes(src)
    for name, f in outs:
        for t, (on, off) in sorted(modes(f).items()):
            on0, off0 = m0.get(t, [0, 0])
            if off < off0 and on > on0:
                lines.append(f"stopped node now runs: {name} has {t} active {on}, stopped {off}"
                             f" (source: active {on0}, stopped {off0}; stopped = bypass or mute)")

    # outputs
    src_out = {src_n["type"] for src_n in src["nodes"] if src_n["id"] in outputs_of(src, oi)
               and src_n.get("mode", 0) == 0}
    out_types = {n["type"] for _, f in outs for n in f["nodes"]}
    for t in sorted(src_out - out_types):
        lines.append(f"output missing from every version: {t}")

    # model Note
    for name, f in outs:
        if f.get("_before_notes"):
            continue
        text = model_note(f)
        models = collect_models({"nodes": [n for n in f["nodes"] if n["type"] not in SKIP_TYPES]})
        if text is None:
            lines.append(f"no model list (## models): {name}" + (f" ({len(models)} models in widget values)" if models else ""))
            continue
        for m in sorted(models):
            if _parts(m)[-1] not in text:
                lines.append(f"not in the model Note: {m} in {name}")
    return lines
