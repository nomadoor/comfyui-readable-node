# Examples

Examples of how the rules in readable-form.md, techniques.md and notes.md applied in real workflows. They are taken from layouts nomadoor rebuilt by hand, and from corrections to agents' rebuilds. In the same situation, lean towards this form.

- "Before" is the form an agent built, "After" is the corrected form. "Layout" is the layout rebuilt by hand itself.

## Workflows rebuilt by hand

### Workflows with SamplerCustomAdvanced

**Flux, HunyuanVideo**
```
Layout: row 1: UNETLoader → (LoRA) → ModelSampling, RandomNoise
        row 2: DualCLIPLoader → CLIP Text Encode → FluxGuidance → BasicGuider (the conditioning wire is horizontal)
        SamplerCustomAdvanced at the vertical middle of the column on its left (RandomNoise, BasicGuider, KSamplerSelect, BasicScheduler, Empty Latent)
        VAELoader above SamplerCustomAdvanced
```

**Qwen-Image (hand-arranged sigmas), Flux (TeaCache), Flux Krea (redraw at 2x)**
```
Before: aligned BasicScheduler → SplitSigmas to the model row. Ran the VAE rail across the top
After:  to the left of SamplerCustomAdvanced, one column in input order (RandomNoise, BasicGuider, KSamplerSelect, the sigma node, Empty Latent)
        Load VAE above SamplerCustomAdvanced (to the upper left of VAE Decode). The width and height values below
        The VAE is carried sideways at its own height below
```

- The wire that loads the model and the nodes that make sigmas have different roles. Do not align them on the same row just because they are connected.
- Because the form in which inputs enter the sampler is always the same, the whole can be read.
- In this workflow, groups are used too (to guide the eye).

**MiniMax reference to video**
```
Before: copied the original workflow's SamplerCustomAdvanced + BasicGuider + KSamplerSelect + BasicScheduler as they were
After:  one KSampler (the same calculation)
```

- Do not be dragged along by the wiring of the original workflow.

### Single-stage workflows

**AnimateDiff**
```
Layout: Load Checkpoint → LoraLoader → CLIP Text Encode(+) → Apply ControlNet → KSamplerAdvanced at one height (the positive wire)
        The AnimateDiff nodes above, as a cluster. ADE_UseEvolvedSampling at the vertical middle of the three nodes that connect to it (not aligned to the height of LoraLoader)
```

**Anima drawn from a pose**
```
Layout: bottom row: Load Image → AnimaPoseControl → Resize → VAE Encode, Get Image Size, Empty Latent
        From there, one wire goes up to AnimaControlApply
        Load VAE below Resize. Connected directly to VAE Encode and VAE Decode. 0 Reroutes
```

**Anima with two reference images**
```
Layout: Load Image → AnimaRefEncode horizontal, each pair side by side, the two pairs stacked vertically
```

**Head swap with Krea2**
```
Before: meaningless Reroutes were left
After:  Load VAE to the left of the two VAE Encode. Connected directly to VAE Encode and VAE Decode
        Load Image → Resize, each pair side by side, the two pairs stacked vertically. Get Image Size and Empty Latent on the bottom row
```

**Relighting with IC-Light**
```
Layout: the foreground chain: Load Image and Resize below; from Remove Background on, it runs sideways on the row above
        The foreground chain, the IC-Light model and Apply share one colour
        The only Note is the model Note
```

- Do not write Notes on things that are clear by looking, such as background removal.

**Cutting out photos, stacking them and redrawing by depth (Create Layered Image and Add Layer)**
```
Layout: Add Layer from bottom to top: the background (forest) at the bottom, the person above it, the wolf at the top. layers is connected from bottom to top
        The LoRA chain and Conditioning (Combine) stay in processing order
        The ControlNet set (Loader, Depth Anything, Preview Image, Apply ControlNet) shares one colour
        Two Notes: the model Note, and one saying the stacking positions can be fixed in the editor
```

- A layer has the background at the bottom and things stacked on top. Making the nodes' up and down match that makes it intuitive. Only layers take this over processing order.

### Multi-stage workflows

**The later stage of SVD**
```
Layout: Image Only Checkpoint Loader and Video Linear CFG Guidance on a row above the main flow
        SVD_img2vid_Conditioning receives the image from the earlier stage's VAE Decode, horizontal with KSampler's positive input
```

**Z-Image Hires.fix → 4x upscale → face Detailer → person Detailer**
```
Layout: the loaders (Unet → ModelSamplingAuraFlow, Load VAE, Load CLIP) gathered at the upper left
        The five wires MODEL, VAE, CLIP, positive, negative run horizontally across the top of the whole as rails; each stage drops what it needs down from the rails
        Eye line: VAE Decode → Upscale Image (using Model) → FaceDetailer → DetailerForEach → Save Image at nearly one height. Large nodes share their top edge
        The stages left to right, in processing order. The first stage's Hires.fix (KSampler → Upscale Latent By → KSampler) keeps the basic form
        The face detection loaders and the person mask chain (Load Checkpoint → CLIP Text Encode → SAM3 Detect → MaskFix+ → MaskToSEGS) on the row one below the eye line, in processing order, just before where they are used
```

- No CFG value node is placed. The CFG 1.0 of a distilled model is not changed, so the value goes into each KSampler.

**Wan2.2 t2i, two samplers (low noise and high noise), then upscale and run again**
```
Layout: of the two model chains, the one that connects to the later sampler (low noise) on top. The wires do not cross
        One Load CLIP and one Load VAE. A rail hands them out to both stages
        The eye line runs from the first stage's VAE Decode to Color Match, the final output
        The positive text (Concatenate Text) above, the negative text (Text Multiline) below
```

**LTX 2.3, two stages (distilled, GGUF)**
```
Before: Load VAE and the audio VAE loader at the bottom left, with the VAE rail run under everything
        the model wire stretched diagonally and far to the second stage's CFGGuider
        the conditioning rail carried only the positive, with one Reroute; the negative was not on a rail
        SamplerCustomAdvanced → Separate AV Latent and LTXVCropGuides → LTXVLatentUpsampler diagonal
After:  VAE and model are handed out to the second stage on rails above (the loader at the head of the rail)
        positive and negative go on rails as a pair
        SamplerCustomAdvanced → Separate AV Latent horizontal. LTXVLatentUpsampler level with Concat AV Latent, Load Latent Upscale Model level with it
```

- Rails of values (fps and so on) may run below.

**Make an image with Kontext, then a video with Wan2.2**
```
Layout: the Kontext stage and the Wan stage left to right. The image from the Kontext VAE Decode crosses horizontally to the Wan stage (WanImageToVideo, CLIP Vision Encode, Get Image Size)
        The size comes from FluxKontextImageScale → Get Image Size → Empty SD3 Latent Image. Values typed by hand are not handed out
```

**AnimateDiff with a start image and an end image**
```
Layout: main flow: CLIP Text Encode(+) → Apply ControlNet (start) → Apply ControlNet (end) → AnimateDiffSampler
        Load Checkpoint at about the same height as the sampler. The MODEL and VAE wires pass above the nodes of the main flow
        The two keyframe chains (LatentKeyframeTiming → TimestepKeyframe → ACN ControlNet Loader) above the main flow, one row each. The one that connects to the later Apply ControlNet on top
        The two Load Image form a staircase at the very bottom. The size is put only in the first Resize Image/Mask (scale dimensions); the second is match size, and Empty Latent takes it from Get Image Size
```

**InstantID portrait (eye redraw → Hires.fix → eye redraw)**
```
Layout: the groups of the three stages share their top edge and height
        Three Load Image (the face photo, the kps image, the pose image). Which gets what cannot be seen by looking, so a Note is placed there
Fixed:  in the second eye redraw, positive and negative were connected the wrong way round (the workflow author's mistake)
        the middle ended in Save Image and the end in Preview Image (save the final one)
```

**SDXL t2i → skin redraw**
```
Layout: the earlier stage's image goes into 4 places in the later stage (VAE Encode, Apply ControlNet, GroundingDinoSAMSegment, ImageCompositeMasked)
        The whole later stage is lowered below that wire, a rail runs above it, and a wire drops down to each target
```

## Judgement examples (layout)

### The eye line is decided from the sampler

**SeedVR2 image upscale**
```
Before: made the input image's latent (VAE Encode → KSampler) horizontal, and put Load Diffusion Model below the eye line
After:  KSampler at the height where the positive and negative of Apply SeedVR2 Conditioning enter horizontally
        Load Diffusion Model above it. The input image chain (Load Image through VAE Encode) on the row one below. Load VAE below VAE Encode
        Only the one wire carrying the original image to Post-Process is a rail passing below
```

**Wan 2.2 I2V**
```
Before: put the main flow below CLIP Text Encode (the eye line too low)
After:  WanImageToVideo top-aligned with CLIP Text Encode. The main flow (WanImageToVideo → sampler → … → CreateVideo) continues right on that row
```

- Putting Load Checkpoint 400px above KSampler was too high (steerable motion). Undecided: how far is acceptable.

### The column of a sampler's sources

```
Before: because of the width of Empty Latent, CLIP Text Encode shifted one column left, and a gap opened where they should have been in the same column (Krea 2)
After:  what connects straight into the sampler (Load LoRA, Empty Latent Image, the two CLIP Text Encode) in one column, right-aligned
```

**Nodes with many inputs (WanAnimateToVideo, WanSoundImageToVideo, WanSCAILToVideo)**
```
Before: the sources of WanSCAILToVideo (8 inputs) were spread around it, and its wires crossed
After:  its sources in one column on its left, top to bottom in input order, right edges aligned, as for a sampler (`inputs`): positive, negative, VAE, pose video, its mask, reference image, its mask, CLIP Vision, size (a hand-made layout)
```
```
Before: put the chain that cuts the face out of the DWPose output above DWPose, to match the slot order (face_video above pose_video)
After:  put it below DWPose (match the flow of processing)
```
```
Before: WanSoundImageToVideo has 9 input slots in a row, so 700px was left between it and the prompt column
After:  pull the input loaders, Load Image and Load Audio close to the node that receives them, even at the cost of some wire overlap
```

- Aligning by the flow of processing is sometimes cleaner than aligning by the order of the input slots.

### Loaders and the model row

- Krea 2: the model row (UNET → LoRA → LoRA) is on top, and Load VAE is bottom-aligned with that row.

```
Before: ModelSamplingAuraFlow was far below the model loader (loader top y -444, ModelSamplingAuraFlow top y -106)
After:  Unet Loader (GGUF) and ModelSamplingAuraFlow top-aligned so the wire is horizontal
```
```
Before: lowered Load Checkpoint one row so that the CLIP wire would not pass behind the LoRA
After (as a preference): Load Checkpoint top-aligned with Load LoRA and FreeU
```
```
Before: bottom-aligned Load VAE with Load Image (height 424)
After:  Load VAE much higher (there is no point in bottom-aligning)
```

- MiniMax H3: VAE Decode and VAE Decode Audio go in the same column. There are many exceptions, so this is not made a rule.

### The row of an image chain

```
Layout: when an image chain starting at Load Image also connects to Get Image Size → Empty Latent Image, that chain goes on the bottom row, in one line with Get Image Size and Empty Latent Image
        To the other targets (ControlNet-type nodes on the model row, background removal and so on), wires go up from that row
```

- Nodes whose size tends to change (Load Image and so on) go low.

```
Before: put the Load Image that makes the depth map to the left of Load Depth Anything 3 (widens by one column)
After:  below Load Depth Anything 3
```

### A large input that breaks the core

```
Before: a node that takes 9 reference image slots, and 9 one-to-one Switch nodes. Lined up in input order, the Switch nodes piled up vertically in the same column as Load CLIP, Load VAE and the node that chooses the resolution, and the form of the core broke
After:  the group of Switch nodes is not lined up in the core's columns; it is built a little away, and only the result is brought into the core
```
```
Layout: Text to Image that composites a background and then applies a depth ControlNet. Load Image, background removal and the layer stacking are placed to the left of Load Checkpoint (up to 1280px), and only the result is drawn into the core
```

- Preparation far from the core is not part of the core.
- The number of inputs changes with autogrow, so it cannot be decided neatly. Judge by how the form breaks.

### One long wire in a single-stage workflow

```
Layout: in a single-stage workflow where the loader's VAE goes into both VAE Encode and VAE Decode, no rail is used; both are connected directly (0 Reroutes)
        Text to Image with a pose reference image: the image chain (Load Image → … → VAE Encode, Get Image Size → Empty Latent Image) on the bottom row, Load VAE next to that row's VAE Encode. The wire to VAE Decode runs diagonally between the nodes
        Relighting Text to Image: the wire from Load Checkpoint's VAE to VAE Decode runs diagonally and passes behind Load Diffusion Model on the way (allowed)
```

### Spacing and width

```
Before: in a Kontext + LoRA workflow, 150px was left between Load LoRA and KSampler (gap 150 in the plan)
After:  do not widen the space to a neighbour connected by a wire without a reason
```

- KSampler, Load Diffusion Model and the like keep their initial width. Do not make them narrower.
- CLIP Text Encode (400) and Empty Latent Image (270) do not get their widths aligned even in the same column (the difference is larger than the gap between columns).
- Conditioning Zero Out goes below the positive CLIP Text Encode. Do not open a large gap for a node that only puts a value into negative at CFG 1.0.

### Nodes that change size

- Save Image and Load Image are nodes for checking the output and the input. Do not pack them; give them a size at which the preview can be seen. Even in a small workflow such as a face swap, shrinking Load Image to pack things makes it harder to read than the original workflow.
- Do not fold Preview Image back below its source (it breaks the left-to-right flow).

```
Before: lifted the save and Preview nodes upward to avoid wires, and because of that a rail stretched upward
After:  do not jump them upward (the problem is less putting them above than the rail stretching upward)
```

### Exceptions to backward wires

- When an upscale or interpolation group is placed on the row one below the main flow, the wire from the main flow's VAE Decode to the first node of the lower row may go back down to the left. Undecided: where to draw the line.

### Groups

```
Before: in a two-stage LTX 2.3 workflow, the decode of the Stage 1 result and the decode after upscaling were put in one group "Decode"
After:  split the groups (having two decodes is fine, as in the original workflow)
```

- Do not put things that are different functions and output different outputs in one group.

## Judgement examples (content)

### Build a size from what the size is for

```
Before: in Qwen-Image-Layered, to split an input image into layers, the size of the empty latent was copied as the original 640×640
After:  Load Image → Scale Image to Total Pixels (0.5 MP) → Get Image Size → empty latent. The shrunk image also goes into VAE Encode
```
```
Before: in Wan 2.2 S2V, the width and height of the workflow author's ImageResize+ (fit into an 832×480 frame) were copied with expressions that give the same values
After:  resize the image to 0.4 MP (round the resolution to the model's multiple), and take width and height with Get Image Size. As a reference image too, it is lighter to resize before feeding it in
```
```
Before: in Wan 2.2 Animate, the same size and length were taken from two separate places with two Get Image Size
After:  take them from one place
```

### Samplers that split one continuous setting

```
Before: 30 steps split into three KSamplerAdvanced (0–10, 10–20, 20–end), with a different seed per stage (add_noise disable for the 2nd and 3rd)
After:  30 steps in one KSampler. Write the difference in the report
```

- The only difference is how the noise comes out at each step of an ancestral sampler. Splitting has no meaning and invites misunderstanding.

### Unconnected parts, disabled branches, branches that differ in method

- Resolution samples the workflow's author prepared (26 Empty Latent Image connected to nothing; to use one, you rewire it by hand): the nodes are removed, and the values kept as a table in the Note on Empty Latent Image.
- A finished stage not connected to the output (the Chroma and SDXL stages of a model comparison workflow; they stop at VAE Decode, and the workflow author's Note says "add Stitch to put it in the comparison row"): left unconnected, and how to connect it written in a Note.
- A bypassed branch whose sources are all empty, so it is unclear what it was meant to connect to (a group whose Chinese name means "local inpainting"; its inputs are Get nodes with empty names): it does not work as a workflow, so it is removed as debris and mentioned in the report.
- A switch between Tiled VAE Decode and ordinary VAE Decode (Boolean → Switch): a difference of method, with or without a speed-up. Keep the one ordinary VAE Decode the workflow's author had enabled.

### Choosing a replacement

```
Before: built Compositor3 (a custom node that stacks images by dragging on the screen) from Image Composite Masked and scaling and flipping nodes
After:  core's Create Layered Image and Add Layer (positions can be fixed in the editor)
```

- A form where position and size are typed as numbers is hard to use even if it can be built. Choose the one that keeps the user's operation (dragging).
- Create Layered Image and Add Layer are experimental nodes, usable only in Nodes 2.0, and their UI is not easy to use either.

### Names

```
Before: used the workflow author's group name "Upscale" as it was (the content enlarges with an upscale model and then redraws at denoise 0.2)
After:  a name that fits the content (a variant of Hires.fix, Enhance, and so on)
```

## Note examples

In each, the before only set down facts. The after says the point in the heading (for a warning, the caution), and keeps what is below it short.

**The finishing upscaler has a value that makes the image smaller (Caution)**
```
Before: The image going into SeedVR2 is 1200×1600 (960×1280 at 1.25x), but resolution is 896, so the short side is shrunk to 896.
After:  ### With the current value, the image gets smaller at the finish
        resolution is not the upscale ratio but "how many px the short side of the result should be".
        The short side of the image arriving here is 1200px, so 896 shrinks it. To enlarge it, set it above 1200.
```

**A cfg-distilled model with cfg at 1.1 (Caution)**
```
Before: The negative text works well on the Base version. On the Distill version it works weakly, so it can be left empty (the author's explanation)
After:  ### With cfg at 1.1, most of the Distill version's speed is lost
        The Distill version is a model built to draw at cfg 1.0 without computing negative.
        Raising cfg above 1.0 makes negative computed too, and the time per step nearly doubles.
```

- The workflow author's explanation (works weakly) had the wrong reason, so it was not used.

**What was not written**: sentences reading the nodes aloud from left to right, explanations of why things were connected this way, explanations of a graph that is only for looking, things everyone who uses ComfyUI knows (negative has no effect at cfg 1, and so on).

## Undecided

- **Parts-shelf workflows.** A workflow where many groups are switched with bypass and assembled for each use does not fit in one workflow.
  - One direction: split it by function. Processing applied to the finished image (Detailer, Upscale, effects and so on) is post-processing; introduce in the conversation what is there and ask whether the user wants any of it. If not, build only the main Text to Image.
  - Decided: do not remove disabled functions. If they can be split, split them and prepare them. Losing functions does not respect the original workflow.
  - Among the generation parts, the ones worth a workflow of their own are those that change what can be done (Text to Image, Regional Prompting, ControlNet LLLite, Image to Image). A part that "might make things a little better", such as CFGZeroStar, is no reason for a separate structure.
- **Whether to split a multi-stage workflow.** A workflow where a later stage uses the result of an earlier stage.
  - The form so far: when what passes from the earlier stage to the later stage is a single image (or video), both a version kept connected and tidied and a split version (the later stage starts from Load Image) were produced. Post-processing where the later stage has no sampler, hires fix or refiner continuing in LATENT, and ones that share models or conditioning were kept as one.
  - This line was drawn from examples and is not decided. Think from 1 task = 1 workflow, and report it when unsure.
- **A switch with only one input.** Removing it breaks equivalence. Keeping it means carrying many values, which gets messy. (Decided: saving with metadata [Image Saver + Civitai Hash Fetcher and so on] is kept as a function of the workflow's author.)
- **Workflows that are too complex.** How to handle workflows with many nested subgraphs that expand to hundreds of nodes (chains of regular expressions that build text, and so on).
- **Conditional branches written in regular expressions.** Dozens of regular expressions in a row, branching on tags in the text. They cannot be changed. Leaving them as a subgraph may be easier to read.
- **What to hand over when splitting.** If what the workflow author's wireless nodes (Image Sender and so on) were sending is turned directly into Save Image → Load Image, the later workflow may apply the same processing (OpenPose and so on) again.
- **Make the wire horizontal, or align the top edges.** In the hand-made layout examples, the horizontal wire wins almost everywhere. The only pair with aligned top edges was AnimateDiff's Latent Keyframe Timing → Timestep Keyframe. How to tell when to take the top edge is not known.
- **Put a node that gathers inputs at the middle of its sources, or align its top edge with its neighbour.** Where Detailer's Simple Detector (three inputs) and SEGS Filter sit side by side, it was corrected because their top edges were not aligned.
- **How to route a single wire when even the output's height hits a node.** Whether to escape above or below.
- **Two Preview Image nodes that show what one node made, next to the sampler.** A rebuild stacked them in the column left of KSampler, so one sat directly below the other (Preview grows). Stepping the lower one to the right put it directly below KSampler instead. Side by side, stacked, merged into one Preview: not decided.
- **When a wire may pass behind nodes.** A wire where it is naturally clear which is where it goes in behind and where it comes out does not need to be lifted with Reroutes (for example, the VAE wire from Load Checkpoint to VAE Decode going in behind KSampler as one wire and coming out as one). Candidate guides are few crossings and no running backwards. It has not been made into a form that can be counted.
- **Whether to simplify a size calculation the workflow's author built.**
  - In a two-stage LTX 2.3 workflow, the workflow's author passed an empty 64×64 latent through the upscale model to measure the ratio (1.5 or 2), rounded the finished size down to a multiple of 96 or 64, and got the Stage 1 size (6 nodes). Even if the upscale model is swapped between x1.5 and x2, the size matches automatically.
  - The LTX 2.5 workflow on nomadoor's site gets the Stage 1 size with Resolution Selector (multiple 64) → Math "a / 2" (3 nodes, a single x2 upscale model). It is no longer equivalent, but it can be written much more simply.
