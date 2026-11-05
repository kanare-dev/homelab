# バックアップの手順

VM 全体のバックアップは取らない（判断は [ADR-0001](../../adr/0001-no-vm-backup.md)）。何を守り、何を守らないかは [災害対策](../../architecture/07-disaster-recovery.md#バックアップの状況)。このページは、守る対象を実際に取り込む手順だけを書く。

## Home Assistant の設定を Git に取り込む

画面で編集した `automations.yaml` / `scripts.yaml` / `scenes.yaml` は、変更したら取り込んでコミットする（`configuration.yaml` は Git が正。[ADR-0011](../../adr/0011-home-assistant-on-vm-apps.md)）。

```bash
make ha-config-pull
```

失ったときの手順は [Home Assistant の復旧](../../services/05-home-assistant.md#復旧)。

## n8n のワークフローを Git に取り込む

画面でワークフローを作る、または変えたら、取り込んでコミットする（[ADR-0012](../../adr/0012-n8n-on-vm-apps.md)）。

```bash
make n8n-workflows-pull
```

失ったときの手順は [n8n の復旧](../../services/06-n8n.md#復旧)。

## FreshRSS の購読リストを退避する

フィードを足す、または整理したら、iCloud Drive に書き出す（Git には入れない。[ADR-0014](../../adr/0014-freshrss-on-vm-apps.md)）。

```bash
make freshrss-opml-pull FRESHRSS_USER=<ユーザー名>
```

失ったときの手順は [FreshRSS の復旧](../../services/09-freshrss.md#復旧)。

## Git に入らないものの退避

age 秘密鍵は iCloud Keychain に退避する（[秘密情報の管理](03-secrets.md#age-秘密鍵)）。SSH 鍵、Terraform の state、証明書などは、非公開の台帳に追記する（`private/secrets-inventory.md`。実体は iCloud Drive で、Git 管理外）。

## （参考）手動で vzdump を取る

通常は使わない。`local` は PVE と同じディスクのため、容量が圧迫され、ディスク故障の備えにもならない。

```bash
# Proxmox ホスト上で実行
vzdump <vmid> --storage local --compress zstd --mode snapshot
```

## vm-windows の退避（2026-11-05）

thin pool の過剰割当（`LvmThinPoolOverprovisioned`）を解消するため、`vm-windows`（VMID 130、60G。Windows 11 のセットアップ済み）を削除した。削除の前に、1 回だけ vzdump を取った。定期バックアップではない（[ADR-0001](../../adr/0001-no-vm-backup.md)）。

| 項目 | 内容 |
| --- | --- |
| 場所 | `pve:/var/lib/vz/dump/vzdump-qemu-130-2026_11_05-23_49_17.vma.zst`（`local`。24GB。`zstd -t` で確認済み） |
| 取り方 | `vzdump 130 --storage local --compress zstd --mode stop` |
| 制約 | pool と同じ NVMe にあり、ディスク故障には備えにならない。`local` の空きを 24GB 使う |

復元するとき:

```bash
# 復元する前に、割当の合計を確認する（復元すると 60G とメモリ 8GB が戻る）。
# 比率は約 1.05 → 約 1.5 になり、しきい値に近い。`vm-dev` を縮めるなどして空けてから戻す
qmrestore /var/lib/vz/dump/vzdump-qemu-130-2026_11_05-23_49_17.vma.zst 130 --storage local-lvm
```

- 復元した VM は、Terraform の管理外になる（`windows.tf` は削除した）。使い続けるなら、`windows.tf` を戻して `terraform import` するか、手動管理のままにする。
- 復元する予定がなくなったら、ファイルを消して `local` を空ける。
