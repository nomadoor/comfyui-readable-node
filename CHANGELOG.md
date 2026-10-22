# Changelog

## Unreleased

- Fixed: values of VideoHelperSuite nodes (`VHS_`) read from an API-format workflow, or added on the canvas, landed in the wrong widgets (for example `frame_load_cap` in `skip_first_frames`). They are now written by name, as VideoHelperSuite saves them.
- VideoHelperSuite's loading nodes (Load Video and others) count as nodes that show a preview: their size includes the preview area, and a node under them is reported.
- A node is reported as directly below a node that grows when it overlaps it horizontally at all (it was more than half of the width).
- New: the Walkthrough view on the report page. The agent writes, for each canvas, the finished workflow cut into groupings in processing order with what the graph does not show (`canvas walk`), and the page shows one grouping at a time.
- The page command is now `canvas report` and the page `report.html` (`canvas replay` still works). It takes any language code; built-in sentences exist in English and Japanese, other languages get English.
- `canvas finish` names files it was given that are outside the working folder, and when it leaves files it does not know, says to delete only those and remove the empty folder with `rmdir`.
- SKILL.md is shorter: a Language section; the content rules moved to references/content.md, the understanding document to references/understanding.md, how to write the Walkthrough to references/notes.md. Steps 9 (write the report page) and 10 (report in the conversation).
- Checks: `overlapping rails` tells apart rails from two outputs of one node. Similar core nodes are suggested for a custom node even when every word of its name is common (Load Video).

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
