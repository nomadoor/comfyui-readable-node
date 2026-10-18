---
name: comfyui-readable-node
description: Rebuilds a ComfyUI workflow (JSON) into the Readable Node form. One task per workflow, wireless links turned back into wires, fewer custom nodes, left-to-right flow, visible wires, colouring, node names left unchanged. Use it to tidy an existing workflow (1 to 1), or to turn a workflow an AI assembled into one people can read (0 to 1).
---

# Readable Node

Read the original workflow and understand it. From that understanding, rebuild it on a new canvas, one move at a time. You are not fixing the author's graph bit by bit.

## What Readable Node is (this is all of it)

- 1 task = 1 workflow
- Remove custom nodes as far as possible
- Remove wireless links (Set/Get, Anything Everywhere, hidden links [badges], and the like)
- Show the wires (do not hide them behind nodes)
- Flow from left to right. Keep the main wires horizontal
- Colour appropriately
- Do not change node names

The goal is that a reader can follow the processing along a single line, and that the layout does not scatter the eye. A rebuild that is harder to read than the original workflow is pointless. Readability includes ease of rearranging (with many Reroutes, every time you move a node you also have to move the Reroutes).

## The canvas

Both building and arranging are done one move at a time on scripts/canvas.py (the canvas). The list of moves is at the top of canvas.py (`python3 $S/canvas.py` prints it).

- The state is kept in the working folder. Each move returns what changed, and the problems that move added and removed. `undo` takes a move back.
- Do not write coordinate numbers. Point at things: "put it to the right of A", "make the wire horizontal", "align the top edges". The canvas does the calculation. Only what you point at moves.
- "Put it to the right of A" is calculated once, at the moment it is placed. If you later move A, B does not follow. Things you want to move together go into a `block`.
- You can type moves one line at a time, or list them in a file and run them with `run`. `run` stops at the line that stops (that line changes nothing).
- What the canvas does (things with exactly one answer): reads the original and turns wireless links back into wires (also expands subgraphs and old group nodes), replaces nodes with nodes of the same calculation from the official node-replacement list, restores value nodes, merges identical loaders, removes outputs that are only for comparing and Previews that just show what was loaded, node sizes (ComfyUI's initial sizes), the default colours of loaders, LoRAs and the model Note, group padding, checks, and export. It returns everything it did.
- What you do: understanding, how to split, what to keep, remove or replace (outside the official list), rebuilding custom nodes, what goes where, what to align, rails, groups, colours for added functions, and Notes.

## Common mistakes

- **Cutting the author's techniques.** Keep processing, parameters and original structure that the author added. "Reducing it to the essentials" or "returning it to the standard" is not this skill's job.
- **Removing disabled functions.** Branches that are bypassed or muted, and the unselected side of a switch, are also functions the author prepared. Do not remove them. If they can be split off, provide them as a separate workflow (it is fine if the count grows or the workflow gets wider). Remove only things that are clearly debugging leftovers.
- **Commenting on how good the generated results are.** Things like "skin becomes realistic" cannot be checked, because you do not generate. If the author wrote it, quote it. Behaviour that can be checked in the node's source may be written.
- **Writing in the same words as the screen.** In Notes, write only what cannot be seen by looking (references/notes.md).
- **Reporting the work.** The people who read Notes are the people who use the workflow. What you did while reworking goes in the report. (Undecided: whether the differences from a replacement go into Notes as well. See "Where replacement stops" under Structure.)
- **Explaining with the author's own names.** Say what is being done using the common name (Hires.fix and so on).
- **Cramming.** Packing nodes together to reduce wires makes things harder to read. Use the screen widely and show the wires first.
- **Reading effort as value.** A part the author spent effort on is not necessarily important. Judge by what it does.
- **Filling undecided points with your own rules.** Where it says "undecided", "judgement" or "see the examples", do not make up your own rules or thresholds.
- **Shipping while knowing.** Do not ship something that remains in the check list and report it as "could not fix". Fix it. If you cannot, write what you tried and what happened.

## Structure (rules about content)

- **Split.** 1 task = 1 workflow.
  - Split a file that contains separate tasks that are not connected (outputs that share no upstream, or a structure that chooses with switch or bypass).
  - For multi-stage workflows (a later stage uses the result of an earlier stage), produce two forms only when what passes from the earlier stage to the later stage is a single image (or video) and both stages have a sampler: a workflow kept connected and tidied, and a split workflow (the later stage starts from Load Image). Whether to split depends on what the user wants to do, so produce both.
  - Other multi-stage workflows (post-processing where the later stage has no sampler, hires fix or refiner continuing in LATENT, ones that share models or conditioning) stay as one.
  - If a switch or bypass only chooses whether one step on the same path is present or not, do not split; keep one, with the step present. However, a switch that changes what the user puts in (whether an image is given or not; I2V and T2V, for example) is a different thing to do, so split it. 1 task = 1 workflow is the premise.
  - When you split, give names that show which version each is, and in the report state the difference in one phrase. Across split workflows, put the same function in the same layout.
- **One workflow is one thing the user wants to do.** Split branches that do different things. Branches that differ only in how they do it are merged into the one the author chose.
- **Remove what is entirely useless.** Nodes that reach no output, pass-through nodes, "values that do nothing" (a LoRA with strength 0, for example), processing that does nothing (resizing to its own size, resizes placed one after another), and Previews that are only for looking (ones that show an image that was only resized, ones only for watching the middle of generation): judge from the meaning of the node and remove them. Processing placed one after another is merged into one where it can be.
- **Tidy value nodes.** Keep value nodes that connect to two or more places. When the same value goes into two or more nodes and it is a value with the same meaning (if you change one, you would change the other in the same way), consider handing it out from one value node. Hand out only values you want to change on each generation and compare (seed, steps for comparison, a prompt handed to several places, and so on). Values that do not change once decided are put directly into each node that uses them.
  - Put the size value in one place only. Elsewhere, make things follow the result through the match size of Resize Image/Mask or through Get Image Size (examples.md).
  - Build sizes from what the size is for. Do not insist on copying the original values or expressions so they give the same result. To match an input image, resize by pixel count (MP), round to the model's fixed multiple, and take it from Get Image Size. Use the shrunk image further on too (reference image, VAE Encode, and so on). If the result is no longer equal to the original value, write that in the report.
- **Check whether a LoRA acts on the text encoder.** Even if the original workflow connects the LoRA's clip, that alone is no reason to use LoraLoader. Most LoRAs for recent models do not train the text encoder. Read only the safetensors header of the LoRA file (if it is not local, the one on HuggingFace or similar), and if there are no text encoder keys, use LoraLoaderModelOnly. If you cannot check, write in the report what you did.
- **Replace old nodes.**
  - A deprecated node is replaced by its successor if the source comments, description or display name point to one. If they do not, do not replace it; write it in a Note.
  - In every case, check in the node's source that the result is the same. If copying values is not enough, rewire. If the same result cannot be reached, do not replace it; write it in a Note.
- **Where replacement stops.** If the part core cannot do changes the shape of the output (image size, number of images, number of frames, length), keep it. If only internal numbers change (weights, quality, encoding), use core and write the difference in a Note and in the report (Undecided: whether the differences go into Notes. See "Reporting the work" under Common mistakes, and the top of references/notes.md). If only the model file the user puts in changes (a GGUF LLM to core's Generate Text, rife49.pth to core's interpolation model), also use core if the function exists in core. Write the difference in the model Note and in the report (Undecided: same as above). However, keep GGUF loaders, because core has no function to read GGUF. When in doubt, lean towards core. But do not take away the user's operations: turning a node where you decide placement by dragging on the screen into a combination of nodes where you type numbers takes away an important operation of the user. Even if it is in core, consider commonly used core nodes before nodes that are experimental (`experimental` in object_info) and not normally used (the part of references/examples.md on choosing a replacement).
- **Replace custom nodes.** Not only nodes for convenience, but also nodes that are the effect itself (sharpen and the like) are decided by where replacement stops. Special samplers (ClownsharKSampler and the like) are the exception; keep them. First look at references/replacements.md (the replacement dictionary). If it is there, build it exactly that way. If not, read the custom node's source, write it in the table in the understanding document, and decide by where replacement stops.
  - For a custom node that is not installed in ComfyUI, read only the files you need.
    1. Find the repository. If the node's properties have `cnr_id`, use `repository` from `https://api.comfy.org/nodes/<cnr_id>`; otherwise `aux_id` (if it is `owner/repo`, GitHub). If neither exists, look up `https://api.comfy.org/comfy-nodes/<type>/node` with the node's type name. If it is not there either, search ComfyUI-Manager's `https://raw.githubusercontent.com/Comfy-Org/ComfyUI-Manager/main/extension-node-map.json`.
    2. Read `__init__.py` by its raw URL, and follow `NODE_CLASS_MAPPINGS` to the file that has the node's type name.
    3. Read only that file. If `ver` is a commit, read the one at that commit.
    Do not clone. Do not run code you fetched. Do not put it into ComfyUI's custom_nodes. If it is found nowhere, leave it unreplaced, and write in the report "the source was not found, so this could not be determined".
  - When building with core, among the forms that give the same calculation, choose the more readable one. Do not copy the custom node's internals as they are (if KSampler or KSamplerAdvanced gives the same result, do not break it down into SamplerCustomAdvanced + SplitSigmas + CFGGuider). (Undecided: whether to merge an existing SamplerCustomAdvanced into KSampler. The examples in references/examples.md do both.)
  - Build video output with core's CreateVideo + SaveVideo.
- **Keep what the author placed stage by stage.** Structures such as handing one seed across stages, or placing a CLIP Text Encode per stage, are not changed (only duplicates of the same loader are merged).
- **Keep the author's intent. Do not keep the author's inconveniences.** A way of building that restricts the user's hands for no reason is returned to the ordinary form, and written in the report.
- **Fix what can only be the author's mistake.** Things like positive and negative swapped in only one of two stages of the same shape, or a VAE Encode right after a VAE Decode (pass the latent straight on; keep a VAE Decode that is for a preview). Write what you fixed in the report.
- **Save the final result.** If an intermediate result goes to Save Image and the final result ends in Preview Image, make the final one Save Image. Write it in the report.
- **A way of building that harms the result, and places that could be done better, are not fixed; write them in the Notes of the parts and in the report.** Always look into it and check it yourself before writing (references/notes.md).

## What not to do

- Do not aim to prove equivalence. If you can build it simpler, in core and more robustly than the author did, use that. But replace only when the result is the same and it can be used the same way.
- Do not keep per-model templates.
- Run ComfyUI only when the user asks. (Undecided: references/notes.md says to check with a small run before writing in a Note. See "Check before writing" there.)

## Steps

Every call of a tool takes time. Do in one call what can be done in one call (build with `run` on build.txt, arrange with `layout` on layout.txt). Read things side by side, at once.

`S` is the path of scripts/. Choose one working folder `W` (inside the output folder), and type every canvas move as `python3 $S/canvas.py --dir $W <move>`. Below, this is written `canvas`.

1. **Read the original.** `canvas open <workflow.json> <object_info URL or saved object_info JSON>`
   When a saved JSON is given instead of a running ComfyUI's URL, the official node-replacement list is not used.
   Read everything it returns (wireless links turned back, replacements, what was removed, outputs, disabled nodes, switches, custom nodes, models).
   Read all nodes at once with `canvas src all`, and read from the outputs upstream, tracing back from the sampler (do not type `src node` many times).

2. **Write the understanding document (`$W/understanding.md`).** One file can contain several tasks. Write it at two levels: the whole file, and each task. You do not know the tasks until you have read it, so write the first version after reading, and revise it while building. Keep what you revised as well.
   - A. The whole file: the list of outputs (what is output, which node). The list of tasks (which outputs form one task; for each task, its core = the sampler and the nodes that determine the core). How tasks relate (separate, unconnected tasks / a later stage uses an earlier stage's result / only models or values are shared / different ways chosen with switch or bypass / different ways of doing the same thing). How to split (how many workflows, which version each is, why; how to keep disabled functions). What belongs to no task, and what to do with it.
   - B. Each task: what it does (from what comes out at the end and what the user wants to do; do not mistake an intermediate means for the goal). What the user puts in and gets out. The core. The base form (t2i / i2i / t2v …, the kind of sampler, CFG, how the model is loaded). Pre- and post-processing techniques added to the base. Disabled functions. Values (values changed on each generation and values that do not change once decided; which are handed out from one). Models. Custom nodes (a table, one by one. For each function: "the value in this workflow, the default value, whether core can do it"; for the part core cannot do, whether it changes the shape of the output; and whether to keep it or use core. For ones in references/replacements.md, copy that row. For ones not there, always look at the "core nodes with similar names" that `canvas open` gives, and check in the source. Core sometimes has a node with the same function). Groupings and layers (which nodes form one grouping; units of work, and units of role such as loader, text encoder, sampler). Things that look like the author's mistakes. Processing that does nothing. Candidates to remove or replace, and why.
   - C. Compare with the author's words: read the author's Notes, group names and titles (`canvas src words`) after writing A and B. What you learned from them, where they disagree with A and B, and what remains in words as the author's techniques.
   - D. What you do not know: if there is someone to ask, ask. If you cannot ask, lean towards keeping, and report it.
   - E. Candidates for Notes: explanations the user needs, the author's techniques (ones with the author's words), and warnings about puzzling processing that was kept.
   Read references/techniques.md (how to build) and references/examples.md (examples) before writing.

   When the understanding document is written, report to the user once, in the user's language, without waiting for an answer: what the workflow does, how many workflows it will be split into, what will be replaced, and an estimate of the time (small workflows take a few minutes, large ones 20 to 40 minutes).

3. **Split.** Following the split in the understanding document, make one canvas per workflow (`canvas new <name>`, `canvas use <name>`).

4. **Build (per canvas).** The core first, then the added techniques.
   - For how to build the core, refer to a workflow for the same use on the skill author's site (Comfy-with-ComfyUI). (`canvas refs <word>` lists, newest first, the site's workflows whose path or article title contains the word, with the date and the article. Read the top ones by their URL.) Old workflows are sometimes built wrongly, so for the same use, choose the newer one. Refer only to how the core is built; do not copy the layout.
   - Write all the build moves in one file (build.txt) and run them once with `canvas run build.txt`. Do not type them one by one (each round trip takes time). If it stops, fix that line and run the rest.
   - To use an original node, `copy <original id> …` (copies type, values and mode; does not copy wires). A new node is `add <type>`. Values are `set`.
   - Wires are connected with `link <A>.<output> <B>.<input> …`, as the understanding document says to build. There is no tool that copies the original wires as they are. Connect only what is needed.
   - When the build is done, compare with the original using `canvas diff` (values, inputs the user puts in, outputs, mode). One item at a time: if it is an intended difference, note the reason; if not, fix it.
   - **Fix the content yourself.** Compare with the understanding document and look for: processing that does nothing, processing placed one after another, Previews only for looking, convenience nodes unrelated to the result, mistakes born from replacement (resizing to its own size, and so on), lost functions. If there are any, fix them.

5. **Arrange (per canvas).** After reading references/readable-form.md.
   - Write the whole arrangement in one plan file (layout.txt) and place it with `canvas layout layout.txt`. Do not type moves one by one. Write the plan at two levels. First, for each grouping, `block <name> <id> …` and the arrangement inside it (written looking only inside the grouping). After that, the arrangement between groupings (`put <block> right <block>` and so on). Rails, groups, colours and titles are written in the same file.
   - Make one block for each grouping in the understanding document. Once the block lines are written, and before writing the arrangement between groupings, use `canvas between layout.txt` to see the number and direction of wires connecting blocks, and outputs handed out to several blocks. If the same value is handed out to several stages, decide how to hand it out, with a rail or with how the stages are stacked, before writing (realising it after placing and rebuilding takes time). The sources that connect directly to a sampler go, with `canvas inputs <sampler>`, into one right-aligned column on its left. If similar stages are lined up, arrange one stage and then copy it into the same shape with `canvas shape <arranged block> <next block>`. Split workflows, too, get the same layout for the same function with `canvas new <name> from <canvas>` or `shape`. Arrange inside groupings (`row`, `stack`, `put … right … wire`, `align`) and arrange groupings against each other (`put <block> …`, `gap`, `move`).
   - Make the main line (what is being made: image, video, latent) horizontal (`put … wire`, `level`). Tool wires (VAE, noise, sampler, sigmas, guider, CLIP) may be diagonal. (Undecided: the definition of the main line differs from the one in references/readable-form.md. See "Core of the layout" and "Eye line" there.)
   - A value handed out to several distant places goes on a rail (`rail`). Do not lay one for a single wire.
   - Groups (`group`, `group-align`), colours for added functions (`color`), titles for value nodes (`title`).

6. **Fix the arrangement yourself.** Look at the whole check list that `canvas layout` returns (it is divided by grouping). For what needs fixing, rewrite the lines of the plan file together, and run `canvas layout` again. In one rewrite, fix as many places as there are. Do not rerun item by item.
   - You may finish only when the list is empty, or when every remaining item has "what was tried and what happened" attached. "Reviewed it" does not finish. Not having tried something is no reason to leave it.
   - What is written as "cannot be left even with a reason" (reverse wires and the like) cannot be left even with a reason. Fix it.
   - Judge good and bad by the list. Do not draw a picture and look at it while arranging (an AI's eye sees packed forms as good, so fixing by the picture drifts towards worse. It also takes time). `canvas render` is used only once, at export.
   - When nothing is left to fix in the list, stop there. Do not keep adjusting, such as changing the gap numbers little by little and comparing.
   - A diagonal main line, overlaps, and a main line passing behind nodes almost never get a reason to be left.

7. **Notes.** Read references/notes.md. From E of the understanding document, write the text in Markdown files. For the model Note, use the draft from `canvas models`. Notes are also written in the plan file with `note <file> <right|left|below|above> <node>` and `title`, and placed with `canvas layout` (where to place them: references/notes.md). After placing, check in the list that no Note overlaps a wire path or a node.
   - One Note at a time, check that the node written on the 🔗 line and the topic of that Note's headings are about the same node. A topic about a different node moves to that node's Note (if it is the author's words, do not delete it).

8. **Export and compare.** For each canvas, `canvas export <name>.json` and `canvas render <name>.png`. Run `canvas diff` (the second time) on every canvas. Look at the differences one by one; if one is not intended, fix it and export again. Finally, `canvas replay replay.html` writes one page that steps through everything done on the canvases; give its path to the user in the report.

9. **Report.** Write it in the user's language. First, a few lines of summary: what was produced, what was changed, and what the user should check. Below that, the details: the understanding document, how it was split, what was changed and why (what was removed, what was replaced, the author's mistakes that were fixed), the diff differences and their reasons, and what was left in check and why.

## References

- references/readable-form.md: tendencies of layout, size, colour and node names. Read before arranging.
- references/notes.md: how to write Notes, and where to place them. Read before writing Notes.
- references/examples.md: examples (examples of judgement).
- references/techniques.md: building techniques. Read before thinking about how to build.
- references/replacements.md: the replacement dictionary (custom node replacements checked once, things that may be removed, things to keep). Look it up first when you see a custom node.
