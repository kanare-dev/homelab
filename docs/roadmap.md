# roadmap

README に書く現行構成は `8GB` 前提の最小実用構成とし、このファイルではその先の拡張計画を整理する。

---

## 完了済み

### インフラ基盤

- [x] ハードウェア調達
- [x] Proxmox VE インストール（`192.168.11.10`）
- [x] ネットワーク設計確定（IP 規約は `README.md` 参照）
- [x] SSH 鍵ペア生成
- [x] Cloud-init テンプレート VM を作成（`terraform/proxmox/README.md` 参照）
- [x] Proxmox API トークン発行
- [x] 初期構成は `vm-infra` + `vm-monitoring` + `vm-dev` に絞る
- [x] 秘密情報管理方針を決定（Ansible Vault を採用）
- [x] DNS ドメイン（`lab.kanare.dev`）を決定

### サービス構築

- [x] `vm-infra` と `vm-monitoring` の構成を Terraform + Ansible で完全再現できるようにする
- [x] CoreDNS で `lab.kanare.dev` 内部ゾーンを運用する
- [x] Caddy を Docker Compose 化し、Cloudflare DNS-01 チャレンジで Let's Encrypt 証明書を取得する
- [x] `pve.lab.kanare.dev` を Caddy 経由で解決できるようにする
- [x] `vm-monitoring`: Prometheus + Grafana デプロイ
- [x] 常時起動する VM に `node_exporter` デプロイ
- [x] Grafana ダッシュボード設定（Node Exporter Full, Prometheus Overview）
- [x] Reverse Proxy 経由のアクセス確認（`grafana.lab.kanare.dev`, `prometheus.lab.kanare.dev`）
- [x] Tailscale を vm-infra にサブネットルーターとして導入し、外出先からホームラボにアクセスできるようにする（二重NAT環境のためWireGuardの代替）

---

## ネットワーク・DNS

- [ ] Cloudflare Tunnel を導入し、`grafana.lab.kanare.dev` 等を外部公開する
- [ ] Split-Horizon DNS を構成する（LAN内は CoreDNS→Caddy 経由、外部は Cloudflare Tunnel 経由で同一 FQDN でアクセス）
- [ ] Tailscale は SSH 等の管理アクセス用として継続利用する
- [x] DNS を AdGuard Home + Unbound に移行する（CoreDNS は権威 DNS として継続）
  - AdGuard Home: 広告ブロック・クエリログ・WebUI（port 53 / 3000）
  - Unbound: フルリゾルバ（1.1.1.1 等に依存せずルートから再帰解決・プライバシー向上、port 5335）
  - CoreDNS: `lab.kanare.dev` 権威 DNS として継続（port 5353、127.0.0.1 バインドに変更）
  - vm-infra 上の Docker Compose に AdGuard + Unbound を追加
- [ ] Buffalo ルータから TP-Link（ルータ + Managed Switch + AP）に分離して Omada で管理する
- [ ] VLAN を構成する（VLAN10 Management / VLAN20 Servers / VLAN30 Clients / VLAN40 IoT / VLAN50 Guests）
- [ ] OPNSense の導入

## 監視・可観測性

- [ ] blackbox_exporter で外形監視を追加する
- [ ] Alertmanager を追加して個人Slackで監視通知を受け取れるようにする
- [ ] uptime-kuma の導入
- [ ] Loki + Promtail でログ収集基盤を構築する
- [ ] telegraf + InfluxDB の導入

## インフラ・IaC・運用

- [ ] TO-BE と AS-IS の構成図を描く
- [ ] メモリの配分を見直しする
- [ ] `vm-dev` を Ansible、Docker、ネットワーク設定の破壊検証用として運用する
- [ ] バックアップ自動化（Proxmox Backup Server or restic）
- [ ] CI/CD パイプライン（GitHub Actions で lint + plan）
- [ ] VM テンプレートの Packer 化

## 可視化・管理 UI

- [ ] Proxmox 上でホームラボのトップページをホスティングしたい (Homepage/Dashy)
- [ ] Portainer で Docker の状態を可視化する
- [ ] Traefik の導入

## ハードウェア・拡張

- [ ] メモリ増設
- [ ] ThinkCentre Tiny をラックに搭載する
- [ ] NAS の導入（TrueNAS）
- [ ] UPS 導入と自動シャットダウン

## メモリ増設後

- [ ] `vm-apps` を常時起動し、各種アプリを載せる
- [ ] k3s などのクラスタ構成を検討する
- [ ] より重いワークロードや複数アプリを分離運用する

## ホームオートメーション

- [ ] Home Assistant の本格運用、SwitchBot の統合
- [ ] MQTT (Mosquitto) + ESP32 連携

  ```plaintext
  ESP32 → MQTT → HomeAssistant → Prometheus → Grafana
  ```

- [ ] IPカメラ + Frigate の導入
- [ ] メディアサーバの導入（Jellyfin / Plex / Emby）
- [ ] テレビの統合
