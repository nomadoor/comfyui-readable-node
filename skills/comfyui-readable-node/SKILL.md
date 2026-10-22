---
name: comfyui-readable-node
description: Builds a ComfyUI workflow (JSON) into a form people can read easily (Readable Node). Use it when the user mentions Readable Node, asks to make a ComfyUI workflow readable or tidy, takes an existing workflow apart to rebuild it, or builds a new workflow. Do not hide nodes, do not hide wires (turn wireless links back into wires), left to right, 1 task per workflow, fewer custom nodes, appropriate colouring.
license: MIT
metadata:
  version: "0.0.2"
---

# Readable Node

Build ComfyUI workflows that are easy to read. There are two situations.
- Take a given workflow apart and rebuild it so it is easy to read.
- When building a new workflow, also build it so it is easy to read.

In both, write the understanding first, then build on the canvas (scripts/canvas.py) one move at a time. You are not fixing the original graph bit by bit.

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

## Words

- The definitions of the words are in references/glossary.md (sampler, core, eye line, rail, preparation, and so on).
- Where it says "Undecided", it has not been decided yet. Do not fill it by making rules or thresholds from your own judgement. Report what you did and what you were unsure about.

## Language

- Everything written for the user is written in the user's language: the conversation (progress messages, the report), Notes (including the part after "Markdown Note: " in the title), the Walkthrough, and the part after the colon in a value node's title.
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

## Rules about content

The rules for splitting, replacing, keeping and removing are in references/content.md.

## What not to do

- Run ComfyUI without being asked by the user.
- Draw a picture to look at the layout (an AI's eye sees packed forms as good, so fixing by the picture drifts towards worse. It also takes time). Judge the layout by the check list.

## Steps

`S` is the path of scripts/. Choose one working folder `W` (inside the output folder), and type every canvas move as `python3 $S/canvas.py --dir $W <move>`. Below, this is written `canvas`. The list of moves and the detailed behaviour (undo, placements calculated only once, block, and so on) are at the top of canvas.py (`python3 $S/canvas.py` prints them).
- Put every file you make while working inside `W`: plan files, Note files, workflows or object_info you fetch to read, notes. Only the exported workflows and the report page go outside `W`. `canvas finish` deletes what is in `W` and nothing outside it. Do not delete `W` yourself.

Moves marked "(when there is an original)" are only for rebuilding a given workflow. When building a new one, skip them.

1. **Read the original (when there is an original)**  
   `canvas open <workflow.json> <object_info URL or saved object_info JSON>`
   - When a saved JSON is given, the official node-replacement list is not used.
   - Read everything it returns (wireless links turned back, replacements, what was removed, outputs, disabled nodes, switches, custom nodes, models).
   - Take all nodes at once with `canvas src all` (do not type `src node` many times). Read from the outputs upstream, tracing back from the sampler.

2. **Write the understanding document (`$W/understanding.md`)**  
   The understanding of the workflow, written before building. Write the first version after reading, and revise it while building. Keep what you revised as well.
   - Read references/techniques.md and references/examples.md before writing.
   - What to write is in references/understanding.md.

   When the understanding document is written, tell the user once, without waiting for an answer: what the workflow does, how many workflows it will be split into, what will be replaced, and an estimate of the time (small workflows take a few minutes, large ones 20 to 40 minutes).

3. **Split**  
   Following the split in the understanding document, make one canvas per workflow (`canvas new <name>`, `canvas use <name>`). The number and names of the files after splitting are Undecided. One canvas becomes one workflow JSON.

4. **Build (per canvas)**  
   The core first, then the added techniques.
   - For how to build the core, do not keep per-model templates; refer to a workflow for the same use on nomadoor's site (Comfy-with-ComfyUI). `canvas refs <word>` lists, newest first, the workflows whose path or article title contains the word. Old workflows are sometimes built wrongly, so for the same use, choose the newer one. Refer only to how the core is built; do not copy the layout.
   - Write all the build moves in build.txt and run them once with `canvas run build.txt`. If it stops, fix that line and run the rest.
   - An original node is `copy <original id> …` (copies type, values and mode; does not copy wires). A new node is `add <type>`. Values are `set`. Wires are `link <A>.<output> <B>.<input> …`. Connect only what is needed.
   - When the build is done (when there is an original), compare with the original using `canvas diff` (values, inputs the user puts in, outputs, mode). One item at a time: if it is an intended difference, note the reason; if not, fix it.
   - Fix the content yourself. Compare with the understanding document and look for what falls under references/content.md. Also look for mistakes born from replacement and for lost functions.

5. **Arrange (per canvas)**  
   After reading references/readable-form.md.
   - Write the whole arrangement in layout.txt and place it with `canvas layout layout.txt`. Write the plan at two levels. First, for each grouping, `block <name> <id> …` and the arrangement inside it. After that, the arrangement between groupings (`put <block> right <block>` and so on). Rails, groups, colours, titles and Notes are written in the same file.
   - Once the block lines are written, and before writing the arrangement between groupings, use `canvas between layout.txt` to see the wires connecting blocks and the outputs handed out to several blocks. If the same value is handed out to several stages, decide first how to hand it out: with a rail, or with how the stages are stacked.
   - The column of sources is `canvas inputs <sampler>`; copying the same shape is `canvas shape`. The rules are in readable-form.md.
   - Split workflows, too, get the same layout for the same function with `canvas new <name> from <canvas>` or `shape`.
   - Make one block for each grouping in the understanding document.
   - Also add groups (`group`, `group-align`), colours for added functions (`color`) and titles for value nodes (`title`). The rules are in readable-form.md, "Groups", "Colour" and "Node names".

6. **Fix the arrangement yourself**  
   Look at the whole check list that `canvas layout` returns. For what needs fixing, rewrite the lines of the plan file together, and run `canvas layout` again. Do not rerun item by item.
   - You may finish only when the list is empty, or when every remaining item has "what was tried and what happened" attached. "Reviewed it" does not finish. Not having tried something is no reason to leave it.
   - When nothing is left to fix in the list, stop there. Do not keep adjusting, such as changing the gap numbers little by little and comparing.

7. **Notes**  
   Read references/notes.md. From E of the understanding document, write the text in Markdown files. Do not make them from everything you looked into. For the overview and models Note, use the draft from `canvas models`. Notes are written in the plan file with `note <file> <right|left|below|above> <node>` and `title`, and placed with `canvas layout`.
   - One Note at a time, check that the node written on the 🔗 line and the topic of the headings are about the same node. A topic about a different node moves to that node's Note (if it is the author's words, do not delete it).

8. **Export and compare**  
   For each canvas, `canvas export <name>.json`. (When there is an original) run `canvas diff` again on every canvas, look at the differences one by one, and if one is not intended, fix it and export again.
   - When there is an original, put the rebuilt workflow side by side with the original, and check that it has not become harder to read than the original.

9. **Write the report page (`report.html`)**  
   Write the page where the user checks the result, as one HTML file. The page has three views. The canvas makes Original (the original workflow) and Rebuilt (what was done on the canvases, one move at a time). You write only the Walkthrough.
   - For each canvas, write `$W/walk_<canvas>.md`, select the canvas with `canvas use <canvas>`, and register it with `canvas walk $W/walk_<canvas>.md` (the file's form is at the top of canvas.py). How to write it is in references/notes.md, "Walkthrough".
   - Finally, write the page with `canvas report report.html <the user's language code>` (`ja`, `en`, `zh` and so on).

10. **Report in the conversation**  
    First, a few lines of summary: what was produced, what was changed, what the user should check. The path of the report page.
    - Below that, the details: the understanding document, how it was split, what was changed and why (what was removed, what was replaced, the author's mistakes that were fixed), the diff differences and their reasons, and what was left in check and why.
    - `canvas finish` deletes the working folder, including the understanding document. Take what the report needs from it first, then run `canvas finish`, then give the report. If a canvas is not exported or the report page is out of date, it stops, says what is missing and deletes nothing.

## References

- references/glossary.md: definitions of the words.
- references/understanding.md: what to write in the understanding document.
- references/content.md: the rules about content (splitting, replacing, keeping, removing).
- references/techniques.md: building techniques (hard-to-read forms, and forms rebuilt to be readable).
- references/replacements.md: the replacement dictionary (custom nodes and deprecated nodes, things that may be removed, things to keep) and how to find the source.
- references/readable-form.md: layout, size, colour, node names.
- references/notes.md: how to write Notes and the Walkthrough, and where to place Notes.
- references/examples.md: examples (how the rules applied in real workflows), and the list of Undecided items.
