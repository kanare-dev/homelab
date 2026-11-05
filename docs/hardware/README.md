# hardware

機器ごとの、仕様・公式資料と、この家での設定値。全体の方式は [architecture/](../architecture/README.md)、サービスの設計は [services/](../services/README.md)、配線の全体像は[物理構成図](../diagrams/physical/physical.png)にある。

## 機器

| 機器 | 役割 | 仕様と資料 | 設定値 |
| --- | --- | --- | --- |
| Lenovo ThinkCentre M70q Tiny | Proxmox ホスト（`pve`）。全 VM が載る | [spec](thinkcentre-m70q-tiny/spec.md) | [settings](thinkcentre-m70q-tiny/settings.md) |
| TP-Link ER605 V2 | ルーター。VLAN ごとのゲートウェイ・DHCP・ACL | [spec](er605/spec.md) | [settings](er605/settings.md) |
| TP-Link SG2210P | PoE+ スイッチ。trunk・access のポート | [spec](sg2210p/spec.md) | [settings](sg2210p/settings.md) |
| Buffalo WSR-1800AX4P | Wi-Fi ルーター。移行後は AP モード | [spec](wsr-1800ax4p/spec.md) | [settings](wsr-1800ax4p/settings.md) |

機器ではないものは、次に置く。

- [10 インチラック](rack-10inch/README.md): 機器を収める 3D プリント用マウント。機器ごとのディレクトリとは別に、そのまま置く。
- Omada コントローラー: `vm-omada` 上のソフトウェアなので、[services/](../services/12-omada-controller.md) に置く。ネットワーク機器（ER605・SG2210P）の設定の入口でもある。

## 置き方の決まり

機器ごとに、ディレクトリ `<型番>/`（小文字、ハイフン区切り）を作り、次のファイルを置く。

| ファイル | 内容 |
| --- | --- |
| `spec.md` | **仕様と公式資料**。公式資料へのリンク（データシートの PDF はリポジトリに入れず、リンクだけ）、仕様、版・ファームウェアの確認結果、使うときの注意。この家での設定値は書かない |
| `settings.md` | **この家での設定値**（詳細設計）。**設定値の正**。ポートの割り当て、IP、モード、変更履歴、未確認の項目 |

- **設定を変えたら、同じ変更で `settings.md` を更新し、変更履歴に 1 行足す**。秘密の値と機器の MAC アドレスは書かない（台帳へ。[シークレット](../operations/runbooks/03-secrets.md)）。コントローラーに採用した機器は、コントローラーの画面から値を書き写す。
- 設定値をまだ持たない機器は、`spec.md` だけを置いてよい。設定を持つようになったら、`settings.md` を足す。
- 機器を足したら、ディレクトリを作り、この表と、[docs/README.md](../README.md)、リポジトリ直下の `README.md` の「リポジトリ構成」を更新する。
- ポートの割り当てや配線を変えたら、`settings.md` と一緒に、[物理構成図](../diagrams/README.md)（生成スクリプトの「配置」）も直す。
