# How to write Notes

There are two kinds of Notes placed in a workflow: the model Note (one) and the Notes of the parts (only when there is something to write). For both, write the text in a Markdown file and place it with the canvas `note`.

The body of Readable Node is rebuilding the workflow so it can be read. Notes fill in what the rebuild could not say, and fewer is better. The overall explanation (what was tidied, the difference between two versions, what was replaced) is reported in the conversation, not in Notes. (Undecided: SKILL.md says to write the differences from a replacement in a Note as well. See "Where replacement stops" in SKILL.md.)

## The model Note

- The colour is purple. Where to place it: "When to write, where to place" below.
- At the very top, give it the same heading in every workflow. Write the heading in the user's language. In English it is:

  ```markdown
  ## What this workflow does
  ```

  Below it, in one or two sentences, write the essence of this workflow: what goes in and what comes out.
- Below that, the list of models. Model names and folder names are in English, so they are outside the language rule. The format is exactly the following (the canvas `models` gives a draft). The heading `## models` is always written exactly like this, in every language, because the canvas finds the model Note by it.

````markdown
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

- For the download URL and size, use what was in the original workflow (the node's information, or the author's Note). If the original does not have it, search HuggingFace (Comfy-Org's repositories and so on) for the same file name, and write only a URL where you confirmed the file actually exists. Do not make one up by guessing. If it is not found, do not write it.
- Models that a node downloads by itself the first time it runs are written below the list: what, where it goes, and what is needed for it. They do not appear in widget values, so you find them when you read the custom node's source.

## What goes in the Notes of the parts

Write only the following four. If nothing fits any of them, do not write. Some workflows have no Note at all.

### Explanation fitted to the user (title: Usage)
Do not decide the user's level yourself. You are in a conversation with the person using this skill. From what they asked and what they said, you can tell how much they know. Within what you can tell, write only where that person is likely to stumble. While you cannot tell, do not write. Do not write, from the start, every explanation for someone touching it for the first time (if they do not understand, the user can ask the agent).

### The author's techniques (title: Author's techniques)
Things the author left words about as a technique (the author's Notes, descriptions, titles). Convey briefly, in the author's own words, why that value or node is there. If no words remain, do not write by guessing.

### The author's techniques whose purpose cannot be seen by looking (title: Usage)
For author's techniques that were kept and whose purpose cannot be seen by looking (a structure that takes a number from a list by the index of a Custom Combo so the size can be chosen by name, a resize that shrinks the image before Text Generate, pixel-count values lined up in a list, and so on), write the purpose in one phrase. Even without the author's words, write it if the purpose is known from the source or from checking (do not write guesses).

### Warnings (title: Caution)
Puzzling processing that is kept, other than what was removed as entirely useless. Even if the author had an intent, write it if it is strange.

- What can only be a mistake, with no other reading, is fixed. What was fixed is not written in a Note; it is reported in the conversation.
- What is technically and obviously meaningless is removed. What was removed is also reported in the conversation.
- What may have been the author's choice, or what is a trade-off between gain and loss, is left unchanged and written here.

### Note things down
The author's techniques, and puzzling things that were kept, are noted down on the spot, as you decide them, during the rebuild (while deciding what the workflow does, working out how to build it, and rearranging it). The Notes of the parts are made only from what was noted down this way and from what you learned about the user in the conversation. They are not made from everything you looked into.

## What not to write

- What can be learned from the graph. This is absolute. Sentences that restate node names and values, and sentences that read nodes aloud in wire order, are not Notes.
- Helper nodes (graphs or previews only for looking), and places that only load the specified model.
- The builder's circumstances (why it was wired this way, why this node was used).
- The same thing in two places. One thing is said only once.

## Form

- The unit of one Note is the place the user is looking at (the same node, or a cluster of nodes looked at together). Topics about the same place are gathered into one Note.
- The titles are "Markdown Note: Usage", "Markdown Note: Author's techniques", "Markdown Note: Caution". When one Note holds two, line them up like "Markdown Note: Author's techniques / Caution" (set with the canvas `title`). Write the part after "Markdown Note: " in the user's language.
- On the top line, 🔗 and the name of the node being explained (you write it yourself).
- Give each topic an H3 heading. The heading says in one phrase what that topic wants to say. For a warning, the heading calls for attention. A different topic gets a different heading.
- Under a heading, one or two phrases. Do not make it long.
- Do not use inline code (`). Text you want copied exactly, such as words to put in a prompt, is enclosed in quotation marks (the ones usual in the user's language).
- Use a polite register. Indent at most one level.

Examples of before and after a rewrite are the Note examples in references/examples.md.

## When to write, where to place

The Notes of the parts are written from what was noted down, after the rebuild is finished (step 7 of SKILL.md).

A Note is outside the workflow and does nothing. It is coloured and catches the eye, and it can be put anywhere. So a single placement can clutter the workflow.

- Notes are not considered in the layout. After the nodes are arranged, place each Note with `note` near the node it explains.
- Do not move the layout of the nodes for Notes. Do not widen the workflow for Notes.
- The width is one value within one workflow.
- Do not place Notes on wire paths.
- The model Note is top-aligned with the top edge of the whole workflow. Where it goes left or right is not decided (to the left of the whole, or near the loaders).

## Language

Write the text of Notes in the language of the person using the skill. Node names and function names are used as they are, not reworded. Phrases that people using ComfyUI use normally, such as Text to Image, Image to Video, Hires.fix, are not reworded either.

## Check before writing

Each "this is what happens" written in a Note is checked, one by one, against the node's source, the official description, the model's description (model card), or a small run, before writing. (Undecided: SKILL.md says to run ComfyUI only when the user asks. See "What not to do" in SKILL.md.) The author's explanation is not used either until its reason is checked.

- Do not write where you checked (file names, function names).
- What you could not find out after looking into it is written as "could not find out".

- When writing that a value should be changed, write the node name and the widget name (for example, "Set sage_attention on Patch Sage Attention KJ to disabled"). Writing "set the node to disabled" can be mistaken for talk about the node's state (bypass, mute).
