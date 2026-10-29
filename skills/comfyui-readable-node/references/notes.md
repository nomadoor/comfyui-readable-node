# How to write Notes and the Walkthrough

Rules read as in readable-form.md (Why, Bad, Fine, Undecided).

**A Note says what the graph cannot show. What the graph shows is not written.** As with comments in code: write why something is there, the pitfalls a reader would fall into, and what could be done better; do not restate what can be read. Why: the reader follows the workflow without being made to read twice.
- Write: the author's intent that cannot be seen (why this value, why this node); pitfalls and advice (a value that makes the image smaller, latent upscaling degrading the image, a setting that wastes a distilled model's speed); where using it is easy to get wrong (which Load Image takes what, when several take images).
- Do not write: node names and values read aloud; the nodes read in wire order; what everyone who uses ComfyUI knows (negative has no effect at cfg 1, Load Image takes the image to edit, a size rounded to the model's multiple); what using ComfyUI shows (a custom node must be installed to run; with a node taken out, its wires are connected directly); which way a value works when that is the usual way (smaller is faster, larger keeps more detail); nodes only for looking or only loading a model; a value the workflow is built not to use (the negative prompt at cfg 1: techniques.md, "With cfg 1.0, make the negative…", says what becomes of it).
- Bad: a sentence that only restates what the graph shows.

Differences from the original workflow (what was tidied, replaced or removed, and why) are reported in the conversation, not in Notes. A report is read once; a Note stays in the workflow.

There are two kinds of Notes: the overview and models Note (one in every workflow), and Notes on part of the processing (only when something above applies). Both are written in a Markdown file and placed with the canvas `note`.

## Who writes the text

The text of the Notes on part of the processing, and the one or two sentences at the top of the overview Note, are written by a separate agent (how to ask it: step 7 of SKILL.md), not by the agent that built the workflow: having built it, you read what you meant rather than what is there. You place the Notes.

## The overview and models Note

**At the very top, what this workflow does, in one or two sentences: what goes in and what comes out. Below it, the list of models.**
- The first heading says that in the user's language. The models heading is always `## models`, in every language (the canvas finds the model Note by it).
- The list of models is in exactly this form (the canvas `models` gives a draft):

````markdown
## What this workflow does

Generates an image from a text prompt with Qwen Image 2.1.

## models

- diffusion_models
  - [qwen_image_2.1_int8_convrot.safetensors](https://huggingface.co/...) (7.26 GB)
- vae
  - [qwen_image_2.1_vae_bf16.safetensors](https://huggingface.co/...) (676 MB)

```text
📂ComfyUI/
└── 📂models/
    ├── 📂diffusion_models/
    │   └── qwen_image_2.1_int8_convrot.safetensors
    └── 📂vae/
        └── qwen_image_2.1_vae_bf16.safetensors
```
````

- The download URL and size come from the original workflow (the node's information, or the author's Note). If it has none, search HuggingFace for the same file name and write only a URL where the file was confirmed to exist. Do not guess; if it is not found, do not write it.
- When the same file is in a Comfy-Org repository on HuggingFace (files repackaged for ComfyUI), link that one rather than another copy. Confirm it there as above.
- Models that a node downloads by itself the first time it runs are written below the list: what, where it goes, and what it needs (found in the custom node's source).

## A Note on part of the processing

**The title is one of three: "Markdown Note: Usage", "Markdown Note: Author's techniques", "Markdown Note: Caution"** (the part after the colon in the user's language; two in one Note are lined up with " / ").
- **Usage**: where using it is easy to get wrong; the purpose of an author's technique that cannot be seen (in one phrase).
- **Author's techniques**: what the author left in words (Notes, descriptions, titles), in the author's own words, only where the user needs it to choose a value or to avoid a trap; not everything the author wrote. A claim that cannot be checked (how good the results look) is quoted as the author's words; what can be checked (swapping in a GGUF loader) is written plainly, without "according to the author".
- **Caution**: puzzling processing that is kept, a trade-off the author may have chosen, and advice on what could be done better. When memory may run short, suggest a smaller form of the same model (fp8_scaled, int8) with its link, from Comfy-Org when it has one, rather than loading the model in a lower weight_dtype. The workflow keeps the model the author chose: another file changes the result and the download.
- Bad: a Note under none of the three. "According to the author" on something that can be checked, or in a Usage Note.

**Check every statement before writing it** in the node's source, the official description or the model card. Before writing that a node is missing, check whether ComfyUI applies a default internally (without ModelSampling, the model's default shift is still used). Rules of thumb (techniques.md) are written as knowledge from experience. Do not write where you checked (file names, function names). What you could not find out is written as "could not find out".

**The form inside a Note**
- On the top line, 🔗 and the name of the node being explained.
- One Note per place the user looks at (one node, or a cluster looked at together). Several topics there become several headings in that one Note. One thing is said once in the whole workflow: the same point (larger is slower) is not written again in the Note of another node.
- Each topic has a `###` heading that says in one plain phrase what the topic wants to say (a warning calls for attention). Under it, one or two phrases. Indent at most one level. A polite register.
- Point at nodes by their names; to have a value changed, write the node name and the widget name ("set sage_attention on Patch Sage Attention KJ to disabled").
- Text to be copied exactly is in quotation marks, not inline code (`), which breaks in the legacy renderer and on coloured Notes.
- Bad: pointing at nodes by their colour (a bypassed node loses its colour).

## Where to place

**The overview and models Note stands at the upper left of the whole workflow, its top edge on the top edge of the whole workflow.** In the plan: `note <file> left all`, then `align top all <Note id>` (`all` is the whole workflow with its group frames; other Notes do not count).
- Bad: the Note set left of everything while the empty space at the upper left of the workflow (above the first nodes, left of a group) holds it: the workflow grows wider for nothing.
- Fine: the Note in that empty space, written next to the node below it (`note <file> above <node>`), then `align top all <Note id>`. Left of everything only when no such space holds it.

**A Note on part of the processing stands next to the node it explains, placed last, in free space.** Why: the Note is read where it is needed, and it does not move the workflow.
- On the canvas, `note` lines run after every other line, rails included, so a Note goes into the space left; a Note on a node inside a group runs where its line stands (write it right after the lines that place that node; it moves with that node's block). The Note goes where its line writes it: when that place is not clear (on a node, too close to one, on a wire's path, below a node that grows), the canvas says what it lands on; write another side of the same node.
- Bad: a Note in another column or row than the node it explains, with other nodes between them. Nodes moved or rows widened to make room for a Note. A Note on a wire's path. A Note narrower or wider than the default width. A Note touching a node (closer than half a column gap), as a Note left-aligned below a narrower node reaches the next column.
- Fine: a Note wider than the node it explains, aligned with either edge of it (right-aligned when left-aligned would reach the next column).
- Fine: when there is no room next to the node, right above or right below it, with no other node between them (the 🔗 line names the node). Not in a gap between nodes, and not below a node that grows when run (a sampler, a node showing a video).
- Fine: a Note on a node inside a group stands inside that group's frame, next to the node. It is placed with the group, not last, so the frame takes it in and what comes after keeps clear of it.
- Bad: a Note that makes its group's frame larger while there is room inside the frame next to a node of the group (below a short node, beside a column). Fine: the frame grows only when there is no such room.

## Walkthrough

**The Walkthrough, like Notes, says what the graph does not show.**
- The groupings are those in B of the understanding document, in processing order.
- For each: one sentence on what the grouping does, then short bullets: what a node or model is, why a step is there, what a value means, what the user changes here.
- Do not write what can be read off the graph (which node passes what to which), or what the Notes say. The understanding document is notes for building; rewrite it as sentences to be read.
- Before: "`TrimVideoLatent` cuts the latent, then passes it to `VAE Decode`." After: "`WanVaceToVideo` adds the reference image to the head of the latent as frames. Those frames are not needed in the result, so `TrimVideoLatent` drops them."
