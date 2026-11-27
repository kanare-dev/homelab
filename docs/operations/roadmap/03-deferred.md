# 見送り中の項目

この文書には、[ロードマップ](README.md)の項目のうち、検討したうえで導入を見送っているものと、導入したあとに外した（廃止した）ものを載せる。見送った理由と、再検討する条件も残す。条件のどれかに当てはまったら、着手するかどうかを判断する。

## uptime-kuma

見送り中（2026-10-27 時点では導入しない）。

- 現状: HTTPS と DNS の外形監視は blackbox-exporter と Alertmanager で行っている。停止の検知は、外部 Heartbeat（Healthchecks.io）が担当する（[monitoring.md](../../architecture/lld/platform/monitoring.md)）。
- 見送る理由: 死活監視と通知の役割が blackbox-exporter と重なり、二重に管理することになる。Alertmanager の `inhibit_rules`（VM の停止や DNS の障害のときに、通知を抑える仕組み）が使えないので、障害のたびに通知が増える。また、vm-apps に置くと、監視される側と同じホストで動くことになり、ホストが停止しても検知できない。
- 再検討する条件:
  - 家族など Grafana を見ない人向けに、ステータスページが必要になった
  - 外形監視のターゲット追加（`prometheus.yml` の編集とデプロイ）が負担になった
  - 回線断・停電を家の外から検知したくなり、外部の VPS を用意できた（[monitoring.md](../../architecture/lld/platform/monitoring.md) の案 C）

## Loki + Grafana Alloy（ログ収集基盤）

見送り中（2026-10-26 時点では導入しない）。ただし、ネットワーク機器の syslog だけを集める案は、[別に検討している](14-syslog-collection.md)（2026-11-25。検討中）。この項目は、全ホストの journald と Docker のログを集める計画を指す。

- 現状: ログは、各ホストの journald（200M、1 か月）と、Docker のログの上限（10MB × 3）に分かれて残っている。横断して検索する手段はないので、調べるときは、VM ごとに `ssh` して `journalctl` や `docker logs` を使う。
- 見送る理由: INC-2026-10-25 の原因は、永続化してある PVE の journald で追えた。ホストの NIC が止まると、ログを転送することもできないので、集約していても役に立たなかった。ストレージにはまだ過剰な割り当てが残っており（約 1.44 倍）、増え続けるログを足すのは危険である。収集エージェントを全ホストに入れる運用の手間も増える（[INC-2026-10-25](../incidents/2026-10-25-nic-hardware-unit-hang.md)）。
- 再検討する条件:
  - 複数 VM をまたぐ原因調査に、手間を感じる場面が増えた
  - ストレージ障害でログごと消え、原因が追えなかった
  - アラートの前後のログを Grafana でメトリクスと並べて見たくなった
  - thin pool の過剰割当を解消した（容量に余裕ができた）
- 導入するときの方針（案）: `vm-monitoring` に Loki を、全ホストに Grafana Alloy を入れる（Promtail は、後継の Alloy に移行済みである）。保持期間を 14 日、容量の上限を 3GB 程度にして始める。導入するときは、ADR を追加し、`monitoring.md` の「容量の上限設定」の表も更新する。

## 回線速度の定期測定（Speedtest）

見送り中（2026-11-01 時点では導入しない）。

- 現状: 回線の断絶と遅延は、blackbox-exporter の ICMP（30 秒ごと）で見ている（[monitoring.md](../../architecture/lld/platform/monitoring.md#回線の疎通遅延の監視)、[ADR 0018](../../adr/0018-internet-speed-monitoring.md)）。
- 見送る理由: Speedtest は、測定のたびに 30〜60 秒、回線を使い切る。仕事中のビデオ会議などに影響が出るうえ、建物の共用回線にも負荷をかける。建物側の混雑は、遅延とパケットロスを見るだけでも、多くの場合に検知できる。
- 再検討する条件:
  - 「遅いのに ping の遅延・ロスに出ていない」状況が起きた
  - 建物の管理会社や ISP に、速度（Mbps）の数字を示す必要が出た
  - 従量課金や上限のない回線になり、通信量を気にしなくてよくなった
- 導入するときの方針（案）: 平日の 9〜18 時を避けて、systemd timer で 1 日に数回だけ測り、結果を `node_exporter` の textfile に書き出す（PVE の `pve-storage-metrics` と同じ方式）。Prometheus の scrape で測る方式（`speedtest-exporter`）は、時間帯を指定できないので使わない。通知は、7 日間の中央値の 60% を下回ったときに出す。

## Glances（Homepage の VM 別バー表示）

見送り中（2026-10-30 時点では導入しない）。

- 現状: Homepage の Hosts では、Prometheus の `node_exporter` から取得した CPU、メモリ、ディスクの使用率を、数値で表示している（[Homepage](../../architecture/lld/apps/homepage.md)）。バーで表示できるのは、Homepage が動いている `vm-apps` 自身だけを測る `resources` ウィジェットだけである。
- 見送る理由: 全 VM に Glances を入れる必要がある（Ansible のロールを作り、公開ポートに対する `DOCKER-USER` と UFW の許可を追加する）。また、`node_exporter` と同じ情報を、二重に集めることになる。今の数値の表示で足りている。
- 再検討する条件: 数値では状況をつかみにくく、バーで見たい場面が増えたとき。
- 導入するときの方針（案）: 全 VM に Glances を入れ、Homepage の Glances ウィジェットで表示する。`vm-apps` の `resources` ウィジェットとは併用しない。

## Scanopy（ネットワーク探索・トポロジー図）

廃止（2026-07-17 に取りやめ）。VLAN 化のあとに再挑戦する余地がある。

- 経緯: 2026-04-04 に `vm-apps` へ導入した。Scanopy 本体、PostgreSQL、スキャンを行うデーモンを Docker Compose で動かし、`vm-apps` のメモリを 2GB から 4GB に増やした。その後、2026-07-17 に、構成ごと取り除いた。
- 外した理由: うまくスキャンできず、期待した効果が得られなかった。原因が Scanopy の限界なのか、設定や使い方の問題なのかは、切り分けていない。
- 再検討する条件:
  - [VLAN 化](04-network-omada-vlan.md)が終わり、VLAN ごとにデーモンを置いてスキャンできる構成になった
  - ネットワーク機器・端末の一覧や構成図を、手作業ではなく自動で作りたくなった
- 試すときの方針（案）: 最初から全 VLAN に広げず、1 つの VLAN で、スキャンが機器を検出できるかを確かめる。まず、前回うまくいかなかった原因を切り分ける（デーモンの置き場所、スキャン対象のネットワーク、権限）。代わりに、nmap、NetAlertX、NetBox を使う案もある（[サービスカタログ](../../homelab-service-catalog.md)）。

## AdGuard Home の exporter の他の候補

見送り（2026-11-27）。AdGuard Home の統計には、`henrywhitaker3/adguard-exporter` を採用した（[ADR-0038](../../adr/0038-adguard-stats-via-adguard-exporter.md)）。

- `JonanekDev/AdGuardHome-Exporter`（ダッシュボード 24520）: 開発は続いているが、リリースが無く、利用者も少ない（スター 14、2026-11-27）。管理者の認証情報を渡すので、版を固定して読める、実績のある方を選んだ。
- `ebrianne/adguard-exporter`（ダッシュボード 13330、14038）: 元のプロジェクトが無くなっている。
- 再検討する条件:
  - 採用した exporter の保守が止まった（1 年以上リリースが無く、AdGuard の新しい版で動かなくなった）
  - 採用した exporter で取れない値（GeoIP など）が必要になった

## Omada の exporter の他の候補

見送り（2026-11-27）。Omada の機器・クライアントの状態には、`RCooLeR/omada_exporter` を採用した（[ADR-0039](../../adr/0039-omada-metrics-via-omada-exporter.md)）。

- `charlie-haley/omada_exporter`（ダッシュボード 16343、20854）: 最後のリリースが v0.13.1（2024-08-05）で、更新が止まっている。コントローラー 6.3 に対応しているかが分からない。採用した exporter は、これの流れをくむ。
- Open API を呼ぶ自前の exporter: 取りたい値は、既存の exporter で全部取れた。書いて保守する手間に見合わない。
- SNMP（`snmp_exporter`）で ER605・SG2210P から直接取る: クライアントの数はコントローラーからしか取れない。機器ごとに SNMP の設定も要る。
- 再検討する条件:
  - 採用した exporter の保守が止まった（1 年以上リリースが無く、コントローラーの新しい版で動かなくなった）
  - exporter がコントローラーのメモリを圧迫し、機器とポートの分だけでも SNMP に移したくなった

## 方針のない候補

理由や設計を詰めていない候補である。既存の構成で役割が足りているので、優先度は低い。必要になったら、上の項目のように、理由と条件を書いてから着手する。

- nginx と Nginx Proxy Manager は、リバースプロキシを Caddy で足りているので見送っている（理由と再検討の条件は [ADR 0019](../../adr/0019-caddy-reverse-proxy.md) に書いた）。Traefik は、学習用に試す項目として、[未着手の項目](01-backlog.md)に移した。
- telegraf と InfluxDB は、メトリクスを Prometheus で集められるので見送っている。
- Portainer は、Docker の状態を可視化するツールで、今のところ必要としていない。
- VM テンプレートの Packer 化は、テンプレートを Terraform と cloud-init で再現できるので見送っている。

## Debian（VM の OS）

見送り中（2026-11-01 時点では Ubuntu のまま）。

- 現状: 全 VM は、Ubuntu Server 24.04 LTS で動いている。PVE ホストは、Debian 13 ベースである（[ADR 0021](../../adr/0021-ubuntu-lts-for-vms.md)）。
- 見送る理由: Docker を載せるだけの VM では、Ubuntu との差が小さい。テンプレートと、Ansible の `common` ロールを作り直す手間に見合わない。
- 再検討する条件:
  - snap が実害になった
  - VM のメモリが逼迫し、OS の素のフットプリントが効いてきた
  - PVE ホストと系統を揃えて、運用を単純にしたくなった
