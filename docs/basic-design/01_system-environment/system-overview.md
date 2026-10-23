# システム構成・環境

homelab の物理・仮想構成と、稼働環境の前提をまとめる。図と IP 規約は [README.md](../../../README.md) が正で、ここでは設計上の前提と制約を整理する。

## 目的と位置づけ

- 個人の検証・常用環境。商用サービスではなく、SLA は持たない（[可用性](../02_availability/availability.md)）。
- 全構成を Terraform / Ansible / Docker Compose でコード化し、いつでも同じ環境を再構築できる状態を保つ。
- 環境は 1 つだけ（本番 = 開発）。破壊を伴う検証は `vm-dev` で行い、他の VM は壊さない。

## 物理構成

| 機器 | モデル | スペック | IP | 備考 |
| --- | --- | --- | --- | --- |
| サーバー | Lenovo ThinkCentre M70q Tiny | i5-10400T / 24GB RAM / 256GB NVMe | `192.168.11.10` | Proxmox VE ホスト。物理 NIC は 1 つ |
| ルーター | Buffalo WSR-1800AX4P | — | `192.168.11.1` | 集合住宅の共用ルーターの下に置く（二重 NAT） |
| IoT | ESP32 | — | `192.168.11.100` | 現在停止中 |

- 電源は UPS なし。ホスト 1 台に全 VM が載る単一障害点の構成（[可用性](../02_availability/availability.md)）。
- 次期構成（TP-Link + Managed Switch + AP、VLAN 分割）は [VLAN 設計](../07_network/vlan-design.md)。未適用。

## 論理構成

Proxmox VE 上に Terraform で VM を作り、Ansible で設定し、各 VM で Docker Compose を動かす。

| 名前 | VMID | IP | vCPU | RAM | ディスク | 起動 | 役割 | 主なサービス |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `vm-infra` | 111 | `192.168.11.11` | 2 | 1.5GB | 20G | 自動（順序 1） | インフラ基盤 | AdGuard Home, Unbound, CoreDNS, Caddy, Tailscale |
| `vm-monitoring` | 113 | `192.168.11.13` | 2 | 2GB | 40G | 自動（順序 2） | 監視 | Prometheus, Alertmanager, Grafana |
| `vm-apps` | 120 | `192.168.11.20` | 2 | 4GB | 40G | 自動（順序 3） | アプリ | Homepage |
| `vm-dev` | 121 | `192.168.11.21` | 2 | 1GB | 30G | 手動 | 破壊検証 | playground |
| `vm-code` | 122 | `192.168.11.22` | 2 | 4GB | 30G | 自動（順序 5） | 常用リモート開発 | Claude Code, CloudCLI, code-server |
| `vm-windows` | 130 | — | 4 | 8GB | 60G | 手動（停止） | 検証用 | Windows 11 |
| `ubuntu-cloud` | 9000 | — | — | — | — | — | VM テンプレート | cloud-init 付き Ubuntu |

正の定義は `terraform/proxmox/terraform.tfvars`（`vm-windows` は `windows.tf`）。起動順序と待機秒数は [運用 Runbook](../../runbook.md#vm-自動起動停止) を参照。

## ソフトウェア構成

| レイヤ | 採用技術 | 管理場所 |
| --- | --- | --- |
| ハイパーバイザ | Proxmox VE 8.x | `ansible/roles/proxmox/`（Web UI の警告除去、収集スクリプト） |
| VM プロビジョニング | Terraform（`telmate/proxmox` 3.0.2-rc07） | `terraform/proxmox/` |
| OS 設定 | Ansible（Ubuntu） | `ansible/roles/common/` ほか |
| コンテナ | Docker Compose | `docker/compose/<stack>/` → VM 上の `/opt/<stack>/` |
| 監視 | Prometheus, Alertmanager, Grafana, node_exporter | [監視・アラート](../05_operations-maintainability/monitoring.md) |
| 名前解決 | AdGuard Home → CoreDNS / Unbound | [DNS 構成](../07_network/dns.md) |
| リバースプロキシ・TLS | Caddy + Let's Encrypt（Cloudflare DNS-01） | [運用 Runbook](../../runbook.md#lan-内-tls) |
| 秘密情報 | SOPS + age | [セキュリティ](../06_security/security.md) |
| CI | GitHub Actions（lint のみ） | [CI/CD](../05_operations-maintainability/cicd.md) |

## 前提と制約

| 項目 | 内容 |
| --- | --- |
| 単一ホスト | 全 VM が 1 台の Proxmox ホストと 1 つの NVMe に載る。冗長化はしない |
| 二重 NAT | 外からポート開放ができない。外部からの到達は Tailscale に限る（[外部接続](../08_external-connectivity/external-connectivity.md)） |
| ストレージ | `local-lvm`（LVM-thin、約 155GiB）に全 VM のディスクを置く。過剰割当（約 1.4 倍）で運用している（[性能・拡張性](../04_performance-scalability/capacity-and-scaling.md)） |
| ドメイン | `lab.kanare.dev`（内部ゾーンは CoreDNS、証明書は Let's Encrypt） |
| タイムゾーン・NTP | `Asia/Tokyo`、`ntp.nict.jp` / `time.google.com` |
| 管理操作 | Mac から SSH / Terraform / Ansible で行う。自動デプロイはしない |

## 命名・採番規約

IP アドレス規約、ドメイン命名規約は [README.md](../../../README.md#ip-アドレス規約) を参照。VMID は IP の末尾オクテットに 100 を足した値（`vm-infra` は `.11` → 111、`vm-apps` は `.20` → 120）。
