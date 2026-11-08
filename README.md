# ComfyUI Readable Node

[![English](https://img.shields.io/badge/lang-English-blue)](README.md) [![日本語](https://img.shields.io/badge/lang-%E6%97%A5%E6%9C%AC%E8%AA%9E-red)](README.ja.md) [![中文](https://img.shields.io/badge/lang-%E4%B8%AD%E6%96%87-green)](README.zh.md)

[![Site](https://img.shields.io/badge/site-comfyui.nomadoor.net-orange)](https://comfyui.nomadoor.net/) [![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

[![ComfyUI Readable Node](https://img.youtube.com/vi/_Pkw9Mcvkng/maxresdefault.jpg)](https://youtu.be/_Pkw9Mcvkng)

A skill that rebuilds ComfyUI workflows so they are easy to read (**Readable Node**).

It doesn't just tidy up the layout with a script.
The AI takes the workflow apart and works out what it does. A workflow that packs several tasks into a single file is split into separate workflows, one per task, and each is rebuilt from scratch following the rules below.

It preserves what the original workflow does as much as possible, while replacing custom nodes with core nodes and rebuilding parts more simply where it can, making the workflow more robust without changing its purpose.

It also works when you ask an AI to build a new workflow from scratch.

## What Readable Node is

Here, "easy to read" means you can tell at a glance what the workflow does, it runs reliably, and it is easy to rework.
It follows six rules:

1. **Don't hide nodes**<br>
   Expand subgraphs, open collapsed nodes, and don't overlap nodes.
2. **Don't hide wires**<br>
   Turn wireless links (Set/Get, Anything Everywhere, hidden wires, etc.) back into wires. Avoid so-called Bento layouts, which pack nodes tightly together, since they hide the wires too.
3. **Left to right**<br>
   Flow from left to right in processing order.
4. **One workflow, one task**<br>
   A workflow does one thing the user wants to do.
5. **Keep custom nodes to a minimum**<br>
   What can be built with core nodes is built with core.
6. **Color appropriately**<br>
   Color shows which function a node belongs to.

## Install

Choose the method for the app you use.

Note: don't install it both as a plugin and with npx, or you'll end up with two copies of the skill.

<details>
<summary><b>Claude desktop app</b></summary>

1. In **Settings → Customize → Plugins**, choose **+ Add → Add marketplace → Add from a repository**
2. Enter `nomadoor/comfyui-readable-node`
3. Click **+** on `comfyui-readable-node`

</details>

<details>
<summary><b>Claude Code (CLI)</b></summary>

In a terminal, run:

```bash
claude plugin install comfyui-readable-node --marketplace nomadoor/comfyui-readable-node
```

</details>

<details>
<summary><b>ChatGPT desktop app (Codex)</b></summary>

1. Open **Plugins** and click **Add** to open **Add plugin marketplace**
2. Enter `https://github.com/nomadoor/comfyui-readable-node.git` in **Source**. Leave **Git ref** and **Sparse paths** empty
3. On the **Personal** tab, click **+** on `comfyui-readable-node`

</details>

<details>
<summary><b>Codex CLI</b></summary>

In a terminal, run:

```bash
codex plugin marketplace add nomadoor/comfyui-readable-node
codex plugin add comfyui-readable-node@comfyui-readable-node
```

</details>

<details>
<summary><b>Other agents (Gemini CLI, Cursor, GitHub Copilot, etc.)</b></summary>

In a terminal, run the following. Requires Node.js 22.20 or later.

```bash
npx skills add nomadoor/comfyui-readable-node -g
```

</details>

The skill's scripts need Python 3 (standard library only).

## Usage

1. Start ComfyUI first. The skill reads the node information from the running ComfyUI.
2. Ask your agent, for example:
   - "Make `my_workflow.json` readable with Readable Node. ComfyUI is running at http://127.0.0.1:8188."
   - "Build a Text to Image workflow for Flux with Readable Node."

   To make sure the skill is invoked, type `/comfyui-readable-node` (`/comfyui-readable-node:comfyui-readable-node` when installed as a plugin).
3. Open the finished workflow in ComfyUI and check it.

A workflow of about 25 nodes takes around 10 minutes. A large workflow can take 20 to 40 minutes.

## What you get

<!-- before / after image goes here -->

- **The rebuilt workflow**: a `.json` file with `_readable` appended to the original name. The original file is not overwritten.
- **report.html**: open it in a browser to watch the AI rebuild the workflow and read an explanation of the result.
  - Original: compare with the original workflow.
  - Rebuilt: replay the AI's moves on a timeline, one step at a time.
  - Walkthrough: the finished workflow explained part by part.

## Recommended AI models

Reading a workflow and rebuilding it cleanly is far more demanding than it looks, so use the strongest model you can.

- Claude Opus 5.5: the skill was developed with it, and it's my top recommendation.
- GPT 6.1 / 6.0 Astra also work, but the layout may still have a few issues.

## What the skill reads

- Your local ComfyUI, to see which nodes are installed.
- Workflows on [Comfy with ComfyUI](https://comfyui.nomadoor.net/), which it may use as a reference for how to build workflows.

## Reporting problems

If a rebuilt workflow is wrong or hard to read, let me know in an [issue](https://github.com/nomadoor/comfyui-readable-node/issues/new/choose). A workflow may contain your prompts and folder paths, so remove anything you don't want to share publicly before attaching it.

## Author

[nomadoor](https://x.com/noma_door). I run [Comfy with ComfyUI](https://comfyui.nomadoor.net/), a site that explains the basics of ComfyUI. This skill is built on more than 400 workflows published there.

## License

MIT
