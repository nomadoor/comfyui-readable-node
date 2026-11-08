# ComfyUI Readable Node

[![English](https://img.shields.io/badge/lang-English-blue)](README.md) [![日本語](https://img.shields.io/badge/lang-%E6%97%A5%E6%9C%AC%E8%AA%9E-red)](README.ja.md) [![中文](https://img.shields.io/badge/lang-%E4%B8%AD%E6%96%87-green)](README.zh.md)

[![Site](https://img.shields.io/badge/site-comfyui.nomadoor.net-orange)](https://comfyui.nomadoor.net/) [![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

[![ComfyUI Readable Node](https://img.youtube.com/vi/_Pkw9Mcvkng/maxresdefault.jpg)](https://youtu.be/_Pkw9Mcvkng)

一个把 ComfyUI workflow 重新组织成易读形式（**Readable Node**）的 skill。

它不只是用脚本整理布局。
AI 会先拆解 workflow，弄清楚它在做什么。如果一个 workflow 里塞了好几项任务，就按任务拆成一个个 workflow，再按照下面的规则从零重新搭建。

它会尽量保留原 workflow 所做的事情，同时把自定义节点（custom node）换成原生节点（core 节点），或在有更简单的搭建方式时改用更简单的方式，在不改变本质的前提下，让 workflow 更加稳健。

当然，让 AI 从零搭建 workflow 时，同样可以使用这个 skill。

## 什么是 Readable Node

这里把"易读"定义为：一眼就能明白它在做什么，运行稳定，并且便于修改和重新组合。
为此需要以下 6 条规则。

1. **不隐藏节点**<br>
   展开 subgraph，展开被折叠的节点，节点之间不重叠。
2. **不隐藏连线**<br>
   把不走连线的隐式连接（Set/Get、Anything Everywhere、隐藏的连线等）恢复成连线。把节点挤得满满当当的所谓 Bento 布局，也会把连线遮住，同样不要用。
3. **从左到右**<br>
   按处理顺序从左往右排列。
4. **一个 workflow，一项任务**<br>
   一个 workflow 只做用户想做的一件事。
5. **自定义节点尽量少**<br>
   能用原生节点搭的，就用原生节点搭。
6. **恰当地上色**<br>
   颜色表示节点属于哪项功能。

## 安装

请根据你使用的应用，选择下面的一种方式安装。

注意：以 plugin 方式安装后，如果再用 npx 安装，skill 会被重复安装。

<details>
<summary><b>Claude 桌面应用</b></summary>

1. 在 **Settings → Customize → Plugins** 中，选择 **+ Add → Add marketplace → Add from a repository**
2. 输入 `nomadoor/comfyui-readable-node`
3. 点击 `comfyui-readable-node` 旁边的 **+**

</details>

<details>
<summary><b>Claude Code（CLI）</b></summary>

在终端中运行：

```bash
claude plugin install comfyui-readable-node --marketplace nomadoor/comfyui-readable-node
```

</details>

<details>
<summary><b>ChatGPT 桌面应用（Codex）</b></summary>

1. 打开 **Plugins**，点击 **Add**，选择 **Add plugin marketplace**
2. 在 **Source** 中输入 `https://github.com/nomadoor/comfyui-readable-node.git`。**Git ref** 和 **Sparse paths** 留空
3. 在 **Personal** 标签页中，点击 `comfyui-readable-node` 旁边的 **+**

</details>

<details>
<summary><b>Codex CLI</b></summary>

在终端中运行：

```bash
codex plugin marketplace add nomadoor/comfyui-readable-node
codex plugin add comfyui-readable-node@comfyui-readable-node
```

</details>

<details>
<summary><b>其他 agent（Gemini CLI、Cursor、GitHub Copilot 等）</b></summary>

在终端中运行以下命令。需要 Node.js 22.20 或更高版本。

```bash
npx skills add nomadoor/comfyui-readable-node -g
```

</details>

skill 中的脚本需要 Python 3（只使用标准库）。

## 使用方法

1. 请先启动 ComfyUI。skill 会从正在运行的 ComfyUI 读取节点信息。
2. 向 agent 提出请求，例如：
   - "用 Readable Node 把 `my_workflow.json` 整理得易读一些。ComfyUI 运行在 http://127.0.0.1:8188。"
   - "用 Readable Node 搭一个 Flux 的 Text to Image workflow。"

   如果想确保调用这个 skill，请输入 `/comfyui-readable-node`（如果以 plugin 方式安装，则输入 `/comfyui-readable-node:comfyui-readable-node`）。
3. 在 ComfyUI 中打开完成的 workflow，检查一下。

25 个节点左右的 workflow 大约需要 10 分钟。较大的 workflow 可能需要 20 到 40 分钟。

## 输出内容

<!-- before / after image goes here -->

- **重新搭建的 workflow**：文件名为原文件名加 `_readable` 的 `.json` 文件，不会覆盖原文件。
- **report.html**：在浏览器中打开，可以看到 AI 重新搭建的过程，以及对完成的 workflow 的讲解。
  - Original：与原 workflow 对照。
  - Rebuilt：在时间轴上回放 AI 一步一步移动节点的过程。
  - Walkthrough：分部分讲解完成的 workflow。

## 推荐的 AI 模型

读懂 workflow 并整齐地重新搭建，远比看起来繁重，请尽量使用能力最强的模型。

- 开发时使用的是 Claude Opus 5.5，也最推荐使用它。
- GPT 6.1 / 6.0 Astra 也可以使用，但可能会留下一些布局上的问题。

## skill 会读取的内容

- 你电脑上正在运行的 ComfyUI，用来确认装了哪些节点。
- [Comfy with ComfyUI](https://comfyui.nomadoor.net/) 上的 workflow，有时会用作搭建方法的参考。

## 遇到问题时

如果重新搭建的 workflow 有问题或不好读，请通过 [issue](https://github.com/nomadoor/comfyui-readable-node/issues/new/choose) 告诉我。issue 请用英文或日文撰写。workflow 中可能包含提示词和文件夹路径，附上之前请删除不想公开的内容。

## 作者

[nomadoor](https://x.com/noma_door)。运营着一个讲解 ComfyUI 基础知识的网站 [Comfy with ComfyUI](https://comfyui.nomadoor.net/)。这个 skill 以该网站上发布的 400 多个 workflow 为基础制作。

## 许可证

MIT
