# Words

The meaning of the words used in the skill's documents. Each is defined here once.

## Workflows and people

- **the original / the original workflow**: the workflow given to be rebuilt.
- **the workflow's author**: the person who made the original workflow.
- **nomadoor**: the author of this skill. The layouts in the examples are ones nomadoor rebuilt by hand.
- **the user**: the person who uses the rebuilt workflow. This is also the person running this skill.
- **task**: one thing the user wants to do (Text to Image, Image to Video, and so on). 1 task = 1 workflow.

## Kinds of nodes

- **sampler**: KSampler, KSampler (Advanced), SamplerCustom, SamplerCustomAdvanced, and custom nodes that add processing these core nodes cannot realise.
- **loader**: a node that reads a model file (Load Checkpoint, Load Diffusion Model, Load CLIP, Load VAE, Load LoRA, and so on).
- **value node**: a node that only outputs one value (Int, Float, String, and so on).
- **core node**: a node that comes with ComfyUI from the start. A **custom node** is a node installed afterwards.
- **deprecated node**: a core node that has been superseded by a newer one ((DEPRECATED) is in its name).
- **source**: an upstream node that connects into an input of a node.
- **chain**: nodes connected in a line by wires.

## Building

- **core**: the central line of a task: model and clip loaders → text encode → sampler → VAE Decode → save.
- **added function**: processing added to the core (ControlNet, IP-Adapter, Hires.fix, Upscale, and so on).
- **preparation**: processing that prepares inputs for the core, before they enter it (switching reference images, compositing a background, assembling text, and so on).
- **stage**: each step of a multi-stage workflow (the first-stage generation, the second-stage redraw, and so on). A later stage uses the result of an earlier stage.
- **grouping**: a cluster of nodes that does one job or role. On the canvas it is made a `block`.

## Layout

- **row**: a horizontal band of nodes lined up side by side. Rows are separated top to bottom by role, like the model row, the conditioning row, the image row.
- **column**: a vertical band of nodes stacked up and down. The column of sources to the left of a sampler, and so on.
- **eye line**: a band with width through which the main flow passes.
- **main flow**: the flow from the sampler towards the final output (sampler → decode → … → save).
- **rail**: a band of wires drawn straight with Reroutes that carries values in a set to far places (`rail`).
- **Reroute**: a small node that relays a wire. Used to make rails.
- **backward wire**: a wire that goes back from right to left.
- **wireless links**: mechanisms that pass values without drawing wires (Set/Get, Anything Everywhere, hidden links).
- **Nodes 2.0 and the legacy renderer**: the two ways ComfyUI's frontend draws nodes.

## Work

- **canvas**: scripts/canvas.py. Both building and arranging are done on it, one move at a time.
- **understanding document**: the understanding of the workflow, written before building (`$W/understanding.md`).
- **check list**: the list of layout and content problems returned by the canvas's `check`.
- **report**: what is told to the user in the conversation when the rebuild is finished. Separate from Notes.
- **Undecided**: something not yet decided.
- **hand-made layout**: a layout a person arranged by hand.
