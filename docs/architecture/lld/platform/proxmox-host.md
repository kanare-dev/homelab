# Proxmox ホスト（ThinkCentre M70q Tiny）の設定

Proxmox ホスト（`pve01`）の、ホスト単体の設定値（詳細設計）。**この文書を、ホストの設定値の正とする。** 機器の仕様と公式資料は [ThinkCentre M70q Tiny の資料](../hardware/thinkcentre-m70q-tiny.md)。VM ごとの割当と、ホストの資源の収支は[システム構成・環境](../../hld/01-system.md)、VLAN のブリッジとポートは [第5章 ネットワーク](../../hld/05-network.md)、監視は[監視・アラート](monitoring.md)にある。

- 設定を変えたら、**同じ変更でこの文書を更新**し、[変更履歴](#変更履歴)に 1 行足す。
- ホストの設定は Ansible（`ansible/roles/proxmox/`）と、手で入れた設定（`/etc/network/interfaces` など）に分かれる。Ansible にあるものは、その旨を「管理」の列に書く。

## 設定値

| 項目 | 現在 | 管理 |
| --- | --- | --- |
| ホスト名 | `pve01`（FQDN は `pve01.lab.kanare.dev`。2026-11-24 に `pve` から変更。確認済み）。Proxmox のノード名も `pve01`。管理画面の `pve.lab.kanare.dev` は、ホスト名ではなくサービス名なので、そのまま残している | `/etc/hostname` と `/etc/hosts`（手動）。手順は[手順書 26](../../../operations/runbooks/26-rename-pve-host-to-pve01.md) |
| IP | `10.77.10.10/24`（タグ付きの `vmbr0.10`。VLAN10 Management。ゲートウェイ `10.77.10.1`）。`vmbr0` は VLAN-aware で、IP を持たない。 | `/etc/network/interfaces` と `/etc/hosts`（手動。`/etc/hosts` の `pve` の行も、同じ IP）。手順は[手順書 24](../../../operations/runbooks/24-pve-move-to-vmbr0-10.md) |
| DNS | `10.77.10.1`（Management のルーター。ER605 の DNS プロキシ）。検索ドメインは `local`（インストール時の値）。内部の名前（`*.lab.kanare.dev`）は引けないので、IP で入る。`vm-infra`（AdGuard）に向けないのは、ホストが自分の上で動く VM に頼る循環を避けるため（[ADR-0007](../../../adr/0007-vm-host-dns-is-router.md)）。2026-11-26 までは、インストール時の建物の共用ルーター（`172.22.0.1`）だった。**Proxmox の画面（System > DNS）では変えない**（Ansible が上書きする） | Ansible（`ansible/roles/proxmox`。`/etc/resolv.conf`） |
| NTP | chrony。`ntp.nict.jp` と `time.google.com`（VM と同じ `ntp_servers`）。Debian の既定の `pool 2.debian.pool.ntp.org` は、コメントにして止めている。2026-11-26 までは、既定の pool だった | Ansible（`ansible/roles/proxmox`。`/etc/chrony/sources.d/homelab.sources`） |
| ホストのファイアウォール | 無い。Proxmox ファイアウォールは無効、UFW は入っていない（2026-11-26 に確認）。Management への通信は、ゲートウェイの ACL で絞る（[ADR-0034](../../../adr/0034-acl-for-vlan-boundaries-ufw-for-ports.md)） | |
| OS | Proxmox VE 9.1.7（Debian 13 ベース。カーネル 6.17.2-1-pve。2026-11-08 に確認） | |
| 物理 NIC | `nic0`（Intel I219、ドライバ `e1000e`）1 つ。スイッチへのポートは SG2210P の p2。全 VLAN をタグ付きで通す trunk にしている | [SG2210P のポート](../network/omada/device-sw01.md#ポート) |
| NIC のオフロード | `nic0` の TSO・GSO・GRO を無効にする（`e1000e` の送信停止への対処。[INC-2026-10-25](../../../operations/incidents/2026-10-25-nic-hardware-unit-hang.md)）。`/etc/network/interfaces` の `post-up` と、実行中の NIC への適用の両方 | Ansible（`ansible/roles/proxmox`） |
| Web UI | `https://pve.lab.kanare.dev`（Caddy → `10.77.10.10:8006`）。サブスクリプションの警告ポップアップを除去している（[INC-2026-10-22-b](../../../operations/incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md)。パッケージ更新で戻ったら、Ansible を再実行する） | Ansible |
| ストレージ | 256GB NVMe。`local-lvm`（thin pool `pve/data`）約 155GiB を、全 VM のディスクが共有する。割当は pool の約 1.05 倍（2026-11-05） | 割当の正は `terraform/proxmox/terraform.tfvars`。経緯は [INC-2026-10-22](../../../operations/incidents/2026-10-22-lvm-thin-exhaustion.md) |
| ストレージの監視 | thin pool の使用率と、VM の io-error を、1 分ごとに node_exporter のテキストファイル（`pve-storage-metrics.timer`）で出す。アラートは `LvmThinPoolData*`、`LvmThinPoolMetadata*`、`LvmThinPoolOverprovisioned`（閾値 1.5）など | Ansible。アラートは[監視・アラート](monitoring.md) |
| メモリ | 24GB。ホスト用に約 2GB を確保して、VM の割当を決める | [インフラ構成](../../hld/04-performance.md#配分) |
| VM の自動起動・停止 | VM ごとの `onboot` と `startup`（起動順序と待機秒数）を設定している | Terraform。手順は [VM 自動起動・停止](../../../operations/runbooks/01-vm-startup-shutdown.md) |
| 電源 | UPS なし。1 台に全 VM が載る単一障害点 | [信頼性](../../hld/02-reliability.md) |

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
| 2026-11-26 | **DNS を `172.22.0.1`（建物の共用ルーター）から `10.77.10.1`（ER605）に、NTP を Debian の既定の pool から `ntp.nict.jp`・`time.google.com` に変えた**（Ansible の `proxmox` ロールに足した）。WAN 側の上流に依存しないようにし、ACL で Management → 他の VLAN を拒否しても困らないようにするため。事前に、`pve01` から `dig @10.77.10.1` で外部の名前が引けることを確かめた。適用のあと、`getent hosts` と `download.proxmox.com` への HTTPS が通り、chrony が `ntp.nict.jp`（`^*`）に同期し、Prometheus の `pve01` が `up` のまま。再実行で変更 0 件。予測が外れた点は無かった（運用者の指示。Claude Code が実施） |
| 2026-11-24 | **ホスト名を `pve` から `pve01` に変えた**（将来、ホストを増やすため。21:00 ごろ。再起動と VM の復帰を含めて、VM は約 20 分止まった）。`/etc/hostname`、`/etc/hosts` を直して再起動し、VM の設定を `/etc/pve/nodes/pve01/` へ移した。管理画面は `pve.lab.kanare.dev` のまま。Terraform の `plan` は変更 0 件。CoreDNS に `pve01`（`10.77.10.10`）を足した。予測が外れた点は[手順書 26](../../../operations/runbooks/26-rename-pve-host-to-pve01.md)の「実績」（運用者の指示。Claude Code が実施） |
| 2026-11-19 | **IP を `192.168.11.10`（`vmbr0`、タグなし）から `10.77.10.10/24`（`vmbr0.10`、VLAN10、GW `10.77.10.1`）に移した**（段階 3b の残り。23:03〜23:05）。`/etc/network/interfaces` で `vmbr0` を `inet manual` にし、`vmbr0.10` を足した。`/etc/hosts` の `pve` の行も直した。`ifreload -a` で反映し、SSH は約 50 秒で、新しい IP から再接続できた。VM は動き続けた。10 分後に元に戻すタイマーを仕掛けたが、確認が通ったので止めた。事前に、設定を iCloud Drive に退避した（`pve-interfaces-bk-20261119.txt`、`pve-hosts-bk-20261119.txt`）。詳細は[手順書 24](../../../operations/runbooks/24-pve-move-to-vmbr0-10.md)（運用者の指示。Claude Code が実施） |
| 2026-11-06 | この文書を作成した。[システム構成・環境](../../hld/01-system.md)、[第5章 ネットワーク](../../hld/05-network.md)、Ansible の `proxmox` ロール、Runbook に分かれていたホスト単体の設定を集約した（値の変更は無い） |
