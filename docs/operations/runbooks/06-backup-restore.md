# バックアップの手順

VM 全体のバックアップは取らない（判断は [ADR-0001](../../adr/0001-no-vm-backup.md)）。何を守り、何を守らないかは [災害対策](../../architecture/07-disaster-recovery.md#バックアップの状況)。このページは、守る対象を実際に取り込む手順だけを書く。

## Home Assistant の設定を Git に取り込む

画面で編集した `automations.yaml` / `scripts.yaml` / `scenes.yaml` は、変更したら取り込んでコミットする（`configuration.yaml` は Git が正。[ADR-0011](../../adr/0011-home-assistant-on-vm-apps.md)）。

```bash
make ha-config-pull
```

失ったときの手順は [Home Assistant の復旧](../../services/apps/home-assistant.md#復旧)。

## n8n のワークフローを Git に取り込む

画面でワークフローを作る、または変えたら、取り込んでコミットする（[ADR-0012](../../adr/0012-n8n-on-vm-apps.md)）。

```bash
make n8n-workflows-pull
```

失ったときの手順は [n8n の復旧](../../services/apps/n8n.md#復旧)。

## FreshRSS の購読リストを退避する

フィードを足す、または整理したら、iCloud Drive に書き出す（Git には入れない。[ADR-0014](../../adr/0014-freshrss-on-vm-apps.md)）。

```bash
make freshrss-opml-pull FRESHRSS_USER=<ユーザー名>
```

失ったときの手順は [FreshRSS の復旧](../../services/apps/freshrss.md#復旧)。

## Git に入らないものの退避

age 秘密鍵は iCloud Keychain に退避する（[秘密情報の管理](03-secrets.md#age-秘密鍵)）。SSH 鍵、Terraform の state、証明書などは、非公開の台帳に追記する（`private/secrets-inventory.md`。実体は iCloud Drive で、Git 管理外）。

## （参考）手動で vzdump を取る

通常は使わない。`local` は PVE と同じディスクのため、容量が圧迫され、ディスク故障の備えにもならない。

```bash
# Proxmox ホスト上で実行
vzdump <vmid> --storage local --compress zstd --mode snapshot
```

## vm-windows の削除と作り直し（2026-11-05）

thin pool の過剰割当（`LvmThinPoolOverprovisioned`）を解消するため、`vm-windows`（VMID 130、60G。Windows 11 のセットアップ済み）を削除した。削除の前に vzdump を 1 回だけ取ったが（24GB）、**復元しない方針にして、2026-11-06 に消した**（Mac などへの写しも取っていない）。バックアップは残っていない。

必要になったら、ISO から作り直す。

- ISO は Proxmox の `local` に残してある: `Win11_25H2_Japanese_x64_v2.iso`、`virtio-win-0.1.285.iso`。
- Terraform の定義は Git の履歴にある: `git show 3a7199c^:terraform/proxmox/windows.tf`。`terraform/proxmox/` に戻して `terraform apply -target=proxmox_vm_qemu.windows` する（`-target` を付けないと、他の VM も一緒に適用される）。EFI ディスクは、Terraform では作れないので、`windows.tf` のコメントのとおり Proxmox の画面で足す。
- **作る前に、割当を確認する。** 60G とメモリ 8GB が戻るので、割当の比率は約 1.05 → 約 1.5 になる（しきい値は 1.5）。`vm-dev` を縮める、または不要な VM を消して、空けてから作る。メモリは、`vm-dev` を止めて起動する（合計が 24GB を超える）。
