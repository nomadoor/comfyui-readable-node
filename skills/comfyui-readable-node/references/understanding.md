# The understanding document

The understanding of the workflow, written before building (`$W/understanding.md`). Write it in two parts, the whole file (A) and each task (B), and add C to E.

## A. The whole file

- The list of outputs (what is output, which node).
- The list of tasks (which outputs form one task; the core of each task).
- How tasks relate (unconnected / a later stage uses an earlier stage's result / only models or values are shared / different ways chosen with switch or bypass / different ways of doing the same thing).
- How to split (how many workflows, which version each is, why, by content.md "Split"; how to keep disabled functions).
- What belongs to no task, and what to do with it.

## B. Each task

- What it does (from what comes out at the end and what the user wants to do; do not mistake an intermediate means for the goal). What the user puts in and gets out.
- The core, and the base form (t2i / i2i / t2v …, the kind of sampler, CFG, how the model is loaded). Pre- and post-processing added to the base. Disabled functions.
- Values (values changed on each generation and values that do not change once decided; which are handed out from one). Models.
- The table of custom nodes (one by one. For each function: "the value in this workflow, the default value, whether core can do it". Whether the part core cannot do changes the shape of the output. Whether to keep it or use core).
  - For ones in replacements.md, copy that row.
  - For ones not there, always look at the "core nodes with similar names" that `canvas open` gives, and check in the source.
- Groupings (which nodes form one grouping; units of work, and units of role such as loader, text encoder, sampler).
- For every node: what it does with its values here (content.md, "Read before deciding"). Then: things that look like the author's mistakes, processing that does nothing, candidates to remove and candidates to replace, and why.

## C. Compare with the author's words (when there is an original)

Read the author's Notes, group names and titles (`canvas src words`) after writing A and B.
- What you learned.
- Where they disagree with A and B.
- What remains in words as the author's techniques.

## D. What you do not know

If there is someone to ask, ask. If you cannot ask, lean towards keeping, and report it.

## E. Candidates for Notes

- Explanations the user needs.
- The author's techniques (ones with the author's words).
- Warnings about puzzling processing that was kept.
