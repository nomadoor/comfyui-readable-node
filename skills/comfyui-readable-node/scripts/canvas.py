"""A canvas operated by an AI agent. It reads the source workflow, then builds new workflows one command at a time, lays them out and checks them.
Python standard library only.

State is kept in a work directory (--dir, default: the current directory). Each command returns only what changed and the problems that command introduced.
`check` returns all checks. Every command can be reverted with `undo`.

Usage: python3 canvas.py [--dir WORK_DIR] <command> [args...]
       python3 canvas.py [--dir WORK_DIR] run <file with one command per line>   (# starts a comment)

■ Reading the source
  open <workflow.json> <object_info URL or JSON>
      Reads the source, turns wireless connections back into wires (Set/Get, Anything Everywhere, subgraph, Reroute),
      applies the official replacement list and replacements that compute the same thing, replaces Image Comparer (rgthree)
      with the core Compare Images (ImageCompare), returns value nodes into their targets or turns them into typed ones,
      and merges identical loaders. Removes Preview Image nodes that only show what was loaded.
      Reports everything it did. Discards positions, sizes, colors, titles and groups (the author's words are returned separately).
  src outputs              output nodes and the size of each one's upstream
  src list [part of type]  list of source nodes
  src all                  inputs/outputs, values and mode of every source node at once (instead of many `src node`)
  src node <id>            inputs/outputs, values and mode of a source node
  src up <id>              everything upstream of that node
  src words                the author's words (Notes, group names, titles)
  models                   list of models and a draft of the model Note text (from all canvases if any exist, otherwise from the source)

■ Making canvases
  new <name> [from <canvas>]   makes a new canvas and makes it current (one canvas per workflow).
                           With from, it starts as a copy of that canvas's current state (nodes, wires, positions, blocks, groups)
  use <name>               switches the current canvas
  list                     list of canvases

■ Building (on the current canvas)
  copy <source id> ...     copies source nodes with their type, values and mode (no wires; ids stay the same as the source)
  add <type> [<new id>]    adds a new node with the object_info defaults
  set <id> <widget>=<value> ...  sets values (a value that is not valid JSON is taken as a string). For a node whose type is not in object_info: <index>=<value>
  link <A>.<output> <B>.<input> [<A>.<output> <B>.<input> ...]   connects (in pairs, any number of pairs). Output by name or index, input by name.
      If B.<input> already has a wire, it is replaced. Connecting to an autogrow input (values.c etc.) adds the slot
  unlink <B>.<input> ...
  rm <id> ...              removes nodes (and their wires)
  mode <on|bypass|mute> <id> ...
  title <id> <title>       sets the title (e.g. a value node's "source node name: what the value is"). The node name is not changed

■ Laying out (<unit> is a node id or a block name. A block moves all its nodes together)
  put <unit> origin                         top-left at (0, 0)
  put <unit> right <ref> [top|wire|bottom|middle] [gap N]   to the right of ref. Default: wire if a wire connects them, else top; gap H_GAP
  put <unit> left <ref> [top|wire|bottom|middle] [gap N]
  put <unit> below <ref> [left|right|center] [gap N]       below ref. Default: left edges aligned, gap V_GAP
  put <unit> above <ref> [left|right|center] [gap N]
      wire: at the height where the (first) wire between ref and unit is horizontal
  row <unit> ... [right <ref>] [top|wire] [gap N]   one row from left to right (the first goes right of ref, or stays where it is).
                           Default: wire between neighbours that are wired, top between those that are not
  stack <unit> ... [below <ref>] [left|right] [gap N]  one column from top to bottom
  align <top|bottom|left|right|middle|center> <unit> ...   aligns to the first unit (the first does not move)
  inputs <id> [gap N]      puts the sources wired directly into that node in one right-aligned column on its left (in input order, top to bottom). Only the sources move.
                           Column height: for a node that takes conditioning, the positive wire is horizontal; otherwise the node is centred on the column vertically
  shape <laid-out block> <block to lay out> [right|below|left|above <ref>]
                           places the nodes of the second block in the same shape as the first (nodes of the same type are matched in order).
                           For laying out similar stages, or giving split workflows the same layout
  level <A>.<output> <B>.<input> [move <unit>]   moves so that this wire is horizontal (default: moves B)
  width <id> ...           sets all widths to the widest (left edges stay; in a right-aligned column the right edges stay).
                           A model, clip or vae loader among them is never narrower than the loader minimum (301).
                           Widening does not move neighbours: write width before the put that places the next node, or the gap shrinks
  move <unit> ... <dx> <dy>    shifts
  gap <A> <B> <N> [h|v]     sets the gap between A and B to N (moves B's unit. h horizontal, v vertical. Default h)
  block <name> <id> ...     makes a block (making it again replaces it). unblock <name>
  group <title> <unit> ... [color <color>]   makes a group. The frame is recomputed from its nodes every time (padding measured from hand-made layouts)
  ungroup <title>
  group-align <title> ...   aligns the top and bottom edges of these groups
  color <color|none> <id> ...    color (red brown green blue pale_blue cyan purple yellow black)
  rail <A>.<output> <above <unit>|below <unit>|level <X>.<output>|out> to <B>.<input> ...
      Rail: carries A's output to many targets along a path of Reroutes at a chosen height. Write any number of targets on one line.
      Height: above X is V_GAP above X's top edge, below X is V_GAP below X's bottom edge, level X.output is the height of that output slot,
      out keeps the height of A's output slot (then no raising Reroute is placed).
      Where Reroutes go: if the height differs from A's slot, one raising Reroute to the right of A (half the column gap), and for each target
      a lowering Reroute to its left. Targets close together share one Reroute.
      Reroutes are left out where they are not needed: a target that a direct wire from A reaches without passing behind any node is
      wired directly; a target reachable that way from the previous Reroute is wired from it; and with above/below, if a straight run at
      the height of A's slot is clear up to the last target, the rail is drawn at A's slot height instead (the command says so).
      With above/below, if the vertical gap to another rail would be less than RAIL_GAP (56), the rail is shifted away from it automatically
  note <md file> <right|left|below|above> <ref> [gap N] [width W]   places a MarkdownNote (height from the text)

■ Syntax
  Quote names that contain spaces (group titles etc.): group "Upscale x2" 12 13
  Values are read as JSON. Write text with line breaks as a JSON string: set 6 'text="line one\\nline two"'
  With align, put and level, the units written later move. The first unit (the reference) does not move.
  A block name moves the whole block. The id of a node inside a block moves only that node
  A Note's id comes from its file name (note_models.md -> note_models). Use that id with title etc.
  In a plan, place a node on an earlier line before using it as a reference
  File paths (note, render, export) are relative to the current directory (not to --dir)

■ Looking before placing
  between [plan file]      number and direction of wires between blocks, outputs that feed several blocks, nodes outside any block.
                           Given a plan file, it reads only that file's block lines and counts (nothing needs to be placed yet).
                           Look at this before deciding the arrangement (whether to use rails, how to stack stages)
  refs <word> ...          workflows on the skill author's site (Comfy with ComfyUI) for the same use, newest first: date, URL and article. A reference for how to build the core
                           (read from the copy of the site's list in references/site/index.json)

■ Placing with a plan file (usually this, to save round trips)
  layout <plan file>       applies the file from the top and re-places everything (positions, blocks, groups, rails and Notes are rebuilt).
                           Allowed commands: block put row stack align level inputs shape width move gap group group-align
                           color rail note title. Write the inside of each block first (make the block, then lay out its inside),
                           and the blocks relative to each other last (put <block> ...).
                           The first line inside a block gives its first node a position (put <id> origin; row and stack
                           do this for an unplaced first unit): put ... right <id> and inputs <id> need <id> placed. If any line stops, nothing changes. Returns the checks grouped by block.
                           To fix things, edit the lines of the file and run layout again. One run can fix any number of places

■ Viewing and checking
  show                     nodes on the current canvas (position, size, block, color, mode) and what is not placed
  node <id>                a node's inputs/outputs, values and slot positions
  check                    the checks (unplaced, overlaps, narrow gaps, wires behind nodes, crossings, non-horizontal wires, backward wires,
                           right edges of sampler inputs, empty band across everything, width differences and value node tops,
                           Preview above its source, gaps inside a column, gap to a wired neighbour, spacing in a row,
                           consecutive Reroutes, Reroutes doing nothing, model Note top edge, rails that can run at the output height,
                           rails with a single target, overlapping rails, rail order against loader order, raising Reroutes right of a loader,
                           loader rails above their targets, wires over group titles, nodes overlapping groups, types and required inputs).
                           Items marked "cannot be kept even with a reason" must be fixed before you finish
  diff                     compares the source with all canvases (values, inputs the user fills in, outputs, mode, model Note)
  render <png>             picture
  export <json>            writes a workflow that ComfyUI can open
  replay <html> [en|ja]    writes a page that steps through every command on every canvas (for the user to see what was done).
                           The page's words are in English (en, default) or Japanese (ja)
  finish                   deletes the working folder once every canvas is exported and the replay page is up to date
                           (otherwise it stops, says what is missing and deletes nothing). Only files the canvas knows are deleted:
                           what it wrote, the plan and Note files it was given, understanding.md. Other files are left, and so is the folder.
                           With the environment variable CANVAS_KEEP_WORK=1 nothing is deleted; the files are only listed
  undo                   reverts one command. A command that stopped changed nothing and is not recorded, so undo after it reverts the command before
  history                  all commands
"""

import argparse
import copy
import hashlib
import json
import re
import os
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import api_format as AF  # noqa: E402
import comfy_schema as CS  # noqa: E402
import compare as CMP  # noqa: E402
import flatten as FL  # noqa: E402
import legacy_groups as LG  # noqa: E402
import geometry as G  # noqa: E402
import nodesize  # noqa: E402
import notes as NT  # noqa: E402
import read_workflow as RW  # noqa: E402
import render as RD  # noqa: E402
import replace as RP  # noqa: E402
import replay as RPL  # noqa: E402
import validate as VD  # noqa: E402
import write_workflow as WW  # noqa: E402
from layout_params import P  # noqa: E402

H_GAP, V_GAP = P["H_GAP"], P["V_GAP"]
FRONTEND_MIN = json.loads((Path(__file__).resolve().parent / "frontend_min_sizes.json").read_text(encoding="utf-8"))["sizes"]
PAD_L, PAD_T, PAD_R, PAD_B = P["GROUP_PAD_LEFT"], P["GROUP_PAD_TOP"], P["GROUP_PAD_RIGHT"], P["GROUP_PAD_BOTTOM"]
GROUP_TITLE_H = 34          # height of the frontend's group title bar (font_size 24 x 1.4)
TEXT_MIN_H = 100            # minimum height of a text area (a number set by the skill author)
# image area added to the initial size of nodes that show an image (layout_params.json), by the kind image_kind returns
IMAGE_AREA = {"save": P["IMAGE_AREA_SAVE"], "preview": P["IMAGE_AREA_PREVIEW"], "load": P["IMAGE_AREA_LOAD"]}
IMAGE_UPLOAD_FLAGS = tuple(f for f in CS.UPLOAD_FLAGS if f in ("image_upload", "video_upload"))
LOADER_MIN_W = 301          # minimum loader width (median of 734 loaders in hand-made layouts)
REROUTE_W, REROUTE_H = 75, 26
COLORS = {
    "red": ("#322", "#533"), "brown": ("#332922", "#593930"), "green": ("#232", "#353"), "blue": ("#223", "#335"),
    "pale_blue": ("#2a363b", "#3f5159"), "cyan": ("#233", "#355"), "purple": ("#323", "#535"),
    "yellow": ("#432", "#653"), "black": ("#222", "#000"),
}
LOADER_COLOR = {"MODEL": "purple", "CLIP": "yellow", "VAE": "red"}
PRODUCT_TYPES = {"IMAGE", "LATENT", "VIDEO", "MASK", "AUDIO"}   # what the workflow produces step by step (readable-form.md)
SELF_PREVIEW_LOADERS = {"LoadImage", "LoadVideo", "VHS_LoadVideo"}
NOTE_TYPES = CS.NOTE_TYPES
# working keys from reading, dropped when copying from the source. orig_size is kept (used for the size of custom nodes that are not installed)
WORK_KEYS = WW.NODE_WORK_KEYS - {"orig_size"}
# marks only the canvas adds. Dropped on export
CANVAS_MARKS = {"size_min", "width_set", "loader_base", "canvas_note", "layout_prev"}


class Stop(Exception):
    pass


def jdump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def jload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def display_title(n, oi):
    if n.get("title"):
        return n["title"]
    info = oi.get(n.get("type")) or {}
    return info.get("display_name") or n.get("type")


# loading nodes whose preview a frontend extension adds, so object_info has no upload flag for them (VideoHelperSuite)
LOADS_WITH_PREVIEW = {"VHS_LoadVideo", "VHS_LoadVideoFFmpeg", "VHS_LoadVideoPath", "VHS_LoadVideoFFmpegPath",
                      "VHS_LoadImages", "VHS_LoadImagesPath", "VHS_LoadImagePath"}


def image_kind(t, oi):
    """Whether a node type shows an image, recognised from object_info (by type name only for LOADS_WITH_PREVIEW):
    "save" for an output node that takes an IMAGE or VIDEO input and saves files ("save" in its category or name, or a
    filename_prefix input), "preview" for another output node that takes an IMAGE input and puts out nothing but IMAGE, "load" for a node with an
    input carrying image_upload or video_upload. None otherwise (also for a type not in object_info)."""
    info = oi.get(t)
    if not info:
        return None
    if t in LOADS_WITH_PREVIEW:
        return "load"
    specs = [(nm, CS._spec_type_and_opts(sp)) for nm, sp, _ in CS.ordered_input_specs(info) if isinstance(sp, (list, tuple)) and sp]
    if any(any(opts.get(f) for f in IMAGE_UPLOAD_FLAGS) for _, (_, opts) in specs):
        return "load"
    if not info.get("output_node") or not any(typ in ("IMAGE", "VIDEO") for _, (typ, _) in specs):
        return None
    words = " ".join(str(info.get(k) or "") for k in ("category", "name", "display_name")) + " " + t
    if "save" in words.lower() or any(nm == "filename_prefix" for nm, _ in specs):
        return "save"
    # a preview shows the image it gets and passes on at most that image (API nodes, prompt helpers and tiling helpers
    # that are output nodes put out other types)
    if any(typ == "IMAGE" for _, (typ, _) in specs) and all(o == "IMAGE" for o in info.get("output") or []):
        return "preview"
    return None


def is_custom(t, oi):
    info = oi.get(t)
    return info is None or str(info.get("python_module", "")).startswith("custom_nodes")


# ---------------------------------------------------------------- work directory

class Work:
    def __init__(self, d):
        self.dir = Path(d)
        self.cfg_path = self.dir / "canvas.config.json"
        self.cfg = jload(self.cfg_path) if self.cfg_path.exists() else {}
        self._oi = None

    @property
    def oi(self):
        if self._oi is None:
            p = self.dir / "object_info.json"
            if not p.exists():
                raise Stop("not opened yet (run open first)")
            self._oi = jload(p)
        return self._oi

    def save_cfg(self):
        jdump(self.cfg_path, self.cfg)

    def consume(self, path):
        """Remembers a file the canvas was given (plan, Note), by its absolute path, so that finish can delete it."""
        p = os.path.abspath(path)
        lst = self.cfg.setdefault("consumed", [])
        if p not in lst:
            lst.append(p)
            self.dir.mkdir(parents=True, exist_ok=True)
            self.save_cfg()

    def src(self):
        p = self.dir / "src.flat.json"
        if not p.exists():
            raise Stop("not opened yet (run open first)")
        return jload(p)

    def canvas_path(self, name):
        return self.dir / "canvas" / f"{name}.json"

    def current(self):
        name = self.cfg.get("current")
        if not name:
            raise Stop("no canvas (make one with new <name>)")
        return Canvas(self, name)

    def names(self):
        d = self.dir / "canvas"
        return sorted(p.stem for p in d.glob("*.json")) if d.exists() else []


# ---------------------------------------------------------------- canvas

class Canvas:
    def __init__(self, work, name, fresh=False):
        self.work, self.name, self.oi = work, name, work.oi
        self.path = work.canvas_path(name)
        self.hist = self.path.with_suffix(".hist")
        if fresh:
            self.s = {"name": name, "nodes": [], "links": [], "next_link": 1, "next_id": 1, "blocks": {},
                      "groups": [], "history": []}
        else:
            if not self.path.exists():
                raise Stop(f"no canvas {name}")
            self.s = jload(self.path)
        self.out = []
        self.changed = set()
        self.moved = {}
        self.in_layout = False   # set while `layout` applies a plan (titles and colours it sets are undone on the next layout)
        self.before = set()

    # ---- saving and undo
    def snapshot(self, cmd):
        self.hist.mkdir(parents=True, exist_ok=True)
        k = len(list(self.hist.glob("*.json")))
        snap = self.hist / f"{k:05d}.json"
        jdump(snap, self.s)
        self.s["history"].append(cmd)
        return snap

    def undo(self):
        snaps = sorted(self.hist.glob("*.json")) if self.hist.exists() else []
        if not snaps:
            raise Stop("nothing to undo")
        last = self.s["history"][-1] if self.s["history"] else "?"
        self.s = jload(snaps[-1])
        snaps[-1].unlink()
        self.save()
        return last

    def is_loader(self, n):
        """A node with no wired inputs that outputs a model such as MODEL, CLIP or VAE (also any type whose name contains Loader)."""
        return self.is_model_loader(n) or "Loader" in (n.get("type") or "")

    def is_model_loader(self, n):
        """A loader of a diffusion model, clip or vae (no wired inputs, first output is MODEL, CLIP or VAE)."""
        ins = [i for i in n.get("inputs") or [] if not i.get("widget")]
        outs = [o.get("type") for o in n.get("outputs") or []]
        return not ins and bool(outs) and outs[0] in LOADER_COLOR

    def same_loader_width(self):
        """Loaders of diffusion model, clip and vae get the same width: the widest one, and never narrower than LOADER_MIN_W.
        Other loaders (upscale models etc.) are not aligned. A loader that would overlap another node when widened
        (sticking out of its column) is not widened. A loader whose width was set with width (width_set) is not
        widened either: it would no longer match the nodes it was made as wide as.
        The width before widening is kept in loader_base and the width is recomputed from it every time."""
        for n in self.s["nodes"]:
            if "loader_base" in n:
                n["size"][0] = max(n.pop("loader_base"), (n.get("size_min") or [0, 0])[0])
        ls = [n for n in self.s["nodes"] if self.is_model_loader(n) and n.get("size")]
        if not ls:
            return
        w = max([LOADER_MIN_W] + [n["size"][0] for n in ls])
        for n in ls:
            if n["size"][0] == w or n.get("width_set"):
                continue
            base = n["size"][0]
            # widest first; if that overlaps a neighbour, at least the minimum width; else leave it as it is
            for cand in (w, max(base, LOADER_MIN_W)):
                if cand == base:
                    break
                n["size"][0] = cand
                if not (self.placed(n) and any(rect_overlap(G.rect(n), G.rect(m)) for m in self.s["nodes"]
                                               if m is not n and self.placed(m))):
                    n["loader_base"] = base
                    self.changed.add(n["id"])
                    break
                n["size"][0] = base

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.same_loader_width()
        self.update_groups()
        jdump(self.path, self.s)

    # ---- lookup
    @property
    def nodes(self):
        return {n["id"]: n for n in self.s["nodes"]}

    def node(self, nid):
        n = self.nodes.get(nid)
        if n is None:
            raise Stop(f"no node {nid}")
        return n

    def unit(self, tok):
        if tok in self.s["blocks"]:
            return list(self.s["blocks"][tok])
        if tok in self.nodes:
            return [tok]
        raise Stop(f"{tok} is neither a node nor a block")

    def placed(self, n):
        return n.get("pos") is not None

    def unplaced_msg(self, nid):
        """Why a node used as a reference cannot be used yet, and what line places it."""
        msg = f"{nid} is not placed yet"
        blk = next((b for b, ids in self.s["blocks"].items() if nid in ids), None)
        if blk is None:
            return msg + f": place it first (put {nid} origin, or put {nid} right <placed node>)"
        placed = [i for i in self.s["blocks"][blk] if i in self.nodes and self.placed(self.nodes[i])]
        if not placed:
            # nothing in the block is placed: the first line inside a block has to give it a position
            return (msg + f": nothing in block {blk} is placed yet. Place the first node of block {blk} first:"
                    f" put {nid} origin (or put {nid} right <placed node>)")
        return msg + f": place it first (e.g. put {nid} right {placed[-1]})"

    def bbox(self, ids, need_all=True):
        rs = []
        for i in ids:
            n = self.node(i)
            if not self.placed(n):
                if need_all:
                    raise Stop(self.unplaced_msg(i))
                continue
            rs.append(G.rect(n))
        if not rs:
            raise Stop("no placed nodes")
        return (min(r[0] for r in rs), min(r[1] for r in rs), max(r[2] for r in rs), max(r[3] for r in rs))

    # ---- slots and wires
    def port_out(self, tok):
        if "." not in tok:
            raise Stop(f"{tok}: write <id>.<output>")
        nid, p = tok.split(".", 1)   # ids never contain "."; input names can (values.a)
        n = self.node(nid)
        outs = n.get("outputs") or []
        if p.isdigit() and int(p) < len(outs):
            return nid, int(p)
        for k, o in enumerate(outs):
            if (o.get("name") or "").lower() == p.lower():
                return nid, k
        for k, o in enumerate(outs):
            if (o.get("type") or "").lower() == p.lower():
                return nid, k
        raise Stop(f"{nid} has no output {p} ({', '.join(o.get('name') or o.get('type') for o in outs)})")

    def port_in(self, tok):
        if "." not in tok:
            raise Stop(f"{tok}: write <id>.<input>")
        nid, p = tok.split(".", 1)   # ids never contain "."; input names can (values.a)
        n = self.node(nid)
        for i in n.get("inputs") or []:
            if i["name"].lower() == p.lower():
                return nid, i["name"]
        if self.grow_input(n, p):
            return nid, p
        raise Stop(f"{nid} has no input {p} ({', '.join(i['name'] for i in n.get('inputs') or [])})")

    def grow_input(self, n, name):
        """Adds an autogrow input (values.c etc.). True if it was added."""
        info = self.oi.get(n.get("type"))
        if not info or not isinstance(n.get("widgets_values"), list):
            return False
        names = [i["name"] for i in n.get("inputs") or []]
        if "." not in name or not any(x.startswith(name.split(".")[0] + ".") for x in names):
            return False
        saved = names + [name]
        if name not in [x for x, _ in CS.input_slots(info, n["widgets_values"], saved)]:
            return False
        keep = {i["name"]: i.get("link") for i in n.get("inputs") or []}
        ins, _ = CS.new_node_slots(info, n["widgets_values"], saved)
        for i in ins:
            i["link"] = keep.get(i["name"])
        n["inputs"] = ins
        self.out.append(f"added input: {n['id']}.{name}")
        return True

    def out_xy(self, nid, slot):
        return G.output_pos(self.node(nid), slot)

    def in_xy(self, nid, name):
        n = self.node(nid)
        names, grow = RD.widget_info(n, self.oi)
        return G.input_pos(n, name, names, grow)

    def wire_pts(self, l):
        o, t = self.nodes.get(l["origin_id"]), self.nodes.get(l["target_id"])
        if not o or not t or not self.placed(o) or not self.placed(t):
            return None
        a, b = self.out_xy(o["id"], l["origin_slot"]), self.in_xy(t["id"], l["target_input"])
        if a is None or b is None:
            return None
        return G.spline(a, b)

    def relink(self):
        nodes = self.nodes
        for n in nodes.values():
            for i in n.get("inputs") or []:
                i["link"] = None
            for o in n.get("outputs") or []:
                o["links"] = []
        for l in self.s["links"]:
            t, o = nodes[l["target_id"]], nodes[l["origin_id"]]
            for i in t.get("inputs") or []:
                if i["name"] == l["target_input"]:
                    i["link"] = l["id"]
            outs = o.get("outputs") or []
            if l["origin_slot"] < len(outs):
                outs[l["origin_slot"]]["links"].append(l["id"])

    def add_link(self, oid, slot, tid, tin):
        self.s["links"] = [l for l in self.s["links"] if not (l["target_id"] == tid and l["target_input"] == tin)]
        o = self.node(oid)
        typ = (o.get("outputs") or [])[slot].get("type") or "*"
        l = {"id": self.s["next_link"], "origin_id": oid, "origin_slot": slot, "target_id": tid,
             "target_input": tin, "type": typ}
        self.s["next_link"] += 1
        self.s["links"].append(l)
        self.relink()
        self.changed |= {oid, tid}
        return l

    # ---- size and color
    def size_node(self, n):
        if n.get("type") == "Reroute":
            n["size"] = [REROUTE_W, REROUTE_H]
            return
        if n.get("type") in NOTE_TYPES:
            return
        n.pop("loader_base", None)   # the size is recomputed, so the loader width alignment is recomputed too
        title = display_title(n, self.oi)
        size = nodesize.default_size(n, self.oi, title=title)
        if size is None:
            size = nodesize.estimate_unknown(n)
            o = n.get("orig_size")
            if o:
                size = [max(size[0], o[0]), max(size[1], o[1])]
        w, h = size
        kind = image_kind(n.get("type"), self.oi)
        if kind:
            # the image area goes below the initial size: as wide as the area at least, and that much taller
            w, h = max(w, IMAGE_AREA[kind][0]), h + IMAGE_AREA[kind][1]
        fm = FRONTEND_MIN.get(n.get("type"))
        if fm:
            # e.g. nodes the frontend adds widgets to later. Never smaller than the size the frontend makes (it would grow and break the layout when opened in ComfyUI)
            w, h = max(w, fm[0]), max(h, fm[1])
        w = max(w, nodesize.min_width(title), (n.get("size_min") or [0, 0])[0])
        if n.get("type") not in nodesize.COMPACT_TYPES:
            # every text area (multiline widget) is at least TEXT_MIN_H tall (so it does not get squeezed on nodes with many parameters)
            names, grow = RD.widget_info(n, self.oi)
            grow = [x for x in names if x in grow]
            if grow:
                sock = [i for i in n.get("inputs") or [] if not i.get("widget")]
                rows = max(len(sock), len(n.get("outputs") or []), 1)
                start = rows * G.SLOT + 6
                fixed = sum(G.WIDGET for x in names if x not in grow)
                h = max(h, start + fixed + TEXT_MIN_H * len(grow))
        old = n.get("size")
        n["size"] = [round(w), round(h)]
        if old and old != n["size"]:
            self.out.append(f"size {n['id']}: {old} → {n['size']}")
            self.changed.add(n["id"])

    def default_color(self, n):
        outs = [o.get("type") for o in n.get("outputs") or []]
        if self.is_model_loader(n):
            n["color"], n["bgcolor"] = COLORS[LOADER_COLOR[outs[0]]]
        elif "lora" in (n.get("type") or "").lower() and "MODEL" in outs:
            n["color"], n["bgcolor"] = COLORS["purple"]

    # ---- moving
    def set_rect_xy(self, nid, x0, y0):
        n = self.node(nid)
        old = list(n["pos"]) if self.placed(n) else None
        n["pos"] = [round(x0), round(y0 + G.title_height(n))]
        if old != n["pos"]:
            self.moved.setdefault(nid, old)
            self.changed.add(nid)

    def translate(self, ids, dx, dy):
        for i in ids:
            n = self.node(i)
            if not self.placed(n):
                raise Stop(f"{i} is not placed yet")
            r = G.rect(n)
            self.set_rect_xy(i, r[0] + dx, r[1] + dy)

    def place_unit(self, ids, x0, y0):
        """Moves the top-left of the unit's bounding box to (x0, y0). A single unplaced node is placed there."""
        if len(ids) == 1 and not self.placed(self.node(ids[0])):
            self.set_rect_xy(ids[0], x0, y0)
            return
        b = self.bbox(ids)
        self.translate(ids, x0 - b[0], y0 - b[1])

    def unit_size(self, ids):
        if len(ids) == 1 and not self.placed(self.node(ids[0])):
            n = self.node(ids[0])
            return n["size"][0], n["size"][1] + G.title_height(n)
        b = self.bbox(ids)
        return b[2] - b[0], b[3] - b[1]

    def link_between(self, a_ids, b_ids):
        a, b = set(a_ids), set(b_ids)
        for l in self.s["links"]:
            if (l["origin_id"] in a and l["target_id"] in b) or (l["origin_id"] in b and l["target_id"] in a):
                return l
        return None

    def level_dy(self, l, move_ids):
        """How far move_ids must move vertically for wire l to be horizontal."""
        a = self.out_xy(l["origin_id"], l["origin_slot"])
        b = self.in_xy(l["target_id"], l["target_input"])
        return (a[1] - b[1]) if l["target_id"] in move_ids else (b[1] - a[1])

    # ---- group
    def update_groups(self):
        boxes = {}
        for g in self.s["groups"]:
            ids = [i for i in g["members"] if i in self.nodes and self.placed(self.nodes[i])]
            if not ids:
                g["bounding"] = None
                continue
            b = self.bbox(ids)
            boxes[g["title"]] = [b[0] - PAD_L, b[1] - PAD_T, b[2] + PAD_R, b[3] + PAD_B]
        for names in self.s.get("group_align") or []:
            have = [boxes[t] for t in names if t in boxes]
            if not have:
                continue
            top, bottom = min(b[1] for b in have), max(b[3] for b in have)
            for t in names:
                if t in boxes:
                    boxes[t][1], boxes[t][3] = top, bottom
        for g in self.s["groups"]:
            b = boxes.get(g["title"])
            if b:
                g["bounding"] = [round(b[0]), round(b[1]), round(b[2] - b[0]), round(b[3] - b[1])]

    # ---- export form
    def flat(self):
        f = {"nodes": [], "links": copy.deepcopy(self.s["links"])}
        for n in self.s["nodes"]:
            m = {k: v for k, v in n.items() if k not in CANVAS_MARKS}
            f["nodes"].append(m)
        return f

    def workflow(self):
        self.update_groups()
        f = self.flat()
        placed = [n for n in f["nodes"] if n.get("pos") is not None]
        f["nodes"] = placed
        keep = {n["id"] for n in placed}
        f["links"] = [l for l in f["links"] if l["origin_id"] in keep and l["target_id"] in keep]
        groups = []
        for g in self.s["groups"]:
            if g.get("bounding"):
                groups.append({"title": g["title"], "bounding": g["bounding"], "color": g.get("color") or "#3f789e",
                               "font_size": 24, "flags": {}})
        wf, ids = WW.write(f, groups)
        return wf, ids


# ---------------------------------------------------------------- checks

def wires_of(cv):
    out = []
    for l in cv.s["links"]:
        pts = cv.wire_pts(l)
        if pts:
            out.append((l, pts))
    return out


def rect_overlap(a, b):
    return min(a[2], b[2]) - max(a[0], b[0]) > 0 and min(a[3], b[3]) - max(a[1], b[1]) > 0


def seg_cross(p1, p2, p3, p4):
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2, d3, d4 = o(p3, p4, p1), o(p3, p4, p2), o(p1, p2, p3), o(p1, p2, p4)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 * d2 < 0 and d3 * d4 < 0


def poly_cross(a, b):
    ba = (min(p[0] for p in a), min(p[1] for p in a), max(p[0] for p in a), max(p[1] for p in a))
    bb = (min(p[0] for p in b), min(p[1] for p in b), max(p[0] for p in b), max(p[1] for p in b))
    if ba[2] < bb[0] or bb[2] < ba[0] or ba[3] < bb[1] or bb[3] < ba[1]:
        return False
    for i in range(len(a) - 1):
        for j in range(len(b) - 1):
            if seg_cross(a[i], a[i + 1], b[j], b[j + 1]):
                return True
    return False


def is_sampler(n):
    """A node that samples: takes conditioning or a guider, does not output conditioning, and handles a latent
    (KSampler, SamplerCustom, SamplerCustomAdvanced; not InpaintModelConditioning)."""
    ins = {i.get("type") for i in n.get("inputs") or []}
    outs = {o.get("type") for o in n.get("outputs") or []}
    return bool({"CONDITIONING", "GUIDER"} & ins) and "CONDITIONING" not in outs and ("LATENT" in outs or "LATENT" in ins)


def group_lower(cv, oid, tid):
    """Whether tid is in a group that does not contain oid, and that group's top edge is below oid's bottom edge."""
    o = cv.nodes[oid]
    for g in cv.s["groups"]:
        if tid in g["members"] and oid not in g["members"] and g.get("bounding"):
            if g["bounding"][1] > G.rect(o)[3]:
                return True
    return False


def row_chains(cv):
    """Sequences of three or more nodes in one horizontal row, wired one after another (vertical ranges overlap, wired to the right)."""
    nodes = cv.nodes
    nxt = {}
    for l in cv.s["links"]:
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if not o or not t or not cv.placed(o) or not cv.placed(t):
            continue
        if o.get("type") in {"Reroute"} | NOTE_TYPES or t.get("type") in {"Reroute"} | NOTE_TYPES:
            continue
        ro, rt = G.rect(o), G.rect(t)
        if rt[0] > ro[2] and min(ro[3], rt[3]) - max(ro[1], rt[1]) > 0 and abs(rt[1] - ro[1]) < 1:
            nxt.setdefault(o["id"], set()).add(t["id"])
    has_prev = {t for ts in nxt.values() for t in ts}
    chains = []
    for start in nxt:
        if start in has_prev:
            continue
        chain, cur = [start], start
        while len(nxt.get(cur, ())) == 1:
            cur = next(iter(nxt[cur]))
            if cur in chain:
                break
            chain.append(cur)
        if len(chain) >= 3:
            chains.append(chain)
    return chains


def lname(cv, l):
    o, t = cv.nodes.get(l["origin_id"]), cv.nodes.get(l["target_id"])
    oname = ((o.get("outputs") or [])[l["origin_slot"]].get("name") if o else "?") or l["origin_slot"]
    return f"{l['origin_id']}.{oname} → {l['target_id']}.{l['target_input']}"


def hidden_wires(cv, only=None):
    """[(wire, id of the node it passes behind)]. With only, just those involving these ids."""
    nodes = [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") != "Reroute"]
    res = []
    for l, pts in wires_of(cv):
        for n in nodes:
            if n["id"] in (l["origin_id"], l["target_id"]):
                continue
            if only is not None and not ({n["id"], l["origin_id"], l["target_id"]} & only):
                continue
            if G.wire_hits(pts, G.rect(n)):
                res.append((l, n["id"]))
    return res


def overlaps(cv, only=None):
    ps = [n for n in cv.s["nodes"] if cv.placed(n)]
    res = []
    for i, a in enumerate(ps):
        for b in ps[i + 1:]:
            if only is not None and not ({a["id"], b["id"]} & only):
                continue
            if rect_overlap(G.rect(a), G.rect(b)):
                res.append((a["id"], b["id"]))
    return res


def narrow(cv, only=None):
    ps = [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") != "Reroute"]
    res = []
    for i, a in enumerate(ps):
        for b in ps[i + 1:]:
            if only is not None and not ({a["id"], b["id"]} & only):
                continue
            ra, rb = G.rect(a), G.rect(b)
            if rect_overlap(ra, rb):
                continue
            ov_y = min(ra[3], rb[3]) - max(ra[1], rb[1]) > 0
            ov_x = min(ra[2], rb[2]) - max(ra[0], rb[0]) > 0
            if ov_y:
                d = max(rb[0] - ra[2], ra[0] - rb[2])
                if 0 <= d < H_GAP:
                    res.append((a["id"], b["id"], "horizontal", round(d)))
            elif ov_x:
                d = max(rb[1] - ra[3], ra[1] - rb[3])
                if 0 <= d < V_GAP:
                    res.append((a["id"], b["id"], "vertical", round(d)))
    return res


def problems(cv):
    """The set of problems compared before and after a command: every line of `check` (one yardstick for both)."""
    return set(full_check(cv)[0])


def local_report(cv, before):
    after = problems(cv)
    for p in sorted(after - before):
        cv.out.append(f"  new: {p}")
    gone = before - after
    if gone:
        cv.out.append(f"  resolved {len(gone)}: " + "; ".join(sorted(gone)[:8]) + (" ..." if len(gone) > 8 else ""))


class _CheckCtx:
    """What the check rules share (node lookup, wire shapes) and the counts shown on the first line."""

    def __init__(self, cv):
        self.cv = cv
        self.nodes = cv.nodes
        self.ws = wires_of(cv)
        self.count = {"overlaps": 0, "wires behind nodes": 0, "crossings": 0, "non-horizontal wires": 0, "unplaced": 0,
                      "backward wires that cannot be kept": 0}


CHECKS = []   # (name, rule function), applied top to bottom. A rule takes (cv, ctx) and returns a list of message lines


def check_rule(name):
    def reg(fn):
        CHECKS.append((name, fn))
        return fn
    return reg



@check_rule("unplaced nodes")
def _chk_unplaced(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    un = [n["id"] for n in cv.s["nodes"] if not cv.placed(n)]
    if un:
        out.append(f"unplaced {len(un)}: {' '.join(un)}")
    c.count["unplaced"] = len(un)
    return out


@check_rule("overlaps")
def _chk_overlap(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    ov = overlaps(cv)
    for a, b in ov:
        out.append(f"overlap: {a} and {b}")
    c.count["overlaps"] = len(ov)
    return out


@check_rule("narrow gaps")
def _chk_narrow(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    for a, b, k, d in narrow(cv):
        out.append(f"narrow gap ({k} {d}px, min {H_GAP if k == 'horizontal' else V_GAP}): {a} and {b}")
    return out


@check_rule("wires behind nodes")
def _chk_hidden(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    hw = hidden_wires(cv)
    c.count["wires behind nodes"] = len(hw)
    for l, nid in hw:
        out.append(f"wire behind a node: {lname(cv, l)} ({l['type']}) passes behind {nid}")
    return out


@check_rule("crossings")
def _chk_cross(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    cross = []
    for i, (la, pa) in enumerate(ws):
        for lb, pb in ws[i + 1:]:
            # skip only wires from the same output slot or into the same input slot. Two wires into different inputs
            # of the same node do cross when they come from heights in the reverse order of the inputs, so they count
            if (la["origin_id"], la["origin_slot"]) == (lb["origin_id"], lb["origin_slot"]) or \
               (la["target_id"], la["target_input"]) == (lb["target_id"], lb["target_input"]):
                continue
            if poly_cross(pa, pb):
                cross.append((la, lb))
    # crossings involving a product wire (image, video, latent, mask, audio) are listed one by one.
    # Crossings between tool wires (VAE, CLIP, conditioning, values etc.) are only counted (a short list keeps what to fix visible)
    tool_cross = 0
    for la, lb in cross:
        if la["type"] in PRODUCT_TYPES or lb["type"] in PRODUCT_TYPES:
            out.append(f"crossing (product wire): {lname(cv, la)} and {lname(cv, lb)}")
        else:
            tool_cross += 1
    if tool_cross:
        out.append(f"crossings between tool wires: {tool_cross} (not listed one by one; reduce them if you can)")
    c.count["crossings"] = len(cross)
    return out


SCA_SIDE_INPUTS = ("noise", "guider", "sampler", "sigmas")   # inputs of SamplerCustomAdvanced not checked for tilt


@check_rule("non-horizontal wires")
def _chk_tilt(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # every wire that is not horizontal, whatever its type (a wire that could be made horizontal)
    tilt = []
    for l, pts in ws:
        dy = pts[-1][1] - pts[0][1]
        if abs(dy) < 1:
            continue
        # SamplerCustomAdvanced sits in the vertical middle of its sources, so the wires into noise, guider, sampler and
        # sigmas are slanted by design. Reporting them would bury the wires that can be fixed (latent_image is still reported)
        if nodes.get(l["target_id"], {}).get("type") == "SamplerCustomAdvanced" and l["target_input"] in SCA_SIDE_INPUTS:
            continue
        tilt.append(l)
        out.append(f"non-horizontal wire ({l['type']}, input at {dy:+.0f}px): {lname(cv, l)}")
    c.count["non-horizontal wires"] = len(tilt)
    return out


@check_rule("backward wires")
def _chk_backward(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    back_hard = 0
    for l, pts in ws:
        if pts[-1][0] >= pts[0][0]:
            continue
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        ro, rt = G.rect(o), G.rect(t)
        one = rt[0] >= ro[0] - H_GAP - (rt[2] - rt[0])   # goes back by at most one node's width
        if cv.is_loader(o):
            one = False   # no backward wire from a loader (a loader sits left of the first node that uses it)
        gl = group_lower(cv, o["id"], t["id"])
        if one or gl:
            why = "goes back by at most one node's width" if one else "enters a group one row lower"
            out.append(f"backward wire that may be allowed ({why}; only one node back into a node with little content, or into a whole group placed one row lower): {lname(cv, l)}")
        else:
            back_hard += 1
            out.append(f"backward wire (cannot be kept even with a reason; fix it): {lname(cv, l)}")
    c.count["backward wires that cannot be kept"] = back_hard
    return out


@check_rule("right edges of sampler inputs")
def _chk_sampler_inputs(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # the sources wired directly into a sampler are not in one column (right edges)
    for n in cv.s["nodes"]:
        if not cv.placed(n) or not is_sampler(n):
            continue
        srcs = []
        for l in cv.s["links"]:
            if l["target_id"] == n["id"]:
                o = nodes.get(l["origin_id"])
                if o and cv.placed(o) and o.get("type") not in {"Reroute"} | NOTE_TYPES and o["id"] not in srcs:
                    srcs.append(o["id"])
        rights = {i: round(G.rect(nodes[i])[2]) for i in srcs}
        if len(set(rights.values())) > 1:
            out.append(f"{n['id']} {n['type']}: right edges of the sources wired directly into it are not aligned (put them in one column: `inputs {n['id']}`): "
                       + ", ".join(f"{i} right {r}" for i, r in rights.items()))
    return out


@check_rule("empty band across everything")
def _chk_empty_band(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # an empty band running across the whole canvas is wider than the minimum gap (space left without a reason)
    rs = sorted(G.rect(n) for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in NOTE_TYPES)   # Notes do not count
    if rs:
        spans = sorted((r[1], r[3]) for r in rs)
        cur = spans[0][1]
        for y0, y1 in spans[1:]:
            if y0 - cur > V_GAP:
                out.append(f"empty band across everything ({round(y0 - cur)}px tall, min {V_GAP}): y {round(cur)}-{round(y0)}. Is it empty without a reason?")
            cur = max(cur, y1)
    return out


@check_rule("width differences and value node tops")
def _chk_width_and_value_tops(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # nodes stacked vertically whose widths differ by less than H_GAP but are not equal ("width" in readable-form)
    # value nodes side by side whose top edges are not aligned
    body = [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in {"Reroute"} | NOTE_TYPES]
    for i, a in enumerate(body):
        ra = G.rect(a)
        for b in body[i + 1:]:
            rb = G.rect(b)
            ov_x = min(ra[2], rb[2]) - max(ra[0], rb[0]) > 0
            ov_y = min(ra[3], rb[3]) - max(ra[1], rb[1]) > 0
            if ov_x and not ov_y:
                gap_v = max(rb[1] - ra[3], ra[1] - rb[3])
                dw = abs((ra[2] - ra[0]) - (rb[2] - rb[0]))
                if 0 <= gap_v <= V_GAP * 2 and 1 <= dw < H_GAP:
                    out.append(f"stacked nodes differ in width by {round(dw)}px (less than {H_GAP}); make them equal (`width {a['id']} {b['id']}`): {a['id']} and {b['id']}")
            if ov_y and not ov_x and a.get("type") in VALUE_TYPES and b.get("type") in VALUE_TYPES:
                gap_h = max(rb[0] - ra[2], ra[0] - rb[2])
                if 0 <= gap_h <= H_GAP * 2 and abs(ra[1] - rb[1]) >= 1:
                    out.append(f"value nodes side by side have unaligned tops ({round(abs(ra[1] - rb[1]))}px): {a['id']} and {b['id']}")
    return out


@check_rule("Preview or Save above its source")
def _chk_output_above_source(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # Preview above its source
    top_rail = min([y for y, *_ in rail_spans(cv)] or [float("inf")])
    for n in cv.s["nodes"]:
        if n.get("type") not in ("PreviewImage", "SaveImage") or not cv.placed(n):
            continue
        for l in cv.s["links"]:
            if l["target_id"] == n["id"]:
                o = nodes.get(l["origin_id"])
                if o and cv.placed(o) and G.rect(n)[1] < G.rect(o)[1]:
                    up = "; a rail runs above it" if top_rail < G.rect(n)[1] else ""
                    out.append(f"{n['type']} is above its source {o['id']} (do not lift it to dodge wires; that makes rails run higher{up}): {n['id']}")
    return out


def single_loader_kind(cv, n):
    """"MODEL", "CLIP" or "VAE" for a loader that outputs only that type (a checkpoint loader, which outputs several, is None)."""
    if not cv.is_model_loader(n):
        return None
    kinds = {o.get("type") for o in n.get("outputs") or []}
    return next(iter(kinds)) if len(kinds) == 1 else None


def ends_through_reroutes(cv, nid):
    """The wires out of nid, followed through Reroutes: the wires that end at a node that is not a Reroute."""
    nodes, ends, seen, stack = cv.nodes, [], set(), [nid]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        for l in cv.s["links"]:
            if l["origin_id"] == x:
                (stack.append(l["target_id"]) if nodes.get(l["target_id"], {}).get("type") == "Reroute" else ends.append(l))
    return ends


def source_through_reroutes(cv, tid, name):
    """The node that feeds input name of tid, followed back through Reroutes (None if not wired)."""
    nodes, seen = cv.nodes, set()
    while tid not in seen:
        seen.add(tid)
        l = next((l for l in cv.s["links"] if l["target_id"] == tid and (name is None or l["target_input"] == name)), None)
        if not l:
            return None
        o = nodes.get(l["origin_id"])
        if not o or o.get("type") != "Reroute":
            return o
        tid, name = o["id"], None
    return None


def is_decode(n):
    """A node that decodes a latent with a vae: takes LATENT and VAE, outputs IMAGE (VAE Decode, VAE Decode (Tiled) and so on)."""
    ins = {i.get("type") for i in n.get("inputs") or []}
    return {"LATENT", "VAE"} <= ins and "IMAGE" in {o.get("type") for o in n.get("outputs") or []}


@check_rule("loader order")
def _chk_loader_order(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # loaders go from the top: model first, then vae and clip (checkpoint loaders are not counted)
    kinds = {}
    for n in cv.s["nodes"]:
        k = single_loader_kind(cv, n) if cv.placed(n) else None
        if k:
            kinds.setdefault(k, []).append(n)
    if not kinds.get("MODEL"):
        return out
    top = min(kinds["MODEL"], key=lambda n: G.rect(n)[1])
    for k in ("VAE", "CLIP"):
        for n in kinds.get(k, []):
            if G.rect(n)[1] < G.rect(top)[1]:
                out.append(f"{k.lower()} loader {n['id']} is above the model loader {top['id']}: "
                           f"loaders go model first, then vae and clip below it")
    return out


@check_rule("VAE loader below the sampler")
def _chk_vae_below_sampler(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # a vae loader used only by decodes goes above the sampler (compared with the topmost sampler it reaches)
    for n in cv.s["nodes"]:
        if not cv.placed(n) or single_loader_kind(cv, n) != "VAE":
            continue
        ends = ends_through_reroutes(cv, n["id"])
        targets = [nodes.get(l["target_id"]) for l in ends]
        if not targets or not all(t and is_decode(t) for t in targets):
            continue
        samplers = []
        for t in targets:
            lat = next((i["name"] for i in t.get("inputs") or [] if i.get("type") == "LATENT"), None)
            s = source_through_reroutes(cv, t["id"], lat)
            if s and is_sampler(s) and cv.placed(s):
                samplers.append(s)
        if not samplers:
            continue
        s = min(samplers, key=lambda x: G.rect(x)[1])
        if G.rect(n)[1] > G.rect(s)[1]:
            out.append(f"vae loader {n['id']} is used only by VAE Decode and sits below the sampler {s['id']}: "
                       f"put it above the sampler")
    return out


# nodes whose drawing area follows their values, so they grow in ComfyUI (Create Bounding Boxes follows width and height).
# Others may exist; add them when found
GROWS_WITH_VALUES = {"CreateBoundingBoxes"}


def grows(cv, n):
    """Why node n grows in ComfyUI ("sampler", "image", "value-sized"), or None."""
    if is_sampler(n):
        return "sampler"
    if image_kind(n.get("type"), cv.oi):
        return "image"
    if n.get("type") in GROWS_WITH_VALUES:
        return "value-sized"
    return None


@check_rule("below a node that grows")
def _chk_below_growing(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # the nearest node directly below a node that grows (any horizontal overlap: even a node that sticks out only a little is hidden when it grows)
    body = [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in {"Reroute"} | NOTE_TYPES]
    for a in body:
        why = grows(cv, a)
        if not why:
            continue
        ra = G.rect(a)
        best = None
        for b in body:
            if b is a:
                continue
            rb = G.rect(b)
            ov = min(ra[2], rb[2]) - max(ra[0], rb[0])
            if ov > 0 and rb[1] >= ra[3] - 1 and (best is None or rb[1] < G.rect(best)[1]):
                best = b
        if best:
            out.append(f"{best['id']} is directly below {a['id']} ({why}), which grows in ComfyUI: "
                       f"move it out from below (staircase, another column)")
    return out


@check_rule("gaps inside a column")
def _chk_column_gap(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # gap inside a column: two sources of the same node (a column of inputs, as `inputs` or `stack` makes it), stacked
    # vertically, further apart than the minimum gap with nothing between them. Nodes in different rows whose gap
    # follows from making their wires horizontal (a model row above a prompt row) are not a column
    feeds = {}
    for l in cv.s["links"]:
        feeds.setdefault(l["origin_id"], set()).add(l["target_id"])
    body2 = sorted([n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in {"Reroute"} | NOTE_TYPES],
                   key=lambda n: G.rect(n)[1])
    for i, a in enumerate(body2):
        ra = G.rect(a)
        below = None
        for b in body2[i + 1:]:
            rb = G.rect(b)
            if rb[1] >= ra[3] and min(ra[2], rb[2]) - max(ra[0], rb[0]) > 0:
                below = b
                break
        if below is None or not (feeds.get(a["id"], set()) & feeds.get(below["id"], set())):
            continue
        rb = G.rect(below)
        gap = rb[1] - ra[3]
        if gap > V_GAP and not any(rect_overlap(G.rect(m), (max(ra[0], rb[0]), ra[3] + 1, min(ra[2], rb[2]), rb[1] - 1))
                                   for m in cv.s["nodes"] if cv.placed(m) and m["id"] not in (a["id"], below["id"])):
            out.append(f"gap inside a column ({round(gap)}px tall, min {V_GAP}): nothing between {a['id']} and {below['id']}")
    return out


@check_rule("gap to a wired neighbour")
def _chk_wide_gap(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # the gap to a wired neighbour is wider than the standard gap (same row, nothing between them)
    seen_pair = set()
    for l in cv.s["links"]:
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if not o or not t or "Reroute" in (o.get("type"), t.get("type")) or not cv.placed(o) or not cv.placed(t):
            continue
        if (o["id"], t["id"]) in seen_pair:
            continue
        ro, rt = G.rect(o), G.rect(t)
        gap = rt[0] - ro[2]
        if gap <= H_GAP + 1 or min(ro[3], rt[3]) - max(ro[1], rt[1]) <= 0:
            continue
        band = (ro[2] + 1, max(ro[1], rt[1]), rt[0] - 1, min(ro[3], rt[3]))
        if any(rect_overlap(G.rect(m), band) for m in cv.s["nodes"]
               if cv.placed(m) and m["id"] not in (o["id"], t["id"]) and m.get("type") != "Reroute"):
            continue
        seen_pair.add((o["id"], t["id"]))
        out.append(f"wide gap to a wired neighbour ({round(gap)}px, standard gap {H_GAP}): {o['id']} → {t['id']}")
    return out


@check_rule("consecutive Reroutes")
def _chk_consecutive_reroute(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # consecutive Reroutes: from a Reroute with one input and one output straight into the next Reroute at the same height
    for n in cv.s["nodes"]:
        if n.get("type") != "Reroute" or not cv.placed(n):
            continue
        outs = [l for l in cv.s["links"] if l["origin_id"] == n["id"]]
        if len(outs) == 1:
            t = nodes.get(outs[0]["target_id"])
            if t and t.get("type") == "Reroute" and cv.placed(t) and abs(G.rect(t)[1] - G.rect(n)[1]) < 1:
                band = (G.rect(n)[2], G.rect(n)[1], G.rect(t)[0], G.rect(n)[3])
                # only when wiring the first Reroute straight to the targets, without the second one, passes behind no node (one is enough)
                a0 = cv.out_xy(n["id"], 0)
                ends = [(l["target_id"], l["target_input"]) for l in cv.s["links"] if l["origin_id"] == t["id"]]
                direct = all(cv.placed(nodes.get(e, {})) and not any(
                    G.wire_hits(G.spline(a0, cv.in_xy(e, ei)), G.rect(m)) for m in cv.s["nodes"]
                    if cv.placed(m) and m["id"] != e and m.get("type") != "Reroute") for e, ei in ends)
                if direct and not any(rect_overlap(G.rect(m), band) for m in cv.s["nodes"] if cv.placed(m) and m["id"] not in (n["id"], t["id"])):
                    out.append(f"consecutive Reroutes ({n['id']} leads straight into {t['id']}; one is enough): {n['id']} → {t['id']}")
    return out


@check_rule("model Note top edge")
def _chk_model_note_top(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # the model Note is top-aligned with the top of the whole workflow
    tops = [G.rect(m)[1] for m in cv.s["nodes"] if cv.placed(m) and m.get("type") not in NOTE_TYPES]
    for m in cv.s["nodes"]:
        if m.get("type") in NOTE_TYPES and cv.placed(m) and "## models" in str((m.get("widgets_values") or [""])[0]) and tops:
            if abs(G.rect(m)[1] - min(tops)) >= 1:
                out.append(f"model Note top edge is not aligned with the top of the whole workflow ({round(min(tops))}): {m['id']}")
    return out


@check_rule("spacing in a row")
def _chk_row_spacing(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # uneven gaps between nodes wired in one row
    for chain in row_chains(cv):
        gaps = [round(G.rect(nodes[b])[0] - G.rect(nodes[a])[2]) for a, b in zip(chain, chain[1:])]
        if max(gaps) - min(gaps) >= 1:
            out.append(f"uneven spacing in a row ({' → '.join(chain)}: gaps {', '.join(map(str, gaps))})")
    return out


@check_rule("Reroutes doing nothing")
def _chk_idle_reroute(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    for n in cv.s["nodes"]:
        if n.get("type") != "Reroute" or not cv.placed(n):
            continue
        ins = [l for l in cv.s["links"] if l["target_id"] == n["id"]]
        outs = [l for l in cv.s["links"] if l["origin_id"] == n["id"]]
        if len(ins) != 1 or not outs:
            out.append(f"Reroute connected to nothing: {n['id']}")
            continue
        src = ins[0]
        o = nodes.get(src["origin_id"])
        if not o or not cv.placed(o):
            continue
        a = cv.out_xy(o["id"], src["origin_slot"])
        ok = True
        for l in outs:
            t = nodes[l["target_id"]]
            if not cv.placed(t):
                ok = False
                break
            pts = G.spline(a, cv.in_xy(t["id"], l["target_input"]))
            for m in cv.s["nodes"]:
                if m["id"] in (o["id"], t["id"]) or m.get("type") == "Reroute" or not cv.placed(m):
                    continue
                if G.wire_hits(pts, G.rect(m)):
                    ok = False
                    break
            if not ok:
                break
        if ok and all(abs(cv.in_xy(l["target_id"], l["target_input"])[1] - a[1]) < 1 for l in outs):
            out.append(f"Reroute doing nothing (a direct wire from {src['origin_id']} would be horizontal and pass behind nothing): {n['id']}")
    return out


@check_rule("rails that can run at the output height")
def _chk_rail_at_output(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # rails that need no raising Reroute if drawn at the output height
    for n in cv.s["nodes"]:
        if n.get("type") == "Reroute" or not cv.placed(n):
            continue
        for l in cv.s["links"]:
            r = nodes.get(l["target_id"])
            if l["origin_id"] != n["id"] or not r or r.get("type") != "Reroute" or not cv.placed(r):
                continue
            a0 = cv.out_xy(n["id"], l["origin_slot"])
            ry = cv.out_xy(r["id"], 0)[1]
            if abs(a0[1] - ry) < 1:
                continue   # already at the output height
            # whether a horizontal line at the output height hits nothing up to the right end of the rail (the rightmost Reroute
            # down the chain), stopping short of the leftmost target that is not a Reroute: the same range rail uses at the output height
            seen, stack, xmax, ends = set(), [r["id"]], G.rect(r)[2], set()
            while stack:
                x = stack.pop()
                if x in seen:
                    continue
                seen.add(x)
                xmax = max(xmax, G.rect(nodes[x])[2])
                for m in cv.s["links"]:
                    if m["origin_id"] != x:
                        continue
                    if nodes.get(m["target_id"], {}).get("type") == "Reroute":
                        stack.append(m["target_id"])
                    elif cv.placed(nodes.get(m["target_id"], {})):
                        ends.add(m["target_id"])
                        xmax = max(xmax, G.rect(nodes[m["target_id"]])[0] - H_GAP / 2)
            band = (a0[0] + 1, a0[1] - REROUTE_H / 2, xmax, a0[1] + REROUTE_H / 2)
            # targets before the rightmost one count as in the way, as in rail (the line would run on behind them)
            last = {e for e in ends if G.rect(nodes[e])[0] - H_GAP / 2 >= xmax - 0.5}
            blocked = any(rect_overlap(G.rect(m), band) for m in cv.s["nodes"]
                          if cv.placed(m) and m["id"] != n["id"] and m["id"] not in last and m.get("type") != "Reroute")
            if not blocked:
                out.append(f"rail needs no raising Reroute ({r['id']}) if drawn at the output height: output of {n['id']} (draw it with `rail ... out`)")
    return out


@check_rule("rails with a single target")
def _chk_single_target_rail(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # rails with only one target where a direct wire passes behind nothing (no Reroute needed)
    for n in cv.s["nodes"]:
        if n.get("type") == "Reroute" or not cv.placed(n):
            continue
        for l in cv.s["links"]:
            r = nodes.get(l["target_id"])
            if l["origin_id"] != n["id"] or not r or r.get("type") != "Reroute":
                continue
            ends, seen, stack = [], set(), [r["id"]]
            while stack:
                x = stack.pop()
                if x in seen:
                    continue
                seen.add(x)
                for m in cv.s["links"]:
                    if m["origin_id"] == x:
                        (stack.append(m["target_id"]) if nodes.get(m["target_id"], {}).get("type") == "Reroute" else ends.append(m))
            if len(ends) != 1 or not cv.placed(nodes[ends[0]["target_id"]]):
                continue
            e = ends[0]
            pts = G.spline(cv.out_xy(n["id"], l["origin_slot"]), cv.in_xy(e["target_id"], e["target_input"]))
            if not any(G.wire_hits(pts, G.rect(m)) for m in cv.s["nodes"] if cv.placed(m)
                       and m["id"] not in (n["id"], e["target_id"]) and m.get("type") != "Reroute"):
                out.append(f"rail with a single target; a direct wire passes behind nothing, so no Reroute is needed: {n['id']} → {e['target_id']}.{e['target_input']}")
    return out


@check_rule("overlapping rails")
def _chk_rail_overlap(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # overlapping rails: rails from different sources overlap horizontally at the same height
    spans = []
    for l, pts in ws:
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if o and t and o.get("type") == "Reroute" and t.get("type") == "Reroute" and abs(pts[0][1] - pts[-1][1]) < 1:
            root = l["origin_id"]
            seen = set()
            while nodes.get(root, {}).get("type") == "Reroute" and root not in seen:
                seen.add(root)
                up = next((x for x in cv.s["links"] if x["target_id"] == root), None)
                if not up:
                    break
                root = up["origin_id"]
            spans.append((pts[0][1], min(pts[0][0], pts[-1][0]), max(pts[0][0], pts[-1][0]), root, l))
    for i, a in enumerate(spans):
        for b in spans[i + 1:]:
            if a[3] != b[3] and abs(a[0] - b[0]) < P["RAIL_GAP"] and min(a[2], b[2]) > max(a[1], b[1]):
                out.append(f"rails too close or overlapping (vertical gap {abs(a[0] - b[0]):.0f}px, min {P['RAIL_GAP']}): rail of {a[3]} and rail of {b[3]}")
    return out


def rail_starts(cv):
    """Where each rail leaves its source: [(source node, output index, first Reroute)], for every wire from a node that is
    not a Reroute into a Reroute (both placed). The rail height is the height of that Reroute's output slot."""
    nodes = cv.nodes
    out = []
    for l in cv.s["links"]:
        o, r = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if not o or not r or o.get("type") == "Reroute" or r.get("type") != "Reroute" or not cv.placed(o) or not cv.placed(r):
            continue
        out.append((o, l["origin_slot"], r))
    return out


@check_rule("rail order and loader order")
def _chk_rail_order(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # rails carrying MODEL, CLIP or VAE from loaders run top to bottom in the same order as their loaders are stacked.
    # A pair whose vertical order is the reverse of their loaders' order is reported (rails of one loader are not compared)
    rails = [(o, r, cv.out_xy(r["id"], 0)[1]) for o, _, r in rail_starts(cv) if cv.is_model_loader(o)]
    seen = set()
    for i, (oa, ra, ya) in enumerate(rails):
        for ob, rb, yb in rails[i + 1:]:
            if oa["id"] == ob["id"] or (oa["id"], ob["id"]) in seen:
                continue
            ta, tb = G.rect(oa)[1], G.rect(ob)[1]
            if abs(ya - yb) < 1 or abs(ta - tb) < 1 or (ya < yb) == (ta < tb):
                continue
            seen |= {(oa["id"], ob["id"]), (ob["id"], oa["id"])}
            up, down = (oa, ob) if ta < tb else (ob, oa)
            out.append(f"rail order differs from loader order (loader {up['id']} is above {down['id']}, but its rail runs below): "
                       f"rail of {up['id']} and rail of {down['id']}")
    return out


@check_rule("raising Reroutes right of a loader")
def _chk_loader_raise(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # a rail from a loader (MODEL, CLIP or VAE) with a raising Reroute just to the right of the loader: the loader can sit
    # at the rail height instead, and then the Reroute is not needed
    for o, slot, r in rail_starts(cv):
        if not cv.is_model_loader(o):
            continue
        ay, ry = cv.out_xy(o["id"], slot)[1], cv.out_xy(r["id"], 0)[1]
        rx, ox1 = G.rect(r)[0], G.rect(o)[2]
        if abs(ay - ry) < 1 or not (ox1 <= rx <= ox1 + H_GAP):
            continue
        out.append(f"raising Reroute right of a loader ({r['id']}): move the loader to the rail height "
                   f"(`move {o['id']} 0 {ry - ay:+.0f}`, or place it there) so the Reroute is not needed: {o['id']}")
    return out


@check_rule("loader rails above their targets")
def _chk_loader_rail_above(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # a rail from a loader (MODEL, CLIP or VAE) runs above the nodes it hands out to. Reported when the rail height is
    # below the top edge of the highest target (the first nodes that are not Reroutes down the chain)
    for o, _, r in rail_starts(cv):
        if not cv.is_model_loader(o):
            continue
        ry = cv.out_xy(r["id"], 0)[1]
        ends, seen, stack = [], set(), [r["id"]]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            for m in cv.s["links"]:
                if m["origin_id"] != x:
                    continue
                t = nodes.get(m["target_id"], {})
                if t.get("type") == "Reroute":
                    stack.append(m["target_id"])
                elif cv.placed(t):
                    ends.append(t)
        if ends and ry > min(G.rect(t)[1] for t in ends):
            out.append(f"loader rail runs below its targets (model, vae and clip rails go above): rail of {o['id']}")
    return out


@check_rule("group titles, overhangs and overlaps")
def _chk_groups(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    cv.update_groups()
    for g in cv.s["groups"]:
        if not g.get("bounding"):
            continue
        gx, gy, gw, gh = g["bounding"]
        band = (gx, gy, gx + gw, gy + GROUP_TITLE_H)
        for l, pts in ws:
            if G.wire_hits(pts, band, margin=0):
                out.append(f"wire over the title of group \"{g['title']}\": {lname(cv, l)}")
        for n in cv.s["nodes"]:
            if cv.placed(n) and rect_overlap(G.rect(n), band):
                out.append(f"node over the title of group \"{g['title']}\": {n['id']}")
        for n in cv.s["nodes"]:
            if cv.placed(n) and n.get("type") != "Reroute" and n["id"] not in g["members"] and rect_overlap(G.rect(n), (gx, gy, gx + gw, gy + gh)):
                out.append(f"node overlapping group \"{g['title']}\" but not in it: {n['id']}")
    gs = [g for g in cv.s["groups"] if g.get("bounding")]
    for i, a in enumerate(gs):
        for b in gs[i + 1:]:
            ra = (a["bounding"][0], a["bounding"][1], a["bounding"][0] + a["bounding"][2], a["bounding"][1] + a["bounding"][3])
            rb = (b["bounding"][0], b["bounding"][1], b["bounding"][0] + b["bounding"][2], b["bounding"][1] + b["bounding"][3])
            if rect_overlap(ra, rb):
                out.append(f"groups overlap: \"{a['title']}\" and \"{b['title']}\"")
    return out


@check_rule("types and required inputs")
def _chk_validate(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    flat = cv.flat()
    for n in flat["nodes"]:
        n["mode"] = 0   # a node's mode is the author's choice, not a problem; the mode is compared by diff
    for p in VD.check(flat, cv.oi):
        out.append(p)
    return out


def full_check(cv):
    """All checks: the message lines from applying the rules top to bottom, and the counts for the first line."""
    c = _CheckCtx(cv)
    out = []
    for _, fn in CHECKS:
        out += fn(cv, c)
    return out, c.count


# ---------------------------------------------------------------- open and src

def load_source(path, oi):
    """Reads the source workflow and returns the expanded flat graph and a list of things noticed while reading.
    open and diff read the same way: expand legacy group nodes -> load (expand subgraphs, wireless to wires)
    -> report mismatched subgraph exits."""
    src_json = jload(path)
    src_json, warns = LG.expand(src_json, oi) if isinstance(src_json, dict) else (src_json, [])
    raw = RW.load(src_json)
    flat = FL.flatten(raw, oi)
    warns = list(warns) + list(flat.get("warnings") or []) + subgraph_exit_mismatch(raw.get("raw") or {})
    return flat, warns


def workflow_hash(wf):
    return hashlib.sha256(json.dumps(wf, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def canvases_hash(work):
    """One hash of every canvas's current state (what the replay page is made from)."""
    h = hashlib.sha256()
    for name in work.names():
        h.update(name.encode("utf-8"))
        h.update(work.canvas_path(name).read_bytes())
    return h.hexdigest()


def _file_hash(path, json_workflow=False):
    """The hash of a file the canvas wrote (of the workflow it holds, for an exported workflow). None if it cannot be read."""
    try:
        if json_workflow:
            return workflow_hash(jload(path))
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except (OSError, TypeError, ValueError):
        return None


# files the canvas writes in the working folder, and the understanding document SKILL.md names
WORK_FILES = ("object_info.json", "src.flat.json", "source.ui.json", "canvas.config.json", "understanding.md")


def do_finish(work):
    """Deletes the working folder once every canvas is exported and the replay page is up to date.
    Only files the canvas knows are deleted, one by one: what it wrote, the plan and Note files it was given (if they are
    inside the working folder) and understanding.md. Anything else is left, and then the folder is left too.
    With the environment variable CANVAS_KEEP_WORK=1 nothing is deleted; the files are only listed."""
    if not work.names():
        raise Stop("no canvas (nothing to finish). Nothing is deleted")
    missing = []
    exported = work.cfg.get("exported") or {}
    for name in work.names():
        rec = exported.get(name)
        now = workflow_hash(Canvas(work, name).workflow()[0])
        if not isinstance(rec, dict) or rec.get("hash") != now:
            missing.append(f"canvas {name} has changed since it was exported (or was never exported): `use {name}` and `export <name>.json`")
        elif _file_hash(rec.get("path"), json_workflow=True) != now:
            missing.append(f"the exported file of canvas {name} is missing or was changed ({rec.get('path')}): `use {name}` and `export <name>.json`")
    rep_ = work.cfg.get("replayed")
    if not isinstance(rep_, dict) or rep_.get("canvases") != canvases_hash(work):
        missing.append("the replay page is older than the canvases: `replay <html> <lang>`")
    elif _file_hash(rep_.get("path")) != rep_.get("file"):
        missing.append(f"the replay page is missing or was changed ({rep_.get('path')}): `replay <html> <lang>`")
    if missing:
        raise Stop("not finished. Nothing is deleted:\n  " + "\n  ".join(missing))
    root = os.path.abspath(work.dir)

    def inside(p):
        try:
            return os.path.commonpath([root, os.path.abspath(p)]) == root and os.path.abspath(p) != root
        except ValueError:   # another drive (Windows): outside
            return False

    # every path absolute, so that the same file given two ways is listed once
    files = [Path(root) / f for f in WORK_FILES]
    for name in work.names():
        cv_path = Path(root) / "canvas" / f"{name}.json"
        files.append(cv_path)
        files += sorted(cv_path.with_suffix(".hist").glob("*.json"))
    files += [Path(os.path.abspath(p)) for p in work.cfg.get("consumed") or []]
    files = [f for f in dict.fromkeys(files) if inside(f) and (f.is_file() or f.is_symlink())]
    dirs = [Path(root) / "canvas" / f"{n}.hist" for n in work.names()] + [Path(root) / "canvas", Path(root)]
    if os.environ.get("CANVAS_KEEP_WORK") == "1":
        return ["CANVAS_KEEP_WORK=1: nothing deleted. finish would delete:"] + [f"  {os.path.relpath(f, root)}" for f in files]
    for f in files:
        f.unlink(missing_ok=True)   # a symlink: only the link
    for d in dirs:
        try:
            d.rmdir()
        except OSError:
            pass
    if os.path.exists(root):
        left = sorted(os.path.relpath(os.path.join(dp, f), root) for dp, _, fs in os.walk(root) for f in fs)
        if not left:
            return [f"deleted {len(files)} files. The working folder {root} is empty but could not be removed "
                    f"(it is the current directory?): remove it from outside"]
        return [f"deleted {len(files)} files. The canvas does not know these, so they and the working folder were left: "
                + ", ".join(left)]
    return [f"deleted the working folder {root} ({len(files)} files)"]


def do_open(work, args):
    if len(args) < 2:
        raise Stop("open <workflow.json> <object_info URL or JSON>")
    wf_path, oi_src = args[0], args[1]
    oi = CS.load_object_info(oi_src)
    work.dir.mkdir(parents=True, exist_ok=True)
    jdump(work.dir / "object_info.json", oi)
    work._oi = oi
    out = []
    raw = jload(wf_path)
    if AF.is_api(raw):
        # no positions in API format: read it as ComfyUI opens it (the original view and diff use this file)
        ui, warns = AF.to_ui(raw, oi)
        wf_path = str(work.dir / "source.ui.json")
        jdump(wf_path, ui)
        out.append(f"API format: {len(ui['nodes'])} nodes. There were no positions, sizes, groups, Notes or bypassed nodes; "
                   f"placed as ComfyUI places them when it opens an API-format file (source.ui.json). Say so in the report")
        out += [f"warning: {w}" for w in warns]
    flat, warns = load_source(wf_path, oi)
    out.append(f"read: {len(flat['nodes'])} nodes, {len(flat['links'])} wires")
    out += [f"warning: {w}" for w in warns]
    repl, warn = {}, []
    if oi_src.startswith("http"):
        try:
            repl = RP.load_replacements(oi_src)
        except Exception as e:  # noqa: BLE001
            warn.append(f"cannot read the official replacement list ({e})")
    else:
        warn.append("object_info is a saved file, so the official replacement list was not used")
    records, warnings = RP.Replacer(flat, oi, repl).run()
    for r in records:
        extra = []
        for k, label in (("set_value", "value set by the list"), ("dropped_values", "values not copied"), ("dropped_links", "wires cut")):
            if r.get(k):
                extra.append(f"{label} {r[k]}")
        out.append(f"replaced: {RP.describe(r)}" + ("  " + "; ".join(extra) if extra else ""))
    for w in warn + warnings:
        out.append(f"warning: {w}")
    for nid, t, wname, value in return_typed_values(flat, oi):
        out.append(f"returned value: {nid} ({json.dumps(value, ensure_ascii=False)[:40]}) → {t}.{wname} (value node wired to a single target)")
    # Preview Image nodes that only show what was loaded
    nodes = {n["id"]: n for n in flat["nodes"]}
    gone = []
    for n in flat["nodes"]:
        if n["type"] == "PreviewImage":
            src = next((l for l in flat["links"] if l["target_id"] == n["id"]), None)
            if src and nodes.get(src["origin_id"], {}).get("type") in SELF_PREVIEW_LOADERS:
                gone.append((n["id"], f"only shows {src['origin_id']} {nodes[src['origin_id']]['type']} as loaded"))
    drop = {i for i, _ in gone}
    flat["nodes"] = [n for n in flat["nodes"] if n["id"] not in drop]
    flat["links"] = [l for l in flat["links"] if l["origin_id"] not in drop and l["target_id"] not in drop]
    for i, why in gone:
        out.append(f"removed: {i} {nodes[i]['type']} ({why})")
    flat["source"] = str(Path(wf_path).resolve())
    jdump(work.dir / "src.flat.json", flat)
    work.cfg["source"] = flat["source"]
    work.cfg["object_info"] = oi_src
    work.save_cfg()
    out += src_summary(flat, oi)
    return out


def subgraph_exit_mismatch(raw):
    """Subgraph exits whose linkIds disagree with the saved wires. The file is broken and the frontend reads it as is
    (which wire is used depends on how the frontend reads it). It may differ from the author's intent, so it is reported."""
    out = []
    for sg in ((raw.get("definitions") or {}).get("subgraphs") or []):
        links = {}
        for l in sg.get("links") or []:
            if isinstance(l, dict):
                links[l["id"]] = (l["origin_id"], l["origin_slot"], l["target_id"], l["target_slot"])
            else:
                links[l[0]] = (l[1], l[2], l[3], l[4])
        seen = {}
        for i, o in enumerate(sg.get("outputs") or []):
            for lid in dict.fromkeys(o.get("linkIds") or []):
                seen.setdefault(lid, set()).add(o.get("name"))
                l = links.get(lid)
                if l and l[3] != i and l[3] >= 0:   # negative numbers are old unused records (the frontend ignores them too)
                    out.append(f"subgraph \"{sg.get('name')}\": exit {o.get('name')} lists wire {lid}, which goes into another exit (#{l[3]})"
                               f" (output {l[1]} of inner node {l[0]}). Inconsistent file. Check which wire is used and whether it matches the author's intent")
        for lid, names in seen.items():
            if len(names) > 1:
                out.append(f"subgraph \"{sg.get('name')}\": wire {lid} goes into more than one exit ({', '.join(sorted(names))}). Inconsistent file")
    return out


VALUE_TYPES = {"PrimitiveInt", "PrimitiveFloat", "PrimitiveString", "PrimitiveStringMultiline", "PrimitiveBoolean",
               "PrimitiveNode", "ComfyMathExpression", "StringFormat", "SeedNode"}
TYPED_VALUE_TYPES = {"PrimitiveInt", "PrimitiveFloat", "PrimitiveString", "PrimitiveStringMultiline", "PrimitiveBoolean",
                     "SeedNode"}


def return_typed_values(flat, oi):
    """Moves the value of a typed value node (PrimitiveInt etc.) wired to a single target widget into that widget and removes the node.
    The same as what replace.py does for PrimitiveNode. Not done when the value node's control is not fixed and the target has no control."""
    R = RP.Replacer(flat, oi, {})
    done = []
    for nid in [n for n, x in R.nodes.items() if x.get("type") in TYPED_VALUE_TYPES]:
        node = R.nodes[nid]
        if node.get("mode", 0) != 0:
            continue
        wv = node.get("widgets_values") or []
        if not wv:
            continue
        value = wv[0]
        control = wv[1] if len(wv) > 1 and isinstance(wv[1], str) else "fixed"
        lids = [lid for o in node.get("outputs") or [] for lid in (o.get("links") or []) if lid in R.links]
        if len(lids) != 1:
            continue
        l = R.links[lids[0]]
        t = R.nodes.get(l["target_id"])
        inp = next((i for i in (t.get("inputs") or []) if i["name"] == l["target_input"]), None) if t else None
        wname = (inp.get("widget") or {}).get("name") if inp else None
        info = oi.get(t.get("type")) if t else None
        if not wname or not info:
            continue
        names = CS.widget_names(info, t.get("widgets_values"))
        ctrl = R._control_of(info, names, wname, t.get("widgets") or {})
        if (control == "fixed" or ctrl) and R._set_widget(t, wname, value):
            if ctrl:
                R._set_widget(t, ctrl, control)
            R._disconnect(l["id"])
            R._remove_node(nid)
            done.append((nid, t["id"], wname, value))
    return done


def src_summary(flat, oi):
    out = []
    outs = [n for n in flat["nodes"] if (oi.get(n["type"]) or {}).get("output_node")]
    out.append(f"output nodes {len(outs)}: " + ", ".join(f"{n['id']} {n['type']}" + (f" (mode {n.get('mode')})" if n.get("mode") else "") for n in outs))
    stopped = [n for n in flat["nodes"] if n.get("mode") in (2, 4)]
    if stopped:
        out.append(f"disabled nodes {len(stopped)}: " + ", ".join(f"{n['id']} {n['type']} ({'mute' if n['mode'] == 2 else 'bypass'})" for n in stopped))
    sw = [n for n in flat["nodes"] if "switch" in n["type"].lower()]
    if sw:
        out.append("switch: " + ", ".join(f"{n['id']} {n['type']}" for n in sw))
    cust = {}
    for n in flat["nodes"]:
        if n["type"] not in NOTE_TYPES and is_custom(n["type"], oi):
            cust.setdefault(n["type"], []).append(n["id"])
    if cust:
        out.append("custom node: " + ", ".join(f"{t} ({' '.join(ids)})" + ("" if t in oi else " [not installed]") for t, ids in sorted(cust.items())))
        for t in sorted(cust):
            near = core_like(t, oi)
            if near:
                out.append(f"  core nodes with names close to {t} (check the source code to see whether they can replace it): " + ", ".join(near))
    models = NT.collect_models(flat)
    if models:
        out.append("models: " + ", ".join(sorted(models)))
    aw = flat.get("author_words") or {}
    notes = [n for n in flat["nodes"] if n["type"] in NOTE_TYPES]
    out.append(f"author's words: Notes {len(notes)}, groups {len(aw.get('groups') or [])}, titles {len(aw.get('titles') or {})} (read them with src words)")
    return out


WORD_RE = re.compile(r"[A-Z]{2,}(?=[A-Z][a-z]|\b|_|\d)|[A-Z]?[a-z]+|[A-Z]{2,}|\d+")


def words_of(text):
    return {w.lower() for w in WORD_RE.findall(text) if len(w) >= 3}


_CORE_WORDS = None


def core_like(t, oi):
    """Core nodes that share a word with the custom node's type name (SUPIR, color, match etc.).
    Looks at type names, display names and search_aliases. API nodes are excluded. Words that appear in many core nodes (more than 30) do not count."""
    global _CORE_WORDS
    if _CORE_WORDS is None:
        _CORE_WORDS = {}
        for k, v in oi.items():
            mod = str(v.get("python_module", ""))
            if mod.startswith("custom_nodes") or mod.startswith("comfy_api_nodes"):
                continue
            ws = words_of(" ".join([k, v.get("display_name") or ""] + list(v.get("search_aliases") or [])))
            _CORE_WORDS[k] = (ws, v.get("display_name") or k)
    df = {}
    for ws, _ in _CORE_WORDS.values():
        for w in ws:
            df[w] = df.get(w, 0) + 1
    mine = {w for w in words_of(t.split("|")[0].replace("(", " ").replace(")", " ")) if df.get(w, 0) and df[w] <= 30}
    mine -= {"easy", "rgthree", "pysssss", "crystools", "vhs", "comfy", "any", "kj"}   # names of custom node authors and packs
    if not mine:
        return []
    hits = sorted(((-len(mine & ws), k, d) for k, (ws, d) in _CORE_WORDS.items() if mine & ws))
    best = hits[0][0] if hits else 0
    return [f"{k} ({d})" for n, k, d in hits if n == best][:6]


def src_node_lines(flat, oi, nid):
    nodes = {n["id"]: n for n in flat["nodes"]}
    n = nodes.get(nid)
    if not n:
        raise Stop(f"the source has no node {nid}")
    out = [f"{nid} {n['type']}" + (f"  mode {n.get('mode')}" if n.get("mode") else "") + ("  [custom]" if is_custom(n["type"], oi) else "")]
    for i in n.get("inputs") or []:
        l = next((l for l in flat["links"] if l["target_id"] == nid and l["target_input"] == i["name"]), None)
        if l:
            o = nodes[l["origin_id"]]
            oname = ((o.get("outputs") or [])[l["origin_slot"]].get("name")) if l["origin_slot"] < len(o.get("outputs") or []) else l["origin_slot"]
            out.append(f"  in  {i['name']} ({i.get('type')}) ← {l['origin_id']}.{oname} {o['type']}")
        elif not i.get("widget"):
            out.append(f"  in  {i['name']} ({i.get('type')}) ← none")
    for k, o in enumerate(n.get("outputs") or []):
        ts = [f"{l['target_id']}.{l['target_input']}" for l in flat["links"] if l["origin_id"] == nid and l["origin_slot"] == k]
        out.append(f"  out {o.get('name')} ({o.get('type')}) → {' '.join(ts) or 'none'}")
    info = oi.get(n["type"])
    vals = n.get("widgets_values")
    if info and isinstance(vals, list):
        named, _ = CS.map_widget_values(n["type"], vals, oi)
        for k, v in (named or {}).items():
            out.append(f"  value {k} = {json.dumps(v, ensure_ascii=False)[:200]}")
    elif vals:
        out.append(f"  values {json.dumps(vals, ensure_ascii=False)[:400]}")
    return out


def do_src(work, args):
    flat, oi = work.src(), work.oi
    if not args:
        raise Stop("src <outputs|list|all|node|up|words>")
    sub = args[0]
    nodes = {n["id"]: n for n in flat["nodes"]}
    if sub == "outputs":
        out = []
        for n in flat["nodes"]:
            if (oi.get(n["type"]) or {}).get("output_node"):
                up = upstream(flat, n["id"])
                out.append(f"{n['id']} {n['type']}" + (f" (mode {n.get('mode')})" if n.get("mode") else "") + f"  upstream {len(up)}")
        return out
    if sub == "list":
        q = (args[1] if len(args) > 1 else "").lower()
        return [f"{n['id']} {n['type']}" + (f"  mode {n.get('mode')}" if n.get("mode") else "") + ("  [custom]" if n["type"] not in NOTE_TYPES and is_custom(n["type"], oi) else "")
                for n in flat["nodes"] if q in n["type"].lower()]
    if sub == "node":
        out = []
        for nid in args[1:]:
            out += src_node_lines(flat, oi, nid)
        return out
    if sub == "all":
        out = []
        for n in flat["nodes"]:
            if n["type"] not in NOTE_TYPES:
                out += src_node_lines(flat, oi, n["id"])
        return out
    if sub == "up":
        if len(args) < 2:
            raise Stop("src up <id>")
        up = upstream(flat, args[1])
        return [f"{i} {nodes[i]['type']}" for i in flat_order(flat) if i in up]
    if sub == "words":
        aw = flat.get("author_words") or {}
        out = []
        for g in aw.get("groups") or []:
            out.append(f"group \"{g.get('title')}\": {' '.join(str(x) for x in g.get('nodes') or [])}")
        for t in aw.get("titles") or []:
            out.append(f"title {t.get('id')} {t.get('type')}: {t.get('title')}")
        for s in aw.get("subgraphs") or []:
            out.append(f"subgraph: {s}")
        for n in flat["nodes"]:
            if n["type"] in NOTE_TYPES:
                out.append(f"Note {n['id']}:\n{(n.get('widgets_values') or [''])[0]}")
        return out
    raise Stop(f"unknown: src {sub} (src <outputs|list|all|node|up|words>)")


def upstream(flat, nid):
    seen, stack = set(), [nid]
    while stack:
        x = stack.pop()
        for l in flat["links"]:
            if l["target_id"] == x and l["origin_id"] not in seen:
                seen.add(l["origin_id"])
                stack.append(l["origin_id"])
    return seen


def flat_order(flat):
    return [n["id"] for n in flat["nodes"]]




# the list of workflows on the skill author's site, shipped with the skill (a copy of https://comfyui.nomadoor.net/workflows/index.json)
SITE_CATALOG = Path(__file__).resolve().parent.parent / "references" / "site" / "index.json"


def site_catalog():
    """The skill author's site (Comfy with ComfyUI) publishes one list of its workflows: for each, the URL,
    the articles that explain it (title and heading per language), the date it was last updated, the models
    it needs (file name, models/ folder, download URL) and its custom nodes. The skill carries a copy of it
    (references/site/index.json); this reads the copy and never the network."""
    if not SITE_CATALOG.is_file():
        raise Stop(f"the copy of the workflow list of the skill author's site is missing ({SITE_CATALOG}). "
                   "Build the core without a reference")
    try:
        return jload(SITE_CATALOG)
    except (OSError, ValueError) as e:
        raise Stop(f"cannot read the copy of the workflow list of the skill author's site ({SITE_CATALOG}): {e}. "
                   "Build the core without a reference")


def do_refs(args):
    """Workflows on the skill author's site whose file path or article title / heading contains all the words, newest first."""
    if not args:
        raise Stop("refs <word> ... (e.g. refs anima compare)")
    words = [a.lower() for a in args]
    hits = []
    for w in site_catalog().get("workflows") or []:
        arts = w.get("articles") or []
        text = " ".join([w.get("url", "")] + [f"{a.get('title', '')} {a.get('heading') or ''}" for a in arts]).lower()
        if all(x in text for x in words):
            en = next((a for a in arts if a.get("lang") == "en"), arts[0] if arts else {})
            about = " / ".join(x for x in (en.get("title"), en.get("heading")) if x)
            hits.append((w.get("updated") or "", w["url"], about))
    hits.sort(key=lambda h: h[0], reverse=True)
    out = [f"{u or '?'}  {url}" + (f"  ({about})" if about else "") for u, url, about in hits[:10]]
    if len(hits) > 10:
        out.append(f"{len(hits) - 10} more (add words to narrow down)")
    return out or ["nothing found (try other words; the site may have no workflow for this use)"]


# File names that many repositories use for different models (diffusers and transformers layouts).
# The file name alone does not tell which model it is.
GENERIC_MODEL_NAMES = {
    "diffusion_pytorch_model.safetensors", "diffusion_pytorch_model.fp16.safetensors", "diffusion_pytorch_model.bin",
    "model.safetensors", "model.fp16.safetensors", "model.bin", "model.pt", "model.pth", "model.ckpt", "model.onnx",
    "pytorch_model.bin", "pytorch_model.fp16.bin", "adapter_model.safetensors", "adapter_model.bin",
    "pytorch_lora_weights.safetensors", "config.json",
}
SHARD_RE = re.compile(r"-\d+-of-\d+\.[^.]+$")


def _same_file_url(url):
    """A download URL without what does not change the file (the query, and /blob/ for /resolve/ on Hugging Face)."""
    return url.split("?")[0].replace("/blob/", "/resolve/")


def _site_models():
    """{file name: {directory, url}} from the site's list, for models whose download URL is known.
    A file name that is too generic to tell the model maps to {"generic": True}: a name in GENERIC_MODEL_NAMES,
    a sharded file, or a name that the list gives two or more different URLs."""
    out, urls = {}, {}
    for w in site_catalog().get("workflows") or []:
        for m in w.get("models") or []:
            if m.get("name") and m.get("url"):
                base = m["name"].replace("\\", "/").split("/")[-1]
                out.setdefault(base, m)
                urls.setdefault(base, set()).add(_same_file_url(m["url"]))
    for base in out:
        if base.lower() in GENERIC_MODEL_NAMES or SHARD_RE.search(base) or len(urls[base]) > 1:
            out[base] = {"generic": True}
    return out


def do_models(work):
    """From the nodes of all canvases if any exist, otherwise from the source."""
    names = work.names()
    if names:
        flat = {"nodes": [n for name in names for n in Canvas(work, name).s["nodes"]]}
    else:
        flat = work.src()
    found = NT.collect_models(flat)
    server = work.cfg.get("object_info") if str(work.cfg.get("object_info", "")).startswith("http") else None
    if server and any(not m["directory"] for m in found.values()):
        finder = NT.FolderFinder(server, work.oi)
        for m in found.values():
            if not m["directory"]:
                m["directory"] = finder.find(m)
    out = []
    if any(not m["url"] or not m["directory"] for m in found.values()):
        try:
            site = _site_models()
        except Stop as e:
            site = {}
            out.append(f"warning: {e}")
        for m in found.values():
            base = m["name"].replace("\\", "/").split("/")[-1]
            hit = site.get(base)
            if hit and hit.get("generic"):
                if not m["url"]:
                    m["too_generic"] = True
                continue
            if hit and (not m["url"] or not m["directory"]):
                m["url"] = m["url"] or hit.get("url")
                m["directory"] = m["directory"] or hit.get("directory")
                m["from_site"] = True
    for m in found.values():
        out.append(f"- {m['name']}  folder: {m['directory'] or '?'}  URL: {m['url'] or '?'}"
                   + ("  (from the skill author's site)" if m.get("from_site") else "")
                   + ("  (file name too generic to look up)" if m.get("too_generic") else ""))
    out.append("draft of the model Note text (fill in unknown folders and URLs from the author's Notes, or search for the file):")
    out.append(NT.model_note_text(list(found.values())))
    return out


# ---------------------------------------------------------------- commands

def parse_opts(args, flags=(), keyed=()):
    """Splits into positional arguments, flags (taken as they are) and keyed options (which take the next value)."""
    pos, opt = [], {}
    i = 0
    while i < len(args):
        a = args[i]
        if a in keyed and i + 1 < len(args):
            opt[a] = args[i + 1]
            i += 2
            continue
        if a in flags:
            opt[a] = True
        else:
            pos.append(a)
        i += 1
    return pos, opt


def num(s, what="value"):
    try:
        return float(s)
    except (TypeError, ValueError):
        raise Stop(f"{what} {s} is not a number")


def put_rel(cv, ids, how, ref_ids, align, gap):
    w, h = cv.unit_size(ids)
    rb = cv.bbox(ref_ids)
    if how in ("right", "left"):
        g = H_GAP if gap is None else gap
        x0 = rb[2] + g if how == "right" else rb[0] - g - w
        align = align or "top"
        if align == "top":
            y0 = rb[1]
        elif align == "bottom":
            y0 = rb[3] - h
        elif align == "middle":
            y0 = (rb[1] + rb[3]) / 2 - h / 2
        elif align == "wire":
            y0 = rb[1]
        else:
            raise Stop(f"unknown alignment {align} for {how} (top bottom middle wire)")
        cv.place_unit(ids, x0, y0)
        if align == "wire":
            l = cv.link_between(ref_ids, ids)
            if not l:
                raise Stop("no wire between the reference and the unit (wire makes a wire horizontal)")
            dy = cv.level_dy(l, set(ids))
            cv.translate(ids, 0, dy)
            cv.out.append(f"made horizontal: {lname(cv, l)}")
    elif how in ("below", "above"):
        g = V_GAP if gap is None else gap
        y0 = rb[3] + g if how == "below" else rb[1] - g - h
        align = align or "left"
        if align == "left":
            x0 = rb[0]
        elif align == "right":
            x0 = rb[2] - w
        elif align == "center":
            x0 = (rb[0] + rb[2]) / 2 - w / 2
        else:
            raise Stop(f"unknown alignment {align} for {how} (left right center)")
        cv.place_unit(ids, x0, y0)
    else:
        raise Stop(f"unknown placement {how} (right left below above origin)")


ALIGNS = {"top", "bottom", "middle", "wire", "left", "right", "center"}


# usage returned instead of a Python error when arguments are missing (command: (minimum count, usage))
MIN_ARGS = {
    "use": (1, "use <name>"), "title": (1, "title <id> <title>"), "unblock": (1, "unblock <name>"),
    "ungroup": (1, "ungroup <title>"), "width": (1, "width <id> <id> ..."), "rm": (1, "rm <id> ..."),
    "mode": (2, "mode <on|bypass|mute> <id> ..."), "color": (2, "color <color> <id> ..."),
    "move": (3, "move <unit> <dx> <dy>"), "layout": (1, "layout <plan file>"),
}


def need_file(path, what):
    if not Path(path).is_file():
        raise Stop(f"no {what} {path}")
    return Path(path)


def run_cmd(work, line):
    """Runs one command. When it stops, the reason is raised as Stop (Python errors are wrapped in Stop too; the state is not changed)."""
    try:
        return _run_cmd(work, line)
    except Stop:
        raise
    except Exception as e:  # noqa: BLE001  a bug in the canvas. Report what happened instead of a traceback
        raise Stop(f"stopped by a canvas error: {type(e).__name__}: {e}") from e


def _run_cmd(work, line):
    toks = shlex.split(line, comments=True)
    if not toks:
        return []
    cmd, args = toks[0], toks[1:]
    if cmd in MIN_ARGS and len(args) < MIN_ARGS[cmd][0]:
        raise Stop(f"missing arguments: {MIN_ARGS[cmd][1]}")
    if cmd == "open":
        return do_open(work, args)
    if cmd == "src":
        return do_src(work, args)
    if cmd == "models":
        return do_models(work)
    if cmd == "refs":
        return do_refs(args)
    if cmd == "finish":
        return do_finish(work)
    if cmd == "list":
        cur = work.cfg.get("current")
        return [("* " if n == cur else "  ") + n for n in work.names()] or ["no canvases"]
    if cmd == "new":
        if not args:
            raise Stop("new <name> [from <canvas>]")
        if work.canvas_path(args[0]).exists():
            raise Stop(f"canvas {args[0]} already exists (select it with use)")
        cv = Canvas(work, args[0], fresh=True)
        if len(args) >= 3 and args[1] == "from":
            base = Canvas(work, args[2])
            cv.s = copy.deepcopy(base.s)
            cv.s["name"] = args[0]
            cv.s["history"] = [f"new {args[0]} from {args[2]}"]
            cv.s.pop("layout_notes", None)   # keyed by the other canvas's undo snapshots
        cv.save()
        work.cfg["current"] = args[0]
        work.save_cfg()
        return [f"made canvas {args[0]}" + (f" (copy of {args[2]})" if len(args) >= 3 and args[1] == "from" else "")]
    if cmd == "use":
        Canvas(work, args[0])
        work.cfg["current"] = args[0]
        work.save_cfg()
        return [f"current canvas: {args[0]}"]
    if cmd == "diff":
        if not work.cfg.get("source"):
            raise Stop("not opened yet (run open first)")
        src, _ = load_source(need_file(work.cfg["source"], "source workflow"), work.oi)
        outs = []
        for name in work.names():
            c = Canvas(work, name)
            f = c.flat()
            for n in f["nodes"]:
                # compare with unsaved widgets filled with defaults, as on the source side (flatten)
                if n.get("type") in work.oi and isinstance(n.get("widgets_values"), list):
                    n["widgets"] = CS.map_widget_values(n["type"], n["widgets_values"], work.oi)[0]
            outs.append((name, f))
        lines = CMP.compare(src, outs, work.oi)
        return [f"differences {len(lines)} (not necessarily errors: give the reason if intended, fix it if not):"] + ["  " + s for s in lines] if lines else ["differences: none"]

    cv = work.current()
    if cmd == "undo":
        last = cv.undo()
        return [f"undone: {last}"]
    if cmd == "history":
        return [f"{k + 1}: {h}" for k, h in enumerate(cv.s["history"])]
    if cmd == "show":
        return show(cv)
    if cmd == "between":
        blocks = dict(cv.s["blocks"])
        if args:
            blocks = {}
            for raw in need_file(args[0], "plan file").read_text(encoding="utf-8").splitlines():
                toks = shlex.split(raw, comments=True)
                if toks and toks[0] == "block" and len(toks) >= 3:
                    ids = []
                    for t in toks[2:]:
                        ids += blocks.get(t, [t])
                    blocks[toks[1]] = ids
        if not blocks:
            raise Stop("no blocks (between <plan file> counts from the block lines of the file)")
        return between(cv, blocks)
    if cmd == "node":
        out = []
        for nid in args:
            out += node_lines(cv, nid)
        return out
    if cmd == "check":
        lines, counts = full_check(cv)
        head = "counts: " + ", ".join(f"{k} {v}" for k, v in counts.items())
        return [head] + (lines or ["no problems"])
    if cmd == "render":
        if not args:
            raise Stop("render <png>")
        wf, ids = cv.workflow()
        names = {v: k for k, v in ids.items()}
        Path(args[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(args[0]).write_bytes(RD.render(wf, cv.oi, names=names).png())
        return [f"picture: {args[0]}"]
    if cmd == "export":
        if not args:
            raise Stop("export <json>")
        wf, ids = cv.workflow()
        Path(args[0]).parent.mkdir(parents=True, exist_ok=True)
        jdump(args[0], wf)
        work.cfg.setdefault("exported", {})[cv.name] = {"path": os.path.abspath(args[0]), "hash": workflow_hash(wf)}
        work.save_cfg()
        un = [n["id"] for n in cv.s["nodes"] if not cv.placed(n)]
        out = [f"exported: {args[0]} ({len(wf['nodes'])} nodes, {len(wf['links'])} wires)"]
        if un:
            out.append(f"not exported because not placed: {' '.join(un)}")
        return out

    if cmd == "replay":
        if not args or (len(args) > 1 and args[1] not in RPL.LANGS):
            raise Stop(f"replay <html> [{'|'.join(RPL.LANGS)}]")
        Path(args[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(args[0]).write_text(replay_page(work, args[1] if len(args) > 1 else "en"), encoding="utf-8")
        work.cfg["replayed"] = {"path": os.path.abspath(args[0]), "canvases": canvases_hash(work),
                                "file": hashlib.sha256(Path(args[0]).read_bytes()).hexdigest()}
        work.save_cfg()
        return [f"replay page: {args[0]}"]

    # from here on, commands change the state. A command that stops changes nothing
    snap = cv.snapshot(line.strip())
    cv.before = problems(cv)
    try:
        out = change(cv, work, cmd, args)
    except Exception:
        # a stopped command changes nothing and leaves no undo record (otherwise the next undo would say "undone" and restore nothing)
        snap.unlink()
        raise
    consume_given_files(work, cmd, args)
    return out


def consume_given_files(work, cmd, args):
    """After a layout or note that succeeded: remember the plan file and the Note files it used (finish deletes them)."""
    if cmd == "note":
        work.consume(args[0])
    elif cmd == "layout":
        work.consume(args[0])
        for raw in Path(args[0]).read_text(encoding="utf-8").splitlines():
            toks = shlex.split(raw, comments=True)
            if len(toks) >= 2 and toks[0] == "note":
                work.consume(toks[1])


def change(cv, work, cmd, args):
    if cmd == "layout":
        return do_layout(cv, work, args)
    apply_op(cv, work, cmd, args)
    return finish(cv)


def _op_copy(cv, work, args):
    nodes = cv.nodes
    src = work.src()
    sn = {n["id"]: n for n in src["nodes"]}
    for sid in args:
        if sid not in sn:
            raise Stop(f"the source has no node {sid}")
        if sid in nodes:
            raise Stop(f"{sid} is already on the canvas")
        n = {k: copy.deepcopy(v) for k, v in sn[sid].items() if k not in WORK_KEYS}
        n.pop("title", None)
        for i in n.get("inputs") or []:
            i["link"] = None
            i.pop("cut_by", None)
        for o in n.get("outputs") or []:
            o["links"] = []
        n.pop("pos", None)
        n["pos"] = None
        if n["type"] in NOTE_TYPES:
            n["size"] = [NT.NOTE_W, max(NT.NOTE_MIN[1], NT.note_height((n.get("widgets_values") or [""])[0]))]
        cv.size_node(n)
        cv.default_color(n)
        cv.s["nodes"].append(n)
        cv.out.append(f"copied: {sid} {n['type']}" + (f" (mode {n.get('mode')})" if n.get("mode") else ""))


def _op_add(cv, work, args):
    nodes = cv.nodes
    if not args:
        raise Stop("add <type> [<id>]")
    t = args[0]
    info = cv.oi.get(t)
    if not info:
        raise Stop(f"type {t} is not in object_info")
    nid = args[1] if len(args) > 1 else f"n{cv.s['next_id']}"
    cv.s["next_id"] += 1
    if nid in nodes:
        raise Stop(f"{nid} already exists")
    vals = CS.build_widgets_values(info, {})
    ins, outs = CS.new_node_slots(info, vals)
    n = {"id": nid, "type": t, "mode": 0, "inputs": ins, "outputs": outs,
         "widgets_values": CS.saved_widgets_values(t, info, {}),
         "properties": {"Node name for S&R": t}, "pos": None}
    cv.size_node(n)
    cv.default_color(n)
    cv.s["nodes"].append(n)
    cv.out.append(f"added: {nid} {t}")


def _op_set(cv, work, args):
    if len(args) < 2:
        raise Stop("set <id> <widget>=<value> ...")
    if args[0] not in cv.nodes and args[0] in {n["id"] for n in work.src()["nodes"]}:
        # set works on the canvas only: a value set before the copy would not reach the node the copy makes
        raise Stop(f"no node {args[0]} on this canvas yet (it is in the source): copy {args[0]} first, then set it")
    n = cv.node(args[0])
    info = cv.oi.get(n["type"])
    vals = n.get("widgets_values")
    if isinstance(vals, dict):
        # nodes that keep values in a named dict (VHS_LoadVideo etc.): write by name
        for kv in args[1:]:
            k, sep, v = kv.partition("=")
            if not sep or k not in vals:
                raise Stop(f"write the values of {n['id']} by name ({', '.join(x for x in vals if not isinstance(vals[x], dict))})")
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                pass
            cv.out.append(f"value {n['id']}.{k}: {json.dumps(vals[k], ensure_ascii=False)[:60]} → {json.dumps(v, ensure_ascii=False)[:60]}")
            vals[k] = v
        cv.changed.add(n["id"])
        return
    if not isinstance(vals, list):
        raise Stop(f"cannot read the value list of {n['id']}")
    if not info:
        # type not in object_info (custom node not installed): write by index in the value list
        for kv in args[1:]:
            k, _, v = kv.partition("=")
            if not k.isdigit() or int(k) >= len(vals):
                raise Stop(f"the type of {n['id']} is not in object_info. Write by index in the value list (0-{len(vals) - 1}): "
                           + ", ".join(f"{i}={json.dumps(x, ensure_ascii=False)[:30]}" for i, x in enumerate(vals)))
            try:
                v = json.loads(v)
            except json.JSONDecodeError:
                pass
            cv.out.append(f"value {n['id']}[{k}]: {json.dumps(vals[int(k)], ensure_ascii=False)[:60]} → {json.dumps(v, ensure_ascii=False)[:60]}")
            vals[int(k)] = v
        cv.changed.add(n["id"])
        return
    for kv in args[1:]:
        if "=" not in kv:
            raise Stop(f"{kv}: write <widget>=<value>")
        k, v = kv.split("=", 1)
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            pass
        names = CS.widget_names(info, vals)
        dyn = CS.widget_spec(info, k, dict(zip(names, vals)))
        if k in names and dyn is not None and CS._spec_type_and_opts(dyn)[0] == "COMFY_DYNAMICCOMBO_V3":
            # changing a DynamicCombo selection: the child widgets change, so rebuild them with the chosen option's defaults
            # (keeping the previous selection's child values would shift the values of later widgets)
            named = {nm: x for nm, x in zip(names, vals) if not nm.startswith(f"{k}.")}
            old = named.get(k)
            named[k] = v
            vals[:] = CS.build_widgets_values(info, named)
            cv.out.append(f"value {n['id']}.{k}: {json.dumps(old, ensure_ascii=False)[:60]} → {json.dumps(v, ensure_ascii=False)[:60]}"
                          f" (child values reset to defaults: {', '.join(f'{nm}={json.dumps(x, ensure_ascii=False)}' for nm, x in zip(CS.widget_names(info, vals), vals) if nm.startswith(f'{k}.'))})")
            continue
        if k == "control_after_generate" and k not in names:
            # the frontend names the control widget after the spec's control_after_generate value ("fixed" etc.)
            ctl = [CS._control_name(CS._spec_type_and_opts(spec)[1]) for _, spec, _ in CS.ordered_input_specs(info)
                   if CS._spec_type_and_opts(spec)[1].get("control_after_generate")]
            k = next((c for c in ctl if c in names), k)
        if k not in names:
            raise Stop(f"{n['id']} has no widget {k} ({', '.join(names)})")
        idx = names.index(k)
        while len(vals) <= idx:
            vals.append(None)
        old = vals[idx]
        vals[idx] = v
        cv.out.append(f"value {n['id']}.{k}: {json.dumps(old, ensure_ascii=False)[:60]} → {json.dumps(v, ensure_ascii=False)[:60]}")
    ins, outs = CS.new_node_slots(info, vals, [i["name"] for i in n.get("inputs") or []])
    keep = {i["name"]: i.get("link") for i in n.get("inputs") or []}
    if [i["name"] for i in ins] != [i["name"] for i in n.get("inputs") or []]:
        for i in ins:
            i["link"] = keep.get(i["name"])
        n["inputs"] = ins
        cv.relink()
    cv.size_node(n)
    cv.changed.add(n["id"])


def _op_link(cv, work, args):
    if len(args) % 2:
        raise Stop("link <A>.<output> <B>.<input> ... (in pairs)")
    for a, b in zip(args[::2], args[1::2]):
        oid, slot = cv.port_out(a)
        tid, tin = cv.port_in(b)
        l = cv.add_link(oid, slot, tid, tin)
        cv.out.append(f"linked: {lname(cv, l)}")
        cv.size_node(cv.node(tid))


def _op_unlink(cv, work, args):
    for b in args:
        tid, tin = cv.port_in(b)
        before = len(cv.s["links"])
        cv.s["links"] = [l for l in cv.s["links"] if not (l["target_id"] == tid and l["target_input"] == tin)]
        cv.relink()
        cv.out.append(f"unlinked: {b}" if len(cv.s["links"]) < before else f"{b} has no wire")
        cv.size_node(cv.node(tid))


def _op_rm(cv, work, args):
    nodes = cv.nodes
    for nid in args:
        cv.node(nid)
        cv.s["nodes"] = [n for n in cv.s["nodes"] if n["id"] != nid]
        cv.s["links"] = [l for l in cv.s["links"] if nid not in (l["origin_id"], l["target_id"])]
        for k in list(cv.s["blocks"]):
            cv.s["blocks"][k] = [i for i in cv.s["blocks"][k] if i != nid]
        for g in cv.s["groups"]:
            g["members"] = [i for i in g["members"] if i != nid]
        cv.out.append(f"removed: {nid}")
    cv.relink()


def _op_mode(cv, work, args):
    m = {"on": 0, "bypass": 4, "mute": 2}.get(args[0] if args else "")
    if m is None:
        raise Stop("mode <on|bypass|mute> <id> ...")
    for nid in args[1:]:
        cv.node(nid)["mode"] = m
        cv.out.append(f"mode {nid}: {args[0]}")


def _op_title(cv, work, args):
    n = cv.node(args[0])
    if cv.in_layout:
        n.setdefault("layout_prev", {}).setdefault("title", n.get("title"))
    n["title"] = " ".join(args[1:])
    cv.size_node(n)
    cv.out.append(f"title {n['id']}: {n['title']}")
    # a value node's title starts with the name shown on screen (Int), not the type name (PrimitiveInt)
    t = n.get("type") or ""
    shown = (work.oi.get(t) or {}).get("display_name") or t
    head = n["title"].split(":", 1)[0].strip()
    if ":" in n["title"] and head == t and shown != t:
        cv.out.append(f"  the title starts with the type name {t}; the name shown on screen is {shown} (write \"{shown}: …\")")


def _op_put(cv, work, args):
    if len(args) < 2:
        raise Stop("put <unit> origin | put <unit> <right|left|below|above> <ref> ...")
    ids = cv.unit(args[0])
    if args[1] == "origin":
        cv.place_unit(ids, 0, 0)
    else:
        if len(args) < 3:
            raise Stop("no reference (put <unit> <right|left|below|above> <ref> ...)")
        rest, opt = parse_opts(args[3:], flags=ALIGNS, keyed=("gap",))
        if rest:
            raise Stop(f"unreadable arguments: {' '.join(rest)}")
        al = next((a for a in ALIGNS if a in opt), None)
        ref = cv.unit(args[2])
        if al is None and args[1] in ("right", "left") and cv.link_between(ref, ids):
            al = "wire"   # side by side and wired: the wire is made horizontal, not the tops aligned
        put_rel(cv, ids, args[1], ref, al, num(opt["gap"], "gap") if "gap" in opt else None)


def _op_row(cv, work, args):
    pos, opt = parse_opts(args, flags={"top", "wire"}, keyed=("right", "gap"))
    units = [cv.unit(t) for t in pos]
    if not units:
        raise Stop("row <unit> ...")
    al = "top" if "top" in opt else "wire"
    gap = num(opt["gap"], "gap") if "gap" in opt else None
    start = 0
    if "right" in opt:
        ref = cv.unit(opt["right"])
        a = al if al == "top" or cv.link_between(ref, units[0]) else "top"
        if a != al:
            cv.out.append(f"no wire between {opt['right']} and {pos[0]}: aligned their tops")
        put_rel(cv, units[0], "right", ref, a, gap)
    elif not all(cv.placed(cv.node(i)) for i in units[0]):
        cv.place_unit(units[0], 0, 0)
        cv.out.append(f"{pos[0]} was not placed: put it at the origin (0, 0)")
    for k, (prev, u) in enumerate(zip(units, units[1:])):
        a = al if (al == "top" or cv.link_between(prev, u)) else "top"
        if a != al:
            cv.out.append(f"no wire between {pos[k]} and {pos[k + 1]}: aligned their tops")
        put_rel(cv, u, "right", prev, a, gap)


def _op_stack(cv, work, args):
    pos, opt = parse_opts(args, flags={"left", "right"}, keyed=("below", "gap"))
    units = [cv.unit(t) for t in pos]
    if not units:
        raise Stop("stack <unit> ...")
    al = "right" if "right" in opt else "left"
    gap = num(opt["gap"], "gap") if "gap" in opt else None
    if "below" in opt:
        put_rel(cv, units[0], "below", cv.unit(opt["below"]), al, gap)
    elif not all(cv.placed(cv.node(i)) for i in units[0]):
        cv.place_unit(units[0], 0, 0)
    for prev, u in zip(units, units[1:]):
        put_rel(cv, u, "below", prev, al, gap)


def _op_align(cv, work, args):
    if len(args) < 3:
        raise Stop("align <top|bottom|left|right|middle|center> <unit> ...")
    how, units = args[0], [cv.unit(t) for t in args[1:]]
    rb = cv.bbox(units[0])
    for u in units[1:]:
        b = cv.bbox(u)
        dx = dy = 0
        if how == "top":
            dy = rb[1] - b[1]
        elif how == "bottom":
            dy = rb[3] - b[3]
        elif how == "middle":
            dy = (rb[1] + rb[3]) / 2 - (b[1] + b[3]) / 2
        elif how == "left":
            dx = rb[0] - b[0]
        elif how == "right":
            dx = rb[2] - b[2]
        elif how == "center":
            dx = (rb[0] + rb[2]) / 2 - (b[0] + b[2]) / 2
        else:
            raise Stop(f"unknown alignment {how} (top bottom middle left right center)")
        cv.translate(u, dx, dy)


def _op_inputs(cv, work, args):
    if not args:
        raise Stop("inputs <id> [gap N]")
    tid = args[0]
    opt = parse_opts(args[1:], keyed=("gap",))[1]
    t = cv.node(tid)
    if not cv.placed(t):
        raise Stop(cv.unplaced_msg(tid))
    order = [i["name"] for i in t.get("inputs") or []]
    srcs = []
    for name in order:
        l = next((l for l in cv.s["links"] if l["target_id"] == tid and l["target_input"] == name), None)
        if l and l["origin_id"] not in srcs and cv.node(l["origin_id"]).get("type") not in {"Reroute"} | NOTE_TYPES:
            srcs.append(l["origin_id"])
    if not srcs:
        raise Stop(f"{tid} has no sources wired directly into it")
    gap = num(opt["gap"], "gap") if "gap" in opt else H_GAP
    rt = G.rect(t)
    right = rt[0] - gap
    y = 0
    for sid in srcs:
        n = cv.node(sid)
        h = n["size"][1] + G.title_height(n)
        cv.set_rect_xy(sid, right - n["size"][0], y)
        y += h + V_GAP
    # column height: for a node that takes conditioning (KSampler etc.), the positive wire is horizontal.
    # For a node that does not (SamplerCustomAdvanced etc.), the receiving node is centred on the column vertically (readable-form)
    pos_l = next((l for l in cv.s["links"] if l["target_id"] == tid and l.get("type") == "CONDITIONING"
                  and l["target_input"] in ("positive", "conditioning") and l["origin_id"] in srcs), None)
    if pos_l:
        dy = cv.in_xy(tid, pos_l["target_input"])[1] - cv.out_xy(pos_l["origin_id"], pos_l["origin_slot"])[1]
        how = "positive wire horizontal"
    else:
        col = cv.bbox(srcs)
        dy = (rt[1] + rt[3]) / 2 - (col[1] + col[3]) / 2
        how = "node centred on the column"
    cv.translate(srcs, 0, dy)
    cv.out.append(f"sources of {tid} in one right-aligned column on its left ({how}): {' '.join(srcs)}")


def _op_shape(cv, work, args):
    pos, opt = parse_opts(args, keyed=("right", "below", "left", "above", "gap"))
    if len(pos) != 2:
        raise Stop("shape <laid-out block> <block to lay out> [right|below|left|above <ref>] [gap N]")
    a_ids, b_ids = cv.unit(pos[0]), cv.unit(pos[1])
    ab = cv.bbox(a_ids)
    a_by_type, b_by_type = {}, {}
    for i in sorted(a_ids, key=lambda i: (G.rect(cv.node(i))[1], G.rect(cv.node(i))[0])):
        a_by_type.setdefault(cv.node(i)["type"], []).append(i)
    for i in b_ids:
        b_by_type.setdefault(cv.node(i)["type"], []).append(i)
    pairs, left_over = [], []
    for typ, bs in b_by_type.items():
        as_ = a_by_type.get(typ, [])
        for k, bi in enumerate(bs):
            (pairs if k < len(as_) else left_over).append((as_[k], bi) if k < len(as_) else bi)
    where = next((k for k in ("right", "below", "left", "above") if k in opt), None)
    if where:
        rb = cv.bbox(cv.unit(opt[where]))
        w, h = ab[2] - ab[0], ab[3] - ab[1]
        gh = num(opt["gap"], "gap") if "gap" in opt else H_GAP
        gv = num(opt["gap"], "gap") if "gap" in opt else V_GAP
        x0 = {"right": rb[2] + gh, "left": rb[0] - gh - w}.get(where, rb[0])
        y0 = {"below": rb[3] + gv, "above": rb[1] - gv - h}.get(where, rb[1])
    else:
        placed_b = [i for _, i in pairs if cv.placed(cv.node(i))]
        if not placed_b:
            raise Stop("no node of the block to lay out is placed. Give a reference with right, below etc.")
        bb = cv.bbox(placed_b)
        x0, y0 = bb[0], bb[1]
    for ai, bi in pairs:
        ra = G.rect(cv.node(ai))
        cv.set_rect_xy(bi, x0 + ra[0] - ab[0], y0 + ra[1] - ab[1])
    cv.out.append(f"{pos[1]} in the same shape as {pos[0]}: " + ", ".join(f"{bi}←{ai}" for ai, bi in pairs))
    if left_over:
        cv.out.append(f"not moved, no node of the same type in {pos[0]}: {' '.join(left_over)}")


def _op_level(cv, work, args):
    pos, opt = parse_opts(args, keyed=("move",))
    if len(pos) != 2:
        raise Stop("level <A>.<output> <B>.<input> [move <unit>]")
    oid, slot = cv.port_out(pos[0])
    tid, tin = cv.port_in(pos[1])
    l = next((l for l in cv.s["links"] if l["origin_id"] == oid and l["origin_slot"] == slot
              and l["target_id"] == tid and l["target_input"] == tin), None)
    if not l:
        raise Stop(f"no wire {pos[0]} → {pos[1]}")
    ids = cv.unit(opt["move"]) if "move" in opt else [tid]
    un = [i for i in (oid, tid) if not cv.placed(cv.node(i))]
    if un:
        raise Stop(f"nodes not placed yet: {' '.join(un)} (place both ends before level)")
    cv.translate(ids, 0, cv.level_dy(l, set(ids)))


def _op_width(cv, work, args):
    ns = [cv.node(i) for i in args]
    # a model loader is never narrower than LOADER_MIN_W. Counted here, because the loader width alignment
    # does not widen a node whose width is set with width (the group would no longer be equal)
    w = max([n["size"][0] for n in ns] + [LOADER_MIN_W for n in ns if cv.is_model_loader(n)])
    # if the placed nodes share a right edge (an inputs column etc.), keep the right edge and widen to the left.
    # Keeping the left edge would break the column's right alignment
    placed = [n for n in ns if cv.placed(n)]
    keep_right = len(placed) == len(ns) and len({round(G.rect(n)[2]) for n in ns}) == 1 \
        and len({round(G.rect(n)[0]) for n in ns}) > 1
    for n in ns:
        n.pop("loader_base", None)   # so the loader width alignment does not undo a width set by hand
        n["width_set"] = True
        if n["size"][0] != w:
            n["size_min"] = [w, 0]
            cv.out.append(f"width {n['id']}: {n['size'][0]} → {w}" + (" (kept the right edge)" if keep_right else ""))
            if keep_right:
                n["pos"][0] -= w - n["size"][0]
            n["size"][0] = w
            cv.changed.add(n["id"])


def _op_move(cv, work, args):
    if len(args) < 3:
        raise Stop("move <unit> ... <dx> <dy>")
    dx, dy = num(args[-2], "dx"), num(args[-1], "dy")
    for t in args[:-2]:
        cv.translate(cv.unit(t), dx, dy)


def _op_gap(cv, work, args):
    if len(args) < 3:
        raise Stop("gap <A> <B> <N> [h|v]")
    a, b, n = cv.unit(args[0]), cv.unit(args[1]), num(args[2], "N")
    hv = args[3] if len(args) > 3 else "h"
    ra, rb = cv.bbox(a), cv.bbox(b)
    if hv == "h":
        dx = (ra[2] + n - rb[0]) if rb[0] >= ra[0] else (ra[0] - n - rb[2])
        cv.translate(b, dx, 0)
    else:
        dy = (ra[3] + n - rb[1]) if rb[1] >= ra[1] else (ra[1] - n - rb[3])
        cv.translate(b, 0, dy)


def _op_block(cv, work, args):
    nodes = cv.nodes
    if len(args) < 2:
        raise Stop("block <name> <id> ...")
    if args[0] in nodes:
        raise Stop(f"{args[0]} is the id of a node. Use another name")
    ids = []
    for t in args[1:]:
        ids += cv.unit(t)
    cv.s["blocks"][args[0]] = ids
    cv.out.append(f"block {args[0]}: {' '.join(ids)}")


def _op_unblock(cv, work, args):
    cv.s["blocks"].pop(args[0], None)
    cv.out.append(f"removed block {args[0]}")


def _op_group(cv, work, args):
    pos, opt = parse_opts(args, keyed=("color",))
    if len(pos) < 2:
        raise Stop("group <title> <unit> ... [color <color>]")
    ids = []
    for t in pos[1:]:
        ids += cv.unit(t)
    col = opt.get("color")
    if col and col not in COLORS:
        raise Stop(f"color {col} is not a core color ({' '.join(COLORS)})")
    cv.s["groups"] = [g for g in cv.s["groups"] if g["title"] != pos[0]]
    cv.s["groups"].append({"title": pos[0], "members": ids, "color": COLORS[col][1] if col else None})
    cv.update_groups()
    g = cv.s["groups"][-1]
    cv.out.append(f"group \"{pos[0]}\": {' '.join(ids)}  frame {g.get('bounding')}")


def _op_ungroup(cv, work, args):
    cv.s["groups"] = [g for g in cv.s["groups"] if g["title"] != args[0]]
    cv.s["group_align"] = [[t for t in s if t != args[0]] for s in cv.s.get("group_align") or []]
    cv.out.append(f"removed group \"{args[0]}\"")


def _op_group_align(cv, work, args):
    have = {g["title"] for g in cv.s["groups"]}
    for t in args:
        if t not in have:
            raise Stop(f"no group \"{t}\"")
    cv.s.setdefault("group_align", []).append(list(args))
    cv.update_groups()
    cv.out.append("aligned top and bottom edges: " + ", ".join(f"\"{g['title']}\" {g['bounding']}" for g in cv.s["groups"] if g["title"] in args))


def _op_color(cv, work, args):
    c = args[0] if args else ""
    if c != "none" and c not in COLORS:
        raise Stop(f"color {c} is not a core color ({' '.join(COLORS)} none)")
    for nid in args[1:]:
        n = cv.node(nid)
        if cv.in_layout:
            n.setdefault("layout_prev", {}).setdefault("color", [n.get("color"), n.get("bgcolor")])
        if c == "none":
            n.pop("color", None)
            n.pop("bgcolor", None)
        else:
            n["color"], n["bgcolor"] = COLORS[c]
        cv.out.append(f"color {nid}: {c}")


def _op_rail(cv, work, args):
    do_rail(cv, args)


def _op_note(cv, work, args):
    nodes = cv.nodes
    pos, opt = args[:3], parse_opts(args[3:], keyed=("gap", "width"))[1]
    if len(pos) < 3:
        raise Stop("note <md file> <right|left|below|above> <ref> [gap N] [width W]")
    if not Path(pos[0]).is_file():
        raise Stop(f"no Note file {pos[0]}")
    text = Path(pos[0]).read_text(encoding="utf-8")
    w = int(num(opt["width"], "width")) if "width" in opt else NT.NOTE_W
    h = max(NT.NOTE_MIN[1], NT.note_height(text, w))
    nid = Path(pos[0]).stem if Path(pos[0]).stem not in cv.nodes else f"{Path(pos[0]).stem}_{cv.s['next_id']}"
    cv.s["next_id"] += 1
    n = {"id": nid, "type": "MarkdownNote", "mode": 0, "inputs": [], "outputs": [], "properties": {},
         "widgets_values": [text], "pos": None, "size": [w, round(h)], "canvas_note": True}
    # the model Note is purple and every other Note yellow (notes.md). There is only one right answer, so the canvas sets it
    model_note = re.search(r"^#+\s*models\s*$", text, re.M)
    n["color"], n["bgcolor"] = COLORS["purple" if model_note else "yellow"]
    cv.s["nodes"].append(n)
    put_rel(cv, [nid], pos[1], cv.unit(pos[2]), None, num(opt["gap"], "gap") if "gap" in opt else None)
    cv.out.append(f"Note {nid}: width {w}, height {round(h)}")


OPS = {  # commands that change the state: command name -> function
    "copy": _op_copy,
    "add": _op_add,
    "set": _op_set,
    "link": _op_link,
    "unlink": _op_unlink,
    "rm": _op_rm,
    "mode": _op_mode,
    "title": _op_title,
    "put": _op_put,
    "row": _op_row,
    "stack": _op_stack,
    "align": _op_align,
    "inputs": _op_inputs,
    "shape": _op_shape,
    "level": _op_level,
    "width": _op_width,
    "move": _op_move,
    "gap": _op_gap,
    "block": _op_block,
    "unblock": _op_unblock,
    "group": _op_group,
    "ungroup": _op_ungroup,
    "group-align": _op_group_align,
    "color": _op_color,
    "rail": _op_rail,
    "note": _op_note,
}


def apply_op(cv, work, cmd, args):
    """Applies one command (no saving, no report). The command is looked up in OPS."""
    fn = OPS.get(cmd)
    if fn is None:
        raise Stop(f"unknown command {cmd} (the list is at the top of canvas.py)")
    fn(cv, work, args)



LAYOUT_ID_BASE = 100000
LAYOUT_OPS = {"block", "put", "row", "stack", "align", "level", "inputs", "shape", "width", "move", "gap",
              "group", "group-align", "color", "rail", "note", "title"}


def do_layout(cv, work, args):
    """Applies the plan file from the top and re-places everything. The inside of each block comes first, blocks relative to each other last.
    If any line stops, nothing changes."""
    if not args:
        raise Stop("layout <plan file>")
    lines = need_file(args[0], "plan file").read_text(encoding="utf-8").splitlines()
    # re-place: clear positions, blocks and groups. Rail Reroutes and Notes placed on the canvas are removed too (the plan writes everything).
    # When a Reroute is removed, the source output is wired straight to its targets again
    nodes = cv.nodes
    rr = {i for i, n in nodes.items() if n.get("type") == "Reroute"}
    # Notes placed with the canvas's note command (their id is the file name, so they are not told apart by name)
    notes = {i for i, n in nodes.items() if n.get("type") in NOTE_TYPES and n.get("canvas_note")}
    direct = []
    for l in cv.s["links"]:
        if l["origin_id"] in rr or l["target_id"] not in rr:
            continue
        # a wire from a source into a Reroute: follow the Reroutes after it and collect every target that is not a Reroute
        stack, seen = [l["target_id"]], set()
        while stack:
            r = stack.pop()
            if r in seen:
                continue
            seen.add(r)
            for m in cv.s["links"]:
                if m["origin_id"] == r:
                    (stack.append(m["target_id"]) if m["target_id"] in rr
                     else direct.append((l["origin_id"], l["origin_slot"], m["target_id"], m["target_input"])))
    drop = rr | notes
    cv.s["nodes"] = [n for n in cv.s["nodes"] if n["id"] not in drop]
    cv.s["links"] = [l for l in cv.s["links"] if l["origin_id"] not in drop and l["target_id"] not in drop]
    for o, sl, t, ti in direct:
        cv.add_link(o, sl, t, ti)
    for n in cv.s["nodes"]:
        n["pos"] = None
        prev = n.pop("layout_prev", None)
        if prev:
            # titles and colours the previous plan set go back to what they were before it (build-time ones stay)
            if "title" in prev:
                if prev["title"] is None:
                    n.pop("title", None)
                else:
                    n["title"] = prev["title"]
                cv.size_node(n)
            if "color" in prev:
                for k, v in zip(("color", "bgcolor"), prev["color"]):
                    if v is None:
                        n.pop(k, None)
                    else:
                        n[k] = v
        widened = n.pop("size_min", None) is not None
        if n.pop("width_set", None) or widened:
            # also clear widths widened by the plan's width and start again from the initial size (a leftover width would not go back when the plan is edited)
            cv.size_node(n)
    cv.s["blocks"], cv.s["groups"], cv.s["group_align"] = {}, [], []
    cv.relink()
    cv.in_layout = True
    # ids of Reroutes and Notes made by the plan start from the same number every time (the same plan gives the same result).
    # They start where they cannot collide with the numbers of ordinary commands (n... from add)
    keep_next = cv.s["next_id"]
    cv.s["next_id"] = LAYOUT_ID_BASE
    count = 0
    notes = []
    for k, raw in enumerate(lines, 1):
        toks = shlex.split(raw, comments=True)
        if not toks:
            continue
        if toks[0] not in LAYOUT_OPS:
            raise Stop(f"line {k} \"{raw.strip()}\": layout accepts only {' '.join(sorted(LAYOUT_OPS))}")
        mark = len(cv.out)
        try:
            apply_op(cv, work, toks[0], toks[1:])
        except Stop as e:
            raise Stop(f"stopped at line {k} \"{raw.strip()}\" (nothing changed): {e}")
        except Exception as e:   # a bug in the canvas. Stop and say which line of the plan (nothing changes)
            raise Stop(f"stopped by a canvas error at line {k} \"{raw.strip()}\" (nothing changed): {type(e).__name__}: {e}")
        notes += [f"  line {k}: {m}" for m in cv.out[mark:]]
        count += 1
    cv.s["next_id"] = keep_next
    # kept for the replay page (keyed by this command's undo snapshot; undo drops it with the state)
    snaps = len(list(cv.hist.glob("*.json"))) if cv.hist.exists() else 0
    cv.s.setdefault("layout_notes", {})[str(snaps - 1)] = {"lines": count, "notes": [m[2:] for m in notes]}
    cv.out = [f"applied {count} lines of the plan and re-placed everything"]
    if notes:
        cv.out.append("what the lines did besides placing (as a single command would report):")
        cv.out += notes
    un = [n["id"] for n in cv.s["nodes"] if not cv.placed(n)]
    if un:
        cv.out.append(f"unplaced: {' '.join(un)}")
    before_w = {n["id"]: n["size"][0] for n in cv.s["nodes"] if n.get("size")}
    cv.same_loader_width()
    for n in cv.s["nodes"]:
        if n.get("size") and before_w.get(n["id"]) != n["size"][0]:
            cv.out.append(f"width {n['id']}: {before_w.get(n['id'])} -> {n['size'][0]} (loader widths aligned)")
    cv.save()
    lines, counts = full_check(cv)
    cv.out.append("counts: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    cv.out += grouped(cv, lines)
    return cv.out


def grouped(cv, lines):
    """Groups the check lines by block."""
    of = {}
    for b, ids in cv.s["blocks"].items():
        for i in ids:
            of.setdefault(i, b)
    ids = {n["id"] for n in cv.s["nodes"]}
    buckets = {}
    for ln in lines:
        found = [t for t in re.findall(r"[\w:~]+", ln) if t in ids]
        bs = sorted({of.get(t, "(no block)") for t in found})
        name = f"inside {bs[0]}" if len(bs) == 1 else ("between " + " and ".join(bs) if bs else "overall")
        buckets.setdefault(name, []).append(ln)
    out = []
    for name in sorted(buckets):
        out.append(f"■ {name} ({len(buckets[name])})")
        out += ["  " + x for x in buckets[name]]
    return out or ["no problems"]


def finish(cv):
    for nid, old in cv.moved.items():
        n = cv.nodes.get(nid)
        if n and n.get("pos") is not None:
            r = G.rect(n)
            cv.out.append(f"moved: {nid} " + (f"{[round(old[0]), round(old[1] - G.title_height(n))]} → " if old else "placed ") + f"[{round(r[0])}, {round(r[1])}]")
    before = {n["id"]: n["size"][0] for n in cv.s["nodes"] if n.get("size")}
    cv.same_loader_width()
    for n in cv.s["nodes"]:
        if n.get("size") and before.get(n["id"]) != n["size"][0]:
            cv.out.append(f"width {n['id']}: {before.get(n['id'])} → {n['size'][0]} (loader widths aligned)")
    local_report(cv, cv.before)
    cv.save()
    return cv.out or ["nothing changed"]


def do_rail(cv, args):
    if "to" not in args:
        raise Stop("rail <A>.<output> <above <unit>|below <unit>|level <X>.<output>|out> to <B>.<input> ...")
    k = args.index("to")
    head, targets = args[:k], args[k + 1:]
    if len(head) < 2 or not targets:
        raise Stop("rail is incomplete: rail <A>.<output> <above <unit>|below <unit>|level <X>.<output>|out> to <B>.<input> ...")
    oid, slot = cv.port_out(head[0])
    if not cv.placed(cv.node(oid)):
        raise Stop(f"the rail source {oid} is not placed yet")
    a = cv.out_xy(oid, slot)
    spec = head[1]
    if spec in ("above", "below", "level") and len(head) < 3:
        raise Stop(f"write rail ... {spec} <{'output' if spec == 'level' else 'unit'}> to ...")
    if len(head) > (2 if spec == "out" else 3):
        extra = " ".join(head[2 if spec == "out" else 3:])
        raise Stop(f"rail does not take \"{extra}\" (write rail <A>.<output> <above <unit>|below <unit>|level <X>.<output>|out> to <B>.<input> ...)")
    if spec == "out":
        y = a[1]
    elif spec == "above":
        y = cv.bbox(cv.unit(head[2]))[1] - V_GAP
    elif spec == "below":
        y = cv.bbox(cv.unit(head[2]))[3] + V_GAP
    elif spec == "level":
        x_id, x_slot = cv.port_out(head[2])
        y = cv.out_xy(x_id, x_slot)[1]
    else:
        raise Stop(f"unknown rail height {spec} (above below level out)")
    tg = []
    for t in targets:
        tid, tin = cv.port_in(t)
        tg.append((cv.bbox([tid])[0], tid, tin))
    tg.sort()
    o = cv.node(oid)
    ox1 = G.rect(o)[2]
    made = []
    if spec in ("above", "below"):
        # if it overlaps horizontally with a rail from another source and the vertical gap is under RAIL_GAP, shift up for above, down for below
        x1 = max(x for x, _, _ in tg)
        step = -1 if spec == "above" else 1
        for _ in range(50):
            near = [sy for sy, sx0, sx1, root in rail_spans(cv) if root != (oid, slot)
                    and min(sx1, x1) > max(sx0, ox1) and abs(sy - y) < P["RAIL_GAP"]]
            if not near:
                break
            y = (min(near) - P["RAIL_GAP"]) if step < 0 else (max(near) + P["RAIL_GAP"])
            cv.out.append(f"too close to another rail; height shifted to {round(y)}")

    if spec in ("above", "below") and abs(y - a[1]) >= 1:
        # if a horizontal line at the output height up to just before the rightmost target hits nothing and is not close
        # to another rail, no raising or lowering Reroute is needed, so the rail is drawn at the output height
        x1 = max(x for x, _, _ in tg)
        band = (ox1 + 1, a[1] - REROUTE_H / 2, x1 - H_GAP / 2, a[1] + REROUTE_H / 2)
        # a target standing between the source and a later target is in the way too (the rail would run on behind it);
        # only the rightmost targets, which the band stops short of, are left out
        last = {t for x, t, _ in tg if x == x1}
        blocked = any(rect_overlap(G.rect(m), band) for m in cv.s["nodes"]
                      if cv.placed(m) and m["id"] != oid and m["id"] not in last and m.get("type") != "Reroute")
        near = [sy for sy, sx0, sx1, root in rail_spans(cv) if root != (oid, slot)
                and min(sx1, x1) > max(sx0, ox1) and abs(sy - a[1]) < P["RAIL_GAP"]]
        if not blocked and not near:
            cv.out.append(f"drawn at the output height {round(a[1])} instead of {spec}, since nothing is in the way")
            y = a[1]

    def reroute(x):
        rid = f"r{cv.s['next_id']}"
        cv.s["next_id"] += 1
        typ = (o.get("outputs") or [])[slot].get("type") or "*"
        n = {"id": rid, "type": "Reroute", "mode": 0, "pos": [round(x), round(y - 0.7 * G.SLOT)],
             "size": [REROUTE_W, REROUTE_H], "inputs": [{"name": "", "type": "*", "link": None}],
             "outputs": [{"name": "", "type": typ, "links": []}],
             "properties": {"showOutputText": False, "horizontal": False}, "widgets_values": []}
        cv.s["nodes"].append(n)
        cv.changed.add(rid)
        made.append(rid)
        return rid

    prev = (oid, slot)
    last_x = ox1
    if abs(y - a[1]) >= 1:
        r0 = reroute(ox1 + H_GAP / 2)
        cv.add_link(oid, slot, r0, "")
        prev = (r0, 0)
        last_x = ox1 + H_GAP / 2 + REROUTE_W
    cur_r, cur_x = None, None

    def direct_ok(tid, tin, src=None):
        """Whether a direct wire from src (default: the source output) passes behind no node."""
        start = a if src is None else cv.out_xy(src, 0)
        pts = G.spline(start, cv.in_xy(tid, tin))
        return not any(G.wire_hits(pts, G.rect(m)) for m in cv.s["nodes"] if cv.placed(m)
                       and m["id"] not in (oid, tid) and m.get("type") != "Reroute")

    for x0, tid, tin in tg:
        if direct_ok(tid, tin):
            cv.add_link(oid, slot, tid, tin)
            continue
        if prev[0] != oid and direct_ok(tid, tin, prev[0]):
            # if the previous Reroute on the rail reaches it without passing behind anything, no Reroute right before it is needed
            cv.add_link(prev[0], prev[1], tid, tin)
            continue
        rx = x0 - H_GAP / 2 - REROUTE_W
        if cur_r is not None and rx - cur_x < REROUTE_W + H_GAP / 2:
            cv.add_link(cur_r, 0, tid, tin)
            continue
        if rx <= last_x:
            cv.add_link(prev[0], prev[1], tid, tin)
            continue
        r = reroute(rx)
        cv.add_link(prev[0], prev[1], r, "")
        cv.add_link(r, 0, tid, tin)
        prev, cur_r, cur_x, last_x = (r, 0), r, rx, rx + REROUTE_W
    # remove, from the end, Reroutes left connected to nothing (e.g. because every target was wired directly)
    for rid in reversed(list(made)):
        if not any(l["origin_id"] == rid for l in cv.s["links"]):
            cv.s["links"] = [l for l in cv.s["links"] if l["target_id"] != rid]
            cv.s["nodes"] = [n for n in cv.s["nodes"] if n["id"] != rid]
            made.remove(rid)
    cv.relink()
    cv.out.append(f"rail {head[0]}: height {round(y)}, Reroutes {' '.join(made) or 'none (all wired directly)'}, targets {' '.join(f'{t}.{i}' for _, t, i in tg)}")


def rail_spans(cv):
    """Horizontal bands of existing rails: [(height, left, right, (source node, output index))].
    A horizontal wire from Reroute to Reroute, and a wire from a rail Reroute straight to a target node (where no
    Reroute was placed right before it), count as a band at that Reroute's height. Rails from different outputs of the same node are separate rails."""
    nodes = cv.nodes
    out = []
    for l in cv.s["links"]:
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if not o or not t or o.get("type") != "Reroute" or not cv.placed(o) or not cv.placed(t):
            continue
        a = cv.out_xy(o["id"], 0)
        b = cv.in_xy(t["id"], l["target_input"]) if t.get("type") != "Reroute" else cv.in_xy(t["id"], "")
        if t.get("type") == "Reroute" and abs(a[1] - b[1]) >= 1:
            continue
        root, rslot, seen = o["id"], 0, set()
        while nodes.get(root, {}).get("type") == "Reroute" and root not in seen:
            seen.add(root)
            up = next((x for x in cv.s["links"] if x["target_id"] == root), None)
            if not up:
                break
            root, rslot = up["origin_id"], up["origin_slot"]
        out.append((a[1], min(a[0], b[0]), max(a[0], b[0]), (root, rslot)))
    return out


def between(cv, blocks):
    """Number and direction of wires between blocks (facts known before placing)."""
    of = {}
    for b, ids in blocks.items():
        for i in ids:
            of.setdefault(i, b)
    pair = {}
    for l in cv.s["links"]:
        a, b = of.get(l["origin_id"], "(outside blocks)"), of.get(l["target_id"], "(outside blocks)")
        if a == b:
            continue
        e = pair.setdefault((a, b), {"n": 0, "src": set(), "types": set()})
        e["n"] += 1
        e["src"].add((l["origin_id"], l["origin_slot"]))
        e["types"].add(l.get("type") or "*")
    out = []
    for (a, b), e in sorted(pair.items(), key=lambda kv: -kv[1]["n"]):
        out.append(f"{a} → {b}: {e['n']} wires (from {len(e['src'])} outputs; {', '.join(sorted(e['types']))})")
    # how many blocks each output feeds (helps decide on rails)
    fan = {}
    for l in cv.s["links"]:
        a, b = of.get(l["origin_id"]), of.get(l["target_id"])
        if a and b and a != b:
            fan.setdefault((l["origin_id"], l["origin_slot"]), set()).add(b)
    many = [(k, v) for k, v in fan.items() if len(v) >= 2]
    if many:
        out.append("outputs feeding several blocks: " + ", ".join(f"{k[0]}.{k[1]} → {len(v)} ({' '.join(sorted(v))})" for k, v in sorted(many, key=lambda kv: -len(kv[1]))))
    lone = [n["id"] for n in cv.s["nodes"] if n["id"] not in of and n.get("type") not in {"Reroute"} | NOTE_TYPES]
    if lone:
        out.append(f"nodes in no block: {' '.join(lone)}")
    return out or ["no wires between blocks"]


def show(cv):
    out = []
    blk = {}
    for b, ids in cv.s["blocks"].items():
        for i in ids:
            blk.setdefault(i, []).append(b)
    for n in cv.s["nodes"]:
        r = G.rect(n) if cv.placed(n) else None
        col = next((k for k, v in COLORS.items() if v[0] == n.get("color")), "")
        s = f"{n['id']} {n['type']}" + (f" \"{n['title']}\"" if n.get("title") else "")
        s += f"  [{round(r[0])}, {round(r[1])}] width {round(r[2] - r[0])} height {round(r[3] - r[1])}" if r else "  (not placed)"
        if blk.get(n["id"]):
            s += f"  block {','.join(blk[n['id']])}"
        if col:
            s += f"  {col}"
        if n.get("mode"):
            s += f"  mode {n['mode']}"
        out.append(s)
    for g in cv.s["groups"]:
        out.append(f"group \"{g['title']}\" {g.get('bounding')}: {' '.join(g['members'])}")
    return out


def node_lines(cv, nid):
    n = cv.node(nid)
    out = [f"{nid} {n['type']}" + (f" \"{n['title']}\"" if n.get("title") else "")
           + (f"  top-left [{round(G.rect(n)[0])}, {round(G.rect(n)[1])}] size {n['size']}" if cv.placed(n) else "  (not placed)")]
    nodes = cv.nodes
    for i in n.get("inputs") or []:
        l = next((l for l in cv.s["links"] if l["target_id"] == nid and l["target_input"] == i["name"]), None)
        y = f" y={round(cv.in_xy(nid, i['name'])[1])}" if cv.placed(n) else ""
        if l:
            out.append(f"  in  {i['name']} ({i.get('type')}){y} ← {l['origin_id']}.{(nodes[l['origin_id']].get('outputs') or [])[l['origin_slot']].get('name')}")
        elif not i.get("widget"):
            out.append(f"  in  {i['name']} ({i.get('type')}){y} ← none")
    for k, o in enumerate(n.get("outputs") or []):
        ts = [f"{l['target_id']}.{l['target_input']}" for l in cv.s["links"] if l["origin_id"] == nid and l["origin_slot"] == k]
        y = f" y={round(cv.out_xy(nid, k)[1])}" if cv.placed(n) else ""
        out.append(f"  out {o.get('name')} ({o.get('type')}){y} → {' '.join(ts) or 'none'}")
    info = cv.oi.get(n["type"])
    if info and isinstance(n.get("widgets_values"), list):
        for k, v in (CS.map_widget_values(n["type"], n["widgets_values"], cv.oi)[0] or {}).items():
            out.append(f"  value {k} = {json.dumps(v, ensure_ascii=False)[:200]}")
    return out


# ---------------------------------------------------------------- replay

def _short(v, limit):
    """A widget value as the page shows it: numbers and booleans as they are, anything else as text cut to limit."""
    if v is None or isinstance(v, (bool, int)):
        return v
    if isinstance(v, float):
        return float(f"{v:.6g}")
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= limit else s[:limit] + "…"


def _node_def(n, oi, title=None):
    """What does not move: type, title, slots (name, type, wired), widget rows (name, kind, value), colours, mode."""
    t = n.get("type") or "?"
    d = {"t": t, "n": title or display_title(n, oi)}
    for k, src in (("c", "color"), ("bg", "bgcolor")):
        if n.get(src):
            d[k] = n[src]
    if n.get("mode"):
        d["m"] = n["mode"]
    outs = [[o.get("label") or o.get("name") or o.get("type") or "", o.get("type") or "*"] for o in n.get("outputs") or []]
    if t == "Reroute":
        d["rr"] = 1
        d["o"] = outs[:1] or [["", "*"]]
        return d
    if t in NOTE_TYPES:
        d["note"] = _short(str((n.get("widgets_values") or [""])[0]), 1500)
        return d
    names, grow = RD.widget_info(n, oi)
    linked_w = {(i.get("widget") or {}).get("name") for i in n.get("inputs") or [] if i.get("widget") and i.get("link") is not None}
    d["i"] = [[i.get("label") or i["name"], i.get("type") or "*", 1 if i.get("link") is not None else 0]
              for i in n.get("inputs") or [] if not i.get("widget")]
    d["o"] = outs
    info = oi.get(t)
    vals = n.get("widgets_values")
    rows = []
    if info and names:
        mapping = CS.map_widget_values(t, vals, oi)[0] or {}
        for nm in names:
            spec = CS.widget_spec(info, nm, mapping)
            kind = "combo"
            if nm == "upload":
                kind = "btn"
            elif spec is not None:
                typ, opts = CS._spec_type_and_opts(spec)
                kind = {"BOOLEAN": "bool", "INT": "num", "FLOAT": "num", "COMBO": "combo",
                        "COMFY_DYNAMICCOMBO_V3": "combo"}.get(typ, "text")
                if nm in grow:
                    kind = "area"
            v = mapping.get(nm)
            rows.append([nm, kind, _short(v, 600 if kind == "area" else 120), 1 if nm in linked_w else 0])
    elif isinstance(vals, list):
        rows = [["", "text", _short(v, 120), 0] for v in vals]   # a type not in object_info: values without names
    if rows:
        d["w"] = rows
    if image_kind(t, oi):
        d["img"] = 1
    return d


class _Intern:
    """Stores each distinct value once and returns its index (the page is small because states repeat)."""

    def __init__(self):
        self.items, self.index = [], {}

    def __call__(self, v):
        k = json.dumps(v, ensure_ascii=False, sort_keys=True)
        if k not in self.index:
            self.index[k] = len(self.items)
            self.items.append(v)
        return self.index[k]


def wire_key(origin, slot, target, inp):
    return f"{origin}|{slot}|{target}|{inp}"


def _view(cv, defs):
    """One state as the page draws it: placed nodes [id, x, y, w, h, def], wires [x0, y0, x1, y1, type, key],
    groups [title, x, y, w, h, colour]. Positions are the body's top-left (the title bar is above, as in ComfyUI)."""
    nodes = [[n["id"], round(n["pos"][0]), round(n["pos"][1]), round(n["size"][0]), round(n["size"][1]), defs(_node_def(n, cv.oi))]
             for n in cv.s["nodes"] if n.get("pos") is not None and n.get("size")]
    wires = []
    for l in cv.s["links"]:
        pts = cv.wire_pts(l)
        if pts:
            wires.append([round(pts[0][0], 1), round(pts[0][1], 1), round(pts[-1][0], 1), round(pts[-1][1], 1), l.get("type") or "*",
                          wire_key(l["origin_id"], l["origin_slot"], l["target_id"], l["target_input"])])
    groups = [[g.get("title", "")] + [round(v) for v in g["bounding"]] + [g.get("color") or "#3f789e"]
              for g in cv.s.get("groups") or [] if g.get("bounding")]
    return nodes, wires, groups


def _original_view(path, oi, defs):
    """The source workflow's top level as saved (positions are the author's), in the same form as _view."""
    raw = jload(path)
    subs = {s.get("id"): s.get("name") for s in (raw.get("definitions") or {}).get("subgraphs") or []}
    by_id, nodes = {}, []
    for n in raw.get("nodes") or []:
        if not (isinstance(n.get("pos"), (list, dict)) and isinstance(n.get("size"), (list, dict))):
            continue
        m = dict(n)
        m["id"] = str(n["id"])
        m["pos"] = list(n["pos"].values())[:2] if isinstance(n["pos"], dict) else n["pos"][:2]
        m["size"] = list(n["size"].values())[:2] if isinstance(n["size"], dict) else n["size"][:2]
        by_id[m["id"]] = m
        nodes.append([m["id"], round(m["pos"][0]), round(m["pos"][1]), round(m["size"][0]), round(m["size"][1]),
                      defs(_node_def(m, oi, title=n.get("title") or subs.get(n.get("type"))))])
    wires = []
    for l in raw.get("links") or []:
        l = l if isinstance(l, list) else [l.get("id"), l.get("origin_id"), l.get("origin_slot"), l.get("target_id"), l.get("target_slot"), l.get("type")]
        o, t = by_id.get(str(l[1])), by_id.get(str(l[3]))
        if not o or not t or not isinstance(l[2], int) or not isinstance(l[4], int) or l[4] >= len(t.get("inputs") or []):
            continue
        names, grow = RD.widget_info(t, oi)
        a, b = G.output_pos(o, l[2]), G.input_pos(t, t["inputs"][l[4]]["name"], names, grow)
        if a and b:
            wires.append([round(a[0], 1), round(a[1], 1), round(b[0], 1), round(b[1], 1), l[5] if isinstance(l[5], str) else "*",
                          wire_key(o["id"], l[2], t["id"], t["inputs"][l[4]]["name"])])
    groups = [[g.get("title", "")] + [round(v) for v in (g.get("bounding") or [0, 0, 0, 0])[:4]] + [g.get("color") or "#3f789e"]
              for g in raw.get("groups") or []]
    return {"nodes": nodes, "wires": wires, "groups": groups, "api": bool((raw.get("extra") or {}).get("api_format"))}


def _plan_rerun(work, name, before, cmd):
    """The per-line notes of a `layout` run that did not record them (made by an older canvas): applies the plan file as it is
    now to the state before. Returns (lines, notes), or None when the file is gone or no longer gives the same result."""
    import os
    import tempfile
    toks = shlex.split(cmd)
    if len(toks) < 2:
        return None
    rel = Path(toks[1])
    parts = rel.parts
    # the agent may have run the canvas from another folder ("out/w/layout.txt"): find the part of the path that is inside the work folder
    for k in range(len(parts)):
        if (work.dir / Path(*parts[k:])).is_file():
            prefix = Path(*parts[:k]) if k else None
            break
    else:
        return None
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "base"
        base.mkdir()
        if prefix is not None:
            (base / prefix).parent.mkdir(parents=True, exist_ok=True)
            (base / prefix).symlink_to(work.dir.resolve(), target_is_directory=True)
            run_dir = base
        else:
            run_dir = work.dir.resolve()
        cv = Canvas(work, name)
        cv.s = copy.deepcopy(before)
        cv.path = Path(tmp) / "canvas.json"
        cv.hist = Path(tmp) / "none.hist"
        try:
            os.chdir(run_dir)
            do_layout(cv, work, [str(rel)])
        except Exception:  # noqa: BLE001  the plan as it is now does not run on that state: no notes
            return None
        finally:
            os.chdir(cwd)
        rec = cv.s.get("layout_notes", {}).get("-1")
        return cv.s, rec


def _replay_order(work):
    """Canvases made with `new X from Y` follow the one they were made from; the one the most others came from is first."""
    names = work.names()
    parent = {}
    for name in names:
        try:
            first = (Canvas(work, name).s.get("history") or [""])[0].split()
        except Exception:
            continue
        if len(first) == 4 and first[0] == "new" and first[2] == "from" and first[3] in names and first[3] != name:
            parent[name] = first[3]
    kids = {n: [m for m in names if parent.get(m) == n] for n in names}
    size = {}

    def count(n, seen=()):
        if n not in size:
            size[n] = 1 + sum(count(m, seen + (n,)) for m in kids[n] if m not in seen)
        return size[n]
    out = []

    def walk(n):
        if n in out:
            return
        out.append(n)
        for m in sorted(kids[n], key=lambda m: (-count(m), m)):
            walk(m)
    for n in sorted((n for n in names if n not in parent), key=lambda n: (-count(n), n)):
        walk(n)
    out += [n for n in names if n not in out]   # a loop of `from`s
    return out


def replay_page(work, lang="en"):
    """Every command of every canvas, the state after it, and the check problems at that point.
    Commands that change nothing on the drawing (building before anything is placed) are shown together as one step."""
    canvases = []
    oi = work.oi
    for name in _replay_order(work):
        final = Canvas(work, name)
        snaps = sorted(final.hist.glob("*.json")) if final.hist.exists() else []
        states = [json.loads(p.read_text(encoding="utf-8")) for p in snaps] + [final.s]
        cmds = final.s["history"]
        off = len(cmds) - len(snaps)   # a canvas made with `new ... from` starts with a command that has no snapshot
        defs, nodes_t, wires_t, groups_t, probs = _Intern(), _Intern(), _Intern(), _Intern(), _Intern()
        steps = []
        pending = []

        def state_of(s):
            cv = Canvas(work, name)
            cv.s = copy.deepcopy(s)
            cv.update_groups()
            n, w, g = _view(cv, defs)
            lines, counts = full_check(cv)
            return cv, (nodes_t(n), wires_t(w), groups_t(g)), lines, counts

        def problem_refs(cv, lines):
            ids = {n["id"] for n in cv.s["nodes"]}
            wires = {lname(cv, l): wire_key(l["origin_id"], l["origin_slot"], l["target_id"], l["target_input"]) for l in cv.s["links"]}
            out = []
            for ln in lines:
                found = [t for t in dict.fromkeys(re.findall(r"[\w:~]+", ln)) if t in ids]
                ws = [k for s, k in wires.items() if s in ln]
                out.append(probs({"r": ln, "ids": found, "w": ws, "names": {i: _plain_name(cv, i) for i in found}}))
            return out

        cv0, sig0, lines0, counts0 = state_of(states[0])
        prev_sig = sig0
        if off > 0 and cmds and any(n.get("pos") is not None for n in states[0]["nodes"]):
            steps.append({"c": cmds[:off], "x": [_explain(cv0, cv0, c, None) for c in cmds[:off]], "kind": "cmd",
                          "v": sig0, "p": problem_refs(cv0, lines0), "counts": counts0})
        before_cv = cv0
        for k in range(1, len(states)):
            cmd = cmds[off + k - 1] if off + k - 1 < len(cmds) else "?"
            cv, sig, lines, counts = state_of(states[k])
            is_layout = cmd.split(" ", 1)[0] == "layout"
            notes = None
            if is_layout:
                notes = (states[k].get("layout_notes") or {}).get(str(k - 1))
                if notes is None:
                    rerun = _plan_rerun(work, name, states[k - 1], cmd)
                    if rerun and rerun[1] and [n.get("pos") for n in rerun[0]["nodes"]] == [n.get("pos") for n in states[k]["nodes"]]:
                        notes = rerun[1]
            x = _explain(before_cv, cv, cmd, notes)
            if sig == prev_sig and not is_layout:
                pending.append((cmd, x, sig, cv, lines, counts))
            else:
                if pending:
                    _flush(steps, pending, problem_refs)
                    pending = []
                steps.append({"c": [cmd], "x": [x], "kind": "layout" if is_layout else "cmd", "v": sig,
                              "p": problem_refs(cv, lines), "counts": counts})
            prev_sig, before_cv = sig, cv
        if pending:
            _flush(steps, pending, problem_refs)
        canvases.append({"name": name, "defs": defs.items, "nodes": nodes_t.items, "wires": wires_t.items,
                         "groups": groups_t.items, "problems": probs.items, "steps": steps})
    src = work.cfg.get("source")
    odefs = _Intern()
    original = None
    if src and Path(src).is_file():
        original = _original_view(src, oi, odefs)
        original["defs"] = odefs.items
        original.update(_original_counts(work, src))
    return RPL.build(canvases, original, lang)


def _original_counts(work, path):
    """The check counts of the source workflow's top level as saved (the author's positions), to compare the canvases with."""
    raw = jload(path)
    nodes, by = [], {}
    for n in raw.get("nodes") or []:
        if not (isinstance(n.get("pos"), (list, dict)) and isinstance(n.get("size"), (list, dict))):
            continue
        m = dict(n)
        m["id"] = str(n["id"])
        for k in ("pos", "size"):
            m[k] = list(n[k].values())[:2] if isinstance(n[k], dict) else list(n[k])[:2]
        for k in ("inputs", "outputs"):
            m[k] = [dict(x, type=x.get("type") if isinstance(x.get("type"), str) else "COMBO") for x in n.get(k) or []]
        by[m["id"]] = m
        nodes.append(m)
    links = []
    for l in raw.get("links") or []:
        l = l if isinstance(l, list) else [l.get("id"), l.get("origin_id"), l.get("origin_slot"), l.get("target_id"), l.get("target_slot"), l.get("type")]
        t = by.get(str(l[3]))
        if str(l[1]) not in by or not t or not isinstance(l[4], int) or l[4] >= len(t["inputs"]):
            continue
        links.append({"id": l[0], "origin_id": str(l[1]), "origin_slot": l[2], "target_id": str(l[3]),
                      "target_input": t["inputs"][l[4]]["name"], "type": l[5]})
    cv = Canvas(work, "original (not saved)", fresh=True)
    cv.s.update(nodes=nodes, links=links)
    try:
        counts = full_check(cv)[1]
    except Exception:   # a source the checks cannot read: no comparison rather than no page
        return {}
    return {"counts": counts}


def _flush(steps, pending, problem_refs):
    """Commands that changed nothing on the drawing, shown as one step (the problems are those after the last one)."""
    cmd, x, sig, cv, lines, counts = pending[-1]
    steps.append({"c": [p[0] for p in pending], "x": [p[1] for p in pending], "kind": "build" if len(pending) > 1 else "cmd",
                  "v": sig, "p": problem_refs(cv, lines), "counts": counts})


def _plain_name(cv, nid):
    n = cv.nodes.get(nid)
    if not n:
        return nid
    if n.get("type") == "Reroute":
        return "Reroute"
    return display_title(n, cv.oi)


def _wired_pairs(cv, toks):
    """For put right|left and row without an alignment word: whether each pair placed side by side is wired
    (then the canvas made the wire horizontal, otherwise it aligned the tops)."""
    def wired(a, b):
        try:
            return bool(cv.link_between(cv.unit(a), cv.unit(b)))
        except Stop:
            return False
    if len(toks) >= 4 and toks[0] == "put" and toks[2] in ("right", "left") and not set(toks[4:]) & set(ALIGNS):
        return {"wired": wired(toks[1], toks[3])}
    if toks and toks[0] == "row" and not {"top", "wire"} & set(toks):
        pos, opt = parse_opts(toks[1:], flags=set(), keyed=("right", "gap"))
        units = ([opt["right"]] if "right" in opt else []) + pos
        return {"wired": [wired(a, b) for a, b in zip(units, units[1:])]}
    return {}


def _explain(before, after, cmd, notes):
    """What the page needs to explain one command: the parsed words and the names of the nodes and blocks it mentions
    (replay.py writes the sentence in the page's language)."""
    try:
        toks = shlex.split(cmd, comments=True)
    except ValueError:
        toks = cmd.split()
    names, before_names, blocks = {}, {}, {}
    for cv in (after, before):
        for b, ids in cv.s.get("blocks", {}).items():
            blocks.setdefault(b, list(ids))
    for t in toks:
        for part in {t, t.split(".", 1)[0]}:
            if part in after.nodes:
                names.setdefault(part, _plain_name(after, part))
            if part in before.nodes:
                before_names.setdefault(part, _plain_name(before, part))
                names.setdefault(part, before_names[part])
    groups = sorted({g["title"] for cv in (after, before) for g in cv.s.get("groups") or []})
    x = {"toks": toks, "names": names, "before": before_names, "blocks": {b: v for b, v in blocks.items() if b in toks},
         "groups": [g for g in groups if g in toks]}
    x.update(_wired_pairs(after, toks))
    if notes is not None:
        x["lines"], x["notes"] = notes.get("lines"), notes.get("notes") or []
        for ln in x["notes"]:
            for t in re.findall(r"[\w:~]+", ln):
                if t in after.nodes:
                    names.setdefault(t, _plain_name(after, t))
                if t in after.s.get("blocks", {}):
                    x["blocks"].setdefault(t, list(after.s["blocks"][t]))
    return x


def main():
    ap = argparse.ArgumentParser(description="A canvas operated by an AI agent (the command list is at the top of canvas.py)", add_help=True)
    ap.add_argument("--dir", default=".")
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    work = Work(a.dir)
    if not a.rest:
        print(__doc__)
        return
    if a.rest[0] == "run":
        if len(a.rest) < 2 or not Path(a.rest[1]).is_file():
            print("Stopped (nothing changed): run <file of commands> (no such file)")
            sys.exit(1)
        lines = Path(a.rest[1]).read_text(encoding="utf-8").splitlines()
        work.consume(a.rest[1])
        for line in lines:
            if not line.strip() or line.strip().startswith("#"):
                continue
            print(f"> {line.strip()}")
            try:
                for s in run_cmd(work, line):
                    print(s)
            except Stop as e:
                print(f"Stopped: {e}")
                print("(Stopped here. This line changed nothing. The remaining lines were not run.)")
                sys.exit(1)
            work = Work(a.dir)
        return
    line = shlex.join(a.rest)
    try:
        for s in run_cmd(work, line):
            print(s)
    except Stop as e:
        print(f"Stopped (nothing changed): {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
