# 運用 Runbook

日常の運用・障害対応の手順書。設計の背景は [architecture/](../../architecture/overview.md)、サービスごとの詳細は [services/](../../services/dns.md) を参照。

## 日常の運用

| 手順 | 内容 |
|---|---|
| [VM の自動起動・停止](vm-startup-shutdown.md) | 起動順序、手動での起動・停止 |
| [更新](updates.md) | OS、Docker イメージ、Terraform Provider の更新 |
| [秘密情報の管理](secrets.md) | SOPS + age。編集、別の Mac での復元、鍵のローテーション |
| [TLS 証明書](tls-certificates.md) | 証明書の確認・更新、サービスの追加 |
| [Slack アラート通知](slack-alerts.md) | Webhook の登録、通知テスト、主なルール |
| [バックアップ・復旧](../backup-restore.md) | バックアップの方針と手動の取り方 |

## 障害対応

| 症状 | 手順 |
|---|---|
| VM・サービス・DNS・Prometheus・Grafana の不調 | [障害時の切り分け](troubleshooting.md) |
| thin pool が 90% を超えた | [ストレージの復旧](storage-recovery.md) |
| PVE の管理画面が開かない | [PVE 管理画面の復旧](pve-webui-recovery.md) |
| VM のコンソールが接続と切断を繰り返す | [コンソールの再接続](vm-console-reconnect.md) |
| `terraform apply` で VM が再起動する | [apply による再起動](terraform-apply-restart.md) |

障害の記録は [incidents/](../incidents/2026-10-22-lvm-thin-exhaustion.md)。
