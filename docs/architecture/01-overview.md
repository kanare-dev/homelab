# システム概要

homelab の全体像。最新の構成図、目的、構成の理由、前提と制約をまとめる。構成要素の詳細は [インフラ構成](02-infrastructure.md)、[ネットワーク設計](03-network.md)、[可用性・信頼性](04-reliability.md) を参照。

## 構成図

> 構成を変えたら、この図（ASCII）と下の表を同じ変更で更新する。SVG は `docs/diagrams/layout-architecture.py` で生成し直して同じ変更で更新する。食い違っていたら、この ASCII 図が正。

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  LAN: 192.168.11.0/24                  GW: 192.168.11.1          Tailscale (外出先)  │
│                                                                                     │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  vm-infra    │  │ vm-monitoring │  │ vm-apps      │  │ vm-code      │            │
│  │  .11  1.5GB  │  │  .13  2GB     │  │  .20  4GB    │  │  .22  4GB    │            │
│  │  AdGuard Home│  │  Prometheus   │  │  Homepage    │  │  Claude Code │            │
│  │  Unbound     │  │  Alertmanager │  │Home Assistant│  │  CloudCLI    │            │
│  │  CoreDNS     │  │  Grafana      │  │  n8n         │  │  code-server │            │
│  │  Caddy       │  │  blackbox     │  │              │  │              │            │
│  │  Tailscale   │  │               │  │              │  │              │            │
│  └──────┬───────┘  └──────┬────────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                  │                 │                    │
│  ┌──────┴─────────────────┴──────────────────┴─────────────────┴───────────────┐    │
│  │                      Proxmox VE (.10)                                       │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                               │
│  │  IoT devices │  │  vm-dev      │  │  vm-windows  │                               │
│  │  .100~       │  │  .21 任意起動 │  │  任意起動    │                               │
│  │  ESP32 etc.  │  │  playground  │  │  検証用      │                               │
│  └──────────────┘  └──────────────┘  └──────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

`vm-monitoring` では Prometheus に加えて blackbox-exporter が、Caddy 経由の HTTPS と AdGuard の名前解決を外形監視する（[監視・アラート](../services/monitoring.md)）。

`node_exporter` は全 VM（`vm-infra` / `vm-monitoring` / `vm-apps` / `vm-dev` / `vm-code`）と Proxmox ホストに常駐し、`vm-monitoring` の Prometheus がまとめてスクレイプする。

![構成図](../diagrams/architecture.drawio.svg)

## 目的と位置づけ

- 個人の検証・常用環境。商用サービスではなく、SLA は持たない（[可用性](04-reliability.md)）。
- 全構成を Terraform / Ansible / Docker Compose でコード化し、いつでも同じ環境を再構築できる状態を保つ。
- 環境は 1 つだけ（本番 = 開発）。破壊を伴う検証は `vm-dev` で行い、他の VM は壊さない。

## この構成にした理由

最小構成から始め、必要に応じて段階的に拡張する方針。

| 観点 | 判断 |
| --- | --- |
| メモリ余裕 | 24GB に増設済み。重めのワークロードや追加 VM を検討できる（[性能・拡張性](02-infrastructure.md)） |
| 優先順位 | まず DNS、リバースプロキシ、監視をコード化して再現性を固める |
| 学習効率 | `vm-dev` があると、設定や playbook を安全に壊して試せる |
| 拡張性 | `vm-apps` に Home Assistant、n8n などを追加しやすい |

## 前提と制約

| 項目 | 内容 |
| --- | --- |
| 単一ホスト | 全 VM が 1 台の Proxmox ホストと 1 つの NVMe に載る。冗長化はしない |
| 二重 NAT | 外からポート開放ができない。外部からの到達は Tailscale に限る（[外部接続](03-network.md)） |
| ストレージ | `local-lvm`（LVM-thin、約 155GiB）に全 VM のディスクを置く。過剰割当（約 1.4 倍）で運用している（[性能・拡張性](02-infrastructure.md)） |
| ドメイン | `lab.kanare.dev`（内部ゾーンは CoreDNS、証明書は Let's Encrypt） |
| タイムゾーン・NTP | `Asia/Tokyo`、`ntp.nict.jp` / `time.google.com` |
| 管理操作 | Mac から SSH / Terraform / Ansible で行う。自動デプロイはしない |
