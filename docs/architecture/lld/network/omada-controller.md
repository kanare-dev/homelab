# Omada コントローラーと管理対象機器（ER605・SG2210P）

Omada コントローラー（`vm-omada`）と、それが管理する ER605・SG2210P の詳細設計。将来は AP も、ここで一元管理する。設定の大半はコントローラーの中にあり、Git では管理しない（Open API でのコード化は[検討中](../../../operations/roadmap/01-backlog.md)）。**この文書を、コントローラーと ER605・SG2210P の設定値の正とする。** 製品の仕様は[ER605](../hardware/er605.md)・[SG2210P](../hardware/sg2210p.md)の資料、VLAN の設計は[第5章 ネットワーク](../../hld/05-network.md)、移行の経緯は[移行計画](../../../operations/roadmap/10-er605-sg2210p-migration-plan.md)にある。

> [!NOTE]
> 作成日は 2026-11-03。**秘密の値（管理者のパスワード、バックアップの暗号化の鍵、TP-Link ID のパスワード）と、機器の MAC アドレスは書かない**（リポジトリは公開）。Keychain の名前は `private/secrets-inventory.md`（台帳）にある。

## 運用

- コントローラーまたは機器（ER605・SG2210P）の設定を変えたら、**同じ変更でこの文書を更新**し、[変更履歴](#変更履歴)に 1 行足す。
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

## 設定値（現在）

| 項目 | 値 |
| --- | --- |
| ユーザー（Accounts） | ローカルユーザー `homelab-owner`（Owner。日常に使う）と `homelab-admin`（Super Admin。予備）。Cloud User（TP-Link ID 名義の Owner。**名前は変更できない仕様**）は Omada Cloud 用。パスワードは Keychain（名前は台帳）。**ローカルユーザーの名前を、メールアドレスの形にしない**（下の注）。ほかに、監視用の `exporter`（Viewer。サイト `kanare-homelab`。2026-11-27 に作成。パスワードは SOPS の `omada_exporter_password`。[ADR-0039](../../../adr/0039-omada-metrics-via-omada-exporter.md)） |
| サイト | 1 つ。名前は `kanare-homelab`（2026-11-06 に決めた） |
| LAN・VLAN のネットワーク | [ER605 の設定値](#er605ルーター)に書いている（コントローラーの Settings > Wired Networks > LAN で作る） |
| mDNS の中継（Settings > 一般設定 > mDNS） | ルール `mdns-trusted-iot`（**無効**のまま）。Bonjour サービスは AirPlay と Google Cast（一覧に無いので、`Google Cast` / `_googlecast._tcp.local` を追加した。サービス ID は `_A._B.local` の形）。バンド VLAN は「VLAN ID 別」、サービスネットワーク VLAN は 50（IoT）、クライアントネットワーク VLAN は 30（Trusted）。有効にして実機で確かめるのは、テレビを IoT に移すとき。Google Cast が中継できるか、`_googlezone._tcp` などの追加が要るかは、そのとき確認する |
| スイッチのポートプロファイル（デバイス設定 > ポートプロファイル） | 標準の Disable・All・Default のほかに、`access-trusted`（VLAN 設定オン、ネイティブネットワーク Trusted(30)、ネットワークタグ設定は全てブロック。PoE は機器の設定を保持）。p3（Buffalo）と p4（ディスプレイ）に割り当てている（「VLAN設定」は「プロファイルに従う」） |
| 採用している機器 | ER605（JP 版 2.4.2）と SG2210P（5.30.7）。2026-11-06 に採用した。デバイス名は、役割と番号（`rtr01`、`sw01`。AP は `ap01`）。2026-11-27 に、型番ベースの小文字（`er605`、`sg2210p`）から変えた（[ADR-0035](../../../adr/0035-network-device-names-by-role.md)）（2026-11-03 に、ER605 を一度採用して更新し、取り外していた） |
| Omada Cloud（クラウドアクセス） | **有効**（試用中。最終的に無効にするかもしれない。[外部サービスの表](../../hld/05-network.md#外部サービスへの依存)）。TP-Link ID は台帳 |
| Open API（Settings > Platform Integration > Open API） | アプリ `exporter`（Client Credentials モード、Viewer ロール。2026-11-27 に作成）。omada-exporter が、クライアント・WAN・ISP を読むのに使う。Client ID とシークレットは SOPS（`omada_exporter_client_id`、`omada_exporter_client_secret`）。最初は Authorization Code モードで作ってしまい、トークンの取得が `-44106` で失敗したので、Client モードに直した |
| 時刻（NTP） | サイトの設定（Site Settings）の NTP に `ntp.nict.jp`（2026-11-06 に設定。ER605・SG2210P に配られる時刻） |
| 地域（タイムゾーン） | (UTC+09:00) 大阪、札幌、東京（2026-11-06 に確認） |
| コントローラー本体の NTP | 指定する欄が無い（6.3.0.111。2026-11-06 に確認）。時刻は、`vm-omada` の OS（`systemd-timesyncd`、`ntp.nict.jp` など）に従う見込み（未確認） |
| 機器のファームウェアの自動更新 | 未確認。有効だと、機器（ER605・SG2210P）が自動で更新・再起動する。更新の時機を自分で決めたいので、無効のままにしたい |

> [!NOTE]
> Cloud Access が有効だと、ログイン画面に **TP-Link ID と同じ名前**（メール形式）を入力すると、ローカルユーザーではなくクラウド側で認証され、Cloud User のセッションになる（ログは `cloud tenant login strategy`）。このセッションは、ユーザーごとの設定（言語・テーマ・24 時間表記）を保存できず、`Account unauthorized`（`-90021`）になる。ローカルユーザーの名前を別の名前（`@` を含まない）にすると、`local tenant login strategy` で入れて保存できる。2026-11-09 に、ローカルの Owner を `homelab-owner` に改名して確認した。

## ER605（ルーター）

TP-Link ER605 V2。製品の仕様とファームウェアは[ER605 の資料](../hardware/er605.md)にある。

家のルーター（NAT と、各 VLAN のゲートウェイ・DHCP・ACL）である。集合住宅の共用ルーターの下に置く（二重 NAT）。既定のネットワークは Management（VLAN10、`10.77.10.0/24`）で、VLAN1 は使わない（[ADR-0032](../../../adr/0032-merge-default-network-into-management-vlan10.md)）。設定はコントローラーから行い、本体の画面は使えない。

### ER605 のポート

| ポート | 接続先 | 備考 |
| --- | --- | --- |
| p1（WAN） | 壁の LAN ポート（ケーブル A） | 接続済み（2026-11-06）。MAC クローンなしで IP を取れた |
| p2（WAN/LAN） | SG2210P の p1 | 接続済み。LAN として動いている（最初から LAN。2026-11-06 に確認） |
| p3（WAN/LAN） | 使わない（段階 1・2 の確認のとき、Mac を一時的に繋いだ） | |
| p4〜p5（LAN） | 使わない | |

ポートの種類は、p1 が WAN 専用、p2 と p3 が WAN/LAN の切り替え、p4 と p5 が LAN 専用（運用者が本体で確認。2026-11-06）。

### WAN

| 項目 | 値 |
| --- | --- |
| 接続方法 | DHCP（上流は建物の共用ルーター。`172.22.0.0/21` の範囲の見込み）。2026-11-06 に、ER605 を繋いで IP を取れた |
| MAC アドレス | 既定（MAC クローンは不要だった。上流は、MAC で絞っていない。2026-11-06 に確認） |
| IPv6 | 使わない（[ADR-0017](../../../adr/0017-ipv6-disabled.md)）。設定値は未確認 |

### LAN と DHCP

| 項目 | 値 |
| --- | --- |
| LAN 側 IP アドレス | `10.77.10.1` / `255.255.255.0`（VLAN10、名前 `Management(Default)`。[ADR-0032](../../../adr/0032-merge-default-network-into-management-vlan10.md)） |
| DHCP サーバー | 使用する。範囲 `10.77.10.240`〜`10.77.10.250`（復旧ポート p8 に繋いだ端末向け）、リース 60 分 |
| 配る DNS | ルーター（`10.77.10.1`）。`1.1.1.1` は併記しない（[ADR-0024](../../../adr/0024-dhcp-dns-single-no-fallback.md)）。ER605 の DNS プロキシが外部の名前を引く。内部の名前（`*.lab.kanare.dev`）は引けないので、IP で入る |
| 配るドメイン名 | 配らない |
| 固定割り当て（予約） | なし（Buffalo の固定リース 1 件は、移さない。[移行計画](../../../operations/roadmap/10-er605-sg2210p-migration-plan.md)） |

### VLAN のネットワーク

コントローラー（Settings > Wired Networks > LAN）で作っている。ER605 の LAN ポート（WAN/LAN2・WAN/LAN3・LAN4・LAN5）に割り当てている。Servers・Lab・Trusted には、ホストと端末を繋いでいる。既定のネットワークは Management（VLAN10）で、VLAN1 は使わない（上の「LAN と DHCP」）。

| VLAN | 名前 | ゲートウェイ | DHCP |
| --- | --- | --- | --- |
| 10 | Management | `10.77.10.1/24` | `.240–.250`、リース 60 分、DNS `10.77.10.1` |
| 20 | Servers | `10.77.20.1/24` | なし |
| 30 | Trusted | `10.77.30.1/24` | `.100–.199`、リース 48 時間、DNS `10.77.20.10` |
| 40 | Lab | `10.77.40.1/24` | `.100–.149`、リース 24 時間、DNS `10.77.20.10` |
| 50 | IoT | `10.77.50.1/24` | `.100–.149`、リース 24 時間、DNS `10.77.20.10` |
| 60 | Guests | `10.77.60.1/24` | `.100–.199`、リース 4 時間、DNS `10.77.20.10` |
| 70 | DMZ | `10.77.70.1/24` | なし |
| 999 | Blackhole | `10.77.99.1/24` | なし（ER605 のポートには割り当てない。使わないポートの native） |

### ゲートウェイの ACL

**2026-11-27 に、この節の値で ACL を絞った**（[手順書 27](../../../operations/runbooks/27-network-acl-tighten.md#実施の記録)。それまでは全許可だった）。方針は[通信ポリシー](../../hld/05-network.md#通信ポリシー)と [ADR-0034](../../../adr/0034-acl-for-vlan-boundaries-ufw-for-ports.md)、名前の付け方は [ACL の名前と説明の付け方](acl.md)にある。画面の場所は、サイト > 構成 > ネットワーク設定 > セキュリティ > ACL の「ゲートウェイ ACL」（方向は LAN → LAN）である。リハーサルの `rh-` のルール 7 件は、同じ日に削除した。

ルールから参照するグループを、先に作る（ルールの作成画面の「＋作成」からも作れる）。IP-Port グループは、サブネット（CIDR）の一覧と、ポートの一覧を別々に持ち、ポートはグループの全サブネットにかかる。範囲（`10.77.10.2-10.77.10.9`）は書けない。そのため、ホストごとにポートが違うものは、グループを分けた（許可の範囲は、分ける前の設計と同じ）。

| グループ名 | 種類 | サブネット | ポート |
| --- | --- | --- | --- |
| `grp-vm-infra` | IP グループ | `10.77.20.10/32` | — |
| `grp-vm-monitoring` | IP グループ | `10.77.20.11/32` | — |
| `grp-mgmt-omada-ui` | IP-Port グループ | `10.77.10.3/32` | 8043 |
| `grp-mgmt-pve-ui` | IP-Port グループ | `10.77.10.10/32` | 8006 |
| `grp-mgmt-metrics` | IP-Port グループ | `10.77.10.3/32`、`10.77.10.10/32` | 9100 |
| `grp-mgmt-pve-admin` | IP-Port グループ | `10.77.10.10/32` | 8006、22 |
| `grp-mgmt-omada-ssh` | IP-Port グループ | `10.77.10.3/32` | 22 |
| `grp-mgmt-devices-web` | IP-Port グループ | `10.77.10.0/29`、`10.77.10.8/31`（機器の帯 `.2`〜`.9` を含む。[ACL の名前と説明の付け方](acl.md)） | 80、443 |
| `grp-lab-access` | IP-Port グループ | `10.77.40.0/24` | 22、80、443 |
| `grp-lab-mosh` | IP-Port グループ | `10.77.40.0/24` | 60000-61000 |
| `grp-lab-metrics` | IP-Port グループ | `10.77.40.0/24` | 9100 |
| `grp-dns` | IP-Port グループ | `10.77.20.10/32` | 53 |

ルールは、上から順に評価される。表の順に作る。一覧に表示されるのは「説明」の欄なので、名前（`130-servers-to-mgmt-caddy` など）を説明の欄に入れた。1 件のルールの宛先には、グループを複数選べる。プロトコルも複数選べる（「TCP & UDP」と表示される）。

| 名前 | 動作 | プロトコル | 送信元 | 宛先 |
| --- | --- | --- | --- | --- |
| `130-servers-to-mgmt-caddy` | 許可 | TCP | `grp-vm-infra` | `grp-mgmt-omada-ui`、`grp-mgmt-pve-ui` |
| `131-servers-to-mgmt-metrics` | 許可 | TCP | `grp-vm-monitoring` | `grp-mgmt-metrics` |
| `140-servers-to-lab-ssh` | 許可 | TCP | `grp-vm-infra` | `grp-lab-access` |
| `141-servers-to-lab-metrics` | 許可 | TCP | `grp-vm-monitoring` | `grp-lab-metrics` |
| `142-servers-to-lab-mosh` | 許可 | UDP | `grp-vm-infra` | `grp-lab-mosh` |
| `150-trusted-to-servers` | 許可 | すべて | ネットワーク Trusted | ネットワーク Servers |
| `151-trusted-to-lab` | 許可 | すべて | ネットワーク Trusted | ネットワーク Lab |
| `153-trusted-to-mgmt` | 許可 | TCP | ネットワーク Trusted | `grp-mgmt-pve-admin`、`grp-mgmt-omada-ssh` |
| `154-trusted-to-mgmt-devices` | 許可 | TCP | ネットワーク Trusted | `grp-mgmt-devices-web` |
| `156-trusted-to-mgmt-icmp` | 許可 | ICMP | ネットワーク Trusted | ネットワーク Management |
| `160-trusted-to-iot` | 許可 | すべて | ネットワーク Trusted | ネットワーク IoT |
| `170-lab-to-servers-dns` | 許可 | TCP と UDP | ネットワーク Lab | `grp-dns` |
| `171-iot-to-servers-dns` | 許可 | TCP と UDP | ネットワーク IoT | `grp-dns` |
| `172-guests-to-servers-dns` | 許可 | TCP と UDP | ネットワーク Guests | `grp-dns` |
| `910-deny-from-mgmt` | 拒否 | すべて | ネットワーク Management | !ネットワーク Management |
| `920-deny-from-servers` | 拒否 | すべて | ネットワーク Servers | !ネットワーク Servers |
| `930-deny-from-trusted` | 拒否 | すべて | ネットワーク Trusted | !ネットワーク Trusted |
| `940-deny-from-lab` | 拒否 | すべて | ネットワーク Lab | !ネットワーク Lab |
| `950-deny-from-iot` | 拒否 | すべて | ネットワーク IoT | !ネットワーク IoT |
| `960-deny-from-guests` | 拒否 | すべて | ネットワーク Guests | !ネットワーク Guests |
| `970-deny-from-dmz` | 拒否 | すべて | ネットワーク DMZ | !ネットワーク DMZ |

- 戻りの通信（確立済み）は、ルールが無くても通る（2026-11-27 に確認。拒否を有効にした VLAN へ、許可した向きから SSH で入れた）。
- Trusted → DMZ（Web・SSH）、Servers → DMZ（ログの取得）、Management → DMZ（管理用ポート）は、DMZ に何も置いていないので、作らない（今は末尾の拒否に当たる）。DMZ に機器を置くときに足す。
- **確認済み（2026-11-27）**: プロトコルは、ICMP だけも、TCP と UDP の両方も選べる。送信元に IP グループ、宛先に IP-Port グループを選べる。
- **確認済み（2026-11-27）**: `!ネットワーク` の拒否は、WAN 側のプライベートアドレス（建物の共用ルーター `172.22.0.1`）宛の通信を止めない。`vm-monitoring` から `172.22.0.1` への ping は、`920` を有効にしたあとも通り、Prometheus の `building-router` の監視は `up` のままだった。
- 確かめ方: Mac（Tailscale をオフ）と各ホストから、許可と拒否の両方を 35 件流す `make acl-check`（`tools/acl-check.py`）で確かめた（[手順書 27](../../../operations/runbooks/27-network-acl-tighten.md#実施の記録)）。コントローラーや機器を作り直したあとは、ACL が全許可に戻っていないかを、これで確かめる。**ルールを変えたら、スクリプトのケースも同じ変更で直す。**

### ER605 の管理・その他

| 項目 | 値 |
| --- | --- |
| Omada でのデバイス名 | `rtr01`（サイト `kanare-homelab`。2026-11-27 に `er605` から変更。[ADR-0035](../../../adr/0035-network-device-names-by-role.md)） |
| ファームウェア | JP 版 2.4.2 Build 20260511 Rel.77362（2026-11-03 に更新。2026-11-06 の採用のあとも、同じ版） |
| 管理者アカウント | パスワードは Keychain（`homelab / er605 admin`） |
| ローカル DNS（Domain Name、Alias Domain Name） | 登録しない（名前解決は `vm-infra` の CoreDNS） |
| NTP | `ntp.nict.jp`（コントローラーのサイトの設定から配る。2026-11-06） |
| UPnP | **無効**（2026-11-27 に確認。デバイス > `rtr01` > 設定 > アドバンス > UPnP）。外に何も公開しない方針なので、無効のままにする |
| 時刻、ファイアウォール | 未確認 |

## SG2210P（スイッチ）

TP-Link SG2210P V5.30。製品の仕様は[SG2210P の資料](../hardware/sg2210p.md)にある。

有線のハブを兼ねる PoE+ スイッチである。ER605 の p2 に繋ぎ、Proxmox（p2）、Buffalo（p3）、ディスプレイ（p4）を収める。VLAN の trunk と access を設定している。設定はコントローラーから行う。

### SG2210P のポート

| ポート | 接続先 | 備考 |
| --- | --- | --- |
| p1 | ER605 の p2 | アップリンク。**native Management(10)**（untagged VLAN10）、タグ付きは Servers(20)〜DMZ(70) のカスタム（`Blackhole` は除く。VLAN 999 を ER605 に流さないため）（2026-11-20〜） |
| p2 | Proxmox | trunk。**native `Blackhole`(999)**、タグ付きは Management(10)・Servers(20)・Trusted(30)・Lab(40)・IoT(50)・Guests(60)・DMZ(70) のカスタム（2026-11-20〜）。**タグ付きに Management を必ず含める**（含めないと、VLAN10 が untagged になり、Proxmox・`vm-omada` に届かなくなる。2026-11-20 の実績） |
| p3 | Buffalo（AP） | **access VLAN30（untagged）**。プロファイル `access-trusted`、「VLAN設定」は「プロファイルに従う」（2026-11-17〜） |
| p4 | メインディスプレイ（Dell U2725QE） | **access VLAN30（untagged）**。p3 と同じ（2026-11-17〜） |
| p5–p7 | 空き | p5 から前詰めで、AP・カメラなどに使う（全ポートが PoE+）。**native `Blackhole`、タグ全ブロック**（2026-11-20〜。どこにも繋がらない） |
| p8 | **復旧ポート**（旧称: 緊急用の入口。決定 2026-11-10 は p6。**2026-11-19 に p8 に変更**。空きを連続させるため） | **native Management(10)**（untagged VLAN10）、タグ全許可（2026-11-20〜）。DHCP は、復旧用の範囲 `10.77.10.240`〜`.250`（ER605 が生きているとき） |
| p9–p10 | SFP（使わない） | |

注: 2026-11-20 より前は、p1・p2・p5〜p8 が、ネイティブ Default(1)・タグ全許可だった（VLAN1。空きポートでも、タグ付きの通信は、すべての VLAN に入れた）。

ポートの VLAN の方針は、[第5章 ネットワーク](../../hld/05-network.md#配置の方針)にある。

### SG2210P の管理

| 項目 | 値 |
| --- | --- |
| Omada でのデバイス名 | `sw01`（サイト `kanare-homelab`。2026-11-27 に `sg2210p` から変更。[ADR-0035](../../../adr/0035-network-device-names-by-role.md)） |
| NTP | `ntp.nict.jp`（コントローラーのサイトの設定から配る。2026-11-06） |
| ファームウェア | 5.30.7。**最新**（2026-11-06 に、採用したあと、コントローラーの画面で確認。サポートページの V5.30 の一覧で、5.30.7（Build 20260509、2026-06-11 掲載）が最新。日本語ページも同じ一覧で、地域の表記は UN だけ）。更新はしていない |
| 管理 IP | **`10.77.10.2/24`（VLAN10、静的。ゲートウェイ・DNS は `10.77.10.1`）。** 管理 VLAN のインターフェースは `Management(Default)`（VLAN10）の 1 つだけ（旧 VLAN1 のインターフェースは、2026-11-20 になくなった）。コントローラーへの接続は、`10.77.10.3` 宛て |
| PoE | 全ポート 802.3af/at。電力予算は 61W 前後。段階 4 まで、給電する機器はない |
| IGMP スヌーピング、STP、ストームコントロール | 未確認 |

## 見直したい項目・未確認

- 自動バックアップの保存先を、`vm-omada` の外にも広げるか（[バックログ](../../../operations/roadmap/01-backlog.md)）。
- Omada Cloud を使い続けるか。
- 設定のコード化（Open API、コミュニティ製の Terraform プロバイダー）。
- 機器のファームウェアの自動更新が、無効になっているかを確認する（有効なら、無効にするか決める）。
- ER605: 採用後の設定値（LAN、DHCP、NTP・時刻、ファイアウォール）を、コントローラーの画面から書き写し直す（採用のあと、LAN と DHCP が変わっていないことは、2026-11-06 に確認した）。
- ER605: 管理者アカウント（コントローラーが機器に入るためのアカウント）が、初期値のままではないこと。
- SG2210P: 採用後の設定値（IGMP スヌーピング、STP、ストームコントロールなど）を、コントローラーの画面から書き写し直す。
- SG2210P: 新しいファームウェアが出たか（サポートページの V5.30 の一覧で確認する。更新するときは、手順の確認が通ってから別の機会に行い、地域は、コントローラーが表示する今の版に合わせる）。

- ER605 で確認済み（2026-11-06）: p2 は最初から LAN として動いた。上流は MAC で絞っていない（MAC クローンなしで IP を取れた）。
- SG2210P で確認済み（2026-11-06）: 標準の設定のまま、スイッチとして動いた（段階 1・2 の配線の確認が通った）。

## 変更履歴

| 日付 | 内容 |
| --- | --- |
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
