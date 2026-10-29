# Changelog

## 0.0.3 (2026-10-29)

- Fixed: values of VideoHelperSuite nodes (`VHS_`) read from an API-format workflow, or added on the canvas, landed in the wrong widgets (for example `frame_load_cap` in `skip_first_frames`). They are now written by name, as VideoHelperSuite saves them.
- VideoHelperSuite's loading nodes (Load Video and others) count as nodes that show a preview: their size includes the preview area, and a node under them is reported.
- A node is reported as directly below a node that grows when it overlaps it horizontally at all (it was more than half of the width).
- New: the Walkthrough view on the report page. The agent writes, for each canvas, the finished workflow cut into groupings in processing order with what the graph does not show (`canvas walk`), and the page shows one grouping at a time.
- The page command is now `canvas report` and the page `report.html` (`canvas replay` still works). It takes any language code; built-in sentences exist in English and Japanese, other languages get English.
- `canvas finish` names files it was given that are outside the working folder, and when it leaves files it does not know, says to delete only those and remove the empty folder with `rmdir`.
- SKILL.md is shorter: a Language section; the content rules moved to references/content.md, the understanding document to references/understanding.md, how to write the Walkthrough to references/notes.md. Steps 9 (write the report page) and 10 (report in the conversation).
- Checks: `overlapping rails` tells apart rails from two outputs of one node. Similar core nodes are suggested for a custom node even when every word of its name is common (Load Video).
- New: a review by another agent (references/review.md, step 9). After export, `canvas render <png> export` draws the picture with the exported node numbers; the reviewer writes a table of rows; each row is answered `fixed` or `left: <a quoted line of the rules>`, registered with `canvas review`, and shown on the report page. `canvas finish` stops until every canvas is reviewed and every row answered; `canvas finish fast` skips the review and the report page when the user asked for it fast.
- New: the Notes on part of the processing and the overview sentence are written by a separate agent (step 7); the builder places them.
- New moves: `canvas core <sampler>` prints the plan lines of the usual form around the first stage's sampler; `canvas guide` prints the lines of the references that name a node on the canvas; `canvas order` sets the order of the canvases on the report page (`<tab>/<canvas>` puts variants that differ only in values in one tab); `include <plan file>` in a plan; `put <unit> right|left <A> below|above <B>` (a place from two references); the reference `all` (every placed node with the group frames); `step` (a node stepped down below the wire passing on).
- Removed: `move`, `gap`, `width`, `gap N`, `note … width W` and `rail … out`. The canvas keeps every gap and width; the one move it makes after the plan is widening a gap between two columns where wires cross three times or more (120px). A rail runs at its source's output height unless `above`, `below` or `level` is written; it no longer looks for a height or moves nodes to make room.
- `canvas layout` replies with an error log: what the canvas did beyond the lines, what is unplaced, and each form that breaks a rule with the rule's file, section and bold sentence. `canvas check` lists the Bad forms first, then the ones that weigh less, then the other notices.
- New checks: samplers of stages in a row at different heights; a main-flow wire that is not horizontal; a reference wire level while the chain wire slants; no wire level into a merging node; the positive into a sampler slanting from the column left of it; a stage's chain level with the previous stage's result while its latent slants; the image into VAE Encode slanting; a side-use image rail above; model, vae and clip rails out of order (and a conditioning rail above them); a loader away from its first user; a Note away from the node it explains, a Note widening its group while there is room inside, a Note touching a node; a one-line String handed into a text area; a title the author gave (the layout also puts the display name back); custom nodes listed under "Use core" and core nodes the list replaces; a wire running along the rails but not on one; wires crossing three times or more in a gap.
- Node sizes: the image area of Load, Preview and Save nodes is a square (320, 320 and 520 px); every node is 30px taller for Nodes 2.0; Preview as Text is 300×180; an Autogrow input is sized for three connected inputs; loaders stacked in one column get one width (a column with aligned right edges keeps them); group padding is 20px on every side (54 at the top with the title bar); the rail gap is 60px.
- A node loading an image or video may keep a title "display name: what it takes" (`Load Image: image to edit`), as a value node does.
- `title` lines take effect before anything is placed, wherever they stand in the plan (a longer title no longer makes its node overlap the next one).
- The places the canvas offers for a Note no longer put another node between the Note and the node it explains. A raising Reroute is no longer called unneeded when the rail drawn at the output height would run too close to another rail.
- Export keeps node numbers from one export to the next; a Reroute the canvas made gets a number of its own.
- Fixed: a link from a broadcaster (Anything Everywhere) saved with the type `*` now takes the type of the output it comes from.
- A Load CLIP whose CLIP reaches no text encoder (one that only feeds an LLM) gets no fixed colour.
- A wire may go back one node's width only into Conditioning Zero Out, or from an empty latent into a scheduler.
- Report page: bypassed nodes are drawn in ComfyUI's bypass colour; the Walkthrough's first page lists the parts, the review and the widened gaps.
- References: readable-form.md rewritten as eight numbered rules with Why, Bad, Fine and Undecided (the usual form, nodes, wires, flow and position, loaders, value nodes, groups and colour, names); content.md rewritten as two decisions (split; keep, fix, replace or remove); examples.md ordered by those sections; glossary.md defines chain wire, raising and lowering Reroute, gaps, step and more; notes.md: link the Comfy-Org copy of a model, suggest a smaller form of the same model when memory runs short; techniques.md: what becomes of the author's negative text at cfg 1 depends on whether raising cfg is an ordinary choice; replacements.md: `canvas open` replaces Image Comparer, braces in Format Text are doubled.

## 0.0.2 (2026-10-21)

- Reads API-format workflows. They have no positions, so the original is shown as ComfyUI places it when it opens the file.
- `put … right|left` and `row` make the wire horizontal by default when the two nodes are wired (`top` aligns the tops).
- New checks: loader order (model loader on top, then vae and clip), a Load VAE used only by VAE Decode placed below the sampler, and a node placed directly below a node that grows in ComfyUI (samplers, image nodes, Create Bounding Boxes).
- `canvas finish` deletes the files the canvas knows in the working folder (and the folder, once nothing else is left) after every canvas is exported and the replay page is up to date.
- README: install as a plugin first (Claude Code, Codex), then `npx skills`; a section on models.
- The plugin manifest has a version. Claude Code and Codex update when it changes. If you installed 0.0.1 as a Codex plugin, it did not update itself; this version and later ones do.

## 0.0.1 (2026-10-20)

- First version. Not announced yet.
- Rebuilds a ComfyUI workflow into the Readable Node form on a small layout tool (`canvas.py`): reads the original (subgraphs and wireless links expanded), rebuilds with core nodes where possible, lays out from relative instructions, checks the layout, writes the workflow and a replay page.
- Install with `npx skills` or as a Claude Code plugin.
