# Words

The meaning of the words used in the skill's documents. Each is defined here once.

## Workflows and people

- **the original / the original workflow**: the workflow given to be rebuilt.
- **the workflow's author**: the person who made the original workflow.
- **nomadoor**: the author of this skill.
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
- **chain wire / reference wire**: of the wires into a node, the chain wire carries what the node takes in, works on and passes on (the image into a resize, the conditioning into a sampler); a reference wire carries what it only looks at (a size to match, a mask, a model).

## Building

- **core**: the central line of a task: model and clip loaders → text encode → sampler → VAE Decode → save.
- **added function**: processing added to the core (ControlNet, IP-Adapter, Hires.fix, Upscale, and so on).
- **preparation**: processing that prepares inputs for the core, before they enter it (switching reference images, compositing a background, assembling text, and so on).
- **stage**: each step of a multi-stage workflow (the first-stage generation, the second-stage redraw, and so on). A later stage uses the result of an earlier stage.
- **the usual form**: the fixed arrangement of a core (readable-form.md, section 1).
- **grouping**: a cluster of nodes that does one job or role. It is written in B of the understanding document. On the canvas it is made a `block`, and the Walkthrough also explains it grouping by grouping.

## Layout

- **row**: a horizontal band of nodes lined up side by side. Rows are separated top to bottom by role, like the model row, the conditioning row, the image row.
- **column**: a vertical band of nodes stacked up and down. The column of sources to the left of a sampler, and so on.
- **eye line (band)**: the height every stage's sampler (KSampler, SamplerCustomAdvanced) stands at; a band with width through which the main flow passes.
- **main flow**: the flow from the sampler towards the final output (sampler → decode → … → save).
- **rail**: a value, or several side by side, carried far or to several places with Reroutes (`rail`).
- **Reroute**: a small node that relays a wire. Used for rails.
- **raising / lowering Reroute**: the Reroute that takes a rail from its source's output up or down to the height the rail runs at, and the one that takes it from the rail down or up into a target.
- **column gap / row gap**: the gap the canvas keeps between columns and between nodes stacked in a column (layout_params.json, H_GAP and V_GAP). A gap where wires cross several times is widened (GAP_WIDE).
- **rail gap**: the vertical distance the canvas keeps between two rails (layout_params.json, RAIL_GAP).
- **title band**: the strip at the top of a group frame where its title is written.
- **step (staircase)**: a node placed just below the wire that passes it (`put <node> right <ref> step`), so the wire runs on above it.
- **model chain**: the nodes the model passes through before the sampler: its loader, LoRAs, and nodes that patch the model (sampling settings, attention).
- **backward wire**: a wire that goes back from right to left.
- **wireless links**: mechanisms that pass values without drawing wires (Set/Get, Anything Everywhere, hidden links).
- **Nodes 2.0 and the legacy renderer**: the two ways ComfyUI's frontend draws nodes.

## Work

- **canvas**: scripts/canvas.py. Both building and arranging are done on it, with moves written as lines.
- **build.txt / the plan (layout.txt)**: the files of moves you write in `W`. build.txt holds the building moves (`canvas run`); the plan, layout.txt, holds the arranging moves (`canvas layout`), and is run whole each time.
- **block**: a name for a set of nodes placed together (`block <name> <id> …`); the lines after it place its nodes relative to each other, and the block then moves as one (`put <block> …`).
- **unit**: what a placing move takes: a node id, a block name, or a group's title.
- **understanding document**: the understanding of the workflow, written before building (`$W/understanding.md`).
- **check list**: the list of layout and content problems returned by the canvas's `check`.
- **report**: what tells the user the result when the rebuild is finished. Separate from Notes. There are two.
  - **report page**: `report.html`. It has three views: Original (the original workflow), Rebuilt (what was done on the canvas, one move at a time), Walkthrough.
  - **conversation report**: what is told in the conversation in step 11.
- **Walkthrough**: one of the views of the report page. It explains the finished workflow grouping by grouping, in processing order.
- **Undecided**: something not yet decided.
- **hand-made layout**: a layout a person arranged by hand.
