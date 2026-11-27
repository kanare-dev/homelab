# 0037. 室内の温度・湿度は Home Assistant の Prometheus 連携で集め、既存の Alertmanager から通知する

- ステータス: 採用（実機への適用は未確認）
- 日付: 2026-11-27

## 背景

Grafana には、ESP32 の温湿度のダッシュボード（`esp32-environment.json`）が残っていた。ダッシュボードは別のリポジトリ（`iot-env-monitor`）の JSON を Ansible がダウンロードして置いていたが、ESP32 は止めていて、2026-10-22 に scrape の対象からも外していた（[INC-2026-10-22](../operations/incidents/2026-10-22-lvm-thin-exhaustion.md)）。そのため、ダッシュボードには何も表示されていなかった。

一方、Home Assistant は SwitchBot Cloud 経由で SwitchBot Hub 2 の温度と湿度（`sensor.switchbot_hub_2_temperature` / `sensor.switchbot_hub_2_humidity`）を取得している。この値は Homepage のウィジェットで現在値を見るだけで、履歴もアラートも無かった（[バックログ](../operations/roadmap/01-backlog.md)に「検討中」として残していた）。

運用者は、ESP32 のダッシュボードを消し、Home Assistant の温度・湿度を Grafana で見られるようにし、湿度のアラートを Slack に送ることにした（2026-11-27）。

## 決定

1. Home Assistant の組み込みの Prometheus 連携（`configuration.yaml` の `prometheus:`）を有効にし、`/api/prometheus` で温度と湿度の 2 つのエンティティだけを出す。
2. `vm-monitoring` の Prometheus が、`10.77.20.20:8123` を直接（Caddy を通さずに）60 秒ごとに scrape する。認証には、Home Assistant の長期アクセストークン（`prometheus`）を使い、SOPS（`prometheus_ha_token`）で管理する。`vm-apps` の UFW で、8123 を `vm-monitoring` にも許可する。
3. 湿度が 35% 未満、または 70% 超の状態が 1 時間続いたら、warning として通知する。解消の判定は 30 分待つ（`keep_firing_for`）。温度は通知せず、ダッシュボードで見るだけにする。
4. 湿度の通知は、homelab のチャンネルとは別の、室内環境用の Slack チャンネルに送る（ラベル `channel: environment` で振り分ける。Webhook URL は SOPS の `slack_webhook_url_environment`）。
5. センサーの値が取れないとき（HA でエンティティが利用できない、または Prometheus に値が無い）も、30 分続いたら warning で通知する。値が途絶えた間は湿度のアラートが鳴らないので、その状態に気づけるようにする。こちらは homelab の側で直すものなので、warning 用のチャンネルに送る。
6. ESP32 のダッシュボードを Grafana から消し、Git 管理の「Room Environment」（`docker/compose/monitoring/grafana/dashboards/room-environment.json`）に置き換える。

## 理由

- Prometheus、Alertmanager、Slack への経路は、すでに運用している。ルールを足すだけで、通知の重要度の分け方や再通知の間隔（[監視・アラート](../architecture/lld/platform/monitoring.md#通知の挙動)）をそのまま使える。
- Home Assistant の連携は組み込みなので、コンテナや exporter を増やさずに済む。センサーを足しても（将来の CO2 など）、エンティティを `include_entities` に足すだけで載る。
- scrape を Caddy 経由ではなく直接にすると、`vm-infra`（DNS と Caddy）が止まっても値を取り続けられる。監視の対象を IP で書く方針（[ADR-0036](0036-a-record-for-every-fixed-ip-host.md)）とも揃う。
- 出すエンティティを絞ると、関係のないエンティティ（Spotify など）の値が Prometheus に入らず、系列も増えない。
- しきい値の 35% と 70% は、冬の乾燥と、夏の結露・カビの目安である。換気や入浴による一時的な変化で鳴らないよう、継続時間を 1 時間にした。しきい値の前後を値が行き来すると、発報と解消が何度も届くので、解消も 30 分待つ。
- 湿度の通知は、加湿・除湿をするための生活の通知で、homelab の障害ではない。homelab の warning に混ぜると、冬は毎日届いてインフラの通知が埋もれるので、チャンネルを分けた（運用者の希望、2026-11-27）。センサーの欠測は、HA、トークン、UFW など homelab の側の原因で起きるので、homelab の warning に残す。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| Home Assistant のオートメーションで Slack に直接送る | 通知の経路が Alertmanager と二重になる。重要度による送り先の分け方、再通知、解消の通知を HA 側で作り直す必要がある |
| Grafana のアラート機能で通知する | アラートのルールが Prometheus（`alerts.yml`）と Grafana の 2 か所に分かれる。Grafana のアラートは、画面で作ると Git に残りにくい |
| SwitchBot の API を直接 scrape する exporter を置く | コンテナと SwitchBot のトークンの管理が増える。HA がすでに同じ値を取っているので、二重にポーリングすることになり、API の上限（1 日 10,000 回）も分け合う |
| ESP32 + MQTT の経路を復活させる | ESP32 は止めている。SwitchBot Hub 2 で温度と湿度を取れているので、機器を増やす理由が無い（MQTT + ESP32 の連携はバックログに残す） |
| 湿度の通知も homelab の warning 用チャンネルに送る | 冬の乾燥のように数日続く通知が、インフラの warning を埋もれさせる。読む人の行動（加湿・換気）も、インフラの対応とは違う |
| Caddy 経由（`https://ha.lab.kanare.dev/api/prometheus`）で scrape する | UFW の変更は不要になるが、`vm-infra` が止まると値が途絶え、DNS の障害がセンサーの欠測にも見えてしまう |

## 結果

- `docker/compose/homeassistant/config/configuration.yaml` に `prometheus:` を足す。`make deploy-apps APP=homeassistant` で反映すると、HA が再起動する。
- Home Assistant で長期アクセストークン（`prometheus`）を作り、`ansible/inventory/group_vars/monitoring/secrets.sops.yml` に `prometheus_ha_token` として足す。トークンは、HA のユーザーを作り直すと失われるので、再発行の手順を [Home Assistant](../architecture/lld/apps/home-assistant.md#復旧) に書く。
- Slack に室内環境用のチャンネルを作って Incoming Webhook を発行し、`slack_webhook_url_environment` として SOPS に足す。
- `make setup-monitoring` で、Prometheus のジョブ、ルール、ダッシュボード、トークンを反映し、ESP32 のダッシュボードを消す。
- `TargetDown` から `job="homeassistant"` を除く。HA の scrape の失敗は VM の停止ではなく、critical にすると、同じ `host`（`vm-apps`）の外形監視まで抑制してしまうためである。
- SwitchBot Cloud のポーリングに頼るので、値は数分おきにしか変わらない。湿度の監視には十分だが、秒単位の変化は見られない。
- 実機に適用し、値が Prometheus に入ることを確かめたら、このステータスを「採用（適用した日付）」にする。

詳細: [監視・アラート](../architecture/lld/platform/monitoring.md#室内の温度湿度)、[Home Assistant](../architecture/lld/apps/home-assistant.md#監視)
