# ThinkCentre M70q Tiny の設定

Proxmox ホスト（`pve`）の、ホスト単体の設定値（詳細設計）。**この文書を、ホストの設定値の正とする。** 機器の仕様と公式資料は [spec.md](spec.md)。VM ごとの割当と、ホストの資源の収支は[インフラ構成](../../architecture/02-infrastructure.md)、VLAN のブリッジとポートは [VLAN 設計](../../architecture/08-vlan-design.md)、監視は[監視・アラート](../../services/platform/monitoring.md)にある。

- 設定を変えたら、**同じ変更でこの文書を更新**し、[変更履歴](#変更履歴)に 1 行足す。
- ホストの設定は Ansible（`ansible/roles/proxmox/`）と、手で入れた設定（`/etc/network/interfaces` など）に分かれる。Ansible にあるものは、その旨を「管理」の列に書く。

## 設定値

| 項目 | 現在 | 段階 3 の後 | 管理 |
| --- | --- | --- | --- |
| ホスト名 | `pve` | 同じ | |
| IP | `192.168.11.10`（`vmbr0`） | `10.77.10.10/24`（タグ付きの `vmbr0.10`。VLAN10 Management）。`vmbr0` は VLAN-aware にして、IP を持たせない | `/etc/network/interfaces`（手動）。切り替えの手順は [VLAN 設計](../../architecture/08-vlan-design.md) |
| OS | Proxmox VE 9.x（Debian 13 ベース） | 同じ | |
| 物理 NIC | `nic0`（Intel I219、ドライバ `e1000e`）1 つ。スイッチへのポートは、段階 2 以降は SG2210P の p2 | trunk（VLAN10/20/40/50/70 を tagged） | [SG2210P の設定](../sg2210p/settings.md) |
| NIC のオフロード | `nic0` の TSO・GSO・GRO を無効にする（`e1000e` の送信停止への対処。[INC-2026-10-25](../../operations/incidents/2026-10-25-nic-hardware-unit-hang.md)）。`/etc/network/interfaces` の `post-up` と、実行中の NIC への適用の両方 | 同じ | Ansible（`ansible/roles/proxmox`） |
| Web UI | `https://pve.lab.kanare.dev`（Caddy → `192.168.11.10:8006`）。サブスクリプションの警告ポップアップを除去している（[INC-2026-10-22-b](../../operations/incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md)。パッケージ更新で戻ったら、Ansible を再実行する） | `10.77.10.10:8006`（Management。VM と同じネットワークには載らない） | Ansible |
| ストレージ | 256GB NVMe。`local-lvm`（thin pool `pve/data`）約 155GiB を、全 VM のディスクが共有する。割当は pool の約 1.05 倍（2026-11-05） | 同じ | 割当の正は `terraform/proxmox/terraform.tfvars`。経緯は [INC-2026-10-22](../../operations/incidents/2026-10-22-lvm-thin-exhaustion.md) |
| ストレージの監視 | thin pool の使用率と、VM の io-error を、1 分ごとに node_exporter のテキストファイル（`pve-storage-metrics.timer`）で出す。アラートは `LvmThinPoolData*`、`LvmThinPoolMetadata*`、`LvmThinPoolOverprovisioned`（閾値 1.5）など | 同じ | Ansible。アラートは[監視・アラート](../../services/platform/monitoring.md) |
| メモリ | 24GB。ホスト用に約 2GB を確保して、VM の割当を決める | 同じ | [インフラ構成](../../architecture/02-infrastructure.md#配分) |
| VM の自動起動・停止 | VM ごとの `onboot` と `startup`（起動順序と待機秒数）を設定している | 同じ | Terraform。手順は [VM 自動起動・停止](../../operations/runbooks/01-vm-startup-shutdown.md) |
| 電源 | UPS なし。1 台に全 VM が載る単一障害点 | 同じ | [可用性・信頼性](../../architecture/04-reliability.md) |

## 未確認

BIOS の設定は、この文書にまだ無い。次を、本体の BIOS 画面で確認して、この表に足す。

| 項目 | 内容 |
| --- | --- |
| 停電から復帰したときの自動起動（AC 電源の復帰） | 無停電電源が無いので、停電のあとに自動で起動するかどうかが、復旧の手間を左右する。未確認 |
| 仮想化支援（VT-x、VT-d） | Proxmox が動いているので VT-x は有効のはず。VT-d は未確認 |
| Wake-on-LAN | PSREF は対応と書いている。BIOS での有効・無効は未確認 |
| BIOS・ファームウェアの版、BIOS パスワード | 未確認（パスワードの値は、この文書に書かず、台帳へ） |

## 変更履歴

| 日付 | 内容 |
| --- | --- |
| 2026-11-06 | この文書を作成した。[インフラ構成](../../architecture/02-infrastructure.md)、[VLAN 設計](../../architecture/08-vlan-design.md)、Ansible の `proxmox` ロール、Runbook に分かれていたホスト単体の設定を集約した（値の変更は無い） |
