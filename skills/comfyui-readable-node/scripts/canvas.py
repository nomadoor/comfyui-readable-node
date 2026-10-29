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
  order <name> ...         the order of the canvases on the report page, left to right: the basic workflow first, then those
                           that add to it (t2i before i2i and edit, the normal version before its fast version), parts last.
                           Name every canvas. Canvases of the same form that differ only in values (one per model) share one
                           tab: write them next to each other as <tab>/<canvas> (t2i/t2i_walnut t2i/t2i_naixl …)

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
  There are no numbers in placing: the canvas keeps every gap (columns 60, rows 45, measured from hand-made layouts),
  plus the group padding where a group frame lies between two nodes (the gap is kept frame to node, frame to frame).
  After the plan's lines, a gap between two columns where wires cross 3 times or more is widened to twice the column gap (the report
  page lists each one); a node reaching over the gap whose right edge is the right edge of the column moved goes with it. Nothing else moves after the plan's lines: what the plan writes is where things stand.
  Widths are the canvas's too: each node keeps its own, and loaders stacked in one column get the widest of them.
  put <unit> right <ref> [top|wire|bottom|middle|step]   to the right of ref. Default: wire if a wire connects them, else top.
                           step: one step down, just below the wire leaving ref (a staircase: an output node under a wire that passes on)
  put <unit> left <ref> [top|wire|bottom|middle|step]   step: just below the wire entering ref (a side node under the image wire)
  put <unit> below <ref> [left|right|center]       below ref. Default: left edges aligned
  put <unit> above <ref> [left|right|center]
      wire: at the height where the (first) wire between ref and unit is horizontal
  put <unit> right|left <A> below|above <B>   beside A and below or above B (x from A, y from B; also written
                           put <unit> below|above <B> right|left <A>): a place that one reference does not give
      <ref> may be all: every placed node but Notes (rail Reroutes too, not the unit being placed) with the group
                           frames (note <file> left all; align top all <Note>)
  row <unit> ... [right <ref>] [top|wire]   one row from left to right (the first goes right of ref, or stays where it is).
                           Default: wire between neighbours that are wired, top between those that are not
  stack <unit> ... [below <ref>] [left|right]  one column from top to bottom
  align <top|bottom|left|right|middle|center> <unit|all> <unit> ...   aligns to the first unit (the first does not move)
  core <sampler id>        prints the plan lines of the usual form around that sampler (readable-form.md, "The usual form"):
                           sources column, model row, Load VAE, decoder, Save (Compare is left to the plan: where its wires
                           need the fewest Reroutes). Paste them into the plan and adjust. Only for the first
                           stage. The sampler and its sources column always; a part the usual shape lacks (a positive
                           conditioning, a decoder) is named in a comment, to be placed by relations
  guide                    prints the lines of references/ (rules, techniques, the replacement list, examples) that name a
                           node on the current canvas, by node type. Run it once the nodes are built, and again before writing the plan
  inputs <id>              puts the sources wired directly into that node in one right-aligned column on its left (in input order, top to bottom). Only the sources move; a source an earlier stage's sampler also takes stays with that stage.
                           Column height: the source that carries the conditioning enters at the node's height (KSampler: the positive wire
                           horizontal; SamplerCustomAdvanced: the guider's wire horizontal); a node that takes neither is centred on the column
  shape <laid-out block> <block to lay out> [right|below|left|above <ref>]
                           places the nodes of the second block in the same shape as the first (nodes of the same type are matched in order).
                           For laying out similar stages, or giving split workflows the same layout
  level <A>.<output> <B>.<input> [move <unit>]   moves so that this wire is horizontal (default: moves B)
  block <name> <id> ...     makes a block (making it again replaces it). unblock <name>
  group <title> <unit> ... [color <color>]   makes a group. The frame is recomputed from its nodes every time (padding measured from hand-made layouts)
  ungroup <title>
  group-align <title> ...   aligns the top and bottom edges of these groups
  color <color|none> <id> ...    color (red brown green blue pale_blue cyan purple yellow black)
  rail <A>.<output> [above <unit>|below <unit>|level <X>.<output>] to <B>.<input> ...
      Rail: carries A's output to many targets along a straight path of Reroutes. What you need to know:
        1. Write all targets on one line. The rail runs at the height written (above X / below X / level X.output) or,
           with none written, at the source's output height. The canvas does not look for a height, move the source or
           move nodes to make room: place the source and the targets so the rail runs where the rules want it (model,
           vae, clip from the top; conditioning above the samplers and below those).
        2. The rail is drawn as written, with its Reroutes, even where a direct wire would pass behind nothing (the check
           then names a Reroute that does nothing). Where a wire is better direct, do not write it on the rail.
        3. A rail that runs behind a node is drawn anyway and named in the check: place the source or the targets differently.
  note <md file> <right|left|below|above> <ref> ...   places a MarkdownNote (default width 400, height from the text), as put
                           places (alignment, a second reference, all). In a layout, note lines and lines naming a Note
                           run last, after the rails, in the order written; those that use all after the others. A
                           Note placed against nodes of one group runs where it is written, once they stand, as part
                           of that group: the frame takes it in
  walk <md file>           the walkthrough of the current canvas, for the report page: the workflow cut into parts in processing order.
                           File: "# <one sentence: what the workflow does>", then for each part "## <title>", a line
                           "nodes: <id> ... block:<name> group:<title>" (a group title with spaces: write its ids), one sentence on what
                           the part does, and "- " bullets (`node names`, the values that matter, what to change; indent to nest).
                           Stops on an unknown id, block or group, on a Note or Reroute id, on a node in two parts, and
                           on a part without text; names the nodes in no part
  review <md file>         registers the review of the current canvas's exported workflow (references/review.md): the table
                           | rule | nodes | what to change | answer |, "No findings." or "Not reviewed: <why>". Node numbers are those of the exported
                           workflow; they are shown with the canvas ids. The report page shows every row; finish stops while a
                           canvas has no review or a row has no answer

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
                           Allowed commands: block put row stack align level inputs shape group group-align
                           color rail note title, and include <plan file> (that file's lines go there: canvases of the
                           same form share one plan for what they have in common). Write the inside of each block first (make the block, then lay out its inside),
                           and the blocks relative to each other last (put <block> ...).
                           The first line inside a block gives its first node a position (put <id> origin; row and stack
                           do this for an unplaced first unit): put ... right <id> and inputs <id> need <id> placed. If any line stops, nothing changes. Returns an error log: what the canvas did beyond the lines, what is unplaced, and each form that breaks a rule of the skill with the rule's file and section and its bold sentence (every notice: check).
                           To fix things, edit the lines of the file and run layout again. One run can fix any number of places

■ Viewing and checking
  show                     nodes on the current canvas (position, size, block, color, mode) and what is not placed
  node <id>                a node's inputs/outputs, values and slot positions
  check                    the checks (unplaced, overlaps, narrow gaps, wires behind nodes, crossings, non-horizontal wires, backward wires,
                           right edges of sampler inputs, empty band across everything, width differences and value node tops,
                           Preview above its source, gaps inside a column, gap to a wired neighbour, spacing in a row,
                           consecutive Reroutes, Reroutes doing nothing, model Note top edge, rails that can run at the output height,
                           single values carried with Reroutes, overlapping rails, rail order against loader order, raising Reroutes right of a loader,
                           loader rails above their targets, wires over group titles, nodes overlapping groups, main flow off its line, Note away from its node, reference wire level and chain wire slanted, no wire level into a merging node,
                           types and required inputs).
                           The forms the rules call Bad are listed first (overlaps, a node or Reroute below a node
                           that grows, a Preview or Save above its source, backward wires, wires or nodes over a group title, model / vae /
                           clip rails out of order, Reroutes doing nothing or one after another, a slanted link of a chain one move makes
                           horizontal, samplers off the eye line, a main flow wire that is not horizontal, a side-use image rail above,
                           a Reroute raising a loader's rail, a loader away from its first user, a wire into Compare or another output hidden behind
                           a node that saves, sampler sources not right-aligned,
                           the model Note off the top edge, a Note away from the node it explains, nodes the replacement list replaces); then the ones that weigh less
                           (single values on Reroutes, an image or latent wire hidden behind a preview node, a title the author
                           gave, other slanted wires one move makes horizontal). They are reported, and stop nothing
  diff                     compares the source with all canvases (values, inputs the user fills in, outputs, mode, model Note)
  render <png> [export]    picture (for the review: with export, the node numbers of the exported workflow)
  export <json>            writes a workflow that ComfyUI can open
  report <html> [<language code>]
                           writes the report page: it steps through every command on every canvas (for the user to see
                           what was done). Give the user's language code (en, ja, zh, fr, ...; en by default). The page's
                           own sentences are in Japanese for ja and in English for every other code
  finish                   deletes the working folder once every canvas is exported and the report page is up to date
                           (otherwise it stops, says what is missing and deletes nothing). Only files the canvas knows are deleted:
                           what it wrote, the plan and Note files it was given, understanding.md. Other files are left, and so is the folder.
  finish fast              the same, when the user asked for it fast: the review and the report page are not asked for
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
import relations as RL  # noqa: E402
import replace as RP  # noqa: E402
import report as RPT  # noqa: E402
import validate as VD  # noqa: E402
import write_workflow as WW  # noqa: E402
from layout_params import P  # noqa: E402

H_GAP, V_GAP = P["H_GAP"], P["V_GAP"]
GAP_WIDE = P["GAP_WIDE"]   # the gap between two columns whose wires cross CROSS_WIDEN times or more between them
CROSS_WIDEN = P["CROSS_WIDEN"]
# the tests build odd shapes with move and numeric gaps; a plan never can (it places by relations only)
HAND_PLACING_FOR_TESTS = False
AUTO_LEVEL = True   # the layout levels wires and closes gaps by itself (a test of one placing alone turns it off)
# the layout keeps the plan's vertical relations and solves the heights all at once (relations.py); being built, off by default
LAYOUT_SOLVE = False
# the layout's own fixes after the plan (levelling, widening and closing gaps, clearing below growing nodes, pulling rails
# together, railing wires along rails, separating groups, clearing frames). Off only to compare
AUTO_FIX = False
# after the plan's lines the canvas moves nothing by itself: the one move kept is widening a gap
# between two columns where wires cross 3 times or more
WIDE_GAP = True
# rails without a written height run at their source's output height: the canvas does not look for a height, move nodes
# to open a lane, or swap heights. The plan places the sources
PLAN_RAILS = True
# a Note goes where the plan writes it: the canvas does not try the other sides or turn below into above
NOTE_SEARCH = False
# level moves only the unit it names: the nodes wired level to it do not move along
LEVEL_CARRIES = False
FRONTEND_MIN = json.loads((Path(__file__).resolve().parent / "frontend_min_sizes.json").read_text(encoding="utf-8"))["sizes"]
PAD_L, PAD_T, PAD_R, PAD_B = P["GROUP_PAD_LEFT"], P["GROUP_PAD_TOP"], P["GROUP_PAD_RIGHT"], P["GROUP_PAD_BOTTOM"]
GROUP_TITLE_H = 34          # height of the frontend's group title bar (font_size 24 x 1.4)
TEXT_MIN_H = 100            # minimum height of a text area (a number set by the skill author)
# a CLIP Text Encode that only names what SAM3 looks for holds one short sentence: the width of the SAM3 nodes, a text
# area of a few lines (the skill author keeps these small; 17 in 10 hand-made layouts, 250-303 wide)
SAM3_PROMPT_SIZE = (270, 100)
# image area added to the initial size of nodes that show an image (layout_params.json), by the kind image_kind returns
IMAGE_AREA = {"save": P["IMAGE_AREA_SAVE"], "preview": P["IMAGE_AREA_PREVIEW"], "load": P["IMAGE_AREA_LOAD"]}
IMAGE_UPLOAD_FLAGS = tuple(f for f in CS.UPLOAD_FLAGS if f in ("image_upload", "video_upload"))
LOADER_MIN_W = 300          # minimum loader width (rounded from the median of 734 loaders in hand-made layouts, 301)
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
NOT_PROCESSING = {"Reroute"} | NOTE_TYPES   # on the canvas but not a step of the processing (left out of walkthrough parts)
# working keys from reading, dropped when copying from the source. orig_size is kept (used for the size of custom nodes that are not installed)
WORK_KEYS = WW.NODE_WORK_KEYS - {"orig_size"}
# marks only the canvas adds. Dropped on export
CANVAS_MARKS = {"size_min", "width_set", "loader_base", "loader_shift", "canvas_note", "layout_prev", "group_note", "note_ref"}


class Stop(Exception):
    pass


class AllIds(list):
    """The reference `all`: every placed node but Notes (rail Reroutes too) and the ones being placed. As a reference its
    box takes in the group frames."""


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


# Video Helper Suite nodes whose preview fits the video's height (their inputs say IMAGE, not VIDEO)
VHS_VIDEO_PREVIEW = {"VHS_VideoCombine", "VHS_LoadVideo", "VHS_LoadVideoPath", "VHS_LoadVideoFFmpeg", "VHS_LoadVideoFFmpegPath"}


def shows_video(t, oi):
    """Whether a node type shows a video: a VIDEO input or a video upload, or a Video Helper Suite video node."""
    if t in VHS_VIDEO_PREVIEW:
        return True
    info = oi.get(t) or {}
    for _, sp, _ in CS.ordered_input_specs(info):
        if isinstance(sp, (list, tuple)) and sp:
            typ, opts = CS._spec_type_and_opts(sp)
            if typ == "VIDEO" or opts.get("video_upload"):
                return True
    return False


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
        (sticking out of its column), or stick out past the sampler stacked right above or below it, is not widened. A loader whose width was set with width (width_set) is not
        widened either: it would no longer match the nodes it was made as wide as.
        The width before widening is kept in loader_base and the width is recomputed from it every time."""
        for n in self.s["nodes"]:
            if "loader_base" in n:
                n["size"][0] = max(n.pop("loader_base"), (n.get("size_min") or [0, 0])[0])
                if n.get("pos") is not None:
                    n["pos"][0] += n.pop("loader_shift", 0)
        ls = [n for n in self.s["nodes"] if self.is_model_loader(n) and n.get("size")]
        if not ls:
            return
        w = max([LOADER_MIN_W] + [n["size"][0] for n in ls])
        for n in ls:
            if n["size"][0] == w or n.get("width_set"):
                continue
            base = n["size"][0]
            # a loader whose right edge is on the right edge of the node stacked right below or above it keeps it there
            # (it widens to the left)
            left = self.placed(n) and any(abs(G.rect(m)[2] - G.rect(n)[2]) < 1 and self.stacked(n, m) for m in self.s["nodes"]
                                          if m is not n and self.placed(m) and m.get("type") not in {"Reroute"} | NOTE_TYPES
                                          and "Loader" not in (m.get("type") or "") and not self.is_model_loader(m))
            # widest first; if that overlaps a neighbour, at least the minimum width; else leave it as it is
            for cand in (w, max(base, LOADER_MIN_W)):
                if cand == base:
                    break
                n["size"][0] = cand
                if left:
                    n["pos"][0] -= cand - base
                if not (self.placed(n) and (any(rect_overlap(G.rect(n), G.rect(m)) for m in self.s["nodes"]
                                                if m is not n and self.placed(m)) or self.sticks_out(n, base))):
                    n["loader_base"] = base
                    if left:
                        n["loader_shift"] = cand - base
                    self.changed.add(n["id"])
                    break
                n["size"][0] = base
                if left:
                    n["pos"][0] += cand - base
        self.same_column_loader_width()

    def same_column_loader_width(self):
        """Loaders stacked in one column (any node whose type name contains Loader and that takes no wire: IPAdapter Model
        Loader, Load CLIP Vision, Load Model Patch, …) get the widest width of that column (the skill author). A column whose right edges are aligned keeps them aligned (it widens to the left). Not widened when that
        would overlap another node."""
        wired_in = {l["target_id"] for l in self.s["links"]}
        ls = [n for n in self.s["nodes"] if self.placed(n) and n.get("size") and n["id"] not in wired_in
              and (self.is_model_loader(n) or "Loader" in (n.get("type") or ""))]
        ls.sort(key=lambda n: G.rect(n)[1])
        cols, seen = [], set()
        for n in ls:
            if n["id"] in seen:
                continue
            col, cur = [n], n
            seen.add(n["id"])
            for m in ls:
                if m["id"] in seen:
                    continue
                r, q = G.rect(cur), G.rect(m)
                if min(r[2], q[2]) > max(r[0], q[0]) and 0 <= q[1] - r[3] <= V_GAP + 1:
                    col.append(m)
                    seen.add(m["id"])
                    cur = m
            if len(col) > 1:
                cols.append(col)
        for col in cols:
            w = max(n["size"][0] for n in col)
            right = len({round(G.rect(n)[2]) for n in col}) == 1
            for n in col:
                d = w - n["size"][0]
                if d <= 0:
                    continue
                n["size"][0] = w
                if right:
                    n["pos"][0] -= d
                if any(rect_overlap(G.rect(n), G.rect(m)) for m in self.s["nodes"] if m is not n and self.placed(m)):
                    n["size"][0] -= d
                    if right:
                        n["pos"][0] += d
                    continue
                n["loader_base"] = n.get("loader_base", w - d)
                n["loader_shift"] = n.get("loader_shift", 0) + (d if right else 0)
                self.changed.add(n["id"])

    def stacked(self, n, m):
        """Whether m stands right below or above n in its column (overlapping in x, within a row gap)."""
        r, q = G.rect(n), G.rect(m)
        return min(r[2], q[2]) > max(r[0], q[0]) and (0 <= q[1] - r[3] <= V_GAP + 1 or 0 <= r[1] - q[3] <= V_GAP + 1)

    def sticks_out(self, n, base):
        """Whether loader n, widened from base, sticks out past the right edge of a sampler stacked right above or below
        it in its column (a Load VAE above a KSampler made wider than the KSampler). Above another node (a Load CLIP above
        Format Text) it is widened like the other loaders."""
        r = G.rect(n)
        for m in self.s["nodes"]:
            if m is n or not self.placed(m) or m.get("type") in {"Reroute"} | NOTE_TYPES or self.is_model_loader(m):
                continue
            q = G.rect(m)
            if not is_sampler(m):
                continue
            stacked = min(r[2], q[2]) > max(r[0], q[0]) and (0 <= q[1] - r[3] <= V_GAP + 1 or 0 <= r[1] - q[3] <= V_GAP + 1)
            if stacked and r[2] > q[2] and n["size"][0] > base:
                return True
        return False

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

    def unit(self, tok, allow_all=False):
        if tok == "all":
            if not allow_all:
                raise Stop("all (every placed node) is only a reference: put <unit> <where> all, align <how> all <unit>")
            # the workflow itself: not its Notes (a Note placed high would set the top the overview Note aligns to)
            return AllIds(n["id"] for n in self.s["nodes"] if self.placed(n) and n.get("type") not in NOTE_TYPES)
        if tok in self.s["blocks"]:
            ids = list(self.s["blocks"][tok])
            # a Note on a node of the block, placed with its group, moves with the block (as with a group's title)
            return ids + [n["id"] for n in self.s["nodes"] if n.get("group_note") and n.get("note_ref") in ids
                          and n["id"] not in ids and self.placed(n)]
        if tok in self.nodes:
            return [tok]
        # a group's title: every node the plan puts in that group moves together
        members = plan_groups(self).get(tok)
        if members:
            return sorted(members)
        raise Stop(f"{tok} is neither a node, a block nor a group title")

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
        if self.grow_input(n, p) or self.widget_input(n, p):
            return nid, p
        raise Stop(f"{nid} has no input {p} ({', '.join(i['name'] for i in n.get('inputs') or [])})")

    def widget_input(self, n, name):
        """Gives a widget its input slot (seed, text, ...), as the frontend does when a wire is dropped on the widget.
        True if the node has such a widget."""
        info = self.oi.get(n.get("type"))
        if not info or not isinstance(n.get("widgets_values"), list):
            return False
        names = [i["name"] for i in n.get("inputs") or []]
        ins, _ = CS.new_node_slots(info, n["widgets_values"], names)
        new = next((i for i in ins if i["name"] == name and i.get("widget")), None)
        if new is None:
            return False
        # the inputs the node has keep their places (and their wires); widget inputs come after the sockets
        n["inputs"] = list(n.get("inputs") or []) + [new]
        return True

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
        if n.get("pos") is not None:
            n["pos"][0] += n.pop("loader_shift", 0)
        title = display_title(n, self.oi)
        size = nodesize.default_size(n, self.oi, title=title)
        if size is None:
            size = nodesize.estimate_unknown(n)
            o = n.get("orig_size")
            if o:
                size = [max(size[0], o[0]), max(size[1], o[1])]
        w, h = size
        kind = image_kind(n.get("type"), self.oi)
        fm = FRONTEND_MIN.get(n.get("type"))
        if fm:
            # e.g. nodes the frontend adds widgets to later. Never smaller than the size the frontend makes (it would grow and break the layout when opened in ComfyUI)
            w, h = max(w, fm[0]), max(h, fm[1])
        if kind:
            # a square image area below the initial size (a landscape image and a portrait one are shown at the same
            # size): the node is at least as wide as the area, and that much taller
            w, h = max(w, IMAGE_AREA[kind]), h + IMAGE_AREA[kind]
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
        # Nodes 2.0 draws a node taller than the legacy renderer: one margin for every type (layout_params.json)
        if n.get("type") not in {"Reroute"} | NOTE_TYPES:
            h += P["VUE_MARGIN"]
        if n.get("type") == "PreviewAny":
            # Preview as Text shows text: big enough to read it (layout_params.json)
            w, h = max(w, P["PREVIEW_TEXT_SIZE"][0]), max(h, P["PREVIEW_TEXT_SIZE"][1])
        if self.is_sam3_prompt(n):
            w, h = SAM3_PROMPT_SIZE
        old = n.get("size")
        n["size"] = [round(w), round(h)]
        if old and old != n["size"]:
            self.out.append(f"size {n['id']}: {old} → {n['size']}")
            self.changed.add(n["id"])

    def is_sam3_prompt(self, n):
        """A CLIP Text Encode whose conditioning goes only into SAM3 nodes (followed through Reroutes)."""
        if n.get("type") != "CLIPTextEncode":
            return False
        ends = [self.nodes.get(l["target_id"], {}).get("type") or "" for l in ends_through_reroutes(self, n["id"])]
        return bool(ends) and all(t.startswith("SAM3") for t in ends)

    def clip_loader_role_color(self):
        """A clip loader is yellow only when its CLIP reaches a text encoder (a node that makes conditioning). One that
        feeds only something else (an LLM's Generate Text) does another job and takes no fixed colour; one that feeds
        both is yellow. Run once the wires are known: the fixed colour is given when a node is copied."""
        yellow = list(COLORS["yellow"])
        for n in self.s["nodes"]:
            outs = [o.get("type") for o in n.get("outputs") or []]
            if not (self.is_model_loader(n) and outs[0] == "CLIP") or [n.get("color"), n.get("bgcolor")] != yellow:
                continue
            # follow the CLIP through Reroutes and through nodes that pass a CLIP on (Load LoRA, CLIP Set Last Layer)
            seen, todo, reaches = set(), [n["id"]], False
            while todo and not reaches:
                cur = todo.pop()
                for l in ends_through_reroutes(self, cur):
                    if (l.get("type") or "CLIP") != "CLIP":
                        continue
                    m = self.nodes.get(l["target_id"]) or {}
                    if m.get("id") in seen:
                        continue
                    seen.add(m.get("id"))
                    outs_m = [o.get("type") for o in m.get("outputs") or []]
                    if "CONDITIONING" in outs_m:
                        reaches = True
                        break
                    if "CLIP" in outs_m:
                        todo.append(m["id"])
            if not reaches:
                n.pop("color", None)
                n.pop("bgcolor", None)
                self.out.append(f"colour {n['id']}: no fixed yellow (its CLIP reaches no text encoder)")

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
            # a frame is drawn around the nodes of its group, not the Notes on other nodes; a Note on a
            # node of the group is part of it
            for n in self.s["nodes"]:
                if n.get("group_note") == g["title"] and n["id"] not in g["members"]:
                    g["members"].append(n["id"])
            ids = [i for i in g["members"] if i in self.nodes and self.placed(self.nodes[i])
                   and (self.nodes[i].get("type") not in NOTE_TYPES or self.nodes[i].get("group_note") == g["title"])]
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
        # numbers given to nodes without one stay the same from export to export (kept with the working folder)
        fixed = self.work.cfg.setdefault("export_ids", {}).setdefault(self.name, {})
        wf, ids = WW.write(f, groups, fixed)
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


GUIDE_FILES = ("readable-form.md", "content.md", "notes.md", "techniques.md", "replacements.md", "examples.md")


def _guide_pieces(path):
    """The pieces of a reference file a guide quotes: a table row, a bullet, a paragraph, or a block of an example (its bold
    heading and code block together), each with the heading it stands under."""
    text = path.read_text(encoding="utf-8")
    out, head, buf, in_code = [], "", [], False

    def flush():
        if buf:
            out.append((head, "\n".join(buf).strip()))
            buf.clear()
    for ln in text.splitlines():
        if ln.startswith("```"):
            in_code = not in_code
            buf.append(ln)
            if not in_code:
                flush()
            continue
        if in_code:
            buf.append(ln)
            continue
        if ln.startswith("#"):
            flush()
            head = ln.lstrip("#").strip()
            continue
        if not ln.strip():
            if buf and not buf[-1].startswith("**"):
                flush()
            continue
        if ln.startswith(("- ", "| ")) and buf and not buf[-1].startswith("**"):
            flush()
        buf.append(ln)
        if ln.startswith("| "):
            flush()
    flush()
    return out


def guide(cv):
    """The lines of the rules, the techniques, the replacement list and the examples that name a node on this canvas, by
    node type: what the agent needs from those files for this workflow, read right before writing the plan (it read
    everything at the start, long before). Rules that name no node are not here: read readable-form.md."""
    names = {}
    for n in cv.s["nodes"]:
        t = n.get("type") or ""
        if t in {"Reroute"} | NOTE_TYPES:
            continue
        shown = (cv.oi.get(t) or {}).get("display_name") or t
        names.setdefault(t, {"shown": shown, "count": 0})
        names[t]["count"] += 1
    pieces = [(f, h, b) for f in GUIDE_FILES if (REFS / f).is_file() for h, b in _guide_pieces(REFS / f)]

    def names_it(body, word):
        i = body.find(word)
        while i >= 0:
            before = body[i - 1] if i else " "
            after = body[i + len(word)] if i + len(word) < len(body) else " "
            if not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_"):
                return True
            i = body.find(word, i + 1)
        return False
    out = ["# the lines of references/ that name a node on this canvas (read them before writing the plan; rules that name",
           "# no node are in readable-form.md)"]
    for t, v in sorted(names.items(), key=lambda kv: kv[1]["shown"]):
        def about(f, b):
            # a row of the replacement list is about the node it replaces (its first cell), not about what it builds with
            text = b.split("|")[1] if f == "replacements.md" and b.startswith("|") else b
            return names_it(text, t) or (len(v["shown"]) > 3 and names_it(text, v["shown"]))
        hits = [(f, h, b) for f, h, b in pieces if about(f, b)]
        if not hits:
            continue
        out.append(f"\n## {v['shown']} ({t})" + (f" ×{v['count']}" if v["count"] > 1 else ""))
        seen = set()
        for f, h, b in hits[:6]:
            key = (f, b)
            if key in seen:
                continue
            seen.add(key)
            body = b if len(b) <= 600 else b[:600] + " …"
            out.append(f"- {f} — {h}:\n  " + body.replace("\n", "\n  "))
        if len(hits) > 6:
            out.append(f"- ({len(hits) - 6} more: grep references/ for {v['shown']})")
    if len(out) == 2:
        out.append("(no line of references/ names a node on this canvas)")
    return out


def core_plan(cv, sid):
    """The plan lines of the usual form around one sampler (readable-form.md, "The usual form"): relations only, to paste
    into the plan and adjust. The sampler at the origin and its sources column always; the parts of the usual shape that
    are missing (a positive conditioning, a decoder) are named in a comment, to be placed by relations. Stops only for a
    sampler that takes another sampler's result (a later stage)."""
    sm = cv.node(sid)
    if not is_sampler(sm):
        raise Stop(f"{sid} is not a sampler")
    links = cv.s["links"]

    def src(nid, name):
        l = next((l for l in links if l["target_id"] == nid and l["target_input"] == name), None)
        return l["origin_id"] if l else None

    def outs_of(nid):
        return [cv.nodes[l["target_id"]] for l in links if l["origin_id"] == nid and l["target_id"] in cv.nodes]

    def upstream(nid, typ):
        """Follow the input of type typ upstream, as long as each node has one: [farthest … nearest]."""
        chain, cur, seen = [], nid, set()
        while cur and cur not in seen:
            seen.add(cur)
            n = cv.node(cur)
            nxt = next((l["origin_id"] for l in links if l["target_id"] == cur
                        and (next((i for i in n.get("inputs") or [] if i.get("name") == l["target_input"]), {}) or {}).get("type") == typ), None)
            if nxt is None:
                break
            chain.insert(0, nxt)
            cur = nxt
        return chain

    # only for the first stage: no sampler upstream of this one
    seen, todo = set(), [sid]
    while todo:
        cur = todo.pop()
        for l in links:
            if l["target_id"] == cur and l["origin_id"] not in seen:
                seen.add(l["origin_id"])
                todo.append(l["origin_id"])
    if any(is_sampler(cv.nodes[i]) for i in seen if i in cv.nodes):
        raise Stop(f"{sid} takes the result of another sampler: core is for the first stage only; place later stages "
                   f"by relations (the wire from the previous stage horizontal)")
    guider = src(sid, "guider")
    cond_at = guider or sid
    pos = src(cond_at, "positive") or src(cond_at, "conditioning")
    model_at = guider or sid
    mchain = upstream(model_at, "MODEL")
    decodes = [n for n in outs_of(sid) if "LATENT" not in {o.get("type") for o in n.get("outputs") or []}
               and any(i.get("type") == "VAE" for i in n.get("inputs") or [])]
    dec = decodes[0]["id"] if decodes else None
    outs = [n for n in outs_of(dec) if is_output_node(cv, n)] if dec else []
    save = next((n["id"] for n in outs if "Compare" not in n.get("type", "")), None)
    compare = next((n["id"] for n in outs if "Compare" in n.get("type", "")), None)
    vae = src(dec, "vae") if dec else None
    vae_only_decode = vae and cv.is_loader(cv.node(vae)) and all(
        any(i.get("type") == "VAE" and src(t["id"], i.get("name")) == vae for i in t.get("inputs") or []) and t["id"] == dec
        for t in outs_of(vae))
    out = [f"# the usual form around {sid} (readable-form.md, \"The usual form\"); paste into the plan and adjust",
           f"put {sid} origin",
           f"inputs {sid}" + ("" if not guider else f"   # {guider} is the guider: its conditioning enters it horizontally")]
    anchor = pos or sid
    if not pos:
        out.append(f"# {sid} has no positive conditioning wired: place what feeds it by relations, against the node it feeds")
    if guider:
        # the conditioning chain into the guider, level with it, leftwards (encoder → … → guider)
        cchain = upstream(guider, "CONDITIONING")
        prev = guider
        for nid in reversed(cchain):
            out.append(f"put {nid} left {prev} wire")
            prev = nid
        anchor = cchain[0] if cchain else guider
    if mchain:
        out += [f"block model_{sid} {' '.join(mchain)}", f"row {' '.join(mchain)}",
                f"put model_{sid} above {anchor} right   # the model row above the encoders; its wire may slant"]
    if vae and vae_only_decode and vae not in mchain:
        out.append(f"put {vae} above {sid}   # Load VAE used only by the decoder")
    if dec:
        out.append(f"put {dec} right {sid} wire")
    else:
        nxt = [n["id"] for n in outs_of(sid) if is_sampler(n)]
        out.append(f"# no decoder takes {sid}'s latent: place what follows by relations"
                   + (f", the next sampler level with it (put {nxt[0]} right {sid} wire)" if nxt else ""))
    if save:
        out.append(f"put {save} right {dec} wire")
    if compare:
        out.append(f"# {compare} (Compare) is not placed here: where its wires need the fewest Reroutes, not between "
                   f"the decoder and Save Image")
    out.append("# not placed here: Load CLIP (the column of the text encoders), the size nodes, "
               + ("the scheduler → split chain (in the sources column), " if guider else "")
               + "and everything added to the core")
    return out


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
    notes = {n["id"] for n in cv.s["nodes"] if n.get("type") in NOTE_TYPES}
    for a, b, k, d in narrow(cv):
        tail = ""
        if (a in notes or b in notes) and d < H_GAP / 2:
            # notes.md: a Note goes in free space, not too close to a node (closer than half a column gap: touching it)
            tail = " (a Note too close to a node: align it with the other edge of the node it explains, or write another side)"
        out.append(f"narrow gap ({k} {d}px, min {H_GAP if k == 'horizontal' else V_GAP}): {a} and {b}{tail}")
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
        out.append(f"non-horizontal wire ({l['type']}, input {'below' if dy > 0 else 'above'} the output): {lname(cv, l)}")
    c.count["non-horizontal wires"] = len(tilt)
    return out


def _quick_bad(cv):
    """The Bad forms a move can make at once: a node below one that grows, a Preview or Save above its source, a wire
    going back. (Overlaps are checked by _try_move.)"""
    c = _CheckCtx(cv)
    return set(_chk_below_growing(cv, c)) | set(_chk_output_above_source(cv, c)) | \
        {x for x in _chk_backward(cv, c) if x.startswith("backward wire (cannot be kept")}


def one_move_levels(cv):
    """readable-form.md, Wires, Bad: "a slanted wire that becomes horizontal by moving the node at one end, without
    slanting another wire". Counted exactly: that node moves (with the nodes wired level to it, so no horizontal wire
    is slanted), lands on no node or Reroute. A Save or Preview stepped down below the wire passing on (a staircase),
    the side inputs of SamplerCustomAdvanced, a loader's wires, a node in a sources column and a move that would take a
    sampler along are left out. [(wire, ids that move, dy, node moved first)]."""
    nodes = cv.nodes
    solid = [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute" and m.get("type") not in NOTE_TYPES]
    pairs = horizontal_pairs(cv)
    out = []
    for l in cv.s["links"]:
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if not o or not t or not cv.placed(o) or not cv.placed(t) or "Reroute" in (o.get("type"), t.get("type")):
            continue
        a, b = cv.out_xy(o["id"], l["origin_slot"]), cv.in_xy(t["id"], l["target_input"])
        if a is None or b is None:
            continue
        dy = b[1] - a[1]
        if abs(dy) < 1:
            continue
        if t.get("type") == "SamplerCustomAdvanced" and l["target_input"] in SCA_SIDE_INPUTS:
            continue
        if (is_output_node(cv, t) or any(t["id"] in u for u in cv.s.get("stepped") or [])) and dy > 0:
            continue   # a staircase: the plan stepped it down below the wire passing on
        if cv.is_loader(o):
            continue   # a loader's wires may slant (it stands in its own column or above, readable-form.md "Loaders")
        if (l["origin_id"], l["origin_slot"]) in getattr(cv, "layout_rail_roots", set()):
            continue   # a rail carries it: the rail sets its height
        for start, other, d in ((t["id"], o["id"], -dy), (o["id"], t["id"], dy)):
            # a node stacked with another source of a node it feeds stands in that node's sources column (`inputs`):
            # moving it alone breaks the column
            fed = {m["target_id"] for m in cv.s["links"] if m["origin_id"] == start}
            sib = {m["origin_id"] for m in cv.s["links"] if m["target_id"] in fed and m["origin_id"] != start}
            r = G.rect(nodes[start])
            if any(min(r[2], q[2]) > max(r[0], q[0]) and (0 <= q[1] - r[3] <= V_GAP + 1 or 0 <= r[1] - q[3] <= V_GAP + 1)
                   for q in (G.rect(m) for m in solid if m["id"] in sib)):
                continue
            mv = move_closure(cv, solid, {start}, d, {other}, pairs)
            if mv and not any(is_sampler(nodes[i]) for i in mv) and not lands_on_reroute(cv, mv, d):
                # the sampler fixes the band: it does not move for a side wire; and the move makes no other Bad form
                bad = _quick_bad(cv)
                if _try_move(cv, mv, d, lambda: _quick_bad(cv) <= bad):
                    out.append((l, mv, d, start))
                    break
    return out


def level_what_one_move_levels(cv):
    """Makes those wires horizontal (the canvas knows the move exactly, so it does not hand it to the plan). One at a time, since a move can change the others. Returns what moved."""
    done = []
    for _ in range(60):
        got = one_move_levels(cv)
        if not got:
            break
        l, mv, d, start = got[0]
        cv.translate(sorted(mv), 0, d)
        done.append(f"made horizontal by moving {' '.join(sorted(mv))} {round(abs(d))}px {'down' if d > 0 else 'up'}: {lname(cv, l)}")
    return done


@check_rule("wires one move makes horizontal")
def _chk_one_move_level(cv, c):
    # what is left after the layout made them horizontal (only when a later step moved something)
    return [f"slanted wire that one move makes horizontal: {lname(cv, l)} (write level "
            f"{lname(cv, l).replace(' → ', ' ')}{' move ' + start if start == l['origin_id'] else ''})"
            for l, mv, d, start in one_move_levels(cv)]


# nodes a wire may go back into (one node's width at most): Conditioning Zero Out in place of the negative prompt.
# A wire may also go back from an empty latent (Empty Latent Image and the like) one column into a scheduler (a node that
# outputs SIGMAS), so that the latent stands in the column of the sampler's sources (readable-form "Wires")
BACKWARD_OK_TYPES = {"ConditioningZeroOut"}


def is_empty_latent(n):
    """A node that makes an empty latent: no wired inputs and a LATENT output (Empty Latent Image, Empty SD3 Latent, …)."""
    ins = [i for i in n.get("inputs") or [] if not i.get("widget")]
    outs = [o.get("type") for o in n.get("outputs") or []]
    return (n.get("type") or "").lower().startswith("empty") and "LATENT" in outs and not any(i.get("link") for i in ins)


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
        # a wire may go back one node's width only into Conditioning Zero Out (in place of the negative prompt) or from an
        # empty latent (BACKWARD_OK_TYPES, is_empty_latent). A display node, a value node and the like stand in front of their use
        into_scheduler = "SIGMAS" in [x.get("type") for x in t.get("outputs") or []]
        one = ((t.get("type") in BACKWARD_OK_TYPES or (is_empty_latent(o) and into_scheduler))
               and rt[0] >= ro[0] - H_GAP - (rt[2] - rt[0]))
        gl = group_lower(cv, o["id"], t["id"])
        if one or gl:
            why = f"{t.get('type')} one node's width back" if one else "enters a group one row lower"
            out.append(f"backward wire that may be allowed ({why}): {lname(cv, l)}")
        else:
            back_hard += 1
            out.append(f"backward wire (cannot be kept even with a reason; fix it): {lname(cv, l)}")
    c.count["backward wires that cannot be kept"] = back_hard
    return out


def owns_source(cv, sampler_id, src_id):
    """Whether a source wired straight into this sampler belongs to its column: a source another sampler also takes
    (conditioning shared by two stages) belongs to the leftmost of them, the first stage (an unplaced one counts as
    further right). Excluded from every sampler, it would be in no column."""
    others = [m["target_id"] for m in cv.s["links"] if m["origin_id"] == src_id and m["target_id"] != sampler_id
              and is_sampler(cv.nodes.get(m["target_id"], {}))]
    if not others:
        return True
    # a sampler of an earlier stage (one whose result reaches this sampler) has it, wherever it stands
    if any(sampler_id in downstream(cv.s, o) for o in others):
        return False
    if all(o in downstream(cv.s, sampler_id) for o in others):
        return True
    me = cv.nodes.get(sampler_id)
    if not me or not cv.placed(me):
        return False
    return all(not cv.placed(cv.nodes[o]) or G.rect(me)[0] <= G.rect(cv.nodes[o])[0] for o in others)


@check_rule("right edges of sampler inputs")
def _chk_sampler_inputs(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # the sources wired directly into a sampler are not in one column (right edges)
    for n in cv.s["nodes"]:
        if not cv.placed(n) or not is_sampler(n):
            continue
        srcs = []
        model = None
        for l in cv.s["links"]:
            if l["target_id"] == n["id"]:
                o = nodes.get(l["origin_id"])
                # a previous stage's sampler stands on the eye line, not in this sampler's column of sources (readable-form §1, §4);
                # a source another sampler also takes (conditioning shared by two stages) stands with the first of them
                if (o and cv.placed(o) and o.get("type") not in {"Reroute"} | NOTE_TYPES and not is_sampler(o)
                        and owns_source(cv, n["id"], o["id"]) and o["id"] not in srcs):
                    # the model chain stands on its own row above (readable-form §1): its wire into the sampler may slant
                    if (l.get("type") or "") == "MODEL":
                        model = o["id"]
                    else:
                        srcs.append(o["id"])
        # a source that also feeds another of them (a VAE Encode whose latent goes into Reference Latent as well) stands
        # left of it: its wire into that node would go back from the column (not into Conditioning Zero Out and the like,
        # which a wire may go back into, BACKWARD_OK_TYPES)
        ahead = {i for i in srcs if nodes[i].get("type") not in BACKWARD_OK_TYPES}
        srcs = [i for i in srcs if not (downstream(cv.s, i) & (ahead - {i}))]
        rights = {i: round(G.rect(nodes[i])[2]) for i in srcs}
        if rights and max(rights.values()) - min(rights.values()) > 2:
            out.append(f"{n['id']} {n['type']}: right edges of the sources wired directly into it are not aligned (put them in one column: `inputs {n['id']}`): "
                       + " ".join(rights))
        # its last node still ends at that column's right edge, near the node it feeds, not at a column further left
        # (the skill author)
        # A node that also feeds other nodes (a LoRA's CLIP into CLIP Set Last Layer, left of the column) stays where
        # those wires go forward
        elif (rights and model and model not in rights and abs(round(G.rect(nodes[model])[2]) - max(rights.values())) > 2
              and all(is_sampler(nodes.get(m["target_id"], {})) for m in cv.s["links"] if m["origin_id"] == model)):
            out.append(f"model chain end {model} {nodes[model]['type']}: its right edge ({round(G.rect(nodes[model])[2])}) is not "
                       f"the right edge of the column of {n['id']}'s sources ({max(rights.values())})")
    return out


@check_rule("empty band across everything")
def _chk_empty_band(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # an empty band running across the whole canvas is wider than the minimum gap (space left without a reason)
    # Notes and Reroutes do not count (a band that only rails cross is still empty)
    rs = sorted(G.rect(n) for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in {"Reroute"} | NOTE_TYPES)
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
    # model, clip and vae loaders stacked vertically whose widths differ by less than H_GAP but are not equal
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
                # only the model, clip and vae loaders are given one width (the canvas aligns them); other nodes keep their own
                if 0 <= gap_v <= V_GAP * 2 and 1 <= dw < H_GAP and cv.is_model_loader(a) and cv.is_model_loader(b):
                    out.append(f"stacked loaders differ in width by {round(dw)}px: the canvas gives a column of loaders one width, but a node "
                               f"next to one is in the way of widening it: {a['id']} and {b['id']}")
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
    # loaders stacked in one column go from the top: model, vae, clip (checkpoint loaders are not counted)
    kinds = {}
    for n in cv.s["nodes"]:
        k = single_loader_kind(cv, n) if cv.placed(n) else None
        if k:
            kinds.setdefault(k, []).append(n)
    # compared only within one stacked column: a loader placed by its first user elsewhere is not in the order
    col = stacks(cv)
    for m in kinds.get("MODEL", []):
        for k in ("VAE", "CLIP"):
            for n in kinds.get(k, []):
                if same_stack(cv, m["id"], n["id"], col) and G.rect(n)[1] < G.rect(m)[1]:
                    out.append(f"{k.lower()} loader {n['id']} is above the model loader {m['id']}: "
                               f"loaders stacked in one column go model, vae, clip from the top")
    for v in kinds.get("VAE", []):
        for n in kinds.get("CLIP", []):
            if same_stack(cv, v["id"], n["id"], col) and G.rect(n)[1] < G.rect(v)[1]:
                out.append(f"clip loader {n['id']} is above the vae loader {v['id']}: loaders stacked in one column go "
                           f"model, vae, clip from the top")
    return out


SAMPLER_TYPES = {"KSampler", "KSamplerAdvanced", "SamplerCustom", "SamplerCustomAdvanced"}
DISPLAY_TYPES = {"PreviewImage", "ImageCompare", "Image Comparer (rgthree)", "ImageStitch", "PreviewAny"}


@check_rule("samplers off the eye line")
def _chk_samplers_eye_line(cv, c):
    """readable-form, 4: every stage's sampler stands on the eye line, their top edges at one height. Two samplers where
    one takes the other's result (through any nodes) are stages in a row; parallel stages are not compared."""
    out = []
    sam = [n for n in cv.s["nodes"] if n.get("type") in SAMPLER_TYPES and cv.placed(n)]
    down = {}
    for n in sam:
        seen, todo = set(), [n["id"]]
        while todo:
            x = todo.pop()
            for l in cv.s["links"]:
                if l["origin_id"] == x and l["target_id"] not in seen:
                    seen.add(l["target_id"])
                    todo.append(l["target_id"])
        down[n["id"]] = seen
    for a in sam:
        for b in sam:
            if b["id"] in down[a["id"]]:
                ya, yb = G.rect(a)[1], G.rect(b)[1]
                if abs(ya - yb) >= 1:
                    out.append(f"samplers of stages in a row at different heights: {a['id']} (top {round(ya)}) and "
                               f"{b['id']} (top {round(yb)}); stand both on the eye line and move what enters them")
    return out


def _product_path_to_sampler(cv, nid, seen=frozenset()):
    """The product links (latent, image, video, audio) from a sampler down to nid, or None"""
    if nid in seen:
        return None
    seen = seen | {nid}
    for l in cv.s["links"]:
        if l["target_id"] != nid or (l.get("type") or "") not in MAIN_FLOW_TYPES:
            continue
        o = cv.nodes.get(l["origin_id"], {})
        if is_sampler(o):
            return [l]
        rest = _product_path_to_sampler(cv, l["origin_id"], seen)
        if rest is not None:
            return rest + [l]
    return None


MAIN_FLOW_TYPES = {"LATENT", "IMAGE", "VIDEO", "AUDIO"}


@check_rule("reference wire level, chain wire slanted")
def _chk_reference_level(cv, c):
    """readable-form §3: at a node with two or more wires coming in, a reference wire made horizontal while the node's
    chain wire (what it works on and passes on) slants."""
    out = []
    nodes = c.nodes
    for n in cv.s["nodes"]:
        if not cv.placed(n) or n.get("type") in {"Reroute"} | NOTE_TYPES:
            continue
        ci = chain_input(cv, n)
        if ci is None:
            continue
        into = [l for l in cv.s["links"] if l["target_id"] == n["id"]]
        if len(into) < 2:
            continue
        lc = next((l for l in into if l["target_input"] == ci), None)
        if lc is None or not cv.placed(nodes.get(lc["origin_id"], {})):
            continue
        a, b = cv.out_xy(lc["origin_id"], lc["origin_slot"]), cv.in_xy(n["id"], ci)
        if not (a and b) or abs(a[1] - b[1]) < 1:
            continue
        for l in into:
            if l is lc or not cv.placed(nodes.get(l["origin_id"], {})):
                continue
            ra, rb = cv.out_xy(l["origin_id"], l["origin_slot"]), cv.in_xy(n["id"], l["target_input"])
            if ra and rb and abs(ra[1] - rb[1]) < 1 and ra[0] < rb[0]:
                out.append(f"reference wire level, chain wire slanted: {lname(cv, l)} is horizontal while {lname(cv, lc)} "
                           f"({round(b[1] - a[1])}px) slants; the chain wire is the one to level")
                break
    return out


@check_rule("no wire level into a merging node")
def _chk_merge_level(cv, c):
    """readable-form §3: a node taking two or more wires that it works on together (positive and negative, a video and an
    audio latent) set between their sources so that none of them is horizontal; its chain wire is the one to level. The
    node midway between them is a liking, not the form to write."""
    out = []
    nodes = c.nodes
    for n in cv.s["nodes"]:
        if not cv.placed(n) or n.get("type") in {"Reroute"} | NOTE_TYPES or is_sampler(n):
            continue
        ci = chain_input(cv, n)
        into = [l for l in cv.s["links"] if l["target_id"] == n["id"] and (l.get("type") or "") not in REFERENCE_TYPES
                and cv.placed(nodes.get(l["origin_id"], {}))]
        if ci is None or len(into) < 2:
            continue
        ys = []
        for l in into:
            a, b = cv.out_xy(l["origin_id"], l["origin_slot"]), cv.in_xy(n["id"], l["target_input"])
            if a and b:
                ys.append(abs(a[1] - b[1]))
        lc = next((l for l in into if l["target_input"] == ci), None)
        # a source already level into another node (one encoder feeding two stages) cannot be level into both
        level_elsewhere = lc and any(
            m is not lc and m["origin_id"] == lc["origin_id"] and m["origin_slot"] == lc["origin_slot"]
            and cv.placed(nodes.get(m["target_id"], {})) and cv.in_xy(m["target_id"], m["target_input"])
            and abs(cv.out_xy(m["origin_id"], m["origin_slot"])[1] - cv.in_xy(m["target_id"], m["target_input"])[1]) < 1
            for m in cv.s["links"])
        if lc and not level_elsewhere and len(ys) == len(into) and min(ys) >= 1:
            out.append(f"no wire level into {n['id']} {n['type']}: its {len(into)} wires all slant; "
                       f"write its chain wire level ({lname(cv, lc).replace(' → ', ' ')})")
    return out


@check_rule("main flow off its line")
def _chk_main_flow_line(cv, c):
    """readable-form, 4: the main flow (sampler → VAE Decode → … → save) runs along one band. A wire on the way from the
    last sampler to a save node that is not horizontal. Where the flow branches into two results (audio and video) one
    branch is level; a branch that only goes to a Compare or a Preview is a side use, and the way to the save is the level one."""
    out = []
    nodes = c.nodes

    def reaches_save(nid, seen):
        if nid in seen:
            return False
        seen.add(nid)
        n = nodes.get(nid, {})
        if is_output_node(cv, n) and (n.get("type") or "").startswith(("Save", "VHS_VideoCombine")):
            return True
        return any(reaches_save(m["target_id"], seen) for m in cv.s["links"] if m["origin_id"] == nid)

    for sv in cv.s["nodes"]:
        if not cv.placed(sv) or sv.get("mode", 0) != 0 or not is_output_node(cv, sv) or not (sv.get("type") or "").startswith(("Save", "VHS_VideoCombine")):
            continue
        path = _product_path_to_sampler(cv, sv["id"]) or []
        for l in path:
            o, t = nodes[l["origin_id"]], nodes[l["target_id"]]
            if o.get("type") == "Reroute" or t.get("type") == "Reroute" or not cv.placed(o) or not cv.placed(t):
                continue
            a, b = cv.out_xy(o["id"], l["origin_slot"]), cv.in_xy(t["id"], l["target_input"])
            if not (a and b) or abs(a[1] - b[1]) < 1:
                continue
            sib = [m for m in cv.s["links"] if m["origin_id"] == o["id"] and m is not l and (m.get("type") or "") in MAIN_FLOW_TYPES
                   and reaches_save(m["target_id"], set())]
            if any(cv.placed(nodes[m["target_id"]]) and cv.in_xy(m["target_id"], m["target_input"]) and abs(cv.out_xy(o["id"], m["origin_slot"])[1] - cv.in_xy(m["target_id"], m["target_input"])[1]) < 1 for m in sib):
                continue
            out.append(f"main flow wire not horizontal: {lname(cv, l)} ({round(b[1] - a[1])}px), on the way from sampler "
                       f"{path[0]['origin_id']} to {sv['id']} (write level {lname(cv, l).replace(' → ', ' ')})")
    return out


@check_rule("side-use image rail above")
def _chk_side_rail_above(cv, c):
    """readable-form, 3: a rail for a side use (an image carried only to be shown or stitched for reference) runs below."""
    out = []
    for o, slot, r in rail_starts(cv):
        if rail_type(cv, o["id"], slot) != "IMAGE":
            continue
        ends = [cv.nodes.get(l["target_id"]) or {} for l in ends_through_reroutes(cv, r["id"])]
        if ends and all(m.get("type") in DISPLAY_TYPES for m in ends) and cv.out_xy(r["id"], 0)[1] < cv.out_xy(o["id"], slot)[1] - 1:
            out.append(f"side-use image rail runs above: {o['id']}.{(o.get('outputs') or [])[slot].get('name')} to "
                       f"{' '.join(m.get('id') for m in ends)} (only shown or compared); write it below")
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
    """Why node n grows in ComfyUI ("sampler", "video", "value-sized"), or None."""
    if is_sampler(n):
        return "sampler"
    # a node showing an image does not grow: it draws the image inside the image area its initial size already has
    # (IMAGE_AREA). A video preview does: the legacy canvas fits its height to the video's aspect ratio (core video
    # widgets, Video Helper Suite)
    if image_kind(n.get("type"), cv.oi) and shows_video(n.get("type"), cv.oi):
        return "video"
    if n.get("type") in GROWS_WITH_VALUES:
        return "value-sized"
    return None


# how much a sampler grows while it runs: the frontend adds a preview area at least 220 high below its widgets and
# draws the image shrunk into it, whatever its shape (useImagePreviewWidget.ts, calculateImageGrid). Legacy adds the
# 4px gap between widgets, Nodes 2.0 an 8px margin above it (imagePreviewLayout.ts): the larger one
SAMPLER_GROW = 220 + 8


def grow_room(cv, n):
    """How far below node n a node is hidden when n grows: SAMPLER_GROW for a sampler (its preview area), None for
    a node whose growth follows its content (a video's aspect ratio, the values of Create Bounding Boxes)."""
    return SAMPLER_GROW if grows(cv, n) == "sampler" else None


def in_grow_room(cv, a, rb):
    """Whether rect rb stands right below node a (overlapping it horizontally) within the room a grows into."""
    ra = G.rect(a)
    room = grow_room(cv, a)
    return (min(ra[2], rb[2]) - max(ra[0], rb[0]) > 0 and rb[1] >= ra[3] - 1
            and (room is None or rb[1] - ra[3] < room))


@check_rule("below a node that grows")
def _chk_below_growing(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # the nearest node directly below a node that grows (any horizontal overlap: even a node that sticks out only a little is hidden when it grows)
    body = [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in {"Reroute"} | NOTE_TYPES]
    # a Reroute or a Note below it is hidden too when it grows
    below = body + [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") in {"Reroute"} | NOTE_TYPES]
    for a in body:
        why = grows(cv, a)
        if not why:
            continue
        ra = G.rect(a)
        best = None
        for b in below:
            if b is a:
                continue
            rb = G.rect(b)
            if in_grow_room(cv, a, rb) and (best is None or rb[1] < G.rect(best)[1]):
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
        wide = any((o["id"] in a and t["id"] in b) or (o["id"] in b and t["id"] in a) for a, b in cv.s.get("wide_pairs") or [])
        std = (GAP_WIDE if wide else H_GAP) + frame_pad(cv, [t["id"]], [o["id"]], "right")
        if gap <= std + 1 or min(ro[3], rt[3]) - max(ro[1], rt[1]) <= 0:
            continue
        band = (ro[2] + 1, max(ro[1], rt[1]), rt[0] - 1, min(ro[3], rt[3]))
        if any(rect_overlap(G.rect(m), band) for m in cv.s["nodes"]
               if cv.placed(m) and m["id"] not in (o["id"], t["id"]) and m.get("type") != "Reroute"):
            continue
        seen_pair.add((o["id"], t["id"]))
        out.append(f"wide gap to a wired neighbour ({round(gap)}px, standard gap {round(std)}): {o['id']} → {t['id']}")
    return out


@check_rule("crossings in a gap between columns")
def _chk_gap_crossings(cv, c):
    out = []
    # wires that still cross CROSS_WIDEN times or more inside a gap between columns: the canvas widens such a gap when
    # it can; crossing there means the sources stand in another order than the inputs, or far above or below them
    for x0, x1, n, oid, tid in column_gaps(cv, GAP_WIDE + 1):
        if n >= CROSS_WIDEN:
            out.append(f"wires cross {n} times in the gap between {oid} and {tid} (look at the order and height of the "
                       f"sources: a node centred on its sources column keeps them from crossing)")
    return out


def runs_along_rails(cv, pts, root, ends):
    """Whether a wire drawn along pts runs beside a rail other than root's (closer than RAIL_GAP) past a whole node."""
    spans = [sp for sp in rail_spans(cv) if sp[3] != root]
    along = [(p[0], q[0]) for p, q in zip(pts, pts[1:])
             if q[0] > p[0] and q[0] - p[0] >= abs(q[1] - p[1]) and any(
                 abs((p[1] + q[1]) / 2 - sy) < P["RAIL_GAP"] and min(sx1, q[0]) > max(sx0, p[0]) for sy, sx0, sx1, _ in spans)]
    if not along:
        return False
    a0, a1 = min(x for x, _ in along), max(x for _, x in along)
    return any(cv.placed(m) and m.get("type") not in {"Reroute"} | NOTE_TYPES and m["id"] not in ends
               and a0 <= G.rect(m)[0] and G.rect(m)[2] <= a1 for m in cv.s["nodes"])


def wires_along_rails(cv):
    """Wires carried far the same way as the rails but not on one: a wire running beside a rail (closer than RAIL_GAP)
    past a whole node. readable-form.md, Wires: a value carried far or to several places goes on a rail (the
    model wire left off the rails ran into them). [wire]"""
    spans = rail_spans(cv)
    if not spans:
        return []
    nodes = cv.nodes
    roots = {root for *_, root in spans}
    body = [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") not in {"Reroute"} | NOTE_TYPES]
    out = []
    for l in cv.s["links"]:
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if not o or not t or "Reroute" in (o.get("type"), t.get("type")) or (l["origin_id"], l["origin_slot"]) in roots:
            continue
        pts = cv.wire_pts(l)
        if not pts:
            continue
        along = [(p[0], q[0]) for p, q in zip(pts, pts[1:])
                 if q[0] > p[0] and q[0] - p[0] >= abs(q[1] - p[1]) and any(
                     abs((p[1] + q[1]) / 2 - sy) < P["RAIL_GAP"] and min(sx1, q[0]) > max(sx0, p[0]) for sy, sx0, sx1, _ in spans)]
        if not along:
            continue
        a0, a1 = min(x for x, _ in along), max(x for _, x in along)
        if any(m["id"] not in (o["id"], t["id"]) and a0 <= G.rect(m)[0] and G.rect(m)[2] <= a1 for m in body):
            out.append(l)
    return out


def rail_the_wires_along_rails(cv):
    """Puts each wire found by wires_along_rails on a rail of its own output, with every target of that output (the canvas
    knows what to do, so it does not hand it back to the plan). Returns what it did."""
    done = []
    for _ in range(10):
        ls = wires_along_rails(cv)
        if not ls:
            break
        l = ls[0]
        o = cv.node(l["origin_id"])
        oname = (o.get("outputs") or [])[l["origin_slot"]].get("name")
        targets = [f"{m['target_id']}.{m['target_input']}" for m in cv.s["links"]
                   if m["origin_id"] == o["id"] and m["origin_slot"] == l["origin_slot"]
                   and cv.nodes.get(m["target_id"], {}).get("type") != "Reroute"]
        mark = len(cv.out)
        cv.rail_no_direct = True   # its direct wire is what ran along the rails: every target takes it from the rail
        try:
            do_rail(cv, [f"{o['id']}.{oname}", "to"] + targets)
        except Stop as e:
            done.append(f"wire {lname(cv, l)} runs along the rails; no rail could be drawn for it: {e}")
            break
        finally:
            cv.rail_no_direct = False
        if any(m is l or (m["origin_id"], m["origin_slot"], m["target_id"]) == (l["origin_id"], l["origin_slot"], l["target_id"])
               for m in cv.s["links"]):
            done.append(f"wire {lname(cv, l)} runs along the rails; the rail left it wired directly")
            break
        done.append(f"put on a rail, since it ran along the rails: {lname(cv, l)}")
        done += cv.out[mark:]
        del cv.out[mark:]
    return done


@check_rule("wires running along rails")
def _chk_wire_along_rails(cv, c):
    return [f"wire running along the rails, not on one (carry it on a rail: rail {lname(cv, l).split(' → ')[0]} to "
            f"{l['target_id']}.{l['target_input']}): {lname(cv, l)}" for l in wires_along_rails(cv)]


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
            # the second one branching (it lowers into a target and carries the rail on) is a rail's stop, not a Reroute doing nothing
            if (t and t.get("type") == "Reroute" and cv.placed(t) and abs(G.rect(t)[1] - G.rect(n)[1]) < 1
                    and sum(1 for l in cv.s["links"] if l["origin_id"] == t["id"]) == 1):
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


def _nearest_points(r1, r2):
    """The nearest points of two rectangles (x0, y0, x1, y1): the segment between them crosses the gap between the two"""
    mx = (max(r1[0], r2[0]) + min(r1[2], r2[2])) / 2 if min(r1[2], r2[2]) >= max(r1[0], r2[0]) else None
    my = (max(r1[1], r2[1]) + min(r1[3], r2[3])) / 2 if min(r1[3], r2[3]) >= max(r1[1], r2[1]) else None
    cl = lambda v, lo, hi: min(max(v, lo), hi)
    x1 = mx if mx is not None else cl((r2[0] + r2[2]) / 2, r1[0], r1[2])
    x2 = mx if mx is not None else cl((r1[0] + r1[2]) / 2, r2[0], r2[2])
    y1 = my if my is not None else cl((r2[1] + r2[3]) / 2, r1[1], r1[3])
    y2 = my if my is not None else cl((r1[1] + r1[3]) / 2, r2[1], r2[3])
    return (x1, y1), (x2, y2)


@check_rule("Note away from its node")
def _chk_note_away(cv, c):
    """notes.md, Where to place: a Note on part of the processing stands next to the node it explains (the node its 🔗 line
    names). Bad: other nodes between them."""
    out = []
    placed = [n for n in cv.s["nodes"] if cv.placed(n)]
    for n in placed:
        if n.get("type") not in NOTE_TYPES:
            continue
        text = str((n.get("widgets_values") or [""])[0])
        if "## models" in text:
            continue
        m = re.search(r"🔗\s*([^\n]+)", text)
        if not m:
            continue
        name = m.group(1).strip().strip("*` ")
        tgt = [x for x in placed if x is not n and x.get("type") not in NOTE_TYPES | {"Reroute"}
               and (x.get("title") or display_title(x, cv.oi)) == name]
        best = None
        for t in tgt:
            a, b = _nearest_points(G.rect(n), G.rect(t))
            between = [x["id"] for x in placed if x is not n and x is not t and x.get("type") not in NOTE_TYPES | {"Reroute"}
                       and G._seg_hits_rect(a, b, G.rect(x))]
            if best is None or len(between) < len(best[1]):
                best = (t["id"], between)
        if best and best[1]:
            out.append(f"Note {n['id']} explains {best[0]}, but other nodes stand between them: {' '.join(best[1])} "
                       f"(place it right, left, above or below {best[0]})")
    return out


def note_room_in_frame(cv, n):
    """For a Note placed as part of a group: (how many px it widens the frame, a note line that keeps it inside the frame
    next to a node of the group, or None when there is no such room). None when it widens nothing."""
    g = next((g for g in cv.s["groups"] if g["title"] == n.get("group_note")), None)
    if not g:
        return None
    mem = [cv.nodes[i] for i in g["members"] if i in cv.nodes and cv.placed(cv.nodes[i])
           and cv.nodes[i].get("type") not in NOTE_TYPES]
    if not mem:
        return None
    b = cv.bbox([m["id"] for m in mem])
    frame = (b[0] - PAD_L, b[1] - PAD_T, b[2] + PAD_R, b[3] + PAD_B)
    rn = G.rect(n)
    widen = max(frame[0] - rn[0], rn[2] - frame[2], frame[1] - rn[1], rn[3] - frame[3], 0)
    if widen <= 0:
        return None
    ref = [i for i in cv.unit(n["note_ref"]) if i in cv.nodes] if n.get("note_ref") else []
    cx, cy = ((G.rect(cv.nodes[ref[0]])[0] + G.rect(cv.nodes[ref[0]])[2]) / 2,
              (G.rect(cv.nodes[ref[0]])[1] + G.rect(cv.nodes[ref[0]])[3]) / 2) if ref else (rn[0], rn[1])
    near = sorted(mem, key=lambda m: abs((G.rect(m)[0] + G.rect(m)[2]) / 2 - cx) + abs((G.rect(m)[1] + G.rect(m)[3]) / 2 - cy))
    keep, out_len, hint = list(n["pos"]), len(cv.out), None
    try:
        for m in near:
            for side, align in (("right", "top"), ("right", "bottom"), ("below", "left"), ("below", "right"),
                                ("left", "top"), ("left", "bottom"), ("above", "left"), ("above", "right")):
                try:
                    _put_rel(cv, [n["id"]], side, [m["id"]], align, None)
                except Stop:
                    continue
                r = G.rect(n)
                if (frame[0] <= r[0] and r[2] <= frame[2] and frame[1] <= r[1] and r[3] <= frame[3]
                        and not note_trouble(cv, n["id"])):
                    hint = f"note <its file> {side} {m['id']} {align}"
                    break
            if hint:
                break
    finally:
        n["pos"] = keep
        del cv.out[out_len:]
    return round(widen), hint


@check_rule("Note widening its group")
def _chk_note_widens_group(cv, c):
    """notes.md: a Note on a node inside a group stands inside the frame; it widens the frame only when there is no room
    inside it next to a node of the group."""
    out = []
    for n in cv.s["nodes"]:
        if n.get("type") in NOTE_TYPES and n.get("group_note") and cv.placed(n):
            r = note_room_in_frame(cv, n)
            if r and r[1]:
                out.append(f"Note {n['id']} widens the frame of group \"{n['group_note']}\" by {r[0]}px, but there is room "
                           f"inside it: write {r[1]}")
    return out


def image_only_encoder(cv, n):
    """A node that turns an image into a latent and takes nothing else to work with (VAE Encode, VAE Encode for
    Inpaint): its inputs are an image, a VAE, a mask or values, its outputs latents. A node that also takes conditioning
    (InpaintModelConditioning) is not one."""
    ins = {(i.get("type") or "") for i in n.get("inputs") or [] if not i.get("widget")}
    outs = {(o.get("type") or "") for o in n.get("outputs") or []}
    return "IMAGE" in ins and ins <= {"IMAGE", "VAE", "MASK", "INT", "FLOAT"} and outs == {"LATENT"}


@check_rule("image into VAE Encode slanted")
def _chk_encode_image_level(cv, c):
    """readable-form.md, Other chains: the image wire into a VAE Encode that takes only the image is level (the image
    chain stands on its row); a node that also takes conditioning is placed by its conditioning."""
    out = []
    for n in cv.s["nodes"]:
        if not cv.placed(n) or not image_only_encoder(cv, n):
            continue
        for l in cv.s["links"]:
            if l["target_id"] != n["id"] or (l.get("type") or "") != "IMAGE":
                continue
            o = cv.nodes.get(l["origin_id"])
            if not o or not cv.placed(o):
                continue
            a, b = cv.out_xy(o["id"], l["origin_slot"]), cv.in_xy(n["id"], l["target_input"])
            if a and b and abs(b[1] - a[1]) >= 1:
                out.append(f"image into {n['id']} {n['type']} slants ({round(b[1] - a[1])}px): set the image chain on its "
                           f"row (write level {lname(cv, l).replace(' → ', ' ')})")
    return out


@check_rule("model Note top edge")
def _chk_model_note_top(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # the model Note is top-aligned with the top of the whole workflow (its nodes and Reroutes, and the group frames:
    # the reference all; other Notes do not count)
    cv.update_groups()
    frames = [g["bounding"][1] for g in cv.s["groups"] if g.get("bounding")]
    for m in cv.s["nodes"]:
        if m.get("type") in NOTE_TYPES and cv.placed(m) and "## models" in str((m.get("widgets_values") or [""])[0]):
            tops = [G.rect(o)[1] for o in cv.s["nodes"] if cv.placed(o) and o.get("type") not in NOTE_TYPES] + frames
            if tops and abs(G.rect(m)[1] - min(tops)) >= 1:
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
            # nor when the rail at the output height would run closer than RAIL_GAP to another rail: one running there now,
            # or one from another output of the same node, which could be drawn at its own output height too
            near = [sy for sy, sx0, sx1, root in rail_spans(cv)
                    if root != (n["id"], l["origin_slot"]) and min(sx1, xmax) > max(sx0, a0[0])]
            near += [cv.out_xy(n["id"], m["origin_slot"])[1] for m in cv.s["links"]
                     if m["origin_id"] == n["id"] and m["origin_slot"] != l["origin_slot"]
                     and nodes.get(m["target_id"], {}).get("type") == "Reroute"]
            if not blocked and not any(abs(sy - a0[1]) < P["RAIL_GAP"] for sy in near):
                out.append(f"rail needs no raising Reroute ({r['id']}, {abs(round(ry - a0[1]))}px off) if drawn at the output height: output of {n['id']}"
                           f" (leave the height out of the rail line, or place {n['id']} at the height the rail should run)")
    return out


@check_rule("single values carried with Reroutes")
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
                       and m["id"] not in (n["id"], e["target_id"]) and m.get("type") != "Reroute") \
                    and not runs_along_rails(cv, pts, (n["id"], l["origin_slot"]), {n["id"], e["target_id"]}):
                out.append(f"single value carried with Reroutes, but a direct wire passes behind nothing, so no Reroute is needed: {n['id']} → {e['target_id']}.{e['target_input']}")
    return out


@check_rule("overlapping rails")
def _chk_rail_overlap(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # overlapping rails: rails from different sources overlap horizontally at the same height
    spans = []
    for l, pts in ws:
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        # a rail runs from its source's output to its last Reroute: the level piece out of the source counts as well
        if o and t and t.get("type") == "Reroute" and abs(pts[0][1] - pts[-1][1]) < 1:
            # the source of the rail is its node and output (two outputs of one node are two rails, as in rail_spans)
            root, rslot, seen = l["origin_id"], l["origin_slot"], set()
            while nodes.get(root, {}).get("type") == "Reroute" and root not in seen:
                seen.add(root)
                up = next((x for x in cv.s["links"] if x["target_id"] == root), None)
                if not up:
                    break
                root, rslot = up["origin_id"], up["origin_slot"]
            spans.append((pts[0][1], min(pts[0][0], pts[-1][0]), max(pts[0][0], pts[-1][0]), root, l, rslot))
    told = set()
    for i, a in enumerate(spans):
        for b in spans[i + 1:]:
            if (a[3], a[5]) != (b[3], b[5]) and abs(a[0] - b[0]) < P["RAIL_GAP"] and min(a[2], b[2]) > max(a[1], b[1]):
                # one line for a pair of rails, however many pieces of them run side by side
                pair = frozenset([(a[3], a[5]), (b[3], b[5])])
                if pair in told:
                    continue
                told.add(pair)
                same = f" (outputs {a[5]} and {b[5]})" if a[3] == b[3] else ""
                up, low = (a, b) if a[0] <= b[0] else (b, a)
                need = round(P["RAIL_GAP"] - abs(a[0] - b[0]))
                out.append(f"rails too close or overlapping (vertical gap {abs(a[0] - b[0]):.0f}px, min {P['RAIL_GAP']}): rail of {a[3]} and rail of {b[3]}{same}"
                           + (f" (open the gap: run the lower one {need}px lower, writing its height in its rail line)" if a[3] == b[3] else
                              f" (open the gap: raise {up[3]}, which heads the upper rail, {need}px with the nodes stacked above it, or run the rail of {low[3]} lower)"))
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


def model_loader_of(cv, nid):
    """The node a model chain starts from: up the MODEL inputs (a LoRA, a patch) to the node that takes no model."""
    seen = set()
    while nid not in seen:
        seen.add(nid)
        up = next((l for l in cv.s["links"] if l["target_id"] == nid and (l.get("type") or "") == "MODEL"), None)
        if not up or cv.nodes.get(up["origin_id"], {}).get("type") == "Reroute":
            break
        nid = up["origin_id"]
    return nid


@check_rule("model, vae and clip rails out of order")
def _chk_rail_type_order(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # rails of MODEL, VAE and CLIP from one node or one stacked column run top to bottom in that order where their runs overlap;
    # a conditioning rail runs below the model and vae rails
    spans = {}
    for y, x0, x1, (root, slot) in rail_spans(cv):
        t = rail_type(cv, root, slot)
        if t in RAIL_TYPE_ORDER or t == "CONDITIONING":
            sp = spans.setdefault((root, slot), [t, y, x0, x1])
            sp[2], sp[3] = min(sp[2], x0), max(sp[3], x1)
    items = list(spans.items())
    col = stacks(cv)
    for i, ((ra, sa), (ta, ya, a0, a1)) in enumerate(items):
        for (rb, sb), (tb, yb, b0, b1) in items[i + 1:]:
            if ta == tb or min(a1, b1) <= max(a0, b0):
                continue
            if "CONDITIONING" in (ta, tb):
                other = tb if ta == "CONDITIONING" else ta
                cy, oy = (ya, yb) if ta == "CONDITIONING" else (yb, ya)
                if other in ("MODEL", "VAE") and cy < oy:
                    out.append(f"CONDITIONING rail runs above the {other} rail (conditioning below model and vae): "
                               f"rail of {ra if ta == 'CONDITIONING' else rb} and rail of {rb if ta == 'CONDITIONING' else ra}")
                continue
            # a model rail headed by the model chain (a LoRA after Load Checkpoint) still runs above the vae and clip rails of
            # the loader it starts from
            if "MODEL" in (ta, tb):
                (rm, ym), (ro, yo) = ((ra, ya), (rb, yb)) if ta == "MODEL" else ((rb, yb), (ra, ya))
                base = model_loader_of(cv, rm)
                if base != rm and (base == ro or same_stack(cv, base, ro, col)) and ym > yo:
                    out.append(f"{tb if ta == 'MODEL' else ta} rail runs above the MODEL rail (model, vae, clip from the top): "
                               f"rail of {ro} and rail of {rm} (the model chain from {base})")
                    continue
            # rails from one node's outputs (Load Checkpoint: MODEL, CLIP, VAE) keep the order of its outputs: the loader order
            # is "model, vae, clip from the top" except for the Checkpoint Loader
            if not same_stack(cv, ra, rb, col) or ra == rb:
                continue
            up, down = ((ra, ta), (rb, tb)) if ya < yb else ((rb, tb), (ra, ta))
            if RAIL_TYPE_ORDER.index(up[1]) > RAIL_TYPE_ORDER.index(down[1]):
                out.append(f"{up[1]} rail runs above the {down[1]} rail (model, vae, clip from the top): "
                           f"rail of {up[0]} and rail of {down[0]}")
    # a vae or clip rail above the model when the model is wired directly (no model rail): the model wire into a sampler
    # runs below the rail along its run
    model_rails = [k for k, v in spans.items() if v[0] == "MODEL"]
    if not model_rails:
        for (r, sl), (t, y, x0, x1) in items:
            if t not in ("VAE", "CLIP"):
                continue
            for l in cv.s["links"]:
                if (l.get("type") or "") != "MODEL" or not is_sampler(nodes.get(l["target_id"], {})):
                    continue
                o = nodes.get(l["origin_id"], {})
                if o.get("type") == "Reroute" or not cv.placed(o):
                    continue
                a, b = cv.out_xy(o["id"], l["origin_slot"]), cv.in_xy(l["target_id"], l["target_input"])
                if a and b and min(a[0], b[0]) < x1 and max(a[0], b[0]) > x0 and min(a[1], b[1]) > y:
                    out.append(f"{t} rail runs above the model wire {lname(cv, l)} (model, vae, clip from the top): rail of {r}")
                    break
    return out


def may_say_what(cv, n):
    """Whether node n may be titled "display name: what": a value node (what the value is), or a node loading an image or
    video (what it takes: the image to edit, reference image 1)."""
    return n.get("type") in VALUE_TYPES or image_kind(n.get("type"), cv.oi) == "load"


@check_rule("titles the author gave")
def _chk_author_titles(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # a node keeps ComfyUI's display name; only a value node or a node loading an image may be titled "display name: what"
    for n in cv.s["nodes"]:
        t = n.get("title")
        if not t or n.get("type") in {"Reroute"} | NOTE_TYPES or not cv.placed(n):
            continue
        shown = (cv.oi.get(n.get("type")) or {}).get("display_name") or n.get("type")
        if t == shown or (may_say_what(cv, n) and t.startswith(shown + ":")):
            continue
        out.append(f"title the author gave left on a node (names go back to the display name \"{shown}\"): {n['id']}")
    return out


@check_rule("loaders away from their first user")
def _chk_loader_far(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # a loader not on a rail stands in the column left of its first user: no other column between them
    solid = [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") not in {"Reroute"} | NOTE_TYPES]
    for n in solid:
        if not cv.is_loader(n):
            continue
        users = [cv.nodes[l["target_id"]] for l in cv.s["links"] if l["origin_id"] == n["id"]
                 and l["target_id"] in cv.nodes and cv.placed(cv.nodes[l["target_id"]])]
        if not users or any(u.get("type") == "Reroute" for u in users):
            continue
        first = min(users, key=lambda u: G.rect(u)[0])
        x0, x1 = G.rect(n)[2], G.rect(first)[0]
        between = [m for m in solid if m is not n and m is not first and G.rect(m)[0] >= x0 and G.rect(m)[2] <= x1]
        if between:
            out.append(f"loader away from its first user (other columns between them; place it in the column left of "
                       f"{first['id']}): {n['id']}")
    return out


@check_rule("custom nodes the replacement list turns into core")
def _chk_use_core_left(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # a custom node named in the "Use core" table of replacements.md is still here: replace it (its row may set a condition)
    cells = use_core_cells()
    for n in cv.s["nodes"]:
        if cv.placed(n) and is_custom(n.get("type"), cv.oi) and in_use_core(n.get("type"), cells):
            out.append(f"custom node listed under \"Use core\" in replacements.md is still here (follow its row, or say why "
                       f"its condition does not apply): {n['id']}")
    return out


@check_rule("core nodes the replacement list replaces")
def _chk_core_replaced(cv, c):
    out = []
    # a core node named, with its type in parentheses, in the first column of the "Use core" table of replacements.md
    # (Concatenate Text (StringConcatenate) → Format Text): the replacement does the same and more, so it cannot be kept
    cells = use_core_cells()
    for n in cv.s["nodes"]:
        t = n.get("type") or ""
        if cv.placed(n) and t and not is_custom(t, cv.oi) and any(f"({t})" in cell for cell in cells):
            out.append(f"core node that replacements.md replaces (follow its row in \"Use core\"): {n['id']} {t}")
    return out


def use_core_cells():
    """The first column of each row of the "Use core" table of replacements.md (the custom nodes it names)."""
    p = REFS / "replacements.md"
    if not p.is_file():
        return []
    text = p.read_text(encoding="utf-8")
    sec = text.split("## Use core", 1)[1].split("\n## ", 1)[0] if "## Use core" in text else ""
    return [ln.split("|")[1] for ln in sec.splitlines()
            if ln.startswith("| ") and not ln.startswith("| custom node") and not ln.startswith("|---")]


def in_use_core(typ, cells):
    """Whether node type typ is named in one of the cells (as a whole name, not inside a longer one)."""
    for cell in cells:
        i = cell.find(typ)
        while i >= 0:
            before = cell[i - 1] if i else " "
            after = cell[i + len(typ)] if i + len(typ) < len(cell) else " "
            if not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_"):
                return True
            i = cell.find(typ, i + 1)
    return False


@check_rule("raising Reroutes right of a loader")
def _chk_loader_raise(cv, c):
    out = []
    nodes, ws = c.nodes, c.ws  # noqa: F841
    # a rail from a loader (MODEL, CLIP or VAE) with a raising Reroute just to the right of the loader: the loader can sit
    # at the rail height instead, and then the Reroute is not needed
    starts = rail_starts(cv)
    for o, slot, r in starts:
        # the node heading a rail of model, vae or clip: a loader, or the last node of the model chain
        if rail_type(cv, o["id"], slot) not in RAIL_TYPE_ORDER:
            continue
        if any(o2["id"] == o["id"] and s2 != slot for o2, s2, _ in starts):
            continue   # a loader with several rails (a checkpoint): only one can run at its output height
        ay, ry = cv.out_xy(o["id"], slot)[1], cv.out_xy(r["id"], 0)[1]
        rx, ox1 = G.rect(r)[0], G.rect(o)[2]
        if abs(ay - ry) < 1 or not (ox1 <= rx <= ox1 + H_GAP):
            continue
        out.append(f"raising Reroute right of a loader or the node heading a rail ({r['id']}): place {o['id']} so its output is at the "
                   f"rail height (it heads the rail; leave the rail's height out), and the Reroute is not needed: {o['id']}")
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


def _behind_output_node(cv, line):
    """A wire of what the workflow produces (an image, a latent …) hidden behind a node that only saves or shows."""
    m = re.match(r"wire behind a node: .* \((\w+)\) passes behind (\S+)$", line)
    return bool(m) and m.group(1) in PRODUCT_TYPES and m.group(2) in cv.nodes and is_output_node(cv, cv.nodes[m.group(2)])


def _behind_save_into_output(cv, line):
    """A wire into another output (a Compare beside Save Image) hidden behind a node that saves: one of them steps down
    (examples.md, the outputs). Behind a Preview the wire on to the next node is common in hand-made layouts, so that
    one weighs less."""
    if not _behind_output_node(cv, line):
        return False
    m = re.match(r"wire behind a node: \S+ → (\S+?)\.\S+ \(\w+\) passes behind (\S+)$", line)
    t, b = (cv.nodes.get(m.group(1)), cv.nodes.get(m.group(2))) if m else (None, None)
    return bool(t and b) and is_output_node(cv, t) and "Preview" not in (b.get("type") or "")


REFERENCE_TYPES = {"MODEL", "CLIP", "VAE", "CLIP_VISION", "CONTROL_NET", "UPSCALE_MODEL", "STYLE_MODEL", "GLIGEN",
                   "MODEL_PATCH", "INTERP_MODEL", "BBOX_DETECTOR", "SEGM_DETECTOR", "SAM_MODEL", "NOISE", "SAMPLER",
                   "SIGMAS", "GUIDER", "INT", "FLOAT", "STRING", "BOOLEAN", "MASK"}


def chain_input(cv, n):
    """The input a node takes in, works on and passes on (its chain wire, glossary): its first wired input of a type it
    also outputs (the image into a resize). None for a sampler: its form (readable-form §1) says which of its wires is level."""
    if is_sampler(n):
        return None
    outs = {o.get("type") for o in n.get("outputs") or []}
    ins = [i for i in n.get("inputs") or [] if any(l["target_id"] == n["id"] and l["target_input"] == i["name"] for l in cv.s["links"])]
    # only an input of the type the node also outputs (image → image, latent → latent, mask → mask): a node that turns
    # what it takes into something else (a text encoder taking an image and a CLIP) has no single chain wire, and the
    # hand-made layouts keep its CLIP wire level (15 of 35 would break otherwise)
    def passes_on(t):
        kinds = set((t or "").split(","))
        return bool(kinds & outs) or ("*" in outs and not kinds <= REFERENCE_TYPES - {"MASK"})
    same = [i for i in ins if passes_on(i.get("type")) and i.get("type") not in REFERENCE_TYPES - {"MASK"}]
    pick = same[0] if same else None
    return pick["name"] if pick else None


def _chain_link_line(cv, line):
    """Whether the wire of a 'one move makes horizontal' line is a link of a chain: its source sends out only this wire
    and its target takes in only this wire. Hand-made layouts leave other wires slanted on purpose (dev measure: 219 such
    wires in 34 of 35 hand-made layouts, 12 chain links)."""
    m = re.search(r": (\S+?)\.\S+ → (\S+?)\.(\S+?) \(write level", line)
    if not m:
        return False
    o, t, tin = m.group(1), m.group(2), m.group(3)
    # the only wire between two nodes in a line (the skill author's examples: sampler → VAE Decode, Load Image → Resize → VAE
    # Encode). Counting every chain input as well makes the skill author's layouts break it 49 times (ltx conditioning chains
    # they keep slanted); the reference-against-chain form has its own check
    return (sum(1 for l in cv.s["links"] if l["origin_id"] == o) == 1
            and sum(1 for l in cv.s["links"] if l["target_id"] == t) == 1)


@check_rule("positive into the sampler slants")
def _chk_positive_level(cv, c):
    """readable-form §1: the positive conditioning enters a KSampler horizontally, from the column just left of it (the
    text encoder, Apply ControlNet). What else stands there (a stage's upscale and VAE Encode) goes to the row below."""
    out = []
    for n in cv.s["nodes"]:
        if not cv.placed(n) or not is_sampler(n):
            continue
        lp = next((l for l in cv.s["links"] if l["target_id"] == n["id"] and l["target_input"] == "positive"), None)
        o = c.nodes.get(lp["origin_id"]) if lp else None
        if not o or not cv.placed(o) or o.get("type") in {"Reroute"} | NOTE_TYPES or is_sampler(o):
            continue
        x0 = G.rect(n)[0]
        if not (x0 - GAP_WIDE - 1 <= G.rect(o)[2] <= x0 - H_GAP / 3):
            continue
        a, b = cv.out_xy(o["id"], lp["origin_slot"]), cv.in_xy(n["id"], "positive")
        # its top on the sampler's top is the same form: the output stands one slot (20px) above the input
        if a and b and abs(a[1] - b[1]) > 20 and abs(G.rect(o)[1] - G.rect(n)[1]) > 20:
            out.append(f"positive into the sampler slants: {lname(cv, lp)} ({round(b[1] - a[1])}px); place {o['id']} so it "
                       f"enters {n['id']} level, and what else stands in that column (upscale, VAE Encode) on the row below")
    return out


def _stage_entry(cv, sid, nodes):
    """The wire carrying the previous stage's result into the chain that ends in sampler sid's latent (the image out of a
    VAE Decode or a latent out of another sampler, then upscale, resize, VAE Encode), and the latent wire into sid. None
    when the chain does not start at another stage (an i2i's Load Image, an empty latent)."""
    into = lambda nid: [l for l in cv.s["links"] if l["target_id"] == nid]
    lat = next((l for l in into(sid) if l.get("type") == "LATENT"), None)
    if lat is None:
        return None
    cur, seen = lat["origin_id"], set()
    if is_sampler(nodes.get(cur) or {}):
        return None   # the latent comes straight from the previous stage's sampler: it is the result wire itself
    while cur not in seen and len(seen) < 12:
        seen.add(cur)
        n = nodes.get(cur) or {}
        ci = chain_input(cv, n)
        lk = next((l for l in into(cur) if l["target_input"] == ci), None) if ci else None
        if lk is None:
            # a node turning one flow into another (VAE Encode: image into latent) passes it on as well
            lk = next((l for l in into(cur) if l.get("type") in MAIN_FLOW_TYPES), None)
        if lk is None:
            return None
        o = nodes.get(lk["origin_id"]) or {}
        outs = {x.get("type") for x in o.get("outputs") or []}
        ins = {x.get("type") for x in o.get("inputs") or [] if x.get("link") is not None}
        if is_sampler(o) or ("LATENT" in ins and "IMAGE" in outs and not is_sampler(o)):
            return lk, lat
        cur = lk["origin_id"]
    return None


@check_rule("result wire level, latent into the sampler slants")
def _chk_stage_entry_level(cv, c):
    """readable-form §1: a stage taking the previous stage's result: its own chain stands with its sampler (the latent
    level, or the top edges aligned), and the wire from the previous stage into that chain is the one that slants. A
    notice: which of the two is the skill author's choice either way."""
    out = []
    for n in cv.s["nodes"]:
        # a sampler taking its sources in one column (SamplerCustomAdvanced: the latent last) has its own level wire
        if not cv.placed(n) or not is_sampler(n) or not any(i.get("name") == "positive" for i in n.get("inputs") or []):
            continue
        e = _stage_entry(cv, n["id"], c.nodes)
        if not e:
            continue
        lk, lat = e
        lp = next((l for l in cv.s["links"] if l["target_id"] == n["id"] and l["target_input"] == "positive"), None)
        pa, pb = (cv.out_xy(lp["origin_id"], lp["origin_slot"]), cv.in_xy(n["id"], "positive")) if lp else (None, None)
        if pa and pb and abs(pa[1] - pb[1]) <= 20:
            continue   # the conditioning enters level: the chain stands on the row below and its latent slants
        if not all(cv.placed(c.nodes.get(x["origin_id"], {})) for x in (lk, lat)):
            continue
        a, b = cv.out_xy(lat["origin_id"], lat["origin_slot"]), cv.in_xy(n["id"], lat["target_input"])
        ra, rb = cv.out_xy(lk["origin_id"], lk["origin_slot"]), cv.in_xy(lk["target_id"], lk["target_input"])
        if not (a and b and ra and rb) or abs(a[1] - b[1]) < 1 or abs(ra[1] - rb[1]) >= 1:
            continue
        # the chain standing with the sampler, top edges aligned, is as good (the conditioning does not enter level either)
        if abs(G.rect(c.nodes[lat["origin_id"]])[1] - G.rect(n)[1]) < 1:
            continue
        out.append(f"result wire level, latent into the sampler slants: {lname(cv, lk)} is horizontal while "
                   f"{lname(cv, lat)} ({round(b[1] - a[1])}px) slants; move the stage's chain to {n['id']} (its latent "
                   f"level, or its top on {n['id']}'s top), and let the wire from the previous stage slant")
    return out


@check_rule("one-line text into a text area")
def _chk_one_line_text(cv, c):
    out = []
    # a text handed out from a one-line String into a widget written in a text area (a prompt): the value node is the same
    # kind of input as where the text goes, Text (Multiline)
    for n in cv.s["nodes"]:
        if n.get("type") != "PrimitiveString" or not cv.placed(n):
            continue
        for l in cv.s["links"]:
            if l["origin_id"] != n["id"]:
                continue
            t = c.nodes.get(l["target_id"]) or {}
            inp = next((i for i in t.get("inputs") or [] if i.get("name") == l["target_input"]), None)
            info = cv.oi.get(t.get("type"))
            spec = CS.widget_spec(info, (inp.get("widget") or {}).get("name") or l["target_input"]) if inp and info else None
            if spec and len(spec) > 1 and isinstance(spec[1], dict) and spec[1].get("multiline"):
                out.append(f"one-line text into a text area: {n['id']} String → {t['id']}.{l['target_input']}"
                           f" (make {n['id']} a Text (Multiline), PrimitiveStringMultiline)")
                break
    return out


# check lines that match a Bad line of the rules exactly, with no Fine or Undecided around them: they cannot be kept.
# {check name: which of its lines}
HARD_CHECKS = {
    "overlaps": lambda cv, l: l.startswith("overlap"),
    "below a node that grows": lambda cv, l: "is directly below" in l,
    "Preview or Save above its source": lambda cv, l: True,
    # a wire may go back only into the few nodes the rules name (Conditioning Zero Out and the like); demoting this to a
    # notice let the agent keep backward wires
    "backward wires": lambda cv, l: l.startswith("backward wire (cannot be kept"),
    "group titles, overhangs and overlaps": lambda cv, l: l.startswith(("wire over the title", "node over the title", "groups overlap")),
    "model, vae and clip rails out of order": lambda cv, l: True,
    "rail order and loader order": lambda cv, l: True,
    "overlapping rails": lambda cv, l: True,
    "one-line text into a text area": lambda cv, l: True,
    "narrow gaps": lambda cv, l: "a Note too close to a node" in l,
    "positive into the sampler slants": lambda cv, l: True,
    # a Reroute lifting a rail off its source's output height where a line at that height passes behind nothing (the skill
    # author lays rails at their output height; a second eye line for a loop is the one exception they make)
    "rails that can run at the output height": lambda cv, l: True,
    "Reroutes doing nothing": lambda cv, l: l.startswith(("Reroute doing nothing", "Reroute connected to nothing")),
    "consecutive Reroutes": lambda cv, l: True,
    "wires behind nodes": _behind_save_into_output,
    # a wire one move makes horizontal is said as one the rules call Bad, so the plan is changed (the canvas does not
    # move it by itself after the plan). Only the links of a chain (see _chain_link_line)
    "wires one move makes horizontal": _chain_link_line,
    "samplers off the eye line": lambda cv, l: True,
    "side-use image rail above": lambda cv, l: True,
    # a rail lifted by a Reroute right after the node heading it
    "raising Reroutes right of a loader": lambda cv, l: True,
    "loaders away from their first user": lambda cv, l: True,
    # a loader stacked above the model loader; clip above vae is not one (the skill author's
    # Qwen layouts stack clip above vae, 10 of 10)
    "loader order": lambda cv, l: "above the model loader" in l,
    "right edges of sampler inputs": lambda cv, l: not l.startswith("model chain end"),
    "model Note top edge": lambda cv, l: True,
    "Note away from its node": lambda cv, l: True,
    "Note widening its group": lambda cv, l: True,
    "reference wire level, chain wire slanted": lambda cv, l: True,
    # the sampler → decode → save wires. The skill author's LTX layouts set the decode midway between the video and
    # audio latents: a liking, not the form to write
    "main flow off its line": lambda cv, l: True,
    "core nodes the replacement list replaces": lambda cv, l: True,
    "custom nodes the replacement list turns into core": lambda cv, l: True,
}

# forms the rules call Bad that weigh less: reported after the others, to fix when it costs nothing else
SOFT_CHECKS = {
    # a node set midway between two wires it merges is a liking of the skill author's (their LTX layouts), so it weighs
    # less; the form to write levels the chain wire
    "no wire level into a merging node": lambda cv, l: True,
    "image into VAE Encode slanted": lambda cv, l: True,
    "right edges of sampler inputs": lambda cv, l: l.startswith("model chain end"),
    "single values carried with Reroutes": lambda cv, l: True,
    "wires behind nodes": lambda cv, l: _behind_output_node(cv, l) and not _behind_save_into_output(cv, l),
    "titles the author gave": lambda cv, l: True,
    "wires one move makes horizontal": lambda cv, l: not _chain_link_line(cv, l),
}


def checked(cv):
    """Every check line with the name of its check, and the counts."""
    c = _CheckCtx(cv)
    out = []
    for name, fn in CHECKS:
        out += [(name, ln) for ln in fn(cv, c)]
    return out, c.count


def full_check(cv):
    """All checks: the message lines from applying the rules top to bottom, and the counts for the first line."""
    lines, count = checked(cv)
    hard = [ln for name, ln in lines if name in HARD_CHECKS and HARD_CHECKS[name](cv, ln)]
    count["cannot be kept"] = len(hard)
    return [ln for _, ln in lines], count


def hard_problems(cv):
    """The check lines that cannot be kept (HARD_CHECKS)."""
    lines, _ = checked(cv)
    return [ln for name, ln in lines if name in HARD_CHECKS and HARD_CHECKS[name](cv, ln)]


def soft_problems(cv):
    """The check lines of Bad forms that weigh less (SOFT_CHECKS)."""
    lines, _ = checked(cv)
    return [ln for name, ln in lines if name in SOFT_CHECKS and SOFT_CHECKS[name](cv, ln)]


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
    """One hash of every canvas's current state (what the report page is made from)."""
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


def do_finish(work, args=()):
    """Deletes the working folder once every canvas is exported and reviewed (every review row answered) and the report page is up to date.
    Only files the canvas knows are deleted, one by one: what it wrote, the plan and Note files it was given (if they are
    inside the working folder) and understanding.md. Anything else is left, and then the folder is left too.
    With the environment variable CANVAS_KEEP_WORK=1 nothing is deleted; the files are only listed.
    finish fast: the user asked for it fast, so the review and the report page are not asked for."""
    fast = list(args) == ["fast"]
    if args and not fast:
        raise Stop("finish, or finish fast (when the user asked for it fast: no review, no report page)")
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
    for name in ([] if fast else work.names()):
        rev = Canvas(work, name).s.get("review")
        if rev is None:
            missing.append(f"canvas {name} has no review: review the exported workflow (references/review.md) and "
                           f"`use {name}`, `review $W/review_{name}.md`")
        elif isinstance(exported.get(name), dict) and rev.get("hash") != exported[name].get("hash"):
            missing.append(f"canvas {name} changed after its review was registered: export it, answer the rows again and "
                           f"`review $W/review_{name}.md`")
        else:
            no_answer = [r["rule"] for r in rev["rows"] if not r["answer"]]
            if no_answer:
                missing.append(f"canvas {name}: {len(no_answer)} review rows have no answer (write \"fixed\" or \"left: <reason>\" "
                               f"in the last column and `review` the file again): {'; '.join(no_answer[:5])}")
    rep_ = work.cfg.get("replayed")
    if fast:
        pass
    elif not isinstance(rep_, dict) or rep_.get("canvases") != canvases_hash(work):
        missing.append("the report page is older than the canvases: `report <html> <language code>`")
    elif _file_hash(rep_.get("path")) != rep_.get("file"):
        missing.append(f"the report page is missing or was changed ({rep_.get('path')}): `report <html> <language code>`")
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
    given = [Path(os.path.abspath(p)) for p in work.cfg.get("consumed") or []]
    files += given
    files = [f for f in dict.fromkeys(files) if inside(f) and (f.is_file() or f.is_symlink())]
    # plan and Note files the canvas was given from outside the working folder: not deleted, only named
    outside = [str(f) for f in dict.fromkeys(given) if not inside(f) and f.exists()]
    note_outside = ([f"these files the canvas was given are outside the working folder, so they were not deleted "
                     f"(next time, put working files inside it): {', '.join(outside)}"] if outside else [])
    dirs = [Path(root) / "canvas" / f"{n}.hist" for n in work.names()] + [Path(root) / "canvas", Path(root)]
    if os.environ.get("CANVAS_KEEP_WORK") == "1":
        return (["finished. Everything is exported and the report page is up to date. CANVAS_KEEP_WORK=1 is set, so the working "
                 "folder is kept as it is (this is expected; go on to the report). Without it, finish would delete:"]
                + [f"  {os.path.relpath(f, root)}" for f in files] + note_outside)
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
                    f"(it is the current directory?): remove it from outside"] + note_outside
        return [f"deleted {len(files)} files. The canvas does not know these, so they and the working folder were left: "
                + ", ".join(left) + f". If you made them, delete those files one by one, then remove the empty folder with "
                f"`rmdir {root}` (do not delete the folder with its contents)"] + note_outside
    return [f"deleted the working folder {root} ({len(files)} files)"] + note_outside


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
    allw = {w for w in words_of(t.split("|")[0].replace("(", " ").replace(")", " ")) if df.get(w, 0)}
    allw -= {"easy", "rgthree", "pysssss", "crystools", "vhs", "comfy", "any", "kj"}   # names of custom node authors and packs
    mine = {w for w in allw if df[w] <= 30}
    if not mine:
        # every word is common (Load, Video): the core nodes that have all of them, those with the fewest other words first
        hits = sorted((len(ws - allw), k, d) for k, (ws, d) in _CORE_WORDS.items() if allw and allw <= ws)
        return [f"{k} ({d})" for _, k, d in hits][:6]
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


def downstream(flat, nid):
    seen, stack = set(), [nid]
    while stack:
        x = stack.pop()
        for l in flat["links"]:
            if l["origin_id"] == x and l["target_id"] not in seen:
                seen.add(l["target_id"])
                stack.append(l["target_id"])
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


def gap_opt(opt):
    """The spacing a plan may ask for: none (the standard gap) or `gap wide` (between columns with many wires)."""
    if "gap" not in opt:
        return None
    if HAND_PLACING_FOR_TESTS:
        return "wide" if opt["gap"] == "wide" else num(opt["gap"], "gap")
    raise Stop(f"there is no gap {opt['gap']}: the canvas keeps every gap, and widens the gap between two columns "
               f"where wires cross in it")


def plan_groups(cv):
    """Group title -> member ids. In a layout, from every group line of the plan (known before the lines that place),
    so a gap can count a group frame that is drawn later."""
    out = {}
    for title, toks in (getattr(cv, "plan_group_lines", None) or [(g["title"], g["members"]) for g in cv.s["groups"]]):
        ids = set()
        for t in toks:
            if t in cv.s["blocks"]:
                ids |= set(cv.s["blocks"][t])
            elif t in cv.nodes:
                ids.add(t)
        out[title] = {i for i in ids if cv.nodes.get(i, {}).get("type") not in NOTE_TYPES}   # a frame holds nodes, not Notes
    # but a Note on a node of the group is part of it: placed with the group, inside its frame
    for n in cv.s["nodes"]:
        if n.get("group_note") in out:
            out[n["group_note"]].add(n["id"])
    return out


def groups_of(cv, ids):
    return {t for t, m in plan_groups(cv).items() if m & set(ids)}


def frame_pad(cv, ids, ref_ids, how):
    """The extra gap where a group frame lies between ref and the unit, so the gap is kept frame to frame (or frame to node)."""
    gu = groups_of(cv, ids)
    gr = set() if isinstance(ref_ids, AllIds) else groups_of(cv, ref_ids)   # the box of all already takes in the frames
    ref_side, unit_side = bool(gr - gu), bool(gu - gr)
    near, far = {"right": (PAD_R, PAD_L), "left": (PAD_L, PAD_R), "below": (PAD_B, PAD_T), "above": (PAD_T, PAD_B)}[how]
    return (near if ref_side else 0) + (far if unit_side else 0)


def without(ref_ids, ids):
    """all, leaving out the unit being placed (other references are kept as they are)."""
    return AllIds(i for i in ref_ids if i not in set(ids)) if isinstance(ref_ids, AllIds) else ref_ids


def ref_box(cv, ref_ids):
    if not isinstance(ref_ids, AllIds):
        return cv.bbox(ref_ids)
    if not ref_ids:
        raise Stop("all: nothing is placed yet")
    b = list(cv.bbox(ref_ids))
    cv.update_groups()
    for g in cv.s["groups"]:
        if g.get("bounding"):
            x, y, w, h = g["bounding"]
            b = [min(b[0], x), min(b[1], y), max(b[2], x + w), max(b[3], y + h)]
    return b


def wide_note(cv, ids, ref_ids):
    k = sum(1 for l in cv.s["links"] if (l["origin_id"] in ref_ids and l["target_id"] in ids)
            or (l["origin_id"] in ids and l["target_id"] in ref_ids))
    cv.wide_gaps = getattr(cv, "wide_gaps", []) + [f"gap wide between {ref_ids[0]} and {ids[0]}: {k} wires"]
    cv.s.setdefault("wide_pairs", []).append([list(ref_ids), list(ids)])
    cv.out.append(f"gap wide between {ref_ids[0]} and {ids[0]} ({GAP_WIDE}px): {k} wires between them")


def side_gap(cv, ids, how, ref_ids, gap):
    if how in ("below", "above") and gap == "wide":
        raise Stop("gap wide is only between columns (right, left)")
    base = (GAP_WIDE if gap == "wide" else H_GAP if gap is None else gap) if how in ("right", "left") \
        else (V_GAP if gap is None else gap)
    if gap == "wide":
        wide_note(cv, ids, ref_ids)
    return base + frame_pad(cv, ids, ref_ids, how)


def keep_frames_apart(cv, ids, how, ref_ids):
    """When the unit and the reference stand in different groups, the unit's group frame keeps a gap from the reference's
    group frame, not only from the reference node: if a frame would reach into the other, every placed node of the
    unit's group moves along that side together (a frame is moved whole, never node by node)."""
    if isinstance(ref_ids, AllIds):
        return
    pg = plan_groups(cv)
    gu = {t for t, m in pg.items() if m & set(ids)}
    gr = {t for t, m in pg.items() if m & set(ref_ids)}
    rgroups, ugroups = gr - gu, gu - gr
    if not rgroups and not ugroups:
        return
    placed = lambda i: i in cv.nodes and cv.placed(cv.nodes[i])
    ref_set = [i for i in set(ref_ids) | {i for t in rgroups for i in pg[t]} if placed(i)]
    # the whole group moves only when the unit is that whole group (its title, or a block holding all its placed nodes);
    # a single member placed while its group is being built keeps its own distance and moves alone
    whole = all({i for i in pg[t] if placed(i)} <= set(ids) for t in ugroups)
    unit_set = [i for i in (set(ids) | {i for t in ugroups for i in pg[t]} if whole else set(ids)) if placed(i)]
    if not ref_set or not unit_set or set(ref_set) & set(unit_set):
        return
    rb, ub = list(cv.bbox(ref_set)), list(cv.bbox(unit_set))
    if rgroups:
        rb = [rb[0] - PAD_L, rb[1] - PAD_T, rb[2] + PAD_R, rb[3] + PAD_B]
    if ugroups:
        ub = [ub[0] - PAD_L, ub[1] - PAD_T, ub[2] + PAD_R, ub[3] + PAD_B]
    dx = dy = 0
    if how == "right":
        dx = max(0, rb[2] + H_GAP - ub[0])
    elif how == "left":
        dx = -max(0, ub[2] - (rb[0] - H_GAP))
    elif how == "below":
        dy = max(0, rb[3] + V_GAP - ub[1])
    elif how == "above":
        dy = -max(0, ub[3] - (rb[1] - V_GAP))
    if dx or dy:
        cv.translate(unit_set, dx, dy)
        cv.out.append(f"moved {round(abs(dx or dy))}px {how} with its group, so the frames stand apart: {' '.join(sorted(unit_set))}")


def put_rel(cv, ids, how, ref_ids, align, gap):
    _put_rel(cv, ids, how, ref_ids, align, gap)
    keep_frames_apart(cv, ids, how, ref_ids)


def _put_rel(cv, ids, how, ref_ids, align, gap):
    w, h = cv.unit_size(ids)
    rb = ref_box(cv, ref_ids)
    if how in ("right", "left"):
        g = side_gap(cv, ids, how, ref_ids, gap)
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
        elif align == "step":
            # a staircase: the unit stands just below the wire leaving ref at its output height, so that wire passes above
            # it; as far below as a rail keeps from the nodes under it (LANE_CLEAR_BELOW)
            l = cv.link_between(ref_ids, ids)
            src = l["origin_id"] if l and l["origin_id"] in ref_ids else ref_ids[0]
            slot = l["origin_slot"] if l and l["origin_id"] in ref_ids else 0
            y0 = cv.out_xy(src, slot)[1] + LANE_CLEAR_BELOW
        else:
            raise Stop(f"unknown alignment {align} for {how} (top bottom middle wire step)")
        cv.place_unit(ids, x0, y0)
        if align == "step":
            cv.s.setdefault("stepped", []).append(list(ids))
            cv.out.append(f"stepped down below the wire from {ref_ids[0]}: {' '.join(ids)}")
        if align == "wire":
            l = cv.link_between(ref_ids, ids)
            if not l:
                raise Stop("no wire between the reference and the unit (wire makes a wire horizontal)")
            dy = cv.level_dy(l, set(ids))
            cv.translate(ids, 0, dy)
            cv.out.append(f"made horizontal: {lname(cv, l)}")
    elif how in ("below", "above"):
        g = side_gap(cv, ids, how, ref_ids, gap)
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


def column_gaps(cv, upto=None):
    """The gaps between wired columns: for each wire, the span from its source's right edge to its target's left edge
    (narrower than GAP_WIDE), with the number of times the wires passing through that span cross inside it.
    [(x0, x1, crossings, source id, target id)], left to right."""
    wires = []
    for l in cv.s["links"]:
        o, t = cv.nodes.get(l["origin_id"]), cv.nodes.get(l["target_id"])
        if not o or not t or "Reroute" in (o.get("type"), t.get("type")) or not cv.placed(o) or not cv.placed(t):
            continue
        a, b = cv.out_xy(o["id"], l["origin_slot"]), cv.in_xy(t["id"], l["target_input"])
        if a is None or b is None or b[0] <= a[0]:
            continue
        wires.append((l, a, b, G.spline(a, b, steps=48)))
    seen = {}
    for l, a, b, _ in sorted(wires, key=lambda w: (w[1][0], w[2][0])):
        # the gap between the two nodes' edges (the hand-made layouts were measured edge to edge; measuring between the
        # slots left a widened gap 19px short of GAP_WIDE)
        x0, x1 = G.rect(cv.nodes[l["origin_id"]])[2], G.rect(cv.nodes[l["target_id"]])[0]
        if not 0 < x1 - x0 < (upto or GAP_WIDE - 1):
            continue
        # the gap is the space between the two nodes: from the higher top to the lower bottom of the source and the target.
        # A crossing in the same span of x but in another row is not in this gap
        ro, rt = G.rect(cv.nodes[l["origin_id"]]), G.rect(cv.nodes[l["target_id"]])
        y0, y1 = min(ro[1], rt[1]), max(ro[3], rt[3])
        inside = [(m, [q for q in pts if x0 - 1 <= q[0] <= x1 + 1 and y0 <= q[1] <= y1])
                  for m, ma, mb, pts in wires if ma[0] <= x0 + 1 and mb[0] >= x1 - 1]
        n = 0
        for i in range(len(inside)):
            for j in range(i + 1, len(inside)):
                (la, pa), (lb, pb) = inside[i], inside[j]
                if (la["origin_id"], la["origin_slot"]) == (lb["origin_id"], lb["origin_slot"]) or \
                   (la["target_id"], la["target_input"]) == (lb["target_id"], lb["target_input"]):
                    continue
                if len(pa) > 1 and len(pb) > 1 and poly_cross(pa, pb):
                    n += 1
        # one entry per span of x: the rows sharing it are counted each in their own band, and the gap is the one with
        # the most crossings (counting only the first wire found missed a crossed gap below a row ending at it)
        key = (round(x0), round(x1))
        if key not in seen or n > seen[key][2]:
            seen[key] = (x0, x1, n, l["origin_id"], l["target_id"])
    return list(seen.values())


def shift_local(cv, cut, band, dx, extra=(), keep=()):
    """Moves by dx (right when dx > 0, left when dx < 0) the nodes on that side of the line x = cut that stand in the band
    of heights (y0, y1), and the nodes that move must take along so nothing overlaps and no wire goes back: a node a
    moved one would land on, a node on the far side that a moved one would pass. Other rows stay (a gap in one process is
    not made in another). Returns the moved ids."""
    placed = [m for m in cv.s["nodes"] if cv.placed(m)]
    by = {m["id"]: m for m in placed}
    side = (lambda r: r[0] >= cut) if dx > 0 else (lambda r: r[2] <= cut)
    keep = set(keep)
    mv = {m["id"] for m in placed if side(G.rect(m)) and G.rect(m)[3] > band[0] and G.rect(m)[1] < band[1]} - keep
    mv |= {i for i in extra if i in by}
    for _ in range(len(placed) + 1):
        add = set()
        for i in mv:
            r = G.rect(by[i])
            moved = (r[0] + dx, r[1], r[2] + dx, r[3])
            for m in placed:
                if m["id"] in mv or not side(G.rect(m)):
                    continue
                q = G.rect(m)
                if min(moved[2] + H_GAP, q[2] + H_GAP) > max(moved[0], q[0]) and min(moved[3], q[3]) > max(moved[1], q[1]):
                    add.add(m["id"])
        for l in cv.s["links"]:
            o, t = l["origin_id"], l["target_id"]
            if o not in by or t not in by:
                continue
            if dx > 0 and o in mv and t not in mv and side(G.rect(by[t])) and G.rect(by[t])[0] < G.rect(by[o])[2] + dx:
                add.add(t)
            if dx < 0 and t in mv and o not in mv and side(G.rect(by[o])) and G.rect(by[o])[2] > G.rect(by[t])[0] + dx:
                add.add(o)
        add -= keep
        if not add:
            break
        mv |= add
    cv.translate(sorted(mv), dx, 0)
    return mv


def shift_right_local(cv, cut, band, dx, extra=()):
    return shift_local(cv, cut, band, dx, extra)


def widen_crossed_gaps(cv):
    """Widens to GAP_WIDE each gap between wired columns where wires cross CROSS_WIDEN times or more (the skill
    author's hand-made layouts): every node right of a line through the gap that crosses no node moves
    right. A gap with no such line is left as it is (the check names it). Returns what was widened."""
    done = []
    for _ in range(100):
        cand = None
        for x0, x1, n, oid, tid in column_gaps(cv):
            if n < CROSS_WIDEN:
                continue
            # the line through the gap crosses no node at any height: moving only some rows would break the columns the
            # plan aligned. A gap with no such line is left as it is and the check names it.
            # A node the line crosses whose right edge is aligned with a node right of the line (a model row ending at the
            # opened column's right edge) moves with that column (the skill author)
            body = [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") not in NOTE_TYPES]

            def riders(x):
                hit = [m for m in body if G.rect(m)[0] < x < G.rect(m)[2]]
                right = [G.rect(q)[2] for q in body if G.rect(q)[0] >= x]
                if all(any(abs(G.rect(m)[2] - e) <= 2 for e in right) for m in hit):
                    return [m["id"] for m in hit]
                return None

            cut = next((x for x in (x1 - 0.5, (x0 + x1) / 2, x0 + 0.5) if riders(x) is not None), None)
            if cut is not None:
                cand = (x0, x1, n, oid, tid, cut, riders(cut))
                break
        if cand is None:
            return done
        x0, x1, n, oid, tid, cut, extra = cand
        dx = GAP_WIDE - (x1 - x0)
        # everything right of the line moves, at every height: moving only the rows the wires pass through broke the
        # columns the plan aligned below or above them (the skill author)
        shift_right_local(cv, cut, (-float("inf"), float("inf")), dx, extra=extra)
        for l in cv.s["links"]:
            o, t = cv.nodes.get(l["origin_id"]), cv.nodes.get(l["target_id"])
            if o and t and cv.placed(o) and cv.placed(t) and G.rect(o)[2] <= cut + 1 and G.rect(t)[0] >= cut:
                cv.s.setdefault("wide_pairs", []).append([[o["id"]], [t["id"]]])
        done.append(f"gap widened between {oid} and {tid} ({GAP_WIDE}px): wires cross {n} times in it")
    return done


def separate_groups(cv):
    """Groups whose frames overlap side by side (a frame takes in the Reroutes lowered into it, and those can stand in
    the column left of the group): the group further right, and everything right of it, moves right until the frames are
    a column gap apart (the skill author). Only along a line that cuts no node; otherwise the check names
    the overlap. Returns what was moved."""
    done = []
    for _ in range(50):
        cv.update_groups()
        gs = [g for g in cv.s["groups"] if g.get("bounding")]
        hit = None
        for a in gs:
            for b in gs:
                ax, ay, aw, ah = a["bounding"]
                bx, by, bw, bh = b["bounding"]
                if a is not b and ax <= bx and rect_overlap((ax, ay, ax + aw, ay + ah), (bx, by, bx + bw, by + bh)):
                    hit = (a, b)
                    break
            if hit:
                break
        if not hit:
            return done
        a, b = hit
        # the group on the left (upstream) moves left, with the rows of its frame and its own members; the group on the
        # right (downstream) stays
        mem = [cv.nodes[i] for i in a["members"] if i in cv.nodes and cv.placed(cv.nodes[i])]
        body = [m for m in mem if m.get("type") != "Reroute"] or mem
        cut = max(G.rect(m)[2] for m in body) + 0.5
        if any(G.rect(m)[0] < cut < G.rect(m)[2] for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute"):
            return done
        dx = -(a["bounding"][0] + a["bounding"][2] + H_GAP - b["bounding"][0])
        ax, ay, aw, ah = a["bounding"]
        shift_local(cv, cut, (ay, ay + ah), dx, extra=[m["id"] for m in mem],
                    keep=[i for i in b["members"] if i not in a["members"]])
        done.append(f"group \"{a['title']}\" moved {round(-dx)}px left: its frame overlapped \"{b['title']}\"")
    return done


def _group_intrusions(cv):
    """Group frames that overlap, and nodes standing inside the frame of a group they are not in (what a move must not add)."""
    cv.update_groups()
    out = set()
    gs = [g for g in cv.s["groups"] if g.get("bounding")]
    fr = {g["title"]: (g["bounding"][0], g["bounding"][1], g["bounding"][0] + g["bounding"][2], g["bounding"][1] + g["bounding"][3])
          for g in gs}
    for i, a in enumerate(gs):
        for b in gs[i + 1:]:
            if rect_overlap(fr[a["title"]], fr[b["title"]]):
                out.add(("groups", a["title"], b["title"]))
    for g in gs:
        for m in cv.s["nodes"]:
            if cv.placed(m) and m.get("type") not in {"Reroute"} | NOTE_TYPES and m["id"] not in g["members"] \
                    and rect_overlap(G.rect(m), fr[g["title"]]):
                out.add(("inside", g["title"], m["id"]))
    return out


def upstream_unit(cv, nid):
    """nid and the nodes upstream of it that feed nothing else: a chain that moves as one."""
    unit, todo = {nid}, [nid]
    while todo:
        cur = todo.pop()
        for l in cv.s["links"]:
            if l["target_id"] != cur or l["origin_id"] in unit:
                continue
            o = cv.nodes.get(l["origin_id"])
            if not o or not cv.placed(o) or o.get("type") in {"Reroute"} | NOTE_TYPES:
                continue
            if all(m["target_id"] in unit for m in cv.s["links"] if m["origin_id"] == o["id"]):
                unit.add(o["id"])
                todo.append(o["id"])
    return unit


def close_gaps(cv):
    """Closes the gaps the plan left: a node whose wires all go right, standing further from the nearest node it feeds
    than the gap there should be (H_GAP, GAP_WIDE where the canvas widened it, plus a group frame between), moves right
    to that gap together with the chain upstream that feeds only it (the skill author: upstream comes to downstream).
    From the right, so a row closes up from its end. A move is made only when the chain lands on no
    node, makes no other Bad form, and makes no group frame overlap another or take in a node of another group. Not a node
    whose output a rail of this layout carries (the rail places it). Returns what moved."""
    done = []
    roots = getattr(cv, "layout_rail_roots", set())
    tried = set()
    for _ in range(300):
        moved = False
        body = sorted((n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in {"Reroute"} | NOTE_TYPES),
                      key=lambda n: -G.rect(n)[2])
        for n in body:
            outs = [l for l in cv.s["links"] if l["origin_id"] == n["id"]]
            if not outs or any((l["origin_id"], l["origin_slot"]) in roots for l in outs):
                continue
            tg = [cv.nodes[l["target_id"]] for l in outs if l["target_id"] in cv.nodes]
            if not tg or any(not cv.placed(t) or t.get("type") in {"Reroute"} | NOTE_TYPES for t in tg):
                continue
            rn = G.rect(n)
            if any(G.rect(t)[0] < rn[2] for t in tg):
                continue
            near = min(tg, key=lambda t: G.rect(t)[0])
            wide = any((n["id"] in a and near["id"] in b) for a, b in cv.s.get("wide_pairs") or [])
            gap = (GAP_WIDE if wide else H_GAP) + frame_pad(cv, [near["id"]], [n["id"]], "right")
            dx = round(G.rect(near)[0] - rn[2] - gap)
            if dx < 1 or (n["id"], dx) in tried:
                continue
            tried.add((n["id"], dx))
            unit = upstream_unit(cv, n["id"])
            # a chain fed from outside it (by a node that also feeds something else) stays: moving it would tear the
            # chain and open the gap behind it instead
            if any(l["target_id"] in unit and l["origin_id"] not in unit and cv.nodes.get(l["origin_id"], {}).get("type") != "Reroute"
                   for l in cv.s["links"]):
                continue
            # as far as the gap allows, or up to the first node in the way (a column gap before it)
            rects = [G.rect(cv.nodes[i]) for i in unit]
            for m in cv.s["nodes"]:
                if m["id"] in unit or not cv.placed(m) or m.get("type") in NOTE_TYPES:
                    continue
                q = G.rect(m)
                for r in rects:
                    if q[0] >= r[2] and min(q[3], r[3] + V_GAP) > max(q[1], r[1] - V_GAP):
                        dx = min(dx, round(q[0] - H_GAP - r[2]))
            if dx < 1:
                continue
            moved_rects = [(r[0] + dx, r[1], r[2] + dx, r[3]) for r in rects]
            if any(m["id"] not in unit and cv.placed(m) and m.get("type") not in NOTE_TYPES and rect_overlap(
                    (r[0] - H_GAP + 1, r[1] - V_GAP + 1, r[2] + H_GAP - 1, r[3] + V_GAP - 1), G.rect(m))
                   for r in moved_rects for m in cv.s["nodes"]):
                continue
            bad, intr = _quick_bad(cv), _group_intrusions(cv)
            if not _try_move_x(cv, unit, dx, lambda: _quick_bad(cv) <= bad and _group_intrusions(cv) <= intr):
                continue
            cv.translate(sorted(unit), dx, 0)
            done.append(f"moved {round(dx)}px right towards {near['id']} which it feeds: {' '.join(sorted(unit))}")
            moved = True
            break
        if not moved:
            break
    cv.update_groups()
    return done


def _try_move_x(cv, ids, dx, ok):
    cv.translate(sorted(ids), dx, 0)
    try:
        return ok()
    finally:
        cv.translate(sorted(ids), -dx, 0)


def clear_group_frames(cv):
    """A node that is not in a group but stands inside the right part of its frame (the frame grew when the canvas moved
    its members): it moves right out of the frame, a column gap past it, with what stands right of it at its heights.
    Returns what moved."""
    done = []
    for _ in range(20):
        cv.update_groups()
        hit = None
        for g in cv.s["groups"]:
            if not g.get("bounding"):
                continue
            x, y, w, h = g["bounding"]
            for m in cv.s["nodes"]:
                if not cv.placed(m) or m["id"] in g["members"] or m.get("type") in {"Reroute"} | NOTE_TYPES:
                    continue
                r = G.rect(m)
                if rect_overlap(r, (x, y, x + w, y + h)) and r[0] > x + w / 2:
                    hit = (g, m, x + w + H_GAP - r[0])
                    break
            if hit:
                break
        if not hit:
            return done
        g, m, dx = hit
        r = G.rect(m)
        shift_local(cv, r[0] - 0.5, (r[1], r[3]), dx, keep=list(g["members"]))
        done.append(f"{m['id']} moved {round(dx)}px right out of the frame of group \"{g['title']}\"")
    return done


def clear_below_growing(cv):
    """A node that grows (a sampler, a node showing a video) with a node or Reroute right below it: the growing node moves
    left until nothing below it overlaps it horizontally (readable-form.md, Nodes, Fine). Only when it
    then stands at least a column gap right of every node wired into it (no wire goes back) and clear of every other
    node; otherwise the check hands it to the plan. Returns what moved."""
    done = []
    for _ in range(40):
        moved = False
        below_all = [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in NOTE_TYPES]
        for a in [n for n in below_all if n.get("type") != "Reroute" and grows(cv, n)]:
            ra = G.rect(a)
            under = [b for b in below_all if b is not a and in_grow_room(cv, a, G.rect(b))]
            if not under:
                continue
            b = min(under, key=lambda b: G.rect(b)[1])
            dx = G.rect(b)[0] - ra[2] - 1
            new = (ra[0] + dx, ra[1], ra[2] + dx, ra[3])
            srcs = [cv.nodes[l["origin_id"]] for l in cv.s["links"] if l["target_id"] == a["id"] and l["origin_id"] in cv.nodes]
            if any(G.rect(o)[2] + (H_GAP if o.get("type") != "Reroute" else 0) > new[0] for o in srcs):
                continue
            if any(m is not a and cv.placed(m) and rect_overlap(new, G.rect(m)) for m in cv.s["nodes"]):
                continue
            room = grow_room(cv, a)
            if any(m is not a and cv.placed(m) and m.get("type") not in NOTE_TYPES and G.rect(m)[1] >= new[3] - 1
                   and (room is None or G.rect(m)[1] - new[3] < room)
                   and min(new[2], G.rect(m)[2]) - max(new[0], G.rect(m)[0]) > 0 for m in cv.s["nodes"]):
                continue   # it would only come over another node below
            cv.translate([a["id"]], dx, 0)
            done.append(f"{a['id']} moved {round(-dx)}px left: it grows, and {b['id']} stood right below it")
            moved = True
            break
        if not moved:
            break
    return done


def put_two(cv, ids, h_how, h_ref, v_how, v_ref, gap):
    """Beside one reference and below or above another: x from the first, y from the second."""
    put_rel(cv, ids, h_how, h_ref, "top", gap)
    x = cv.bbox(ids)[0]
    put_rel(cv, ids, v_how, v_ref, "left", None)
    cv.place_unit(ids, x, cv.bbox(ids)[1])


ALIGNS = {"top", "bottom", "middle", "wire", "step", "left", "right", "center"}


# usage returned instead of a Python error when arguments are missing (command: (minimum count, usage))
MIN_ARGS = {
    "use": (1, "use <name>"), "title": (1, "title <id> <title>"), "unblock": (1, "unblock <name>"),
    "ungroup": (1, "ungroup <title>"), "width": (1, "width <id> <id> ..."), "rm": (1, "rm <id> ..."),
    "mode": (2, "mode <on|bypass|mute> <id> ..."), "color": (2, "color <color> <id> ..."),
    "layout": (1, "layout <plan file>"),
}


def plan_lines(path, seen=()):
    """The lines of a plan file, with `include <file>` replaced by that file's lines (canvases of the same form share
    one plan for what they have in common). An included line carries where it came from as a comment, so a stop names
    it. Returns (lines, every file read)."""
    f = need_file(path, "plan file")
    key = os.path.abspath(f)
    if key in seen:
        raise Stop(f"include: {path} includes itself (through {' → '.join(Path(x).name for x in seen)})")
    out, files = [], [str(f)]
    for k, raw in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        toks = shlex.split(raw, comments=True)
        if toks[:1] != ["include"]:
            out.append(raw if not seen else f"{raw.split('#', 1)[0].rstrip()}  # {f.name}:{k}")
            continue
        if len(toks) != 2:
            raise Stop(f"{f.name} line {k}: include <plan file>")
        # a path as written, or next to the file that includes it
        inc = toks[1] if Path(toks[1]).is_file() else str(f.parent / toks[1])
        sub, sub_files = plan_lines(inc, tuple(seen) + (key,))
        out += sub
        files += sub_files
    return out, files


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
        return do_finish(work, args)
    if cmd == "core":
        if not args:
            raise Stop("core <sampler id>")
        return core_plan(work.current(), args[0])
    if cmd == "guide":
        return guide(work.current())
    if cmd == "order":
        names = work.names()
        tab = {}
        for a in args:
            if "/" in a:
                tab[a.split("/", 1)[1]] = a.split("/", 1)[0]
        args = [a.split("/", 1)[1] if "/" in a else a for a in args]
        unknown = [a for a in args if a not in names]
        if unknown:
            raise Stop(f"no canvas {' '.join(unknown)} (canvases: {' '.join(names)})")
        missing = [n for n in names if n not in args]
        if missing or len(set(args)) != len(args):
            raise Stop(f"name every canvas once (missing: {' '.join(missing) or 'none'})")
        work.cfg["order"] = list(args)
        work.cfg["tab_group"] = tab
        work.save_cfg()
        return [f"report page order: {' '.join(args)}"]
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
            cv.s.pop("walk", None)   # the walkthrough of the other canvas; this one gets its own
            cv.s.pop("review", None)   # so is its review
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
            for raw in plan_lines(args[0])[0]:
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
        # the lines of a Bad form carry the rule they break, as in layout's reply; the other notices follow as they are
        hard, soft = hard_problems(cv), soft_problems(cv)
        rest = [ln for ln in lines if ln not in hard and ln not in soft]
        out = [head]
        if hard:
            out += violations(hard)
        if soft:
            out += violations(soft, "weigh less: fix them when it breaks nothing above")
        if rest:
            out += [f"notices ({len(rest)}):"] + ["  " + ln for ln in rest]
        return out if len(out) > 1 else [head, "no problems"]
    if cmd == "render":
        if not args:
            raise Stop("render <png> [export]")
        wf, ids = cv.workflow()
        # `render <png> export` draws the ids of the exported workflow (for the review), otherwise the canvas ids
        names = None if args[1:2] == ["export"] else {v: k for k, v in ids.items()}
        Path(args[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(args[0]).write_bytes(RD.render(wf, cv.oi, names=names).png())
        work.consume(args[0])   # finish deletes it with the working folder
        work.save_cfg()   # the numbers drawn stay those of later exports
        if names is None:
            # the workflow the reviewer sees: a review row answered "fixed" must come with a change since then. Only the
            # first picture until the review is registered counts (a picture drawn again after fixing is not a new review)
            work.cfg.setdefault("review_render", {}).setdefault(cv.name, workflow_hash(wf))
            work.save_cfg()
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

    if cmd in ("report", "replay"):   # replay: the command's old name
        if not args:
            raise Stop("report <html> [<language code>]")
        Path(args[0]).parent.mkdir(parents=True, exist_ok=True)
        Path(args[0]).write_text(report_page(work, args[1] if len(args) > 1 else "en"), encoding="utf-8")
        work.cfg["replayed"] = {"path": os.path.abspath(args[0]), "canvases": canvases_hash(work),
                                "file": hashlib.sha256(Path(args[0]).read_bytes()).hexdigest()}
        work.save_cfg()
        return [f"report page: {args[0]}"] + [ln for name in work.names() for ln in walk_gaps(Canvas(work, name))]

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
    """After a layout, note or walk that succeeded: remember the files it used (the plan and its Note files, a Note file,
    the walkthrough file); finish deletes them."""
    if cmd in ("note", "walk", "review"):
        work.consume(args[0])
    elif cmd == "layout":
        lines, files = plan_lines(args[0])
        for f in files:
            work.consume(f)
        for raw in lines:
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
        _walk_forget(cv, nid)
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
        if isinstance(ids, AllIds):
            raise Stop("all is only a reference")
        rest = list(args[3:])
        second = None
        sides = ("right", "left", "below", "above")
        for k, a in enumerate(rest):
            if a in sides and k + 1 < len(rest) and (rest[k + 1] == "all" or rest[k + 1] in cv.nodes or rest[k + 1] in cv.s["blocks"]):
                second = (a, rest[k + 1])
                rest = rest[:k] + rest[k + 2:]
                break
        rest, opt = parse_opts(rest, flags=ALIGNS, keyed=("gap",))
        if rest:
            raise Stop(f"unreadable arguments: {' '.join(rest)}")
        al = next((a for a in ALIGNS if a in opt), None)
        ref = without(cv.unit(args[2], allow_all=True), ids)
        gap = gap_opt(opt)
        if second:
            hz = {"right", "left"}
            if (args[1] in hz) == (second[0] in hz):
                raise Stop(f"two references need one side (right or left) and one height (below or above): "
                           f"put <unit> right|left <A> below|above <B>")
            if al:
                raise Stop(f"with two references the place comes from them; {al} is not used")
            h_how, h_ref, v_how, v_ref = (args[1], ref, second[0], without(cv.unit(second[1], allow_all=True), ids)) if args[1] in hz \
                else (second[0], without(cv.unit(second[1], allow_all=True), ids), args[1], ref)
            put_two(cv, ids, h_how, h_ref, v_how, v_ref, gap)
            return
        if al is None and args[1] in ("right", "left") and cv.link_between(ref, ids):
            al = "wire"   # side by side and wired: the wire is made horizontal, not the tops aligned
        put_rel(cv, ids, args[1], ref, al, gap)


def _op_row(cv, work, args):
    pos, opt = parse_opts(args, flags={"top", "wire"}, keyed=("right", "gap"))
    units = [cv.unit(t) for t in pos]
    if not units:
        raise Stop("row <unit> ...")
    al = "top" if "top" in opt else "wire"
    gap = gap_opt(opt)
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
    gap = gap_opt(opt)
    if gap == "wide":
        raise Stop("gap wide is only between columns (put right, row, inputs)")
    if "below" in opt:
        put_rel(cv, units[0], "below", cv.unit(opt["below"]), al, gap)
    elif not all(cv.placed(cv.node(i)) for i in units[0]):
        cv.place_unit(units[0], 0, 0)
    for prev, u in zip(units, units[1:]):
        put_rel(cv, u, "below", prev, al, gap)


def _op_align(cv, work, args):
    if len(args) < 3:
        raise Stop("align <top|bottom|left|right|middle|center> <unit> ...")
    how, units = args[0], [cv.unit(args[1], allow_all=True)] + [cv.unit(t) for t in args[2:]]
    units[0] = without(units[0], [i for u in units[1:] for i in u])
    rb = ref_box(cv, units[0])
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
        raise Stop("inputs <id>")
    tid = args[0]
    opt = parse_opts(args[1:], keyed=("gap",))[1]
    gap = gap_opt(opt)
    t = cv.node(tid)
    if not cv.placed(t):
        raise Stop(cv.unplaced_msg(tid))
    order = [i["name"] for i in t.get("inputs") or []]
    srcs = []
    for name in order:
        l = next((l for l in cv.s["links"] if l["target_id"] == tid and l["target_input"] == name), None)
        # a previous stage's sampler stays on the eye line: it is not moved into this column (readable-form §1, §4)
        if (l and l["origin_id"] not in srcs and cv.node(l["origin_id"]).get("type") not in {"Reroute"} | NOTE_TYPES
                and not is_sampler(cv.node(l["origin_id"]))):
            srcs.append(l["origin_id"])
    # as the check reads the column: a source another sampler also takes (conditioning shared by two stages) stays with
    # the first of them (the leftmost placed sampler that takes it)
    srcs = [i for i in srcs if owns_source(cv, tid, i)]
    if not srcs:
        raise Stop(f"{tid} has no sources wired directly into it")
    if gap == "wide":
        wide_note(cv, srcs, [tid])
    gap = (GAP_WIDE if gap == "wide" else H_GAP if gap is None else gap) + frame_pad(cv, srcs, [tid], "left")
    rt = G.rect(t)
    right = rt[0] - gap
    y = 0
    for sid in srcs:
        n = cv.node(sid)
        h = n["size"][1] + G.title_height(n)
        cv.set_rect_xy(sid, right - n["size"][0], y)
        y += h + V_GAP
    # column height: the node stays (it stands on the eye line) and the column moves to it. The source that carries the
    # conditioning enters at the node's height: for KSampler etc. the positive wire is horizontal, for
    # SamplerCustomAdvanced the guider's wire is (the sampler was centred on its column, and the column
    # had nowhere to go). A node that takes neither is centred on the column
    pos_l = next((l for l in cv.s["links"] if l["target_id"] == tid and l.get("type") == "CONDITIONING"
                  and l["target_input"] in ("positive", "conditioning") and l["origin_id"] in srcs), None)
    gd_l = next((l for l in cv.s["links"] if l["target_id"] == tid and l.get("type") == "GUIDER"
                 and l["origin_id"] in srcs), None)
    if pos_l:
        dy = cv.in_xy(tid, pos_l["target_input"])[1] - cv.out_xy(pos_l["origin_id"], pos_l["origin_slot"])[1]
        how = "positive wire horizontal"
    elif gd_l:
        dy = cv.in_xy(tid, gd_l["target_input"])[1] - cv.out_xy(gd_l["origin_id"], gd_l["origin_slot"])[1]
        how = "guider wire horizontal"
    else:
        col = cv.bbox(srcs)
        dy = (rt[1] + rt[3]) / 2 - (col[1] + col[3]) / 2
        how = "node centred on the column"
    cv.translate(srcs, 0, dy)
    cv.out.append(f"sources of {tid} in one right-aligned column on its left ({how}): {' '.join(srcs)}")


def _op_shape(cv, work, args):
    pos, opt = parse_opts(args, keyed=("right", "below", "left", "above"))
    if len(pos) != 2:
        raise Stop("shape <laid-out block> <block to lay out> [right|below|left|above <ref>]")
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
        ref = cv.unit(opt[where], allow_all=True)
        rb = ref_box(cv, ref)
        w, h = ab[2] - ab[0], ab[3] - ab[1]
        gh = H_GAP + frame_pad(cv, b_ids, ref, where) if where in ("right", "left") else H_GAP
        gv = V_GAP + frame_pad(cv, b_ids, ref, where) if where in ("below", "above") else V_GAP
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
    dy = cv.level_dy(l, set(ids))
    # the nodes wired level to the moving ones, and those they would land on, move along, so no horizontal wire slants
    # and nothing overlaps (move_closure); the other end of the wire stays
    solid = [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute" and m.get("type") not in NOTE_TYPES]
    other = {oid} if tid in ids else {tid}
    mv = (move_closure(cv, solid, set(ids), dy, other - set(ids), horizontal_pairs(cv))
          if LEVEL_CARRIES and not other <= set(ids) else None)
    moved = sorted(mv) if mv else ids
    cv.translate(moved, 0, dy)
    if mv and set(mv) - set(ids):
        cv.out.append(f"moved along to keep their wires level: {' '.join(sorted(set(mv) - set(ids)))}")


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
        n.pop("loader_shift", None)
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
    pos = args[:3]
    if len(pos) < 3:
        raise Stop("note <md file> <right|left|below|above> <ref> ... (placed as put places)")
    if not Path(pos[0]).is_file():
        raise Stop(f"no Note file {pos[0]}")
    text = Path(pos[0]).read_text(encoding="utf-8")
    # every Note has the default width (a Note as narrow as the node it sat on grew tall and was pushed into gaps)
    w = NT.NOTE_W
    h = max(NT.NOTE_MIN[1], NT.note_height(text, w))
    nid = Path(pos[0]).stem if Path(pos[0]).stem not in cv.nodes else f"{Path(pos[0]).stem}_{cv.s['next_id']}"
    cv.s["next_id"] += 1
    n = {"id": nid, "type": "MarkdownNote", "mode": 0, "inputs": [], "outputs": [], "properties": {},
         "widgets_values": [text], "pos": None, "size": [w, round(h)], "canvas_note": True}
    if getattr(cv, "note_group", None):
        n["group_note"] = cv.note_group
        n["note_ref"] = args[2] if len(args) > 2 else None
    # the model Note is purple and every other Note yellow (notes.md). There is only one right answer, so the canvas sets it
    model_note = re.search(r"^#+\s*models\s*$", text, re.M)
    n["color"], n["bgcolor"] = COLORS["purple" if model_note else "yellow"]
    cv.s["nodes"].append(n)
    where = list(args[1:])
    if where and where[0] == "below" and len(where) > 1 and where[1] != "all":
        try:
            ref = cv.unit(where[1])
        except Stop:
            ref = []
        grow = [i for i in ref if cv.placed(cv.node(i)) and grows(cv, cv.node(i))]
        if grow and NOTE_SEARCH:
            # a node that grows (a sampler, a node showing a video) would cover a Note below it: the Note goes above
            where[0] = "above"
            cv.out.append(f"Note {nid}: {grow[0]} grows when run, so the Note goes above it, not below")
    # where the plan wrote (NOTE_SEARCH off): what it lands on is reported, and the plan chooses another side. With
    # NOTE_SEARCH the canvas would try the other sides of the same node and keep the first that is clear
    ref = where[1] if len(where) > 1 else None
    tries = [where]
    if NOTE_SEARCH and ref and ref != "all" and where[0] in ("right", "left", "above", "below"):
        try:
            unit = cv.unit(ref)
        except Stop:
            unit = []
        grow = any(cv.placed(cv.node(i)) and grows(cv, cv.node(i)) for i in unit)
        tries += [[side, ref] for side in ("right", "left", "above", "below")
                  if side != where[0] and not (side == "below" and grow)]
    best = None
    for k, wh in enumerate(tries):
        n["pos"] = None
        try:
            _op_put(cv, work, [nid] + wh)
        except Stop:
            if k == 0:
                raise
            continue
        trouble = note_trouble(cv, nid)
        # a Note on top of a node is worse than one too close to it
        weight = lambda tr: sum(10 if x.startswith("overlap") else 1 for x in tr)
        if best is None or weight(trouble) < weight(best[1]):
            best = (wh, trouble, list(n["pos"]))
        if not trouble:
            break
    wh, trouble, n["pos"] = best
    if wh is not where:
        cv.out.append(f"Note {nid}: placed {' '.join(wh)} ({' '.join(where[:2])} was not clear)"
                      + (f"; still: {'; '.join(trouble)}" if trouble else ""))
    elif trouble:
        cv.out.append(f"Note {nid}: placed {' '.join(where[:2])} as written; not clear there: {'; '.join(trouble)}")
    cv.out.append(f"Note {nid}: width {w}, height {round(h)}")


def note_trouble(cv, nid):
    """What is wrong with where a Note stands: it overlaps something, stands too close to a node, a wire passes behind
    it, it stands right below a node that grows, or other nodes stand between it and the node it explains."""
    only = {nid}
    return ([f"overlap {a} {b}" for a, b in overlaps(cv, only)] + [f"narrow {a} {b}" for a, b, *_ in narrow(cv, only)]
            + [f"wire behind {lname(cv, l)}" for l, _ in hidden_wires(cv, only) if _ == nid]
            + [x for x in _chk_below_growing(cv, _CheckCtx(cv)) if nid in x.split()]
            + [x for x in _chk_note_away(cv, None) if x.startswith(f"Note {nid} ")])


def _review_cells(line):
    """The four cells of a review row. A rule may contain "|" (a quoted move such as `put … right|left`): the last three
    cells are nodes, what to change and the answer, and everything before them is the rule. "\\|" is a "|" inside a cell."""
    parts = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())]
    if parts and parts[0] == "":
        parts = parts[1:]
    if parts and parts[-1] == "":
        parts = parts[:-1]
    if len(parts) > 4:
        # an empty cell before the answer (the answer written after the reviewer's empty answer cell): drop it
        parts = [c for c in parts[:-1] if c] + parts[-1:]
    if len(parts) < 4:
        return None
    return ["|".join(parts[:-3])] + parts[-3:]


REFS = Path(__file__).resolve().parent.parent / "references"
REVIEW_RULE_FILES = ("readable-form.md", "content.md", "notes.md")


def _op_review(cv, work, args):
    """Registers the review of the exported workflow (references/review.md): a table | rule | nodes | what to change | answer |,
    "No findings.", or "Not reviewed: <why>", and the reviewer's last line "Checked: …".
    The node numbers are those of the exported workflow; they are shown with the canvas ids."""
    if not args:
        raise Stop("review <md file>")
    if not Path(args[0]).is_file():
        raise Stop(f"no review file {args[0]}")
    text = Path(args[0]).read_text(encoding="utf-8")
    lines = [ln.strip() for ln in text.splitlines()]
    table = [ln for ln in lines if ln.startswith("|")]
    if table and "rule" not in table[0].lower():
        raise Stop(f"the table has no header row: start it with | rule | nodes | what to change | answer | (got \"{table[0]}\")")
    body = [ln for ln in table[1:] if not re.fullmatch(r"\|[\s:|-]*\|?", ln)]   # after the header, without the |---| line
    not_reviewed = next((ln for ln in lines if ln.lower().startswith("not reviewed:")), None)
    no_findings = any(ln.lower() == "no findings." for ln in lines)
    checked = next((ln for ln in lines if ln.lower().startswith("checked:")), None)
    if not body and not not_reviewed and not no_findings:
        raise Stop("the review has no rows. Write the table | rule | nodes | what to change | answer |, the line "
                   "\"No findings.\" when the reviewer found nothing, or \"Not reviewed: <why>\" when no other agent could review it")
    wf, ids = cv.workflow()
    now = workflow_hash(wf)
    to_canvas = {str(v): k for k, v in ids.items()}
    rows, unknown = [], []
    for ln in body:
        cells = _review_cells(ln)
        if cells is None:
            raise Stop(f"\"{ln}\": a row has four cells (rule | nodes | what to change | answer)")
        answer = cells[3]
        if answer and not (answer.lower().startswith("fixed") or answer.lower().startswith("left:")):
            raise Stop(f"\"{answer}\": an answer starts with \"fixed\" or \"left: <why>\"")
        nums = re.findall(r"[\w:~]+", cells[1])
        unknown += [t for t in nums if t not in to_canvas]
        rows.append({"rule": cells[0], "nodes": cells[1], "ids": [to_canvas[t] for t in nums if t in to_canvas],
                     "change": cells[2], "answer": answer})
    # a row is left only with a reason the rules give: a quoted line of a rule file (a Fine or Undecided line, or the
    # bold line of the rule the fix would break), each row its own reason
    rules_text = " ".join(" ".join((REFS / f).read_text(encoding="utf-8").split()) for f in REVIEW_RULE_FILES if (REFS / f).is_file())
    lefts = {}
    for r in rows:
        a = r["answer"]
        if not a.lower().startswith("left:"):
            continue
        why = " ".join(a[5:].split())
        if why in lefts:
            raise Stop(f"rows \"{lefts[why]}\" and \"{r['rule']}\" are left with the same words: answer each row for its own "
                       f"nodes (fix it one row at a time; references/review.md)")
        lefts[why] = r["rule"]
        quotes = [" ".join(q.split()) for q in re.findall(r'"([^"]+)"|“([^”]+)”|「([^」]+)」', a) for q in q if q]
        if not any(len(q) >= 8 and q in rules_text for q in quotes):
            raise Stop(f"\"{a}\": a row is left only with a quoted line of {', '.join(REVIEW_RULE_FILES)} (a Fine or "
                       f"Undecided line, or the bold line of the rule the fix would break), written as it is in the file "
                       f"between quotes. If no such line applies, fix the row")
    seen = (work.cfg.get("review_render") or {}).get(cv.name)
    if any(r["answer"].lower().startswith("fixed") for r in rows) and seen == now:
        raise Stop("rows say \"fixed\", but the workflow is the same as in the picture the reviewer saw: fix it, export again, then register")
    (work.cfg.get("review_render") or {}).pop(cv.name, None)   # the next picture is for a new review
    work.save_cfg()
    cv.s["review"] = {"rows": rows, "not_reviewed": not_reviewed if not rows else None,
                      "no_findings": no_findings and not rows, "checked": checked, "hash": now}
    if not_reviewed and not rows:
        cv.out.append(f"review of {cv.name}: {not_reviewed} (the report page says so; say it in the conversation report too)")
        return
    open_rows = [r for r in rows if not r["answer"]]
    cv.out.append(f"review of {cv.name}: {len(rows)} rows" + (f", {len(open_rows)} without an answer" if open_rows else "")
                  + (f". {checked}" if checked else ". The reviewer's \"Checked: …\" line is missing"))
    if unknown:
        cv.out.append(f"  not a node of the exported workflow (check the reviewer's ids): {' '.join(dict.fromkeys(unknown))}")
    for r in rows:
        cv.out.append(f"  {r['rule']} — {' '.join(r['ids']) or r['nodes']} — {r['answer'] or '(no answer yet)'}")
    cv.out.append("  run `report` again after this, so that the report page shows the review")


def _op_walk(cv, work, args):
    if not args:
        raise Stop("walk <md file>")
    if not Path(args[0]).is_file():
        raise Stop(f"no walkthrough file {args[0]}")
    intro, parts, cur = "", [], None
    for raw in Path(args[0]).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            cur = {"title": line[3:].strip(), "refs": [], "text": []}
            parts.append(cur)
        elif line.startswith("# ") and cur is None and not intro:
            intro = line[2:].strip()
        elif line.startswith("# "):
            raise Stop(f"\"{line}\": write one \"# \" line at the top (what the workflow does), then \"## \" for each part")
        elif cur is None and line:
            raise Stop(f"\"{line}\" comes before the first part: start with \"# <one sentence>\", then \"## <title>\" for each part")
        elif cur is not None and line.lower().startswith("nodes:"):
            cur["refs"] += line.split(":", 1)[1].split()
        elif cur is not None and line:
            cur["text"].append(raw.rstrip())   # kept as lines: a lead sentence and "- " bullets (indented bullets nest)
    if not parts:
        raise Stop("the walkthrough has no part (write \"## <title>\", \"nodes: ...\" and the text for each part)")
    groups = {g["title"]: g["members"] for g in cv.s["groups"]}
    seen, out_parts = {}, []
    for k, prt in enumerate(parts):
        ids = []
        for ref in prt["refs"]:
            if ref.startswith("block:"):
                if ref[6:] not in cv.s["blocks"]:
                    raise Stop(f"part \"{prt['title']}\": no block {ref[6:]}")
                ids += cv.s["blocks"][ref[6:]]
            elif ref.startswith("group:"):
                if ref[6:] not in groups:
                    raise Stop(f"part \"{prt['title']}\": no group {ref[6:]} (a title with spaces cannot be written here; use the ids)")
                ids += groups[ref[6:]]
            elif ref in cv.nodes:
                if cv.nodes[ref].get("type") in NOT_PROCESSING:
                    raise Stop(f"part \"{prt['title']}\": {ref} is a {cv.nodes[ref].get('type')}, not a part of the processing "
                               f"(write only the nodes that do the work)")
                ids.append(ref)
            else:
                raise Stop(f"part \"{prt['title']}\": no node {ref}")
        ids = [i for i in dict.fromkeys(ids) if cv.nodes[i].get("type") not in NOT_PROCESSING]   # blocks and groups may hold Notes
        for i in ids:
            if i in seen:
                raise Stop(f"{i} is in two parts: \"{parts[seen[i]]['title']}\" and \"{prt['title']}\"")
            seen[i] = k
        if not ids:
            raise Stop(f"part \"{prt['title']}\" has no node")
        if not any(t.strip() for t in prt["text"]):
            raise Stop(f"part \"{prt['title']}\" has no text: write one sentence on what the part does under \"nodes:\"")
        out_parts.append({"title": prt["title"], "text": "\n".join(prt["text"]), "ids": ids})
    cv.s["walk"] = {"intro": intro, "parts": out_parts}
    left = [n["id"] for n in cv.s["nodes"] if n["id"] not in seen and n.get("type") not in NOT_PROCESSING]
    cv.out.append(f"walkthrough: {len(out_parts)} parts" + (f"; in no part: {' '.join(left)}" if left else ""))


def _walk_forget(cv, nid):
    """rm: take a removed node out of its walkthrough part, and say so when the part is left with no node."""
    for prt in (cv.s.get("walk") or {}).get("parts") or []:
        if nid in prt["ids"]:
            prt["ids"] = [i for i in prt["ids"] if i != nid]
            if not prt["ids"]:
                cv.out.append(f"walkthrough part \"{prt['title']}\" has no node left: write the walkthrough again")


def walk_gaps(cv):
    """What no longer matches the walkthrough when the report page is made: parts left with no node, and nodes added
    after `walk` that are in no part."""
    w = cv.s.get("walk")
    if not w:
        return []
    out, inside = [], set()
    for prt in w["parts"]:
        ids = [i for i in prt["ids"] if i in cv.nodes]
        inside.update(ids)
        if not ids:
            out.append(f"walkthrough of {cv.name}: part \"{prt['title']}\" has no node (it is left out of the page)")
    left = [n["id"] for n in cv.s["nodes"] if n["id"] not in inside and n.get("type") not in NOT_PROCESSING]
    if left:
        out.append(f"walkthrough of {cv.name}: in no part: {' '.join(left)}")
    return out


def walk_view(cv):
    """The walkthrough for the report page: for each part, the nodes and Reroutes to light (lit) and the wires to light
    (w, keys), following wires through Reroutes. A part whose nodes were all removed is left out (None when none is left)."""
    w = cv.s.get("walk")
    if not w:
        return None
    nodes = cv.nodes
    is_rr = lambda i: nodes.get(i, {}).get("type") == "Reroute"
    key = lambda l: wire_key(l["origin_id"], l["origin_slot"], l["target_id"], l["target_input"])
    out = []
    for p in w["parts"]:
        ids = [i for i in p["ids"] if i in nodes]
        if not ids:
            continue
        lit, keys = set(ids), set()

        def down(nid, path):
            for l in cv.s["links"]:
                if l["origin_id"] != nid:
                    continue
                if is_rr(l["target_id"]):
                    if l["target_id"] not in {x["target_id"] for x in path}:   # a broken file may loop
                        down(l["target_id"], path + [l])
                    continue
                chain = path + [l]
                keys.update(key(x) for x in chain)
                lit.update(x["target_id"] for x in chain[:-1])

        def up(nid, path):
            for l in cv.s["links"]:
                if l["target_id"] != nid:
                    continue
                if is_rr(l["origin_id"]):
                    if l["origin_id"] not in {x["origin_id"] for x in path}:
                        up(l["origin_id"], [l] + path)
                    continue
                chain = [l] + path
                keys.update(key(x) for x in chain)
                lit.update(x["origin_id"] for x in chain[1:])
        for i in ids:
            down(i, [])
            up(i, [])
        out.append({"title": p["title"], "text": p["text"], "ids": ids, "lit": sorted(lit), "w": sorted(keys)})
    return {"intro": w.get("intro", ""), "parts": out} if out else None


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
    "walk": _op_walk,
    "review": _op_review,
}


def apply_op(cv, work, cmd, args):
    """Applies one command (no saving, no report). The command is looked up in OPS."""
    fn = OPS.get(cmd)
    if cmd == "width" and not HAND_PLACING_FOR_TESTS:
        raise Stop("there is no width: each node keeps its own width, and the canvas gives loaders stacked in one "
                   "column the same width")
    if cmd in ("move", "gap") and not HAND_PLACING_FOR_TESTS:
        raise Stop(f"there is no {cmd}: the canvas keeps the gaps. Place by relations (put, row, stack, align, level, "
                   f"inputs; put <unit> right|left <A> below|above <B> for a place between two references). When no "
                   f"relation gives the place, report which two nodes you could not relate")
    if fn is None:
        raise Stop(f"unknown command {cmd} (the list is at the top of canvas.py)")
    fn(cv, work, args)



LAYOUT_ID_BASE = 100000
LAYOUT_OPS = {"block", "put", "row", "stack", "align", "level", "inputs", "shape", "width", "move", "gap",
              "group", "group-align", "color", "rail", "note", "title"}   # move and gap only answer that there is none


# ---- layout by relations (LAYOUT_SOLVE): the plan's vertical relations are kept and the heights solved at once ----
# Order in which relations are added: the geometry of the plan's placing (always) -> the plan's level
# wires -> the canvas's levelling (readable-form, Wires, Bad) -> rails at their output heights -> the plan's other relations. Later plan lines
# first, so a later line wins as it does when the lines are run one by one. A relation that cannot hold with those
# added before it is not kept, and is reported with its line.
REL_WIRE, REL_LEVEL, REL_OTHER = 2, 3, 4


def _solid(cv):
    return [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in {"Reroute"} | NOTE_TYPES]


def _top_node(cv, ids):
    return min(ids, key=lambda i: (G.rect(cv.node(i))[1], i))


def _bottom_node(cv, ids):
    return max(ids, key=lambda i: (G.rect(cv.node(i))[3], i))


def plan_y_relations(cv, k, raw, toks, before):
    """The vertical relations one plan line made, read from where the line put things (so they are exactly what the line
    meant): [(tier, kind, node, anchor, offset, label)] with kind "eq" (y_node - y_anchor = offset), "ge" (>=) or "le" (<=).
    y is the top of the node's box (title included)."""
    op, args = toks[0], toks[1:]
    moved = [n["id"] for n in _solid(cv) if before.get(n["id"]) != (n.get("pos") and list(n["pos"]))]
    if not moved:
        return []
    label = f"line {k} \"{raw.strip()}\""
    y = lambda i: G.rect(cv.node(i))[1]
    out = []

    def rel(tier, kind, m, a):
        if m != a:
            out.append((tier, kind, m, a, y(m) - y(a), label))

    def unit(t):
        u = cv.unit(t, allow_all=True)
        return None if isinstance(u, AllIds) else list(u)

    def beside(ids, ref, al):
        """ids placed beside ref (right or left) with alignment al: a level wire, or tops/bottoms aligned."""
        ids = [i for i in ids if i in moved]
        if not ids:
            return
        l = cv.link_between(ref, ids) if al in ("wire", "step") else None
        if l:
            m, a = (l["target_id"], l["origin_id"]) if l["target_id"] in ids else (l["origin_id"], l["target_id"])
            rel(REL_WIRE, "eq", m, a)
        else:
            a = _bottom_node(cv, ref) if al == "bottom" else _top_node(cv, ref)
        for i in ids:
            rel(REL_OTHER, "eq", i, a)

    def stacked(ids, ref, how):
        ids = [i for i in ids if i in moved]
        if how == "below":
            a = _bottom_node(cv, ref)
            for i in ids:
                rel(REL_OTHER, "ge", i, a)
        else:
            a = _top_node(cv, ref)
            for i in ids:
                rel(REL_OTHER, "le", i, a)

    try:
        if op == "put" and len(args) >= 3:
            ids, side, ref = unit(args[0]), args[1], unit(args[2])
            rest = args[3:]
            second = next(((a, unit(rest[j + 1])) for j, a in enumerate(rest)
                           if a in ("right", "left", "below", "above") and j + 1 < len(rest)), None)
            if ids is None:
                return []
            if second:
                v = (side, ref) if side in ("below", "above") else second
                if v[1] is not None:
                    stacked(ids, v[1], v[0])
            elif ref is None:
                return []
            elif side in ("right", "left"):
                al = next((a for a in rest if a in ALIGNS), None) or ("wire" if cv.link_between(ref, ids) else "top")
                beside(ids, ref, al)
            elif side in ("below", "above"):
                stacked(ids, ref, side)
        elif op == "row":
            pos, opt = parse_opts(args, flags={"top", "wire"}, keyed=("right", "gap"))
            units = [unit(t) for t in pos]
            al = "top" if "top" in opt else "wire"
            pairs = list(zip(units, units[1:]))
            if "right" in opt:
                pairs.insert(0, (unit(opt["right"]), units[0]))
            for prev, u in pairs:
                if prev and u:
                    beside(u, prev, al if al == "top" or cv.link_between(prev, u) else "top")
        elif op == "stack":
            pos, opt = parse_opts(args, flags={"left", "right"}, keyed=("below", "gap"))
            units = [unit(t) for t in pos]
            pairs = list(zip(units, units[1:]))
            if "below" in opt:
                pairs.insert(0, (unit(opt["below"]), units[0]))
            for prev, u in pairs:
                if prev and u:
                    stacked(u, prev, "below")
        elif op == "align" and args and args[0] in ("top", "bottom", "middle") and len(args) > 2:
            ref = unit(args[1])
            if ref:
                a = _bottom_node(cv, ref) if args[0] == "bottom" else _top_node(cv, ref)
                for t in args[2:]:
                    for i in unit(t) or []:
                        if i in moved:
                            rel(REL_OTHER, "eq", i, a)
        elif op == "inputs":
            tid = args[0]
            pos_l = next((l for l in cv.s["links"] if l["target_id"] == tid and l.get("type") == "CONDITIONING"
                          and l["target_input"] in ("positive", "conditioning") and l["origin_id"] in moved), None)
            if pos_l:
                rel(REL_WIRE, "eq", pos_l["origin_id"], tid)
            for i in moved:
                rel(REL_OTHER, "eq", i, tid)
            cv.inputs_columns |= set(moved)
        elif op == "level":
            pos, opt = parse_opts(args, keyed=("move",))
            oid, _ = cv.port_out(pos[0])
            tid, _ = cv.port_in(pos[1])
            ids = cv.unit(opt["move"]) if "move" in opt else [tid]
            m, a = (tid, oid) if tid in ids else (oid, tid)
            rel(REL_WIRE, "eq", m, a)
        elif op == "shape":
            for i in moved[1:]:
                rel(REL_OTHER, "eq", i, moved[0])
    except Stop:
        return []
    return out


def _one_move_equal(cv, p, v, a, b, off, label):
    """Keeps pos[b] - pos[a] = off only when it is one move: everything that moves for it belongs to the block of one
    end (the nodes held to it), and no sampler moves (readable-form, Wires: move its source or its target). Otherwise the
    problem is left as it was."""
    snap = p.snapshot()
    before = p.solve()
    ba, bb = p.block_of(v[a]), p.block_of(v[b])
    if not p.try_equal(v[a], v[b], off, label)[0]:
        return False
    after = p.solve()
    names = {i: n for n, i in v.items()}
    moved = {i for i in range(len(before)) if i in names and abs(after[i] - before[i]) >= 1}
    if (moved <= ba or moved <= bb) and not any(is_sampler(cv.node(names[i])) for i in moved):
        return True
    p.restore(snap)
    return False


def _wire_clear_solved(cv, p, v, rect, ids, oid, slot, tid, tin):
    """Whether the wire oid.slot -> tid.tin passes behind no node where the problem, solved as it stands, puts things."""
    y = p.solve()
    saved = {i: list(cv.node(i)["pos"]) for i in ids}
    try:
        for i in ids:
            cv.set_rect_xy(i, rect[i][0], y[v[i]])
        return wire_clear(cv, cv.out_xy(oid, slot), cv.in_xy(tid, tin), {oid, tid})
    finally:
        for i, xy in saved.items():
            cv.node(i)["pos"] = xy


def _apply_one_moves(cv):
    """Makes level, one after another, the wires one move makes level (one_move_levels: one end moves, with what is
    wired level to it), as the layout without relations does, and returns those wires. Each move is made from where the
    one before it left things, so a node may pass another; where they end up is where the problem starts from."""
    out = []
    for _ in range(60):
        got = one_move_levels(cv)
        if not got:
            break
        l, mv, d, start = got[0]
        cv.translate(sorted(mv), 0, d)
        out.append(l)
    return out


def live_plan_relations(cv, rels):
    """The plan's relations a later line has not overridden, read when the plan's lines are done. A later line overrides
    a relation when it moved the placed node (not only the reference) and the relation no longer holds: the later line
    wins, as when the lines run one by one. A relation broken only because its reference moved is kept (the placed node
    follows its reference)."""
    out = []
    for r in rels:
        tier, kind, m, a, off, label = r
        k = int(label.split()[1])
        if m not in cv.nodes or a not in cv.nodes or not cv.placed(cv.node(m)) or not cv.placed(cv.node(a)):
            continue
        d = G.rect(cv.node(m))[1] - G.rect(cv.node(a))[1] - off
        holds = abs(d) < 1 if kind == "eq" else (d > -1 if kind == "ge" else d < 1)
        if holds or cv.placed_at.get(m, 0) <= k:
            out.append(r)
    return out


def solve_vertical(cv, rails, order, notes):
    """The heights of every node and every rail at once, from the plan's relations (cv.plan_rels) and the canvas's own
    (relations.py). Returns the rails' heights [[y, source, output, targets]] in the order of rails.
    It starts from where the plan put things after the wires one move makes level are made level (those wires are kept
    level, in their place in the order: after the plan's level wires, before the rails and the plan's other relations).
    When the result leaves more such wires (the rails moved nodes), they are made level from there and the problem is
    solved once more from there."""
    out = []
    lv = _apply_one_moves(cv)
    lanes = _solve_vertical_once(cv, rails, order, {n["id"]: G.rect(n) for n in _solid(cv)}, lv, out)
    more = _apply_one_moves(cv)
    if more:
        out2 = []
        lanes = _solve_vertical_once(cv, rails, order, {n["id"]: G.rect(n) for n in _solid(cv)}, lv + more, out2)
        out += [m for m in out2 if m not in out]
    notes += out
    return lanes


def _solve_vertical_once(cv, rails, order, rect, moves, notes):
    p = RL.Problem()
    v = {i: p.var(i, r[1]) for i, r in rect.items()}
    h = {i: r[3] - r[1] for i, r in rect.items()}
    cy = {i: (r[1] + r[3]) / 2 for i, r in rect.items()}
    # 1. geometry, always: nodes that overlap side to side keep their order from top to bottom and a row gap between
    # them (frame to frame where a group frame lies between); a gap the plan made narrower is not widened
    ids = sorted(rect)

    def apart(a, b, ya, yb):
        """The geometry edge between nodes a and b standing at heights ya and yb (box tops), or None when they do not
        overlap side to side: the upper one stays above, a row gap apart (a narrower gap the plan made is kept)."""
        ra, rb = rect[a], rect[b]
        if a == b or not min(ra[2], rb[2]) > max(ra[0], rb[0]):
            return None
        if (ya + h[a] / 2, a) > (yb + h[b] / 2, b):
            a, b, ya, yb = b, a, yb, ya
        need = V_GAP + frame_pad(cv, [b], [a], "below")
        g = yb - (ya + h[a])
        return (v[a], v[b], h[a] + (need if g < 0 else min(g, need)), "geo")
    for a in ids:
        for b in ids:
            if a < b:
                e = apart(a, b, rect[a][1], rect[b][1])
                if e:
                    p.hard(*e)

    # rails: one variable each; the nodes along its run keep their side of the rail's cut, the rails their order
    geo = []
    for idx, (k, raw, args, oid, slot, targets) in enumerate(rails):
        x0, x1, last = rail_extent(cv, oid, targets)
        run = [i for i in ids if i not in {oid} | last and rect[i][0] < x1 and rect[i][2] > x0]
        out_y = cv.out_xy(oid, slot)[1]
        typ = rail_type(cv, oid, slot)
        spec = args[1] if len(args) > 2 and args[1] in ("above", "below", "level") else None
        tins = [cv.port_in(t) for t in args[args.index("to") + 1:]]
        if spec and all(wire_clear(cv, (rect[oid][2], out_y), cv.in_xy(tid, tin), {oid, tid}) for tid, tin in tins):
            notes.append(f"  line {k}: every target is reached directly; the written height ({spec} {args[2]}) is not used")
            spec = None
        if spec == "above":
            cut = cv.bbox(cv.unit(args[2]))[1]
        elif spec == "below":
            cut = cv.bbox(cv.unit(args[2]))[3]
        elif spec == "level":
            cut = cv.out_xy(*cv.port_out(args[2]))[1]
        else:
            cut = out_y
            eyes = [rect[i][1] for i in run if is_sampler(cv.node(i))]
            if eyes and typ == "CONDITIONING":
                cut = min(cut, min(eyes))   # a conditioning rail runs above the samplers even from below them (rail_side)
        geo.append([x0, x1, run, out_y, typ, cut, spec])
    # the order of overlapping rails: model, vae, clip from one loader or one stacked column; conditioning below the
    # model and vae rails; the others by their cuts. Cuts are made to follow the fixed order first, so no cycle forms
    col = stacks(cv)
    must = []
    for i in range(len(rails)):
        for j in range(len(rails)):
            gi, gj = geo[i], geo[j]
            if i == j or min(gi[1], gj[1]) <= max(gi[0], gj[0]):
                continue
            ti, tj = gi[4], gj[4]
            if ti in RAIL_TYPE_ORDER and tj in RAIL_TYPE_ORDER and same_stack(cv, rails[i][3], rails[j][3], col) \
                    and RAIL_TYPE_ORDER.index(ti) < RAIL_TYPE_ORDER.index(tj):
                must.append((i, j))
            elif ti in ("MODEL", "VAE") and tj == "CONDITIONING":
                must.append((i, j))
    for _ in range(len(rails) + 1):
        changed = False
        for i, j in must:
            if geo[j][5] < geo[i][5]:
                geo[j][5] = geo[i][5]
                changed = True
        if not changed:
            break
    rv = [p.var(("rail", idx)) for idx in range(len(rails))]
    for idx, (k, raw, args, oid, slot, targets) in enumerate(rails):
        p.wish(rv[idx], 0, v[oid], geo[idx][3] - rect[oid][1])   # a rail that leaves its output height leaves it as little as it can
    if not p.solvable():
        raise Stop("the placing itself cannot be kept apart (a canvas error): report it")
    dropped = []

    def add(rels):
        for tier, kind, m, a, off, label in rels:
            if m not in v or a not in v:
                continue
            if kind == "eq":
                ok, why = p.try_equal(v[a], v[m], off, label)
            elif kind == "ge":
                ok, why = p.try_edge(v[a], v[m], off, label)
            else:
                ok, why = p.try_edge(v[m], v[a], -off, label)
            if not ok:
                dropped.append(f"{label}: {m} relative to {a} not kept ({why})")
    plan = sorted(getattr(cv, "plan_rels", []), key=lambda r: -int(r[5].split()[1]))   # later lines first
    # 2. the plan's level wires, then every wire level where the plan put it
    add([r for r in plan if r[0] == REL_WIRE])
    roots = getattr(cv, "layout_rail_roots", set())
    level_now = []
    for l in cv.s["links"]:
        o, t = l["origin_id"], l["target_id"]
        if o in rect and t in rect and abs(cv.out_xy(o, l["origin_slot"])[1] - cv.in_xy(t, l["target_input"])[1]) < 1:
            level_now.append((REL_WIRE, "eq", t, o, rect[t][1] - rect[o][1], f"wire {lname(cv, l)} (level where the plan put it)"))
    add(level_now)
    # 3. the canvas's levelling: the wires one move made level before the problem started (solve_vertical), kept level
    for l in moves:
        o, t = l["origin_id"], l["target_id"]
        if o in v and t in v:
            off = (cv.out_xy(o, l["origin_slot"])[1] - rect[o][1]) - (cv.in_xy(t, l["target_input"])[1] - rect[t][1])
            if p.try_equal(v[o], v[t], off, f"levelling {lname(cv, l)}")[0]:
                notes.append(f"  made horizontal: {lname(cv, l)}")
    # 4. rails, one at a time in the rail order: a rail of one target is first tried as a level direct wire. Otherwise
    # its run is taken: the nodes along it whose centre is above its cut stay above it, the others below, and it keeps
    # its order with the rails taken before it. The cut is its output height (written: the unit's edge); when that cannot
    # hold, the nearest cut that can. Then the rail is put at its output height when that can hold (it moves with its
    # source), before the plan's other relations: a rail that leaves its output height needs a raising Reroute, a Bad
    # form as a slanted wire is
    taken = {}

    def run_edges(idx, cut):
        x0, x1, run, out_y, typ, _, spec = geo[idx]
        targets = rails[idx][5]
        above = rail_clear_above(cv, targets)
        es = [(v[i], rv[idx], h[i] + above) if cy[i] < cut else (rv[idx], v[i], LANE_CLEAR_BELOW) for i in run]
        for j, cj in taken.items():
            gi, gj = geo[idx], geo[j]
            if min(gi[1], gj[1]) <= max(gi[0], gj[0]):
                continue
            if (j, idx) in must:
                up = True
            elif (idx, j) in must:
                up = False
            else:
                ti = RAIL_TYPE_ORDER.index(gi[4]) if gi[4] in RAIL_TYPE_ORDER else 9
                tj = RAIL_TYPE_ORDER.index(gj[4]) if gj[4] in RAIL_TYPE_ORDER else 9
                up = (cj, tj, j) < (cut, ti, idx)
            es.append((rv[j], rv[idx], P["RAIL_GAP"]) if up else (rv[idx], rv[j], P["RAIL_GAP"]))
        return es
    direct = set()
    for idx in order:
        k, raw, args, oid, slot, targets = rails[idx]
        x0, x1, run, out_y, typ, cut0, spec = geo[idx]
        out_off = out_y - rect[oid][1]
        if len(targets) == 1 and spec is None:
            tid = targets[0]
            tin = next((l["target_input"] for l in cv.s["links"] if l["origin_id"] == oid and l["origin_slot"] == slot
                        and l["target_id"] == tid), None)
            if tin is not None and tid in v:
                off = out_off - (cv.in_xy(tid, tin)[1] - rect[tid][1])
                snap = p.snapshot()
                if _one_move_equal(cv, p, v, oid, tid, off, f"line {k} (one target, wired level)") and \
                        _wire_clear_solved(cv, p, v, rect, ids, oid, slot, tid, tin):
                    notes.append(f"  line {k}: one target: wired directly, level")
                    direct.add(idx)
                    continue
                p.restore(snap)
        cands = [cut0] + sorted({c for i in run for c in (cy[i] - 0.5, cy[i] + 0.5)} - {cut0}, key=lambda c: (abs(c - cut0), c))
        for c in cands:
            if p.try_edges(run_edges(idx, c), f"line {k} (the rail's run)")[0]:
                taken[idx] = c
                if c != cut0:
                    notes.append(f"  line {k}: the rail's run could not pass at its output height; it passes nearer {round(c)}")
                break
        else:
            raise Stop(f"stopped at line {k} \"{raw.strip()}\" (nothing changed): no run for the rail (a canvas error): report it")
        if spec is not None:
            # a written height: the source does not move for it (the rail lowers or rises with Reroutes); only when the
            # output height is clear as things stand is the rail drawn there (do_rail decides)
            continue
        ok, why = p.try_equal(v[oid], rv[idx], out_off, f"line {k} (rail at its output height)")
        if not ok:
            notes.append(f"  line {k}: the rail cannot run at its output height ({why}); it runs at the nearest height")
    # 5. the plan's other relations
    add([r for r in plan if r[0] == REL_OTHER])
    # 6. no empty band between rails: from the lowest rail up, a rail at its output height
    # comes down with its source (the nodes held to it) towards the next rail below, as far as that moves nothing else
    y = p.solve()
    free = [i for i in taken if geo[i][6] is None and p.find(rv[i])[0] == p.find(v[rails[i][3]])[0]]
    for i in sorted(free, key=lambda i: -y[rv[i]]):
        below = [j for j in taken if y[rv[j]] > y[rv[i]] + 1 and min(geo[i][1], geo[j][1]) > max(geo[i][0], geo[j][0])]
        if not below:
            continue
        j = min(below, key=lambda j: y[rv[j]])
        mine = p.block_of(rv[i])

        def fits(gap):
            snap = p.snapshot()
            try:
                if not p.try_edge(rv[j], rv[i], -gap, f"line {rails[i][0]} (towards the rail below)")[0]:
                    return False
                y1 = p.solve()
                moved = {u for u in range(len(y)) if abs(y1[u] - y[u]) >= 1}
                return moved <= mine and not any(is_sampler(cv.node(n)) for n, u in v.items() if u in moved)
            finally:
                p.restore(snap)
        lo, hi = P["RAIL_GAP"], y[rv[j]] - y[rv[i]]
        if hi - lo < 1:
            continue
        if not fits(lo):
            while hi - lo > 4:
                mid = (lo + hi) / 2
                if fits(mid):
                    hi = mid
                else:
                    lo = mid
            lo = hi
        if lo < y[rv[j]] - y[rv[i]] - 1:
            p.try_edge(rv[j], rv[i], -lo, f"line {rails[i][0]} (towards the rail below)")
            y2 = p.solve()
            notes.append(f"  line {rails[i][0]}: rail pulled {round(y2[rv[i]] - y[rv[i]])}px down towards the rail of line "
                         f"{rails[j][0]}, with its source")
            y = y2
    for i in ids:
        cv.set_rect_xy(i, rect[i][0], y[v[i]])
    for m in dropped:
        notes.append(f"  not kept: {m}")
    lanes = []
    for idx, (k, raw, args, oid, slot, targets) in enumerate(rails):
        ry = y[rv[idx]]
        oy = cv.out_xy(oid, slot)[1]
        if abs(ry - oy) >= 1:
            notes.append(f"  line {k}: rail height {round(ry)}: {round(abs(ry - oy))}px {'above' if ry < oy else 'below'} "
                         f"the output height" + (f" (more than {RAIL_SHIFT_MAX}px)" if abs(ry - oy) > RAIL_SHIFT_MAX else ""))
        lanes.append([ry, oid, slot, targets])
    return lanes


def do_layout(cv, work, args):
    """Applies the plan file from the top and re-places everything. The inside of each block comes first, blocks relative to each other last.
    If any line stops, nothing changes.
    Order, each phase moving only what the phases before it left:
    1. the plan lines that place nodes (rails and Notes wait)
    2. nodes: level the one-move wires, widen crossed gaps, close gaps, clear below growing nodes
    3. rails: written heights first, the others around them; draw; wires along a rail join it
    4. groups: frames from their nodes only (not Notes); separate overlapping groups; push other nodes out of a frame
    5. Notes, last; they move nothing"""
    if not args:
        raise Stop("layout <plan file>")
    lines, _ = plan_lines(args[0])
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
        # a title the author gave goes back to ComfyUI's display name (readable-form.md, Names): the canvas knows the
        # name, so it does it. A value node keeps "display name: what the value is", a node loading an image "display name: what it takes"
        t = n.get("title")
        if t and n.get("type") not in {"Reroute"} | NOTE_TYPES:
            shown = (cv.oi.get(n.get("type")) or {}).get("display_name") or n.get("type")
            if t != shown and not (may_say_what(cv, n) and t.startswith(shown + ":")):
                n.pop("title", None)
                cv.size_node(n)
        widened = n.pop("size_min", None) is not None
        if n.pop("width_set", None) or widened or n.get("type") == "CLIPTextEncode":
            # (a CLIP Text Encode is sized again too: whether it only feeds SAM3 is known once it is wired)
            # also clear widths widened by the plan's width and start again from the initial size (a leftover width would not go back when the plan is edited)
            cv.size_node(n)
    cv.s["blocks"], cv.s["groups"], cv.s["group_align"] = {}, [], []
    cv.relink()
    cv.in_layout = True
    cv.placed_at = {}
    drawn_later = []
    # ids of Reroutes and Notes made by the plan start from the same number every time (the same plan gives the same result).
    # They start where they cannot collide with the numbers of ordinary commands (n... from add)
    keep_next = cv.s["next_id"]
    cv.s["next_id"] = LAYOUT_ID_BASE
    count = 0
    notes = []
    hand = []
    # every group of the plan is known before the lines that place, so a gap can count a frame drawn later
    cv.wide_gaps = []
    cv.s["wide_pairs"] = []
    cv.plan_rels, cv.inputs_columns = [], set()
    cv.s["stepped"] = []
    cv.clip_loader_role_color()
    cv.plan_group_lines = []
    for raw in lines:
        try:
            toks = shlex.split(raw, comments=True)
        except ValueError:
            continue
        if toks and toks[0] == "group":
            gpos = parse_opts(toks[1:], keyed=("color",))[0]
            if len(gpos) >= 2:
                cv.plan_group_lines.append((gpos[0], gpos[1:]))
        elif len(toks) > 2 and toks[0] == "title" and toks[1] in cv.nodes:
            # a title changes the node's width: set it before anything is placed, wherever the line is written (its
            # line sets it again in its turn, to the same width)
            mark = len(cv.out)
            _op_title(cv, work, toks[1:])
            del cv.out[mark:]
    later = []
    note_ids = set()
    for raw in lines:
        try:
            toks = shlex.split(raw, comments=True)
        except ValueError:
            continue
        if len(toks) > 1 and toks[0] == "note":
            note_ids.add(Path(toks[1]).stem)

    def in_group_note(toks):
        """The title of the group holding every node the Note line is placed against, once those nodes stand; else None."""
        if len(toks) < 4 or toks[3] == "all" or Path(toks[1]).stem in cv.nodes:
            return None
        try:
            ref = set(cv.unit(toks[3]))
        except Stop:
            return None
        if not ref or not all(cv.placed(cv.nodes[i]) for i in ref if i in cv.nodes):
            return None
        return next((t for t, m in plan_groups(cv).items() if ref <= m), None)

    def run_line(k, raw, toks):
        nonlocal count, notes, hand
        mark = len(cv.out)
        wide_before = len(cv.wide_gaps)
        before = {n["id"]: n.get("pos") and list(n["pos"]) for n in cv.s["nodes"]}
        try:
            if toks[0] == "rail" and "to" in toks:
                # every rail waits for the rail stage (a height written in the plan is fixed there, before the others)
                cv.port_out(toks[1])
                for t in toks[toks.index("to") + 1:]:
                    cv.port_in(t)
                drawn_later.append((k, raw, toks[1:]))
            elif toks[0] == "group" and any(t in note_ids for t in toks[1:]) and \
                    any(g["title"] == toks[1] for g in cv.s["groups"]):
                # a group line naming a Note, run after the rails: the Notes join the group made earlier (so the
                # lowering Reroutes that joined it stay in it)
                g = next(g for g in cv.s["groups"] if g["title"] == toks[1])
                for t in parse_opts(toks[2:], keyed=("color",))[0]:
                    for i in cv.unit(t):
                        if i not in g["members"]:
                            g["members"].append(i)
                cv.update_groups()
            else:
                apply_op(cv, work, toks[0], toks[1:])
                if LAYOUT_SOLVE:
                    cv.plan_rels += plan_y_relations(cv, k, raw, toks, before)
        except Stop as e:
            raise Stop(f"stopped at line {k} \"{raw.strip()}\" (nothing changed): {e}")
        except Exception as e:   # a bug in the canvas. Stop and say which line of the plan (nothing changes)
            raise Stop(f"stopped by a canvas error at line {k} \"{raw.strip()}\" (nothing changed): {type(e).__name__}: {e}")
        for n in cv.s["nodes"]:
            if n.get("pos") and before.get(n["id"]) != list(n["pos"]):
                cv.placed_at[n["id"]] = k
        notes += [f"  line {k}: {m}" for m in cv.out[mark:]]
        hand += [{"line": k, "plan": raw.split("#", 1)[0].strip(), "why": w} for w in cv.wide_gaps[wide_before:]]
        count += 1

    for k, raw in enumerate(lines, 1):
        toks = shlex.split(raw, comments=True)
        if not toks:
            continue
        if toks[0] not in LAYOUT_OPS:
            raise Stop(f"line {k} \"{raw.strip()}\": layout accepts only {' '.join(sorted(LAYOUT_OPS))}")
        if toks[0] == "group" and any(t in note_ids for t in toks[1:]):
            now = [t for t in toks if t not in note_ids]
            if len(parse_opts(now[1:], keyed=("color",))[0]) > 1:
                run_line(k, raw, now)          # the group now, its Notes after the rails
            later.append((k, raw, toks))
        elif toks[0] == "note" and in_group_note(toks):
            # a Note on a node of a group is placed now, in the order written, as part of that group: its frame takes
            # it in from the start, and what is placed after keeps clear of the frame
            cv.note_group = in_group_note(toks)   # the Note is in the group while it is placed (no frame gap to it)
            run_line(k, raw, toks)
            cv.note_group = None
            cv.update_groups()
        elif toks[0] == "note" or any(t in note_ids for t in toks[1:]):
            later.append((k, raw, toks))        # Notes are placed last, after the rails
        else:
            run_line(k, raw, toks)
    # wires one move makes horizontal, then the gaps where wires cross, before the rails (rails are drawn from where the
    # nodes then stand)
    # (the outputs the plan carries on rails are left to the rails: their heights are the rails')
    cv.layout_rail_roots = {cv.port_out(args[0]) for _, _, args in drawn_later}
    if LAYOUT_SOLVE:
        cv.plan_rels = live_plan_relations(cv, cv.plan_rels)
    for m in (level_what_one_move_levels(cv) if AUTO_LEVEL and AUTO_FIX and not LAYOUT_SOLVE else []):
        notes.append(f"  {m}")
    for m in (widen_crossed_gaps(cv) if AUTO_FIX or WIDE_GAP else []):
        notes.append(f"  {m}")
    for m in (close_gaps(cv) if AUTO_LEVEL and AUTO_FIX else []):
        notes.append(f"  {m}")
    for m in (clear_below_growing(cv) if AUTO_FIX else []):
        notes.append(f"  {m}")
        hand.append({"line": 0, "plan": "", "why": m})
    # rails without a written height, after every other line: first each one's height (moving nodes where needed; a later
    # move carries the heights already chosen along when it moves their source and targets), then their Reroutes.
    # The order does not follow the plan: loaders of model, clip and vae first (they head their rails), then from the left
    # and from the top, so the same rails give the same result whatever order the plan writes them in
    rails = []
    for k, raw, args in drawn_later:
        try:
            oid, slot = cv.port_out(args[0])
            if not cv.placed(cv.node(oid)):
                raise Stop(f"the rail source {oid} is not placed yet")
            targets = [cv.port_in(t)[0] for t in args[args.index("to") + 1:]]
            un = [t for t in targets if not cv.placed(cv.node(t))]
            if un:
                raise Stop(f"rail targets not placed: {' '.join(un)}")
        except Stop as e:
            raise Stop(f"stopped at line {k} \"{raw.strip()}\" (nothing changed): {e}")
        rails.append((k, raw, args, oid, slot, targets))
    rank = lambda i: (RAIL_TYPE_ORDER.index(rail_type(cv, rails[i][3], rails[i][4]))
                      if rail_type(cv, rails[i][3], rails[i][4]) in RAIL_TYPE_ORDER else len(RAIL_TYPE_ORDER))
    order = sorted(range(len(rails)), key=lambda i: (rank(i), not cv.is_model_loader(cv.node(rails[i][3])),
                                                     G.rect(cv.node(rails[i][3]))[0], cv.out_xy(rails[i][3], rails[i][4])[1], rails[i][0]))
    if LAYOUT_SOLVE:
        lanes = solve_vertical(cv, rails, order, notes)
        cv.fixed_lanes = set()
    else:
        lanes = [None] * len(rails)
        done = []
        # a height written in the plan is fixed first, from where the nodes now stand; the other rails choose theirs around
        # it. When every target of such a rail is reached directly behind nothing, it is one without a height
        fixed = set()

        # rails written at the same place (above X / below X) are stacked in the rules' order whatever order the plan
        # lists them in: from the top model, vae, clip, then conditioning, then the rest; the outputs of one node in slot
        # order (positive right above its negative). For above the last in that order is nearest X, for below the first
        # (listed as model, vae, vae under `above 1`, they had stacked upwards in reverse)
        def stack_key(i):
            k, raw, args, oid, slot, targets = rails[i]
            t = rail_type(cv, oid, slot)
            rank = (RAIL_TYPE_ORDER + ("CONDITIONING",)).index(t) if t in RAIL_TYPE_ORDER + ("CONDITIONING",) else 9
            return (rank, cv.out_xy(oid, slot)[1], slot, k)

        def written(i):
            args = rails[i][2]
            return args[1] if len(args) > 2 and args[1] in ("above", "below", "level") else None
        seq = sorted(range(len(rails)), key=lambda i: (written(i) or "", rails[i][2][2] if written(i) else "", stack_key(i)))
        seq = [i for i in seq if written(i) != "above"] + [i for i in reversed(seq) if written(i) == "above"]
        for i in seq:
            k, raw, args, oid, slot, targets = rails[i]
            spec = args[1] if len(args) > 2 and args[1] in ("above", "below", "level") else None
            if spec is None:
                continue
            a = cv.out_xy(oid, slot)
            tins = [cv.port_in(t) for t in args[args.index("to") + 1:]]
            if not PLAN_RAILS and all(wire_clear(cv, a, cv.in_xy(tid, tin), {oid, tid}) for tid, tin in tins):
                notes.append(f"  line {k}: every target is reached directly; the written height ({spec} {args[2]}) is not used")
                continue
            try:
                if spec == "above":
                    y = cv.bbox(cv.unit(args[2]))[1] - V_GAP
                elif spec == "below":
                    y = cv.bbox(cv.unit(args[2]))[3] + V_GAP
                else:
                    y = cv.out_xy(*cv.port_out(args[2]))[1]
            except Stop as e:
                raise Stop(f"stopped at line {k} \"{raw.strip()}\" (nothing changed): {e}")
            if spec in ("above", "below"):
                # two rails written at the same height are stacked, the later one further out (up for above, down for below)
                x0, x1 = rail_extent(cv, oid, targets)[:2]
                for _ in range(50):
                    near = [lanes[j][0] for j in fixed if abs(lanes[j][0] - y) < P["RAIL_GAP"]
                            and min(x1, rail_extent(cv, lanes[j][1], lanes[j][3])[1]) > max(x0, rail_extent(cv, lanes[j][1], lanes[j][3])[0])]
                    if not near:
                        break
                    y = min(near) - P["RAIL_GAP"] if spec == "above" else max(near) + P["RAIL_GAP"]
                y = one_target_height(cv, oid, slot, tins, spec, y, notes, k)
            lanes[i] = [y, oid, slot, targets]
            fixed.add(i)

        def choose(i):
            k, raw, args, oid, slot, targets = rails[i]
            try:
                y, msgs = open_lane(cv, oid, slot, targets, [ln for ln in lanes if ln is not None and ln[1:3] != [oid, slot]])
            except Stop as e:
                raise Stop(f"stopped at line {k} \"{raw.strip()}\" (nothing changed): {e}")
            if lanes[i] is None:
                lanes[i] = [y, oid, slot, targets]
            else:
                lanes[i][0] = y
            notes.extend(f"  line {k}: {m}" for m in msgs)
        for i in order:
            if i in fixed:
                continue
            if PLAN_RAILS:
                k, raw, args, oid, slot, targets = rails[i]
                lanes[i] = [cv.out_xy(oid, slot)[1], oid, slot, targets]
                notes.append(f"  line {k}: rail height {round(lanes[i][0])}: the output height of its source")
            else:
                choose(i)
        # a later move may have put a node on a height chosen earlier: choose that one again from where things are now.
        # A rail chosen again twice means two rails keep pushing each other: stop and name them
        again = {}
        for _ in (range(0) if PLAN_RAILS else range(2 * len(rails) + 1)):
            bad = None
            for i in order:
                if i in fixed:
                    continue   # the plan wrote that height
                y, oid, slot, targets = lanes[i]
                x0, x1, last = rail_extent(cv, oid, targets)
                near = [j for j in order if j != i and abs(lanes[j][0] - y) < P["RAIL_GAP"]
                        and min(rail_extent(cv, lanes[j][1], lanes[j][3])[1], x1) > max(rail_extent(cv, lanes[j][1], lanes[j][3])[0], x0)]
                if lane_blockers(cv, y, x0, x1, {oid} | last, rail_clear_above(cv, targets)) or near:
                    bad = (i, near)
                    break
            if bad is None:
                break
            i, near = bad
            again[i] = again.get(i, 0) + 1
            if again[i] > 1:
                others = " ".join(f"line {rails[j][0]}" for j in near) or "the nodes moved for another rail"
                raise Stop(f"stopped at line {rails[i][0]} \"{rails[i][1].strip()}\" (nothing changed): its height keeps being "
                           f"blocked by {others}. Place the sources or targets of these rails apart, or give one of them above <unit> or below <unit>")
            choose(i)
        for i, j in ([] if PLAN_RAILS else swap_by_crossings(cv, lanes)):
            notes.append(f"  line {rails[i][0]}: rail height {round(lanes[i][0])}: swapped with the rail of line {rails[j][0]}, "
                         f"so fewer wires cross")
        cv.fixed_lanes = {i for i in fixed}
        for m in (pull_rails(cv, lanes) if AUTO_FIX else []):
            notes.append(f"  {m}")
    cv.layout_lanes = lanes
    for (k, raw, args, oid, slot, _), (y, *_rest) in zip(rails, lanes):
        mark = len(cv.out)
        try:
            do_rail(cv, [args[0], "at", str(y), str(k)] + args[args.index("to"):])
        except Stop as e:
            raise Stop(f"stopped at line {k} \"{raw.strip()}\" (nothing changed): {e}")
        except Exception as e:
            raise Stop(f"stopped by a canvas error at line {k} \"{raw.strip()}\" (nothing changed): {type(e).__name__}: {e}")
        notes += [f"  line {k}: {m}" for m in cv.out[mark:]]
    # Notes placed against all (the overview Note), and every line naming them, after the other Notes, so all takes
    # every Note in. In the order written within each
    all_notes = {Path(t[1]).stem for _, _, t in later if t[0] == "note" and len(t) > 1 and "all" in t[2:]}
    all_notes |= {x for _, _, t in later if t[0] == "align" and "all" in t[1:] for x in t[1:] if x in note_ids}
    while True:   # a Note placed against one of them comes after it too
        more = {Path(t[1]).stem for _, _, t in later if t[0] == "note" and len(t) > 2
                and any(x in all_notes for x in t[2:])} - all_notes
        if not more:
            break
        all_notes |= more
    # rails done; then the groups (frames from their nodes), then the Notes, which move nothing
    for m in (rail_the_wires_along_rails(cv) if AUTO_FIX else []):
        notes.append(f"  {m}")
    for m in (separate_groups(cv) if AUTO_FIX else []):
        notes.append(f"  {m}")
    for m in (clear_group_frames(cv) if AUTO_FIX else []):
        notes.append(f"  {m}")
    for k, raw, toks in sorted(later, key=lambda x: "all" in x[2][1:] or any(t in all_notes for t in x[2][1:])
                               or (x[2][0] == "note" and len(x[2]) > 1 and Path(x[2][1]).stem in all_notes)):
        run_line(k, raw, toks)
    cv.s["next_id"] = keep_next
    cv.s["hand_placed"] = hand
    # kept for the report page (keyed by this command's undo snapshot; undo drops it with the state)
    snaps = len(list(cv.hist.glob("*.json"))) if cv.hist.exists() else 0
    cv.s.setdefault("layout_notes", {})[str(snaps - 1)] = {"lines": count, "notes": [m[2:] for m in notes]}
    # the reply is an error log: what the agent wrote is not reported back; only what the canvas did
    # beyond the lines, what is left unplaced, and the forms that break a rule of the skill, each with the rule's place
    # and its bold sentence. Everything else is in `check`
    cv.out = [f"layout: applied {count} lines"]
    beyond = [m for m in notes if any(k in m for k in BEYOND_THE_LINES)]
    un = [n["id"] for n in cv.s["nodes"] if not cv.placed(n)]
    before_w = {n["id"]: n["size"][0] for n in cv.s["nodes"] if n.get("size")}
    cv.same_loader_width()
    for n in cv.s["nodes"]:
        if n.get("size") and before_w.get(n["id"]) != n["size"][0]:
            beyond.append(f"  width {n['id']}: {before_w.get(n['id'])} -> {n['size'][0]} (loader widths aligned)")
    cv.save()
    if beyond:
        cv.out.append("done by the canvas beyond the lines:")
        cv.out += beyond
    if un:
        cv.out.append(f"unplaced: {' '.join(un)}")
    hard = hard_problems(cv)
    cv.out += violations(hard) if hard else ["no form the rules call Bad (all notices: check)"]
    soft = soft_problems(cv)
    if soft:
        cv.out += violations(soft, "weigh less: fix them when it breaks nothing above")
    return cv.out


# what the canvas did that the plan's lines did not say (reported back after a layout)
BEYOND_THE_LINES = ("with its group", "lowering Reroute stands", "no fixed yellow", "not clear there", "was not clear",
                    "gap widened", "was not placed", "stepped down")


def violations(lines, how="fix them in the plan"):
    """The forms that break a rule, as an error log: [file section name] where; then the rule's bold sentence."""
    blocks = rule_blocks()
    out = [f"violations of the skill's rules ({len(lines)}): {how}"]
    for ln in lines:
        body = ln.strip()
        ref, rule = "readable-form.md", ""
        if "replacements.md" in body:
            ref = "replacements.md"
        elif body.startswith("Note ") and ("explains" in body or "widens the frame" in body):
            ref, rule = "notes.md Where to place", "A Note on part of the processing stands next to the node it explains, placed last, in free space."
        elif "model Note top edge" in body:
            ref, rule = "notes.md Where to place", "The overview and models Note stands at the upper left of the whole workflow, its top edge on the top edge of the whole workflow."
        else:
            for keys, start in CHECK_RULES:
                if any(k in body for k in keys):
                    b = next(((k, v) for k, v in blocks.items() if k.startswith(start)), None)
                    if b:
                        ref = f"readable-form.md {b[1][0].split(':')[0]}"
                        rule = b[0].split(". ")[0].rstrip(".") + "."
                    break
        out.append(f"  [{ref}] {body}")
        if rule:
            out.append(f"      rule: {rule}")
    return out


# which rule of readable-form.md each kind of check line comes from (the rule's bold line starts with this). The rule's
# text is read from the file each time, so the skill stays the one place it is written
CHECK_RULES = [
    # the more particular first: a line takes the first rule whose words it contains
    (("groups overlap", "wire over the title", "node over the title", "node overlapping group"),
     "A group holds one large function"),
    (("loader is above the model loader", "loader is above the vae loader", "clip loader"), "A loader stands in the column left"),
    (("rail order differs", "rail runs above the", "loader rail runs below", "stacked loaders differ"),
     "A wire is drawn directly"),   # its rail line holds the order
    (("loader away from its first user", "vae loader"), "A loader stands in the column left"),
    (("right edges of the sources", "model chain end"), "The sources wired straight into a sampler"),
    (("overlap:", "is directly below"), "No node is hidden"),
    (("narrow gap", "empty band", "gap inside a column", "wide gap to a wired neighbour", "uneven spacing",
      "times in the gap"), "Wires show and nothing is packed"),
    (("wire behind a node", "Reroute", "single value carried", "rail needs no raising", "rails too close"),
     "A wire is drawn directly"),
    (("non-horizontal wire", "slanted wire", "reference wire level", "no wire level into"), "A wire is horizontal when it can be"),
    (("image into",), "Other chains have their own rows"),
    (("one-line text into",), "A value is put in a value node only when"),
    (("latent into the sampler slants", "positive into the sampler slants"), "Build the core in the usual form"),
    (("backward wire",), "No wire goes back"),
    (("crossing",), "Left to right in processing order"),
    (("samplers of stages in a row", "main flow wire"), "The main flow"),
    (("side-use image rail",), "A wire is drawn directly"),
    (("is above its source",), "Build the core in the usual form"),
    (("wire over the title", "node over the title", "node overlapping group", "groups overlap"),
     "A group holds one large function"),
    (("value nodes side by side",), "A value is put in a value node"),
    (("title the author gave",), "Node names are not changed"),
]
RULES_FILE = Path(__file__).resolve().parent.parent / "references" / "readable-form.md"


def rule_blocks():
    """{bold line of a rule: [section and bold line, then its bullet lines]} from readable-form.md."""
    out, cur, section = {}, None, ""
    try:
        text = RULES_FILE.read_text(encoding="utf-8")
    except OSError:
        return {}
    for ln in text.splitlines():
        if ln.startswith("## "):
            section, cur = ln[3:].strip(), None
        elif ln.startswith("**"):
            bold = ln.split("**")[1]
            cur = out.setdefault(bold, [f"{section}: {bold}"])
        elif ln.startswith("- ") and cur is not None:
            cur.append("  " + ln)
        elif ln.strip():
            cur = None
    return out


def rules_for(lines):
    """The rules the check lines come from, quoted from readable-form.md, each once."""
    blocks = rule_blocks()
    want = []
    for ln in lines:
        body = ln.strip()
        for keys, start in CHECK_RULES:
            if any(k in body for k in keys):
                if start not in want:
                    want.append(start)
                break
    out = []
    for start in want:
        b = next((v for k, v in blocks.items() if k.startswith(start)), None)
        if b:
            out += ["  " + x for x in b]
    if not out:
        return []
    return ["■ the rules these lines come from (quoted from references/readable-form.md). Decide by them, on the picture; "
            "the counts are not the goal"] + out


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


RAIL_USAGE = "rail <A>.<output> [above <unit>|below <unit>|level <X>.<output>] to <B>.<input> ..."
# rails of what the sampler uses run above the eye line (the top of the samplers along the rail); other rails run below it.
# Measured on the skill author's hand-made layouts (35 workflows, every rail of these types on the measured side)
TOOL_RAIL_TYPES = {"MODEL", "VAE", "NOISE", "CLIP", "CONDITIONING"}
# clearance from a rail (its height) to the nodes it passes, rounded from half a Reroute (13) plus the smallest gap between
# a Reroute and the node above (27) and below (35) it in the skill author's hand-made layouts (118 Reroutes in 35 workflows)
LANE_CLEAR_ABOVE = 40
LANE_CLEAR_BELOW = 50


# rails of these types run top to bottom in this order wherever their runs overlap (the skill author: always, no exception)
RAIL_TYPE_ORDER = ("MODEL", "VAE", "CLIP")


def stacks(cv):
    """Columns of nodes stacked one right below another: {node id: column number}. Two placed nodes (not Reroutes or
    Notes) are in one column when their horizontal ranges overlap and one stands within V_GAP below the other."""
    ns = [n for n in cv.s["nodes"] if cv.placed(n) and n.get("type") not in {"Reroute"} | NOTE_TYPES]
    parent = {n["id"]: n["id"] for n in ns}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a in ns:
        ra = G.rect(a)
        for b in ns:
            rb = G.rect(b)
            if a is not b and min(ra[2], rb[2]) > max(ra[0], rb[0]) and 0 <= rb[1] - ra[3] <= V_GAP + 1:
                parent[find(a["id"])] = find(b["id"])
    return {i: find(i) for i in parent}


def same_stack(cv, a, b, col=None):
    """Whether nodes a and b are one node or stand in one stacked column (stacks)."""
    if a == b:
        return True
    col = col or stacks(cv)
    return a in col and b in col and col[a] == col[b]


def rail_type(cv, oid, slot):
    return ((cv.node(oid).get("outputs") or [])[slot] or {}).get("type")


def type_bounds(cv, oid, slot, targets, lanes):
    """Bounds (lo, hi) on a rail's height from the rails of MODEL, VAE and CLIP already given a height whose runs overlap
    it and whose source is the same node or stands in the same stacked column: a rail of a type earlier in
    RAIL_TYPE_ORDER stays above, a later one below, RAIL_GAP apart. (A Load VAE placed by its first user elsewhere,
    not stacked with the other loaders, is not ordered with them.)"""
    t = rail_type(cv, oid, slot)
    if t == "CONDITIONING":
        # a conditioning rail runs below the model and vae rails whose runs overlap it (the skill author: by default)
        x0, x1, _ = rail_extent(cv, oid, targets)
        lo = float("-inf")
        for y, o, sl, tg in lanes:
            if rail_type(cv, o, sl) in ("MODEL", "VAE"):
                a0, a1, _ = rail_extent(cv, o, tg)
                if min(a1, x1) > max(a0, x0):
                    lo = max(lo, y + P["RAIL_GAP"])
        return lo, float("inf")
    if t not in RAIL_TYPE_ORDER:
        return float("-inf"), float("inf")
    r = RAIL_TYPE_ORDER.index(t)
    x0, x1, _ = rail_extent(cv, oid, targets)
    lo, hi = float("-inf"), float("inf")
    col = stacks(cv)
    for y, o, sl, tg in lanes:
        u = rail_type(cv, o, sl)
        if u not in RAIL_TYPE_ORDER or (o, sl) == (oid, slot) or not same_stack(cv, o, oid, col):
            continue
        a0, a1, _ = rail_extent(cv, o, tg)
        if min(a1, x1) <= max(a0, x0):
            continue
        if RAIL_TYPE_ORDER.index(u) < r:
            lo = max(lo, y + P["RAIL_GAP"])
        elif RAIL_TYPE_ORDER.index(u) > r:
            hi = min(hi, y - P["RAIL_GAP"])
    return lo, hi


def is_output_node(cv, n):
    """A node that only shows or saves (Save Image, Preview, Compare): its own position matters less than a wire through it."""
    return bool((cv.oi.get(n.get("type")) or {}).get("output_node"))


def lane_blockers(cv, y, x0, x1, skip, above=LANE_CLEAR_ABOVE):
    """Placed nodes (not Reroutes, not those in skip) that a rail at height y from x0 to x1 would pass too close to."""
    return [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute" and m["id"] not in skip
            and G.rect(m)[0] < x1 and G.rect(m)[2] > x0
            and G.rect(m)[3] > y - above and G.rect(m)[1] < y + LANE_CLEAR_BELOW]


def rail_clear_above(cv, targets):
    """Clearance from a rail to the nodes above it. A rail with a target in a group lowers into it with a Reroute that
    joins the group, so the group's frame reaches GROUP_PAD_TOP above that Reroute's top (half a Reroute above the rail):
    the nodes above must clear the frame, not only the rail."""
    if any(t in g["members"] for g in cv.s["groups"] for t in targets):
        return max(LANE_CLEAR_ABOVE, PAD_T + REROUTE_H / 2)
    return LANE_CLEAR_ABOVE


def rail_extent(cv, oid, targets):
    """Where the run of a rail starts and ends: (right edge of the source, left edge of the rightmost target, the rightmost
    targets). The end is open (infinity) while a target is not placed yet."""
    x0 = G.rect(cv.node(oid))[2]
    placed = [(G.rect(cv.node(t))[0], t) for t in targets if cv.placed(cv.node(t))]
    if len(placed) < len(targets) or not placed:
        return x0, float("inf"), set()
    x1 = max(x for x, _ in placed)
    return x0, x1, {t for x, t in placed if x == x1}


def rail_side(cv, oid, slot, x0, x1):
    """Bounds (lo, hi) on the height of a rail from the eye line: a rail of what the sampler uses whose output is above the
    eye line stays above it, and a conditioning rail always does; another rail whose output is below the eye line
    stays below it."""
    a = cv.out_xy(oid, slot)
    typ = (cv.node(oid).get("outputs") or [])[slot].get("type")
    eye = [G.rect(m)[1] for m in cv.s["nodes"] if cv.placed(m) and is_sampler(m) and G.rect(m)[0] <= x1 and G.rect(m)[2] > x0]
    if eye and typ in TOOL_RAIL_TYPES and a[1] < min(eye):
        return float("-inf"), min(eye)
    if eye and typ == "CONDITIONING":
        # conditioning runs above the samplers even when its encoder stands lower (the skill author)
        return float("-inf"), min(eye)
    if eye and typ not in TOOL_RAIL_TYPES and a[1] > min(eye):
        return min(eye), float("inf")
    return float("-inf"), float("inf")


def rail_height(cv, oid, slot, targets, extra=(), bounds=None):
    """The height of a rail whose height is not written: (height, how it was chosen).
    The output height if the run there passes no node too closely (rail_clear_above / LANE_CLEAR_BELOW) and keeps RAIL_GAP
    from other rails (and from extra: [(height, left, right, root)]); otherwise the clear height nearest to the output height,
    on its side of the eye line (rail_side). A target that stands before the rightmost one counts as in the way (the run
    would go on behind it)."""
    a = cv.out_xy(oid, slot)
    x0, x1, last = rail_extent(cv, oid, targets)
    skip = {oid} | last
    above = rail_clear_above(cv, targets)
    lo, hi = rail_side(cv, oid, slot, x0, x1)
    if bounds:
        lo, hi = max(lo, bounds[0]), min(hi, bounds[1])
    others = [sy for sy, sx0, sx1, root in rail_spans(cv) + list(extra)
              if root != (oid, slot) and min(sx1, x1) > max(sx0, x0)]

    def free(y):
        return lo <= y <= hi and not lane_blockers(cv, y, x0, x1, skip, above) and not any(abs(sy - y) < P["RAIL_GAP"] for sy in others)
    if free(a[1]):
        return a[1], "at the output height"
    cands = [lo, hi] + [y for sy in others for y in (sy - P["RAIL_GAP"], sy + P["RAIL_GAP"])]
    for m in cv.s["nodes"]:
        if cv.placed(m) and m.get("type") != "Reroute" and m["id"] not in skip and G.rect(m)[0] < x1 and G.rect(m)[2] > x0:
            r = G.rect(m)
            cands += [r[1] - LANE_CLEAR_BELOW, r[3] + above]
    cands = sorted({c for c in cands if abs(c) != float("inf") and free(c)}, key=lambda c: (abs(c - a[1]), c))
    if not cands:
        raise Stop(f"no clear height for the rail of {oid}: place its source or targets in the plan so the run is clear")
    y = cands[0]
    in_way = " ".join(m["id"] for m in lane_blockers(cv, a[1], x0, x1, skip, above))
    why = f"in the way at the output height: {in_way}" if in_way else "too close to another rail at the output height"
    return y, f"{round(abs(y - a[1]))}px {'above' if y < a[1] else 'below'} the output height, the nearest clear height ({why})"


# how far a rail may leave its output height: rounded from the largest such shift in the skill author's hand-made layouts
# (253px, ltx_2_5_image2video). Farther than this, the rail opens a lane near the output height instead
RAIL_SHIFT_MAX = 250


def horizontal_pairs(cv):
    """Pairs of placed nodes (not Reroutes) joined by a horizontal wire: what a lane must not cut apart."""
    nodes = cv.nodes
    out = []
    for l in cv.s["links"]:
        o, t = nodes.get(l["origin_id"]), nodes.get(l["target_id"])
        if not o or not t or "Reroute" in (o.get("type"), t.get("type")) or not cv.placed(o) or not cv.placed(t):
            continue
        if abs(cv.out_xy(o["id"], l["origin_slot"])[1] - cv.in_xy(t["id"], l["target_input"])[1]) < 1:
            out.append((o["id"], t["id"]))
    return out


def lands_on_reroute(cv, moving, dy):
    """Whether moving these nodes by dy puts one on a Reroute already drawn (a rail with a written height, drawn at its
    line): such a move would leave the Reroute behind on the node."""
    rr = [G.rect(m) for m in cv.s["nodes"] if m.get("type") == "Reroute" and cv.placed(m) and m["id"] not in moving]
    if not rr:
        return False
    for i in moving:
        r = G.rect(cv.node(i))
        if any(rect_overlap((r[0], r[1] + dy, r[2], r[3] + dy), q) for q in rr):
            return True
    return False


def lane_moving(cv, solid, run, pairs, c, down, oid, out_y):
    """The nodes that move down by `down` to open a lane at height c, or None if that cannot be done cleanly.
    Starts from the nodes along the run whose centre is below c, and adds, until nothing changes, the nodes joined to a
    moving node by a horizontal wire and the nodes a moving node would land on or come within V_GAP of. If that reaches a node along the run whose
    centre is above c, or the source while the lane is not above its output, the lane is not opened there."""
    if not down:
        return set()
    by_id = {m["id"]: m for m in solid}
    in_run = {m["id"] for m in run}
    moving = {m["id"] for m in run if (G.rect(m)[1] + G.rect(m)[3]) / 2 > c}
    while True:
        # a node that only saves or shows steps down from the wire it is level with (a staircase): the wire through wins
        add = ({q for p, q in pairs if p in moving}
               | {p for p, q in pairs if q in moving and not (q in in_run and is_output_node(cv, by_id[q]))})
        for i in moving:
            r = G.rect(by_id[i])
            # where it lands, and the V_GAP below it: a node it would come closer to than V_GAP moves too (the column keeps its gap)
            moved = (r[0], r[1] + down, r[2], r[3] + down + V_GAP)
            add |= {m["id"] for m in solid if m["id"] not in moving and rect_overlap(G.rect(m), moved)}
        add -= moving
        if not add:
            return None if lands_on_reroute(cv, moving, down) else moving
        if (oid in add and c >= out_y) or any((G.rect(by_id[i])[1] + G.rect(by_id[i])[3]) / 2 <= c
                                               for i in add if i in in_run):
            return None
        moving |= {i for i in add if i in by_id}


def move_closure(cv, solid, start, dy, forbid, pairs):
    """The nodes that move by dy (up or down) when the nodes in start move, or None if that reaches a node in forbid.
    Adds, until nothing changes: the nodes joined to a moving node by a horizontal wire (it stays horizontal), the nodes a
    moving node would land on or come within V_GAP of in the direction it moves, and the nodes of its block standing in
    its column within V_GAP of it (a stack moves as a stack and keeps its gaps)."""
    by_id = {m["id"]: m for m in solid}
    block_of = {}
    for b, ids in cv.s["blocks"].items():
        for i in ids:
            block_of.setdefault(i, b)
    moving = set(start)
    while True:
        add = {q for p, q in pairs if p in moving} | {p for p, q in pairs if q in moving}
        for i in moving:
            r = G.rect(by_id[i])
            moved = (r[0], r[1] + dy - (V_GAP if dy < 0 else 0), r[2], r[3] + dy + (V_GAP if dy > 0 else 0))
            add |= {m["id"] for m in solid if m["id"] not in moving and rect_overlap(G.rect(m), moved)}
            b = block_of.get(i)
            if b:
                for m in solid:
                    q = G.rect(m)
                    if (block_of.get(m["id"]) == b and m["id"] not in moving and min(q[2], r[2]) > max(q[0], r[0])
                            and (abs(q[1] - r[3]) <= V_GAP + 1 or abs(r[1] - q[3]) <= V_GAP + 1)):
                        add.add(m["id"])
        add = {i for i in add if i in by_id} - moving
        if not add:
            return None if lands_on_reroute(cv, moving, dy) else moving
        if add & forbid:
            return None
        moving |= add


def _try_move(cv, ids, dy, ok):
    """Moves ids by dy, asks ok(), and moves them back. Whether ok() held and nothing moved landed on a node left in place."""
    cv.translate(sorted(ids), 0, dy)
    try:
        solid = [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute" and m.get("type") not in NOTE_TYPES]
        landed = any(rect_overlap(G.rect(m), G.rect(q)) for m in solid if m["id"] in ids for q in solid if q["id"] not in ids)
        return not landed and ok()
    finally:
        cv.translate(sorted(ids), 0, -dy)


def wire_clear(cv, a, b, skip):
    """Whether a wire drawn from point a to point b passes behind no node (Reroutes and the nodes in skip aside)."""
    pts = G.spline(a, b)
    return not any(G.wire_hits(pts, G.rect(m)) for m in cv.s["nodes"] if cv.placed(m)
                   and m["id"] not in skip and m.get("type") != "Reroute")


def pull_rails(cv, lanes):
    """A rail runs at its source's output height, and nothing brings it near the rails below it: a source (a loader, a
    model chain) placed high leaves a wide empty band. From the lowest rail up, a source's rails move down
    with the source (and the nodes wired level to it) until they are RAIL_GAP above the next rail below, or as close to the nodes
    along the run as a rail may come, whichever is higher. Only when nothing lands on a node and no other rail's source or
    target moves. Returns what moved."""
    out = []
    solid = [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute" and m.get("type") not in NOTE_TYPES]
    pairs = horizontal_pairs(cv)
    for i in sorted(range(len(lanes)), key=lambda i: -lanes[i][0]):
        if i in getattr(cv, "fixed_lanes", set()):
            continue   # a height the plan wrote
        y, oid, slot, targets = lanes[i]
        if abs(cv.out_xy(oid, slot)[1] - y) >= 1:
            continue
        mine = [j for j, ln in enumerate(lanes) if ln[1] == oid]
        if any(abs(cv.out_xy(oid, lanes[j][2])[1] - lanes[j][0]) >= 1 for j in mine):
            continue
        ext = {j: rail_extent(cv, lanes[j][1], lanes[j][3]) for j in range(len(lanes))}
        lows = []
        for j in mine:
            x0, x1, last = ext[j]
            yj = lanes[j][0]
            lows += [ln[0] - P["RAIL_GAP"] - (yj - y) for k, ln in enumerate(lanes) if k not in mine and ln[0] > yj
                     and min(ext[k][1], x1) > max(ext[k][0], x0)]
            lows += [G.rect(m)[1] - LANE_CLEAR_BELOW - (yj - y) for m in solid if m["id"] not in {oid} | last
                     and G.rect(m)[0] < x1 and G.rect(m)[2] > x0 and G.rect(m)[1] > yj]
        if not lows:
            continue
        d = min(lows) - y
        if d < 1:
            continue
        fixed = lane_nodes([ln for k, ln in enumerate(lanes) if k not in mine]) | {t for j in mine for t in lanes[j][3]}
        mv = move_closure(cv, solid, {oid}, d, fixed - {oid}, pairs)
        if not mv:
            continue

        def clear():
            return all(not lane_blockers(cv, lanes[j][0] + d, ext[j][0], ext[j][1], {oid} | ext[j][2],
                                         rail_clear_above(cv, lanes[j][3])) for j in mine)
        if lands_on_reroute(cv, mv, d) or not _try_move(cv, mv, d, clear):
            continue
        cv.translate(sorted(mv), 0, d)
        for j in mine:
            lanes[j][0] += d
        out.append(f"rail of {oid} pulled {round(d)}px down towards the rail below, with {' '.join(sorted(mv))}")
    return out


def lane_nodes(lanes):
    """The sources and targets of the rails already given a height in this layout (what a later move must leave alone)."""
    return {i for ln in lanes for i in [ln[1]] + list(ln[3])}


def level_single(cv, oid, slot, tid, solid, pairs, lanes):
    """A rail with one target whose direct wire passes behind a node: moves the target, or the source, so that the wire is
    horizontal and passes behind nothing; the one moving fewer nodes. Returns (moved ids, dy, what moved) or None."""
    tin = next(l["target_input"] for l in cv.s["links"] if l["origin_id"] == oid and l["origin_slot"] == slot and l["target_id"] == tid)
    fixed = lane_nodes(lanes)
    best = None
    for start, other in ((tid, oid), (oid, tid)):
        if start in fixed:
            continue
        a, b = cv.out_xy(oid, slot), cv.in_xy(tid, tin)
        dy = (a[1] - b[1]) if start == tid else (b[1] - a[1])
        if abs(dy) < 1:
            continue
        moving = move_closure(cv, solid, {start}, dy, {other} | fixed, pairs)
        if moving is None:
            continue
        if _try_move(cv, moving, dy, lambda: wire_clear(cv, cv.out_xy(oid, slot), cv.in_xy(tid, tin), {oid, tid})):
            if best is None or len(moving) < len(best[0]):
                best = (moving, dy, start)
    return best


def lane_at(cv, solid, run, pairs, c, oid, out_y, above, others):
    """Opening a lane at height c along the run: (down, moving) or None (see lane_moving)."""
    if any(abs(sy - c) < P["RAIL_GAP"] for sy in others):
        return None
    if any((G.rect(m)[1] + G.rect(m)[3]) / 2 <= c < G.rect(m)[3] + above for m in run):
        return None   # a node above the lane reaches too close to it
    down = max([c + LANE_CLEAR_BELOW - G.rect(m)[1] for m in run if (G.rect(m)[1] + G.rect(m)[3]) / 2 > c] + [0])
    moving = lane_moving(cv, solid, run, pairs, c, down, oid, out_y)
    return None if moving is None else (down, moving)


def source_move(cv, oid, slot, targets, solid, run, pairs, lanes, lo, hi, others, above):
    """Moving the source (with what it drags along, move_closure) so that the rail runs clear at its output height:
    (height, moving, dy) for the nearest such height, or None. Not farther than RAIL_SHIFT_MAX (as far as a rail leaves its
    output height in hand-made layouts), and not if the move reaches a node along the run, a target, or
    a node of a rail already given its height."""
    a = cv.out_xy(oid, slot)
    x0, x1, last = rail_extent(cv, oid, targets)
    forbid = {m["id"] for m in run} | set(targets) | lane_nodes(lanes)
    cands = {lo, hi} | {sy + g for sy in others for g in (-P["RAIL_GAP"], P["RAIL_GAP"])}
    for m in run:
        r = G.rect(m)
        cands |= {r[1] - LANE_CLEAR_BELOW, r[3] + above}
    for c in sorted((c for c in cands if abs(c) != float("inf") and lo <= c <= hi and 1 <= abs(c - a[1]) <= RAIL_SHIFT_MAX),
                    key=lambda c: (abs(c - a[1]), c)):
        if any(abs(sy - c) < P["RAIL_GAP"] for sy in others):
            continue
        dy = c - a[1]
        moving = move_closure(cv, solid, {oid}, dy, forbid, pairs)
        if moving is None:
            continue
        if _try_move(cv, moving, dy, lambda: not lane_blockers(cv, c, x0, x1, {oid} | last, above)):
            return c, moving, dy
    return None


def open_lane(cv, oid, slot, targets, lanes):
    """Layout: the height of a rail without a written height, moving nodes rather than bending the wire. Returns (height,
    report lines). lanes: the rails of this layout given a height so far, [[height, source, output, targets]]; opening a
    lane moves them with the nodes.
    1. The output height, if the run there is clear (and on the rail's side of the eye line).
    2. A rail with one target: the target or the source moves so that a direct horizontal wire passes behind nothing.
    3. At the output height, by moving nodes: either a lane is opened (the nodes along the run whose centre is below it
       move down, lane_moving) or the source moves to a clear height (source_move). The one moving fewer nodes.
    4. Not for a loader of a model, clip or vae (it heads its rail): a raising Reroute to the nearest clear height within
       RAIL_SHIFT_MAX, then a lane opened near the output height.
    Otherwise it stops and says what is in the way."""
    a = cv.out_xy(oid, slot)
    extra = [(y, *rail_extent(cv, o, tg)[:2], (o, sl)) for y, o, sl, tg in lanes]
    x0, x1, last = rail_extent(cv, oid, targets)
    above = rail_clear_above(cv, targets)
    lo, hi = rail_side(cv, oid, slot, x0, x1)
    tlo, thi = type_bounds(cv, oid, slot, targets, lanes)
    lo, hi = max(lo, tlo), min(hi, thi)
    others = [sy for sy, sx0, sx1, root in rail_spans(cv) + extra if root != (oid, slot) and min(sx1, x1) > max(sx0, x0)]
    if lo <= a[1] <= hi and not lane_blockers(cv, a[1], x0, x1, {oid} | last, above) and not any(abs(sy - a[1]) < P["RAIL_GAP"] for sy in others):
        return a[1], [f"rail height {round(a[1])}: at the output height"]
    solid = [m for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute"]
    run = [m for m in solid if m["id"] not in {oid} | last and G.rect(m)[0] < x1 and G.rect(m)[2] > x0]
    pairs = horizontal_pairs(cv)

    def apply(ids, dy):
        cv.translate(sorted(ids), 0, dy)
        for ln in lanes:
            if ln[1] in ids and all(t in ids for t in ln[3]):
                ln[0] += dy
    if len(targets) == 1:
        tid = targets[0]
        tin = next((l["target_input"] for l in cv.s["links"] if l["origin_id"] == oid and l["origin_slot"] == slot
                    and l["target_id"] == tid), None)
        if tin is not None and wire_clear(cv, a, cv.in_xy(tid, tin), {oid, tid}):
            return a[1], [f"rail height {round(a[1])}: wired directly (the direct wire passes behind nothing)"]
        lv = level_single(cv, oid, slot, tid, solid, pairs, lanes)
        if lv:
            moving, dy, start = lv
            apply(moving, dy)
            y = cv.out_xy(oid, slot)[1]
            return y, [f"rail height {round(y)}: wired directly, made horizontal by moving the {'target' if start == tid else 'source'} "
                       f"{round(abs(dy))}px {'up' if dy < 0 else 'down'}: {' '.join(sorted(moving))}"]
    opts = []
    if lo <= a[1] <= hi:
        ln = lane_at(cv, solid, run, pairs, a[1], oid, a[1], above, others)
        if ln:
            opts.append((len(ln[1]), 0, "lane", ln))
    sm = source_move(cv, oid, slot, targets, solid, run, pairs, lanes, lo, hi, others, above)
    if sm:
        opts.append((len(sm[1]), 1, "source", sm))
    if opts:
        # fewer nodes moved first, then the shorter move (a lane opened far below moves the band away)
        dist = lambda o: o[3][0] if o[2] == "lane" else abs(o[3][2])
        _, _, kind, v = min(opts, key=lambda o: (o[0], dist(o), o[1]))
        if kind == "lane":
            down, moving = v
            out = [f"rail height {round(a[1])}: at the output height, opening a lane there"]
            if down:
                apply(moving, down)
                out.append(f"moved {round(down)}px down to open the lane: {' '.join(sorted(moving))}")
            return a[1], out
        c, moving, dy = v
        apply(moving, dy)
        return c, [f"rail height {round(c)}: at the output height, moving the source {round(abs(dy))}px "
                   f"{'up' if dy < 0 else 'down'}: {' '.join(sorted(moving))}"]
    in_way = " ".join(m["id"] for m in lane_blockers(cv, a[1], x0, x1, {oid} | last, above))
    if cv.is_model_loader(cv.node(oid)) and not any(ln[1] == oid for ln in lanes) and not tlo <= a[1] <= thi:
        t = rail_type(cv, oid, slot)
        rk = RAIL_TYPE_ORDER.index(t) if t in RAIL_TYPE_ORDER else len(RAIL_TYPE_ORDER)
        down = a[1] < tlo
        other = next((ln[1] for ln in lanes if cv.is_model_loader(cv.node(ln[1])) and rail_type(cv, ln[1], ln[2]) in RAIL_TYPE_ORDER
                      and (RAIL_TYPE_ORDER.index(rail_type(cv, ln[1], ln[2])) < rk) == down), None)
        hint = (f": e.g. put {oid} {'below' if down else 'above'} {other}" + (f", or stack {other} {oid}" if down else f", or stack {oid} {other}")) if other else ""
        raise Stop(f"the {t} rail of {oid} must run {'below' if down else 'above'} the other loaders' rails "
                   f"(rails go model, vae, clip from the top), but its output is on the other side: stack the loaders "
                   f"model, vae, clip from the top{hint}")
    if cv.is_model_loader(cv.node(oid)) and not any(ln[1] == oid for ln in lanes):
        raise Stop(f"no room for the rail of {oid} at its output height: in the way {in_way or '(other rails)'}; no lane "
                   f"opens there without cutting a horizontal wire, and {oid} cannot move without reaching the run or "
                   f"a target. A loader heads its rail: place it where its output height is clear along the run "
                   f"(a rail of model, clip or vae runs above the samplers' top)"
                   + (f", e.g. put {oid} above {in_way.split()[0]}" if in_way else ""))
    try:
        y, how = rail_height(cv, oid, slot, targets, extra, (tlo, thi))
    except Stop:
        y, how = None, ""
    # a conditioning rail lifted from below the samplers to above them may go farther than RAIL_SHIFT_MAX
    # (620px in a layout of a Z-Image Turbo workflow the skill author arranged)
    cap = float("inf") if rail_type(cv, oid, slot) == "CONDITIONING" and a[1] > hi else RAIL_SHIFT_MAX
    if y is not None and abs(y - a[1]) <= cap:
        return y, [f"rail height {round(y)}: {how}"]
    best = None
    cands = {G.rect(m)[3] + above for m in run} | {sy + g for sy in others for g in (-P["RAIL_GAP"], P["RAIL_GAP"])}
    for c in sorted(cands, key=lambda c: (abs(c - a[1]), c)):
        if abs(c - a[1]) > RAIL_SHIFT_MAX or not lo <= c <= hi:
            continue
        ln = lane_at(cv, solid, run, pairs, c, oid, a[1], above, others)
        if ln and (best is None or (ln[0], len(ln[1])) < (best[0], len(best[2]))):
            best = (ln[0], c, ln[1])
    if best is None:
        raise Stop(f"no room for the rail of {oid} near its output height: in the way {in_way or '(other rails)'}; "
                   f"the nearest clear height is {'none' if y is None else str(round(abs(y - a[1]))) + 'px away'}, and no lane "
                   f"can be opened within {RAIL_SHIFT_MAX}px without cutting a horizontal wire or moving a node above the rail. "
                   f"Place the source or the targets so the run is shorter")
    down, c, moving = best
    out = [f"rail height {round(c)}: opened a lane {round(abs(c - a[1]))}px {'above' if c < a[1] else 'below'} the output height, "
           f"since the nearest clear height is {'none' if y is None else str(round(abs(y - a[1]))) + 'px away'}"]
    if down:
        apply(moving, down)
        out.append(f"moved {round(down)}px down to open the lane: {' '.join(sorted(moving))}")
    return c, out


def lane_crossings(cv, upper, lower):
    """How many wires of two rails cross when `upper` runs above `lower` ([height, source, output, targets] each):
    the rise from each source and the drop to each target, crossing the other rail's run."""
    n = 0
    for a, b in ((upper, lower), (lower, upper)):
        bx0, bx1, _ = rail_extent(cv, b[1], b[3])
        legs = [(G.rect(cv.node(a[1]))[2], cv.out_xy(a[1], a[2])[1])]
        for t in a[3]:
            tin = next((l["target_input"] for l in cv.s["links"] if l["target_id"] == t and l["origin_id"] == a[1]
                        and l["origin_slot"] == a[2]), None)
            legs.append((G.rect(cv.node(t))[0], cv.in_xy(t, tin)[1] if tin is not None else G.rect(cv.node(t))[1]))
        for x, y in legs:
            if bx0 < x < bx1 and min(a[0], y) < b[0] < max(a[0], y):
                n += 1
    return n


def swap_by_crossings(cv, lanes):
    """Rails other than MODEL, VAE and CLIP: two rails whose runs overlap swap heights when fewer wires cross that way
    and both heights stay clear for the rail that takes them. Returns the pairs swapped."""
    done = []
    free = [i for i, ln in enumerate(lanes) if rail_type(cv, ln[1], ln[2]) not in RAIL_TYPE_ORDER]
    for _ in range(len(free)):
        changed = False
        for i in free:
            for j in free:
                a, b = lanes[i], lanes[j]
                if i == j or a[0] >= b[0]:
                    continue
                ax0, ax1, alast = rail_extent(cv, a[1], a[3])
                bx0, bx1, blast = rail_extent(cv, b[1], b[3])
                if min(ax1, bx1) <= max(ax0, bx0):
                    continue
                now = lane_crossings(cv, a, b)
                if not now or lane_crossings(cv, [a[0]] + b[1:], [b[0]] + a[1:]) >= now:
                    continue
                ya, yb = a[0], b[0]
                lo_a, hi_a = rail_side(cv, a[1], a[2], ax0, ax1)
                lo_b, hi_b = rail_side(cv, b[1], b[2], bx0, bx1)
                if not (lo_a <= yb <= hi_a and lo_b <= ya <= hi_b):
                    continue
                if lane_blockers(cv, yb, ax0, ax1, {a[1]} | alast, rail_clear_above(cv, a[3])) or \
                        lane_blockers(cv, ya, bx0, bx1, {b[1]} | blast, rail_clear_above(cv, b[3])):
                    continue
                a[0], b[0] = yb, ya
                done.append((i, j))
                changed = True
        if not changed:
            break
    return done


def rail_raise_x(cv, ox1):
    """x of a raising Reroute: its left edge on the left edge of the column right of the source (as in hand-made layouts),
    or half the column gap right of the source when there is no such column."""
    lefts = [G.rect(m)[0] for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute"
             and ox1 + H_GAP / 3 <= G.rect(m)[0] <= ox1 + H_GAP + REROUTE_W / 2]
    return min(lefts) if lefts else ox1 + H_GAP / 2


def rail_lower_x(cv, x0, tid):
    """x of a lowering Reroute before a target whose left edge is x0: its right edge on the right edge of the column left
    of the target (as in hand-made layouts), or one column gap left of the target when there is no such column. The
    column may stand up to a wide gap away (a widened gap, or two group frames between them)."""
    rights = [G.rect(m)[2] for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute" and m["id"] != tid
              and x0 - GAP_WIDE - REROUTE_W / 2 <= G.rect(m)[2] <= x0 - H_GAP / 3]
    return (max(rights) if rights else x0 - H_GAP) - REROUTE_W


def rail_free_x(cv, x, y, step):
    """x for a Reroute at height y, moved (right for step 1, left for -1) out from below a node that grows in ComfyUI
    (a sampler, a video): a Reroute there would be hidden when it grows."""
    for _ in range(20):
        box = (x, y - REROUTE_H / 2, x + REROUTE_W, y + REROUTE_H / 2)
        over = [G.rect(m) for m in cv.s["nodes"] if cv.placed(m) and m.get("type") != "Reroute" and grows(cv, m)
                and in_grow_room(cv, m, box)]
        if not over:
            return x
        x = (max(r[2] for r in over) + 1) if step > 0 else (min(r[0] for r in over) - REROUTE_W - 1)
    return x


def _frame_would_hit_another(cv, g, rect):
    """Whether widening group g's frame to take in rect would make it overlap another group's frame."""
    b = g.get("bounding")
    if not b:
        return False
    pad = 40
    x0, y0 = min(b[0], rect[0] - pad), min(b[1], rect[1] - pad)
    x1, y1 = max(b[0] + b[2], rect[2] + pad), max(b[1] + b[3], rect[3] + pad)
    for o in cv.s["groups"]:
        ob = o.get("bounding")
        if o is g or not ob:
            continue
        if min(x1, ob[0] + ob[2]) > max(x0, ob[0]) and min(y1, ob[1] + ob[3]) > max(y0, ob[1]):
            if not (min(b[0] + b[2], ob[0] + ob[2]) > max(b[0], ob[0]) and min(b[1] + b[3], ob[1] + ob[3]) > max(b[1], ob[1])):
                return True
    return False


def one_target_height(cv, oid, slot, tins, spec, y, notes, k):
    """A rail written above or below with one target further that way than the written height: it runs at the target's
    input height, so its Reroute lowers all the way and the wire into the target is horizontal (a
    Reroute stopped halfway, and the wire from it slanted into the target). Only when that run is clear."""
    if len(tins) != 1:
        return y
    tid, tin = tins[0]
    ty = cv.in_xy(tid, tin)[1]
    if not ((spec == "below" and ty > y + 1) or (spec == "above" and ty < y - 1)):
        return y
    ox1 = G.rect(cv.node(oid))[2]
    band = (ox1 + 1, ty - REROUTE_H / 2, G.rect(cv.node(tid))[0] - 1, ty + REROUTE_H / 2)
    if any(rect_overlap(G.rect(m), band) for m in cv.s["nodes"]
           if cv.placed(m) and m["id"] not in (oid, tid) and m.get("type") != "Reroute"):
        return y
    notes.append(f"{'  line ' + str(k) + ': ' if k is not None else ''}rail into its one target {tid} at the target's input height {round(ty)} (written {spec})")
    return ty


def do_rail(cv, args):
    if "to" not in args:
        raise Stop(RAIL_USAGE)
    k = args.index("to")
    head, targets = args[:k], args[k + 1:]
    if not head or not targets:
        raise Stop(f"rail is incomplete: {RAIL_USAGE}")
    oid, slot = cv.port_out(head[0])
    if not cv.placed(cv.node(oid)):
        raise Stop(f"the rail source {oid} is not placed yet")
    a = cv.out_xy(oid, slot)
    spec = head[1] if len(head) > 1 else "auto"
    if spec in ("above", "below", "level") and len(head) < 3:
        raise Stop(f"write rail ... {spec} <{'output' if spec == 'level' else 'unit'}> to ...")
    n_head = {"auto": 1, "at": 4}.get(spec, 3)
    if len(head) > n_head:
        extra = " ".join(head[n_head:])
        raise Stop(f"rail does not take \"{extra}\" (write {RAIL_USAGE})")
    tg = []
    for t in targets:
        tid, tin = cv.port_in(t)
        tg.append((cv.bbox([tid])[0], tid, tin))
    tg.sort()
    if spec in ("above", "below", "level") and not PLAN_RAILS and all(wire_clear(cv, a, cv.in_xy(tid, tin), {oid, tid}) for _, tid, tin in tg):
        # a written height where every target is reached directly, behind nothing: the rail is drawn as one without a
        # height (it wires them directly), not down and back up to that height
        cv.out.append(f"rail {head[0]}: every target is reached directly; the written height ({spec} {head[2]}) is not used")
        spec = "auto"
    if spec == "auto":
        y, how = rail_height(cv, oid, slot, [t for _, t, _ in tg])
        cv.out.append(f"rail height {round(y)}: {how}")
    elif spec == "at":
        # layout: the height open_lane chose (the layout checked it is still clear after every rail was given its height)
        if not getattr(cv, "in_layout", False):
            raise Stop(f"unknown rail height at (above below level)")
        y = float(head[2])
    elif spec == "above":
        y = cv.bbox(cv.unit(head[2]))[1] - V_GAP
    elif spec == "below":
        y = cv.bbox(cv.unit(head[2]))[3] + V_GAP
    elif spec == "level":
        x_id, x_slot = cv.port_out(head[2])
        y = cv.out_xy(x_id, x_slot)[1]
    else:
        raise Stop(f"unknown rail height {spec} (above below level; or leave it out)")
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

    if spec in ("above", "below") and abs(y - a[1]) >= 1 and not PLAN_RAILS:
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

    if spec in ("above", "below"):
        y = one_target_height(cv, oid, slot, [(t, i) for _, t, i in tg], spec, y, cv.out, None)

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
        x_r0 = rail_raise_x(cv, ox1)
        fx = rail_free_x(cv, x_r0, y, 1)
        if fx + REROUTE_W <= min(x for x, _, _ in tg) - H_GAP / 3:
            x_r0 = fx
        r0 = reroute(x_r0)
        cv.add_link(oid, slot, r0, "")
        prev = (r0, 0)
        last_x = x_r0 + REROUTE_W
    cur_r, cur_x, cur_g = None, None, None
    group_of = {}
    for g in cv.s["groups"]:
        for i in g["members"]:
            group_of.setdefault(i, g)

    def direct_ok(tid, tin, src=None):
        """Whether a direct wire from src (default: the source output) passes behind no node."""
        start = a if src is None else cv.out_xy(src, 0)
        return wire_clear(cv, start, cv.in_xy(tid, tin), {oid, tid})

    # targets from the left. Until the rail lowers into a target, a target the source reaches directly is wired from the
    # source (as is a target in the column right of the source). From the first lowering Reroute on, every target takes
    # the value from the rail: from a Reroute placed before it, or straight from the rail when its input is at the rail's height
    lowered = False
    for x0, tid, tin in tg:
        if x0 < ox1:
            raise Stop(f"rail target {tid} stands left of the source {oid}'s right edge (the wire would go back): "
                       f"place {tid} right of {oid}, or wire it directly")
        # a target the source reaches directly is wired directly only when the canvas chooses the rails; a rail the plan
        # writes is drawn as written (wiring it directly drew one wire across the whole workflow)
        if not lowered and not getattr(cv, "rail_no_direct", False) and not PLAN_RAILS and direct_ok(tid, tin):
            cv.add_link(oid, slot, tid, tin)
            continue
        if prev[0] != oid and abs(cv.in_xy(tid, tin)[1] - y) < 1 and direct_ok(tid, tin, prev[0]):
            cv.add_link(prev[0], prev[1], tid, tin)
            continue
        # a rail into one target after its raising Reroute: when a wire from that Reroute reaches the target passing behind
        # no node, a lowering Reroute would follow it straight, which the rules call Bad (consecutive Reroutes: one is enough)
        if (prev[0] != oid and not lowered and (x0, tid, tin) == tg[-1] and direct_ok(tid, tin, prev[0])
                and not any(t2 == tid for _, t2, _ in tg[:-1])):
            cv.add_link(prev[0], prev[1], tid, tin)
            continue
        rx = rail_lower_x(cv, x0, tid)
        rx0 = rx
        # not below a node that grows: to its left if that stays right of the rail's last Reroute, else to its right if
        # that stays left of the target, else where it is
        for step in (-1, 1):
            fx = rail_free_x(cv, rx, y, step)
            if fx == rx or (last_x < fx and fx + REROUTE_W <= x0 - H_GAP / 3):
                rx = fx
                break
        if rx != rx0:
            cv.out.append(f"rail into {tid}: its lowering Reroute stands {abs(round(rx - rx0))}px {'left' if rx < rx0 else 'right'} "
                          f"of where it would, out from below a node that grows; the wire from it to {tid} slants")
        # rails from one node's outputs run 20px apart: their lowering Reroutes into one target would overlap, so a later
        # one steps left of the Reroute already there (a staircase), as long as it stays right of the rail's last Reroute
        def hits_reroute(x):
            box = (x, y - 0.7 * G.SLOT, x + REROUTE_W, y - 0.7 * G.SLOT + REROUTE_H)
            return any(m.get("type") == "Reroute" and cv.placed(m) and rect_overlap(G.rect(m), box) for m in cv.s["nodes"])
        tries = 0
        while hits_reroute(rx) and tries < 4 and rx - (REROUTE_W + 10) > last_x:
            rx -= REROUTE_W + 10
            tries += 1
        g = group_of.get(tid)
        if cur_r is not None and rx - cur_x < REROUTE_W + H_GAP / 2 and cur_g is g:
            cv.add_link(cur_r, 0, tid, tin)
            continue
        if rx <= last_x:
            if prev[0] == oid or (cur_r is None and not lowered):
                # the target stands in the column right of the source: wired from the source, not from the raising Reroute
                cv.add_link(oid, slot, tid, tin)
            else:
                cv.add_link(prev[0], prev[1], tid, tin)
            continue
        r = reroute(rx)
        cv.add_link(prev[0], prev[1], r, "")
        cv.add_link(r, 0, tid, tin)
        if g is not None and not _frame_would_hit_another(cv, g, G.rect(cv.node(r))):
            # it lowers into the group: it belongs to it, so the frame takes the rail in and the wire stays off the title band.
            # Not when taking it in would widen the frame into another group's frame (groups must not overlap)
            g["members"].append(r)
        prev, cur_r, cur_x, cur_g, last_x = (r, 0), r, rx, g, rx + REROUTE_W
        lowered = True
    made_all = set(made)
    # remove, from the end, Reroutes left connected to nothing (e.g. because every target was wired directly)
    for rid in reversed(list(made)):
        if not any(l["origin_id"] == rid for l in cv.s["links"]):
            cv.s["links"] = [l for l in cv.s["links"] if l["target_id"] != rid]
            cv.s["nodes"] = [n for n in cv.s["nodes"] if n["id"] != rid]
            made.remove(rid)
    for g in cv.s["groups"]:
        g["members"] = [i for i in g["members"] if i not in made_all or i in made]
    cv.relink()
    cv.update_groups()
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


# ---------------------------------------------------------------- report page

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


def _report_order(work):
    """The order written with `order`. Without it: canvases made with `new X from Y` follow the one they were made from;
    the one the most others came from is first."""
    names = work.names()
    written = [n for n in work.cfg.get("order") or [] if n in names]
    if written:
        return written + [n for n in names if n not in written]
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

    def visit(n):
        if n in out:
            return
        out.append(n)
        for m in sorted(kids[n], key=lambda m: (-count(m), m)):
            visit(m)
    for n in sorted((n for n in names if n not in parent), key=lambda n: (-count(n), n)):
        visit(n)
    out += [n for n in names if n not in out]   # a loop of `from`s
    return out


def report_page(work, lang="en"):
    """Every command of every canvas, the state after it, and the check problems at that point.
    Commands that change nothing on the drawing (building before anything is placed) are shown together as one step."""
    canvases = []
    oi = work.oi
    for name in _report_order(work):
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
        canvases.append({"name": name, "tab": (work.cfg.get("tab_group") or {}).get(name), "defs": defs.items, "nodes": nodes_t.items, "wires": wires_t.items,
                         "groups": groups_t.items, "problems": probs.items, "steps": steps, "walk": walk_view(final),
                         "review": _review_names(final, final.s.get("review")), "hand": final.s.get("hand_placed") or []})
    src = work.cfg.get("source")
    odefs = _Intern()
    original = None
    if src and Path(src).is_file():
        original = _original_view(src, oi, odefs)
        original["defs"] = odefs.items
        original.update(_original_counts(work, src))
    return RPT.build(canvases, original, lang)


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


def _review_names(cv, rev):
    """The review with each row's nodes by name (Reroutes left out), for the report page."""
    if not rev:
        return rev
    rev = dict(rev)
    rev["rows"] = [dict(r, names=list(dict.fromkeys(_plain_name(cv, i) for i in r.get("ids") or []
                                                    if i in cv.nodes and cv.nodes[i].get("type") != "Reroute")))
                   for r in rev.get("rows") or []]
    return rev


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
    (report.py writes the sentence in the page's language)."""
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
