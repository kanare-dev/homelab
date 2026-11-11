# Omada コントローラー（vm-omada）

Omada コントローラーの詳細設計。ER605・SG2210P・将来の AP を一元管理する。設定の大半はコントローラーの中にあり、Git では管理しない（Open API でのコード化は[検討中](../../operations/roadmap/01-backlog.md)）。**この文書を、設定値の正とする。** 製品の仕様は[ER605](../../hardware/er605/spec.md)・[SG2210P](../../hardware/sg2210p/spec.md)の資料、機器ごとの設定は[ER605 の設定](../../hardware/er605/settings.md)・[SG2210P の設定](../../hardware/sg2210p/settings.md)、移行の手順は[移行計画](../../operations/roadmap/10-er605-sg2210p-migration-plan.md)にある。

> [!NOTE]
> 作成日は 2026-11-03。**秘密の値（管理者のパスワード、バックアップの暗号化の鍵、TP-Link ID のパスワード）と、機器の MAC アドレスは書かない**（リポジトリは公開）。Keychain の名前は `private/secrets-inventory.md`（台帳）にある。

## 運用

- コントローラーまたは機器の設定を変えたら、**同じ変更でこの文書（と、機器の文書）を更新**し、[変更履歴](#変更履歴)に 1 行足す。
- 設定を変えたあとは、手動バックアップを取る。画面の Settings > Maintenance の「Backup & Restore」で保存する（メニューの名前は 6.3 で未確認）。保存先は iCloud Drive の `homelab/`（暗号化なし。運用者が受け入れ。[バックログ](../../operations/roadmap/01-backlog.md)）。ファイル名は `omada-bk-YYYYMMDD.cfg`（案）。直近の 3 世代ほどを残す。
- 自動バックアップは、毎週日曜 03:00（`vm-omada` の `/opt/omada/data/autobackup`）。VM のディスクの中なので、VM が壊れると一緒に失われる。
- 画面には、`ssh -L 8043:localhost:8043 vm-omada` のあと `https://localhost:8043` で入る（`omada.lab.kanare.dev` は未作成。段階 1・2 のあとに作る）。

## 構成

| 項目 | 値 |
| --- | --- |
| VM | `vm-omada`（VMID 112、`192.168.11.12`。VLAN 化のあとは `10.77.10.3`、VLAN10）。2 vCPU、メモリ 4GB（2026-11-09 に 3GB から増やした）、ディスク 20G。起動は自動（順序 6） |
| コントローラー | Omada Controller 6.3.0.111。Docker（`mbentley/omada-controller:6.3.0.111`、host ネットワーク）。`docker/compose/omada/docker-compose.yml`、Ansible の `omada.yml` |
| メモリの上限 | Java ヒープ最大 768MB（`JAVA_MAX_HEAP_SIZE`）、MongoDB の WiredTiger キャッシュ 0.25GB（`MONGOD_EXTRA_ARGS`）、コンテナ全体で 2.5GB（`mem_limit`）。VM にスワップは無い。上限の根拠は [INC-2026-11-09](../../operations/incidents/2026-11-09-omada-memory-exhaustion.md) |
| データ | `/opt/omada/data`、ログ `/opt/omada/logs` |
| 反映 | `make setup-omada` |
| ポート | 管理 HTTPS 8043、管理 HTTP 8088、ポータル 8843。機器との通信は UDP 29810（自動検出）、TCP 29811〜29816。UFW で絞る（`ansible/inventory/group_vars/omada/vars.yml`） |
| 監視 | `node_exporter` を Prometheus が見ている（`TargetDown`）。画面（HTTPS）の外形監視は未導入（[監視・アラート](../platform/monitoring.md)） |

## 設定値（現在）

| 項目 | 値 |
| --- | --- |
| ユーザー（Accounts） | ローカルユーザー `homelab-owner`（Owner。日常に使う）と `homelab-admin`（Super Admin。予備）。Cloud User（TP-Link ID 名義の Owner。**名前は変更できない仕様**）は Omada Cloud 用。パスワードは Keychain（名前は台帳）。**ローカルユーザーの名前を、メールアドレスの形にしない**（下の注） |
| サイト | 1 つ。名前は `kanare-homelab`（2026-11-06 に決めた） |
| LAN（Settings > Wired Networks > LAN） | `192.168.11.1/24`、DHCP `.60`〜`.99`、リース 48 時間、DNS は `192.168.11.11` だけ（2026-11-03 に運用者が設定。画面の値は未確認） |
| VLAN のネットワーク（段階 3 の準備。2026-11-11 に作成） | 10・20・30・40・50・60・70 の 7 つ（値は[ER605 の設定](../../hardware/er605/settings.md#vlan-のネットワーク段階-3-の準備)）。端末・ホストは、まだ繋がっていない。当日（段階 3）に、ポートと端末を移す。ACL は作らない（全許可。[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)） |
| mDNS の中継（Settings > 一般設定 > mDNS） | ルール `mdns-trusted-iot`（2026-11-11 に作成。**無効**のまま）。Bonjour サービスは AirPlay と Google Cast（一覧に無いので、`Google Cast` / `_googlecast._tcp.local` を追加した。サービス ID は `_A._B.local` の形）。バンド VLAN は「VLAN ID 別」、サービスネットワーク VLAN は 50（IoT）、クライアントネットワーク VLAN は 30（Trusted）。有効にして実機で確かめるのは、段階 4（テレビを IoT に移すとき）。Google Cast が中継できるか、`_googlezone._tcp` などの追加が要るかは、そのとき確認する |
| スイッチのポートプロファイル（デバイス設定 > ポートプロファイル） | 標準の Disable・All・Default のほかに、`access-trusted`（2026-11-11 に作成。VLAN 設定オン、ネイティブネットワーク Trusted(30)、ネットワークタグ設定は全てブロック。PoE は機器の設定を保持）。**どのポートにも割り当てていない**。当日（段階 3）に、p3（Buffalo）と p4（ディスプレイ）へ割り当てる |
| 採用している機器 | ER605（JP 版 2.4.2）と SG2210P（5.30.7）。2026-11-06 に採用した。デバイス名は、型番ベースの小文字（`er605`、`sg2210p`。AP を足すときも、同じ付け方で `eap-xxx` など）（2026-11-03 に、ER605 を一度採用して更新し、取り外していた） |
| Omada Cloud（クラウドアクセス） | **有効**（試用中。最終的に無効にするかもしれない。[外部サービスの表](../../architecture/03-network.md#外部サービスへの依存)）。TP-Link ID は台帳 |
| Open API | 使っていない |
| 時刻（NTP） | サイトの設定（Site Settings）の NTP に `ntp.nict.jp`（2026-11-06 に設定。ER605・SG2210P に配られる時刻） |
| 地域（タイムゾーン） | (UTC+09:00) 大阪、札幌、東京（2026-11-06 に確認） |
| コントローラー本体の NTP | 指定する欄が無い（6.3.0.111。2026-11-06 に確認）。時刻は、`vm-omada` の OS（`systemd-timesyncd`、`ntp.nict.jp` など）に従う見込み（未確認） |
| 機器のファームウェアの自動更新 | 未確認。有効だと、機器（ER605・SG2210P）が自動で更新・再起動する。更新の時機を自分で決めたいので、無効のままにしたい |

> [!NOTE]
> Cloud Access が有効だと、ログイン画面に **TP-Link ID と同じ名前**（メール形式）を入力すると、ローカルユーザーではなくクラウド側で認証され、Cloud User のセッションになる（ログは `cloud tenant login strategy`）。このセッションは、ユーザーごとの設定（言語・テーマ・24 時間表記）を保存できず、`Account unauthorized`（`-90021`）になる。ローカルユーザーの名前を別の名前（`@` を含まない）にすると、`local tenant login strategy` で入れて保存できる。2026-11-09 に、ローカルの Owner を `homelab-owner` に改名して確認した。

## 見直したい項目・未確認

- 自動バックアップの保存先を、`vm-omada` の外にも広げるか（[バックログ](../../operations/roadmap/01-backlog.md)）。
- Omada Cloud を使い続けるか。
- 設定のコード化（Open API、コミュニティ製の Terraform プロバイダー）。
- 機器のファームウェアの自動更新が、無効になっているかを確認する（有効なら、無効にするか決める）。

## 変更履歴

| 日付 | 内容 |
| --- | --- |
| 2026-11-11 | 段階 3 の準備として、mDNS のルール `mdns-trusted-iot`（無効）と、ポートプロファイル `access-trusted`（未割り当て）を作った（運用者の報告） |
| 2026-11-11 | 段階 3 の準備として、VLAN のネットワーク 7 つ（10〜70）を、設計書の値にそろえた（Servers・Lab・Guests・DMZ を新規に作成。Management の DNS を `10.77.10.1`、Trusted のリースを 48 時間に修正）。端末は繋いでいない（運用者の報告） |
| 2026-11-09 | ローカルの Owner の名前を、TP-Link ID と同じメール形式から `homelab-owner` に変えた。`omada.lab.kanare.dev` でユーザー設定（言語・テーマ）が `Account unauthorized` で保存できなかったため。予備に `homelab-admin`（Super Admin）を作った（運用者の報告） |
| 2026-11-09 | メモリ枯渇で固まった（[INC-2026-11-09](../../operations/incidents/2026-11-09-omada-memory-exhaustion.md)）ため、VM のメモリを 4GB にし、コンテナに Java ヒープ 768MB・MongoDB キャッシュ 0.25GB・`mem_limit` 2.5GB を付けた |
| 2026-11-06 | サイトの NTP を `ntp.nict.jp` にした（運用者の報告） |
| 2026-11-06 | サイト名を `kanare-homelab`、デバイス名を `er605`、`sg2210p` にした（運用者の報告） |
| 2026-11-06 | 段階 1・2 で、ER605（2.4.2）と SG2210P（5.30.7）を採用した（運用者の報告）。`omada.lab.kanare.dev` を新設し、`router.lab.kanare.dev` を廃止した（Caddy の転送先と DNS レコード） |
| 2026-11-03 | `vm-omada` を立てた（6.3.0.111）。ER605 を一度採用してファームウェアを更新し、取り外した |
| 2026-11-03 | コントローラーの LAN の設定を、ER605 の LAN に合わせた（運用者の申告）。採用前のバックアップを iCloud Drive に保存した |
| 2026-11-03 | この文書を作成 |
