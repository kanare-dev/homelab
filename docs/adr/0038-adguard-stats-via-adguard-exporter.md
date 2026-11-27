# 0038. AdGuard Home の統計は adguard-exporter で集め、Caddy 経由の HTTPS で読む

- ステータス: 採用（未適用）
- 日付: 2026-11-27

## 背景

AdGuard Home の監視は、名前解決が成功するかどうか（blackbox の `dns-lab`・`dns-external`）だけだった。クエリ数、ブロックの件数と率、上流の応答時間、クライアントごとの件数は、AdGuard の画面でしか見られなかった。AdGuard の画面は直近の集計しか出さないので、期間を指定して振り返ることもできなかった。また、名前解決が止まってはいないが遅い状態（上流の応答時間が延びている状態）は、今の監視では見えない。

運用者は、AdGuard Home のダッシュボードを Grafana で見られるようにしたいと考え（2026-11-20、[バックログ](../operations/roadmap/01-backlog.md)に「検討中」として残していた）、2026-11-27 に採用を決めた。

## 決定

1. コミュニティ製の exporter、`henrywhitaker3/adguard-exporter` を、`vm-monitoring` の監視の compose に、コンテナとして足す。Prometheus が 30 秒ごとに scrape する。
2. イメージは、コードを読んで確かめた版（v1.2.3）に、ダイジェストで固定する。更新するときは、差分を読んでから上げる。
3. exporter は、AdGuard の API を、Caddy 経由の HTTPS（`https://adguard.lab.kanare.dev`）で読む。平文の `:3000` は使わない。
4. AdGuard に exporter 専用のユーザー（`exporter`）を作る。パスワードは SOPS（`group_vars/all` の `adguard_exporter_password`）で管理し、Ansible が AdGuard の設定ファイルに bcrypt のハッシュを書く。
5. exporter のポート（`:9618`）は、ホストに公開しない。Prometheus と同じ Docker ネットワークの中だけで使う。
6. Grafana のダッシュボードは、exporter に付属のもの（Grafana.com の 20799 と同じ系統）を、データソースの指定だけ直して、リポジトリに置く。
7. 統計の値（クエリ数、ブロック率、応答時間）には、まだ通知を付けない。統計が取れないことだけを warning で通知する。

## 理由

- **exporter の選択**: 調べた候補のうち、継続して保守され（2024 年 3 月から。v1.2.3 は 2026-11-07）、コントリビューターが 10 人いて、ダッシュボードも揃っているのは、これだけだった。スターは 168 と多くないが、コードは Go のファイル 12 個（約 49KB）と小さく、読んで確かめられる。
- **コードを読んで確かめたこと（2026-11-27、v1.2.3、コミット `f81a6d1`）**: 通信先は、設定した AdGuard の URL だけで、呼ぶ API は 5 つ（`/control/stats`、`/control/status`、`/control/dhcp/status`、`/control/querylog`、`/control/clients/search`）である。最後の POST もクライアント名の検索で、設定は変えない。認証情報は Basic 認証のヘッダーとして AdGuard に送るだけで、ログには出さない。外部コマンドの実行も無い。イメージは `scratch` に実行ファイルと CA 証明書だけを入れたもので、root ではないユーザー（65532）で動く。ビルドは GitHub Actions（コミットの SHA で固定）と goreleaser で行われている。
- **ダイジェストで固定する理由**: AdGuard には読み取り専用の権限が無く、exporter に管理者の権限を渡すことになる。読んだ版と動く版を一致させ、知らないうちに中身が変わらないようにする。
- **HTTPS で読む理由**: 平文の `:3000` を読むと、Basic 認証の情報が暗号化されずに Servers の VLAN を流れる。Caddy を通すと、exporter は Caddy が止まったときに統計を取れなくなるが、そのときは外形監視（`ServiceProbeFailed`）が先に気づくので、困らない。
- **専用のユーザーにする理由**: 運用者のユーザーと分けておくと、漏れたときに、このユーザーだけを差し替えられる。Homepage のウィジェットが使う運用者のユーザーにも、影響しない。
- **ポートを公開しない理由**: `/metrics` には、どの端末がどのドメインを引いたかが出る。exporter のこのエンドポイントには認証が無い。
- **外への通信を止めない理由**: コードに AdGuard 以外への通信が無いことを確かめ、イメージをダイジェストで固定した。`DOCKER-USER` に、コンテナごとの外向きの規則を足すと設定が複雑になるわりに、得るものが小さい。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| `JonanekDev/AdGuardHome-Exporter` とダッシュボード 24520 | 動いてはいるが、リリースが無く、利用者も少ない（スター 14、2026-11-27） |
| GeoIP のパネルがあるダッシュボード 24856 と、その exporter | 地域の表示は、家庭内の DNS では要らない |
| 古い `ebrianne/adguard-exporter` と、ダッシュボード 13330・14038 | 元のプロジェクトが無くなっている |
| exporter を `vm-infra` に置き、AdGuard をローカルで読む | 認証情報が平文で流れない利点はあるが、`vm-infra` の分割（DNS を LXC に移す）でまた移すことになる。監視の部品は `vm-monitoring` にまとめる |
| 平文の `http://10.77.20.10:3000` を読む | Caddy への依存は無くなるが、管理者の認証情報が暗号化されずに流れる |
| 運用者の管理者ユーザーを使い回す | 漏れたときに、運用者のパスワードと Homepage の設定まで変えることになる |
| 入れない（AdGuard の画面で見る） | 期間を指定して振り返れず、上流の応答時間の推移も見られない |

## 結果

- 運用者が `sops ansible/inventory/group_vars/all/secrets.sops.yml` で `adguard_exporter_password` を足す。
- `make setup-infra` で AdGuard に `exporter` ユーザーを作る。AdGuard の設定ファイルを書き換えるので、DNS のスタックが再起動し、名前解決が数秒止まる。
- `make setup-monitoring` で、exporter、Prometheus のジョブ、ルール、ダッシュボードを反映する。
- `TargetDown` から `job="adguard"` を除く。exporter の停止は VM の停止ではなく、critical にすると、同じ `host`（`vm-monitoring`）の外形監視まで抑制してしまうためである。代わりに `AdGuardExporterFailing`（warning）で知らせる。
- Prometheus の系列が、クライアント・上流・応答の状態の組み合わせの数だけ増える。TSDB の上限（5GB）に収まるかを、入れたあとに測る。
- exporter を更新するときは、新しい版のコードの差分を読み、ダイジェストを書き換える。
- AdGuard を DNS の LXC に移すとき（`vm-infra` の分割）も、exporter は名前（`adguard.lab.kanare.dev`）で読むので、設定を直さずに済む。

再検討の条件: exporter の保守が止まったとき、AdGuard に読み取り専用の権限ができたとき、統計の値に通知を付けたくなったとき。

詳細: [監視・アラート](../architecture/lld/platform/monitoring.md#adguard-home-の統計)、[DNS 構成](../architecture/lld/network/dns.md)
