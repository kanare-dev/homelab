# Slack アラート通知

Prometheus のアラートは Alertmanager 経由で Slack に通知する（INC-2026-10-22 の再発防止）。

## 構成

```text
pve (pve-storage-metrics.timer, 1分毎)
  -> node_exporter textfile collector (:9100)
  -> Prometheus (alerts.yml)  -> Alertmanager (:9093) -> Slack Incoming Webhook
                                                          critical: critical 用チャンネル（1 時間毎に再通知）
                                                          それ以外: warning 用チャンネル（24 時間毎に再通知）
```

通知先は重要度で分ける。再通知の間隔など、詳細は [monitoring.md](../../services/platform/monitoring.md#通知の挙動) にある。

## Webhook URL の登録

1. Slack で App を作成し、Incoming Webhooks を有効化して、チャンネルごとに Webhook URL を発行する。critical 用と warning 用の 2 チャンネルが要る。
2. SOPS で登録する（URL は Git に平文で置かない。値はチャットに貼らない）。

   ```bash
   sops ansible/inventory/group_vars/monitoring/secrets.sops.yml
   # 追記: slack_webhook_url: "https://hooks.slack.com/services/..."          （critical 用）
   # 追記: slack_webhook_url_warning: "https://hooks.slack.com/services/..."  （warning 用）
   ```

3. デプロイする。

   ```bash
   ansible-playbook -i inventory/hosts.yml playbooks/monitoring.yml
   ```

## 通知テスト（デプロイ後に必ず実施）

```bash
# 疑似アラートを Alertmanager に直接送る
curl -XPOST https://alertmanager.lab.kanare.dev/api/v2/alerts -H 'Content-Type: application/json' \
  -d '[{"labels":{"alertname":"TestAlert","severity":"warning","instance":"manual"},"annotations":{"summary":"通知テスト"}}]'
```

`severity` を `warning` にすると warning 用チャンネルへ、`critical` にすると critical 用チャンネルへ届く。両方で確認する。

## 主なルール

| アラート | 条件 | 重大度 |
| --- | --- | --- |
| LvmThinPoolDataHigh / Critical | thin pool Data% > 75% / 90% | warning / critical |
| LvmThinPoolMetadataHigh / Critical | thin pool Meta% > 75% / 90% | warning / critical |
| PveVmIoError | VM が io-error | critical |
| HostDiskUsageHigh / Critical | ファイルシステム > 80% / 90% | warning / critical |
| TargetDown | scrape 先が 3 分以上 down | critical |
| PveStorageMetricsStale | thin pool メトリクスが 5 分以上更新されない | warning |

## 既知の限界

監視 VM (vm-monitoring) は同じ Proxmox ストレージ上にある。ストレージや NIC の障害時は Alertmanager も停止し、Slack に通知が届かない。
外部 Heartbeat で補う（[monitoring.md](../../services/platform/monitoring.md#外部-heartbeat)、[ADR-0010](../../adr/0010-external-heartbeat.md)）。
