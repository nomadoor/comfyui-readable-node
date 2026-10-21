# comfyui-readable-node

[日本語](README.ja.md)

An agent skill that rebuilds ComfyUI workflows into a form people can read: **Readable Node**.

1. **Do not hide nodes.** Expand subgraphs, open collapsed nodes, and do not overlap nodes.
2. **Do not hide wires.** Turn wireless links (Set/Get, Anything Everywhere, hidden links) back into wires.
3. **Left to right.** Flow from left to right in processing order.
4. **1 task = 1 workflow.** One workflow is one thing the user wants to do.
5. **Remove custom nodes as far as possible.** What can be built with core nodes is built with core.
6. **Colour appropriately.** Colour shows which function a node belongs to.

## Install

Use one of the ways below. Installing two lists the skill twice.

### Claude Code

In a Claude Code session, run:

```
/plugin marketplace add nomadoor/comfyui-readable-node
/plugin install comfyui-readable-node@comfyui-readable-node
```

To get updates automatically, open `/plugin`, go to Marketplaces, select `comfyui-readable-node` and choose Enable auto-update.

### Codex

```bash
codex plugin marketplace add nomadoor/comfyui-readable-node
codex plugin add comfyui-readable-node@comfyui-readable-node
```

### Other agents (Gemini CLI, Cursor, GitHub Copilot and others)

```bash
npx skills add nomadoor/comfyui-readable-node -g
```

This needs Node.js 22.20 or later.

The scripts need Python 3 (standard library only).

## Models

The skill runs a long job and checks its own work as it goes, so it needs a strong model.

- Claude Opus 5.5 works best.
- GPT 6.1 works, but may leave some layout problems.
- With anything below Sonnet, it may not work well.

## Use

1. Start ComfyUI. The skill reads the node definitions from the running ComfyUI.
2. Ask your agent, for example:
   - "Make `my_workflow.json` readable with Readable Node. ComfyUI is running at http://127.0.0.1:8188."
   - "Build a Text to Image workflow for Flux with Readable Node."

   To call it directly: `/comfyui-readable-node` (`/comfyui-readable-node:comfyui-readable-node` when installed as a plugin).
3. You get the rebuilt workflow (`.json`) and a report. Open the workflow in ComfyUI to check it.

As an extra, `replay.html` replays the rebuild step by step.

## Licence

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
