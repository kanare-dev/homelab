# ER605（rtr01。Omada のパラメーターシート）

画面の場所は、デバイス > `rtr01` である。実機の値は [`snapshot/device-rtr01.json`](snapshot/device-rtr01.json) にある。表の読み方は [README](README.md#表の読み方) にある。製品の仕様とファームウェアは [ER605 の資料](../../hardware/er605.md)にある。

家のルーターである。NAT と、各 VLAN のゲートウェイ・DHCP・ACL を受け持つ。集合住宅の共用ルーターの下に置く（二重 NAT）。既定のネットワークは Management（VLAN10、`10.77.10.0/24`）で、VLAN1 は使わない（[ADR-0032](../../../../adr/0032-merge-default-network-into-management-vlan10.md)）。設定はコントローラーから行い、本体の画面は使えない。WAN、LAN、DHCP、VLAN の値は[ネットワーク](network.md)、ACL は[セキュリティ](security.md)にある。

## ポート

| ポート | 名前（`name`） | 種類 | 接続先 | 備考 |
| --- | --- | --- | --- | --- |
| p1 | WAN1 | WAN 専用 | 壁の LAN ポート（ケーブル A） | 2026-11-06 に接続。MAC クローンなしで IP を取れた |
| p2 | WAN/LAN2 | WAN/LAN の切り替え | SG2210P の p1 | LAN として使う（最初から LAN。2026-11-06 に確認） |
| p3 | WAN/LAN3 | WAN/LAN の切り替え | 使わない | 段階 1・2 の確認のとき、Mac を一時的に繋いだ |
| p4〜p5 | LAN4、LAN5 | LAN 専用 | 使わない | |
| （6） | USB Modem | USB | 使わない | |

- ポートの種類は、運用者が本体で確認した（2026-11-06）。API の `type`（p1 が `0`、p2・p3 が `1`、p4・p5 が `2`、USB が `4`）と `mode`（p1 が `0`、p2〜p5 が `1`、USB が `-1`）は、この種類と使い方に合っている。値の意味は、仕様書に記載が無い（未確認）。
- LAN 側のポート p2〜p5 は、すべての VLAN のネットワークに入っている（[ネットワーク](network.md#lan)の `interfaceIds`）。

## 機器の設定（general-config）

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `name` | `rtr01` | 機器の名前 | 役割と番号（[ADR-0035](../../../../adr/0035-network-device-names-by-role.md)。2026-11-27 に `er605` から変えた） |
| `ledSetting` | `2` | LED。0 は消灯、1 は点灯、2 はサイトの設定に従う | 既定 |
| `rememberDevice` | `2` | 未確認（仕様書に記載が無い） | 既定 |
| `snmp.contact` / `snmp.location` | 空 | SNMP の連絡先・場所 | SNMP は使わない |

## 機器の情報と、書き出しに無い設定

| 項目 | 値 |
| --- | --- |
| 型番 | ER605 v2.30 |
| ファームウェア | JP 版 2.4.2 Build 20260511 Rel.77362（2026-11-03 に更新。2026-11-06 の採用のあとも、同じ版） |
| 管理者アカウント | サイトのデバイスアカウント（[一般設定](general.md#デバイスアカウント)）。パスワードは Keychain（台帳） |
| ローカル DNS（Domain Name、Alias Domain Name） | 登録しない（名前解決は `vm-infra` の CoreDNS） |
| UPnP | 無効（[ネットワーク](network.md#そのほかのサービス)。2026-11-27 に画面でも確認。デバイス > `rtr01` > 設定 > アドバンス > UPnP） |
| クラウド管理（Cloud-Based Controller Management） | 初期化すると、既定で「有効」になり Online になる（2026-11-20 に確認）。使わないなら無効にする。今の値は未確認 |
