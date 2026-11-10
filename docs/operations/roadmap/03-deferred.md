# 見送り中の項目

[ロードマップ](README.md)のうち、検討したうえで導入を見送っているもの、および導入後に外した（廃止した）もの。見送った理由と、再検討する条件を残す。条件のどれかに該当したら、着手を判断する。

## uptime-kuma

見送り中（2026-10-27 時点では導入しない）。

- 現状: HTTPS と DNS の外形監視は blackbox-exporter + Alertmanager で行い、停止の検知は外部 Heartbeat（Healthchecks.io）が担う（[monitoring.md](../../services/platform/monitoring.md)）
- 見送る理由: 死活監視と通知が blackbox-exporter と重なり、二重管理になる。Alertmanager の `inhibit_rules`（VM 停止・DNS 障害時の抑制）が使えず、障害のたびに通知が増える。vm-apps に置くと監視対象と同じホストで止まり、ホスト停止は検知できない
- 再検討する条件:
  - 家族など Grafana を見ない人向けに、ステータスページが必要になった
  - 外形監視のターゲット追加（`prometheus.yml` の編集とデプロイ）が負担になった
  - 回線断・停電を家の外から検知したくなり、外部の VPS を用意できた（[monitoring.md](../../services/platform/monitoring.md) の案 C）

## Loki + Grafana Alloy（ログ収集基盤）

見送り中（2026-10-26 時点では導入しない）。

- 現状: ログは各ホストの journald（200M・1 か月）と Docker のログ上限（10MB × 3）に分散している。横断検索の手段はなく、調べるときは VM ごとに `ssh` して `journalctl` / `docker logs` を使う
- 見送る理由: INC-2026-10-25 の原因は PVE の journald（永続化済み）で追えた。ホストの NIC が止まると転送もできず、集約していても効果はなかった。ストレージの過剰割当（約 1.44 倍）が残っており、増え続けるログを足すリスクがある。収集エージェントを全ホストに入れる運用の手間も増える（[INC-2026-10-25](../incidents/2026-10-25-nic-hardware-unit-hang.md)）
- 再検討する条件:
  - 複数 VM をまたぐ原因調査に、手間を感じる場面が増えた
  - ストレージ障害でログごと消え、原因が追えなかった
  - アラートの前後のログを Grafana でメトリクスと並べて見たくなった
  - thin pool の過剰割当を解消した（容量に余裕ができた）
- 導入するときの方針（案）: `vm-monitoring` に Loki、全ホストに Grafana Alloy（Promtail は後継の Alloy に移行済み）。保持期間 14 日、容量の上限 3GB 程度から始める。ADR を追加し、`monitoring.md` の「容量の上限設定」の表も更新する

## 回線速度の定期測定（Speedtest）

見送り中（2026-11-01 時点では導入しない）。

- 現状: 回線断と遅延は、blackbox-exporter の ICMP（30 秒毎）で見ている（[monitoring.md](../../services/platform/monitoring.md#回線の疎通遅延の監視)、[ADR 0018](../../adr/0018-internet-speed-monitoring.md)）
- 見送る理由: Speedtest は測定のたびに 30〜60 秒、回線を使い切る。仕事中のビデオ会議などに影響し、建物の共用回線にも負荷をかける。遅延とパケットロスでも、建物側の混雑は多くの場合に検知できる
- 再検討する条件:
  - 「遅いのに ping の遅延・ロスに出ていない」状況が起きた
  - 建物の管理会社や ISP に、速度（Mbps）の数字を示す必要が出た
  - 従量課金や上限のない回線になり、通信量を気にしなくてよくなった
- 導入するときの方針（案）: 平日 9〜18 時を避け、systemd timer で 1 日数回だけ測り、結果を `node_exporter` の textfile に書く（PVE の `pve-storage-metrics` と同じ方式）。Prometheus の scrape で測る方式（`speedtest-exporter`）は、時間帯を指定できないため使わない。通知は 7 日間の中央値の 60% 未満で出す

## Glances（Homepage の VM 別バー表示）

見送り中（2026-10-30 時点では導入しない）。

- 現状: Homepage の Hosts は、Prometheus の `node_exporter` から CPU・メモリ・ディスクの使用率を数値で出している（[Homepage](../../services/apps/homepage.md)）。バー表示は、Homepage が動く `vm-apps` 自身だけを測る `resources` ウィジェットにしかない
- 見送る理由: 全 VM に Glances を入れる必要がある（Ansible のロール、公開ポートと `DOCKER-USER` / UFW の許可の追加）。`node_exporter` と同じ情報を二重に集めることになる。数値の表示で足りている
- 再検討する条件: 数値では状況をつかみにくく、バーで見たい場面が増えた
- 導入するときの方針（案）: 全 VM に Glances を入れ、Homepage の Glances ウィジェットで表示する。`vm-apps` の `resources` ウィジェットとは併用しない

## Scanopy（ネットワーク探索・トポロジー図）

廃止（2026-07-17 に取りやめ）。VLAN 化のあとに再挑戦する余地がある。

- 経緯: 2026-04-04 に `vm-apps` へ導入した（Scanopy 本体と PostgreSQL、スキャンを行うデーモンを Docker Compose で稼働。`vm-apps` のメモリを 2GB から 4GB に増やした）。2026-07-17 に構成ごと取り除いた
- 外した理由: うまくスキャンできず、期待した効果が得られなかった。原因が Scanopy の限界なのか、設定や使い方の問題なのかは切り分けていない
- 再検討する条件:
  - [VLAN 化](04-network-omada-vlan.md)が終わり、VLAN ごとにデーモンを置いてスキャンできる構成になった
  - ネットワーク機器・端末の一覧や構成図を、手作業ではなく自動で作りたくなった
- 試すときの方針（案）: 最初から全 VLAN に広げず、1 つの VLAN で、スキャンが機器を検出できるかを確かめる。前回の原因の切り分け（デーモンの置き場所、スキャン対象のネットワーク、権限）から始める。代替として nmap、NetAlertX、NetBox も候補になる（[サービスカタログ](../../homelab-service-catalog.md)）

## 方針のない候補

理由や設計を詰めていない候補。既存の構成で役割が足りているため、優先度は低い。必要になったら、上の項目のように理由と条件を書いてから着手する。

- nginx、Nginx Proxy Manager（リバースプロキシは Caddy で足りている。理由と再検討の条件は [ADR 0019](../../adr/0019-caddy-reverse-proxy.md)）。Traefik は学習用に試す項目として[未着手の項目](01-backlog.md)に移した
- telegraf + InfluxDB（メトリクスは Prometheus で足りている）
- Portainer（Docker の状態の可視化）
- VM テンプレートの Packer 化（テンプレートは Terraform + cloud-init で再現できる）

## Debian（VM の OS）

見送り中（2026-11-01 時点では Ubuntu のまま）。

- 現状: 全 VM は Ubuntu Server 24.04 LTS。PVE ホストは Debian 13 ベース（[ADR 0021](../../adr/0021-ubuntu-lts-for-vms.md)）
- 見送る理由: Docker を載せるだけの VM では Ubuntu との差が小さい。テンプレートと Ansible の `common` ロールを作り直す手間に見合わない
- 再検討する条件:
  - snap が実害になった
  - VM のメモリが逼迫し、OS の素のフットプリントが効いてきた
  - PVE ホストと系統を揃えて、運用を単純にしたくなった
