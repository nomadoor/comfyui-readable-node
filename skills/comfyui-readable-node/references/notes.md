# How to write Notes and the Walkthrough

There are two kinds of Notes placed in a workflow.
- The overview and models Note: one in every workflow.
- A Note on part of the processing: only when there is something to keep about part of the workflow's processing.

For both, write the text in a Markdown file and place it with the canvas `note`.

**In a Note, write only what is useful when looking at that workflow alone and cannot be learned by looking.** The people who read it are the people who use this workflow.
- Do not write what can be learned by looking at the graph. Sentences that restate node names and values, and sentences that read nodes aloud in wire order, are this.
- Do not write on nodes that are only for looking (previews and so on) or on nodes that only load a model either.
- How good the generated results are ("skin becomes realistic" and so on) cannot be checked, because you do not generate. Do not write it. If the workflow's author wrote it, quote it as the author's words in Author's techniques. Behaviour that can be checked in the node's source may be written.
- Say what is being done with the common name (Hires.fix and so on), not the author's own name.

The idea comes from chapter 5 of "The Art of Readable Code" (Dustin Boswell and Trevor Foucher): the purpose of a comment is to tell the reader what the writer intended, and a comment should not say what the code already shows.

Differences from the original workflow (what was tidied, the difference between two versions, what was replaced, old nodes and custom nodes kept without replacing and why) are reported in the conversation, not in Notes. A report is read once and done, but a Note stays in the workflow.

## The overview and models Note

**At the very top, what this workflow does. Below it, the list of models.**

- At the very top, give it the same heading in every workflow. The heading is "what this workflow does" (in English, `## What this workflow does`).
  - Below it, in one or two sentences, write the essence of this workflow: what goes in and what comes out.
- Below that, the list of models. The format is exactly the form of the following example (the canvas `models` gives a draft).
  - The heading `## models` is always written exactly like this, in every language. The canvas finds the model Note by it.

Example (when the user is English-speaking):

````markdown
## What this workflow does

Generates an image from a text prompt with Qwen Image 2.1.

## models

- diffusion_models
  - [qwen_image_2.1_int8_convrot.safetensors](https://huggingface.co/...) (7.26 GB)
- text_encoders
  - [qwen3vl_8b_int8_convrot.safetensors](https://huggingface.co/...) (9.35 GB)
- vae
  - [qwen_image_2.1_vae_bf16.safetensors](https://huggingface.co/...) (676 MB)

```text
📂ComfyUI/
└── 📂models/
    ├── 📂diffusion_models/
    │   └── qwen_image_2.1_int8_convrot.safetensors
    ├── 📂text_encoders/
    │   └── qwen3vl_8b_int8_convrot.safetensors
    └── 📂vae/
        └── qwen_image_2.1_vae_bf16.safetensors
```
````

- For the download URL and size, use what was in the original workflow (the node's information, or the author's Note).
  - If the original does not have it, search HuggingFace (Comfy-Org's repositories and so on) for the same file name, and write only a URL where you confirmed the file actually exists.
  - Do not make one up by guessing. If it is not found, do not write it.
- Models that a node downloads by itself the first time it runs are written below the list: what, where it goes, and what is needed for it.
  - They do not appear in widget values, so you find them when you read the custom node's source.

## A Note on part of the processing

### What to write (three titles)

**There are three titles. Write only what falls under one of them.** If nothing falls under them, do not place a Note on part of the processing.

The title is "Markdown Note: " followed by one of the following three (set with the canvas `title`). When one Note holds two, line them up like "Markdown Note: Author's techniques / Caution".

**Usage**: places where how to use it, or what it is for, cannot be seen just by looking.
- Places where the user is likely to stumble.
  - Judge the user's level from what you usually know about that person (the conversation so far, what they asked, what they said). While you cannot tell, do not write.
  - Do not write, from the start, every explanation for someone touching it for the first time (if they do not understand, the user can ask the agent).
- Author's techniques that were kept and whose purpose cannot be seen by looking. Write the purpose in one phrase.
  - Even without the author's words, write it if the purpose is known from the source. Do not write guesses.
- Examples: a structure that takes a number from a list by the index of a Custom Combo so the size can be chosen by name. A resize that shrinks the image before Generate Text. Pixel-count values lined up in a list.

**Author's techniques**: techniques the author left words about (the author's Notes, descriptions, titles).
- Convey briefly, in the author's own words, why that value or node is there.
- However, when the reason the author explains disagrees with the source or the model card, write the reason you checked.
- If no words remain, do not write. Do not write by guessing.

**Caution**: puzzling processing that is kept.
- What may have been the author's choice, or what is a trade-off between gain and loss. Even if the author had an intent, write it if it is strange.
- Ways of building that harm the result, and places that could be done better, that were kept without fixing. Write them in the conversation report too.
- What can only be a mistake is fixed, and what is plainly meaningless is removed. Neither is written in a Note; both are reported in the conversation.

### How to check what goes in a Note

Each "this is what happens" written in a Note is checked, one by one, before writing.
- Check it in the node's source, the official description, or the model's description (model card).
- Before writing a Caution that a node which should be there is missing, check whether ComfyUI applies a default internally. For example, without a ModelSampling node the model's default shift (sampling_settings in comfy/supported_models.py) is still used.
- Do not use the reason the author explains until you have checked it.
- Rules of thumb are written so that it is clear they are knowledge from experience (the section "Rules of thumb" in techniques.md).
- Do not write where you checked (file names, function names).
- What you could not find out after looking into it is written as "could not find out".

### Format

**The unit of one Note**
- One Note is per place the user is looking at (the same node, or a cluster of nodes looked at together). If there are several topics in the same place, do not add Notes; add headings inside the one Note.
- One thing is said only once. Do not write the same thing in two Notes.

**How the inside is built**
- On the top line, 🔗 and the name of the node being explained (you write it yourself).
- Give each topic an H3 heading. The heading says in one phrase what that topic wants to say. For a warning, the heading calls for attention. A different topic gets a different heading.
- Under a heading, one or two phrases.
- Indent at most one level.

**Sentences**
- Write in a polite register.
- When writing that a value should be changed, write the node name and the widget name (for example, "Set sage_attention on Patch Sage Attention KJ to disabled"). Writing "set the node to disabled" can be mistaken for talk about the node's state (bypass, mute).
- Text you want copied exactly (words to put in a prompt and so on) is enclosed in quotation marks (the ones usual in the user's language). Do not use inline code (`). It does not work in the legacy renderer, it becomes blue text in Nodes 2.0, and it cannot be read on a coloured Note.

Examples of before and after a rewrite are in the Note examples in references/examples.md.

## Where to place

**Place the overview and models Note at the upper left of the whole workflow.** Align its top edge with the top edge of the whole workflow.
- In the plan file, place it on the left with `note <file> left <leftmost block>`, and align the top edges with `align top <topmost block> <Note id>`.

**Place a Note on part of the processing near the node it explains.** After the nodes are arranged, place it with `note`.

- The width is one value within one workflow.
- The canvas applies the colour (readable-form.md, "Colour").

What not to do:
- Do not move the layout of the nodes for Notes. Do not widen the workflow for Notes.
- Do not place Notes on wire paths.

A Note is outside the workflow and does nothing. Even so, it is coloured and catches the eye, and it can be put anywhere. A single placement can clutter the workflow.

## Walkthrough

**The Walkthrough, like Notes, says what the graph does not show.**
- The groupings are the "Groupings" in B of the understanding document, lined up in processing order. If the groupings are not written, add them to the understanding document first.
- What to write: what a node or model is, why a step is there, what a value means, what the user changes here.
- What not to write: what can be read off the graph (which node passes what to which), and what the Notes say.
- The material is the understanding document, but it is notes for building, so do not copy it; rewrite it as sentences to be read.
- Say in one sentence what the grouping does, then short bullets below it.

Example:
- Before: "`TrimVideoLatent` cuts the latent, then passes it to `VAE Decode`."
- After: "`WanVaceToVideo` adds the reference image to the head of the latent as frames. Those frames are not needed in the result, so `TrimVideoLatent` drops them."
