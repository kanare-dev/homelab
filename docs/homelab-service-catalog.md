# HomeLab Service Catalog

ホームラボで利用するツール・サービスをカテゴリ別に整理したカタログです。候補集であり、このリポジトリの構成そのものではありません。各ツールの「状況」で、採用の度合いを示します。

## カテゴリ一覧

| # | カテゴリ |
| --- | --- |
| 1 | [ハードウェア](#1-ハードウェア-hardware) |
| 2 | [コンピュート & 仮想化](#2-コンピュート--仮想化-compute--virtualization) |
| 3 | [オペレーティングシステム](#3-オペレーティングシステム-os) |
| 4 | [ネットワーク](#4-ネットワーク-network) |
| 5 | [ストレージ & バックアップ](#5-ストレージ--バックアップ-storage--backup) |
| 6 | [データベース](#6-データベース-database) |
| 7 | [監視 & 可観測性](#7-監視--可観測性-monitoring--observability) |
| 8 | [セキュリティ & アイデンティティ](#8-セキュリティ--アイデンティティ-security--identity) |
| 9 | [メディア & エンターテインメント](#9-メディア--エンターテインメント-media--entertainment) |
| 10 | [スマートホーム & IoT](#10-スマートホーム--iot-smart-home--iot) |
| 11 | [通信](#11-通信-communication) |
| 12 | [ダッシュボード & 管理](#12-ダッシュボード--管理-dashboard--management) |
| 13 | [開発 & 生産性](#13-開発--生産性-development--productivity) |
| 14 | [レシピ・ライフスタイル](#14-レシピライフスタイル-lifestyle) |
| 15 | [カメラ・セキュリティ](#15-カメラセキュリティ-camera--security) |
| 16 | [分析 & その他](#16-分析--その他-analytics--other) |
| 17 | [通信分析](#17-通信分析-network-traffic-analysis) |
| 18 | [ハニーポット](#18-ハニーポット-honeypot) |

---

## 状況の凡例

| 状況 | 意味 | 根拠 |
| --- | --- | --- |
| 導入済み | 現行構成で稼働している | [インフラ構成](architecture/02-infrastructure.md) |
| 計画中 | 導入を決めて、ロードマップに載せている | [未着手の項目](operations/roadmap/01-backlog.md)、大型計画 |
| 検討中 | 導入するか、条件が整ったら着手するかを検討している | [ロードマップ](operations/roadmap/README.md)、[ADR](adr/README.md) |
| 見送り | 検討して導入しないと決めた | [見送り中の項目](operations/roadmap/03-deferred.md)、[ADR](adr/README.md) |
| 廃止 | 導入して使っていたが、のちに外した | 外した理由を [ADR](adr/README.md) か[障害記録](operations/incidents/README.md)に残す |
| 未検討 | 候補として挙げただけで、判断していない | — |

## 更新のしかた

- 構成や判断を変えたら、同じ変更で「状況」を更新する。会話に出たサービスは、導入するか決めていなくても「未検討」で行を追加する
- 状況は、おおむね 未検討 → 検討中 → 計画中 → 導入済み → 廃止 の順に進む。見送りは、どの段階からでも決められる
- 見送り・廃止にしたら、理由と再検討する条件を [見送り中の項目](operations/roadmap/03-deferred.md) か ADR に書き、「根拠・備考」からリンクする
- 計画中・検討中・導入済みの行は、「根拠・備考」から設計書・ロードマップ・ADR へリンクする
- 同じ役割のツールが複数あるときは、末尾の「役割別の採用状況」も更新する

---

## 1. ハードウェア (Hardware)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | Lenovo ThinkCentre Tiny | 省スペース型デスクトップ PC | [インフラ構成](architecture/02-infrastructure.md) |
| 未検討 | Dell Optiplex Micro | 省スペース型デスクトップ PC | — |
| 未検討 | HP EliteDesk Mini | 省スペース型デスクトップ PC | — |
| 未検討 | Raspberry Pi | シングルボードコンピュータ | — |
| 未検討 | RTL-SDR | USB 接続のソフトウェア無線レシーバー（電波の受信・解析） | — |

---

## 2. コンピュート & 仮想化 (Compute & Virtualization)

### 2.1 ハイパーバイザー (Hypervisor)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | Proxmox VE | オープンソースの仮想化・コンテナ基盤 | [インフラ構成](architecture/02-infrastructure.md) |
| 未検討 | XCP-ng | Xen ベースのオープンソースハイパーバイザー | — |
| 未検討 | Harvester | Rancher 製 Kubernetes ネイティブハイパーバイザー | — |

### 2.2 Kubernetes

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 検討中 | k3s | 軽量 Kubernetes ディストリビューション | [未着手の項目](operations/roadmap/01-backlog.md) |
| 未検討 | k0s | ゼロフリック Kubernetes ディストリビューション | — |
| 未検討 | MicroK8s | Canonical 製軽量 Kubernetes | — |
| 未検討 | Talos | イミュータブル OS ベースの Kubernetes | — |
| 未検討 | Kubeadm | 公式 Kubernetes クラスタ構築ツール | — |

### 2.3 ワークロードオーケストレーション（Kubernetes 外）

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | Nomad | HashiCorp 製ワークロードオーケストレーター | — |

### 2.4 Kubernetes ツール

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | Helm | Kubernetes パッケージマネージャ | — |
| 未検討 | Rancher | Kubernetes クラスタ管理 UI | — |
| 未検討 | Longhorn | Kubernetes 向け分散ストレージ | — |

### 2.5 コンテナランタイム

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | Docker | コンテナランタイム・デーモン | [インフラ構成](architecture/02-infrastructure.md) |
| 未検討 | containerd | OCI 準拠コンテナランタイム | — |
| 未検討 | nerdctl | containerd 向け Docker 互換 CLI | — |
| 未検討 | Podman | daemon レス・ルートレス対応コンテナツール | — |

### 2.6 仮想化補助ツール

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | Cockpit | サーバー管理 Web UI | — |
| 未検討 | virt-manager | 仮想マシン管理 GUI | — |
| 未検討 | libvirt | 仮想化管理 API・ライブラリ | — |
| 導入済み | Terraform | 宣言型インフラ管理 | [インフラ構成](architecture/02-infrastructure.md) |
| 導入済み | Ansible | 構成管理・自動化 | [インフラ構成](architecture/02-infrastructure.md) |

### 2.7 VM テンプレート・プロビジョニング

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 見送り | Packer | マルチクラウド対応 VM イメージビルダー | [見送り中の項目](operations/roadmap/03-deferred.md#方針のない候補) |
| 導入済み | cloud-init | クラウド / VM 初回起動時の初期化 | [インフラ構成](architecture/02-infrastructure.md) |

### 2.8 コンテナ管理

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 見送り | portainer/portainer-ce | Docker / Kubernetes 管理 UI | [見送り中の項目](operations/roadmap/03-deferred.md#方針のない候補) |
| 未検討 | containerrr/watchtower | コンテナイメージの自動更新 | — |
| 未検討 | amir20/dozzle | Docker コンテナのログをブラウザでリアルタイム表示 | — |

---

## 3. オペレーティングシステム (OS)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | Ubuntu | Debian 系 Linux ディストリビューション。VM は 24.04 LTS | [ADR 0021](adr/0021-ubuntu-lts-for-vms.md)、[インフラ構成](architecture/02-infrastructure.md) |
| 見送り | Debian | 汎用 Linux ディストリビューション。PVE ホストは Debian 13 ベース | [ADR 0021](adr/0021-ubuntu-lts-for-vms.md)、[見送り中の項目](operations/roadmap/03-deferred.md) |
| 未検討 | Arch | ロールリリース型 Linux ディストリビューション | — |
| 未検討 | openSUSE | SUSE 系 Linux ディストリビューション | — |

---

## 4. ネットワーク (Network)

### 4.1 ルーター / ファイアウォール

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 計画中 | OPNSense | オープンソースファイアウォール・ルーター | [OPNsense 導入](operations/roadmap/08-network-opnsense.md) |
| 未検討 | pfSense | オープンソースファイアウォール・ルーター | — |
| 未検討 | FRITZ!Box（fritz.box） | AVM 製ルーター（管理画面は `fritz.box`） | — |

### 4.2 DNS

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | Unbound DNS | 軽量キャッシュ DNS リゾルバ | [ADR 0020](adr/0020-dns-three-layer-stack.md)、[DNS 構成](services/network/dns.md) |
| 導入済み | CoreDNS | Kubernetes 向けプラグイン型 DNS（`lab.kanare.dev` の権威として利用） | [ADR 0020](adr/0020-dns-three-layer-stack.md)、[DNS 構成](services/network/dns.md) |
| 見送り | pi-hole/pi-hole | 広告ブロック DNS | [ADR 0020](adr/0020-dns-three-layer-stack.md) |
| 見送り | TechnitiumSoftware/DnsServer | 権威・再帰・ブロックを兼ねる DNS サーバー | [ADR 0020](adr/0020-dns-three-layer-stack.md) |
| 見送り | isc-projects/bind9 | 権威・再帰の本格的な DNS サーバー | [ADR 0020](adr/0020-dns-three-layer-stack.md) |
| 導入済み | adguard/adguardhome | 広告・トラッキングブロック DNS | [ADR 0020](adr/0020-dns-three-layer-stack.md)、[DNS 構成](services/network/dns.md) |
| 導入済み | Cloudflare DNS | 公開ドメインの DNS と API（Caddy の DNS-01 証明書に利用。SaaS） | [リバースプロキシ・TLS](services/network/reverse-proxy-tls.md) |

### 4.3 リバースプロキシ

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 見送り | nginx/nginx | Web サーバー・リバースプロキシ | [ADR 0019](adr/0019-caddy-reverse-proxy.md) |
| 見送り | jc21/nginx-proxy-manager | Nginx の Web UI 管理ツール | [ADR 0019](adr/0019-caddy-reverse-proxy.md) |
| 導入済み | caddy/caddy | 自動 HTTPS 対応の Web サーバー | [ADR 0019](adr/0019-caddy-reverse-proxy.md)、[リバースプロキシ・TLS](services/network/reverse-proxy-tls.md) |
| 導入済み | Let's Encrypt | 無料の TLS 証明書（Caddy が DNS-01 で取得。SaaS） | [リバースプロキシ・TLS](services/network/reverse-proxy-tls.md) |
| 計画中 | traefik/traefik | 動的リバースプロキシ・ロードバランサ（`vm-apps` で学習用に試す。Caddy は置き換えない） | [ADR 0019](adr/0019-caddy-reverse-proxy.md)、[未着手の項目](operations/roadmap/01-backlog.md) |

### 4.4 VPN

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 見送り | WireGuard | 軽量 VPN プロトコル | [ADR 0005](adr/0005-tailscale-only-remote-access.md) |
| 導入済み | Tailscale | WireGuard ベースのメッシュ VPN | [ADR 0005](adr/0005-tailscale-only-remote-access.md) |
| 未検討 | OpenVPN | オープンソース VPN | — |

### 4.5 ネットワーク管理

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | Ubiquiti UniFi | ネットワーク機器・管理プラットフォーム | — |
| 計画中 | TP-Link Omada | ネットワーク機器・管理プラットフォーム | [Omada 導入・VLAN 化](operations/roadmap/04-network-omada-vlan.md)。コントローラーは `vm-omada` で稼働中（2026-11-03、[インフラ構成](architecture/02-infrastructure.md)）。ER605・SG2210P の本設置はこれから（[移行計画](operations/roadmap/10-er605-sg2210p-migration-plan.md)） |
| 未検討 | terraform-provider-omada（コミュニティ製） | Omada の設定を Terraform で管理する | [バックログ](operations/roadmap/01-backlog.md)。対応範囲は未確認。公式のプロバイダーはない |
| 検討中 | Omada Cloud | Omada コントローラーをクラウド経由で開く機能 | 2026-11-03 から有効にして試用中。最終的に無効にするかもしれない（[検討中の項目](operations/roadmap/01-backlog.md)） |
| 未検討 | LibreNMS | ネットワーク監視 (SNMP) | — |
| 廃止 | Scanopy | ネットワーク探索・トポロジー図の自動作成 | [見送り中の項目](operations/roadmap/03-deferred.md#scanopyネットワーク探索トポロジー図) |
| 未検討 | nmap | ネットワーク・ポートのスキャン | — |
| 未検討 | NetAlertX | ネットワーク上の端末の検出と新規端末の通知 | — |
| 未検討 | netbox-community/netbox | IPAM / DCIM（IP アドレス・機器の台帳） | — |
| 未検討 | Custom WiFi Monitor | Wi-Fi の電波状況・接続端末を監視する自作ツール（Wi-Fi 経由の速度・遅延の自動測定にも使う案） | [Wi-Fi 経由の測定](services/platform/monitoring.md#wi-fi-経由の測定未実装) |
| 未検討 | Pi.Alert (PiAlert) | ネットワーク上の端末の検出と新規端末の通知（NetAlertX の前身） | — |

---

## 5. ストレージ & バックアップ (Storage & Backup)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 計画中 | truenas/core | NAS 用オープンソース OS | [未着手の項目](operations/roadmap/01-backlog.md) |
| 未検討 | nextcloud/nextcloud | セルフホスト型クラウドストレージ | — |
| 未検討 | linuxserver/duplicati | バックアップ・リストア | — |
| 未検討 | linuxserver/syncthing | P2P ファイル同期 | — |
| 検討中 | Proxmox Backup Server (PBS) | Proxmox 向けの差分バックアップ（NAS 導入後に見直す） | [ADR 0001](adr/0001-no-vm-backup.md) |
| 検討中 | restic | 暗号化・重複排除つきの CLI バックアップ（NAS 導入後に見直す） | [ADR 0001](adr/0001-no-vm-backup.md) |
| 未検討 | borgbackup/borg | 重複排除つきのバックアップ | — |
| 未検討 | kopia/kopia | 暗号化・重複排除つきのバックアップ（Web UI あり） | — |
| 未検討 | rclone/rclone | クラウドストレージとの同期・転送 | — |
| 未検討 | copyparty | ファイルサーバー（ブラウザからのアップロード・共有） | — |
| 未検討 | OpenMediaVault (OMV) | Debian ベースの NAS 用 OS | — |
| 未検討 | filebrowser/filebrowser | Web ブラウザで操作するファイルマネージャ（NAS 向け） | — |
| 未検討 | kern/filepizza | ブラウザ間の P2P ファイル転送 | — |
| 未検討 | plexdrive | クラウドストレージを Plex 向けにマウントする | — |

---

## 6. データベース (Database)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | postgres/postgres | リレーショナルデータベース | — |
| 未検討 | clickhouse/clickhouse-server | 列指向分析用 DB | — |
| 見送り | influxdata/influxdb | 時系列データベース | [見送り中の項目](operations/roadmap/03-deferred.md#方針のない候補) |

---

## 7. 監視 & 可観測性 (Monitoring & Observability)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | prom/prometheus | メトリクス収集・アラート | [監視・アラート](services/platform/monitoring.md) |
| 導入済み | prom/alertmanager | アラート管理・通知 | [監視・アラート](services/platform/monitoring.md) |
| 導入済み | prom/node-exporter | Prometheus 用ホストメトリクス | [監視・アラート](services/platform/monitoring.md) |
| 導入済み | prom/blackbox-exporter | Blackbox プローブ（HTTP/HTTPS/DNS/TCP 等） | [監視・アラート](services/platform/monitoring.md) |
| 導入済み | grafana/grafana | ダッシュボード・可視化 | [監視・アラート](services/platform/monitoring.md) |
| 見送り | grafana/loki | ログ集約・検索 | [見送り中の項目](operations/roadmap/03-deferred.md#loki--grafana-alloyログ収集基盤) |
| 見送り | grafana/promtail | Loki 用ログ収集エージェント | [見送り中の項目](operations/roadmap/03-deferred.md#loki--grafana-alloyログ収集基盤) |
| 見送り | influxdata/telegraf | メトリクス・ログ収集エージェント | [見送り中の項目](operations/roadmap/03-deferred.md#方針のない候補) |
| 見送り | louislam/uptime-kuma | サービス稼働監視・ステータスページ | [見送り中の項目](operations/roadmap/03-deferred.md#uptime-kuma) |
| 未検討 | binwiederhier/ntfy | セルフホストのプッシュ通知（Alertmanager・n8n の通知先） | — |
| 未検討 | gotify/server | セルフホストのプッシュ通知 | — |
| 未検討 | prometheus-community/smartctl_exporter | ディスクの SMART 情報を Prometheus に出す | — |
| 未検討 | allinurl/goaccess | Web サーバーのアクセスログのリアルタイム解析（Caddy / nginx のログ向け） | — |
| 未検討 | AnalogJ/scrutiny | ディスクの SMART 情報の Web ダッシュボード・故障予兆の検知 | — |
| 見送り | miguelndecarvalho/speedtest-exporter | インターネット回線速度の定期測定（Ookla Speedtest CLI）を Prometheus に出す。scrape のたびに回線を使い切り、時間帯を指定できない | [見送り中の項目](operations/roadmap/03-deferred.md#回線速度の定期測定speedtest) |
| 未検討 | iperf3_exporter | iperf3 で LAN 内の速度を測り Prometheus に出す（回線速度の監視の LAN 拡張用） | [家庭内 LAN への拡張](services/platform/monitoring.md#家庭内-lan-への拡張未実装) |
| 未検討 | gnmyt/myspeed | インターネット回線速度の定期測定・履歴表示（Prometheus・Alertmanager に載らない） | — |
| 未検討 | librespeed/speedtest | セルフホストの回線速度テスト（LAN 内の速度測定にも使える） | — |
| 未検討 | oss/smokeping | ネットワークの遅延・パケットロスの長期グラフ化 | — |
| 未検討 | statping-ng/statping-ng | サービス稼働監視・ステータスページ | — |
| 未検討 | Monit | プロセス・ファイル・ホストの監視と自動復旧 | — |
| 未検討 | Zabbix | エージェント型の統合監視プラットフォーム | — |
| 検討中 | google/cadvisor | コンテナごとのリソース使用量メトリクス（Prometheus 連携可）。`vm-omada` だけに入れる案。同じコンテナ内の Java と MongoDB は分けられない | [未着手の項目](operations/roadmap/01-backlog.md) |
| 未検討 | ncabatoff/process-exporter | プロセス名ごとの CPU・メモリを Prometheus に出す。`vm-omada` で、Java と MongoDB を分けて見る案（cAdvisor の代案） | [未着手の項目](operations/roadmap/01-backlog.md) |
| 未検討 | NUT (Network UPS Tools) | UPS の監視と自動シャットダウン（UPS 導入が前提） | [未着手の項目](operations/roadmap/01-backlog.md) |
| 導入済み | Slack | Alertmanager の通知先（SaaS） | [監視・アラート](services/platform/monitoring.md) |
| 導入済み | healthchecks.io | 外部 Heartbeat（Alertmanager の Watchdog が途絶えたら通知。SaaS） | [ADR 0010](adr/0010-external-heartbeat.md) |
| 未検討 | linuxserver/tautulli | Plex 利用状況監視 | — |
| 見送り | nicolargo/glances | システムリソース監視（CPU・メモリ・ディスク・ネットワーク） | [見送り中の項目](operations/roadmap/03-deferred.md#glanceshomepage-の-vm-別バー表示) |
| 未検討 | netdata/netdata | リアルタイムのシステム監視 | — |

---

## 8. セキュリティ & アイデンティティ (Security & Identity)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 見送り | authelia/authelia | SSO・2FA 認証プロキシ（Caddy forward_auth 経由で Grafana/PVE/AdGuardHome 等のログインを一元化する案。見送り） | [ADR 0008](adr/0008-no-authelia.md) |
| 未検討 | goauthentik/authentik | オープンソース SSO・アイデンティティプロバイダー（IdP） | — |
| 未検討 | vaultwarden/server | Bitwarden 互換パスワードマネージャ | — |
| 未検討 | crowdsecurity/crowdsec | 侵入検知・ファイアウォール | — |
| 未検討 | gravitational/teleport | セキュアなインフラアクセス | — |
| 検討中 | cloudflare/cloudflared | Cloudflare Tunnel（セキュアリモートアクセス） | [ADR 0005](adr/0005-tailscale-only-remote-access.md) |
| 導入済み | SOPS + age | シークレットの暗号化（Git に暗号化して置く） | [シークレット管理](operations/runbooks/03-secrets.md) |
| 未検討 | Wazuh | HIDS / SIEM（ホストの侵入検知・ログ分析） | — |
| 未検討 | fail2ban/fail2ban | ログイン失敗の多い IP の遮断 | — |
| 未検討 | aquasecurity/trivy | コンテナイメージ・設定の脆弱性スキャン | — |
| 未検討 | stamparm/maltrail | 悪性トラフィック（既知の不審な通信先）の検知 | — |

---

## 9. メディア & エンターテインメント (Media & Entertainment)

### 9.1 メディアサーバー

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 検討中 | jellyfin/jellyfin | オープンソースメディアサーバー | [未着手の項目](operations/roadmap/01-backlog.md) |
| 検討中 | plexinc/pms-docker | メディアサーバー | [未着手の項目](operations/roadmap/01-backlog.md) |
| 検討中 | emby/embyserver | メディアサーバー | [未着手の項目](operations/roadmap/01-backlog.md) |
| 未検討 | gotson/komga | コミック・漫画サーバー | — |
| 未検討 | stashapp/stash | メディアコレクションの整理・タグ付け | — |
| 未検討 | airsonic/airsonic | 音楽ストリーミングサーバー | — |

### 9.2 メディア取得・管理

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | linuxserver/radarr | 映画の自動取得・管理 | — |
| 未検討 | linuxserver/sonarr | TV 番組の自動取得・管理 | — |
| 未検討 | linuxserver/prowlarr | インデクサー・トラッカーマネージャ | — |
| 未検討 | linuxserver/jackett | トラッカー・プロキシ | — |
| 未検討 | linuxserver/bazarr | 字幕の自動取得 | — |
| 未検討 | linuxserver/ombi | メディアリクエスト UI | — |
| 未検討 | CouchPotato | 映画の自動取得・管理（Radarr の前身） | — |
| 未検討 | darkalfx/requestrr | Discord から映画・TV 番組をリクエストする Bot | — |
| 未検討 | lordmyrdal/plexrequests | Plex 向けのメディアリクエスト UI | — |
| 未検討 | fallenbagel/jellyseerr | Jellyfin / Plex / Emby 向けのメディアリクエスト UI | — |
| 未検討 | revenz/fileflows | メディアファイルの自動変換・処理（エンコード、整理） | — |

### 9.3 ダウンロード

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | haugene/transmission-openvpn | Transmission + OpenVPN | — |
| 未検討 | AllTube | 動画サイトの動画をブラウザからダウンロードする（youtube-dl の Web UI） | — |
| 未検討 | YT Downloads | YouTube 動画のダウンロードツール | — |
| 未検討 | pyload/pyload | ダウンロードマネージャ（Web UI あり） | — |
| 未検討 | linuxserver/deluge | BitTorrent クライアント（Web UI あり） | — |
| 未検討 | binhex/arch-delugevpn | Deluge + VPN | — |
| 未検討 | binhex/arch-sabnzbd | Usenet クライアント | — |

### 9.4 地上波・IP 放送

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | linuxserver/tvheadend | DVB チューナー・ストリーミング | — |
| 未検討 | prengineer/tvhproxy | TVheadend プロキシ | — |
| 未検討 | mirakurun/mirakurun | 日本の地上波チューナー | — |
| 未検討 | epgstation/epgstation | 日本の地上波録画・視聴 | — |

### 9.5 写真・ドキュメント

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | immichapp/immich | セルフホスト型写真管理 | — |
| 未検討 | paperless-ngx/paperless-ngx | ドキュメント管理・アーカイブ | — |

---

## 10. スマートホーム & IoT (Smart Home & IoT)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | homeassistant/home-assistant | スマートホーム統合プラットフォーム | [Home Assistant](services/apps/home-assistant.md) |
| 計画中 | blakeblackshear/frigate | NVR・AI 物体検知 | [未着手の項目](operations/roadmap/01-backlog.md) |
| 未検討 | koush/scrypted | カメラ・デバイスの HomeKit ブリッジ | — |
| 未検討 | oznu/homebridge | HomeKit ブリッジ | — |
| 計画中 | eclipse-mosquitto/eclipse-mosquitto | MQTT ブローカー | [未着手の項目](operations/roadmap/01-backlog.md) |
| 未検討 | nodered/node-red | フローベースの自動化・IoT 連携 | — |
| 未検討 | OctoPrint | 3D プリンターの Web 管理・遠隔操作 | — |
| 未検討 | AlarmPi | Raspberry Pi で作る目覚まし時計・アラーム | — |
| 未検討 | BrewPi | 自家醸造（ビール）の温度制御・ログ | — |
| 見送り | Home Assistant Operating System (HAOS) | Home Assistant 専用 OS（アドオン対応。Container 版を採用） | [ADR 0011](adr/0011-home-assistant-on-vm-apps.md) |

---

## 11. 通信 (Communication)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | FreePBX | オープンソース VoIP PBX | — |
| 未検討 | 3CX | VoIP PBX | — |
| 未検討 | bytemark/smtp | SMTP メールサーバー | — |

---

## 12. ダッシュボード & 管理 (Dashboard & Management)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | gethomepage/homepage | ホームラボ用ダッシュボード | [Homepage](services/apps/homepage.md) |
| 未検討 | linuxserver/heimdall | アプリケーションランチャー | — |
| 未検討 | fenruscn/fenrus | ダッシュボード・ブックマーク | — |
| 未検討 | glanceapp/glance | フィード・天気・監視をまとめて表示する軽量ダッシュボード | — |

---

## 13. 開発 & 生産性 (Development & Productivity)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 導入済み | coder/code-server | ブラウザ版 VS Code | [vm-code](services/dev/vm-code.md) |
| 未検討 | oznu/guacamole | ブラウザベースのリモートデスクトップ | — |
| 未検討 | ich777/krusader | ファイルマネージャ | — |
| 導入済み | siteboon/claudecodeui | Claude Code をリモート管理する Web UI（CloudCLI UI） | [vm-code](services/dev/vm-code.md) |
| 導入済み | n8n-io/n8n | ワークフロー自動化 | [n8n](services/apps/n8n.md) |
| 未検討 | Renovate | 依存・Docker イメージのバージョン更新の自動 PR | — |
| 未検討 | Dependabot | GitHub 標準の依存更新の自動 PR | — |
| 導入済み | mosh | 切れにくい SSH 代替（`vm-code` で利用） | [vm-code](services/dev/vm-code.md) |
| 導入済み | GitHub CLI (gh) | GitHub 操作の CLI（`vm-code` で利用） | [vm-code](services/dev/vm-code.md) |
| 導入済み | freshrss/freshrss | RSS リーダー | [FreshRSS](services/apps/freshrss.md) |
| 未検討 | DIYgod/RSSHub | あらゆるサイトの RSS フィードを生成 | — |
| 未検討 | RSSHub Radar | RSSHub のフィードを見つけるブラウザ拡張 | — |
| 未検討 | usememos/memos | セルフホスト型メモ | — |
| 未検討 | go-gitea/gitea | セルフホスト型 Git サービス | — |
| 未検討 | solidnerd/bookstack | Wiki 型のドキュメント管理 | — |
| 導入済み | GitHub Actions | CI（lint のみ） | [CI/CD](services/dev/cicd.md) |

---

## 14. レシピ・ライフスタイル (Lifestyle)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | mealie-mealie/mealie | レシピ管理・メニュープランナー | — |

---

## 15. カメラ・セキュリティ (Camera & Security)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | shinobicctv/shinobi | CCTV・NVR | — |

---

## 16. 分析 & その他 (Analytics & Other)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 未検討 | plausible/analytics | プライバシー重視の Web 分析 | — |
| 未検討 | searxng/searxng | プライバシー重視のメタ検索エンジン（SearX の後継） | — |
| 未検討 | sysadminsmedia/homebox | 家庭用の物品・備品の在庫管理 | — |
| 未検討 | pterodactyl/panel | ゲームサーバーの管理パネル | — |
| 未検討 | AWS（EC2 / Lightsail） | クラウドの VPS。ハニーポットの受け口（VPS からトンネルで自宅の DMZ へ転送）や外部監視の候補。利用規約でハニーポットが許されるかを確認する（[DMZ と外部公開](operations/roadmap/07-dmz.md)） | — |
| 未検討 | Oracle Cloud Always Free | Oracle Cloud の無料枠 VPS（外部監視の案 C など、外部ホストの候補。[監視・アラート](services/platform/monitoring.md)） | — |
| 未検討 | AltServer | AltStore 用 AltServer（iOS サイドロード） | — |
| 未検討 | AirMessage | iMessage を Android で利用 | — |

---

## 17. 通信分析 (Network Traffic Analysis)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 計画中 | ntopng/ntopng | フロー・パケットの可視化（端末ごとのアクセス先、通信量） | [通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md) |
| 計画中 | tcpdump | パケットキャプチャ | [通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md) |
| 計画中 | tshark / Wireshark | パケットの詳細解析（tshark は CLI 版） | [通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md) |
| 検討中 | Arkime | PCAP の保存と検索 | [通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md) |
| 検討中 | Zeek | プロトコルごとの接続・DNS・TLS のログ生成 | [通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md) |
| 検討中 | Suricata | IDS（不審な通信の検出） | [通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md) |
| 未検討 | Malcolm | Zeek・Suricata・Arkime などを統合した通信解析基盤 | — |

根拠: [ネットワーク通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md)

---

## 18. ハニーポット (Honeypot)

| 状況 | ツール | 説明 | 根拠・備考 |
| --- | --- | --- | --- |
| 計画中 | Cowrie | SSH / Telnet のハニーポット | [DMZ と外部公開](operations/roadmap/07-dmz.md) |
| 検討中 | T-Pot | 複数のハニーポットを統合したプラットフォーム | [DMZ と外部公開](operations/roadmap/07-dmz.md) |
| 検討中 | Dionaea | サービスへの攻撃とマルウェアを収集するハニーポット | [DMZ と外部公開](operations/roadmap/07-dmz.md) |
| 未検討 | Snare / Tanner | Web アプリを模倣するハニーポット（HTTP 系の攻撃を記録） | [DMZ と外部公開](operations/roadmap/07-dmz.md) |
| 未検討 | OpenCanary | 内部ネットワーク向けの検知用ハニーポット（触られたら通知） | [DMZ と外部公開](operations/roadmap/07-dmz.md) |

根拠: [DMZ と外部公開](operations/roadmap/07-dmz.md)

---

## 役割別の採用状況

同じ役割のツールを並べて、何を採用し、何を見送ったかを一目で分かるようにした表。

| 役割 | 採用 | 他の候補（状況） |
| --- | --- | --- |
| ハイパーバイザー | Proxmox VE | XCP-ng、Harvester（未検討） |
| リバースプロキシ | Caddy（[ADR 0019](adr/0019-caddy-reverse-proxy.md)） | Nginx Proxy Manager、nginx（見送り）、Traefik（計画中。学習用に併設） |
| DNS | AdGuard Home + CoreDNS + Unbound（[ADR 0020](adr/0020-dns-three-layer-stack.md)） | Pi-hole、Technitium DNS Server、BIND9（いずれも見送り） |
| リモートアクセス | Tailscale | WireGuard（見送り）、OpenVPN（未検討）、Omada Cloud（検討中。Omada コントローラーの管理画面だけ） |
| メトリクス監視 | Prometheus + Grafana | Netdata（未検討）、Glances・Telegraf + InfluxDB（見送り） |
| コンテナ・プロセス別のメモリ監視 | 未決定（`vm-omada` だけ。検討中: cAdvisor、process-exporter） | 入れずに `docker stats` で見る案もある |
| 回線の疎通・遅延の監視 | blackbox-exporter（ICMP）+ Prometheus + Grafana（計画中） | Speedtest 系: speedtest-exporter（見送り）、MySpeed、LibreSpeed（未検討） |
| 死活監視・ステータスページ | blackbox-exporter + Alertmanager | Uptime Kuma（見送り） |
| ログ集約 | なし（journald と Docker のログ） | Loki + Alloy（見送り） |
| コンテナ管理 | Docker Compose | Portainer（見送り）、k3s（検討中） |
| VM の OS | Ubuntu Server LTS（[ADR 0021](adr/0021-ubuntu-lts-for-vms.md)） | Debian（見送り）、Arch、openSUSE（未検討） |
| VM イメージ | Terraform + cloud-init | Packer（見送り） |
| 認証の一元化 | なし（各サービスのログイン） | Authelia（見送り）、authentik（未検討） |
| バックアップ | なし（[ADR 0001](adr/0001-no-vm-backup.md)） | PBS、restic（検討中）、borg、kopia（未検討） |
| ネットワーク探索 | なし | Scanopy（廃止）、nmap、NetAlertX、NetBox（未検討） |
| メディアサーバー | なし | Jellyfin、Plex、Emby（検討中） |
| ホームオートメーション | Home Assistant（Container 版） | HAOS（見送り） |
| RSS | FreshRSS | RSSHub（未検討） |
| ダッシュボード | Homepage | Glance、Heimdall、Fenrus（未検討） |
| メディアリクエスト | なし | Jellyseerr、Ombi、Requestrr、Plex Requests（未検討） |
