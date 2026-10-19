# Building techniques

Models of how to build, used when rebuilding. Each puts a hard-to-read way of building (Before) next to the form rebuilt with core nodes to be readable (After). Read them before writing the understanding document, and use them when building (step 4 of SKILL.md).

**If the original workflow has a "Before" form, build it in the "After" form.** Do not use it when "When it does not apply" fits.

- Before using one, confirm in object_info that the needed nodes (and the options of the mode you use) exist. Depending on the user's ComfyUI version, they may not exist yet.
- "Where verified" is the source in which it was confirmed that this way of building gives the same result. Verified with ComfyUI 0.39.0. When the user's version differs greatly, look here and verify again.
- What core nodes each individual custom node is replaced with is in replacements.md.

## Parameter comparison: the same pipeline differing only in a value

### Do not duplicate the pipeline; make it one with Create List (execution by list)

```
Before: LoRA(strength 0.6) → KSampler → VAE Decode → Save Image("LoRA1")
        LoRA(strength 0.8) → KSampler → VAE Decode → Save Image("LoRA2")
        LoRA(strength 1.0) → KSampler → VAE Decode → Save Image("LoRA3")
After:  Float(0.6), Float(0.8), Float(1.0) → Create List → LoRA.strength_model, LoRA.strength_clip
        LoRA → KSampler → VAE Decode → Save Image("LoRA")
```

- A node that receives a list is executed per element, and everything after it also flows per element.
- If the same value goes into two places (strength_model and strength_clip), connect the same Create List to both.
- If the per-branch filenames exist only to tell the files apart, do not make a list of names. Use one filename_prefix and leave it to Save Image's sequence number (within one execution, the number order is the list order).
- In the Usage of a nearby Note, add one line in the user's language: "One image is generated for each of these values." When you did not make a list of filenames, also add "Files are saved in the order of the list."
- When it does not apply: two or more values differ per branch (both the strength and the prompt, and so on). Different processing has been added per branch.
- Watch out:
  - If lists go into two places, they are not multiplied. They are paired in element order (1st with 1st, 2nd with 2nd). If the lengths differ, the last element of the shorter one is repeated. The number of executions is the length of the longest list.
  - One Create List holds up to 10 items.
  - If downstream there is a node that receives the list all at once, the list is merged into one there.
- Where verified: `_async_map_node_over_list` in execution.py (`slice_dict` takes the i-th item, and the last one if there are not enough), comfy_extras/nodes_toolkit.py (Create List).

## Specifying resolution

### Put the resolution value in one place; match the rest with match size and Get Image Size

```
Before: Int(1024) → Resize Image/Mask(image A).width, Resize Image/Mask(image B).width, Empty Latent.width
        Int(1024) → the same for height
After:  Resize Image/Mask(image A, scale dimensions 1024×1024)
        → Resize Image/Mask(image B, match size)
        → Get Image Size → Empty Latent
```

- When it does not apply: values that are the same but mean different things (ones meant to have only one of them changed later, the generation resolution and the save resolution, and so on).
- Watch out: whether match size's crop is the same as the original build (cropping the center, and so on).
- Where verified: comfy_extras/nodes_post_processing.py (match size of resize_type), comfy_extras/nodes_images.py (Get Image Size).

### For an image resized partway through, take the resolution from the resized image with Get Image Size

```
Before: Load Image → (a node partway through resizes) → …    Empty Latent(width, height typed by hand)
After:  Load Image → (a node partway through resizes) → Get Image Size → Empty Latent
```

- A value typed by hand drifts from the resolution the node partway through changed it to.

### Build the resolution from what the resolution is for

```
Before: copy the values or expressions of a resize that fits into a frame, so that they give the same values
After:  to match the input image, Resize Image/Mask (scale total pixels, MP) → round to the model's fixed multiple → Get Image Size
        use the shrunk image further on too (reference image, VAE Encode, and so on)
```

- If the result is not equal to the original value, write it in the report.

## Value nodes

### Return a value node that goes into only one place to a widget; hand out anew only values changed on each generation

```
Before: value node → only one place
        value node → two or more places
        the same value is put directly into each node that uses it
After:  value node that goes into only one place → returned to a widget (`canvas open` does this when reading the original)
        value node connected to two or more places → kept
        hand out anew from one value node only values changed on each generation (seed, steps for comparison, a prompt handed to several places, and so on)
```

- Hand out anew when a value with the same meaning (if you change one, you would change the other in the same way) goes into two or more nodes. Do not make a new value node for values that do not change once decided (steps, cfg, and so on).

### A node that only changes the type: look at the receiving input's type before copying it

```
Before: Int (fps) → Math Expression (split into int and float) → receiving node A (FLOAT), receiving node B (INT)
After:  Float (fps) → receiving node A, receiving node B (when B's input also accepts FLOAT)
```

- A type conversion in the original workflow fits the nodes of the time it was made. Look at the type of today's inputs in object_info; if they accept the value as it is, remove the conversion node.

## Conditioning

### With cfg 1.0, make the negative by passing the positive conditioning through ConditioningZeroOut

```
Before: empty CLIP Text Encode → negative
        empty CLIP Text Encode → ConditioningZeroOut → negative
After:  positive conditioning → ConditioningZeroOut → negative
```

- With cfg 1.0 the sampler does not use the negative in its calculation. The negative input only needs a conditioning connected; there is no need to encode a text.
- Does not apply: cfg is higher than 1.0 (encoding an empty text and a zeroed conditioning then give different results).
- Checked in: comfy/samplers.py (with cfg 1.0 the negative is not calculated), nodes.py ConditioningZeroOut (only sets the conditioning it receives to zero).

## LoRA

### Whether to connect the LoRA's clip is decided by the file

```
Before: the original workflow connects the LoRA's clip, so LoraLoader is used
After:  read only the safetensors header of the LoRA file; if there are text encoder keys, LoraLoader, otherwise LoraLoaderModelOnly
```

- If the file is not at hand, read the header of the one on HuggingFace or similar. If you cannot check, write in the report what you did.

## String processing

### Consecutive Replace Text become one Replace Text (Regex)

```
Before: text → Replace Text(image → X) → Replace Text(photo → X) → Replace Text(picture → X) → …
After:  text → Replace Text (Regex)(pattern: image|photo|picture, replace: X) → …
```

- Replace Text (StringReplace), Replace Text (Regex) (RegexReplace).
- When it does not apply: each word is replaced with a different target (image → A, photo → B).
- Watch out: Replace Text is case-sensitive and does not look at word boundaries. Replace Text (Regex)'s case_insensitive is on by default, so to keep it the same as the original, turn it off. Adding `\b` to the pattern drops words like "images", and the result changes from the original. Which to choose is decided by meaning.
- Where verified: comfy_extras/nodes_string.py (StringReplace, RegexReplace).

### If an instruction and the body text are joined and fed into Generate Text, put the instruction in system_prompt

```
Before: instruction, body text → Format Text → Generate Text.prompt
After:  instruction → Generate Text.system_prompt (optional)
        body text → Generate Text.prompt
```

- The behaviour changes slightly (it is passed as system). Write it in the report.
- Where verified: TextGenerate in object_info.

## Display nodes

### Do not put a display node in the flow; put it on a branch

```
Before: A → (a node that displays the value or image it receives and passes it straight on) → B
After:  A → B
        A → Preview as Text (for a value) / Preview Image (for an image)
```

- Preview as Text (PreviewAny) shows not only text but also numbers and conditioning.
- Because it is not in the flow, the display node can be moved freely without being tied to the flow.
- Watch out: Preview as Text also has a STRING output, but do not connect anything onward from it (that would put it back in the flow).
- Where verified: comfy_extras/nodes_preview_any.py (the input `source` accepts anything).

### Remove outputs that only decode and show the result of an intermediate stage

```
Before: KSampler(stage 1) → VAE Decode → Save Image / Preview Image   (an intermediate picture before it has finished drawing)
        KSampler(stage 1) → … → KSampler(stage 2) → …
After:  KSampler(stage 1) → … → KSampler(stage 2) → …
```

- It has nothing to do with the final result and only makes things heavier by the decode. Remove it and write it in the report.

## Reusing the latent

### In an edit at denoise 1.0, put the latent of the reference image's VAE Encode into latent_image

```
Before: reference image → VAE Encode → (edit conditioning)
        reference image → Get Image Size → Empty Latent → sampler.latent_image
After:  reference image → VAE Encode → (edit conditioning), sampler.latent_image
```

- Get Image Size and Empty Latent disappear, and there are fewer wires too.
- When it does not apply: denoise is smaller than 1.0 (the original picture remains and the result changes). The generation resolution is decided separately from the reference image.
- How to verify: whether the sampler's denoise is 1.0. At 1.0, the contents of the original latent do not remain in the result; only its resolution is used.

## Branches and options

### A switch that chooses one from candidate values (resolutions, prompts, and so on) is kept with Get Item From List or Create List

```
Before: candidate values A, B, C (resolutions, prompts, and so on) → (a switch that chooses one of several) → …
After:  candidates A, B, C → Create List → Get Item From List(index) → …   (choose by number)
        candidates A, B, C → Create List → …                              (run them all at once)
```

- Keep the ability to choose as a whole. Do not keep only the one that is currently chosen.
- A switch that chooses between ways of doing it is merged into the one the workflow's author chose, as in "Split" in SKILL.md.
- Where verified: comfy_extras/nodes_toolkit.py (Create List, Get Item From List). Whether the type of the chosen value matches where it plugs in is `canvas check`.

### Return a build that restricts the output's resolution or shape for no reason to the standard form

```
Before: latent of TextEncodeQwenImage21 → sampler.latent_image   (without a reference image, only a resolution × resolution square)
After:  Empty Latent Image → sampler.latent_image
```

- Write in the report that it was returned.
- When it does not apply: values or builds the author chose on purpose (hand-arranged sigmas, and so on).
- How to verify: in the node's source, how that output is decided (in this example, the latent's resolution).

## Turning custom nodes into core

### Build a combination of samplers in the simplest core form that gives the same calculation

```
Before: (a custom sampler, or SamplerCustomAdvanced + SplitSigmas + CFGGuider …)
After:  KSampler or KSamplerAdvanced (if it gives the same result)
        two stages (switching models between the first and second half, like high noise and low noise): KSamplerAdvanced ×2 (split with start_at_step and end_at_step)
```

- Do not copy the internals as they are. Among the forms that give the same calculation, choose the more readable one.
- When it does not apply: the stages are split by sigma values rather than by step. It uses its own scheduler (splitting by step does not give the same result).
- How to verify: read in the custom node's source what it calls internally. Map it to the core sampler's arguments (add_noise, return_with_leftover_noise, and so on).

### A sampler that removes all the noise: take its output

```
Before: SamplerCustomAdvanced.denoised_output → …
After:  SamplerCustomAdvanced.output → …   (when the last sigma is 0)
```

- When the last sigma is 0, all the noise is removed and output and denoised_output are the same. Taking it from output, as the name says, reads more easily.
- Does not apply: the sigmas do not end at 0 (stopping partway and handing over to the next stage, and so on).

## Rules of thumb (cannot be checked in the source)

### Latent upscale tends to degrade (recommend upscaling in pixel space)

```
Form to look for: … → Upscale Latent By → KSampler → …
```

- Do not change what was rebuilt. Write in the Caution of a Note that it is better to decode once and upscale as an image. Write it so that it is clear it is knowledge from experience.

### Most LoRAs for recent models do not train the text encoder

- Whether to connect the clip is decided by the file's header, as in the section "LoRA".
