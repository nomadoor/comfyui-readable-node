---
name: comfyui-readable-node
description: Builds a ComfyUI workflow (JSON) into a form people can read easily (Readable Node). Use it when the user mentions Readable Node, asks to make a ComfyUI workflow readable or tidy, takes an existing workflow apart to rebuild it, or builds a new workflow. Do not hide nodes, do not hide wires (turn wireless links back into wires), left to right, 1 task per workflow, fewer custom nodes, appropriate colouring.
license: MIT
metadata:
  version: "0.0.3"
---

# Readable Node

Build ComfyUI workflows that are easy to read. There are two situations.
- Take a given workflow apart and rebuild it so it is easy to read.
- When building a new workflow, also build it so it is easy to read.

In both, write the understanding first, then build on the canvas (scripts/canvas.py) with moves you write as lines. You are not fixing the original graph bit by bit.

## What Readable Node is

The items are ordered by how much they matter when a person reads a workflow. When building, think in this order too.

1. **Do not hide nodes.** Expand subgraphs, open collapsed nodes, and do not overlap nodes.
2. **Do not hide wires.** Turn wireless links (Set/Get, Anything Everywhere, hidden links, and the like) back into wires.
3. **Left to right.** Flow from left to right in processing order. Do not stretch too far towards the lower right.
4. **1 task = 1 workflow.** One workflow is one thing the user wants to do.
5. **Remove custom nodes as far as possible.** What can be built with core nodes is built with core.
6. **Colour appropriately.** Colour shows which function a node belongs to.

There are three goals.
- The reader can follow the processing along a single line (can trace the details).
- The whole picture of the processing can be grasped at a glance (the shape is clear without reading the details).
- The workflow, as a tool, is easy to rearrange and easy to reuse.

The rules in the references serve these principles and goals; most rules name the one they serve ("Why"). When a case is not covered by a rule, decide by them. Where a rule says "Undecided", it is not decided yet: do not fill it with a rule or threshold of your own; report what you did and what you were unsure about. The words are defined in references/glossary.md.

## Language

- Everything written for the user is written in the user's language: the conversation (progress messages, the report), Notes (including the part after "Markdown Note: " in the title), the Walkthrough, and the part after the colon in the title of a value node or a node loading an image.
- Things from ComfyUI stay in English.
  - Node names: ComfyUI's display names (display_name in object_info). Make them the same as the node titles on the canvas.
  - ComfyUI terms: latent, conditioning, sampler, cfg, steps, widget names and so on. Also phrases that people using ComfyUI use normally, such as Text to Image, Image to Video, Hires.fix. Do not reword them.
  - Model names, folder names, file names.

## Division of work

**What you decide (judgement)**: understanding, how to split, what to keep, remove or replace, rebuilding custom nodes, what goes where, what to align, rails, groups, colours for added functions, Notes.

**What the canvas does (things with exactly one answer)**: node sizes, calculating positions, the default colours of loaders, LoRAs and Notes, group padding, checks (check), export. When reading the original (`canvas open`), it fixes what has exactly one way of fixing, such as turning wireless links back into wires, and applying the official node-replacement list and replacements that give the same calculation. It returns everything it did.

**How to use the canvas**
- Do not write coordinate numbers. Point at things: "put it to the right of A", "make the wire horizontal", "align the top edges". The canvas does the calculation. Only what you point at moves.
- Every call of the tool takes time. Do in one call what can be done in one call (build with `run` on build.txt, arrange with `layout` on layout.txt). Read things side by side, at once.

## What not to do

- Run ComfyUI without being asked by the user.
- Decide that your layout is good because its picture looks good to you (an AI's eye sees packed forms as good). Look at the picture to find what to fix (step 6); the check list and the review by another agent judge it.
- Search the disk (`find /`, the user's folders). The source of a node is read as in references/replacements.md.
- Wait for another agent by repeating `sleep`. Wait for its notice that it has finished.
- Copy the original as it is. Read what each part does with its values (references/content.md).

## Steps

`S` is the path of scripts/. Choose one working folder `W` inside the folder where the results go (the one the user named; otherwise next to the original), and type every canvas move as `python3 $S/canvas.py --dir $W <move>`. Below, this is written `canvas`. The list of moves, their syntax and the detailed behaviour (undo, placements calculated only once, block, and so on) are at the top of canvas.py (`python3 $S/canvas.py` prints them): read it once before step 4.
- Put every file you make while working inside `W`: plan files (build.txt for building, layout.txt for arranging: "the plan" is layout.txt), Note files, workflows or object_info you fetch to read, notes. Only the exported workflows and the report page go outside `W`. `canvas finish` deletes the files of `W` it knows (what it wrote, the plan and Note files, understanding.md) and names the others it left: delete only those, one by one. Do not delete `W` with a recursive delete.

Moves marked "(when there is an original)" are only for rebuilding a given workflow. When building a new one, skip them.

When the user asks for it fast, skip steps 9 and 10 (the review and the report page), finish with `canvas finish fast`, and say in the report that it was not reviewed.

1. **Read the original (when there is an original)**  
   `canvas open <workflow.json> <object_info URL or saved object_info JSON>`
   - When a saved JSON is given, the official node-replacement list is not used.
   - Read everything it returns (wireless links turned back, replacements, what was removed, outputs, disabled nodes, switches, custom nodes, models). What it does not mention is not covered by it: a node of the original that appears nowhere in what it returned is read by you.
   - Take all nodes at once with `canvas src all` (do not type `src node` many times). Read from the outputs upstream, tracing back from the sampler.

2. **Write the understanding document (`$W/understanding.md`)**  
   The understanding of the workflow, written before building. Write the first version after reading, and revise it while building. Keep what you revised as well.
   - Read references/content.md, references/techniques.md, and the "Content" and "Notes" parts of references/examples.md before writing (its "Layout" part comes in step 5).
   - What to write is in references/understanding.md. For every node, write what it does with its values here.

   When the understanding document is written, tell the user once, without waiting for an answer: what the workflow does, how many workflows it will be split into, and what will be replaced.

3. **Split**  
   Following the split in the understanding document, make one canvas per workflow (`canvas new <name>`, `canvas use <name>`). How many files there are after splitting is Undecided; how they are named is in content.md ("Split"). One canvas becomes one workflow JSON.
   - Workflows of the same form that differ only in part (another input, an added stage): build one, then make the others with `canvas new <name> from <canvas>`, so the shared nodes keep their ids. Write what they share in one plan file, and in each canvas's plan only `include <that file>` and the lines of the part that differs. A fix to the shared part is made once.

4. **Build (per canvas)**  
   The core first, then the added techniques.
   - This skill has no per-model templates: for how to build the core, refer to a workflow for the same use on nomadoor's site (Comfy-with-ComfyUI). `canvas refs <word>` lists, newest first, the workflows whose path or article title contains the word (a model name such as "flux" or "wan", or a use such as "inpaint"). Old workflows are sometimes built wrongly, so for the same use, choose the newer one. Refer only to how the core is built; do not copy the layout.
   - Write all the build moves in build.txt and run them once with `canvas run build.txt`. If it stops, fix that line and run the rest. Once the nodes are on the canvas, `canvas guide` prints the lines of techniques.md and replacements.md (and of the rules and examples) that name them: read the first two before going on.
   - An original node is `copy <original id> …` (copies type, values and mode; does not copy wires). A new node is `add <type>` (a type in object_info). Values are `set`. Wires are `link <A>.<output> <B>.<input> …`; a wire into a widget (seed, text) gives that widget its input. `canvas node <id>` shows a node's input and output names: look before writing the lines. Connect only what is needed.
   - When the build is done (when there is an original), compare with the original using `canvas diff` (values, inputs the user puts in, outputs, mode). One item at a time: if it is an intended difference, note the reason; if not, fix it.
   - Fix the content yourself. Compare with the understanding document and look for what falls under references/content.md. Also look for mistakes born from replacement and for lost functions.

5. **Arrange (per canvas)**  
   After reading references/readable-form.md. In this order:
   1. Run `canvas guide` again and read the lines of the rules and examples it prints for the nodes of this canvas.
   2. Paste the lines of `canvas core <the first stage's sampler>` at the top of layout.txt. They are a draft of the core's block: adjust them to this workflow (a part the usual form lacks is named in a comment, to be placed by relations).
   3. For each grouping of the understanding document, write `block <name> <id> …` and the arrangement inside it.
   4. Run `canvas between layout.txt` to see the wires between blocks and the outputs handed out to several blocks. A value handed out to several stages is written as a `rail` (readable-form.md, "Wires").
   5. Write the arrangement between blocks: each block against the block it is wired to (`put <block> left|right <block> wire`). Groups, colours and the titles of value nodes and of nodes loading an image go in the same file (readable-form.md, "Groups and colour", "Names"); the canvas reads every group line before it places anything, so where in the file a group line stands does not change the layout.
   6. Run `canvas layout layout.txt`.

   How to place:
   - A node's column comes from the node it feeds (just left of it); its row comes from the rows in readable-form.md. Neither comes from a node that merely stands nearby.
   - Place by relations only (put, row, stack, align, level, inputs, rail). No numbers: gaps and widths are the canvas's; where a rail runs is in readable-form.md, "Wires". A place one reference does not give takes two (`put <unit> right <A> below <B>`).
   - Copy a shape with `canvas shape`. Split workflows give the same function the same layout (`canvas new <name> from <canvas>`).

6. **Look, and fix**  
   1. Draw the picture with `canvas render $W/look.png` and look at it. Does it look as if a person arranged it? A node far from what it feeds, a wire running a long way, an empty area, a crowded area: fix the plan.
   2. Read what `canvas layout` returned, as it is: each line names a rule of this skill that a form breaks (its file and section). Fix each in the plan; look at it on the picture. It stops nothing. `canvas check` lists every notice.
   3. Rewrite the plan lines for everything to fix together and run `canvas layout` again (not item by item). `rail` stops when its line cannot be drawn (a target stands left of the source, or rails keep blocking each other's height); fix what it names. A rail that runs behind a node or has a Reroute that does nothing is drawn, and the check names it.
   4. Repeat 1–3 until nothing is left to fix.

   Leaving something:
   - Leave an item only after trying, with what was tried and what happened.
   - When no relation gives a place, leave it and report which two nodes you could not relate.
   - The check list finds only what can be counted; an empty list does not mean the layout is right. The review (step 9) checks the rest.

7. **Notes**  
   Read references/notes.md. Export the canvas (a draft for the Note writer; the final export is step 8), then start a separate agent (a subagent) and give it: the exported workflow (a node keeps its number from one export to the next; a node the canvas named, such as a Reroute it made, gets a number of its own), `$W/understanding.md` (E lists the candidates), and references/notes.md, with this request: "Write the Notes for this ComfyUI workflow following notes.md: the one or two sentences at the top of the overview Note, and the Notes on part of the processing, one Markdown file each in $W/notes/, in <the user's language>. Write from what happens to the user, not from the nodes. Write nothing that the graph shows. Point at nodes by their display names. Each file holds only the text: no heading for the title. In your final message, list each file with the id of the node it explains and its title (one of the three in notes.md)." If no separate agent can be started, write them yourself and say so in the report.
   - Add the models list from `canvas models` under the overview sentence.
   - Place each Note where notes.md, "Where to place", says, with `note <file> <right|left|below|above> <node>` in the plan (it takes what `put` takes: an alignment, a second reference), give it its title with `title <Note id> "Markdown Note: …"` (the file holds only the text), and run `canvas layout`. When the place written is not clear, the canvas says what the Note lands on.
   - One Note at a time, check that the node on the 🔗 line and the topics are about the same node; a topic about another node moves to that node's Note.

8. **Export and compare**  
   For each canvas, `canvas export <name>.json`. (When there is an original) run `canvas diff` again on every canvas, look at the differences one by one, and if one is not intended, fix it and export again.

9. **Review (another agent)**  
   Read references/review.md and follow it: draw the picture for each canvas, give the brief to a new agent, fix the rows one at a time, answer every row, export again and register the review with `canvas review`.

10. **Write the report page (`report.html`)**  
   Write the page where the user checks the result, as one HTML file. The page has three views. The canvas makes Original (the original workflow) and Rebuilt (what was done on the canvases, one move at a time). You write only the Walkthrough.
   - For each canvas, write `$W/walk_<canvas>.md`, select the canvas with `canvas use <canvas>`, and register it with `canvas walk $W/walk_<canvas>.md` (the file's form is at the top of canvas.py). How to write it is in references/notes.md, "Walkthrough".
   - Set the order of the canvases on the page with `canvas order <canvas> …`: the basic workflow on the left, then those that add to it (t2i before i2i and edit, the normal version before its fast version), parts last. Workflows of the same form that differ only in values (one per model) share one tab: write them next to each other as `<tab>/<canvas>`.
   - Finally, write the page with `canvas report report.html <the user's language code>` (`ja`, `en`, `zh` and so on).

11. **Report in the conversation**  
    First, a few lines of summary: what was produced, what was changed, what the user should check. The path of the report page.
    - Below that, the details: the understanding document, how it was split, what was changed and why (what was removed, what was replaced, the author's mistakes that were fixed), the diff differences and their reasons, what was left in check and why, the reviewer's one-line reply for each canvas (or that it was not reviewed), and the review rows that were left and why.
    - `canvas finish` deletes the files of the working folder it knows, including the understanding document. Take what the report needs from it first, then run `canvas finish`, then give the report. While something is missing (an export, a review, an answer to a review row, an up-to-date report page) it stops, says what, and deletes nothing. When the environment keeps the working folder, it only lists the files: say so in the report.

## References

- references/glossary.md: definitions of the words.
- references/understanding.md: what to write in the understanding document.
- references/content.md: the rules about content (splitting, replacing, keeping, removing).
- references/techniques.md: building techniques (hard-to-read forms, and forms rebuilt to be readable).
- references/replacements.md: the replacement dictionary (custom nodes and deprecated nodes, things that may be removed, things to keep) and how to find the source.
- references/readable-form.md: the layout rules (nodes, wires, flow and position, groups and colour, names).
- references/notes.md: how to write Notes and the Walkthrough, and where to place Notes.
- references/examples.md: examples (how the rules applied in real workflows), and the list of Undecided items.
- references/review.md: the review after export (what you do, and the brief for the agent that reviews).
