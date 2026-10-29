# Rules about content

Two decisions for each part of the original: which workflow it goes into (Split), and what becomes of it (keep it, fix it, replace it with core, or remove it). Used when writing the understanding document (step 2) and when building (step 4); `canvas diff` compares the result with the original (step 8). Rules read as in readable-form.md (Why, Bad, Fine, Undecided).

## Read before deciding

**Read what each part does with its values here, not what it is called.** Do not copy the original as it is. For each node: what goes in, what comes out, and what its current values make it do (a node can be an identity at its values: a LoRA at strength 0, a wildcard processor with no wildcard in its text, two samplers where the second redraws everything). Why: the workflow is easy to rearrange and reuse; a part copied without reading is carried for nothing.
- Bad: a node kept or rebuilt without its job here written in the understanding document.

## Split

**One workflow is one thing the user wants to do.** Many workflows are fine: the aim is the principles of SKILL.md, not fewer workflows. Why: 1 task = 1 workflow.
- One workflow: a generation whose stages pass conditioning or a latent on (base → refiner → Hires.fix; t2i → a redraw at a larger size with the same model).
- Split: what changes what can be done (t2i, i2i and edit; T2V and I2V); what changes the sampling setup (steps, sigmas, cfg, the sampler): models each with their own settings, a speed-up that changes steps or cfg. Tasks that are not connected (outputs sharing no upstream).
- Its own workflow: effects applied to the finished image (film grain, colour correction and the like).
- A bypassed branch in the one workflow: an optional guide (a depth or reference image the task can do without), a speed-up that only may make it faster, an addition that only may make it a little better (CFGZeroStar, a guidance adjustment).
- Bad: one workflow whose switch or bypass chooses between things that must be split. Workflows split for an optional guide or an on/off branch. Of several selectable sets (models with their settings), one built as nodes and the others left as a table in a Note. Effects on the finished image packed into the generation workflow.

Name split workflows so the version shows, give the difference in one phrase in the report, and put the same function in the same layout across them.

## What becomes of each part

**Keep what the author added on purpose** (processing, values, structure per stage: one seed handed across stages, a CLIP Text Encode per stage; bypassed or muted branches, the unselected side of a switch; a Compare). Merge ways of doing one step differently (Tiled VAE Decode and VAE Decode) into the one the author chose. Why: the rebuilt workflow keeps every function of the original.
- Bad: a function of the original gone from every rebuilt workflow (only debugging leftovers may go).

**Fix what does nothing for the result or harms it, and what narrows what the user can do for no gain; report it.** Examples: a sampler whose result the next one fully redraws (both start at step 0 with noise added); VAE Encode right after VAE Decode (pass the latent on); decoding and previewing the middle of generation (techniques.md shows the form); positive and negative swapped in one of two same-shaped stages; an intermediate result saved while the final one only previews; a value that breaks the model's required multiple; a fixed size where the user should choose one. Why: the workflow does what it seems to do.
- Bad: one of these left in the rebuilt workflow.
- Fine: a value the author may have chosen on purpose (a hand-made sigma list, a strength) is kept; if it looks strange, it is explained in a Caution Note (notes.md). This is for values only: a strange way of wiring (the positive and the negative encoded through different CLIP chains) is fixed.

**Replace old nodes and custom nodes with core nodes when core can do the job.** Build it simpler and more robust than the author did when you can; read the source to know what the node does, but the core build need not be proven equivalent. Why: remove custom nodes as far as possible.
- Look up replacements.md first and follow it exactly. Otherwise read the node's source (how to find it: top of replacements.md), write it in the understanding document's table, and rewire if copying values is not enough. A deprecated node goes to its successor. Readable forms of the same calculation are in techniques.md.
- Keep it when: the part core cannot do changes the shape of the output (image size, number of images or frames, length); it is a GGUF loader; it is a special sampler (ClownsharKSampler and the like); replacing it would take away an operation the user does by dragging on screen; core cannot take the same input by wire (a crop whose region comes in by wire); its source cannot be found. Report what was kept and why.
- Use core when only internal numbers change (weights, quality, encoding), when the image size changes but still fits the model's required multiple, or when only the model file changes and core has the function (a GGUF LLM to core's Generate Text). Prefer core nodes not marked `experimental`.
- Bad: a custom node kept although none of the reasons to keep it applies. A custom node kept without reading what it does with its values here.

**Remove what reaches no output or does nothing with its values, and report it**: pass-through nodes; a LoRA at strength 0; a text processor whose features the text does not use; resizing to its own size; resizes one after another (merge them); a save node chosen for a feature it does not use (saving with metadata when no metadata is used: core Save Image already writes the workflow into the image); nodes that do not change the result (playing a sound, freeing GPU memory); a Preview only for looking (an image that was only resized).
- Fine: a Preview that lets the user check something the result depends on (which person in the input video the reference image goes on). A Compare the author added (it stays; where it stands: readable-form.md). A step that does nothing but makes the flow clearer (a size match before a compare).
- Bad: any of the above left in the rebuilt workflow.
