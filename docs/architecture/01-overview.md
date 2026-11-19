# システム概要

homelab の全体像。最新の構成図、目的、構成の理由、前提と制約をまとめる。構成要素の詳細は [インフラ構成](02-infrastructure.md)、[ネットワーク設計](03-network.md)、[可用性・信頼性](04-reliability.md) を参照。

## 構成図

> 構成を変えたら、この図（ASCII）と下の表を同じ変更で更新する。現状の構成図（`docs/diagrams/as-is-diagram/`。削除せず、常に実機の状態を表す）は、`make-as-is-diagram.py` で生成し直して同じ変更で更新する。食い違っていたら、この ASCII 図が正。

```text
 External: Healthchecks.io / Slack / Cloudflare / Let's Encrypt / Tailscale / GitHub
     │
 Internet ── ER605 router (.1) ── SG2210P switch ── Buffalo AP (.2) / Proxmox / Display
     │
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  Servers VLAN20: 10.77.20.0/24  GW: 10.77.20.1                   Tailscale (外出先)  │
│                                                                                     │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  vm-infra    │  │ vm-monitoring │  │ vm-apps      │  │ vm-code      │            │
│  │  .10  1.5GB  │  │  .11  2GB     │  │  .20  4GB    │  │  .30  4GB    │            │
│  │  AdGuard Home│  │  Prometheus   │  │  Homepage    │  │  Claude Code │            │
│  │  Unbound     │  │  Alertmanager │  │Home Assistant│  │  CloudCLI    │            │
│  │  CoreDNS     │  │  Grafana      │  │  n8n         │  │  code-server │            │
│  │  Caddy       │  │  blackbox     │  │              │  │              │            │
│  │  Tailscale   │  │               │  │              │  │              │            │
│  └──────┬───────┘  └──────┬────────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                  │                 │                    │
│  ┌──────┴─────────────────┴──────────────────┴─────────────────┴───────────────┐    │
│  │                      Proxmox VE (192.168.11.10。今の LAN)                   │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                               │
│  │  IoT devices │  │  vm-dev      │  │  vm-omada    │                               │
│  │  .100~       │  │  .10 任意起動 │  │  .3   4GB    │                              │
│  │  ESP32 etc.  │  │  playground  │  │  Omada Ctrl  │                               │
│  └──────────────┘  └──────────────┘  └──────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

図の読み方（段階 3b の後。ACL は全許可）: 上段の 4 台は Servers（VLAN20、`10.77.20.0/24`）。`vm-dev` は Lab（VLAN40、`10.77.40.10`）。`vm-omada`（`10.77.10.3`）と SG2210P（`10.77.10.2`）は、2026-11-19 に Management（VLAN10）へ移った（[ADR-0031](../adr/0031-stage3b-devices-before-controller.md)）。Proxmox ホスト（`192.168.11.10`）と ER605 の既定の LAN（`192.168.11.1`）は、今の LAN（VLAN1、`192.168.11.0/24`）に残る（ホストの移動と、`10.77.1.0/24` への付け替えは未実施。[ADR-0028](../adr/0028-defer-management-vlan10.md)）。Buffalo（AP）は Trusted（VLAN30、`10.77.30.50`）。ESP32 は停止中で、旧アドレスのまま。

`vm-monitoring` では Prometheus に加えて blackbox-exporter が、Caddy 経由の HTTPS と AdGuard の名前解決を外形監視し、ping（ICMP）でインターネット回線の断・遅延も見る（[監視・アラート](../services/platform/monitoring.md)）。

外部サービス（Healthchecks.io、Slack、Cloudflare、Let's Encrypt、Tailscale、GitHub、Omada Cloud）は、図の上部にまとめて描いている。いずれも LAN から外向きに接続するだけ。外部から入る経路は Tailscale と、Omada Cloud 経由の Omada コントローラーの管理画面（[外部接続](03-network.md#外部サービスへの依存)）。

`node_exporter` は全 VM（`vm-infra` / `vm-monitoring` / `vm-apps` / `vm-dev` / `vm-code` / `vm-omada`）と Proxmox ホストに常駐し、`vm-monitoring` の Prometheus がまとめてスクレイプする。

`vm-omada` の Omada コントローラーは、ER605・SG2210P を管理する（2026-11-03 に稼働。2026-11-06 に、ER605・SG2210P を採用した）。Buffalo は AP モードで、管理対象外。止まっても、機器は設定を持ったまま動く。

![現状の構成図（as-is）](../diagrams/as-is-diagram/as-is-diagram.png)

上は現状（as-is。段階 3 の後）。詳しくは[現状の構成図](../diagrams/README.md#現状の構成図as-is-diagram)。最終形（to-be）は、[to-be の構成図](../diagrams/README.md#to-be-の構成図-vlan-化のあとto-be-diagram)。

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
| 拡張性 | `vm-apps` に Home Assistant、n8n、FreshRSS などを追加しやすい |

## 前提と制約

| 項目 | 内容 |
| --- | --- |
| 単一ホスト | 全 VM が 1 台の Proxmox ホストと 1 つの NVMe に載る。冗長化はしない |
| 二重 NAT | 外からポート開放ができない。外部からの到達は Tailscale に限る（[外部接続](03-network.md)） |
| ストレージ | `local-lvm`（LVM-thin、約 155GiB）に全 VM のディスクを置く。過剰割当（約 1.4 倍）で運用している（[性能・拡張性](02-infrastructure.md)） |
| ドメイン | `lab.kanare.dev`（内部ゾーンは CoreDNS、証明書は Let's Encrypt） |
| タイムゾーン・NTP | `Asia/Tokyo`、`ntp.nict.jp` / `time.google.com` |
| 管理操作 | Mac から SSH / Terraform / Ansible で行う。自動デプロイはしない |
