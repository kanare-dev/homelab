# diagrams

構成図と、その生成・整形スクリプト。図は draw.io の XML を埋め込んだ SVG（`*.drawio.svg`）で、ブラウザや Markdown でそのまま見られ、draw.io で開いて編集もできる。

## 構成図

### 現行の構成（`architecture.drawio.svg`）

Buffalo がルーターの、今の構成。VM とサービス、外部サービス、LAN の端末。最新版の ASCII 図は [システム概要](../architecture/01-overview.md) にある（食い違っていたら、ASCII 図が正）。

![現行の構成図](architecture.drawio.svg)

### VLAN 化のあとの構成（`tobe-vlan.drawio.svg`）

ER605 と SG2210P を入れて VLAN に分けたあと（段階 3 の完了時点）の構成。VLAN ごとのアドレス、スイッチのポートの割り当て、通信ポリシーの要約。内容は [ER605・SG2210P の移行計画](../operations/roadmap/10-er605-sg2210p-migration-plan.md)の「段階 3 の後」と [VLAN 設計](../architecture/08-vlan-design.md)による。

![VLAN 化のあとの構成図](tobe-vlan.drawio.svg)

### stack-diagram で描いた現行の構成（`stack-diagram/`、試作）

[stack-diagram](https://github.com/caru-ini/stack-diagram)（エージェント用のスキル。公式のロゴで構成図を描く）を試した図。内容は現行の構成で、`architecture.drawio.svg` と同じ範囲（外部サービス、Buffalo、Proxmox 上の VM とサービス、LAN の端末）を、日本語で描いた。**正は、これまでの `architecture.drawio.svg` のまま**で、これは比較用の試作。ライト・ダークの PNG と、ロゴと文字を埋め込んだ単体の HTML（ブラウザで開ける）がある。

![stack-diagram で描いた現行の構成図](stack-diagram/homelab.png)

ダーク版は [`homelab-dark.png`](stack-diagram/homelab-dark.png)、HTML は [`homelab.html`](stack-diagram/homelab.html)。

- スキルは、`~/.claude/skills/stack-diagram` に入れた（リポジトリの外。確認した版は、リポジトリ `caru-ini/stack-diagram` の `1ed53e3`）。導入の前に、`SKILL.md` とスクリプトを読んで、危険な呼び出しがないことを確かめた。
- **スキルの「ギャラリーへの公開」（`share.py`）は使わない。** 図に内部の IP アドレスが入っているため。
- 生成は [`stack-diagram/make-homelab.py`](stack-diagram/make-homelab.py)（座標を計算して下書きの HTML を作る）。ロゴ（`<icons-dir>`、Git 管理外）は、スキルの `fetch_icons.py` で取得する。取れなかったもの（Caddy、AdGuard Home、Unbound、CoreDNS、FreshRSS、code-server、Healthchecks.io、Let's Encrypt、Homepage、Omada、SwitchBot、ESP32、CloudCLI）は、`assets/icons/` にある既存の素材を使った。
- PNG の書き出しには、Playwright と Chromium が要る。

### 方眼とフォントを取り入れた VLAN 化のあとの構成（`tobe-html/`、試作）

`tobe-vlan.drawio.svg` と同じ内容・同じ座標を、単体の HTML で描き直した試作。**正は、`tobe-vlan.drawio.svg` のまま**で、これは比較用。draw.io では、書き出す SVG に方眼を入れられず（CLI に指定がない）、フォントも埋め込めないため、HTML にした。

![方眼とフォントを取り入れた VLAN 化のあとの構成図](tobe-html/tobe-vlan.png)

ダーク版は [`tobe-vlan-dark.png`](tobe-html/tobe-vlan-dark.png)、HTML は [`tobe-vlan.html`](tobe-html/tobe-vlan.html)。

- stack-diagram から取り入れたのは、背景の方眼（20px。座標の 10px グリッドに合わせた）、フォント（Geist と JetBrains Mono。日本語は Hiragino / Noto Sans JP）、ライト・ダークの切り替え、線のラベルの縁取り。
- 現行の図から残したのは、VLAN ごとの枠の色、VM・Docker の入れ子、アイコンと文字の行、凡例、IP・ポートの橙色（ここは等幅）。stack-diagram の「白いタイルにロゴ」と「ノードごとの箱」は使っていない（情報の密度を保つため）。
- 生成は [`tobe-html/make-tobe-vlan.py`](tobe-html/make-tobe-vlan.py)。`python3 docs/diagrams/tobe-html/make-tobe-vlan.py --png` で、HTML と PNG（Google Chrome のヘッドレスで書き出す。Playwright は要らない）を作る。フォントは `~/.claude/skills/stack-diagram/assets/fonts` のものを HTML に埋め込む。
- draw.io 版を直したら、こちらも合わせる（座標は同じ構造）。

## ファイル

| ファイル | 内容 |
| --- | --- |
| `architecture.drawio.svg` | 現行の構成図 |
| `layout-architecture.py` | 現行の構成図の座標・文字を、規格どおりに組み直すスクリプト |
| `tobe-vlan.drawio.svg` | VLAN 化のあとの構成図 |
| `layout-tobe-vlan.py` | VLAN 化のあとの構成図を作るスクリプト |
| `tobe-html/` | 方眼とフォントを取り入れた VLAN 化のあとの構成図（試作）。`tobe-vlan.html`、`tobe-vlan.png`、`tobe-vlan-dark.png`、生成スクリプト `make-tobe-vlan.py` |
| `stack-diagram/` | stack-diagram で描いた現行の構成図（試作）。`homelab.html`、`homelab.png`、`homelab-dark.png`、生成スクリプト `make-homelab.py` |
| `assets/` | アイコン素材（**Git 管理外**。無ければ取得する） |

## 更新の手順

構成を変えたら（VM・サービス・IP・機器の追加や削除）、同じ変更で図も更新する。

1. スクリプトの「配置」を直す。
2. 実行する。必要なのは、draw.io のデスクトップ版（`brew install --cask drawio`）。`tobe-vlan` は、macOS の `sips`（アイコンの縮小）も使う。

   ```bash
   python3 docs/diagrams/layout-architecture.py   # 現行
   python3 docs/diagrams/layout-tobe-vlan.py      # VLAN 化のあと
   ```

3. 書き出した PNG（`drawio -x -f png -b 20 -o <出力先>.png <SVG>`）で、崩れていないか目で見る。
4. スクリプトと SVG を、**一緒に**コミットする。
5. 実行で出る `docs/diagrams/__pycache__/` は消す。

## draw.io での手直しがあるとき

図は draw.io で直接手直しされることがある。**確認せずに再生成すると、手直しが消える**（過去に起きた）。

- スクリプトを実行する前に、**現在の SVG と、スクリプトが出す内容を、セルごとに比べる**（位置、大きさ、文字、スタイル）。スクリプトが `KeyError` で止まったら、手直しでセルの ID が変わった印。
- 手直しは、**先にスクリプトへ取り込んで**から再生成する。取り込んだあとは、再生成した SVG と手直しの SVG が、見た目も意味も同じになることを確認する。
- 手直しは、運用者が直接コミットすることもある。`git log` で、スクリプトを通っていない図のコミットを確かめる。
