# Omada のパラメーターシート

Omada コントローラーと、それが管理する ER605（`rtr01`）・SG2210P（`sw01`）の設定値を、画面のメニューの区分ごとに書いた詳細設計書である。**この文書群を、Omada の設定値の正とする**（[ADR-0040](../../../../adr/0040-config-source-of-truth-by-location.md)）。コントローラーの構成、運用、Open API、変更履歴は、[Omada コントローラーと管理対象機器](../omada-controller.md)にある。

## 文書の一覧

| 文書 | 画面の場所 | 書き出し（実機の値） |
| --- | --- | --- |
| [一般設定](general.md) | サイト > 構成 > ネットワーク設定 > 一般設定 | [`snapshot/general.json`](snapshot/general.json) |
| [ネットワーク](network.md) | 同 > ネットワーク設定（インターネット、LAN、WLAN） | [`snapshot/network.json`](snapshot/network.json) |
| [認証](authentication.md) | 同 > 認証 | [`snapshot/authentication.json`](snapshot/authentication.json) |
| [セキュリティ](security.md) | 同 > セキュリティ（ACL、ファイアウォール、IDS/IPS など） | [`snapshot/security.json`](snapshot/security.json) |
| [送信](transmission.md) | 同 > 送信（ルーティング、NAT、DHCP の予約、QoS など） | [`snapshot/transmission.json`](snapshot/transmission.json) |
| [プロファイル](profiles.md) | 同 > プロファイル（グループ）、デバイス設定 > ポートプロファイル | [`snapshot/profiles.json`](snapshot/profiles.json) |
| [VPN](vpn.md) | 同 > VPN | [`snapshot/vpn.json`](snapshot/vpn.json) |
| [コントローラー](controller.md) | コントローラー全体の設定（グローバル） | [`snapshot/controller.json`](snapshot/controller.json) |
| [ER605（rtr01）](device-rtr01.md) | デバイス > `rtr01` | [`snapshot/device-rtr01.json`](snapshot/device-rtr01.json) |
| [SG2210P（sw01）](device-sw01.md) | デバイス > `sw01` | [`snapshot/device-sw01.json`](snapshot/device-sw01.json) |

機器の一覧（型番、ファームウェア、IP）は [`snapshot/devices.json`](snapshot/devices.json) にある。

## 表の読み方

各文書の表は、「キー」「値」「意味」「理由・備考」の 4 列にする。

- **キー**は、Open API の応答のキー名である。書き出し（`snapshot/`）の同じ名前のキーと突き合わせられる。画面の項目名が分かっているものは、意味の列に添える。画面の表記が分からないものは、仕様書の説明から訳した。
- **値**は、2026-11-28 に Open API で読んだ値である（確認済み）。真偽値は `true`・`false`、数値の選択肢は、数値と意味を両方書く。
- **意味**は、コントローラーの API の仕様書（`/v3/api-docs/00 All`）の説明を訳したものである。仕様書にも説明が無く、意味が分からないものは「未確認」と書く。
- **理由・備考**には、その値にした理由を書く。「既定」は、[変更履歴](../omada-controller.md#変更履歴)に変えた記録が無く、初期値のままと見込む値である。初期値そのものは、仕様書に記載が無いものが多く、確かめていない。

次のキーは、設定ではないので載せない。書き出しには残っている。

- 機器がその機能に対応しているかを表すだけのキー（`support*`、`exist*`、`featureDescription`）。
- サイトやコントローラー、設定そのものの ID（`siteId`、`omadacId`、`id` など）。ほかの設定を指す ID は、名前で書く。
- 書き出しの段階で落とした値（秘密の値、MAC アドレス、シリアル番号、状態、統計、時刻）。

## 更新のしかた

1. 設定を変える前に、変える文書の値を直す（変更の種類によっては同時でよい。[ADR-0033](../../../../adr/0033-docs-first-by-change-type-and-diagram-order.md)）。
2. 画面で設定を変える。
3. `make omada-export` で書き出し直し、`git diff` で、変わった値が意図したものだけかを確かめる。
4. 文書、書き出し、[変更履歴](../omada-controller.md#変更履歴)を同じ変更でコミットする。

文書と書き出しが食い違っていたら、ずれである。どちらに合わせるかを決めて直し、変更履歴に書く。
