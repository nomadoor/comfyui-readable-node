# The Readable Node form (layout, size, colour, node names)

What is written here is what form to aim for.
- The layout is built with the moves of the canvas (scripts/canvas.py). The steps of building are in SKILL.md; the list of moves is at the top of canvas.py.
- For situations where you are unsure which way to go, see the examples in examples.md.

## Layout

### The heart of it

**Do not hide nodes.** Do not overlap nodes.

**Make wires horizontal.** Make every wire horizontal if it can be made horizontal. A wire that cannot may stay diagonal.
- Making a wire horizontal means aligning the height of the output slot and the input slot. What is aligned is the wire, not the node.
- Do not leave diagonal a wire that can be made horizontal. If you leave one, attach "what was tried, and why it does not become horizontal".

**The flow can be followed along a single line.**

**Keep "the usual form" in which inputs enter the sampler.** Because that form is always the same, the whole workflow can be read. The form is in the section "Around the sampler".

### Eye line (how heights are decided)

**The eye line is a band with width through which the main flow passes.** It is not the height of a single wire. Place it with the sampler as the reference.
- The main flow is sampler → decode → … → save. Running what is being made straight through applies to the flow after the sampler (decode → save).
- Each stage (group) may have its own band. If shifting them makes the whole cleaner, shift them per stage.
- Pre-processing (image pre-processing and so on) and loaders are often outside the band.

**Make the positive conditioning enter the node that receives it (KSampler, CFGGuider and so on) horizontally.**
- Making it horizontal is `put … wire`, `level`.
- Nodes that make conditioning (CLIP Text Encode, Apply … Conditioning, WanImageToVideo and so on) are placed on the same row as the sampler.
- The negative side goes below it.
- When the latent of the input image and the conditioning collide, take the conditioning horizontal and lower the chain of the input image to the row one below.

**The heights of other chains**
- The chain that loads the model (UNETLoader → LoRA → ModelSampling …) is basically above the eye line. As more nodes sit in between, it goes higher.
- Helper chains (making masks, detection loaders and so on) go on the row one below the eye line, lined up in processing order just before where they are used. They do not get in the way of the eye line.
- The chain of the image and the size nodes (Get Image Size, Empty Latent, width and height values) go in one horizontal row on a lower row. This is because the image wire should run horizontal up to Get Image Size → Empty Latent.
  - When the image only goes into a node in front as a reference image, which row that chain goes on is Undecided.
- Do not put too many nodes above the eye line.
  - Neither Preview Image nor Save Image goes above its source. Place them below the eye line or at the same height.
  - Jumping upward to avoid wires makes rails stretch upward.

### Order (left to right)

**Left to right, in processing order.**
- For every node, line up its sources from the top in the order they plug in. In this order, wires do not cross.
  - Sometimes this cannot be kept. Depending on how the surrounding nodes are placed or how the node's inputs are ordered, an upper node goes into a lower input. It is not an absolute rule.
- Do not fold output nodes back under their sources.
- When two or more chains of the same shape are lined up, put on top the chain that connects to the later sampler (or the later node). This way the wires do not cross.
  - Example: when there are two stages of KSampler Advanced, like Wan 2.2's high noise and low noise, put on top the model loading that connects to the second sampler.
  - Example: when there are two AnimateDiff keyframe chains (LatentKeyframeTiming → TimestepKeyframe → ACN ControlNet Loader), put on top the one that connects to the later Apply ControlNet.
- Only nodes that stack layers are lined up from bottom to top (background at the bottom). With core's Add Layer → Create Layered Image, or custom nodes that handle layers, make the stacking order the same up and down as layers in image editing software.

**Conditioning Zero Out goes where the negative prompt would be.** It is a node that does the job in place of a negative prompt, so place it below the positive CLIP Text Encode (`below`). Do not open a column for it between positive and the sampler. If you do, it looks as if the negative is to the lower right of positive.
- There are other situations where you do not want to open a column on the central row for a node with a thin role. Which ones those are is Undecided.

**Place a loader near and to the left of the node that first uses it, and connect it directly.** However, a loader (model, vae, clip) that is handed out to several stages on a rail goes on top, at the head of the rail (the section "Rails"). Even when the node that uses it first is in a lower row, bring the wire down to it from the rail.
- Example: Load VAE goes to the left of the node that first uses it (VAE Encode, InpaintModelConditioning, WanImageToVideo and so on). If it is used only for VAE Decode, above the KSampler.

**Move the whole thing forward (right), and do not make backward wires (wires going back from right to left).**
- The only one allowed is a backward wire of one node's width into a node with little content (but needed for clarity) (Conditioning Zero Out and so on). Do not connect to nodes that went back further than that.
- The other exception is when placing a group on the row one below is better than placing the whole group on the same row (the wire entering that group). Where to draw the line for this exception is not yet clear (examples.md).

### Staircase (when large nodes that change size are lined up)

**Make a staircase only when several loading nodes that are large themselves and change size a lot (Load Image, Load Video and so on) go into the same single node.** Do not use it for the sources of SamplerCustomAdvanced.
- Do not stack them vertically; shift them to the right while also shifting the height. Stacking vertically takes room and hides what is below when they grow. Lining them up side by side hides the wires passing between them. A staircase is compact and does not hide wires.
- Example: three Load Image → Batch Images. Put the first at the upper left, at the same height as the slot that receives it, and shift the next ones towards the lower right. Each wire enters its slot without passing over other nodes.
- Several nodes of the same kind connecting from an output hardly ever happens. If it does, the direction is the opposite of inputs (the farthest at the upper right, nearer ones further to the lower left).

### Around the sampler (how to place the sources)

- The sources that connect directly to a sampler (LoRA, CLIP Text Encode, Empty Latent, value nodes and so on) go in the same column even if their kinds differ, aligned at the right edge (`inputs`).
- The chains in front of them are not all aligned just because they are connected; separate them by role. The wire that loads the model and the nodes that make sigmas (BasicScheduler → SplitSigmas) are different roles. The sigma nodes go in the sampler's input column.
- SamplerCustomAdvanced goes at the vertical middle of its sources (`stack`, `align middle`). To its left, one column from the top in input order (noise, guider, sampler, sigmas, latent). The conditioning enters CFGGuider horizontally. The wires from noise, guider, sampler and sigmas into SamplerCustomAdvanced may be diagonal (because it sits in the middle; the canvas checks do not report these four).

### Core and preparation

**Do not break the form of the core.**
- Large groups of preparation (switching reference images, compositing a background and so on) are not mixed into the core's columns. Build them together outside the core and bring only the result into the core (`move`).
- The groups may go further left than the model and clip loaders (in 12 of 27 hand-made layouts, there are nodes left of the loaders).
- Whether to use Reroutes for the wire that brings the result follows the rules of "Rails".
- How to tell whether the form breaks is not decided.
- If similar stages are lined up, make the form of one stage and copy it with `shape`.

### Rails

**A rail carries values in a set to far places.** It is useful because it reads as one straight band. A rail that bends up and down cannot be read as a rail.

**When to lay one**: when carrying several values together to a later stage, or when handing the same value out to several places (`rail`).
- Values that come as a pair (positive and negative and so on) go on rails as a pair. Do not put only one of them on a rail.
- Do not place the same loader per stage. Hand one out with a rail.
- Rails from loaders (model, vae, clip) run above the nodes they hand out to. Rails of values (fps and so on) may run below.
- Rails go, from the top, model, vae, clip, conditioning, then others. Make it the same order as the loaders lined up from the top as model, vae, clip. If the order differs, wires cross and Reroutes increase.
- When handing model, vae and clip out to later stages, do not raise them with Reroutes; put the loader (and the model chain that continues from it, such as LoRAs) at the height of the rail, as the head of the rail.
  - One Reroute fewer.
  - When a wire goes up once and then sideways, the eye moves up and down.
- Rails and wires may pass inside a group or outside it. It is fine as long as they do not overlap the group's title band. Forcing them outside the group wastes space.

**When not to lay one**: do not lay a rail for a single wire.
- If a single wire passing behind nodes bothers you, fix it by how nodes are placed (changing the row, placing the loader near where it is used) before a rail.
- Wires that are not written as rails are connected directly from the source to where they plug in. Do not place meaningless Reroutes.

### Nodes that change size

**Nodes that show images (saving, preview, loading) are placed by the canvas at their initial size plus the image area, and overlaps are counted at that size.** (The image areas are in "Size and width".)
- Samplers (KSampler, SamplerCustomAdvanced and so on) grow when run, with a progress preview inside. The canvas does not add this, so keep the space for that growth yourself.
- Do not stack other nodes directly below such nodes. When they grow, they hide the nodes below. When lining them up, follow the section "Staircase".

### Groups

**Groups are used more to guide the eye than to separate functions.**
- Examples of where to put them:
  - Each stage of a multi-stage workflow where the stages are clearly separate.
  - Parallel stages of the same form (generation per model, from load model to VAE Decode).
  - Functions switched together with bypass (upscaling, interpolation and so on).
- The guide is functions. Put them in workflows where several large functions are connected. Do not decide by the number of samplers, nodes or stages.
- Other than this, when to gather things into a group is Undecided.

**How to put them**
- The title says what that stage or function does, by the common name (Hires.fix, Upscale, Face Detailer and so on).
- A grouping of a function also includes that function's loaders. When bypass or mute is applied to a whole group, only the nodes outside the group are left behind.
- Loaders and text rows shared by stages that follow one another (generation in the first stage → redrawing in the second, and so on) go into the group of the stage that uses them first.
- Values shared by parallel stages of the same form (generation per model, and so on) — seed, steps, Empty Latent, prompts — go into no group.
- For groups made to operate stages in order, align all their top and bottom edges. Enclose with room to spare.
- Do not remove a group because a wire overlaps its title band. Move the wire or the group.

## Size and width (the canvas calculates)

- The size is the initial value when the node is created in ComfyUI. The sizes in the original workflow are not used. Only nodes that show images get the image area added to the initial size (the canvas does this).
- Minimum: the width is 225px and the width where the whole node name is visible. The height of a text field is 100px.
- Format Text and Math Expression get the smallest size that fits their content. Whether to apply this to other nodes is Undecided.
- The image area (width × height) of nodes that show images, which the canvas adds to the initial size: saving nodes 500×520, previews 340×320, loading nodes 300×320.
- If the difference in width between nodes stacked in the same column is smaller than the gap between columns (60px), align them to the widest (`width`).
- Spacing: between rows, 45px (from the bottom edge of the upper node to the top edge of the lower node's title band). Between columns, 60px (from the right edge of the left column to the left edge of the right column).

## Colour

Colours are chosen from core's 9 colours (red, brown, green, blue, pale_blue, cyan, purple, yellow, black) (`color`). black is not used.

**Fixed colours** (the canvas applies them)
- Model loaders and LoRAs: purple
- CLIP loaders: yellow
- VAE loaders: red
- The model Note: purple
- Other Notes: yellow (if no colour is set, a ComfyUI bug makes them yellow)

**The remaining colours that can be used**: the 5 colours brown, green, blue, pale_blue, cyan.

**When to use them**: colour shows "which function it belongs to".
- The basic t2i / t2v form (sampler, decode, save, text encoder) is uncoloured.
- green: the part that is the core of that workflow when compared with the basic form (the image input of i2i, the ControlNet of a workflow where ControlNet is the lead, and so on).
- One colour for each other added function. ControlNet types are pale_blue. Others are chosen from brown, blue, cyan.
- Apply the colour to every node belonging to that function (that function's loader, preprocessor, down to the Load Image for it).
- Usually 1 to 2 colours are added on top of the 3 loader colours. 4 or more is rare. If 5 colours are not enough, the workflow is too large.
- Coloured nodes, loaders excluded, are up to about a third of the whole. Do not go over half.

## Node names

**Do not change node names.** ComfyUI searches by node name, so if a name has been changed, you cannot tell what node it originally was. If the workflow's author changed them, return them to the original node names.

As an exception, only the following value nodes get information added to the node name. The form is "display name: what the value is" (for example `Float: video length (seconds)`, `Float: fps`, `Int: pixel count for 720p`). The display name is the name shown on the ComfyUI screen (display_name in object_info: Int, Float and so on), not the type name (PrimitiveInt and so on). Write the part after the colon in the user's language.
- Value nodes (Float, Int, String and so on) that reach several nodes from one.
- Value nodes whose value alone does not tell what the value is (pixel counts lined up in a list and so on).
