# The Readable Node form

What you decide when arranging a workflow, and what a finished workflow is checked against. The canvas does the rest (node sizes and widths, the fixed colours, rail heights and the room for rails, Reroute positions); its moves and checks are at the top of canvas.py.

How to read a rule: the bold line says what to do. **Why** names the principle or goal of SKILL.md it serves; when a case is not covered, decide by it. **Bad** is the form that breaks the rule, as seen in a finished workflow. **Fine** is a form that looks like Bad but is not; a rule without Fine has no exception. **Undecided** is not decided: do not fill it with your own rule. Cases are in examples.md, "Layout", under the same section headings.

## 1. The usual form

**Build the core in the usual form, so every workflow of the same kind reads the same.** Why: the whole picture at a glance.
- Text to image with KSampler: the model chain (loader → LoRA → model patches) on a row above the encoders; its wire into the KSampler may slant (the conditioning is the one made horizontal, not the model). The text encoders in the column left of the KSampler, positive above, negative below (Conditioning Zero Out stands where the negative would be). The positive conditioning enters the KSampler horizontally. Empty Latent in the same column as the encoders. Load VAE above the KSampler when only VAE Decode uses it. VAE Decode right of the KSampler, level with it; Save Image right of VAE Decode.
- With SamplerCustomAdvanced: its sources in one column on its left in input order (noise, guider, sampler, sigmas, latent), the guider level with the sampler (its wire horizontal); the guider's conditioning enters horizontally; the sigma nodes (scheduler → split) in that column, not on the model row. Load VAE above the sampler.
- The outputs: Save Image next to the node that makes the result. Compare and Preview need not be next to Save Image: they go where their wires need the fewest Reroutes (below Save Image is fine), but never between the node that makes the result and Save Image. When the main flow's wire passes an output node on its way to a later node, one of them steps down so the wire passes above it (a staircase: `put <node> right <ref> step` places it just below the wire). Which one steps down is chosen so fewer Reroutes are needed.
- The sampler stays where the eye line puts it; what enters it (its column of sources and the chains before them) moves up or down to it, never the sampler to them.
- A stage that takes the previous stage's result (an image, a latent): its sampler stands on the eye line first (section 4); its conditioning enters horizontally from the column just left of it (Apply ControlNet, as the text encoder does in text to image), and the stage's own chain (upscale, resize, VAE Encode) stands on the row below, its latent slanting up into the sampler. When the conditioning cannot enter horizontally (it comes on a rail), the chain moves to the sampler instead: its latent enters horizontally, or its top edge is on the sampler's (either is fine). The wire bringing the previous stage's result into that chain is the one that slants (or runs on a rail).

## 2. Nodes

**No node is hidden.** Why: do not hide nodes.
- Bad: two nodes overlap. A node or a Reroute stands right below a node that grows when run or when its values change (a sampler, a node that shows a video, Create Bounding Boxes), within its width. A node that shows an image does not grow: the image is drawn inside the room its size already has.
- Fine: the growing node shifted left until nothing below it overlaps it horizontally.

## 3. Wires

**A wire is horizontal when it can be.** Horizontal means the output slot and the input slot are at one height. This matters most. Why: the reader follows the processing along a single line.
- Bad: a slanted wire that becomes horizontal by moving the node at one end, without slanting another wire. At a node with two or more wires coming in, a reference wire (a size to match, a mask, a model) made horizontal while the node's chain wire (what it takes in, works on and passes on) slants. A node taking two wires it works on together (positive and negative, a video and an audio latent) set midway between their sources so that neither is horizontal: its chain wire is the horizontal one.

**No wire goes back from right to left.** Why: left to right.
- Bad: a wire entering a node whose left edge is left of the source's right edge.
- Fine: back by at most the target's width plus one column gap, into Conditioning Zero Out or from an empty latent into a scheduler.

**A wire is drawn directly. Reroutes are used only when, without them, one could not see where the wire goes (a value carried far or to several places: a rail). When a direct wire would be hidden behind a node, move its source or its target so it shows, before bending it with Reroutes.** Why: Reroutes cut one wire into pieces, and the reader must trace them to see where a value comes from.
- A rail is one value, or several side by side, carried with Reroutes. Write a `rail` line; it runs at the height the line writes (`above <unit>`, `below <unit>`, `level <X>.<output>`) or, with none written, at its source's output height, and gives every target after its first lowering Reroute the value from the rail. The canvas does not look for a height or move nodes to make room: place the source and the targets so the rail runs where it should. A loader heads its rail. Rails of model, vae and clip from one loader or from loaders stacked in one column run in that order from the top; a conditioning rail runs above the samplers and below the model and vae rails; other rails are ordered so fewer wires cross. A rail for a side use (an image carried only to be shown or stitched for reference) runs below, written `below <unit>`: a rail above stands out on its own.
- Bad: a wire bent with Reroutes while neither its source nor its target was moved. One of a pair (positive and negative) on a rail and the other not. The same loader placed again for each stage. A rail that goes up and down. Two rails closer than the rail gap (a conditioning rail written just under the vae rail): the loaders heading the upper rails go up together, so the gap opens. A rail lifted off its source's output height by a Reroute where a line at that height would pass behind nothing (two values of Get Image Size raised to a height written in the rail line): the source stands at the height the rail runs, or the rail runs at the output height.
- Fine: a rail inside or outside a group, off the group's title band. A rail of values (fps and so on) below the main flow.
- Undecided: when a wire may pass behind a node (a wire whose way in and way out are plain to see may).

## 4. Flow and position

**Left to right in processing order. A node's sources stand from the top in the order of its inputs.** Why: left to right; follow along a single line.
- Bad: two wires into one node cross because the sources stand in another order, and swapping them breaks no other rule. A chain folded back below or above itself.

**The main flow (sampler → VAE Decode → … → save) runs along one band (the eye line), from the first stage to the last. Every stage's sampler stands on it: their top edges at one height.** Why: follow along a single line; one look along the eye line finds every stage.
- Bad: stages whose samplers stand at different heights. A slanted wire inside a stage along the main flow or into the sampler's positive input, where it could be horizontal. From VAE Decode to the save node, top edges not shared, unless an output node stepped down for a wire passing on. A Preview or Save above the node that feeds it. A main-flow wire hidden behind a save or preview node.
- Fine: stages that do not take each other's result (parallel stages) each have their own band. What enters a sampler (conditioning, guider, latent) and what follows it (decode, save) stand around it as its form places them, so with SamplerCustomAdvanced the guider and VAE Decode are off the samplers' height. A wire from one stage to the next that slants, or runs on a rail, so the samplers stay on the eye line.

**Other chains have their own rows, by role, not lined up because they are connected.** Why: the whole picture at a glance. The model chain goes above the band. Helper chains (masks, detection) one row below the band, in the column left of the node that uses them. The image chain and the size nodes (Get Image Size, Empty Latent, width and height) on a row lower down; the image that goes into the sampler (the input image of an i2i, through Resize and VAE Encode) is part of the main flow, not of this row.
- Bad: such a chain inside the band, so that the main flow steps around it. A side node (a detector provider, a Preview of a stage's image) aligned to the bottom of the tall node beside it, far from the wire it hangs on.
- Fine: a side node just below the image wire that passes it, as far down as keeps it off that wire (`step`).
- Bad: the image wire into a VAE Encode that takes only the image (and the VAE) slants, also when the same image goes on to a text encoder as a reference: the image chain (Load Image, Resize) stands on VAE Encode's row, so that wire is level; the wire from VAE Encode on to the sampler may slant.
- Fine: a node that takes conditioning as well as the image (InpaintModelConditioning, an image-taking text encoder) stands where its conditioning enters level; the image wire into it slants.

**The sources wired straight into a sampler stand in one column, right edges aligned (`inputs`).** Why: follow along a single line.
- Bad: those sources spread over several columns, or not right-aligned. The model chain, on its row above, ending at another column's right edge than this one (its last node stands near the sampler it feeds).

**Preparation stays out of the core.** Preparation (switching reference images, compositing a background, assembling text, and so on) is built outside the core's columns, and only its result comes into the core. Why: the whole picture at a glance (the core keeps its usual form).
- Bad: a preparation node squeezed into the column of a loader, a text encoder or the sampler (between those nodes).
- Fine: preparation further left than the loaders. A preparation node next to the node it feeds that ends up above or below a column of the core.

**Wires show and nothing is packed; no empty space is made by hand.** Why: do not hide wires; the whole picture at a glance. Place by relations (put, row, stack, align, level, inputs, rail); the canvas keeps the gaps, also around group frames.
- Bad: a node squeezed into a gap so that wires run behind it. An empty band left between nodes.

## 5. Loaders

**A loader stands in the column left of the node that first uses it.** Why: left to right; the wire from a loader is short and does not go back.
- Bad: other columns between a loader and its first user, when it is not on a rail. A loader at the far left that feeds only a later stage. A loader of one node's model (Load Upscale Model) away from that node. Load VAE above the model loaders (it stands below the model chain; below the text encoders is fine too).
- Fine: Load CLIP in the column of the text encoders. A Load VAE first used on the input side (VAE Encode, WanImageToVideo and so on), when it is not on a rail, stands there, apart from the other loaders.

## 6. Value nodes

**A value is put in a value node only when it is changed for each generation and reaches several nodes.** Otherwise it stays in the widget of the node that uses it. Why: the workflow is easy to rearrange and reuse.
- Bad: a value node with a single target. A value node holding a value nobody changes. A PrimitiveNode (use Int, Float, String and so on). A value node standing between the positive and negative prompts. A text written in a text area where it was (a prompt, a negative prompt) handed out from String, a one-line input: it is handed out from Text (Multiline), the same kind of input.
- Fine: a value node titled "display name: what the value is" (`Float: fps`, `Int: pixel count for 720p`); the display name follows "Language" in SKILL.md.

## 7. Groups and colour

**A group holds one large function: a clearly separate stage, one of parallel stages of the same form, or a function switched with bypass. A workflow that does one simple thing has none. Decide by function, not by counting samplers or nodes.** Why: the whole picture at a glance (a group guides the eye). The title is in the user's language, as a Note's title is: a common name stays as it is (Hires.fix, Upscale); otherwise a short noun phrase for what the group does (Mask for IPAdapter), not a sentence explaining it. A group holds its function's loaders; shared loaders go into the group of the first stage that uses them; values shared by parallel stages go into no group.
- Bad: stages that are clearly separate with no group. A group for each small piece of a stage (each ControlNet switched with bypass inside the first stage): the stage's group holds them, and the frames of small groups leave the layout full of gaps. A group removed because a wire crossed its title band (move the wire or the group instead). A function switched with bypass whose nodes are not all in its group. Groups of stages operated in order not sharing their top and bottom edges (`group-align`). A wire over a group's title band.

**Colour shows which function a node belongs to, on the few nodes that do one job.** Why: colour appropriately. Loaders, LoRAs and Notes have fixed colours (the canvas applies them; a Load CLIP whose CLIP reaches no text encoder, one that feeds only an LLM, has none). Five colours are left: brown, green, blue, pale_blue, cyan. The basic t2i / t2v form stays uncoloured; green is the part that makes this workflow differ from the basic form; ControlNet kinds are pale_blue; each other added function gets one colour. A group already guides the eye; colour nodes inside a group only with a reason.
- Bad: a sixth colour. A node only for looking (a Preview) coloured. Every node of a group coloured the same. One node of a function coloured while the nodes that do that function with it stay uncoloured (Generate Text green, its Text (Multiline) and its Load CLIP not). A node that only makes the run faster (a cache, an attention backend) coloured: it belongs to the basic form.
- Undecided: what reason is enough to colour nodes inside a group.

## 8. Names

**Node names are not changed.** Names the workflow's author changed go back to ComfyUI's display names. Why: the workflow is easy to rearrange and reuse.
- Bad: a title the author gave (in any language) left on a node.
- Fine: a value node's title (section 6). A node loading an image or video titled "display name: what it takes" (`Load Image: image to edit`, `Load Image: reference image 1`), in the same form: which image goes where is read without opening a Note.
