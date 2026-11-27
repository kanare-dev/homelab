# Omada コントローラーと管理対象機器（ER605・SG2210P）

Omada コントローラー（`vm-omada`）と、それが管理する ER605・SG2210P の詳細設計。将来は AP も、ここで一元管理する。設定の大半はコントローラーの中にあり、コードでは管理できない（[ADR-0040](../../../adr/0040-config-source-of-truth-by-location.md)）。この文書には、構成、運用、Open API、変更履歴を書く。**設定値の正は、画面の区分ごとの[パラメーターシート](#パラメーターシート)（`omada/`）とする。** 実機の設定値は、Open API で取り出して [`omada/snapshot/`](omada/snapshot/) に置いており、パラメーターシートとのずれを確かめるのに使う（[ADR-0041](../../../adr/0041-omada-settings-exported-by-open-api.md)。[下の節](#open-api-と設定値の書き出し)）。 製品の仕様は[ER605](../hardware/er605.md)・[SG2210P](../hardware/sg2210p.md)の資料、VLAN の設計は[第5章 ネットワーク](../../hld/05-network.md)、移行の経緯は[移行計画](../../../operations/roadmap/10-er605-sg2210p-migration-plan.md)にある。

> [!NOTE]
> 作成日は 2026-11-03。**秘密の値（管理者のパスワード、バックアップの暗号化の鍵、TP-Link ID のパスワード）と、機器の MAC アドレスは書かない**（リポジトリは公開）。Keychain の名前は `private/secrets-inventory.md`（台帳）にある。

## 運用

- コントローラーまたは機器（ER605・SG2210P）の設定を変えたら、**同じ変更で[パラメーターシート](#パラメーターシート)を更新**し、この文書の[変更履歴](#変更履歴)に 1 行足す。手順は [`omada/README.md`](omada/README.md#更新のしかた) にある。
- 設定を変えたあとは、`make omada-export` で実機の値を取り出し、`git diff` で、変わった値が意図したものだけかを確かめる。書き出した値（`omada/snapshot/`）も、同じ変更でコミットする。
- 設定を変えたあとは、手動バックアップを取る。画面の Settings > Maintenance の「Backup & Restore」で保存する（メニューの名前は 6.3 で未確認）。保存先は iCloud Drive の `homelab/`（暗号化なし。運用者が受け入れ。[バックログ](../../../operations/roadmap/01-backlog.md)）。ファイル名は `omada-bk-YYYYMMDD.cfg`（案）。直近の 3 世代ほどを残す。
- 自動バックアップは、毎週日曜 03:00（`vm-omada` の `/opt/omada/data/autobackup`）。VM のディスクの中なので、VM が壊れると一緒に失われる。
- 画面には、`https://omada.lab.kanare.dev`（Caddy が `10.77.10.3:8043` に転送する）で入る。Caddy が使えないときは、`ssh -L 8043:localhost:8043 vm-omada` のあと `https://localhost:8043` で入る。

## 構成

| 項目 | 値 |
| --- | --- |
| VM | `vm-omada`（VMID 112、`10.77.10.3`、VLAN10、NIC 1 枚）。2 vCPU、メモリ 4GB（2026-11-09 に 3GB から増やした）、ディスク 20G。起動は自動（順序 6） |
| コントローラー | Omada Controller 6.3.0.111。Docker（`mbentley/omada-controller:6.3.0.111`、host ネットワーク）。`docker/compose/omada/docker-compose.yml`、Ansible の `omada.yml` |
| メモリの上限 | Java ヒープ最大 768MB（`JAVA_MAX_HEAP_SIZE`）、MongoDB の WiredTiger キャッシュ 0.25GB（`MONGOD_EXTRA_ARGS`）、コンテナ全体で 2.5GB（`mem_limit`）。VM にスワップは無い。上限の根拠は [INC-2026-11-09](../../../operations/incidents/2026-11-09-omada-memory-exhaustion.md) |
| データ | `/opt/omada/data`、ログ `/opt/omada/logs` |
| 反映 | `make setup-omada` |
| ポート | 管理 HTTPS 8043、管理 HTTP 8088、ポータル 8843。機器との通信は UDP 29810（自動検出）、TCP 29811〜29816。UFW で絞る（`ansible/inventory/group_vars/omada/vars.yml`） |
| 監視 | `node_exporter` を Prometheus が見ている（`TargetDown`）。画面（HTTPS）は、`https://omada.lab.kanare.dev` を blackbox で外形監視している（2026-11-06 から）。管理する機器・ポート・クライアントの状態は、`vm-monitoring` の omada-exporter が API を読み、Grafana で見る（[ADR-0039](../../../adr/0039-omada-metrics-via-omada-exporter.md)、[監視・アラート](../platform/monitoring.md#omada-の機器クライアントの状態)） |

## Open API と設定値の書き出し

コントローラーの Open API で、設定値を読み取りだけで取り出す（[ADR-0041](../../../adr/0041-omada-settings-exported-by-open-api.md)）。

| 項目 | 値 |
| --- | --- |
| スクリプト | `tools/omada-export.py`（`make omada-export`）。Mac で動かす。GET だけを呼ぶ |
| 書き出し先 | [`omada/snapshot/`](omada/snapshot/)。画面のメニューの区分ごとに 1 ファイル（`general`、`network`、`authentication`、`security`、`transmission`、`profiles`、`vpn`、`controller`）と、機器ごとのファイル（`device-rtr01`、`device-sw01`）、機器の一覧（`devices`） |
| 認証 | omada-exporter 用の Open API のアプリ `exporter`（Client Credentials、Viewer）。Client ID とシークレットは SOPS（`group_vars/monitoring` の `omada_exporter_client_id`、`omada_exporter_client_secret`）にあり、スクリプトが `sops -d` で読む。値は画面にもファイルにも出さない |
| 落とす値 | 秘密の値（パスワード、鍵など）、シリアル番号、実行のたびに変わる値（状態、統計、時刻）。機器の MAC アドレスは機器の名前（`rtr01`、`sw01`）に、機器でない MAC は `<mac>` に置き換える。ACL などがほかの設定を ID で指すところには、`<ID> (<名前>)` の形で名前を添える |
| 仕様書 | コントローラーの `/v3/api-docs/00 All`（認証なしで取れる。窓口は約 1900） |
| 読めない窓口 | バックアップのスケジュール（Viewer では権限が足りない）。mDNS は、呼び方を確かめていないので、まだ取り出していない |

### Viewer の権限で機器のパスワードが読める（危険）

Open API の Viewer の権限でも、サイトのデバイスアカウント（ER605・SG2210P に共通の管理者。サイト設定 > デバイスアカウント）のパスワードが、伏せ字にされずに平文で返る（`/sites/{siteId}/device-account`。2026-11-28 に確認）。Viewer は「見るだけ」の権限だが、機器の管理者のパスワードまで読めることになる。

このクライアントの認証情報は、`vm-monitoring` の `/opt/monitoring/omada-exporter/secrets.env`（root だけが読める）と、SOPS にある。`vm-monitoring` が乗っ取られると、認証情報が漏れ、そこから機器の管理者のパスワードも漏れる。

今の守りは、次のとおりである。

- ゲートウェイの ACL で、Servers（`vm-monitoring` を含む）から Management の機器（ER605・SG2210P）の SSH と画面への通信を止めている。`vm-monitoring` から Management に届くのは、Proxmox と `vm-omada` の 9100 番だけである（[ゲートウェイ ACL](omada/security.md#ゲートウェイ-acl)）。パスワードが漏れても、Servers からは機器に入れない。
- 機器は、コントローラーに採用されているあいだ、本体の画面では設定を変えられない。
- `tools/omada-export.py` は、パスワードを書き出す前に落とす。

残る危険は、パスワードが漏れたあと、Trusted や Management の端末から機器に入られることである。対策の案（未決定）は、機器のパスワードを定期的に変えること、Open API のクライアントの権限を、ほかの絞り方（サイト単位の権限など）で狭められないか確かめることである。

## パラメーターシート

コントローラーと機器の設定値は、画面のメニューの区分ごとに、[`omada/`](omada/README.md) の文書に書いている。**この文書群を、設定値の正とする。** 実機の値は、Open API で取り出して [`omada/snapshot/`](omada/snapshot/) に置き、文書とのずれを確かめるのに使う。

| 文書 | 内容 |
| --- | --- |
| [一般設定](omada/general.md) | サイト名、NTP、デバイスアカウント、SSH、SNMP、リモートログ、mDNS の中継 |
| [ネットワーク](omada/network.md) | WAN、LAN（VLAN ごとのネットワークと DHCP）、WLAN、UPnP などのサービス |
| [認証](omada/authentication.md) | ポータル、802.1X、MAC ベース認証（使わない） |
| [セキュリティ](omada/security.md) | ゲートウェイ ACL、ファイアウォール、攻撃の防御 |
| [送信](omada/transmission.md) | ルーティング、NAT、DHCP の予約、QoS（ほとんど使わない） |
| [プロファイル](omada/profiles.md) | ACL のグループ、スイッチのポートプロファイル |
| [VPN](omada/vpn.md) | 使わない（Tailscale を使う） |
| [コントローラー](omada/controller.md) | アカウント、Open API のアプリ、データの保持、機器へのアクセス |
| [ER605（rtr01）](omada/device-rtr01.md) | ポート、機器の設定 |
| [SG2210P（sw01）](omada/device-sw01.md) | ポートと VLAN、管理 IP、機器の設定 |

## ER605（ルーター）

TP-Link ER605 V2（`rtr01`、`10.77.10.1`）。家のルーターで、NAT と、各 VLAN のゲートウェイ・DHCP・ACL を受け持つ。集合住宅の共用ルーターの下に置く（二重 NAT）。製品の仕様は [ER605 の資料](../hardware/er605.md)、設定値は [ER605（rtr01）](omada/device-rtr01.md)、[ネットワーク](omada/network.md)、[セキュリティ](omada/security.md)にある。

## SG2210P（スイッチ）

TP-Link SG2210P V5.30（`sw01`、`10.77.10.2`）。有線のハブを兼ねる PoE+ スイッチで、ER605 の p2 に繋ぎ、Proxmox（p2）、Buffalo（p3）、ディスプレイ（p4）を収める。p8 は復旧ポートである。製品の仕様は [SG2210P の資料](../hardware/sg2210p.md)、設定値は [SG2210P（sw01）](omada/device-sw01.md)にある。

## 見直したい項目・未確認

- 自動バックアップの保存先を、`vm-omada` の外にも広げるか（[バックログ](../../../operations/roadmap/01-backlog.md)）。
- Omada Cloud を使い続けるか。
- 設定のコード化（Open API、コミュニティ製の Terraform プロバイダー）。
- 機器のファームウェアの自動更新が、無効になっているかを確認する（有効なら、無効にするか決める）。
- ER605 の LAN、DHCP、NTP、ファイアウォールの値は、2026-11-28 に Open API で確かめて、パラメーターシートに書いた。
- ER605: 管理者アカウント（コントローラーが機器に入るためのアカウント）が、初期値のままではないこと。
- SG2210P: IGMP スヌーピング、STP の細かい設定、ストームコントロールは、まだ書き出していない（API の窓口を確かめる）。
- ずれ（2026-11-28 に発見。どちらに合わせるか未決定）: LAN の Blackhole が ER605 のポートに割り当たっている（[ネットワーク](omada/network.md#lan)）。ポートプロファイル `Default` が `Management` になっている（[プロファイル](omada/profiles.md#ポートプロファイル)）。
- SG2210P の SFP ポート（p9・p10）がタグ全許可のまま（[SG2210P](omada/device-sw01.md#ポート)）。
- SG2210P: 新しいファームウェアが出たか（サポートページの V5.30 の一覧で確認する。更新するときは、手順の確認が通ってから別の機会に行い、地域は、コントローラーが表示する今の版に合わせる）。

- ER605 で確認済み（2026-11-06）: p2 は最初から LAN として動いた。上流は MAC で絞っていない（MAC クローンなしで IP を取れた）。
- SG2210P で確認済み（2026-11-06）: 標準の設定のまま、スイッチとして動いた（段階 1・2 の配線の確認が通った）。

## 変更履歴

| 日付 | 内容 |
| --- | --- |
| 2026-11-28 | [文書] 設定値を、画面の区分ごとのパラメーターシート（`omada/`）に移した。値は Open API の書き出しで確かめた。`omada-export.py` に、スイッチのポート、ポートプロファイル、VLAN ごとのポートを足した。**ずれを 2 つ見つけた**（LAN の Blackhole が ER605 のポートに割り当たっている、ポートプロファイル `Default` が `Management` になっている） |
| 2026-11-28 | [文書] Open API で設定値を取り出す `tools/omada-export.py` を作り、`omada/snapshot/` に書き出した（[ADR-0041](../../../adr/0041-omada-settings-exported-by-open-api.md)）。Viewer の権限でデバイスアカウントのパスワードが平文で読めることを、危険として記録した |
| 2026-11-27 | [ER605] **ゲートウェイ ACL を絞った**（[手順書 27](../../../operations/runbooks/27-network-acl-tighten.md)）。グループ 12 件と許可のルール 14 件を作り、末尾の拒否 7 件を DMZ・Guests・IoT、Lab、Servers、Trusted、Management の順に 1 件ずつ足した。リハーサルの `rh-` の 7 件は削除した。**予測が外れた点:** IP-Port グループはポートを全サブネットにかけ、範囲も書けないので、`grp-mgmt-caddy` と `grp-mgmt-admin` を 2 つずつに分けた（10 件 → 12 件。許可の範囲は同じ）。`!ネットワーク` は、WAN 側の `172.22.0.1` 宛を止めなかった |
| 2026-11-27 | [コントローラー] 監視用に、ユーザー `exporter`（Viewer）と、Open API のアプリ `exporter`（Client Credentials、Viewer）を作った（運用者の作業。[ADR-0039](../../../adr/0039-omada-metrics-via-omada-exporter.md)） |
| 2026-11-27 | [確認] ER605（`rtr01`）の UPnP が無効であることを、コントローラーの画面で確かめた（運用者の報告。画面の写し） |
| 2026-11-27 | [コントローラー] デバイス名を `er605` → `rtr01`、`sg2210p` → `sw01` に変えた（運用者の報告。[ADR-0035](../../../adr/0035-network-device-names-by-role.md)） |
| 2026-11-27 | [文書] デバイス名を、役割と番号（`rtr01`、`sw01`）に変えると決めた（[ADR-0035](../../../adr/0035-network-device-names-by-role.md)）。文書が先で、実機（Omada の画面）は未変更 |
| 2026-11-20 | [コントローラー] **既定のネットワークを Management（VLAN10）に統合した（案 B）。** ER605 を「削除」（初期化）→ 停止中に、`Blackhole`（VLAN 999）作成、`Management` ネットワークの削除、`Default` を `Management(Default)`（VLAN10、`10.77.10.1/24`、DHCP `.240`〜`.250`）に変更 → ER605 を再採用した（Inform URL `10.77.10.3`）。ER605 の接続元 IP は `10.77.10.1`。`vm-omada` の UFW から `10.77.1.1` の許可を消した（Ansible）。**つまずき:** `Management` は、スイッチの管理 VLAN とポート（p8）のネイティブに紐づいていて、先に外さないと消せなかった。消した時点で、スイッチから VLAN10 が消え、コントローラーから切れた。詳細は[手順書 25](../../../operations/runbooks/25-merge-default-network-into-vlan10.md) |
| 2026-11-20 | [ER605] **既定のネットワークを Management（VLAN10）に統合した（案 B、[ADR-0032](../../../adr/0032-merge-default-network-into-management-vlan10.md)、[手順書 25](../../../operations/runbooks/25-merge-default-network-into-vlan10.md)）。** ER605 をコントローラーで「削除」（初期化）→ 停止中に、`Blackhole` の作成、SG2210P のポート変更、「Management」の削除、既定のネットワークを `Management(Default)`（VLAN10、`10.77.10.1/24`、DHCP `.240`〜`.250`、リース 60 分）に変更 → ER605 を、スタンドアロンで LAN を `10.77.10.1/24`（VLAN は 1 のまま。スイッチ p1 の PVID が 10）にして、Inform URL `10.77.10.3` で再採用。コントローラーの接続元 IP は `10.77.10.1`。全面停止は、約 1 時間（22:30 ごろ〜23:15 ごろ）。管理者のアカウントは、また作り直した（台帳へ）。ER605 は、既定でクラウド管理（Cloud-Based Controller Management）が「有効」で Online になるので、使わないなら無効にする |
| 2026-11-20 | [SG2210P] **既定のネットワークの VLAN10 への統合（案 B、[ADR-0032](../../../adr/0032-merge-default-network-into-management-vlan10.md)、[手順書 25](../../../operations/runbooks/25-merge-default-network-into-vlan10.md)）。** (1) `Blackhole`（VLAN 999）を作り、p1 のタグから `Blackhole` を外した。(2) p8 を native Management に、p2 を native `Blackhole` に、p5〜p7 を native `Blackhole`・タグ全ブロックにした。(3) 管理 VLAN を `Default`（VLAN1）に付け替え、`Management` ネットワークを削除し、`Default` を `Management`（VLAN10、`10.77.10.1/24`）にした。**削除の時点で、スイッチから VLAN10 が消え、コントローラー（VLAN10）から切れた**（想定どおり）。(4) 復旧は、本体の画面（ER605 の DHCP から受けた `192.168.0.100`）で、802.1Q VLAN に VLAN10（tagged p1・p2・p8）を足して、L3 Interface に VLAN10 の静的 `10.77.10.2` を足した。(5) **コントローラーの p2 の設定が、タグ付きに Management を含めていなかったため、p2 の VLAN10 が untagged になっていた**（配信のあと、本体の画面で気づいた）。タグ付きに Management を足して直した。(6) コントローラー側の管理インターフェースを、静的 `10.77.10.2/24`（GW・DNS `10.77.10.1`）にした。再接続のあと、設定結果の「失敗」の通知は、切断中の古い記録だった |
| 2026-11-19 | [コントローラー] 夜（最後）: 既定のネットワークの IP を、`192.168.11.1/24` から `10.77.1.1/24`（DHCP `.60`〜`.99`）に付け替えた。ER605 の送信元が `10.77.1.1` になるので、先に UFW に許可を足した（旧 `192.168.11.1` は、後で外した）。ER605 は、約 2 分（接続エラーの状態を経て）で再接続した。LAN の画面の適用の表示は、約 5 分「適用中」のままだった（応答のタイムアウト）。インターネットと各 VLAN は、確認できた範囲で、通じていた |
| 2026-11-19 | [コントローラー] 夜（2 回目。最終形）: ER605 を、もう一度、初期化して再採用した。今度は、LAN を `192.168.11.1/24` にせず、VLAN10 のネットワーク（`10.77.10.1/24`）と Inform URL（`10.77.10.3`）だけで、**`10.77.10.3` から導入した**。`vm-omada` の旧 NIC（`192.168.11.12`）を外し、NIC 1 枚（`10.77.10.3`、VLAN10）にした（Terraform。`apply` 22:19、VM が再起動）。Caddy（`omada.lab.kanare.dev` の転送先）と Prometheus を `10.77.10.3` に付け替えた。UFW は、機器向けのポートを、`10.77.10.0/24` と ER605（`192.168.11.1`）だけに許可。22:21 に ER605・SG2210P が `10.77.10.3` に再接続した。「デバイス管理アクセス」は `10.77.10.3` のまま（運用者の報告）。詳細は[ロードマップ 13](../../../operations/roadmap/13-defer-management-vlan.md) |
| 2026-11-19 | [コントローラー] 夜（1 回目）: ER605 を、コントローラーで「削除」して初期化し、再採用した（初期化から約 20 分で、全 VLAN・インターネットが戻った）。導入は、旧住所（`192.168.11.12`）で行われ、ER605 は新しい住所（`10.77.10.3`）に付いてこなかった。事前に Omada のバックアップを取った（`omada_backup_...2026-11-19_21-03-45.cfg`、`sitebackup_...21-03-57.cfg`。iCloud Drive。運用者の報告）。詳細は[ロードマップ 13](../../../operations/roadmap/13-defer-management-vlan.md) |
| 2026-11-19 | [コントローラー] 段階 3b の手順 1〜3（[手順書 23](../../../operations/runbooks/23-network-stage-3b-management-vlan10.md)）: SG2210P を VLAN10（`10.77.10.2`）に移した。「デバイス管理アクセス」のホスト名/IP を `10.77.10.3` にして、コンテナを再起動した。**SG2210P は `10.77.10.3` に付いてきた。ER605 は付いてこなかった**（旧住所を塞いだ約 8 分の間、コントローラー向けのパケットを送らず、塞ぎを外すと約 14 秒で旧住所 `192.168.11.12` に戻った）。「デバイス管理アクセス」は、`10.77.10.3` のまま。`vm-omada` は 2 枚の NIC（`192.168.11.12` と `10.77.10.3`）のまま（旧 NIC は外せない）。事前に Omada のバックアップを取った（運用者の報告）。詳細は[ロードマップ 13](../../../operations/roadmap/13-defer-management-vlan.md) |
| 2026-11-19 | [ER605] **既定の LAN を `192.168.11.0/24` から `10.77.1.0/24` に付け替えた**（Omada の「ネットワーク設定 → LAN → Default」で、IP `10.77.1.1/24`、DHCP `.60`〜`.99`、リース 120 分）。ER605 は、`10.77.1.1` から、`10.77.10.3` に再接続した（接続中の通信が、約 2 分で張り直された。画面の適用の表示は、応答のタイムアウトで約 5 分、「適用中」のまま残った）。事前に、`vm-omada` の UFW に `10.77.1.1` の許可を足した。ER605 の管理画面のアドレスは `10.77.1.1` |
| 2026-11-19 | [ER605] **2 回目の初期化と再採用（最終形）**（21:41〜22:27）: LAN は `192.168.0.1/24` のまま、スタンドアロンで VLAN10 のネットワーク（`10.77.10.1/24`）を足し、Inform URL を `10.77.10.3` にして、`10.77.10.3` から導入した。導入のあと、サイトの設定で既定の LAN が `192.168.11.1/24` になり、全 VLAN が戻った（停止は約 25 分）。ER605 は、コントローラーの `10.77.10.3` に、`192.168.11.1` を送信元にして接続している。管理者のアカウントは、また作り直した（台帳へ）。詳細は[ロードマップ 13](../../../operations/roadmap/13-defer-management-vlan.md) |
| 2026-11-19 | [ER605] **初期化して、再採用した（1 回目）**（段階 3b。コントローラーで「削除」→ 初期化 → スタンドアロンの初期設定（WAN は DHCP で `172.22.1.63`、MAC クローン不要）→ LAN を `192.168.11.1/24`（DHCP `.60`〜`.99`）にして → VLAN10 のネットワークを足して → 導入）。導入のあと、サイトの設定（VLAN のネットワーク、ゲートウェイ）が自動で配られ、約 20 分の全面停止（21:09〜21:29）のあとに、全 VLAN・インターネットが戻った。管理者のアカウントは、初期設定で作り直した（台帳へ）。ファームウェアは 2.4.2（Build 20260511）のまま。ER605 は、旧住所（`192.168.11.12`）でコントローラーに接続している（`10.77.10.3` に付いてこない）。DHCP の範囲・リース・DNS の値は、導入のあとに、画面で確認していない。詳細は[ロードマップ 13](../../../operations/roadmap/13-defer-management-vlan.md) |
| 2026-11-19 | [SG2210P] 緊急用の入口を、p6 から p8 に変える方針にした（設定は変えていない。p5〜p8 は同じ設定。空きの PoE ポート p5〜p7 を連続させるため。ADR-0032、手順書 25） |
| 2026-11-19 | [SG2210P] 段階 3b の手順 1: 「デバイス → sg2210p → 設定 → インターフェース」の Management（VLAN10）で、管理 VLAN を有効にし、IP を静的（`10.77.10.2/24`、GW・プライマリ DNS `10.77.10.1`）にした。保存のポップアップの「以前の管理 VLAN のインターフェースを無効にする」は、チェックを入れなかった。約 1 分で再接続した。手順 2 で、コントローラーの住所（デバイス管理アクセス）を `10.77.10.3` にして、SG2210P が `10.77.10.3` 宛てに接続することを確認した。事前に Omada のバックアップを取った（運用者の報告）。詳細は[ロードマップ 13](../../../operations/roadmap/13-defer-management-vlan.md) |
| 2026-11-18 | [コントローラー] 段階 3b の確認として、「デバイス管理アクセス」のホスト名/IP を、`10.77.10.3`（`vm-omada` に足した VLAN10 の NIC）に、2 回（合計 約 1 時間）して、`192.168.11.12` に戻した。機器には新しい住所が伝わったが、接続は完了せず、旧住所で復帰した。事前に Omada のバックアップを取った（運用者の報告）。詳細は[ロードマップ 13](../../../operations/roadmap/13-defer-management-vlan.md) |
| 2026-11-17 | [コントローラー] 全体の設定（システム設定）の「デバイス管理アクセス」を有効にし、デバイス管理ホスト名/IP を `192.168.11.12`（今の `vm-omada` の住所）にした。段階 3b で、機器がコントローラーの新しい住所に付いてくるかを確かめるための、低リスクの確認（機器に伝わる住所は変わらない）。10 分間の監視で、切断は無く、ER605・SG2210P は接続済みのまま（運用者の画面と、Claude の疎通確認）。保存の確認（再読み込み）は未了。これで、デバイスの追加の「手動で追加」も使える状態になる。詳細は[ロードマップ 13](../../../operations/roadmap/13-defer-management-vlan.md) |
| 2026-11-17 | [コントローラー] 既定の LAN（`192.168.11.0/24`）の DHCP の DNS を、`192.168.11.11`（旧 `vm-infra`）から、ルーター（`192.168.11.1`）に変えた。変更後に確認した（運用者の報告） |
| 2026-11-17 | [コントローラー] 段階 3 の手順 5・6 のあと、Omada のバックアップを取り直した（`omada_backup_...2026-11-17_22-01-59.cfg`、`sitebackup_...2026-11-17_22-01-49.cfg`。iCloud Drive）。p3・p4 の `access-trusted` の割り当てが入った状態（運用者の報告） |
| 2026-11-17 | [コントローラー] 段階 3 の当日の手順 2 で、SG2210P の p3・p4 にポートプロファイル `access-trusted` を割り当てた（詳細は[SG2210P](#sg2210pスイッチ)の変更履歴）。事前に、Omada のバックアップを取り直した（`omada_backup_...2026-11-17_20-55-01.cfg`、`sitebackup_...2026-11-17_20-55-17.cfg`。iCloud Drive）。バックアップは、p3・p4 を割り当てる前の状態 |
| 2026-11-17 | [ER605] 今の LAN（`192.168.11.0/24`）の DHCP が配る DNS を、`192.168.11.11`（旧 `vm-infra`）から、ルーター（`192.168.11.1`）に変えた。段階 3 で `vm-infra` が `10.77.20.10`（Servers）に移り、旧アドレスが使えなくなったため。変更後に確認した（運用者の報告） |
| 2026-11-17 | [SG2210P] p5〜p8 の設定を、Omada の画面で確認した（設定は変えていない。すべて同じ。上のポートの表の注）。p6（緊急用の入口）は、native VLAN1 のままで、計画どおり（運用者の確認） |
| 2026-11-17 | [SG2210P] 段階 3 の当日の手順 2 で、p4（ディスプレイ）と p3（Buffalo）にプロファイル `access-trusted` を割り当てた（access VLAN30）。**「VLAN設定」が「カスタム」のままだと、プロファイルを選んでも Native が Default(1) のままで VLAN30 にならない**ので、「プロファイルに従う」にした。割り当て後、Mac の有線・Wi-Fi が `10.77.30.x` を受け取り、ER605 経由で今の LAN（Proxmox、`vm-omada`）に届くことを確認した。p1 は untagged VLAN1・tagged 10〜70 で問題なし（運用者の確認）。p2 には触っていない |
| 2026-11-11 | [コントローラー] 段階 3 の準備として、mDNS のルール `mdns-trusted-iot`（無効）と、ポートプロファイル `access-trusted`（未割り当て）を作った（運用者の報告） |
| 2026-11-11 | [コントローラー] 段階 3 の準備として、VLAN のネットワーク 7 つ（10〜70）を、設計書の値にそろえた（Servers・Lab・Guests・DMZ を新規に作成。Management の DNS を `10.77.10.1`、Trusted のリースを 48 時間に修正）。端末は繋いでいない（運用者の報告） |
| 2026-11-11 | [ER605] 段階 3 の準備として、VLAN のネットワーク 7 つ（10〜70）を、設計書の値にそろえた。Servers・Lab・Guests・DMZ を作成し、Management の DNS を `10.77.10.1`、Trusted のリースを 48 時間に直した。ACL は作っていない（運用者の報告） |
| 2026-11-11 | [SG2210P] ポートプロファイル `access-trusted`（ネイティブ Trusted(30)、タグ付きなし）を作った。どのポートにも割り当てていない。当日、p3・p4 に割り当てる（運用者の報告） |
| 2026-11-11 | [SG2210P] VLAN 20・40・60・70 を作ったあと、p2 の tagged に 10・20・30・40・50・60・70 がすべて入った（自動。untagged は VLAN1。p1〜p4 の Native と Network Tags は変わっていないことを確認。運用者の報告）。設計書の表は 10/20/40/50/70。30 と 60 は余分だが、Proxmox 側に 30・60 の VM がないので、害はない |
| 2026-11-09 | [コントローラー] ローカルの Owner の名前を、TP-Link ID と同じメール形式から `homelab-owner` に変えた。`omada.lab.kanare.dev` でユーザー設定（言語・テーマ）が `Account unauthorized` で保存できなかったため。予備に `homelab-admin`（Super Admin）を作った（運用者の報告） |
| 2026-11-09 | [コントローラー] メモリ枯渇で固まった（[INC-2026-11-09](../../../operations/incidents/2026-11-09-omada-memory-exhaustion.md)）ため、VM のメモリを 4GB にし、コンテナに Java ヒープ 768MB・MongoDB キャッシュ 0.25GB・`mem_limit` 2.5GB を付けた |
| 2026-11-09 | [SG2210P] リハーサルで access にしていた p5（VLAN30）と p6（VLAN50）を、空きポート（p7）と同じ設定に戻した。p5 は A の後も VLAN30 のままだった（運用者の報告）。p6 は IoT(50) のアクセスポートだった（A で作成。記録は INC-2026-11-08 と 22 番 Runbook の A） |
| 2026-11-06 | [コントローラー] サイトの NTP を `ntp.nict.jp` にした（運用者の報告） |
| 2026-11-06 | [コントローラー] サイト名を `kanare-homelab`、デバイス名を `er605`、`sg2210p` にした（運用者の報告） |
| 2026-11-06 | [コントローラー] 段階 1・2 で、ER605（2.4.2）と SG2210P（5.30.7）を採用した（運用者の報告）。`omada.lab.kanare.dev` を新設し、`router.lab.kanare.dev` を廃止した（Caddy の転送先と DNS レコード） |
| 2026-11-06 | [ER605] 段階 1・2 を実施した。Buffalo と入れ替え、壁の LAN を p1（WAN）に繋いだ。MAC クローンなしで WAN の IP を取れた。p2 は最初から LAN で動いた。コントローラーに採用した（採用のあとも、LAN と DHCP は変わらず。ファームウェアは 2.4.2 のまま）（運用者の報告） |
| 2026-11-06 | [ER605] ポートの種類（p1 が WAN、p2・p3 が WAN/LAN、p4・p5 が LAN）を、ポート表に追記した（運用者が本体で確認） |
| 2026-11-06 | [SG2210P] 段階 1・2 を実施した。Proxmox（p2）、Buffalo（p3）、ディスプレイ（p4）を繋ぎ、コントローラーに採用した。ファームウェアは 5.30.7（更新はしていない）（運用者の報告） |
| 2026-11-03 | [コントローラー] `vm-omada` を立てた（6.3.0.111）。ER605 を一度採用してファームウェアを更新し、取り外した |
| 2026-11-03 | [コントローラー] コントローラーの LAN の設定を、ER605 の LAN に合わせた（運用者の申告）。採用前のバックアップを iCloud Drive に保存した |
| 2026-11-03 | [コントローラー] この文書を作成 |
| 2026-11-03 | [ER605] JP 版 2.4.2 に更新した。工場出荷時に戻し、スタンドアロンで LAN `192.168.11.1/24`、DHCP `.60`〜`.99`・リース 48 時間・DNS `192.168.11.11` を設定した（運用者の申告） |
| 2026-11-03 | [ER605] この文書を作成 |
| 2026-11-03 | [SG2210P] この文書を作成（設定の変更は無し。ER605 の p2 に SG2210P の p1 を繋いだ） |
