# ComfyUI Readable Node

[![English](https://img.shields.io/badge/lang-English-blue)](README.md) [![日本語](https://img.shields.io/badge/lang-%E6%97%A5%E6%9C%AC%E8%AA%9E-red)](README.ja.md) [![中文](https://img.shields.io/badge/lang-%E4%B8%AD%E6%96%87-green)](README.zh.md)

[![Site](https://img.shields.io/badge/site-comfyui.nomadoor.net-orange)](https://comfyui.nomadoor.net/) [![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

[![ComfyUI Readable Node](https://img.youtube.com/vi/_Pkw9Mcvkng/maxresdefault.jpg)](https://youtu.be/_Pkw9Mcvkng)

ComfyUI の workflow を、読みやすい形（**Readable Node**）に組み直す skill です。

単にスクリプトでレイアウトを整えるものではありません。
AI は workflow を一度ばらばらにし、何をしているのかを理解します。その後、タスクがいくつも詰め込まれているものは 1 つずつの workflow に分け、下のルールに従って 0 から組み直します。

元の workflow がやっていることはなるべく保ちつつ、custom node を core のノードに置き換えたり、よりシンプルに組める手段があればそちらで組み直したりして、本質を変えないまま堅牢な workflow にしていきます。

もちろん、0 から AI に workflow を組んでもらうときにも役立ちます。

## Readable Node とは

ここでは「読みやすい」を、何をしているかがスッと頭に入って、安定して動いて、気軽に組み替えられること、と定義しています。
そのために必要な 6 つのルールが以下です。

1. **ノードを隠さない**<br>
   subgraph は展開し、折りたたみは開き、ノードを重ねない。
2. **ワイヤを隠さない**<br>
   無線（Set/Get、Anything Everywhere、ワイヤの非表示など）は、ワイヤに戻す。ノードをギチギチに詰めた、いわゆる Bento レイアウトも、ワイヤが隠れるのでやめる。
3. **左から右へ**<br>
   処理の順に左から右へ流す。
4. **1 つの workflow に、1 つの作業**<br>
   1 workflow は、使う人のやりたいこと一つ。
5. **カスタムノードは最小限**<br>
   core のノードで組めるものは core で組む。
6. **適切な色付け**<br>
   色は、どの機能に属するかを示す。

## 導入

使っているアプリに合わせて、下のどれかで入れてください。

※ plugin として入れたあとに npx でも入れると、skill が二重に入ってしまうので注意してください。

<details>
<summary><b>Claude デスクトップアプリ</b></summary>

1. **プラグイン** の画面で **＋追加 → マーケットプレイスを追加 → リポジトリから追加** を選ぶ
2. `nomadoor/comfyui-readable-node` を入力
3. `comfyui-readable-node` の **＋** をクリック

</details>

<details>
<summary><b>Claude Code（CLI）</b></summary>

ターミナルで次を実行してください。

```bash
claude plugin install comfyui-readable-node --marketplace nomadoor/comfyui-readable-node
```

</details>

<details>
<summary><b>ChatGPT デスクトップアプリ（Codex）</b></summary>

1. **カスタマイズ → プラグイン** で **追加** を押す
2. ソースに `https://github.com/nomadoor/comfyui-readable-node.git` を入力。Git ref とスパースパスは空のまま
3. **個人用** のタブの `comfyui-readable-node` の **＋** をクリック

</details>

<details>
<summary><b>Codex CLI</b></summary>

ターミナルで次を実行してください。

```bash
codex plugin marketplace add nomadoor/comfyui-readable-node
codex plugin add comfyui-readable-node@comfyui-readable-node
```

</details>

<details>
<summary><b>そのほかのエージェント（Gemini CLI、Cursor、GitHub Copilot など）</b></summary>

ターミナルで次を実行してください。Node.js 22.20 以上が必要です。

```bash
npx skills add nomadoor/comfyui-readable-node -g
```

</details>

skill の scripts を動かすには、Python 3 が必要です（標準ライブラリだけを使います）。

## 使い方

1. ComfyUI を起動しておいてください。skill は、動いている ComfyUI からノードの情報を読みます。
2. エージェントに頼んでください。たとえば:
   - 「Readable Node で `my_workflow.json` を読みやすくして。ComfyUI は http://127.0.0.1:8188 で動いています。」
   - 「Readable Node で、Flux の Text to Image の workflow を作って。」

   確実に呼びたいときは `/comfyui-readable-node` と打ってください（plugin で入れたときは `/comfyui-readable-node:comfyui-readable-node`）。
3. 出来上がった workflow を ComfyUI で開いて、確かめてください。

時間は、ノード 25 個ほどの workflow で 10 分前後です。大きな workflow だと 20〜40 分かかることもあります。

## できあがるもの

<!-- before / after image goes here -->

- **組み直した workflow**: 元のファイル名に `_readable` を付けた `.json` です。元のファイルは上書きしません。
- **report.html**: ブラウザで開くと、AI が組み直していく様子と、出来上がった workflow の解説が見られます。
  - Original: 元の workflow と見比べられます。
  - Rebuilt: AI がノードを一手ずつ動かしていく様子を、タイムラインで再生できます。
  - Walkthrough: 出来上がった workflow を、部分ごとに解説します。

## おすすめの AI モデル

workflow を読み解いて綺麗に組み直すのは、見た目に反してかなり重い作業なので、できるだけ強いモデルを使ってください。

- 開発に使っていて、いちばんおすすめなのは Claude Opus 5.5 です。
- GPT 6.1 / 6.0 Astra でも使えますが、配置の崩れが残ることがあります。

## skill が読みに行くもの

- お使いの PC で動いている ComfyUI。どんなノードが入っているかを確かめます。
- [Comfy with ComfyUI](https://comfyui.nomadoor.net/) の workflow。組み方の参考にすることがあります。

## うまくいかなかったとき

組み直した workflow がおかしい、読みにくいときは、[issue](https://github.com/nomadoor/comfyui-readable-node/issues/new/choose) で教えてください。workflow には、プロンプトやフォルダのパスが入っていることがあります。公開したくないものは消してから添付してください。

## 作者

[nomadoor](https://x.com/noma_door)。ComfyUI の基本を解説するサイト [Comfy with ComfyUI](https://comfyui.nomadoor.net/) を運営しています。この skill は、サイトに載せてきた 400 本を超える workflow を土台に作りました。

## ライセンス

MIT
