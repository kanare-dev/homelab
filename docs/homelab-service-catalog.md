# HomeLab Service Catalog

ホームラボで利用するツール・サービスをカテゴリ別に整理したカタログです。候補集であり、このリポジトリの構成そのものではありません。各ツールの「状況」で、採用の度合いを示します。

## カテゴリ一覧

| # | カテゴリ |
| --- | --- |
| 1 | ハードウェア |
| 2 | コンピュート & 仮想化 |
| 3 | オペレーティングシステム |
| 4 | ネットワーク |
| 5 | ストレージ & バックアップ |
| 6 | データベース |
| 7 | 監視 & 可観測性 |
| 8 | セキュリティ & アイデンティティ |
| 9 | メディア & エンターテインメント |
| 10 | スマートホーム & IoT |
| 11 | 通信 |
| 12 | ダッシュボード & 管理 |
| 13 | 開発 & 生産性 |
| 14 | レシピ・ライフスタイル |
| 15 | カメラ・セキュリティ |
| 16 | 分析 & その他 |
| 17 | 通信分析 |
| 18 | ハニーポット |

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

構成を変えたら、この状況も同じ変更で更新する。

---

## 1. ハードウェア (Hardware)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | Lenovo ThinkCentre Tiny | 省スペース型デスクトップ PC |
| 未検討 | Dell Optiplex Micro | 省スペース型デスクトップ PC |
| 未検討 | HP EliteDesk Mini | 省スペース型デスクトップ PC |
| 未検討 | Raspberry Pi | シングルボードコンピュータ |
| 未検討 | RTL-SDR | USB 接続のソフトウェア無線レシーバー（電波の受信・解析） |

---

## 2. コンピュート & 仮想化 (Compute & Virtualization)

### 2.1 ハイパーバイザー (Hypervisor)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | Proxmox VE | オープンソースの仮想化・コンテナ基盤 |
| 未検討 | XCP-ng | Xen ベースのオープンソースハイパーバイザー |
| 未検討 | Harvester | Rancher 製 Kubernetes ネイティブハイパーバイザー |

### 2.2 Kubernetes

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 検討中 | k3s | 軽量 Kubernetes ディストリビューション |
| 未検討 | k0s | ゼロフリック Kubernetes ディストリビューション |
| 未検討 | MicroK8s | Canonical 製軽量 Kubernetes |
| 未検討 | Talos | イミュータブル OS ベースの Kubernetes |
| 未検討 | Kubeadm | 公式 Kubernetes クラスタ構築ツール |

### 2.3 ワークロードオーケストレーション（Kubernetes 外）

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | Nomad | HashiCorp 製ワークロードオーケストレーター |

### 2.4 Kubernetes ツール

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | Helm | Kubernetes パッケージマネージャ |
| 未検討 | Rancher | Kubernetes クラスタ管理 UI |
| 未検討 | Longhorn | Kubernetes 向け分散ストレージ |

### 2.5 コンテナランタイム

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | Docker | コンテナランタイム・デーモン |
| 未検討 | containerd | OCI 準拠コンテナランタイム |
| 未検討 | nerdctl | containerd 向け Docker 互換 CLI |
| 未検討 | Podman | daemon レス・ルートレス対応コンテナツール |

### 2.6 仮想化補助ツール

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | Cockpit | サーバー管理 Web UI |
| 未検討 | virt-manager | 仮想マシン管理 GUI |
| 未検討 | libvirt | 仮想化管理 API・ライブラリ |
| 導入済み | Terraform | 宣言型インフラ管理 |
| 導入済み | Ansible | 構成管理・自動化 |

### 2.7 VM テンプレート・プロビジョニング

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 見送り | Packer | マルチクラウド対応 VM イメージビルダー |
| 導入済み | cloud-init | クラウド / VM 初回起動時の初期化 |

### 2.8 コンテナ管理

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 見送り | portainer/portainer-ce | Docker / Kubernetes 管理 UI |
| 未検討 | containerrr/watchtower | コンテナイメージの自動更新 |

---

## 3. オペレーティングシステム (OS)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | Ubuntu | Debian 系 Linux ディストリビューション |
| 未検討 | Debian | 汎用 Linux ディストリビューション |
| 未検討 | Arch | ロールリリース型 Linux ディストリビューション |
| 未検討 | openSUSE | SUSE 系 Linux ディストリビューション |

---

## 4. ネットワーク (Network)

### 4.1 ルーター / ファイアウォール

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 計画中 | OPNSense | オープンソースファイアウォール・ルーター |
| 未検討 | pfSense | オープンソースファイアウォール・ルーター |

### 4.2 DNS

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | Unbound DNS | 軽量キャッシュ DNS リゾルバ |
| 導入済み | CoreDNS | Kubernetes 向けプラグイン型 DNS |
| 未検討 | pi-hole/pi-hole | 広告ブロック DNS |
| 導入済み | adguard/adguardhome | 広告・トラッキングブロック DNS |
| 導入済み | Cloudflare DNS | 公開ドメインの DNS と API（Caddy の DNS-01 証明書に利用。SaaS） |

### 4.3 リバースプロキシ

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | nginx/nginx | Web サーバー・リバースプロキシ |
| 未検討 | jc21/nginx-proxy-manager | Nginx の Web UI 管理ツール |
| 導入済み | caddy/caddy | 自動 HTTPS 対応の Web サーバー |
| 導入済み | Let's Encrypt | 無料の TLS 証明書（Caddy が DNS-01 で取得。SaaS） |
| 見送り | traefik/traefik | 動的リバースプロキシ・ロードバランサ |

### 4.4 VPN

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 見送り | WireGuard | 軽量 VPN プロトコル |
| 導入済み | Tailscale | WireGuard ベースのメッシュ VPN |
| 未検討 | OpenVPN | オープンソース VPN |

### 4.5 ネットワーク管理

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | Ubiquiti UniFi | ネットワーク機器・管理プラットフォーム |
| 計画中 | TP-Link Omada | ネットワーク機器・管理プラットフォーム |
| 未検討 | LibreNMS | ネットワーク監視 (SNMP) |

---

## 5. ストレージ & バックアップ (Storage & Backup)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 計画中 | truenas/core | NAS 用オープンソース OS |
| 未検討 | nextcloud/nextcloud | セルフホスト型クラウドストレージ |
| 未検討 | linuxserver/duplicati | バックアップ・リストア |
| 未検討 | linuxserver/syncthing | P2P ファイル同期 |
| 検討中 | Proxmox Backup Server (PBS) | Proxmox 向けの差分バックアップ（[ADR 0001](adr/0001-no-vm-backup.md)。NAS 導入後に見直す） |
| 検討中 | restic | 暗号化・重複排除つきの CLI バックアップ（[ADR 0001](adr/0001-no-vm-backup.md)。NAS 導入後に見直す） |
| 未検討 | borgbackup/borg | 重複排除つきのバックアップ |
| 未検討 | kopia/kopia | 暗号化・重複排除つきのバックアップ（Web UI あり） |
| 未検討 | rclone/rclone | クラウドストレージとの同期・転送 |
| 未検討 | copyparty | ファイルサーバー（ブラウザからのアップロード・共有） |

---

## 6. データベース (Database)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | postgres/postgres | リレーショナルデータベース |
| 未検討 | clickhouse/clickhouse-server | 列指向分析用 DB |
| 見送り | influxdata/influxdb | 時系列データベース |

---

## 7. 監視 & 可観測性 (Monitoring & Observability)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | prom/prometheus | メトリクス収集・アラート |
| 導入済み | prom/alertmanager | アラート管理・通知 |
| 導入済み | prom/node-exporter | Prometheus 用ホストメトリクス |
| 導入済み | prom/blackbox-exporter | Blackbox プローブ（HTTP/HTTPS/DNS/TCP 等） |
| 導入済み | grafana/grafana | ダッシュボード・可視化 |
| 見送り | grafana/loki | ログ集約・検索 |
| 見送り | grafana/promtail | Loki 用ログ収集エージェント |
| 見送り | influxdata/telegraf | メトリクス・ログ収集エージェント |
| 見送り | louislam/uptime-kuma | サービス稼働監視・ステータスページ |
| 未検討 | binwiederhier/ntfy | セルフホストのプッシュ通知（Alertmanager・n8n の通知先） |
| 未検討 | gotify/server | セルフホストのプッシュ通知 |
| 未検討 | prometheus-community/smartctl_exporter | ディスクの SMART 情報を Prometheus に出す |
| 未検討 | NUT (Network UPS Tools) | UPS の監視と自動シャットダウン（UPS 導入が前提。[未着手の項目](operations/roadmap/01-backlog.md)） |
| 導入済み | Slack | Alertmanager の通知先（SaaS） |
| 導入済み | healthchecks.io | 外部 Heartbeat（Alertmanager の Watchdog が途絶えたら通知。SaaS） |
| 未検討 | linuxserver/tautulli | Plex 利用状況監視 |
| 見送り | nicolargo/glances | システムリソース監視（CPU・メモリ・ディスク・ネットワーク） |
| 未検討 | netdata/netdata | リアルタイムのシステム監視 |

---

## 8. セキュリティ & アイデンティティ (Security & Identity)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 見送り | authelia/authelia | SSO・2FA 認証プロキシ（Caddy forward_auth 経由で Grafana/PVE/AdGuardHome 等のログインを一元化する案。[ADR 0008](adr/0008-no-authelia.md) で見送り） |
| 未検討 | goauthentik/authentik | オープンソース SSO・アイデンティティプロバイダー（IdP） |
| 未検討 | vaultwarden/server | Bitwarden 互換パスワードマネージャ |
| 未検討 | crowdsecurity/crowdsec | 侵入検知・ファイアウォール |
| 未検討 | gravitational/teleport | セキュアなインフラアクセス |
| 検討中 | cloudflare/cloudflared | Cloudflare Tunnel（セキュアリモートアクセス） |
| 導入済み | SOPS + age | シークレットの暗号化（Git に暗号化して置く） |
| 未検討 | Wazuh | HIDS / SIEM（ホストの侵入検知・ログ分析） |
| 未検討 | fail2ban/fail2ban | ログイン失敗の多い IP の遮断 |
| 未検討 | aquasecurity/trivy | コンテナイメージ・設定の脆弱性スキャン |

---

## 9. メディア & エンターテインメント (Media & Entertainment)

### 9.1 メディアサーバー

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 検討中 | jellyfin/jellyfin | オープンソースメディアサーバー |
| 検討中 | plexinc/pms-docker | メディアサーバー |
| 検討中 | emby/embyserver | メディアサーバー |
| 未検討 | gotson/komga | コミック・漫画サーバー |
| 未検討 | stashapp/stash | メディアコレクションの整理・タグ付け |

### 9.2 メディア取得・管理

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | linuxserver/radarr | 映画の自動取得・管理 |
| 未検討 | linuxserver/sonarr | TV 番組の自動取得・管理 |
| 未検討 | linuxserver/prowlarr | インデクサー・トラッカーマネージャ |
| 未検討 | linuxserver/jackett | トラッカー・プロキシ |
| 未検討 | linuxserver/bazarr | 字幕の自動取得 |
| 未検討 | linuxserver/ombi | メディアリクエスト UI |

### 9.3 ダウンロード

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | haugene/transmission-openvpn | Transmission + OpenVPN |
| 未検討 | binhex/arch-delugevpn | Deluge + VPN |
| 未検討 | binhex/arch-sabnzbd | Usenet クライアント |

### 9.4 地上波・IP 放送

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | linuxserver/tvheadend | DVB チューナー・ストリーミング |
| 未検討 | prengineer/tvhproxy | TVheadend プロキシ |
| 未検討 | mirakurun/mirakurun | 日本の地上波チューナー |
| 未検討 | epgstation/epgstation | 日本の地上波録画・視聴 |

### 9.5 写真・ドキュメント

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | immichapp/immich | セルフホスト型写真管理 |
| 未検討 | paperless-ngx/paperless-ngx | ドキュメント管理・アーカイブ |

---

## 10. スマートホーム & IoT (Smart Home & IoT)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | homeassistant/home-assistant | スマートホーム統合プラットフォーム |
| 計画中 | blakeblackshear/frigate | NVR・AI 物体検知 |
| 未検討 | koush/scrypted | カメラ・デバイスの HomeKit ブリッジ |
| 未検討 | oznu/homebridge | HomeKit ブリッジ |
| 計画中 | eclipse-mosquitto/eclipse-mosquitto | MQTT ブローカー |
| 見送り | Home Assistant Operating System (HAOS) | Home Assistant 専用 OS（アドオン対応。[ADR 0011](adr/0011-home-assistant-on-vm-apps.md) の代替案。Container 版を採用） |

---

## 11. 通信 (Communication)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | FreePBX | オープンソース VoIP PBX |
| 未検討 | 3CX | VoIP PBX |
| 未検討 | bytemark/smtp | SMTP メールサーバー |

---

## 12. ダッシュボード & 管理 (Dashboard & Management)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | gethomepage/homepage | ホームラボ用ダッシュボード |
| 未検討 | linuxserver/heimdall | アプリケーションランチャー |
| 未検討 | fenruscn/fenrus | ダッシュボード・ブックマーク |

---

## 13. 開発 & 生産性 (Development & Productivity)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 導入済み | coder/code-server | ブラウザ版 VS Code |
| 未検討 | oznu/guacamole | ブラウザベースのリモートデスクトップ |
| 未検討 | ich777/krusader | ファイルマネージャ |
| 導入済み | siteboon/claudecodeui | Claude Code をリモート管理する Web UI（CloudCLI UI） |
| 導入済み | n8n-io/n8n | ワークフロー自動化 |
| 未検討 | Renovate | 依存・Docker イメージのバージョン更新の自動 PR |
| 未検討 | Dependabot | GitHub 標準の依存更新の自動 PR |
| 導入済み | mosh | 切れにくい SSH 代替（`vm-code` で利用） |
| 導入済み | GitHub CLI (gh) | GitHub 操作の CLI（`vm-code` で利用） |
| 導入済み | freshrss/freshrss | RSS リーダー |
| 未検討 | DIYgod/RSSHub | あらゆるサイトの RSS フィードを生成 |
| 未検討 | RSSHub Radar | RSSHub のフィードを見つけるブラウザ拡張 |
| 未検討 | usememos/memos | セルフホスト型メモ |
| 導入済み | GitHub Actions | CI（lint のみ） |

---

## 14. レシピ・ライフスタイル (Lifestyle)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | mealie-mealie/mealie | レシピ管理・メニュープランナー |

---

## 15. カメラ・セキュリティ (Camera & Security)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | shinobicctv/shinobi | CCTV・NVR |

---

## 16. 分析 & その他 (Analytics & Other)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 未検討 | plausible/analytics | プライバシー重視の Web 分析 |
| 未検討 | Oracle Cloud Always Free | Oracle Cloud の無料枠 VPS（外部監視の案 C など、外部ホストの候補。[監視・アラート](services/03-monitoring.md)） |
| 未検討 | AltServer | AltStore 用 AltServer（iOS サイドロード） |
| 未検討 | AirMessage | iMessage を Android で利用 |

---

## 17. 通信分析 (Network Traffic Analysis)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 計画中 | ntopng/ntopng | フロー・パケットの可視化（端末ごとのアクセス先、通信量） |
| 計画中 | tcpdump | パケットキャプチャ |
| 計画中 | tshark / Wireshark | パケットの詳細解析（tshark は CLI 版） |
| 検討中 | Arkime | PCAP の保存と検索 |
| 検討中 | Zeek | プロトコルごとの接続・DNS・TLS のログ生成 |
| 検討中 | Suricata | IDS（不審な通信の検出） |
| 未検討 | Malcolm | Zeek・Suricata・Arkime などを統合した通信解析基盤 |

根拠: [ネットワーク通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md)

---

## 18. ハニーポット (Honeypot)

| 状況 | ツール | 説明 |
| --- | --- | --- |
| 計画中 | Cowrie | SSH / Telnet のハニーポット |
| 検討中 | T-Pot | 複数のハニーポットを統合したプラットフォーム |
| 検討中 | Dionaea | サービスへの攻撃とマルウェアを収集するハニーポット |

根拠: [DMZ と外部公開](operations/roadmap/07-dmz.md)
