# Examples

How the rules applied in real workflows: "Layout" under the section headings of readable-form.md, then "Content" and "Notes" by topic. "Before" is a form an agent built, "After" the corrected form, "Layout" a layout arranged by hand. In the same situation, lean toward this form.
An example marked **Exception (<rule>)** is a correct counter-example: there that rule gives way. Every other example is a rule applied as written.

## Layout

### 1. The usual form

**Text to image with SamplerCustomAdvanced (Flux, HunyuanVideo, Qwen-Image with hand-made sigmas)**
```
Layout: row 1: UNETLoader → (LoRA) → ModelSampling, RandomNoise
        row 2: DualCLIPLoader → CLIP Text Encode → FluxGuidance → BasicGuider (the conditioning wire is horizontal)
        SamplerCustomAdvanced at the vertical middle of the column on its left (RandomNoise, BasicGuider, KSamplerSelect, the sigma node, Empty Latent)
        Load VAE above SamplerCustomAdvanced (to the upper left of VAE Decode)
Before: BasicScheduler → SplitSigmas aligned to the model row; the VAE run across the top on a rail
```
- The wire that loads the model and the nodes that make sigmas have different roles; do not put them on one row because they are connected.

**The outputs (VAE Decode → Save Image → Compare)**
```
After: Save Image, which matters more, stands next to VAE Decode; Compare where its wires need the fewest Reroutes (right of Save Image or below it)
       The wire to Compare passed behind Save Image: one of them steps down so the wire passes above
       When Compare's other input comes on a rail, Compare is set at the rail's height so no Reroute is needed before it
After: a stage whose result is made by another node than VAE Decode (Merge List of Tiles to Image after redrawing tiles): Save Image next to that node
```

**One latent node between two samplers (Hires.fix: KSampler → Upscale Latent By → KSampler)**
```
Before: Upscale Latent By set lower so its wire into the second KSampler was level; the longer wire from the first KSampler slanted
After:  Upscale Latent By on the eye line, its top edge on the KSamplers'; the longer wire from the first KSampler is level, the short one into the second KSampler slants
```

**A stage whose conditioning node stands just left of its sampler (MiniMax H3 hires fix, image to video)**
```
Before: the chain (Separate AV Latent → Latent Upscaler → Concat AV Latent) at the height of the second KSampler's latent slot, the wire from the first KSampler slanting into it
After:  MiniMax H3 Image to Video just left of the second KSampler, its positive level; the chain below that column (under Conditioning Zero Out)
```

**A stage with SamplerCustomAdvanced taking the previous stage's latent (KSampler → Upscale Latent By → SamplerCustomAdvanced)**
```
Before: Upscale Latent By at the first KSampler's height, left of the sources column, its wire from the KSampler level
After:  Upscale Latent By at the bottom of the sources column (the latent is the last input); both its wires slant
```

**Stages in a row (t2i → tiled upscale, t2i → Hires.fix → upscale)**
```
Before: the upscale stage 500px below the first; the image lifted with Reroutes and lowered again
After:  the upscale stage's first node level with the first stage's VAE Decode; the image goes straight on
        Save Image of the first stage steps down so that wire passes above it
```

### 2. Nodes

- Shrinking Load Image to pack a small workflow makes it harder to read than the original.
- Two Preview Image of the same image: one. A Preview and a Compare of one result: stacked in one column.

### 3. Wires

**A single value going far**
```
Layout: in a single-stage workflow where the loader's VAE goes into both VAE Encode and VAE Decode, no rail; both wired directly
        Relighting Text to Image: the VAE wire from Load Checkpoint to VAE Decode runs diagonally behind Load Diffusion Model (no other wire crosses it behind the node)
```

**Reroutes that are not needed**
```
Before: two samplers side by side (KSamplerAdvanced ×2, Wan 2.2 high noise and low noise) took the same positive and negative from a rail
After:  wired directly, passing behind the first sampler; without Reroutes it is still clear where the wires go
Before: a Reroute right after the source lifting its output, then the rail (a seed, a Wildcard Processor, Load Image → Split Image into List of Tiles)
After:  the source moved to the height of the rail (or the rail kept at the source's output height)
Before: the image from an upscaler to Save Image and Compare right after it, through Reroutes
After:  wired directly
```

**Which wire is horizontal**
```
Before: Resize Image/Mask (match size) took the image it matches on a horizontal wire, and the Load Image it resizes from below on a slant
After:  Load Image → Resize Image/Mask → Stitch Images on one horizontal line; the wire into match slants (Wan 2.1 Fun Control)
Before: LTXV Conditioning set midway between the positive and negative encoders; the AV latent split's VAE Decode midway between its video and audio wires (LTX 2.5)
After:  the positive wire into LTXV Conditioning horizontal; the video latent into VAE Decode horizontal (midway is a liking, not needed)
Before: Detailer's Simple Detector and SEGS Filter side by side, the SEGS wire between them slanting
After:  the SEGS wire horizontal (both slots are the first, so their top edges align)
```

### 4. Flow and position

**The band is decided from the sampler**
```
Before (SeedVR2): Load Diffusion Model below the band
After:  KSampler where Apply SeedVR2 Conditioning's positive and negative enter horizontally; Load Diffusion Model above
Before (Wan 2.2 I2V): the main flow below CLIP Text Encode (the band too low)
After:  WanImageToVideo top-aligned with CLIP Text Encode; the main flow continues right on that row
```

**Nodes with many inputs (WanAnimateToVideo, WanSoundImageToVideo, WanSCAILToVideo)**
```
After: its sources in one column on its left, top to bottom in input order, right edges aligned (`inputs`)
Before: the model row (… → Skip Layer Guidance → EasyCache) ending at the right edge of the text encoders, one column left of WanFunControlToVideo, the sampler's source column
After:  the model row ending at WanFunControlToVideo's right edge; when the gap left of that column is wide, the model row ends there too (Wan 2.1 Fun Control)
Before: WanSoundImageToVideo's 9 input slots in a row left 700px between it and the prompt column
After:  Load Image and Load Audio pulled close to the node that receives them
```

**The row of an image chain**
```
Layout: an image chain from Load Image that also goes to Get Image Size → Empty Latent goes on the bottom row, in one line with them;
        wires go up from that row to other targets (ControlNet, background removal)
Before: the Load Image for a depth map left of Load Depth Anything 3 (one more column)
After:  below Load Depth Anything 3
Before: the mask chain raised from the bottom row to a middle row (SDXL inpaint)
After:  on the bottom row, its wires level
```

**Preparation**
```
Before: a node with 9 reference image slots and 9 Switch nodes piled in the column of Load CLIP and Load VAE; the core's form broke
After:  the Switch nodes built a little away; only the result comes into the core
Layout: a background composite before a depth ControlNet: Load Image, background removal and layer stacking left of Load Checkpoint
```

**Stages switched on and off in a row**
```
Before (four post-processing stages, each a group with its own Boolean that switches two If/Else Switches, one for the image and one for the file name): the image Switches at a different height in each group; the Booleans and a long Note inside the groups, so every group, its top and bottom aligned with the others, grew to the tallest
Layout: the image Switches of all stages, the loader and the saver at one height, so the line that passes the stages is one horizontal line from the first node to the last; the file-name Switches at one lower height, a second line; the Booleans in a row above the groups, outside them, their Notes above them; the long Note below its group, outside it
```

**Layers, same-shape chains**
- **Exception (sources in the order of the inputs)**: nodes that stack layers (Add Layer → Create Layered Image) go from the bottom up, background at the bottom. Only these.
- Two chains of the same shape (Wan 2.2 high and low noise; two AnimateDiff keyframe chains): the one for the later node on top, so their wires do not cross.
- **Exception (sources in the order of the inputs)**: in Wan Animate, WanAnimateToVideo's face_video slot is above pose_video, yet the chain that cuts the face out with SDPose (SDPose Face Bounding Boxes → Crop By BBoxes) stands below the DWPose chain.
- **Exception (sources in one column)**: several large loading nodes (Load Image, Load Video) into one node: a staircase, the first at the upper left at its slot's height, the next lower right. Stacked in one column they make the workflow too tall.

**Spacing**
```
Before: 150px between Load LoRA and KSampler
After:  no wider space to a wired neighbor without a reason
```

### 5. Loaders

```
Layout: basic t2i: Load VAE above the KSampler (it is first used by VAE Decode)
Layout: Load VAE next to the VAE Encode of the bottom row when it is first used there (Anima pose, Krea2 head swap, SeedVR2)
Layout: an edit (Flux.2 Klein, Anima with Klein): Load VAE below the text encoder; without a Reroute, between Conditioning Zero Out and Resize Image
Before: a second Load Checkpoint used only from the third stage, at the far left with a long diagonal wire
After:  in the column left of its first user
Before: Load Upscale Model at the far left, feeding one node
After:  right next to that node
Before: the loader column left-aligned with the wider Text (Multiline) column below
After:  right-aligned (its outputs closer to their users)
Before: ModelSamplingAuraFlow far below the model loader
After:  level with it, so the model wire is horizontal
Before: Load VAE bottom-aligned with Load Image (height 424)
After:  much higher (no reason to align with it)
Before: Load VAE at the top of the loader column, above two Unet Loaders (Wan 2.2 GGUF)
After:  below the model loaders
Before: the model row 400px above KSampler, an empty gap between it and the nodes below
After:  the loaders placed in order from the top, with no empty gap
Layout: a single stage: Load Checkpoint just left of the text encoders (its CLIP goes there; its model reaches KSampler without a wire going back)
```
- VAE Decode and VAE Decode Audio (MiniMax H3, LTX) stand in the same column.

### 6. Value nodes

- The cfg 1.0 of a distilled model is not changed, so it stays in each KSampler; no cfg value node.
- Sizes typed by hand once are not handed out; a size the author measures from an image comes from Get Image Size.

### 7. Groups and color

- A two-stage LTX workflow has three groups (stage 1, stage 2, decode). A t2i with IPAdapter has no group.
- A Detail pass whose every node was colored green inside its group: the group already guides the eye.
- Color split finely (SCAIL 2): the core green; taking the person in the input video pale_blue; taking the person in the reference image cyan; CLIP Vision brown.
- In that two-stage LTX workflow, when the Stage 1 result is decoded too, that decode belongs to the stage 1 group; only the decode after upscaling is in the decode group.

### 8. Names

```
Before: the author's group name "Upscale" kept (the content enlarges with an upscale model and then redraws at denoise 0.2)
After:  a name that fits the content (a variant of Hires.fix)
Before: a node title in Chinese the author gave (on Mahiro)
After:  ComfyUI's display name
```

## Content

### Split

```
One: base → refiner → Hires.fix (conditioning passes on), with the film grain and color correction on the finished image
Split: nine models with their own sampler settings × t2i and i2i = eighteen workflows
Split: a prompt written by hand or by an MLLM from an image, one side bypassed in the author's workflow: two text-to-image workflows, one with the MLLM and one without
Before: an Anima LLLite guide, its nodes in no group, switched on and off with bypass in one workflow
After:  two workflows, with LLLite and without
```

### Fix

```
Before: two KSampler (Advanced) in a row, both adding noise from step 0; the second redraws the first's result entirely; kept with a Caution
After:  the first removed, reported
Before: 30 steps split into three KSampler (Advanced) (0–10, 10–20, 20–end) with a different seed each
After:  one KSampler with 30 steps; the difference reported
Before: looping once and looping twice saved through two Create Video and Save Video
After:  one Create Video and Save Video; bypassing Batch Images switches between once and twice
```

### Sizes from what they are for

```
Before: the empty latent size copied from the original (640×640) to split an input image into layers
After:  Load Image → Scale Image to Total Pixels (0.5 MP) → Get Image Size → empty latent; the shrunk image also into VAE Encode
Before: the width and height of the author's ImageResize+ (fit into 832×480) rebuilt as expressions
After:  resize the image to 0.4 MP (rounded to the model's multiple) and take width and height with Get Image Size
Before: the same size and length taken from two places with two Get Image Size
After:  from one place
```

### Unconnected parts and disabled branches

- Resolution samples the author prepared (26 Empty Latent Image connected to nothing): removed, the values kept as a table in the Note on Empty Latent Image.
- A finished stage not connected to the output, with the author's Note saying how to connect it: left unconnected, and how to connect it written in a Note.
- A bypassed branch whose sources are all empty: it cannot work, so it is removed as debris and reported.
- A switch between Tiled VAE Decode and VAE Decode: keep the one the author had enabled.
- A switch choosing the base image of an i2i among three generated patterns (random shapes, a binary pattern, a gradient; the author's choice enabled, the other two groups muted): all three kept, the switch replaced by Branch (inputs named for the patterns), the groups unmuted. Every function is kept first; then the workflow is split as Split says.

### Choosing a replacement

```
Before: copied SamplerCustomAdvanced + BasicGuider + KSamplerSelect + BasicScheduler as they were (MiniMax reference to video)
After:  one KSampler (the same calculation)
Before: Compositor3 (stacks images by dragging) rebuilt from Image Composite Masked and scaling nodes
After:  core Create Layered Image and Add Layer (positions fixed by dragging in the editor)
After:  tiles: Split Image into List of Tiles → redraw each → Merge List of Tiles to Image (in place of Ultimate SD Upscale)
        Color Transfer only when the original workflow uses it; with Qwen Image 2.1, whose VAE outputs RGBA, Split Image with Alpha before it
Kept:   a crop whose region comes in by wire (core Crop Image cannot take it by wire)
```

## Notes

Each before only set down facts; the after says the point in the heading and keeps what is below it short.

**The finishing upscaler has a value that makes the image smaller (Caution)**
```
Before: The image going into SeedVR2 is 1200×1600, but resolution is 896, so the short side is shrunk to 896.
After:  ### With the current value, the image gets smaller at the finish
        resolution is not the upscale ratio but the short side of the result. The image arriving here is 1200px, so 896 shrinks it.
```

**A cfg-distilled model with cfg at 1.1 (Caution)**
```
Before: The negative text works weakly on the Distill version, so it can be left empty (the author's explanation)
After:  ### With cfg at 1.1, most of the Distill version's speed is lost
        Raising cfg above 1.0 makes negative computed too, and the time per step nearly doubles.
```

**Not written**: "16:9 is 1088, not 1080, to divide by 16" (rounding to the model's multiple is expected); "un-bypass the blue nodes" (point at nodes by name); "according to the author, swap in Unet Loader (GGUF)" (a checkable step is written plainly).
