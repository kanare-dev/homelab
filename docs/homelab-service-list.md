# HomeLab Service List

ホームラボで利用するツール・サービスをカテゴリ別に整理した一覧です。

---

## 1. ハードウェア (Hardware)

| ツール | 説明 | 参照 |
|--------|------|------|
| Lenovo ThinkCentre Tiny | 省スペース型デスクトップ PC | @homelab-service-list.md (11) |
| Dell Optiplex Micro | 省スペース型デスクトップ PC | @homelab-service-list.md (12) |
| HP EliteDesk Mini | 省スペース型デスクトップ PC | @homelab-service-list.md (13) |
| Raspberry Pi | シングルボードコンピュータ | @homelab-service-list.md (14) |

---

## 2. コンピュート & 仮想化 (Compute & Virtualization)

| ツール | 説明 | 参照 |
|--------|------|------|
| Proxmox VE | オープンソースの仮想化・コンテナ基盤 | @homelab-service-list.md (22) |
| Docker | コンテナランタイム | @homelab-service-list.md (23) |
| k3s | 軽量 Kubernetes ディストリビューション | @homelab-service-list.md (24) |
| Rancher | Kubernetes クラスタ管理 UI | @homelab-service-list.md (25) |
| Helm | Kubernetes パッケージマネージャ | @homelab-service-list.md (26) |
| Longhorn | Kubernetes 向け分散ストレージ | @homelab-service-list.md (27) |
| portainer/portainer-ce | Docker / Kubernetes 管理 UI | @homelab-service-list.md (28) |
| containerrr/watchtower | コンテナイメージの自動更新 | @homelab-service-list.md (29) |

---

## 3. オペレーティングシステム (OS)

| ツール | 説明 | 参照 |
|--------|------|------|
| Ubuntu | Debian 系 Linux ディストリビューション | @homelab-service-list.md (37) |
| Debian | 汎用 Linux ディストリビューション | @homelab-service-list.md (38) |
| Arch | ロールリリース型 Linux ディストリビューション | @homelab-service-list.md (39) |

---

## 4. インフラストラクチャ as Code (IaC)

| ツール | 説明 | 参照 |
|--------|------|------|
| Terraform | 宣言型インフラ管理 | @homelab-service-list.md (47) |
| Ansible | 構成管理・自動化 | @homelab-service-list.md (48) |

---

## 5. ネットワーク (Network)

### 5.1 ルーター / ファイアウォール

| ツール | 説明 | 参照 |
|--------|------|------|
| OPNSense | オープンソースファイアウォール・ルーター | @homelab-service-list.md (58) |
| pfSense | オープンソースファイアウォール・ルーター | @homelab-service-list.md (59) |

### 5.2 DNS

| ツール | 説明 | 参照 |
|--------|------|------|
| Unbound DNS | 軽量キャッシュ DNS リゾルバ | @homelab-service-list.md (65) |
| CoreDNS | Kubernetes 向けプラグイン型 DNS | @homelab-service-list.md (66) |
| pi-hole/pi-hole | 広告ブロック DNS | @homelab-service-list.md (67) |
| adguard/adguardhome | 広告・トラッキングブロック DNS | @homelab-service-list.md (68) |

### 5.3 リバースプロキシ

| ツール | 説明 | 参照 |
|--------|------|------|
| nginx/nginx | Web サーバー・リバースプロキシ | @homelab-service-list.md (74) |
| jc21/nginx-proxy-manager | Nginx の Web UI 管理ツール | @homelab-service-list.md (75) |
| caddy/caddy | 自動 HTTPS 対応の Web サーバー | @homelab-service-list.md (76) |
| traefik/traefik | 動的リバースプロキシ・ロードバランサ | @homelab-service-list.md (77) |

### 5.4 VPN

| ツール | 説明 | 参照 |
|--------|------|------|
| WireGuard | 軽量 VPN プロトコル | @homelab-service-list.md (82) |
| Tailscale | WireGuard ベースのメッシュ VPN | @homelab-service-list.md (83) |
| OpenVPN | オープンソース VPN | @homelab-service-list.md (84) |

### 5.5 ネットワーク管理

| ツール | 説明 | 参照 |
|--------|------|------|
| Ubiquiti UniFi | ネットワーク機器・管理プラットフォーム | @homelab-service-list.md (90) |
| TP-Link Omada | ネットワーク機器・管理プラットフォーム | @homelab-service-list.md (91) |
| LibreNMS | ネットワーク監視 (SNMP) | @homelab-service-list.md (92) |

---

## 6. ストレージ & バックアップ (Storage & Backup)

| ツール | 説明 | 参照 |
|--------|------|------|
| truenas/core | NAS 用オープンソース OS | @homelab-service-list.md (101) |
| nextcloud/nextcloud | セルフホスト型クラウドストレージ | @homelab-service-list.md (102) |
| linuxserver/duplicati | バックアップ・リストア | @homelab-service-list.md (103) |
| linuxserver/syncthing | P2P ファイル同期 | @homelab-service-list.md (104) |

---

## 7. データベース (Database)

| ツール | 説明 | 参照 |
|--------|------|------|
| postgres/postgres | リレーショナルデータベース | @homelab-service-list.md (112) |
| clickhouse/clickhouse-server | 列指向分析用 DB | @homelab-service-list.md (113) |
| influxdata/influxdb | 時系列データベース | @homelab-service-list.md (114) |

---

## 8. 監視 & 可観測性 (Monitoring & Observability)

| ツール | 説明 | 参照 |
|--------|------|------|
| prom/prometheus | メトリクス収集・アラート | @homelab-service-list.md (122) |
| prom/alertmanager | アラート管理・通知 | @homelab-service-list.md (123) |
| prom/node-exporter | Prometheus 用ホストメトリクス | @homelab-service-list.md (124) |
| prom/blackbox-exporter | Blackbox プローブ（HTTP/HTTPS/DNS/TCP 等） | @homelab-service-list.md (125) |
| grafana/grafana | ダッシュボード・可視化 | @homelab-service-list.md (126) |
| grafana/loki | ログ集約・検索 | @homelab-service-list.md (127) |
| grafana/promtail | Loki 用ログ収集エージェント | @homelab-service-list.md (128) |
| influxdata/telegraf | メトリクス・ログ収集エージェント | @homelab-service-list.md (129) |
| louislam/uptime-kuma | サービス稼働監視・ステータスページ | @homelab-service-list.md (130) |
| linuxserver/tautulli | Plex 利用状況監視 | @homelab-service-list.md (131) |

---

## 9. セキュリティ & アイデンティティ (Security & Identity)

| ツール | 説明 | 参照 |
|--------|------|------|
| authelia/authelia | SSO・2FA 認証プロキシ | @homelab-service-list.md (139) |
| vaultwarden/server | Bitwarden 互換パスワードマネージャ | @homelab-service-list.md (140) |
| crowdsecurity/crowdsec | 侵入検知・ファイアウォール | @homelab-service-list.md (141) |
| gravitational/teleport | セキュアなインフラアクセス | @homelab-service-list.md (142) |
| cloudflare/cloudflared | Cloudflare Tunnel（セキュアリモートアクセス） | @homelab-service-list.md (143) |

---

## 10. メディア & エンターテインメント (Media & Entertainment)

### 10.1 メディアサーバー

| ツール | 説明 | 参照 |
|--------|------|------|
| jellyfin/jellyfin | オープンソースメディアサーバー | @homelab-service-list.md (154) |
| plexinc/pms-docker | メディアサーバー | @homelab-service-list.md (155) |
| emby/embyserver | メディアサーバー | @homelab-service-list.md (156) |

### 10.2 メディア取得・管理

| ツール | 説明 | 参照 |
|--------|------|------|
| linuxserver/radarr | 映画の自動取得・管理 | @homelab-service-list.md (162) |
| linuxserver/sonarr | TV 番組の自動取得・管理 | @homelab-service-list.md (163) |
| linuxserver/prowlarr | インデクサー・トラッカーマネージャ | @homelab-service-list.md (164) |
| linuxserver/jackett | トラッカー・プロキシ | @homelab-service-list.md (165) |
| linuxserver/bazarr | 字幕の自動取得 | @homelab-service-list.md (166) |
| linuxserver/ombi | メディアリクエスト UI | @homelab-service-list.md (167) |

### 10.3 ダウンロード

| ツール | 説明 | 参照 |
|--------|------|------|
| haugene/transmission-openvpn | Transmission + OpenVPN | @homelab-service-list.md (172) |
| binhex/arch-delugevpn | Deluge + VPN | @homelab-service-list.md (173) |
| binhex/arch-sabnzbd | Usenet クライアント | @homelab-service-list.md (174) |

### 10.4 地上波・IP 放送

| ツール | 説明 | 参照 |
|--------|------|------|
| linuxserver/tvheadend | DVB チューナー・ストリーミング | @homelab-service-list.md (179) |
| prengineer/tvhproxy | TVheadend プロキシ | @homelab-service-list.md (180) |
| mirakurun/mirakurun | 日本の地上波チューナー | @homelab-service-list.md (181) |
| epgstation/epgstation | 日本の地上波録画・視聴 | @homelab-service-list.md (182) |

### 10.5 写真・ドキュメント

| ツール | 説明 | 参照 |
|--------|------|------|
| immichapp/immich | セルフホスト型写真管理 | @homelab-service-list.md (187) |
| paperless-ngx/paperless-ngx | ドキュメント管理・アーカイブ | @homelab-service-list.md (188) |

---

## 11. スマートホーム & IoT (Smart Home & IoT)

| ツール | 説明 | 参照 |
|--------|------|------|
| homeassistant/home-assistant | スマートホーム統合プラットフォーム | @homelab-service-list.md (197) |
| blakeblackshear/frigate | NVR・AI 物体検知 | @homelab-service-list.md (198) |
| koush/scrypted | カメラ・デバイスの HomeKit ブリッジ | @homelab-service-list.md (199) |
| oznu/homebridge | HomeKit ブリッジ | @homelab-service-list.md (200) |
| eclipse-mosquitto/eclipse-mosquitto | MQTT ブローカー | @homelab-service-list.md (201) |

---

## 12. 通信 (Communication)

| ツール | 説明 | 参照 |
|--------|------|------|
| FreePBX | オープンソース VoIP PBX | @homelab-service-list.md (209) |
| 3CX | VoIP PBX | @homelab-service-list.md (210) |
| bytemark/smtp | SMTP メールサーバー | @homelab-service-list.md (211) |

---

## 13. ダッシュボード & 管理 (Dashboard & Management)

| ツール | 説明 | 参照 |
|--------|------|------|
| gethomepage/homepage | ホームラボ用ダッシュボード | @homelab-service-list.md (218) |
| linuxserver/heimdall | アプリケーションランチャー | @homelab-service-list.md (219) |
| fenruscn/fenrus | ダッシュボード・ブックマーク | @homelab-service-list.md (220) |

---

## 14. 開発 & 生産性 (Development & Productivity)

| ツール | 説明 | 参照 |
|--------|------|------|
| coder/code-server | ブラウザ版 VS Code | @homelab-service-list.md (227) |
| oznu/guacamole | ブラウザベースのリモートデスクトップ | @homelab-service-list.md (228) |
| ich777/krusader | ファイルマネージャ | @homelab-service-list.md (229) |

---

## 15. レシピ・ライフスタイル (Lifestyle)

| ツール | 説明 | 参照 |
|--------|------|------|
| mealie-mealie/mealie | レシピ管理・メニュープランナー | @homelab-service-list.md (236) |

---

## 16. カメラ・セキュリティ (Camera & Security)

| ツール | 説明 | 参照 |
|--------|------|------|
| shinobicctv/shinobi | CCTV・NVR | @homelab-service-list.md (243) |

---

## 17. 分析 & その他 (Analytics & Other)

| ツール | 説明 | 参照 |
|--------|------|------|
| plausible/analytics | プライバシー重視の Web 分析 | @homelab-service-list.md (250) |
| AltServer | AltStore 用 AltServer（iOS サイドロード） | @homelab-service-list.md (251) |
| AirMessage | iMessage を Android で利用 | @homelab-service-list.md (252) |
| stanley | （要確認） | @homelab-service-list.md (253) |

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
