# インフラ構成

物理・仮想構成、ソフトウェア構成、資源の配分と拡張の方針をまとめる。全体像と構成図は [システム概要](overview.md)。

## 物理構成

| 機器 | モデル | スペック | IP | 備考 |
| --- | --- | --- | --- | --- |
| サーバー | Lenovo ThinkCentre M70q Tiny | i5-10400T / 24GB RAM / 256GB NVMe | `192.168.11.10` | Proxmox VE ホスト。物理 NIC は 1 つ |
| ルーター | Buffalo WSR-1800AX4P | — | `192.168.11.1` | 集合住宅の共用ルーターの下に置く（二重 NAT） |
| IoT | ESP32 | — | `192.168.11.100` | 現在停止中 |

- 電源は UPS なし。ホスト 1 台に全 VM が載る単一障害点の構成（[可用性](reliability.md)）。
- 次期構成（TP-Link + Managed Switch + AP、VLAN 分割）は [VLAN 設計](vlan-design.md)。未適用。

## 論理構成

Proxmox VE 上に Terraform で VM を作り、Ansible で設定し、各 VM で Docker Compose を動かす。

| 名前 | VMID | IP | vCPU | RAM | ディスク | 起動 | 役割 | 主なサービス |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `vm-infra` | 111 | `192.168.11.11` | 2 | 1.5GB | 20G | 自動（順序 1） | インフラ基盤 | AdGuard Home, Unbound, CoreDNS, Caddy, Tailscale |
| `vm-monitoring` | 113 | `192.168.11.13` | 2 | 2GB | 40G | 自動（順序 2） | 監視 | Prometheus, Alertmanager, Grafana |
| `vm-apps` | 120 | `192.168.11.20` | 2 | 4GB | 40G | 自動（順序 3） | アプリ | Homepage |
| `vm-dev` | 121 | `192.168.11.21` | 2 | 1GB | 30G | 手動 | 破壊検証 | playground |
| `vm-code` | 122 | `192.168.11.22` | 2 | 4GB | 30G | 自動（順序 5） | 常用リモート開発 | Claude Code, CloudCLI, code-server, gh, git, mosh, moshi-hook |
| `vm-windows` | 130 | — | 4 | 8GB | 60G | 手動（停止） | 検証用 | Windows 11 |
| `ubuntu-cloud` | 9000 | — | — | — | — | — | VM テンプレート | cloud-init 付き Ubuntu |

正の定義は `terraform/proxmox/terraform.tfvars`（`vm-windows` は `windows.tf`）。起動順序と待機秒数は [運用 Runbook](../operations/runbooks/vm-startup-shutdown.md#vm-自動起動停止) を参照。

## ソフトウェア構成

| レイヤ | 採用技術 | 管理場所 |
| --- | --- | --- |
| ハイパーバイザ | Proxmox VE 8.x | `ansible/roles/proxmox/`（Web UI の警告除去、収集スクリプト） |
| VM プロビジョニング | Terraform（`telmate/proxmox` 3.0.2-rc07） | `terraform/proxmox/` |
| OS 設定 | Ansible（Ubuntu） | `ansible/roles/common/` ほか |
| コンテナ | Docker Compose | `docker/compose/<stack>/` → VM 上の `/opt/<stack>/` |
| 監視 | Prometheus, Alertmanager, Grafana, node_exporter | [監視・アラート](../services/monitoring.md) |
| 名前解決 | AdGuard Home → CoreDNS / Unbound | [DNS 構成](../services/dns.md) |
| リバースプロキシ・TLS | Caddy + Let's Encrypt（Cloudflare DNS-01） | [運用 Runbook](../operations/runbooks/tls-certificates.md#lan-内-tls) |
| 秘密情報 | SOPS + age | [セキュリティ](security.md) |
| CI | GitHub Actions（lint のみ） | [CI/CD](../services/cicd.md) |

## ホストの資源

| 資源 | 容量 | 備考 |
| --- | --- | --- |
| CPU | i5-10400T（6 コア 12 スレッド） | 省電力版 |
| メモリ | 24GB（8GB + 16GB） | 2026-10 に 8GB から増設 |
| ストレージ | 256GB NVMe。`local-lvm`（thin pool `pve/data`）は約 155GiB | 全 VM のディスクがこの pool を共有する |
| NIC | 1 つ | VLAN 化の際は trunk にする（[VLAN 設計](vlan-design.md)） |

## 配分

VM ごとの vCPU・メモリ・ディスクは [論理構成](#論理構成) の表が正。ここでは実使用と、全体の収支を示す。

| 対象 | 実使用（目安） | 備考 |
| --- | --- | --- |
| Proxmox ホスト | — | メモリを約 2GB 確保する（ホスト側の余裕を削りすぎない） |
| `vm-infra` | 約 500MB | |
| `vm-monitoring` | 約 660MB | |
| `vm-apps` | 約 256MB | 実使用に対して割当が大きい |
| `vm-code` / `vm-dev` | — | `vm-dev` は手動起動 |
| `vm-windows` | — | 手動起動（通常は停止） |

- 常時起動の VM の割当メモリ合計は 11.5GB。`vm-dev` を加えて 12.5GB、`vm-windows` も起動すると 20.5GB になる。ホストの確保分（約 2GB）を足すと 22.5GB で、24GB に対する余白は約 1.5GB しかない。**`vm-windows` を起動するときは、他の VM の負荷に注意する。**
- vCPU は物理スレッドに対して過剰割当（常時起動分で 8 vCPU、全 VM で 14 vCPU）。常時高負荷の VM がないことを前提にしている。
- メモリ配分の見直しはロードマップの未着手項目（実使用に対して `vm-apps` の割当が大きい）。

## ストレージの設計

- thin provisioning で過剰割当している。割当の合計は pool の約 1.4 倍（`LvmThinPoolOverprovisioned` の閾値は 1.5）。
- 仮想ディスクはすべて `discard` を有効にし、毎週 `fstrim` で未使用ブロックを pool に返す。
- 使用率は `LvmThinPoolDataHigh`（75%）と `Critical`（90%）で見る。メタデータも同様。
- VG に未割当の余りは、pool 拡張の余地として使える（`lvextend`）。余りがなければ、ディスク追加か VM ディスクの縮小になる。
- 詳細は [thin pool 枯渇の障害記録](../operations/incidents/2026-10-22-lvm-thin-exhaustion.md)。

## 資源の見張り方

| 見たいもの | アラート（[監視・アラート](../services/monitoring.md)） |
| --- | --- |
| CPU の逼迫 | `HostCpuHigh`（85%、15 分）/ `HostCpuCritical`（95%、10 分） |
| メモリの逼迫・OOM | `HostMemoryLow`（利用可能 10% 未満）/ `HostMemoryCritical`（5%）、`HostOomKilled` |
| ディスクの逼迫 | `HostDiskUsageHigh`（80%）/ `Critical`（90%） |
| thin pool の逼迫 | `LvmThinPoolData*`、`LvmThinPoolMetadata*`、`LvmThinPoolOverprovisioned` |

Grafana の「Storage / Thin Pool」ダッシュボードで、pool と VM ディスク別の割当・増加ペースを確認できる。

## 拡張の方針

**垂直拡張（資源の追加）だけを前提にする。** クラスタ化や負荷分散は、個人利用の規模では行わない。

| 状況 | 対応 |
| --- | --- |
| VM のメモリ・CPU が足りない | `terraform.tfvars` の `memory` / `cores` を変更（再起動を伴う場合は 1 台ずつ） |
| ディスクが足りない | まず `fstrim` と不要データの整理。足りなければ pool を拡張（VG の余り）、ディスクの追加 |
| ホストのメモリが足りない | 配分の見直し。常時起動しない VM を止める。SO-DIMM を交換する（最大容量はモデルの仕様を確認する） |
| 重い構成を載せたい（k3s など） | 学習用に分離して運用する。安定稼働中のサービスは当面 Docker Compose のまま（ロードマップ） |
| 複数ホストが必要になった | Proxmox クラスタと共有ストレージ（NAS）を検討する。現在の設計の対象外 |

### VM を追加する手順

1. `terraform/proxmox/terraform.tfvars` の `vms` に定義を追加し、`terraform plan` / `apply`。
2. `ansible/inventory/hosts.yml` にホストを追加し、`group_vars` / playbook を用意して Ansible で設定する。
3. 必要なら `dns_records`（`group_vars/infra/vars.yml`）と Caddyfile を追記し、`playbooks/infra.yml` を実行する。
4. Prometheus の scrape 対象とアラートの対象に加える（`prometheus.yml`）。
5. 配分の表（この文書と [システム構成・環境](overview.md)）と構成図を更新する。

## 既知の限界

- ストレージが NVMe 1 枚で、容量にも故障にも余裕がない。NAS の導入（TrueNAS）はロードマップの未着手項目。
- CPU・メモリの実測の推移は、まだ設計の根拠として整理していない。
- Prometheus の保持上限 5GB は暫定値で、実測で調整する。
