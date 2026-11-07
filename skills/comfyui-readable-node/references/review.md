# The review after export

Another agent reviews each exported workflow. You do not judge your own layout: having made it, you see what you meant rather than what is there.

## What you do

1. After `canvas export <name>.json`, draw the picture for the reviewer: `canvas render $W/review_<canvas>.png export`. It also writes `$W/review_<canvas>.txt`, the titles and Note texts the picture cannot draw. Do not look at them yourself.
2. Start a separate agent (a subagent) for each canvas and give it the brief below as written, with the paths filled in (`<skill>` is the folder that holds SKILL.md). Add nothing: no hints, no summary, no reasons, nothing you already know is wrong.
   - A canvas made with `canvas new <name> from <canvas>` that differs from it only in values (the same nodes, wires and layout) is not reviewed again: write `Not reviewed: values only, the same layout as <canvas>` in `$W/review_<canvas>.md`.
   - If no separate agent can be started, do not review it yourself: write `Not reviewed: <why>` in `$W/review_<canvas>.md`.
3. Fix the rows one at a time: change the plan (or the build) for that row, run `canvas layout`, and keep the change if the row's form is gone and the check list gained no new item; otherwise `canvas undo` and try another way. Then export again.
   When you think a row itself is wrong (the reviewer misread the picture), do not answer it yourself: send that row and why to the same reviewer, once. It withdraws the row (moves it under the table as "Withdrawn: <rule> — <why>") or keeps it. If the same reviewer cannot be reached, answer the row as below.
   Answer every row in the last column, once: `fixed`, or `left: <why, in the user's language>`. A row is left only with a quoted line of readable-form.md or notes.md, written between quotes as it is in the file (the whole line or a part of it, eight characters or more, copied exactly): the Fine line that applies, or the bold line of the rule that fixing it would break. Each left row gives its own reason. `canvas review` stops on a left row without such a quote. Do not edit the reviewer's rows or its `Checked:` line.
4. `canvas use <canvas>`, `canvas review $W/review_<canvas>.md`, then `canvas report` again. The report page shows every row with your answer. `canvas finish` stops while a review is missing, a row is unanswered, or the canvas changed after its review was registered; `review` stops when a row says `fixed` but nothing changed since the picture the reviewer saw. Each canvas is reviewed once: after fixing the rows, do not start another review.

## The brief (give it as written)

```text
You look at a ComfyUI workflow that another agent rebuilt to be easy to read, and say where it does not look easy to read. Do not grade it. Assume it has real problems.

Read only these files; open nothing else and do not search the disk:
- the picture of the rebuilt workflow: <png path> (the numbers on the nodes are node ids; thick white lines are wires passing behind nodes)
- what the picture cannot draw: <txt path> (each node's number and its title as ComfyUI shows it, and the text of every Note; the picture's font has Latin letters only and draws no Note text)
- the rules: <skill>/references/readable-form.md and notes.md, and the words they use: glossary.md

Judge from the picture and that text, as a person opening the workflow would see it. Do not read the workflow JSON and do not compute anything: what can be measured (overlaps, wires behind nodes, slanted wires, gaps) the tool that built it already checked. First look at the whole: does it look like a person laid it out? Far-off nodes, long wires, empty areas, crowded places, wires crossing, a Note away from what it explains. Then go through the rules of the two files. The tool already checks these forms and names them to the builder, so do not report them: overlapping nodes; a node or Reroute right below a node that grows; a Preview or Save above its source; a wire or node over a group's title; group frames overlapping; model, vae and clip rails out of order, or in another order than their loaders; Reroutes doing nothing or carrying a single value that a direct wire could carry; a wire into Compare or another output hidden behind a node that saves. Report a place only when it has the rule's Bad form and does not match its Fine form. In a workflow without a sampler, the rules about samplers do not apply. One row per cause, listing all its nodes.

Write <$W/review_<canvas>.md> in <the user's language>, keeping node names, rule names and ComfyUI terms as they are:

# Review: <canvas>

| rule | nodes | what to change | answer |
|---|---|---|---|
| <file>: <the rule's bold line, as written; "|" as "\|"> | <node ids, space-separated> | <what to place, connect or remove differently> | |

Leave the answer column empty. If nothing breaks a rule, write "No findings." instead of the table.
If the builder later sends you a row it thinks is wrong, look again once: withdraw it (move it under the table as "Withdrawn: <rule> — <why>", above the "Checked:" line) or keep it, and reply in one line.
End the file with: "Checked: readable-form.md <n> rules, notes.md <n> rules".
Reply with one line: the number of rows and the "Checked:" line.
```
