# roadmap

README に書く現行構成は `8GB` 前提の最小実用構成とし、このファイルではその先の拡張計画を整理する。

## 近い将来

- [x] `vm-infra` と `vm-monitoring` の構成を Terraform + Ansible で完全再現できるようにする
- [x] CoreDNS で `lab.kanare.dev` 内部ゾーンを運用する
- [x] Caddy を Docker Compose 化し、Cloudflare DNS-01 チャレンジで Let's Encrypt 証明書を取得する
- [x] `pve.lab.kanare.dev` を Caddy 経由で解決できるようにする
- [x] Tailscale を vm-infra にサブネットルーターとして導入し、外出先からホームラボにアクセスできるようにする（二重NAT環境のためWireGuardの代替）
- [ ] Cloudflare Tunnel を導入し、`grafana.lab.kanare.dev` 等を外部公開する
- [ ] Split-Horizon DNS を構成する（LAN内は CoreDNS→Caddy 経由、外部は Cloudflare Tunnel 経由で同一 FQDN でアクセス）
- [ ] Tailscale は SSH 等の管理アクセス用として継続利用する
- [ ] Proxmox 上でホームラボのトップページをホスティングしたい
- [ ] blackbox_exporter で外形監視を追加する
- [ ] Portainer で Docker の状態を可視化する
- [ ] メモリの配分を見直しする
- [ ] `vm-dev` を Ansible、Docker、ネットワーク設定の破壊検証用として運用する
- [ ] Alertmanager を追加して監視通知を受け取れるようにする
- [ ] TO-BE と AS-IS の構成図を描く
- [ ] DNS を AdGuard Home + Unbound に移行する（CoreDNS を置き換え）
  - AdGuard Home: 広告ブロック・クエリログ・`lab.kanare.dev` 内部レコード管理
  - Unbound: フルリゾルバ（1.1.1.1 等に依存せずルートから再帰解決・プライバシー向上）
  - vm-infra 上の Docker Compose に両方載せる

## メモリ増設後にやりたいこと

- `vm-apps` を常時起動し、Home Assistant などのアプリを載せる
- Loki + Promtail などのログ基盤を検討する
- より重いワークロードや複数アプリを分離運用する

## ネットワーク構成の改良

- 現状の Buffalo ルータから、TP-Link 製のルータ、Managed Switch、AP に分離して Omada で管理する
- VLAN を構成する
- VLAN10 Management
- VLAN20 Servers
- VLAN30 Clients
- VLAN40 IoT
- VLAN50 Guests

## 将来試したいこと

- Home Assistant の本格運用, SwitchBotの統合
- ThinkCentre Tiny をラックに搭載する
- メモリ増設後に k3s などのクラスタ構成を検討する
- portainerの導入
- treafikの導入
- OPNSenseの導入
- truenasの導入
- telegraf, influxDBの導入
- uptime-kumaの導入
- embyの導入
- IPカメラ、frigateの導入
- テレビの統合

- 以下の構成：

```plaintext
Traefik
↓
HomeAssistant
Emby
Frigate
Grafana
```

```plaintext
ESP32
↓
MQTT (Mosquitto)
↓
HomeAssistant
↓
Prometheus
↓
Grafana
```
