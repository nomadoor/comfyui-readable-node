---
name: comfyui-readable-node
description: Builds a ComfyUI workflow (JSON) into a form people can read easily (Readable Node). Use it when the user mentions Readable Node, asks to make a ComfyUI workflow readable or tidy, takes an existing workflow apart to rebuild it, or builds a new workflow. Do not hide nodes, do not hide wires (turn wireless links back into wires), left to right, 1 task per workflow, fewer custom nodes, appropriate colouring.
license: MIT
metadata:
  version: "0.0.1"
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

## Division of work

**What you decide (judgement)**: understanding, how to split, what to keep, remove or replace, rebuilding custom nodes, what goes where, what to align, rails, groups, colours for added functions, Notes.

**What the canvas does (things with exactly one answer)**: node sizes (ComfyUI's initial sizes), calculating positions, the default colours of loaders, LoRAs and Notes, group padding, checks (check), export. It returns everything it did.

**What the tool does when reading the original** (`canvas open`): turns wireless links back into wires (also expands subgraphs and old group nodes). Applies the official node-replacement list and replacements that give the same calculation. Returns value nodes that go into only one place to widgets. Merges identical loaders. Removes Previews that only show what was loaded. It returns everything it did.

Do not keep per-model templates. For how to build the core, refer to workflows on nomadoor's site, as in step 4.

**How to use the canvas**
- Do not write coordinate numbers. Point at things: "put it to the right of A", "make the wire horizontal", "align the top edges". The canvas does the calculation. Only what you point at moves.
- The list of moves and the detailed behaviour (undo, placements calculated only once, block, and so on) are at the top of canvas.py (`python3 $S/canvas.py` prints them).
- Every call of the tool takes time. Do in one call what can be done in one call (build with `run` on build.txt, arrange with `layout` on layout.txt). Read things side by side, at once.

## Rules about content

### Split

**One workflow is one thing the user wants to do.** Split branches that do different things.
- Split separate tasks that are not connected (outputs that share no upstream, separate structures chosen with switch or bypass).
- Split a branch that changes what the user puts in (whether an image is given or not: t2i and i2i, T2V and I2V, and so on).
- Split a branch that changes how the generation itself is built (the model, steps, cfg, the sampler setup). Example: a normal version and a distilled version.
- Do not split a branch that only changes the result a little when added (a LoRA that refines the style, TorchCompile that only changes speed, and so on). Keep it bypassed in the one workflow, for the user to switch (optional). Splitting every disabled branch makes the combinations grow exponentially.
- Ways of doing one step differently (Tiled VAE Decode and VAE Decode, and so on) are merged into the one the workflow's author chose.
- Whether to split a multi-stage workflow (a later stage uses the result of an earlier stage) is Undecided (Undecided in examples.md). Think from 1 task = 1 workflow, and report it when unsure.
- When you split, give names that show which version each is, and in the report state the difference in one phrase. Across split workflows, put the same function in the same layout.
- Functions the workflow's author prepared (branches that are bypassed or muted, the unselected side of a switch) are kept in one of the forms above. Of the disabled branches, remove only things that are clearly debugging leftovers.

### Replace

**If old nodes or custom nodes can be realised with a combination of core nodes, replace them.** Do not aim to prove equivalence. If you can build it simpler, in core and more robustly than the workflow's author did, build it that way.
- First look up references/replacements.md (the replacement dictionary). If it is there, build it exactly that way.
- If not, read the node's source, write it in the table in the understanding document, and decide by "Where replacement stops". How to find the source is at the top of replacements.md.
- A deprecated node is replaced by its successor if the source comments, description or display name point to one. If they do not, replace it with core nodes that give the same calculation, if there is such a form. If none is found, do not replace it; keep it and write it in the report.
- In every case, check in the node's source that the result is the same. If copying values is not enough, rewire.
- How to build is in references/techniques.md (readable forms of the same calculation).

**Where replacement stops**
- If the part core cannot do changes the shape of the output (image size, number of images, number of frames, length), keep it.
- If only internal numbers change (weights, quality, encoding), use core. If it is within the margin of error, lean towards core.
- If the image size changes only a little and still fits the model's required multiple (64 and so on), do not count it as a change in the shape of the output. Use core and write it in the report.
- If only the model file the user puts in changes (a GGUF LLM to core's Generate Text, and so on), use core if the function exists in core. However, keep GGUF loaders, because core has no function to read GGUF.
- Keep special samplers (ClownsharKSampler and the like).
- Do not take away the user's operations. Do not turn a node where you decide by dragging on the screen into a combination of nodes where you type numbers.
- Even if it is in core, consider commonly used core nodes before nodes that are experimental (`experimental` in object_info) and not normally used.
- Write what changes through a replacement in the report.

### Keep the author's intent, fix mistakes and inconveniences

**Keep what the workflow's author added on purpose (processing, parameters, structure per stage).** Fix mistakes and ways of building that restrict the user's hands for no reason, and write them in the report.
- Examples of keeping: handing one seed across stages, placing a CLIP Text Encode per stage (only duplicates of the same loader are merged).
- Examples of fixing: positive and negative swapped in only one of two stages of the same shape. A VAE Encode right after a VAE Decode (pass the latent straight on). An intermediate result going to Save Image while the final result ends in Preview Image (save the final one).
- A part the author spent effort on is not necessarily important. Judge by what it does.
- Say what is being done with the common name (Hires.fix and so on), not the author's own name.

### Remove what is useless

**Remove what reaches no output and what does nothing, judging from the meaning of the node.** Write it in the report.
- Pass-through nodes, "values that do nothing" (a LoRA with strength 0, for example).
- Processing that does nothing (resizing to its own size, resizes placed one after another). Processing placed one after another is merged into one where it can be.
- Previews only for looking (ones that show an image that was only resized, ones only for watching the middle of generation).

### What is kept without fixing

**Ways of building that harm the result, and places that could be done better, are not fixed; write them in the Caution of a Note and in the report.** Before writing, check in the source or the model card (references/notes.md).

## What not to do

- Write coordinate numbers.
- Fill "Undecided" with your own rules or thresholds.
- Ship something that remains in the check list, saying "could not fix". Fix it. If you cannot, write what you tried and what happened.
- Silently remove functions the workflow's author prepared (bypass or switch branches).
- Run ComfyUI without being asked by the user.
- Draw a picture to look at the layout (an AI's eye sees packed forms as good, so fixing by the picture drifts towards worse. It also takes time). Judge the layout by the check list.

## Steps

`S` is the path of scripts/. Choose one working folder `W` (inside the output folder), and type every canvas move as `python3 $S/canvas.py --dir $W <move>`. Below, this is written `canvas`.

Moves marked "(when there is an original)" are only for rebuilding a given workflow. When building a new one, skip them.

1. **Read the original (when there is an original).** `canvas open <workflow.json> <object_info URL or saved object_info JSON>`
   - When a saved JSON is given, the official node-replacement list is not used.
   - Read everything it returns (wireless links turned back, replacements, what was removed, outputs, disabled nodes, switches, custom nodes, models).
   - Take all nodes at once with `canvas src all` (do not type `src node` many times). Read from the outputs upstream, tracing back from the sampler.

2. **Write the understanding document (`$W/understanding.md`).** Write it at two levels: the whole file, and each task. Write the first version after reading, and revise it while building. Keep what you revised as well. Read references/techniques.md and references/examples.md before writing.
   - A. The whole file
     - The list of outputs (what is output, which node).
     - The list of tasks (which outputs form one task; the core of each task).
     - How tasks relate (unconnected / a later stage uses an earlier stage's result / only models or values are shared / different ways chosen with switch or bypass / different ways of doing the same thing).
     - How to split (how many workflows, which version each is, why; how to keep disabled functions).
     - What belongs to no task, and what to do with it.
   - B. Each task
     - What it does (from what comes out at the end and what the user wants to do; do not mistake an intermediate means for the goal). What the user puts in and gets out.
     - The core, and the base form (t2i / i2i / t2v …, the kind of sampler, CFG, how the model is loaded). Pre- and post-processing added to the base. Disabled functions.
     - Values (values changed on each generation and values that do not change once decided; which are handed out from one). Models.
     - The table of custom nodes (one by one. For each function: "the value in this workflow, the default value, whether core can do it". Whether the part core cannot do changes the shape of the output. Whether to keep it or use core). For ones in replacements.md, copy that row. For ones not there, always look at the "core nodes with similar names" that `canvas open` gives, and check in the source.
     - Groupings (which nodes form one grouping; units of work, and units of role such as loader, text encoder, sampler).
     - Things that look like the author's mistakes, processing that does nothing, candidates to remove and candidates to replace, and why.
   - C. Compare with the author's words (when there is an original): read the author's Notes, group names and titles (`canvas src words`) after writing A and B. What you learned, where they disagree with A and B, and what remains in words as the author's techniques.
   - D. What you do not know: if there is someone to ask, ask. If you cannot ask, lean towards keeping, and report it.
   - E. Candidates for Notes: explanations the user needs, the author's techniques (ones with the author's words), and warnings about puzzling processing that was kept.

   When the understanding document is written, tell the user once, in the user's language, without waiting for an answer: what the workflow does, how many workflows it will be split into, what will be replaced, and an estimate of the time (small workflows take a few minutes, large ones 20 to 40 minutes).

3. **Split.** Following the split in the understanding document, make one canvas per workflow (`canvas new <name>`, `canvas use <name>`). The number and names of the files after splitting are Undecided. One canvas becomes one workflow JSON.

4. **Build (per canvas).** The core first, then the added techniques.
   - For how to build the core, refer to a workflow for the same use on nomadoor's site (Comfy-with-ComfyUI). `canvas refs <word>` lists, newest first, the workflows whose path or article title contains the word. Old workflows are sometimes built wrongly, so for the same use, choose the newer one. Refer only to how the core is built; do not copy the layout.
   - Write all the build moves in build.txt and run them once with `canvas run build.txt`. If it stops, fix that line and run the rest.
   - An original node is `copy <original id> …` (copies type, values and mode; does not copy wires). A new node is `add <type>`. Values are `set`. Wires are `link <A>.<output> <B>.<input> …`. Connect only what is needed.
   - When the build is done (when there is an original), compare with the original using `canvas diff` (values, inputs the user puts in, outputs, mode). One item at a time: if it is an intended difference, note the reason; if not, fix it.
   - Fix the content yourself. Compare with the understanding document and look for what falls under "Rules about content". Also look for mistakes born from replacement and for lost functions.

5. **Arrange (per canvas).** After reading references/readable-form.md.
   - Write the whole arrangement in layout.txt and place it with `canvas layout layout.txt`. Write the plan at two levels. First, for each grouping, `block <name> <id> …` and the arrangement inside it. After that, the arrangement between groupings (`put <block> right <block>` and so on). Rails, groups, colours, titles and Notes are written in the same file.
   - Once the block lines are written, and before writing the arrangement between groupings, use `canvas between layout.txt` to see the wires connecting blocks and the outputs handed out to several blocks. If the same value is handed out to several stages, decide first how to hand it out: with a rail, or with how the stages are stacked.
   - The column of sources is `canvas inputs <sampler>`; copying the same shape is `canvas shape`. The rules are in readable-form.md.
   - Split workflows, too, get the same layout for the same function with `canvas new <name> from <canvas>` or `shape`.
   - Make one block for each grouping in the understanding document.
   - Also add groups (`group`, `group-align`), colours for added functions (`color`) and titles for value nodes (`title`). The rules are in readable-form.md, "Groups", "Colour" and "Node names".

6. **Fix the arrangement yourself.** Look at the whole check list that `canvas layout` returns. For what needs fixing, rewrite the lines of the plan file together, and run `canvas layout` again. Do not rerun item by item.
   - You may finish only when the list is empty, or when every remaining item has "what was tried and what happened" attached. "Reviewed it" does not finish. Not having tried something is no reason to leave it.
   - Do not leave diagonal a wire that can be made horizontal. Do not leave overlapping nodes, or backward wires that do not fall under the exceptions in readable-form.md, either.
   - When nothing is left to fix in the list, stop there. Do not keep adjusting, such as changing the gap numbers little by little and comparing.

7. **Notes.** Read references/notes.md. From E of the understanding document, write the text in Markdown files. Do not make them from everything you looked into. For the overview and models Note, use the draft from `canvas models`. Notes are written in the plan file with `note <file> <right|left|below|above> <node>` and `title`, and placed with `canvas layout`.
   - One Note at a time, check that the node written on the 🔗 line and the topic of the headings are about the same node. A topic about a different node moves to that node's Note (if it is the author's words, do not delete it).

8. **Export and compare.** For each canvas, `canvas export <name>.json`. (When there is an original) run `canvas diff` again on every canvas, look at the differences one by one, and if one is not intended, fix it and export again. Finally, `canvas replay replay.html <lang>` writes a page that steps through what was done on the canvases, one move at a time. Pass `ja` when the user speaks Japanese, otherwise `en`.
   - When there is an original, put the rebuilt workflow side by side with the original, and check that it has not become harder to read than the original.

9. **Report.** Write it in the user's language.
   - First, a few lines of summary: what was produced, what was changed, what the user should check. The path of the replay page.
   - Below that, the details: the understanding document, how it was split, what was changed and why (what was removed, what was replaced, the author's mistakes that were fixed), the diff differences and their reasons, and what was left in check and why.
   - `canvas finish` deletes the working folder, including the understanding document. Take what the report needs from it first, then run `canvas finish`, then give the report. If a canvas is not exported or the replay page is out of date, it stops, says what is missing and deletes nothing.

## References

- references/glossary.md: definitions of the words.
- references/readable-form.md: layout, size, colour, node names. Read before arranging.
- references/notes.md: how to write Notes and where to place them. Read before writing Notes.
- references/techniques.md: building techniques (hard-to-read forms, and forms rebuilt to be readable). Read before thinking about how to build.
- references/replacements.md: the replacement dictionary (custom nodes and deprecated nodes, things that may be removed, things to keep). Look it up first when you see a custom node.
- references/examples.md: examples (how the rules applied in real workflows), and the list of Undecided items.
