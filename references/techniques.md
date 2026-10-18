# Building techniques

Techniques for building, with core nodes, the most straightforward graph from what the workflow means (what this task is trying to do). Do not copy how the author arranged the nodes; if there is a better way to build the same thing, build it that way.

- These are not rules. Whether one applies is judged from the meaning. Also look at each item's "When it does not apply". If there is nothing to rebuild, leaving it as it is is fine.
- Before using one, confirm in object_info that the needed nodes (and the options of the mode you use) exist. Depending on the user's ComfyUI version, they may not exist yet.
- Confirm the behavior with the method written under "How to verify" before using it. (Undecided: verifying with a small run conflicts with SKILL.md's "run ComfyUI only when the user asks". See SKILL.md.)
- Version verified against: ComfyUI 0.39.0.

## Do not line up copies of the same shape

### Identical chains lined up with only one value changed become one chain with a list

- **When to use:** When chains of the same shape (LoRA → KSampler → VAE Decode → Save Image, etc.) are lined up many times with only one value changed. Comparing LoRA strengths, comparing seeds, and so on.
- **How to build:** Put each value to vary into its own value node such as Float or Int, gather them with Create List (utilities), and connect it to that value's input. Place only one chain. A node that receives a list is executed per element, and everything after it also flows per element.
  - If the same value goes into two places (LoRA's strength_model and strength_clip), connect the same Create List to both.
  - If lists go into two places, they are not multiplied. They are paired in element order (1st with 1st, 2nd with 2nd). If the lengths differ, the last element of the shorter one is repeated. The number of executions is the length of the longest list.
  - One Create List holds up to 10 items.
  - If downstream there is a node that receives the list all at once (one that takes its input as a list), the list is merged into one there.
  - If the per-branch save filenames ("LoRA1" to "LoRA4", etc.) exist only to tell the files apart, do not make a list of names. Use one filename_prefix and leave it to Save Image's sequence number (within one execution, the number order is the list order). In a nearby Note, write "Files are saved in the order of the list."
- **When it does not apply:** Two or more values differ per branch (both the strength and the prompt differ, etc.). Different processing has been added per branch.
- **For the reader:** Some people do not know Create List, so add one line in a nearby Note: "One image is generated for each of these values."
- **How to verify:** `_async_map_node_over_list` in ComfyUI's execution.py (`slice_dict` takes the i-th item, or the last one if there are not enough). Small run (Undecided: see SKILL.md): put Create List [1, 2] and [10, 20] into Math Expression (a + b) and output to Preview Any; two results, 11 and 22, come out.

## Decide sizes in one place

### Keep size values in only one place

- **When to use:** When the author has put the same value in many places, for the generation size and for the size the loaded image is matched to (three or four links coming out of a value node).
- **How to build:** Put the value in only one place (such as scale dimensions of the first Resize Image/Mask). Match the other images to that result with Resize Image/Mask's "match size". Take the Empty Latent's size from that image with Get Image Size.
- **When it does not apply:** Values that are the same but mean different things (ones meant to have only one of them changed later, the generation size and the save size, etc.).
- **How to verify:** That Resize Image/Mask's resize_type has "match size" and that Get Image Size exists (object_info). Whether match size's crop is the same as the original build (cropping the center, etc.).

### If another node resizes the image later, take the size from that result

- **When to use:** When a node partway through resizes the loaded image further, and the Empty Latent after it uses a value typed in by hand. The hand-typed value drifts from the size the node partway through changed it to.
- **How to build:** Take the size with Get Image Size from the image after the resize, and put it into Empty Latent.

## Do not line up the same operation in a row

### Text replacements lined up in a row become one RegexReplace

- **When to use:** When many Replace Text (StringReplace) nodes are chained on the same text, replacing several words with the same word.
- **How to build:** One RegexReplace, with a single pattern like `image|photo|picture`.
- **Watch out:** Replace Text is case-sensitive and does not look at word boundaries. RegexReplace's case_insensitive is on by default. To keep it the same as the original, turn case_insensitive off. Adding `\b` to the pattern drops words like "images" from the target and changes the result from the original. Which to choose is decided by meaning.
- **When it does not apply:** Each word is replaced with a different word.

### Concatenate Text becomes one Format Text

- **When to use:** When text is joined with Concatenate Text (StringConcatenate). Both when many are joined into a chain and when there is only one (two inputs). The node gets smaller.
- **How to build:** In one Format Text (StringFormat, utilities), put the texts to join as inputs a, b, c…, and write the separators in f_string (`{a}, {b}\n{c}`, etc.). The chain of concatenations disappears.
- **Watch out:** If an empty text goes in, the separator stays (`{a}, {b}` with a = "cat", b = "" gives "cat, "). Concatenate Text does the same, so nothing changes from the original.
- **How to verify:** Small run (Undecided: see SKILL.md): put "cat" and "dog" into Format Text with f_string `{a}, {b}` and output to Preview as Text; you get "cat, dog".

## Do not put view-only nodes in the flow

### A node that only shows a value becomes a Preview as Text on a branch

- **When to use:** When a node such as ShowText or easy showAnything, which displays the value it receives and passes it straight on, sits in the middle of the flow.
- **How to build:** Remove that node and connect the nodes before and after it directly, then run one branch from the value you want to see into Preview as Text (PreviewAny). It shows not only text but also numbers and conditioning. Because it is not in the flow, the view-only node can be moved freely without being tied to the flow.
- **Watch out:** Preview as Text also has a STRING output, but do not connect anything onward from it (that would put it back in the flow).
- **How to verify:** In object_info, PreviewAny's input is `source` (accepts anything).

## Building custom nodes with core

### Do not copy the internals as they are; use a readable form of the same computation

- **When to use:** When rebuilding the internals of a custom node (a combination of samplers, etc.) with core.
- **How to build:** Among the forms that give the same computation, choose the more readable one. If KSampler or KSamplerAdvanced gives the same result, do not break it down into SamplerCustomAdvanced + SplitSigmas + CFGGuider.
  - A two-stage sampler (one that switches models between the first and second half, like high noise and low noise) becomes two KSamplerAdvanced (split with start_at_step and end_at_step).
- **When it does not apply:** The custom node splits the stages by sigma values rather than by step, or uses its own scheduler (splitting by step does not give the same result).
- **How to verify:** Read in the custom node's source what it calls internally. Map it to the core sampler's arguments (add_noise, return_with_leftover_noise, etc.).

### ImageResizeKJ (v1, fit into a square box and center-crop to a multiple of 8) becomes two Resize Image/Mask

- **When to use:** When ImageResizeKJ (v1) has keep_proportion on and width and height are the same (a square box).
- **How to build:** Resize Image/Mask with "scale longer dimension" (match the longer side), followed by "scale to multiple" (to a multiple of 8). The size and the center crop come out the same. KJ crops first and then scales, while core scales to cover and then crops, so the pixels differ slightly.
- **When it does not apply:** The box is a rectangle (width and height differ). ImageResizeKJv2 (has more kinds of keep_proportion).
- **How to verify:** `scale_to_multiple_cover` in comfy_extras/nodes_post_processing.py. That Resize Image/Mask's resize_type has "scale to multiple".

### Apply ControlNet (DEPRECATED) becomes Apply ControlNet

- **How to build:** The old one receives one conditioning and also acts on the negative side. The new one (ControlNetApplyAdvanced) receives positive and negative, so connect negative too.
- **How to verify:** ControlNetApply and ControlNetApplyAdvanced (control_apply_to_uncond) in nodes.py.

## From experience (the source is experience; this cannot be verified in source code)

- Upscaling while still in latent (Upscale Latent By) tends to degrade the image. It is better to decode once and upscale as an image. Do not change what was rebuilt; tell the user in each part's Note (caution) and in the report. When writing it, write it so that it is clear this is knowledge from experience.
- An output that only decodes and shows a latent from partway through a stage (before it has finished drawing) just makes things heavier and is meaningless. Delete it and write it in the report.

## Reuse what is already at hand

Reuse what is already at hand. If the same thing is already flowing, do not make a new one. Keep a build that lets the user choose, choosable as it is.

### Put the existing latent straight into latent_image

- **When to use:** In a workflow that VAE Encodes a reference image (Image Edit, etc.), when the generation latent is made separately with Get Image Size → Empty Latent.
- **How to build:** Put VAE Encode's latent straight into the sampler's latent_image. Get Image Size and Empty Latent disappear, and there are fewer links.
- **When it does not apply:** denoise is smaller than 1.0 (the original picture remains; the result changes). The generation size is decided separately from the reference image.
- **How to verify:** Whether the sampler's denoise is 1.0. At 1.0, the contents of the original latent do not remain in the result; only its size is used.

### A build that lets the user choose uses core lists and selection

- **When to use:** A workflow that lets the user choose one of several options with a Muxer or a switch.
- **How to build:** Do not keep only the one that is currently selected. To choose by number, use Get Item From List; to run them all at once, use Create List. Keep the ability to choose as a whole.
- **How to verify:** Whether the nodes to use exist (object_info). Whether the type of the chosen value matches where it is plugged in (`canvas check`).

### Undo builds that narrow what the user can do for no reason

- **When to use:** When the author's way of building narrows what the user can do. Example: in Text to Image, using TextEncodeQwenImage21's latent means that without a reference image only a resolution × resolution square can be made.
- **How to build:** Return it to the ordinary form (in this example, Empty Latent Image). Write in the report that it was returned.
- **When it does not apply:** Values or builds the author chose on purpose (hand-arranged sigmas, etc.).
- **How to verify:** In the node's source, how that output is decided (in this example, the latent's size).
