# comfyui-readable-node

[English](README.md)

ComfyUI の workflow を、人が読みやすい形（**Readable Node**）に組み直す、エージェント向けの skill です。

1. **ノードを隠さない。** subgraph は展開し、折りたたみは開き、ノードを重ねない。
2. **線を隠さない。** 無線（Set/Get、Anything Everywhere、線の非表示など）は、線に戻す。
3. **左から右へ。** 処理の順に左から右へ流す。
4. **1 task = 1 workflow。** 1 workflow は、使う人のやりたいこと一つ。
5. **custom node はできるだけ取り除く。** core のノードで組めるものは core で組む。
6. **適切に色を付ける。** 色は、どの機能に属するかを示す。

## 導入

下のどれか一つで入れてください。二つ入れると、skill が二重に並びます。

### Claude Code

Claude Code のセッションの中で、次を実行してください。

```
/plugin marketplace add nomadoor/comfyui-readable-node
/plugin install comfyui-readable-node@comfyui-readable-node
```

自動で更新したいときは、`/plugin` の Marketplaces で `comfyui-readable-node` を選び、Enable auto-update を選んでください。

### Codex

```bash
codex plugin marketplace add nomadoor/comfyui-readable-node
codex plugin add comfyui-readable-node@comfyui-readable-node
```

### そのほかのエージェント（Gemini CLI、Cursor、GitHub Copilot など）

```bash
npx skills add nomadoor/comfyui-readable-node -g
```

Node.js 22.20 以上が必要です。

scripts を動かすには Python 3 が必要です（標準ライブラリだけを使います）。

## モデル

長い作業を自分で確かめながら進める skill なので、強いモデルを使ってください。

- いちばん良いのは Claude Opus 5.5 です。
- GPT 6.1 でも使えますが、配置の崩れが残ることがあります。
- 少なくとも Sonnet 以上のモデルでないと、うまくいかないかもしれません。

## 使い方

1. ComfyUI を起動しておいてください。skill は、動いている ComfyUI からノードの定義を読みます。
2. エージェントに頼んでください。たとえば:
   - 「Readable Node で `my_workflow.json` を読みやすくして。ComfyUI は http://127.0.0.1:8188 で動いています。」
   - 「Readable Node で、Flux の Text to Image の workflow を作って。」

   確実に呼びたいときは `/comfyui-readable-node` と打ってください（plugin で入れたときは `/comfyui-readable-node:comfyui-readable-node`）。
3. 組み直した workflow（`.json`）と報告が出てきます。workflow を ComfyUI で開いて確かめてください。

報告のページ `report.html` も出ます。元の workflow、組み直しの手順、出来上がった workflow の説明（Walkthrough）を見られます。

## ライセンス

MIT。[LICENSE](LICENSE) と [NOTICE](NOTICE) を見てください。
