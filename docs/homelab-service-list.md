# HomeLab Service List

ホームラボで利用するツール・サービスをカテゴリ別に整理した一覧です。

---

## 1. ハードウェア (Hardware)

| ツール | 説明 |
|--------|------|
| Lenovo ThinkCentre Tiny | 省スペース型デスクトップ PC |
| Dell Optiplex Micro | 省スペース型デスクトップ PC |
| HP EliteDesk Mini | 省スペース型デスクトップ PC |
| Raspberry Pi | シングルボードコンピュータ |

---

## 2. コンピュート & 仮想化 (Compute & Virtualization)

| ツール | 説明 |
|--------|------|
| Proxmox VE | オープンソースの仮想化・コンテナ基盤 |
| Docker | コンテナランタイム |
| k3s | 軽量 Kubernetes ディストリビューション |
| Rancher | Kubernetes クラスタ管理 UI |
| Helm | Kubernetes パッケージマネージャ |
| Longhorn | Kubernetes 向け分散ストレージ |
| portainer/portainer-ce | Docker / Kubernetes 管理 UI |
| containerrr/watchtower | コンテナイメージの自動更新 |

---

## 3. オペレーティングシステム (OS)

| ツール | 説明 |
|--------|------|
| Ubuntu | Debian 系 Linux ディストリビューション |
| Debian | 汎用 Linux ディストリビューション |
| Arch | ロールリリース型 Linux ディストリビューション |
| openSUSE | SUSE 系 Linux ディストリビューション |

---

## 4. インフラストラクチャ as Code (IaC)

| ツール | 説明 |
|--------|------|
| Terraform | 宣言型インフラ管理 |
| Ansible | 構成管理・自動化 |

---

## 5. ネットワーク (Network)

### 5.1 ルーター / ファイアウォール

| ツール | 説明 |
|--------|------|
| OPNSense | オープンソースファイアウォール・ルーター |
| pfSense | オープンソースファイアウォール・ルーター |

### 5.2 DNS

| ツール | 説明 |
|--------|------|
| Unbound DNS | 軽量キャッシュ DNS リゾルバ |
| CoreDNS | Kubernetes 向けプラグイン型 DNS |
| pi-hole/pi-hole | 広告ブロック DNS |
| adguard/adguardhome | 広告・トラッキングブロック DNS |

### 5.3 リバースプロキシ

| ツール | 説明 |
|--------|------|
| nginx/nginx | Web サーバー・リバースプロキシ |
| jc21/nginx-proxy-manager | Nginx の Web UI 管理ツール |
| caddy/caddy | 自動 HTTPS 対応の Web サーバー |
| traefik/traefik | 動的リバースプロキシ・ロードバランサ |

### 5.4 VPN

| ツール | 説明 |
|--------|------|
| WireGuard | 軽量 VPN プロトコル |
| Tailscale | WireGuard ベースのメッシュ VPN |
| OpenVPN | オープンソース VPN |

### 5.5 ネットワーク管理

| ツール | 説明 |
|--------|------|
| Ubiquiti UniFi | ネットワーク機器・管理プラットフォーム |
| TP-Link Omada | ネットワーク機器・管理プラットフォーム |
| LibreNMS | ネットワーク監視 (SNMP) |

---

## 6. ストレージ & バックアップ (Storage & Backup)

| ツール | 説明 |
|--------|------|
| truenas/core | NAS 用オープンソース OS |
| nextcloud/nextcloud | セルフホスト型クラウドストレージ |
| linuxserver/duplicati | バックアップ・リストア |
| linuxserver/syncthing | P2P ファイル同期 |

---

## 7. データベース (Database)

| ツール | 説明 |
|--------|------|
| postgres/postgres | リレーショナルデータベース |
| clickhouse/clickhouse-server | 列指向分析用 DB |
| influxdata/influxdb | 時系列データベース |

---

## 8. 監視 & 可観測性 (Monitoring & Observability)

| ツール | 説明 |
|--------|------|
| prom/prometheus | メトリクス収集・アラート |
| prom/alertmanager | アラート管理・通知 |
| prom/node-exporter | Prometheus 用ホストメトリクス |
| prom/blackbox-exporter | Blackbox プローブ（HTTP/HTTPS/DNS/TCP 等） |
| grafana/grafana | ダッシュボード・可視化 |
| grafana/loki | ログ集約・検索 |
| grafana/promtail | Loki 用ログ収集エージェント |
| influxdata/telegraf | メトリクス・ログ収集エージェント |
| louislam/uptime-kuma | サービス稼働監視・ステータスページ |
| linuxserver/tautulli | Plex 利用状況監視 |

---

## 9. セキュリティ & アイデンティティ (Security & Identity)

| ツール | 説明 |
|--------|------|
| authelia/authelia | SSO・2FA 認証プロキシ |
| vaultwarden/server | Bitwarden 互換パスワードマネージャ |
| crowdsecurity/crowdsec | 侵入検知・ファイアウォール |
| gravitational/teleport | セキュアなインフラアクセス |
| cloudflare/cloudflared | Cloudflare Tunnel（セキュアリモートアクセス） |

---

## 10. メディア & エンターテインメント (Media & Entertainment)

### 10.1 メディアサーバー

| ツール | 説明 |
|--------|------|
| jellyfin/jellyfin | オープンソースメディアサーバー |
| plexinc/pms-docker | メディアサーバー |
| emby/embyserver | メディアサーバー |

### 10.2 メディア取得・管理

| ツール | 説明 |
|--------|------|
| linuxserver/radarr | 映画の自動取得・管理 |
| linuxserver/sonarr | TV 番組の自動取得・管理 |
| linuxserver/prowlarr | インデクサー・トラッカーマネージャ |
| linuxserver/jackett | トラッカー・プロキシ |
| linuxserver/bazarr | 字幕の自動取得 |
| linuxserver/ombi | メディアリクエスト UI |

### 10.3 ダウンロード

| ツール | 説明 |
|--------|------|
| haugene/transmission-openvpn | Transmission + OpenVPN |
| binhex/arch-delugevpn | Deluge + VPN |
| binhex/arch-sabnzbd | Usenet クライアント |

### 10.4 地上波・IP 放送

| ツール | 説明 |
|--------|------|
| linuxserver/tvheadend | DVB チューナー・ストリーミング |
| prengineer/tvhproxy | TVheadend プロキシ |
| mirakurun/mirakurun | 日本の地上波チューナー |
| epgstation/epgstation | 日本の地上波録画・視聴 |

### 10.5 写真・ドキュメント

| ツール | 説明 |
|--------|------|
| immichapp/immich | セルフホスト型写真管理 |
| paperless-ngx/paperless-ngx | ドキュメント管理・アーカイブ |

---

## 11. スマートホーム & IoT (Smart Home & IoT)

| ツール | 説明 |
|--------|------|
| homeassistant/home-assistant | スマートホーム統合プラットフォーム |
| blakeblackshear/frigate | NVR・AI 物体検知 |
| koush/scrypted | カメラ・デバイスの HomeKit ブリッジ |
| oznu/homebridge | HomeKit ブリッジ |
| eclipse-mosquitto/eclipse-mosquitto | MQTT ブローカー |

---

## 12. 通信 (Communication)

| ツール | 説明 |
|--------|------|
| FreePBX | オープンソース VoIP PBX |
| 3CX | VoIP PBX |
| bytemark/smtp | SMTP メールサーバー |

---

## 13. ダッシュボード & 管理 (Dashboard & Management)

| ツール | 説明 |
|--------|------|
| gethomepage/homepage | ホームラボ用ダッシュボード |
| linuxserver/heimdall | アプリケーションランチャー |
| fenruscn/fenrus | ダッシュボード・ブックマーク |

---

## 14. 開発 & 生産性 (Development & Productivity)

| ツール | 説明 |
|--------|------|
| coder/code-server | ブラウザ版 VS Code |
| oznu/guacamole | ブラウザベースのリモートデスクトップ |
| ich777/krusader | ファイルマネージャ |

---

## 15. レシピ・ライフスタイル (Lifestyle)

| ツール | 説明 |
|--------|------|
| mealie-mealie/mealie | レシピ管理・メニュープランナー |

---

## 16. カメラ・セキュリティ (Camera & Security)

| ツール | 説明 |
|--------|------|
| shinobicctv/shinobi | CCTV・NVR |

---

## 17. 分析 & その他 (Analytics & Other)

| ツール | 説明 |
|--------|------|
| plausible/analytics | プライバシー重視の Web 分析 |
| AltServer | AltStore 用 AltServer（iOS サイドロード） |
| AirMessage | iMessage を Android で利用 |
| stanley | （要確認） |

---

## カテゴリ一覧（クイックリファレンス）

| # | カテゴリ |
|---|----------|
| 1 | ハードウェア |
| 2 | コンピュート & 仮想化 |
| 3 | オペレーティングシステム |
| 4 | IaC |
| 5 | ネットワーク |
| 6 | ストレージ & バックアップ |
| 7 | データベース |
| 8 | 監視 & 可観測性 |
| 9 | セキュリティ & アイデンティティ |
| 10 | メディア & エンターテインメント |
| 11 | スマートホーム & IoT |
| 12 | 通信 |
| 13 | ダッシュボード & 管理 |
| 14 | 開発 & 生産性 |
| 15 | レシピ・ライフスタイル |
| 16 | カメラ・セキュリティ |
| 17 | 分析 & その他 |
