# The conversation report

**Short, only the points. Details are answered when the user asks.** Why: a long report is not read, and what the workflow and its Notes show need not be told again.
- In the user's language, in a polite register. The headings below are written in that language, with the same meaning.
- Ask nothing while working: build to the end, then report.

1. When the workflow was split, the first line says so ("Split into two workflows."). When it was not, there is no such line.
2. The folder of the files, once. Under it, each file name as a bullet, with nested lines:
   - What the workflow makes, from what. From the second workflow on, with how it differs ("The same video, with Turbo LoRA in 4 steps.").
   - Only when split: how it differs from the others (a LoRA, the steps).
   - For `report.html`: "Open it to compare with the original workflow and to read how the rebuilt workflow works." When there is no original: "Open it to read how the workflow works."
3. **Changed from the original workflow** (when there is an original): each change that makes the result differ, one bullet each. Nested under it: the reason, when the change alone does not explain itself; what takes the place of something lost. Of what the references say to report, only these are said.
4. **What else could be changed**, only when there is something: another build with core only (also when a Caution Note already says it); a step that makes in core an input the user would make elsewhere (a depth map from a photo with Depth Anything 3), not added. Write it as "there is also a form that …", not as what you can do ("I can …", "… can also be made").
5. **Other**, only when there is something: a model whose download link was not found; a custom node not installed, whose values were matched from its source.

Do not write: what was removed or replaced without changing the result; why it was split; the steps taken; the check list; the review; that the workflow was not run in ComfyUI.
