# 運用 Runbook

日常の運用・障害対応の手順書。設計の背景は [architecture/](../../architecture/01-overview.md)、サービスごとの詳細は [services/](../../services/01-dns.md) を参照。

番号は種類を表す。01〜09 は日常の運用、11〜19 は障害対応。新しい手順は、該当する範囲の次の番号を振り、この表に追加する。

## 日常の運用

| 手順 | 内容 |
| --- | --- |
| [VM の自動起動・停止](01-vm-startup-shutdown.md) | 起動順序、手動での起動・停止 |
| [更新](02-updates.md) | OS、Docker イメージ、Terraform Provider の更新 |
| [秘密情報の管理](03-secrets.md) | SOPS + age。編集、別の Mac での復元、鍵のローテーション |
| [TLS 証明書](04-tls-certificates.md) | 証明書の確認・更新、サービスの追加 |
| [Slack アラート通知](05-slack-alerts.md) | Webhook の登録、通知テスト、主なルール |
| [バックアップの手順](06-backup-restore.md) | HA の設定・n8n のワークフローの取り込み、FreshRSS の購読リストの退避、手動の取り方 |

## 障害対応

| 症状 | 手順 |
| --- | --- |
| VM・サービス・DNS・Prometheus・Grafana の不調 | [障害時の切り分け](11-troubleshooting.md) |
| thin pool が 90% を超えた | [ストレージの復旧](12-storage-recovery.md) |
| PVE の管理画面が開かない | [PVE 管理画面の復旧](13-pve-webui-recovery.md) |
| VM のコンソールが接続と切断を繰り返す | [コンソールの再接続](14-vm-console-reconnect.md) |
| `terraform apply` で VM が再起動する | [apply による再起動](15-terraform-apply-restart.md) |

障害の記録は [incidents/](../incidents/README.md)。
