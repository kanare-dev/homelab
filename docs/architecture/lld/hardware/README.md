# hardware

機器ごとの、仕様と公式資料をまとめる。この家での設定値は、役割に合わせて、[network/](../network/) と [platform/](../platform/) の文書に書く。全体の方式は[基本設計](../../hld/README.md)、配線の全体像は[物理構成図](../../../diagrams/physical-diagram/physical-diagram.png)にある。

## 機器

| 機器 | 役割 | 仕様と資料 | 設定値 |
| --- | --- | --- | --- |
| Lenovo ThinkCentre M70q Tiny | Proxmox ホスト（`pve`）。全 VM が載る | [thinkcentre-m70q-tiny](thinkcentre-m70q-tiny.md) | [Proxmox ホスト](../platform/proxmox-host.md) |
| TP-Link ER605 V2 | ルーター。VLAN ごとのゲートウェイ・DHCP・ACL | [er605](er605.md) | [Omada コントローラーと管理対象機器](../network/omada-controller.md#er605ルーター) |
| TP-Link SG2210P | PoE+ スイッチ。trunk・access のポート | [sg2210p](sg2210p.md) | [Omada コントローラーと管理対象機器](../network/omada-controller.md#sg2210pスイッチ) |
| Buffalo WSR-1800AX4P | Wi-Fi ルーター。今は AP モード | [wsr-1800ax4p](wsr-1800ax4p.md) | [Buffalo の設定](../network/wsr-1800ax4p.md) |

機器ではないものは、次に置く。

- [future/](future/rack-10inch/README.md): 導入前の機器・用品。今は 10 インチラック（機器を収める 3D プリント用マウント）だけ。導入して設定を持つようになったら、機器の仕様をこのディレクトリの `<型番>.md` に、設定値を network または platform の文書に置く。
- Omada コントローラー: `vm-omada` 上のソフトウェアである。[network/omada-controller.md](../network/omada-controller.md) に置き、ER605・SG2210P の設定値も同じ文書にまとめている。

## 置き方の決まり

機器ごとに、仕様を `<型番>.md`（小文字、ハイフン区切り）として、このディレクトリに置く。

| 置くもの | 場所 | 内容 |
| --- | --- | --- |
| 仕様と公式資料 | `lld/hardware/<型番>.md` | 公式資料へのリンク（データシートの PDF はリポジトリに入れず、リンクだけ）、仕様、版・ファームウェアの確認結果、使うときの注意。この家での設定値は書かない |
| この家での設定値 | `lld/network/` または `lld/platform/` の文書 | **設定値の正**。ポートの割り当て、IP、モード、変更履歴、未確認の項目。ネットワーク機器は `network/`、ホストは `platform/` に置く。コントローラーで管理する機器は、コントローラーの文書にまとめる |

- **設定を変えたら、同じ変更で、設定値の文書を更新し、変更履歴に 1 行足す**。秘密の値と機器の MAC アドレスは書かない（台帳へ。[シークレット](../../../operations/runbooks/03-secrets.md)）。コントローラーに採用した機器は、コントローラーの画面から値を書き写す。
- 設定値をまだ持たない機器は、仕様（`<型番>.md`）だけを置いてよい。設定を持つようになったら、設定値の文書を足す。
- 機器を足したら、仕様を置き、この表と、[docs/README.md](../../../README.md) の「リポジトリ構成」を更新する。
- ポートの割り当てや配線を変えたら、設定値の文書と一緒に、[物理構成図](../../../diagrams/README.md)（生成スクリプトの「配置」）も直す。
