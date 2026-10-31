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

## Git に入らないものの退避

age 秘密鍵は iCloud Keychain に退避する（[秘密情報の管理](03-secrets.md#age-秘密鍵)）。SSH 鍵、Terraform の state、証明書などは、非公開の台帳に追記する（`private/secrets-inventory.md`。実体は iCloud Drive で、Git 管理外）。

## （参考）手動で vzdump を取る

通常は使わない。`local` は PVE と同じディスクのため、容量が圧迫され、ディスク故障の備えにもならない。

```bash
# Proxmox ホスト上で実行
vzdump <vmid> --storage local --compress zstd --mode snapshot
```
