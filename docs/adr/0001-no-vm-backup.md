# 0001. VM のバックアップを取らない

- ステータス: 採用
- 日付: 2026-10-22

## 背景

INC-2026-10-22（[thin pool 枯渇](../operations/incidents/2026-10-22-lvm-thin-exhaustion.md)）の調査で、VM 全体のバックアップ（vzdump）のジョブもダンプも存在しないことを確認した。バックアップを取るべきかを検討した。

## 決定

VM 全体のバックアップは当面取らない。守る対象は **VM の外にある再現不能データ**（age 秘密鍵、SSH 鍵、Terraform の state など）に限り、非公開の台帳で管理する。

## 理由

- VM は Terraform / Ansible で再現できる。
- `vm-code`・`vm-dev` は Git 管理のリポジトリだけを扱う（未 push の作業を置かない運用）。
- `vm-windows` は検証用で、重要データがない。
- 保存先が `local`（PVE と同じ NVMe、空き約 48GiB）しかなく、ディスク故障に備えにならない。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| `vzdump` を `local` に取る | 同じディスクなので、ディスク故障の備えにならない。容量も圧迫する |
| Proxmox Backup Server / 別ストレージ | 現在、別ストレージがない（NAS 未導入） |

## 影響と再検討の条件

- 例外: Home Assistant の設定の YAML は Git で守る（[ADR-0011](0011-home-assistant-on-vm-apps.md)）。VM のバックアップではない。
- ホストやディスクを失うと、VM は再構築になる（[災害対策](../architecture/07-disaster-recovery.md)）。
- 次のいずれかになったら再検討する: NAS や外部ストレージを追加した、VM に再現できないデータを置くようになった、`vm-windows` を実用に使い始めた。

詳細: [バックアップ・復旧](../operations/backup-restore.md)
