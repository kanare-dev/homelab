# HomeLab Service Catalog

ホームラボで利用するツール・サービスをカテゴリ別に整理したカタログです。候補集であり、このリポジトリの構成そのものではありません。各ツールの「状況」で、採用の度合いを示します。

## 状況の凡例

| 状況 | 意味 | 根拠 |
| --- | --- | --- |
| 導入済み | 現行構成で稼働している | [インフラ構成](architecture/02-infrastructure.md) |
| 計画中 | 導入を決めて、ロードマップに載せている | [未着手の項目](operations/roadmap/01-backlog.md)、大型計画 |
| 検討中 | 導入するか、条件が整ったら着手するかを検討している | [ロードマップ](operations/roadmap/README.md)、[ADR](adr/README.md) |
| 見送り | 検討して導入しないと決めた | [見送り中の項目](operations/roadmap/03-deferred.md)、[ADR](adr/README.md) |
| 未検討 | 候補として挙げただけで、判断していない | — |

構成を変えたら、この状況も同じ変更で更新する。

---

## 1. ハードウェア (Hardware)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Lenovo ThinkCentre Tiny | 省スペース型デスクトップ PC | 導入済み |
| Dell Optiplex Micro | 省スペース型デスクトップ PC | 未検討 |
| HP EliteDesk Mini | 省スペース型デスクトップ PC | 未検討 |
| Raspberry Pi | シングルボードコンピュータ | 未検討 |
| RTL-SDR | USB 接続のソフトウェア無線レシーバー（電波の受信・解析） | 未検討 |

---

## 2. コンピュート & 仮想化 (Compute & Virtualization)

### 2.1 ハイパーバイザー (Hypervisor)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Proxmox VE | オープンソースの仮想化・コンテナ基盤 | 導入済み |
| XCP-ng | Xen ベースのオープンソースハイパーバイザー | 未検討 |
| Harvester | Rancher 製 Kubernetes ネイティブハイパーバイザー | 未検討 |

### 2.2 Kubernetes

| ツール | 説明 | 状況 |
| --- | --- | --- |
| k3s | 軽量 Kubernetes ディストリビューション | 検討中 |
| k0s | ゼロフリック Kubernetes ディストリビューション | 未検討 |
| MicroK8s | Canonical 製軽量 Kubernetes | 未検討 |
| Talos | イミュータブル OS ベースの Kubernetes | 未検討 |
| Kubeadm | 公式 Kubernetes クラスタ構築ツール | 未検討 |

### 2.3 ワークロードオーケストレーション（Kubernetes 外）

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Nomad | HashiCorp 製ワークロードオーケストレーター | 未検討 |

### 2.4 Kubernetes ツール

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Helm | Kubernetes パッケージマネージャ | 未検討 |
| Rancher | Kubernetes クラスタ管理 UI | 未検討 |
| Longhorn | Kubernetes 向け分散ストレージ | 未検討 |

### 2.5 コンテナランタイム

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Docker | コンテナランタイム・デーモン | 導入済み |
| containerd | OCI 準拠コンテナランタイム | 未検討 |
| nerdctl | containerd 向け Docker 互換 CLI | 未検討 |
| Podman | daemon レス・ルートレス対応コンテナツール | 未検討 |

### 2.6 仮想化補助ツール

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Cockpit | サーバー管理 Web UI | 未検討 |
| virt-manager | 仮想マシン管理 GUI | 未検討 |
| libvirt | 仮想化管理 API・ライブラリ | 未検討 |
| Terraform | 宣言型インフラ管理 | 導入済み |
| Ansible | 構成管理・自動化 | 導入済み |

### 2.7 VM テンプレート・プロビジョニング

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Packer | マルチクラウド対応 VM イメージビルダー | 見送り |
| cloud-init | クラウド / VM 初回起動時の初期化 | 導入済み |

### 2.8 コンテナ管理

| ツール | 説明 | 状況 |
| --- | --- | --- |
| portainer/portainer-ce | Docker / Kubernetes 管理 UI | 見送り |
| containerrr/watchtower | コンテナイメージの自動更新 | 未検討 |

---

## 3. オペレーティングシステム (OS)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Ubuntu | Debian 系 Linux ディストリビューション | 導入済み |
| Debian | 汎用 Linux ディストリビューション | 未検討 |
| Arch | ロールリリース型 Linux ディストリビューション | 未検討 |
| openSUSE | SUSE 系 Linux ディストリビューション | 未検討 |

---

## 4. ネットワーク (Network)

### 4.1 ルーター / ファイアウォール

| ツール | 説明 | 状況 |
| --- | --- | --- |
| OPNSense | オープンソースファイアウォール・ルーター | 計画中 |
| pfSense | オープンソースファイアウォール・ルーター | 未検討 |

### 4.2 DNS

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Unbound DNS | 軽量キャッシュ DNS リゾルバ | 導入済み |
| CoreDNS | Kubernetes 向けプラグイン型 DNS | 導入済み |
| pi-hole/pi-hole | 広告ブロック DNS | 未検討 |
| adguard/adguardhome | 広告・トラッキングブロック DNS | 導入済み |

### 4.3 リバースプロキシ

| ツール | 説明 | 状況 |
| --- | --- | --- |
| nginx/nginx | Web サーバー・リバースプロキシ | 未検討 |
| jc21/nginx-proxy-manager | Nginx の Web UI 管理ツール | 未検討 |
| caddy/caddy | 自動 HTTPS 対応の Web サーバー | 導入済み |
| traefik/traefik | 動的リバースプロキシ・ロードバランサ | 見送り |

### 4.4 VPN

| ツール | 説明 | 状況 |
| --- | --- | --- |
| WireGuard | 軽量 VPN プロトコル | 見送り |
| Tailscale | WireGuard ベースのメッシュ VPN | 導入済み |
| OpenVPN | オープンソース VPN | 未検討 |

### 4.5 ネットワーク管理

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Ubiquiti UniFi | ネットワーク機器・管理プラットフォーム | 未検討 |
| TP-Link Omada | ネットワーク機器・管理プラットフォーム | 計画中 |
| LibreNMS | ネットワーク監視 (SNMP) | 未検討 |

---

## 5. ストレージ & バックアップ (Storage & Backup)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| truenas/core | NAS 用オープンソース OS | 計画中 |
| nextcloud/nextcloud | セルフホスト型クラウドストレージ | 未検討 |
| linuxserver/duplicati | バックアップ・リストア | 未検討 |
| linuxserver/syncthing | P2P ファイル同期 | 未検討 |
| copyparty | ファイルサーバー（ブラウザからのアップロード・共有） | 未検討 |

---

## 6. データベース (Database)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| postgres/postgres | リレーショナルデータベース | 未検討 |
| clickhouse/clickhouse-server | 列指向分析用 DB | 未検討 |
| influxdata/influxdb | 時系列データベース | 見送り |

---

## 7. 監視 & 可観測性 (Monitoring & Observability)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| prom/prometheus | メトリクス収集・アラート | 導入済み |
| prom/alertmanager | アラート管理・通知 | 導入済み |
| prom/node-exporter | Prometheus 用ホストメトリクス | 導入済み |
| prom/blackbox-exporter | Blackbox プローブ（HTTP/HTTPS/DNS/TCP 等） | 導入済み |
| grafana/grafana | ダッシュボード・可視化 | 導入済み |
| grafana/loki | ログ集約・検索 | 見送り |
| grafana/promtail | Loki 用ログ収集エージェント | 見送り |
| influxdata/telegraf | メトリクス・ログ収集エージェント | 見送り |
| louislam/uptime-kuma | サービス稼働監視・ステータスページ | 見送り |
| healthchecks.io | 外部 Heartbeat（Alertmanager の Watchdog が途絶えたら通知。SaaS） | 導入済み |
| linuxserver/tautulli | Plex 利用状況監視 | 未検討 |
| nicolargo/glances | システムリソース監視（CPU・メモリ・ディスク・ネットワーク） | 見送り |
| netdata/netdata | リアルタイムのシステム監視 | 未検討 |

---

## 8. セキュリティ & アイデンティティ (Security & Identity)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| authelia/authelia | SSO・2FA 認証プロキシ（Caddy forward_auth 経由で Grafana/PVE/AdGuardHome 等のログインを一元化する案。[ADR 0008](adr/0008-no-authelia.md) で見送り） | 見送り |
| goauthentik/authentik | オープンソース SSO・アイデンティティプロバイダー（IdP） | 未検討 |
| vaultwarden/server | Bitwarden 互換パスワードマネージャ | 未検討 |
| crowdsecurity/crowdsec | 侵入検知・ファイアウォール | 未検討 |
| gravitational/teleport | セキュアなインフラアクセス | 未検討 |
| cloudflare/cloudflared | Cloudflare Tunnel（セキュアリモートアクセス） | 検討中 |
| SOPS + age | シークレットの暗号化（Git に暗号化して置く） | 導入済み |

---

## 9. メディア & エンターテインメント (Media & Entertainment)

### 9.1 メディアサーバー

| ツール | 説明 | 状況 |
| --- | --- | --- |
| jellyfin/jellyfin | オープンソースメディアサーバー | 検討中 |
| plexinc/pms-docker | メディアサーバー | 検討中 |
| emby/embyserver | メディアサーバー | 検討中 |
| gotson/komga | コミック・漫画サーバー | 未検討 |
| stashapp/stash | メディアコレクションの整理・タグ付け | 未検討 |

### 9.2 メディア取得・管理

| ツール | 説明 | 状況 |
| --- | --- | --- |
| linuxserver/radarr | 映画の自動取得・管理 | 未検討 |
| linuxserver/sonarr | TV 番組の自動取得・管理 | 未検討 |
| linuxserver/prowlarr | インデクサー・トラッカーマネージャ | 未検討 |
| linuxserver/jackett | トラッカー・プロキシ | 未検討 |
| linuxserver/bazarr | 字幕の自動取得 | 未検討 |
| linuxserver/ombi | メディアリクエスト UI | 未検討 |

### 9.3 ダウンロード

| ツール | 説明 | 状況 |
| --- | --- | --- |
| haugene/transmission-openvpn | Transmission + OpenVPN | 未検討 |
| binhex/arch-delugevpn | Deluge + VPN | 未検討 |
| binhex/arch-sabnzbd | Usenet クライアント | 未検討 |

### 9.4 地上波・IP 放送

| ツール | 説明 | 状況 |
| --- | --- | --- |
| linuxserver/tvheadend | DVB チューナー・ストリーミング | 未検討 |
| prengineer/tvhproxy | TVheadend プロキシ | 未検討 |
| mirakurun/mirakurun | 日本の地上波チューナー | 未検討 |
| epgstation/epgstation | 日本の地上波録画・視聴 | 未検討 |

### 9.5 写真・ドキュメント

| ツール | 説明 | 状況 |
| --- | --- | --- |
| immichapp/immich | セルフホスト型写真管理 | 未検討 |
| paperless-ngx/paperless-ngx | ドキュメント管理・アーカイブ | 未検討 |

---

## 10. スマートホーム & IoT (Smart Home & IoT)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| homeassistant/home-assistant | スマートホーム統合プラットフォーム | 導入済み |
| blakeblackshear/frigate | NVR・AI 物体検知 | 計画中 |
| koush/scrypted | カメラ・デバイスの HomeKit ブリッジ | 未検討 |
| oznu/homebridge | HomeKit ブリッジ | 未検討 |
| eclipse-mosquitto/eclipse-mosquitto | MQTT ブローカー | 計画中 |
| Home Assistant Operating System (HAOS) | Home Assistant 専用 OS（アドオン対応。[ADR 0011](adr/0011-home-assistant-on-vm-apps.md) の代替案。Container 版を採用） | 見送り |

---

## 11. 通信 (Communication)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| FreePBX | オープンソース VoIP PBX | 未検討 |
| 3CX | VoIP PBX | 未検討 |
| bytemark/smtp | SMTP メールサーバー | 未検討 |

---

## 12. ダッシュボード & 管理 (Dashboard & Management)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| gethomepage/homepage | ホームラボ用ダッシュボード | 導入済み |
| linuxserver/heimdall | アプリケーションランチャー | 未検討 |
| fenruscn/fenrus | ダッシュボード・ブックマーク | 未検討 |

---

## 13. 開発 & 生産性 (Development & Productivity)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| coder/code-server | ブラウザ版 VS Code | 導入済み |
| oznu/guacamole | ブラウザベースのリモートデスクトップ | 未検討 |
| ich777/krusader | ファイルマネージャ | 未検討 |
| siteboon/claudecodeui | Claude Code をリモート管理する Web UI（CloudCLI UI） | 導入済み |
| n8n-io/n8n | ワークフロー自動化 | 導入済み |
| freshrss/freshrss | RSS リーダー | 導入済み |
| DIYgod/RSSHub | あらゆるサイトの RSS フィードを生成 | 未検討 |
| RSSHub Radar | RSSHub のフィードを見つけるブラウザ拡張 | 未検討 |
| usememos/memos | セルフホスト型メモ | 未検討 |
| GitHub Actions | CI（lint のみ） | 導入済み |

---

## 14. レシピ・ライフスタイル (Lifestyle)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| mealie-mealie/mealie | レシピ管理・メニュープランナー | 未検討 |

---

## 15. カメラ・セキュリティ (Camera & Security)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| shinobicctv/shinobi | CCTV・NVR | 未検討 |

---

## 16. 分析 & その他 (Analytics & Other)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| plausible/analytics | プライバシー重視の Web 分析 | 未検討 |
| Oracle Cloud Always Free | Oracle Cloud の無料枠 VPS（外部監視の案 C など、外部ホストの候補。[監視・アラート](services/03-monitoring.md)） | 未検討 |
| AltServer | AltStore 用 AltServer（iOS サイドロード） | 未検討 |
| AirMessage | iMessage を Android で利用 | 未検討 |

---

## 17. 通信分析 (Network Traffic Analysis)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| ntopng/ntopng | フロー・パケットの可視化（端末ごとのアクセス先、通信量） | 計画中 |
| tcpdump | パケットキャプチャ | 計画中 |
| tshark / Wireshark | パケットの詳細解析（tshark は CLI 版） | 計画中 |
| Arkime | PCAP の保存と検索 | 検討中 |
| Zeek | プロトコルごとの接続・DNS・TLS のログ生成 | 検討中 |
| Suricata | IDS（不審な通信の検出） | 検討中 |
| Malcolm | Zeek・Suricata・Arkime などを統合した通信解析基盤 | 未検討 |

根拠: [ネットワーク通信の収集・可視化](operations/roadmap/06-network-traffic-analysis.md)

---

## 18. ハニーポット (Honeypot)

| ツール | 説明 | 状況 |
| --- | --- | --- |
| Cowrie | SSH / Telnet のハニーポット | 計画中 |
| T-Pot | 複数のハニーポットを統合したプラットフォーム | 検討中 |
| Dionaea | サービスへの攻撃とマルウェアを収集するハニーポット | 検討中 |

根拠: [DMZ と外部公開](operations/roadmap/07-dmz.md)

---

## カテゴリ一覧（クイックリファレンス）

| # | カテゴリ |
| --- | --- | --- |
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
