# Examples

How the rules applied in real workflows: "Layout" under the section headings of readable-form.md, then "Content" and "Notes" by topic. "Before" is a form an agent built, "After" the corrected form, "Layout" a layout arranged by hand. In the same situation, lean towards this form.

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

**A SamplerCustomAdvanced setup that is one KSampler (MiniMax reference to video)**
```
Before: copied SamplerCustomAdvanced + BasicGuider + KSamplerSelect + BasicScheduler as they were
After:  one KSampler (the same calculation)
```

**The outputs (VAE Decode → Save Image → Compare)**
```
After: Save Image, which matters more, stands next to VAE Decode; Compare where its wires need the fewest Reroutes (right of Save Image or below it)
       The wire to Compare passed behind Save Image: one of them steps down so the wire passes above
       When Compare's other input comes on a rail, Compare is set at the rail's height so no Reroute is needed before it
After: a stage whose result is made by another node than VAE Decode (Merge List of Tiles to Image after redrawing tiles): Save Image next to that node
```

**Stages in a row (t2i → tiled upscale, t2i → Hires.fix → upscale)**
```
Before: the upscale stage 500px below the first; the image lifted with Reroutes and lowered again
After:  the upscale stage's first node level with the first stage's VAE Decode; the image goes straight on
        Save Image of the first stage steps down so that wire passes above it
```

### 2. Nodes

- Save Image and Load Image are for checking the output and the input: give them a size at which the preview can be seen. Shrinking Load Image to pack a small workflow makes it harder to read than the original.
- Two Preview Image of one node next to the sampler, stacked in the column left of KSampler: the lower one stood right below the upper. Undecided: side by side, stacked, or merged into one.

### 3. Wires

**A single value going far**
```
Layout: in a single-stage workflow where the loader's VAE goes into both VAE Encode and VAE Decode, no rail; both wired directly
        Relighting Text to Image: the VAE wire from Load Checkpoint to VAE Decode runs diagonally behind Load Diffusion Model (way in and way out plain to see)
```

**Reroutes that are not needed**
```
Before: two samplers side by side (KSamplerAdvanced ×2, Wan 2.2 high noise and low noise) took the same positive and negative from a rail
After:  wired directly; without Reroutes it is still clear where the wires go
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
```

### 4. Flow and position

**The band is decided from the sampler**
```
Before (SeedVR2): Load Diffusion Model below the band
After:  KSampler where Apply SeedVR2 Conditioning's positive and negative enter horizontally; Load Diffusion Model above
Before (Wan 2.2 I2V): the main flow below CLIP Text Encode (the band too low)
After:  WanImageToVideo top-aligned with CLIP Text Encode; the main flow continues right on that row
Before (i2i): Load Image → Resize → VAE Encode moved 300px below VAE Encode's sampler
After:  Load Image → Resize → VAE Encode level, as part of the main flow
```

**Nodes with many inputs (WanAnimateToVideo, WanSoundImageToVideo, WanSCAILToVideo)**
```
After: its sources in one column on its left, top to bottom in input order, right edges aligned (`inputs`)
Before: the model row (… → Skip Layer Guidance → EasyCache) ending at the right edge of the text encoders, one column left of WanFunControlToVideo, the sampler's source column
After:  the model row ending at WanFunControlToVideo's right edge; when the gap left of that column is widened, the model row moves with it (Wan 2.1 Fun Control)
Before: the chain that cuts the face out of the DWPose output above DWPose, to match the slot order
After:  below DWPose (match the flow of processing)
Before: WanSoundImageToVideo's 9 input slots in a row left 700px between it and the prompt column
After:  Load Image and Load Audio pulled close to the node that receives them, even at the cost of some wire overlap
```

**The row of an image chain**
```
Layout: an image chain from Load Image that also goes to Get Image Size → Empty Latent goes on the bottom row, in one line with them;
        wires go up from that row to other targets (ControlNet, background removal)
Before: the Load Image for a depth map left of Load Depth Anything 3 (one more column)
After:  below Load Depth Anything 3
```

**Preparation**
```
Before: a node with 9 reference image slots and 9 Switch nodes piled in the column of Load CLIP and Load VAE; the core's form broke
After:  the Switch nodes built a little away; only the result comes into the core
Layout: a background composite before a depth ControlNet: Load Image, background removal and layer stacking left of Load Checkpoint
```

**Layers, same-shape chains**
- Nodes that stack layers (Add Layer → Create Layered Image) go from the bottom up, background at the bottom. Only these.
- Two chains of the same shape (Wan 2.2 high and low noise; two AnimateDiff keyframe chains): the one for the later node on top, so their wires do not cross.
- Several large loading nodes (Load Image, Load Video) into one node: a staircase, the first at the upper left at its slot's height, the next lower right.

**Spacing**
```
Before: 150px between Load LoRA and KSampler
After:  no wider space to a wired neighbour without a reason
```

### 5. Loaders

```
Layout: basic t2i: Load VAE above the KSampler (it is first used by VAE Decode)
Layout: Load VAE next to the VAE Encode of the bottom row when it is first used there (Anima pose, Krea2 head swap, SeedVR2)
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
```
- VAE Decode and VAE Decode Audio (MiniMax H3, LTX) stand in the same column.

### 6. Value nodes

- The cfg 1.0 of a distilled model is not changed, so it stays in each KSampler; no cfg value node.
- Sizes typed by hand once are not handed out; a size the author measures from an image comes from Get Image Size.

### 7. Groups and colour

- A two-stage LTX workflow has three groups (stage 1, stage 2, decode). A t2i with IPAdapter has none.
- A Detail pass whose every node was coloured green inside its group: the group already guides the eye.
- Colour split finely (SCAIL 2): the core green; taking the person in the input video pale_blue; taking the person in the reference image cyan; CLIP Vision brown.
- In that two-stage LTX workflow, the decode of the Stage 1 result and the decode after upscaling are different outputs: they were split out of one "Decode" group (a case, not a rule).

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
One: base → refiner → Hires.fix (conditioning passes on). The film grain and colour correction on the finished image: a workflow of its own
Split: nine models with their own sampler settings × t2i and i2i = eighteen workflows
One, bypassed: a depth image as an optional guide for an edit (not a second workflow)
```

### Fix

```
Before: two KSampler (Advanced) in a row, both adding noise from step 0; the second redraws the first's result entirely; kept with a Caution
After:  the first removed, reported
Before: 30 steps split into three KSampler (Advanced) (0–10, 10–20, 20–end) with a different seed each
After:  one KSampler with 30 steps; the difference reported
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

- Resolution samples the author prepared (26 Empty Latent Image connected to nothing): removed, the values kept as a table in the Note on Empty Latent Image. Undecided: that table, or the core Resolution Selector wired in. Either is fine.
- A finished stage not connected to the output, with the author's Note saying how to connect it: left unconnected, and how to connect it written in a Note.
- A bypassed branch whose sources are all empty: it cannot work, so it is removed as debris and reported.
- A switch between Tiled VAE Decode and VAE Decode: keep the one the author had enabled.

### Choosing a replacement

```
Before: Compositor3 (stacks images by dragging) rebuilt from Image Composite Masked and scaling nodes
After:  core Create Layered Image and Add Layer (positions fixed by dragging in the editor)
After:  tiles: Split Image into List of Tiles → redraw each → Color Transfer → Merge List of Tiles to Image (in place of Ultimate SD Upscale)
        With Qwen Image 2.1, whose VAE outputs RGBA, Split Image with Alpha before Color Transfer
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

## Undecided

- **Workflows that are too complex**: nested subgraphs expanding to hundreds of nodes (chains of regular expressions that build text, and so on). Leaving them as a subgraph may be easier to read.
- **What to hand over when splitting**: if what the author's wireless nodes sent is turned into Save Image → Load Image, the later workflow may apply the same processing again.
- **A node that gathers inputs**: at the middle of its sources, or its top edge aligned with its neighbour (Detailer's Simple Detector and SEGS Filter side by side were corrected to align their tops).
- **How high a loader may stand above the sampler** (400px above KSampler was too high).
- **A backward wire into a lower row**: an upscale group on the row below the main flow takes VAE Decode's image going back down to the left; where to draw the line.
- **Simplifying an author's size calculation**: the author measured an upscale ratio with an empty 64×64 latent (6 nodes, works for any upscale model); Resolution Selector → Math "a / 2" does it in 3 nodes for a single x2 model, no longer equivalent.
