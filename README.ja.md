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

下の二つのどちらか一つで入れます。同じ PC で両方を使うと、skill が二重に並びます。

**どのエージェントでも（Claude Code、Codex、Gemini CLI、Cursor、GitHub Copilot など）**

```bash
npx skills add nomadoor/comfyui-readable-node -g
```

更新:

```bash
npx skills update -g
```

Node.js 22.20 以上が要ります。

**Claude Code（Node.js は要りません）**

Claude Code のセッションの中で:

```
/plugin marketplace add nomadoor/comfyui-readable-node
/plugin install comfyui-readable-node@comfyui-readable-node
```

自動で更新するには、`/plugin` の Marketplaces で `comfyui-readable-node` を選び、Enable auto-update を選びます。選ばない場合は、`/plugin marketplace update comfyui-readable-node` で更新します。

scripts は Python 3 で動きます（標準ライブラリだけ）。

## 使い方

1. ComfyUI を起動しておきます。skill は、動いている ComfyUI からノードの定義を読みます。
2. エージェントに頼みます。たとえば:
   - 「Readable Node で `my_workflow.json` を読みやすくして。ComfyUI は http://127.0.0.1:8188 で動いています。」
   - 「Readable Node で、Flux の Text to Image の workflow を作って。」
3. 組み直した workflow（`.json`）と、報告が出てきます。workflow を ComfyUI で開いて確かめます。

おまけとして、組み直しを一手ずつたどる `replay.html` も出ます。

## ライセンス

MIT。[LICENSE](LICENSE) と [NOTICE](NOTICE) を見てください。
