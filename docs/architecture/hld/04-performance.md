# 第4章 性能・拡張性

この章では、ホストの資源とその配分、ストレージの設計、資源の見張り方、拡張の方針、既知の限界をまとめる。物理構成と、VM ごとの vCPU・メモリ・ディスクを示した論理構成は、[第1章](01-system.md)にある。

## ホストの資源

| 資源 | 容量 | 備考 |
| --- | --- | --- |
| CPU | i5-10400T（6 コア 12 スレッド） | 省電力版 |
| メモリ | 24GB（8GB + 16GB） | 2026-10 に 8GB から増設 |
| ストレージ | 256GB NVMe。`local-lvm`（thin pool `pve/data`）は約 155GiB | 全 VM のディスクがこの pool を共有する |
| NIC | 1 つ | スイッチとの間は、全 VLAN をタグ付きで通す trunk にしている（[第5章 ネットワーク](05-network.md#配置の方針)）。`e1000e` の送信停止（INC-2026-10-25）への対処として、`nic0` の TSO/GSO/GRO を無効にしている（`ansible/roles/proxmox`） |

## 配分

VM ごとの vCPU、メモリ、ディスクは、[論理構成](01-system.md#論理構成)の表が正である。ここでは、実際の使用量と、全体の収支を示す。

| 対象 | 実使用（目安） | 備考 |
| --- | --- | --- |
| Proxmox ホスト | — | メモリを約 2GB 確保する（ホスト側の余裕を削りすぎない） |
| `vm-infra` | 約 500MB | |
| `vm-monitoring` | 約 660MB | |
| `vm-apps` | 約 1.6GB | OS と Homepage（約 100MB）、Home Assistant（約 620MB）、n8n（約 360MB）、FreshRSS（待機時で約 20MB）を含む（2026-10-30。FreshRSS は 2026-11-01 に追加）。割当（4GB）には余裕がある |
| `vm-omada` | 約 1.5〜2GB（見込み） | MongoDB を含む Java アプリ。機器を採用したあとに実測して直す |
| `vm-code` / `vm-dev` | — | `vm-dev` は手動起動 |

- 常時起動する VM に割り当てたメモリの合計は 15.5GB である（`vm-omada` の 4GB を含む。`vm-omada` は 2026-11-09 に 3GB から増やした。[INC-2026-11-09](../../operations/incidents/2026-11-09-omada-memory-exhaustion.md)）。`vm-dev` を加えると 16.5GB になり、ホストが確保する約 2GB を足すと 18.5GB になるので、24GB に収まる。`vm-windows` は 2026-11-05 に削除した。8GB を使うため、起動すると 24GB を超えていたからである（作り直す手順は[バックアップの手順](../../operations/runbooks/06-backup-restore.md#vm-windows-の削除と作り直し2026-11-05)にある）。
- vCPU は、物理スレッドの数より多く割り当てている（常時起動する VM の合計で 10 vCPU、全 VM の合計で 16 vCPU）。常に高負荷になる VM がないことを前提にしている。
- `vm-apps` は、Home Assistant、n8n、FreshRSS を載せても、割り当てたメモリに余裕がある。

## ストレージの設計

- thin provisioning を使い、pool の容量より多くのディスクを割り当てている。割り当てた合計は 163.5G で、pool（155.6G）の約 1.05 倍である（2026-11-05 時点）。`vm-windows` を削除し、`vm-dev` のディスクを 30G から 10G に減らしたことで、1.57 倍から下げた。`LvmThinPoolOverprovisioned` の閾値は 1.5 倍である。`vm-omada` を追加した 2026-11-03 には、1.44 倍から 1.57 倍に増えて、アラートが出ていた。
- 仮想ディスクにはすべて `discard` を有効にし、毎週 `fstrim` を実行して、未使用のブロックを pool に返している。
- 使用率は、`LvmThinPoolDataHigh`（75%）と `LvmThinPoolDataCritical`（90%）で見張る。メタデータにも、同じ考え方のアラートを置いている。
- VG に未割り当ての余りがあれば、`lvextend` で pool を拡張できる。余りがなければ、ディスクを追加するか、VM のディスクを縮小する。
- 詳しくは [thin pool 枯渇の障害記録](../../operations/incidents/2026-10-22-lvm-thin-exhaustion.md)を参照してほしい。

## 資源の見張り方

| 見たいもの | アラート（[監視・アラート](../lld/platform/monitoring.md)） |
| --- | --- |
| CPU の逼迫 | `HostCpuHigh`（85%、15 分）/ `HostCpuCritical`（95%、10 分） |
| メモリの逼迫・OOM | `HostMemoryLow`（利用可能 10% 未満）/ `HostMemoryCritical`（5%）、`HostOomKilled` |
| ディスクの逼迫 | `HostDiskUsageHigh`（80%）/ `Critical`（90%） |
| thin pool の逼迫 | `LvmThinPoolData*`、`LvmThinPoolMetadata*`、`LvmThinPoolOverprovisioned` |

Grafana の「Storage / Thin Pool」ダッシュボードで、pool と VM ディスク別の割当・増加ペースを確認できる。

## 拡張の方針

**拡張は、1 台の資源を増やす垂直拡張だけを前提にする。** クラスタ化や負荷分散は、個人利用の規模では行わない。

| 状況 | 対応 |
| --- | --- |
| VM のメモリ・CPU が足りない | `terraform.tfvars` の `memory` / `cores` を変更する（再起動が必要な場合は 1 台ずつ） |
| ディスクが足りない | まず `fstrim` と不要データの整理を行う。それでも足りなければ、VG の余りで pool を拡張するか、ディスクを追加する |
| ホストのメモリが足りない | 配分を見直し、常時起動しない VM を止める。それでも足りなければ SO-DIMM を交換する（最大容量はモデルの仕様を確認する） |
| 重い構成を載せたい（k3s など） | 学習用として分離して運用する。安定して稼働しているサービスは、当面 Docker Compose のまま動かす（ロードマップ） |
| 複数ホストが必要になった | Proxmox クラスタと共有ストレージ（NAS）を検討する。現在の設計では対象にしていない |

### VM を追加する手順

1. `terraform/proxmox/terraform.tfvars` の `vms` に定義を追加し、`terraform plan` と `terraform apply` を実行する。
2. `ansible/inventory/hosts.yml` にホストを追加し、`group_vars` / playbook を用意して Ansible で設定する。
3. 必要であれば、`dns_records`（`group_vars/infra/vars.yml`）と Caddyfile に追記し、`playbooks/infra.yml` を実行する。
4. `prometheus.yml` で、Prometheus の scrape 対象とアラートの対象に加える。HTTPS で公開するサービスは、外形監視の `blackbox_http` にも URL を追加する。
5. 配分の表（この文書と [システム概要](01-system.md)）と構成図を更新する。

## 既知の限界

- ストレージが NVMe 1 枚だけなので、容量にも故障にも余裕がない。NAS（TrueNAS）の導入は、ロードマップに載せているが、まだ着手していない。
- CPU とメモリの実測値の推移は、まだ設計の根拠として整理していない。
- Prometheus のデータの保持上限 5GB は暫定の値なので、実測しながら調整する。
