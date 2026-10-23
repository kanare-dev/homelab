# 性能・拡張性

ホストの資源と各 VM への配分、増設の余地、限界に達したときの対応を整理する。性能の目標値（応答時間など）は置いていない。個人利用のため、**資源が足りているか**を監視で確認する方針。

## ホストの資源

| 資源 | 容量 | 備考 |
| --- | --- | --- |
| CPU | i5-10400T（6 コア 12 スレッド） | 省電力版 |
| メモリ | 24GB（8GB + 16GB） | 2026-10 に 8GB から増設 |
| ストレージ | 256GB NVMe。`local-lvm`（thin pool `pve/data`）は約 155GiB | 全 VM のディスクがこの pool を共有する |
| NIC | 1 つ | VLAN 化の際は trunk にする（[VLAN 設計](../07_network/vlan-design.md)） |

## 配分

| 対象 | vCPU | メモリ（割当） | ディスク | 備考 |
| --- | ---: | ---: | ---: | --- |
| Proxmox ホスト | — | 約 2GB（確保） | — | ホスト側の余裕を削りすぎない |
| `vm-infra` | 2 | 1.5GB | 20G | 実使用 約 500MB |
| `vm-monitoring` | 2 | 2GB | 40G | 実使用 約 660MB |
| `vm-apps` | 2 | 4GB | 40G | 実使用 約 256MB |
| `vm-code` | 2 | 4GB | 30G | 常時起動 |
| `vm-dev` | 2 | 1GB | 30G | 手動起動 |
| `vm-windows` | 4 | 8GB | 60G | 手動起動（通常は停止） |

- 常時起動の VM の割当メモリ合計は 11.5GB。`vm-dev` を加えて 12.5GB、`vm-windows` も起動すると 20.5GB になる。ホストの確保分（約 2GB）を足すと 22.5GB で、24GB に対する余白は約 1.5GB しかない。**`vm-windows` を起動するときは、他の VM の負荷に注意する。**
- vCPU は物理スレッドに対して過剰割当（常時起動分で 8 vCPU、全 VM で 14 vCPU）。常時高負荷の VM がないことを前提にしている。
- メモリ配分の見直しはロードマップの未着手項目（実使用に対して `vm-apps` の割当が大きい）。

## ストレージの設計

- thin provisioning で過剰割当している。割当の合計は pool の約 1.4 倍（`LvmThinPoolOverprovisioned` の閾値は 1.5）。
- 仮想ディスクはすべて `discard` を有効にし、毎週 `fstrim` で未使用ブロックを pool に返す。
- 使用率は `LvmThinPoolDataHigh`（75%）と `Critical`（90%）で見る。メタデータも同様。
- VG に未割当の余りは、pool 拡張の余地として使える（`lvextend`）。余りがなければ、ディスク追加か VM ディスクの縮小になる。
- 詳細は [thin pool 枯渇の障害記録](../../incidents/2026-10-22-lvm-thin-exhaustion.md)。

## 資源の見張り方

| 見たいもの | アラート（[監視・アラート](../05_operations-maintainability/monitoring.md)） |
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
5. 配分の表（この文書と [README.md](../../../README.md)）を更新する。

## 既知の限界

- ストレージが NVMe 1 枚で、容量にも故障にも余裕がない。NAS の導入（TrueNAS）はロードマップの未着手項目。
- CPU・メモリの実測の推移は、まだ設計の根拠として整理していない。
- Prometheus の保持上限 5GB は暫定値で、実測で調整する。
