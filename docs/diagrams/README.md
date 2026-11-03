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
- 生成は [`stack-diagram/make-homelab.py`](stack-diagram/make-homelab.py)（座標を計算して下書きの HTML を作る）。ロゴ（`<icons-dir>`、Git 管理外）は、スキルの `fetch_icons.py` で取得する。取れなかったもの（Caddy、AdGuard Home、Unbound、CoreDNS、FreshRSS、code-server、Windows、Healthchecks.io、Let's Encrypt、Homepage、Omada、SwitchBot、ESP32、CloudCLI）は、`assets/icons/` にある既存の素材を使った。
- PNG の書き出しには、Playwright と Chromium が要る。

## ファイル

| ファイル | 内容 |
| --- | --- |
| `architecture.drawio.svg` | 現行の構成図 |
| `layout-architecture.py` | 現行の構成図の座標・文字を、規格どおりに組み直すスクリプト |
| `tobe-vlan.drawio.svg` | VLAN 化のあとの構成図 |
| `layout-tobe-vlan.py` | VLAN 化のあとの構成図を作るスクリプト |
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
