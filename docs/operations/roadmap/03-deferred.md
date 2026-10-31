# 見送り中の項目

[ロードマップ](README.md)のうち、検討したうえで導入を見送っているもの。見送った理由と、再検討する条件を残す。条件のどれかに該当したら、着手を判断する。

## uptime-kuma

見送り中（2026-10-27 時点では導入しない）。

- 現状: HTTPS と DNS の外形監視は blackbox-exporter + Alertmanager で行い、停止の検知は外部 Heartbeat（Healthchecks.io）が担う（[03-monitoring.md](../../services/03-monitoring.md)）
- 見送る理由: 死活監視と通知が blackbox-exporter と重なり、二重管理になる。Alertmanager の `inhibit_rules`（VM 停止・DNS 障害時の抑制）が使えず、障害のたびに通知が増える。vm-apps に置くと監視対象と同じホストで止まり、ホスト停止は検知できない
- 再検討する条件:
  - 家族など Grafana を見ない人向けに、ステータスページが必要になった
  - 外形監視のターゲット追加（`prometheus.yml` の編集とデプロイ）が負担になった
  - 回線断・停電を家の外から検知したくなり、外部の VPS を用意できた（[03-monitoring.md](../../services/03-monitoring.md) の案 C）

## Loki + Grafana Alloy（ログ収集基盤）

見送り中（2026-10-26 時点では導入しない）。

- 現状: ログは各ホストの journald（200M・1 か月）と Docker のログ上限（10MB × 3）に分散している。横断検索の手段はなく、調べるときは VM ごとに `ssh` して `journalctl` / `docker logs` を使う
- 見送る理由: INC-2026-10-25 の原因は PVE の journald（永続化済み）で追えた。ホストの NIC が止まると転送もできず、集約していても効果はなかった。ストレージの過剰割当（約 1.44 倍）が残っており、増え続けるログを足すリスクがある。収集エージェントを全ホストに入れる運用の手間も増える（[INC-2026-10-25](../incidents/2026-10-25-nic-hardware-unit-hang.md)）
- 再検討する条件:
  - 複数 VM をまたぐ原因調査に、手間を感じる場面が増えた
  - ストレージ障害でログごと消え、原因が追えなかった
  - アラートの前後のログを Grafana でメトリクスと並べて見たくなった
  - thin pool の過剰割当を解消した（容量に余裕ができた）
- 導入するときの方針（案）: `vm-monitoring` に Loki、全ホストに Grafana Alloy（Promtail は後継の Alloy に移行済み）。保持期間 14 日、容量の上限 3GB 程度から始める。ADR を追加し、`03-monitoring.md` の「容量の上限設定」の表も更新する

## Glances（Homepage の VM 別バー表示）

見送り中（2026-10-30 時点では導入しない）。

- 現状: Homepage の Hosts は、Prometheus の `node_exporter` から CPU・メモリ・ディスクの使用率を数値で出している（[Homepage](../../services/04-homepage.md)）。バー表示は、Homepage が動く `vm-apps` 自身だけを測る `resources` ウィジェットにしかない
- 見送る理由: 全 VM に Glances を入れる必要がある（Ansible のロール、公開ポートと `DOCKER-USER` / UFW の許可の追加）。`node_exporter` と同じ情報を二重に集めることになる。数値の表示で足りている
- 再検討する条件: 数値では状況をつかみにくく、バーで見たい場面が増えた
- 導入するときの方針（案）: 全 VM に Glances を入れ、Homepage の Glances ウィジェットで表示する。`vm-apps` の `resources` ウィジェットとは併用しない

## 方針のない候補

理由や設計を詰めていない候補。既存の構成で役割が足りているため、優先度は低い。必要になったら、上の項目のように理由と条件を書いてから着手する。

- Traefik（リバースプロキシは Caddy で足りている）
- telegraf + InfluxDB（メトリクスは Prometheus で足りている）
- Portainer（Docker の状態の可視化）
- VM テンプレートの Packer 化（テンプレートは Terraform + cloud-init で再現できる）
