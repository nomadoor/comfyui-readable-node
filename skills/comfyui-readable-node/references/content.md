# Rules about content

Used when writing the understanding document (step 2) and when building (step 4).

## Split

**One workflow is one thing the user wants to do.** Split branches that do different things.
- Split separate tasks that are not connected (outputs that share no upstream, separate structures chosen with switch or bypass).
- Split a branch that changes what the user puts in (whether an image is given or not: t2i and i2i, T2V and I2V, and so on).
- Split a branch that changes how the generation itself is built (the model, steps, cfg, the sampler setup). Example: a normal version and a distilled version.
- Do not split a branch that only changes the result a little when added (a LoRA that refines the style, TorchCompile that only changes speed, and so on). Keep it bypassed in the one workflow, for the user to switch (optional). Splitting every disabled branch makes the combinations grow exponentially.
- Ways of doing one step differently (Tiled VAE Decode and VAE Decode, and so on) are merged into the one the workflow's author chose.
- Whether to split a multi-stage workflow (a later stage uses the result of an earlier stage) is Undecided (Undecided in examples.md). Think from 1 task = 1 workflow, and report it when unsure.
- When you split, give names that show which version each is, and in the report state the difference in one phrase. Across split workflows, put the same function in the same layout.
- Functions the workflow's author prepared (branches that are bypassed or muted, the unselected side of a switch) are kept in one of the forms above. Of the disabled branches, remove only things that are clearly debugging leftovers.

## Replace

**If old nodes or custom nodes can be realised with a combination of core nodes, replace them.** Do not aim to prove equivalence. If you can build it simpler, in core and more robustly than the workflow's author did, build it that way.
- First look up replacements.md (the replacement dictionary). If it is there, build it exactly that way.
- If not, read the node's source, write it in the table in the understanding document, and decide by "Where replacement stops". How to find the source is at the top of replacements.md.
- A deprecated node is replaced by its successor if the source comments, description or display name point to one. If they do not, replace it with core nodes that give the same calculation, if there is such a form. If none is found, do not replace it; keep it and write it in the report.
- In every case, check in the node's source that the result is the same. If copying values is not enough, rewire.
- How to build is in techniques.md (readable forms of the same calculation).

### Where replacement stops

- If the part core cannot do changes the shape of the output (image size, number of images, number of frames, length), keep it.
- If only internal numbers change (weights, quality, encoding), use core. If it is within the margin of error, lean towards core.
- If the image size changes only a little and still fits the model's required multiple (64 and so on), do not count it as a change in the shape of the output. Use core and write it in the report.
- If only the model file the user puts in changes (a GGUF LLM to core's Generate Text, and so on), use core if the function exists in core. However, keep GGUF loaders, because core has no function to read GGUF.
- Keep special samplers (ClownsharKSampler and the like).
- Do not take away the user's operations. Do not turn a node where you decide by dragging on the screen into a combination of nodes where you type numbers.
- Even if it is in core, consider commonly used core nodes before nodes that are experimental (`experimental` in object_info) and not normally used.

## Keep the author's intent, fix mistakes and inconveniences

**Keep what the workflow's author added on purpose (processing, parameters, structure per stage).** Fix mistakes and ways of building that restrict the user's hands for no reason, and write them in the report.
- Examples of keeping: handing one seed across stages, placing a CLIP Text Encode per stage (only duplicates of the same loader are merged).
- Examples of fixing: positive and negative swapped in only one of two stages of the same shape. A VAE Encode right after a VAE Decode (pass the latent straight on). An intermediate result going to Save Image while the final result ends in Preview Image (save the final one).
- A part the author spent effort on is not necessarily important. Judge by what it does.

## Remove what is useless

**Remove what reaches no output and what does nothing, judging from the meaning of the node.** Write it in the report.
- Pass-through nodes, "values that do nothing" (a LoRA with strength 0, for example).
- Processing that does nothing (resizing to its own size, resizes placed one after another). Processing placed one after another is merged into one where it can be.
- Previews only for looking (ones that show an image that was only resized, ones only for watching the middle of generation).
  - A Preview that lets the user check something the result depends on is not one of these; keep it. Example: the mask that shows which person in the input video the reference image is put on.

## What is kept without fixing

**Ways of building that harm the result, and places that could be done better, are kept without fixing.** How to write them is in the Caution of notes.md.
