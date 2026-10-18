# The Readable Node form (layout, size, colour, node names, Notes)

The layout is built with the moves of the canvas (scripts/canvas.py). The list of moves is at the top of canvas.py; the steps of building are in SKILL.md.
What is written here is what form to aim for. For situations where you are unsure which way to go, see the examples in examples.md.
Where it says "undecided", it has not been decided yet. Do not fill it by making rules from your own judgement.

## Core of the layout

**What the eye follows is the flow of what is being made (image, video, latent). Run it straight through. The wires of tools (VAE, noise, sampler, sigmas, guider, CLIP) may be diagonal.** (`canvas check` calls the first kind *product wires* and the second *tool wires*.) (Undecided: the definition of the main line differs between this paragraph, the next paragraph, "Eye line" below, and step 5 of SKILL.md.)

However, the height of the eye line is decided with the sampler as the reference ("Eye line" below). Running what is being made straight through applies to the flow after the sampler (decode → save). Among the wires into the sampler, when the latent of the input image and the conditioning collide, take the conditioning horizontal and lower the chain of the input image to the row one step below. (Undecided: see the note on the main line above.)

- In 407 hand-made layouts, the share of wires that were horizontal: VIDEO 97%, IMAGE 57%, MODEL 38%, LATENT 32%, CONDITIONING 26%, CLIP 9%, SIGMAS 2%, VAE, NOISE, GUIDER 0%.
- What is aligned is the wire, not the node. Making a wire horizontal means aligning the height of the output slot and the input slot.
- Align the edges of a column. If nodes stacked above and below have similar widths, align them to the widest (`width`).
- Use the screen widely and show the wires. Do not cram. Keeping things compact matters, but before that the wires must be visible.
- There is no perfect. It is enough if it is easier to read than the original workflow and the flow can be followed along one line.

**Eye line**

- The wire heading to the final output (sampler → decode → … → save) runs at one height across the whole workflow. This is the eye line. The trunk is at this height.
- Think of the eye line with the sampler (KSampler and so on) as the reference. The main line is the path of the positive conditioning. Run it horizontal up to the sampler (`put … wire`, `level`). The negative side goes below it. Nodes that make conditioning (CLIP Text Encode, Apply … Conditioning, WanImageToVideo and so on) are placed on the same row as the sampler. (Undecided: see the note on the main line under "Core of the layout".)
- The chain that loads the model (UNETLoader → LoRA → ModelSampling …) is basically above the eye line. As more nodes sit in between, it goes higher.
- Helper chains (making masks, detection loaders and so on) are lowered one step below the eye line and lined up in processing order just before where they are used. They do not get in the way of the eye line.
- Do not put too many nodes above the eye line. Neither Preview Image nor Save Image goes above its source. Jumping upward to avoid wires makes rails stretch upward. Place them below the eye line or at the same height.

**Tendencies of placement** (from hand-made layouts)

- From left to right, in processing order. Do not fold output nodes back under their sources.
- A node with many inputs (SamplerCustomAdvanced and so on) goes at the vertical middle of its sources (`stack`, `align middle`). Its input wires (noise, guider, sampler, sigmas) are tool wires, so they are not made horizontal. That is why it can be placed at the middle.
- SamplerCustomAdvanced has a usual form: to its left, one column from the top in input order (noise, guider, sampler, sigmas, latent).
- Inputs are lined up from the top in the order they plug in.
- The sources that connect directly to a sampler (KSampler and so on) (LoRA, CLIP Text Encode, Empty Latent, value nodes and so on) go in the same column even if their kinds differ, aligned at the right edge (`inputs`). Do not split the sources into separate columns by kind. If similar stages are lined up, a sense of unity at the level of making the form of one stage and copying it is enough (`shape`).
- Do not break the form of the core (load model, load clip → text encode → KSampler → VAE Decode → Save) heavily for one large input. If a group of input nodes takes up position inside the core and breaks its form, shift that group a little to the left and bring it in with Reroutes (`move`, `rail`). It may go further left than the model and clip loaders (in 12 of 27 hand-made layouts, there are nodes left of the loaders). How to tell whether the form breaks is not decided (examples.md).
- Chains in front of the sources that connect directly to the sampler are not all aligned just because they are connected; separate them by role. The wire that loads the model and the nodes that make sigmas (BasicScheduler → SplitSigmas) are different roles. The sigma nodes go in the sampler's input column.
- The chain of the image and the size nodes (Get Image Size, Empty Latent, width and height values) go in one horizontal row on the lower level. This is because the image wire should run horizontal up to Get Image Size → Empty Latent. If the image only goes into a node in front as a reference image, it may not need to be lowered that far (undecided).
- An image and the node that receives it go side by side, one pair at a time; pairs are stacked vertically.
- A loader is placed near and to the left of the node that first uses it, and connected directly. Load VAE goes to the left of the node that first uses it (VAE Encode, InpaintModelConditioning, WanImageToVideo and so on). It may overlap a node slightly. If there is no node that uses the VAE in front, it goes above the KSampler.
- Two nodes that receive the same thing (VAE Decode and VAE Decode Audio) go in the same column, stacked vertically.
- The order of parallel chains (two model chains, two keyframe chains) is the one with fewer wire crossings.
- Do not open a gap the width of one column across the whole workflow for a node with little content (Conditioning Zero Out and so on). It may be tucked under its source (`below`).
- Wires that cross to another layer are shown with space opened, not packed.
- Only stacking of layers goes from bottom to top (background at the bottom). The same up and down as layers in image editing software.
- Reverse wires (wires going back from right to left) are not allowed as a rule. Move the whole thing forward (right). The only allowed case is a reverse of one node's width into a node with little content (but needed for clarity) (Conditioning Zero Out and so on). Do not connect to nodes that went back further than that. The exception is when placing a group one step lower is better than placing the whole group on the same layer (the wire entering that group). Where to draw the line for this exception is not yet clear (examples.md).

**Rails**

A rail is a road that carries values in a set to far places. Lay one (`rail`) when carrying several values together to a later stage, or when handing the same value out to several places. A road is useful because it reads as one straight band. A road that bends up and down is not a road.

- Rails go, from the top, model, vae, clip, conditioning, then others. When handing model, vae and clip out to later stages, do not raise them with Reroutes; put the loader (and the model chain that continues from it, such as LoRAs) at the head of the rail.
- Rails and wires may pass inside a group or outside it. It is fine as long as they do not overlap the group's title band. Forcing them outside the group wastes space.

- Do not lay a rail for a single wire. If a single wire passing behind nodes bothers you, fix it by how nodes are placed (changing the level, placing the loader near where it is used) before a rail.
- Wires that are not drawn as rails are connected directly from the source to where they plug in. Do not place meaningless Reroutes.
- Do not place the same loader per stage. Hand one out with a rail.

**Nodes that change shape**

- Nodes that show an image, a video or a progress preview inside when run or loaded (KSampler, SamplerCustomAdvanced, Save Image, Preview Image, Video Combine, Load Image, Load Video). The canvas counts overlaps at the size before they grow. Keep the space for the growth yourself.
- Two outputs (two Video Combines, Video Combine and Save Image) are not stacked vertically; line them up to the right as a staircase.

**Groups**

- Groups are used more to guide the eye than to separate functions. For groups made to operate stages in order, align all their top and bottom edges. Enclose with room to spare.
- Examples of where to put them: each stage of a multi-stage workflow where the stages are clearly separate. Parallel stages of the same form (generation per model, from load model to VAE Decode). Functions switched together with bypass (upscaling, interpolation and so on). The title says what that stage or function does, by the common name (Hires.fix, Upscale, Face Detailer and so on).
- A grouping of a function also includes that function's loaders (some people use tools that bypass per group, so if even one is outside, it gets confusing). Values shared by stages go into no group.
- Do not remove a group because a wire overlaps its title band. Move the wire or the group.
- The guide is functions, not the number of samplers. Put them in workflows where several large functions are connected. It is not "always put them if there are several". Do not overuse them. However, do not decide not to put them by the number of nodes or stages. As part of guiding the eye and making it readable, use them effectively, without overusing.
- Other than this, when to gather things into a group is undecided.

## Size and width (the tool calculates)

- The size is the initial value when the node is created in ComfyUI (scripts/nodesize.py; the same calculation as the frontend's computeSize). The sizes in the original workflow are not used.
- Nodes that take text (CLIP Text Encode and so on) basically have the initial size. But the text field is not made lower than 100px (so that the field does not become narrow on nodes with many parameters; the canvas stretches it).
- Format Text and Math Expression get the smallest size that fits their content (the width is not narrower than 225px). Whether to apply this to other nodes is undecided.
- Nodes that show images (Save Image, Preview Image, Load Image) are not made smaller than the hand-made sizes (Save Image 503×574, Load Image 300×424, Preview Image 338×344: the median of 433 workflows on Comfy-with-ComfyUI from 2026-07-01 on; the canvas stretches them).
- The width is the initial width. But it is not narrower than "the width where the whole node name is visible" and "225px" (the minimum width of Nodes 2.0).
- If the difference in width between nodes stacked in the same column is smaller than the gap between columns (62px), align them to the widest (`width`). Ones with a large difference, like CLIP Text Encode (400) and Empty Latent Image (270), are not aligned.
- Spacing: the gap between nodes stacked in the same column is 44px, the gap between columns is 62px (the median of hand-made layouts).

## Colour

- Colour shows "which function it belongs to" (`color`).
- The basic t2i / t2v form (sampler, decode, save, text encoder) is uncoloured.
- One colour per added function (ControlNet, IP-Adapter and so on). Apply it to every node belonging to that function (loader, preprocessor, down to the Load Image for it).
- What counts as an "added function" is not strict. The deciding factor is whether it gets noisy.
- Loaders (MODEL, CLIP, VAE) and LoRAs get the wire colour by default (purple, yellow, red). In a large workflow they become the first place the eye goes.
- Colours are chosen from core's colours. If they are not enough, the workflow is too large. More colours scatter the eye.

## Node names

- Do not change node names. ComfyUI searches by node name, so if a name has been changed, you cannot tell what node it originally was. If the author changed them, return all of them to the original node names.
- For value nodes (Float, Int, String and so on) that reach several nodes from one, and value nodes whose value alone does not tell what the value is (pixel counts lined up in a list and so on), make the title "original node name: what the value is" (for example `Float: video length (seconds)`, `Float: fps`, `Int: pixel count for 720p`). Write the part after the colon in the user's language. Other nodes are not given titles.

## Notes

How to place Notes is in notes.md ("When to write, where to place"); how to write them is also in notes.md.

## Form of the output

- The number and names of the files after splitting are undecided. One canvas becomes one workflow JSON.
