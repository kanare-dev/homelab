# バックアップ

## 方針（2026-10-22 決定）

判断の記録: [ADR-0001](../adr/0001-no-vm-backup.md)

- **VM 全体のバックアップ（vzdump）は当面行わない。** 自動バックアップのジョブは設定していない（INC-2026-10-22 の調査で、ジョブもダンプも存在しないことを確認した）。
- 理由:
  - VM は Terraform / Ansible で再現できる。
  - vm-code・vm-dev は Git 管理のリポジトリだけを扱う（未 push の作業を置かない運用）。
  - vm-windows は検証用で、重要データがない。
  - 保存先が `local`（PVE と同じ NVMe、空き約 48GiB）しかなく、ディスク故障に備えにならない。
- 守る対象は **VM の外にある再現不能データ**（Mac にしかないシークレット類など）。一覧と退避先は非公開の台帳（リポジトリ外）で管理する。
- **再検討する条件**: NAS や外部ストレージを追加したとき、VM に再現できないデータを置くようになったとき、vm-windows を実用に使い始めたとき。その場合は Proxmox Backup Server か `vzdump` を別ストレージ向けに設定する。

## （参考）手動で vzdump を取る場合

```bash
# Proxmox ホスト上で実行。local は PVE と同じディスクのため、容量と障害時の備えに注意
vzdump <vmid> --storage local --compress zstd --mode snapshot
```

## Docker ボリュームバックアップ

```bash
# Prometheus データバックアップ
docker run --rm -v monitoring_prometheus_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup-$(date +%Y%m%d).tar.gz -C /data .

# Grafana データバックアップ
docker run --rm -v monitoring_grafana_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup-$(date +%Y%m%d).tar.gz -C /data .
```

## 設定ファイルバックアップ

このリポジトリ自体が設定のバックアップ。機密値は SOPS で暗号化して Git に入っているため、**age 秘密鍵があれば全て復号できる**（「秘密情報管理」参照）。次は Git に入らないので別途保管する:

- age 秘密鍵（iCloud Keychain に退避）
- SSH 秘密鍵
