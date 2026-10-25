# 0010. 外部 Heartbeat（Healthchecks.io）で監視 VM の停止を検知する

- ステータス: 採用（導入作業中）
- 日付: 2026-10-25

## 背景

[ADR-0002](0002-no-external-monitoring.md) では、PVE ホストや監視 VM の停止を検知する外部監視を見送り、リスクを受け入れた。
2026-10-25 に PVE ホストの NIC（`e1000e`）が送信を止め、ホストと全 VM が LAN から消えた。通知は 1 通も届かず、利用者が気づくまで検知できなかった（[INC-2026-10-25](../operations/incidents/2026-10-25-nic-hardware-unit-hang.md)）。
ADR-0002 の再検討の条件（再び監視 VM を巻き込む障害が起きた場合）に該当した。

## 決定

`Watchdog`（常に発報しているアラート）を、Alertmanager の webhook で Healthchecks.io に 5 分毎に送る。一定時間届かなくなったら、Healthchecks.io から通知する。
ADR-0002 の案 A を採用する。

## 理由

- 監視 VM、PVE ホスト、NIC、回線のどれが止まっても、**ホストの外から**検知できる。今回の障害を検知できる。
- 無料枠で足りる。追加の VM やハードが要らない。
- 外向きの HTTPS 通信だけで済み、ポート開放が要らない（[二重 NAT](../architecture/03-network.md#回線と-wan) でも動く）。
- 既存の `Watchdog` を使うので、ルールの追加が要らない。通知経路（Alertmanager）も含めた死活確認になる。

## 代替案

ADR-0002 の案 B〜E のうち、B（別ホスト）と C（VPS）は、ハードや費用の運用負担が増えるので見送る。D（別ストレージ）は NIC の停止を防げない。

## 影響と再検討の条件

- ping URL が増える。SOPS で管理する（`heartbeat_ping_url`。[秘密情報管理](../operations/runbooks/secrets.md)）。URL を知っていれば誰でも ping できるため、漏えいしたら再発行する。
- 回線断や停電でも通知が出る（ホストの外から見るため）。これは意図した挙動で、障害の種類（ホスト停止か回線断か）は通知だけでは区別できない。
- 外部サービス（Healthchecks.io）に依存する。無料枠の条件の変更や、サービスの終了があれば再検討する。
- 通知先は、Slack ではなく、回線が止まっても届く経路（メール、スマホ通知）にする。Slack は Alertmanager 経由なので、ホストが止まると届かない。
