# 0039. Omada の機器・クライアントの状態は omada-exporter（RCooLeR 版）で集め、Caddy 経由の HTTPS で読む

- ステータス: 採用（未適用）
- 日付: 2026-11-27

## 背景

Omada の監視は、`vm-omada` の OS（node_exporter）と、コントローラーの画面の外形監視（blackbox）と、ルーター・回線の ping だけだった。Omada が管理する機器（ER605・SG2210P）の状態、スイッチのポートごとのトラフィック、クライアントの数は、Omada の画面でしか見られず、期間を指定して振り返ることもできなかった。

運用者は、Omada のメトリクスを Grafana で見られるようにしたいと考え（2026-11-09、[バックログ](../operations/roadmap/01-backlog.md)に「検討中」として残していた）、2026-11-27 に、動作確認のうえで採用を決めた。見たいものは、機器のオンライン・オフライン、ポートごとのトラフィック、クライアントの数である。

コントローラーは、2026-11-09 にメモリが尽きて固まったことがあり（[INC-2026-11-09](../operations/incidents/2026-11-09-omada-memory-exhaustion.md)）、今もコンテナの上限（2.5GiB）の約 75% を使っている。exporter がコントローラーの API を呼ぶ負荷が、採用の条件の 1 つだった。

## 決定

1. コミュニティ製の exporter、`RCooLeR/omada_exporter`（OmadaBridge）を、`vm-monitoring` の監視の compose に、コンテナとして足す。Prometheus が 60 秒ごとに scrape する。
2. イメージは、コードを読んで確かめた版（v2.4.5）に、ダイジェストで固定する。更新するときは、差分を読んでから上げる。
3. exporter は、Omada の API を、Caddy 経由の HTTPS（`https://omada.lab.kanare.dev`）で読み、証明書を検証する。
4. Omada に、閲覧専用のユーザー `exporter`（Viewer）と、Open API のアプリ `exporter`（Client Credentials モード、Viewer）を作る。パスワードと Client ID・シークレットは SOPS（`group_vars/monitoring`）で管理し、Ansible が `vm-monitoring` に root だけが読める env ファイルとして置く。
5. exporter のポート（`:9202`）は、ホストに公開しない。Prometheus と同じ Docker ネットワークの中だけで使う。
6. 機器を操作する機能（MQTT 経由の再起動、PoE の入れ直し）は使わない。MQTT も `OMADA_ALLOW_DEVICE_CONTROL` も無効にする。
7. 端末ごとのメトリクス（`OMADA_TRACK_CLIENT_METRICS`）は、有効のまま残す。系列の数やラベルに載る端末の情報を見て、あとで見直すことがある。
8. Grafana のダッシュボードは、exporter に付属の「Omada Overview」と「Omada Device Details」を、そのままリポジトリに置く。
9. 機器の状態や使用量には、まだ通知を付けない。状態が取れないことだけを warning で通知する。

## 理由

- **exporter の選択**: よく紹介される `charlie-haley/omada_exporter` は、最後のリリースが v0.13.1（2024-08-05）で、更新が止まっている。その流れをくむ `RCooLeR/omada_exporter` は、v2.4.5（2026-11-09）まで続けてリリースされており、コントローラー v6 系の API に合わせて直されている。ほかの候補（`StanislawHorna/omada-exporter-go` など）は、利用者が少なかった。
- **動作確認（2026-11-27）**: `vm-monitoring` で一時的なコンテナとして起動し、60 秒ごとに 7 回読んだ。コントローラー 6.3.0.111 で、Web API と Open API の両方の認証が通り、7 つの collector がすべて成功した。系列は 183 で、Omada のコンテナのメモリ（1.891 → 1.892GiB）と CPU（0.7〜1.5%）に目に見える変化は無く、1 回の読み取りは 0.5 秒未満だった。結果は[監視・アラート](../architecture/lld/platform/monitoring.md)の「動作確認の記録」にある。
- **コードを読んで確かめたこと（2026-11-27、v2.4.5、コミット `332f440`）**: HTTP の通信先は、設定した Omada コントローラー（`OMADA_HOST`）だけである。コード中のほかの URL は、Home Assistant に送る機器情報に入るプロジェクトの URL で、通信先ではない。機器を操作する処理は、MQTT と `OMADA_ALLOW_DEVICE_CONTROL` の両方が有効なときだけ動く。イメージは Alpine に実行ファイルと CA 証明書を入れたもので、root ではないユーザー（10001）で動く。ビルドは GitHub Actions と goreleaser で行われている。
- **ダイジェストで固定する理由**: exporter には、Omada の認証情報を渡す。読んだ版と動く版を一致させ、知らないうちに中身が変わらないようにする。
- **Viewer にする理由**: AdGuard と違い、Omada には閲覧専用のロールがある。exporter が読むだけで済むことを確かめたので、漏れても設定は変えられない権限にした。
- **Open API も使う理由**: クライアント、WAN、ISP の値は、Open API からしか取れない。クライアントの数は、見たいものの 1 つである。
- **HTTPS で読む理由**: `vm-omada` の UFW は、管理画面の `:8043` を Caddy にだけ開いている。Caddy を通せば、UFW を変えずに済み、認証情報も暗号化して送れる。Caddy が止まると状態が取れなくなるが、そのときは外形監視（`ServiceProbeFailed`）が先に気づく。
- **env ファイルで渡す理由**: exporter は、認証情報を環境変数でしか受け取れない（`_FILE` 形式に対応していない）。compose のファイルに値を書かず、Ansible が SOPS から 0600 のファイルに書いて `env_file` で読ませる。
- **60 秒にする理由**: exporter は、scrape のたびにコントローラーの API を呼ぶ。機器・ポートの状態を見るには 60 秒で足り、コントローラーの負荷を小さくできる。
- **ポートを公開しない理由**: `/metrics` には、端末の MAC アドレス、ホスト名、IP が出る。exporter のこのエンドポイントには認証が無い。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| `charlie-haley/omada_exporter` | 2024 年 8 月から更新が止まっている。コントローラー 6.3 に対応しているかが分からない |
| Open API を呼ぶ exporter を自分で書く | 取りたい値は、既存の exporter で全部取れた。書いて保守する手間に見合わない |
| SNMP（`snmp_exporter`）で ER605・SG2210P から直接取る | コントローラーに負荷をかけない利点はあるが、クライアントの数はコントローラーからしか取れない。機器ごとに SNMP の設定も要る。コントローラーへの負荷が問題になったら、機器とポートの分だけ SNMP に移すことを考える |
| `vm-monitoring` から `vm-omada:8043` を直接読む | `vm-omada` の UFW を開ける必要がある。証明書の検証もできない（自己署名） |
| 端末ごとのメトリクスを止める | 運用者が残すことを選んだ（2026-11-27）。あとで見直すことはあり得る |
| 入れない（Omada の画面で見る） | 期間を指定して振り返れず、回線・VM の監視と同じ画面で見られない |

## 結果

- 運用者が、Omada にユーザー `exporter` と Open API のアプリ `exporter` を作り、`sops ansible/inventory/group_vars/monitoring/secrets.sops.yml` で `omada_exporter_password`、`omada_exporter_client_id`、`omada_exporter_client_secret` を足した（2026-11-27）。
- `make setup-monitoring` で、exporter、Prometheus のジョブ、ルール、ダッシュボードを反映する。
- `TargetDown` から `job="omada"` を除く。exporter の停止は VM の停止ではなく、critical にすると、同じ `host`（`vm-monitoring`）の外形監視まで抑制してしまうためである。代わりに `OmadaExporterFailing`（warning）で知らせる。DNS の障害と、Omada の画面の外形監視の失敗の間は、これを抑制する。
- Prometheus の系列が、機器・ポート・端末の数だけ増える。端末が増えたり入れ替わったりすると増えるので、入れたあとに、数日おいてもう一度測る。
- 反映したあと、数日は、Omada のコンテナのメモリ（`vm-omada` の node_exporter と `docker stats`）を見る。
- exporter を更新するときは、新しい版のコードの差分を読み、ダイジェストを書き換える。

再検討の条件: exporter の保守が止まったとき、コントローラーのメモリが exporter のせいで足りなくなったとき、端末ごとの系列が増えすぎたとき、機器の状態に通知を付けたくなったとき、Omada の AP を入れたとき（無線のパネルとメトリクスが増える）。

詳細: [監視・アラート](../architecture/lld/platform/monitoring.md#omada-の機器クライアントの状態)、[Omada コントローラー](../architecture/lld/network/omada-controller.md)
