# ロゴ

kanare’s homelab のロゴ（SVG）。`make-logo.py` で作る。マークは静止で、点滅するのは、横長のロゴの、文字の横のカーソルだけ。

## 種類と使い分け

| ファイル | 用途 |
| --- | --- |
| `logo-stack-{light,dark}.svg` | **主役。** 横長。3 枚の機器（ルーター、スイッチ、ミニ PC）を積み、屋根を載せた「家」+ `kanare’s homelab` + `10.77.0.0/16 · lab.kanare.dev`。README の見出し、Homepage |
| `seal-{light,dark}.svg` | 円形のエンブレム。縁に名前・アドレス・ドメイン、中央に積み重ね。ポートフォリオ、ステッカー、README の末尾 |
| `logo-graph-{light,dark}.svg` | サブ。横長。家の形のネットワーク図（頂点がノード、中央がハブ）+ 文字 |
| `icon-stack.svg`、`icon-graph.svg` | 正方形のアイコン（暗い地 + 縁取り。どの背景でも使える）。favicon、Homepage のタイル |
| `gallery.html` | 上の一覧（ライトとダークの背景に並べる）。ブラウザで開いて見る。`make-logo.py` が作る |
| `social-preview.png`（元: `social-preview.html`） | GitHub のソーシャルプレビュー（リンクを貼ったときに出る画像。1280 × 640、ダークの地にダーク版のロゴ） |

`light` は明るい背景用（濃い文字）、`dark` は暗い背景用（明るい文字）。背景は透明。

## 使い方

### GitHub の README（ライトとダークの切り替え）

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/logo/logo-stack-dark.svg">
  <img alt="kanare’s homelab" src="docs/assets/logo/logo-stack-light.svg" width="480">
</picture>
```

カーソルの点滅は、`<img>` で読み込んだ SVG の CSS アニメーション。GitHub で動くかは、**未確認**（動かなくても、カーソルが見えたままになるだけで、読める）。

### ポートフォリオなど、ページに直接埋め込む

SVG の中身をそのまま HTML に入れてよい。色の指定は、SVG ごとのクラス（`hl-logo-stack-light` など）に閉じているので、ライトとダークの両方を、同じページに入れても、色は混ざらない。

### Homepage

画像の URL で表示できる見込み（Homepage の `logo` ウィジェットなど）。**未確認**。

## 色を変える

色は `make-logo.py` の `THEMES`（`light` と `dark`）の 1 か所で決める。アクセント色は `accent`（名前、カーソル、LED、エンブレムの点）、屋根は `froof` と `fgable`。機器の面は `ftop`（上）、`fleft`（左）、`fright`（右）。**面の濃淡は、透明度でなく、不透明の色**で決めている（暗い背景で透けて見えないため）。

## 作り直す

文字は、フォントの輪郭（パス）に変換して入れる（`<img>` の SVG は、フォントを読み込めないため）。

1. fontTools を入れる: `python3 -m venv ~/.cache/homelab-logo-venv && ~/.cache/homelab-logo-venv/bin/pip install fonttools`
2. JetBrains Mono（Medium と Bold）をインストールしておく（Nerd Font 版でも、文字の形は同じ）。探す場所は、`make-logo.py` の `FONT_DIRS`。
3. `~/.cache/homelab-logo-venv/bin/python docs/assets/logo/make-logo.py`

SVG と `gallery.html` が、同じフォルダに書き出される。

## ソーシャルプレビュー

`make-logo.py` が `social-preview.html` を作る。PNG にするには、ブラウザで 1280 × 640 で撮る。

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
  --window-size=1280,640 --screenshot="$PWD/docs/assets/logo/social-preview.png" \
  "file://$PWD/docs/assets/logo/social-preview.html"
```

GitHub への登録は、**手で行う**（API では設定できない）: リポジトリの Settings → General → Social preview → Edit → Upload an image で、`social-preview.png` を選ぶ。

## ライセンス

- **ロゴ（SVG、PNG、`gallery.html`、`social-preview.*`）は、リポジトリの MIT の対象外。** すべての権利は、作者にある。自分のものとして使わないこと。生成スクリプト `make-logo.py` は、MIT。
- 文字の輪郭は、[JetBrains Mono](https://github.com/JetBrains/JetBrainsMono)（SIL Open Font License 1.1）から作っている。

## 作った経緯

最初は、文字だけのロゴ（ターミナルのプロンプト風）を作った。「ロゴというより、ただの文字」「VLAN の色の並びは、VLAN と分からず、色も変わるかもしれない」という意見で、VLAN の色を使わず、色は、アクセント 1 色 + 白黒にした。マークは、図形を主役にして、「家 + カーソル」「k のネットワーク」「サブネットの分割」「家のネットワーク図」「機器の積み重ね + 屋根」「円形のエンブレム」を比べ、積み重ね（サーバー + 家 = homelab）を主役にした。
