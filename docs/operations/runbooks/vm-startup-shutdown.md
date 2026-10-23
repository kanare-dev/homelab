# VM 自動起動・停止

## 概要

Proxmox の `onboot` および `startup` 設定で、ホスト起動・停止時の VM 制御を自動化している。
設定は Terraform で管理し、`terraform/proxmox/terraform.tfvars` の `onboot` / `startup` フィールドで定義する。

## 起動順序

ホスト (Proxmox) 起動時、以下の順で VM が自動起動する。依存関係（DNS → モニタリング → アプリ）に従った順序。

| 順序 | VM | onboot | startup | 役割 |
| ------ | ---- | ---- | --------- | ------ |
| 1 | vm-infra | true | `order=1,up=30,down=60` | DNS・リバースプロキシ（他 VM が依存） |
| 2 | vm-monitoring | true | `order=2,up=20,down=60` | Prometheus・Grafana |
| 3 | vm-apps | true | `order=3,up=20,down=60` | Homepage ダッシュボード |
| 4 | vm-dev | false | `order=4,up=10,down=30` | 開発用（手動起動のみ） |
| 5 | vm-code | true | `order=5,up=10,down=30` | Claude Code・CloudCLI・code-server |

`up` は次の VM を起動するまでの待機秒数。`down` はシャットダウン信号送信後の最大待機秒数。

## シャットダウン順序

ホストのシャットダウン時は `order` の**逆順**で ACPI シャットダウン信号が送られる（vm-code → vm-apps → vm-monitoring → vm-infra）。

## 設定の反映

```bash
# Terraform で設定を適用（vm-infra の例）
cd terraform/proxmox
terraform plan   # 差分確認（onboot / startup の変更が表示される）
terraform apply
```

## 手動での VM 起動・停止

```bash
# 個別起動（Proxmox ホスト上）
ssh root@192.168.11.10 "qm start <vmid>"

# 個別停止（ACPI シャットダウン）
ssh root@192.168.11.10 "qm shutdown <vmid>"

# 全 VM を起動順に一括起動（vm-dev は onboot=false のため対象外）
for vmid in 111 113 120 122; do
  ssh root@192.168.11.10 "qm start $vmid"
  sleep 30
done
```
