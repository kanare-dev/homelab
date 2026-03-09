# roadmap

README に書く現行構成は `8GB` 前提の最小実用構成とし、このファイルではその先の拡張計画を整理する。

## 近い将来

- [x] `vm-infra` と `vm-monitoring` の構成を Terraform + Ansible で完全再現できるようにする
- [ ] `vm-dev` を Ansible、Docker、ネットワーク設定の破壊検証用として運用する
- [ ] Alertmanager を追加して監視通知を受け取れるようにする
- [ ] TO-BEとAS-ISの構成図を描く
- WireGuardを使えるようにする
- pveのドメイン名を解決できるようにする
- DNS設計
- Let's Encrypt
- Cloudflare Tunnel
- Split-Horizon DNS
- ルータ側でDNS=192.168.11.11に設定する
- blackbox_exporter 

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

- Home Assistant の本格運用
- WireGuard を外部アクセスの標準入口にする
- ThinkCentre Tiny をラックに搭載する
- メモリ増設後に k3s などのクラスタ構成を検討する
- portainerの導入
- treafikの導入
- OPNSenseの導入
- truenasの導入
- telegraf, influxDBの導入


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
