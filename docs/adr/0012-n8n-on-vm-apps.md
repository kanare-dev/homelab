# 0012. n8n を vm-apps に置き、ワークフローだけ Git で守る

- ステータス: 採用
- 日付: 2026-10-30

## 背景

Prometheus / Grafana のアラートの整形、Home Assistant の外のサービスとの連携、GitHub の通知など、サービスどうしをつなぐ自動化を、コードを書かずに組みたい。

2026-10-27 に `vm-apps` へ手動で試験導入した（コンテナ `n8n-trial`）。メモリは約 500MB で `vm-apps` に収まり、公開ポートを `vm-infra` だけに絞れることも確認できたので、使い続けることにして構成管理に載せる。

## 決定

- n8n を `vm-apps` に Docker Compose で置く。バージョンを固定し、Ansible（`apps.yml`）で配置する。
- `https://n8n.lab.kanare.dev` を Caddy 経由で公開し、`vm-apps` の 5678 は `docker_published_allow` で `vm-infra` だけに許可する。外形監視に加える。
- 認証情報の暗号鍵（`N8N_ENCRYPTION_KEY`）は SOPS で管理する。
- バックアップは、**ワークフローの JSON だけを Git で守る**（`make n8n-workflows-pull`）。認証情報（API トークンなど）は Git に入れない。VM 全体のバックアップは取らない（[ADR-0001](0001-no-vm-backup.md) のまま）。

## 理由

- `vm-apps` は割当 4GB に対して実使用が約 1.6GB で、n8n（約 360MB）が収まる。専用 VM を増やすと、ホストのメモリの余白が減る。
- 既存の構成（Docker Compose、Ansible、Caddy、blackbox）にそのまま乗る。Home Assistant と同じ作り方なので、運用の型が増えない。
- 守りたいのはワークフローの定義で、JSON として Git に置ける。実行履歴は失っても困らない（7 日で自動削除する）。
- 認証情報（API トークンなど）は、暗号化されていても公開リポジトリには置かない。再発行できるものなので、失ったら入れ直す。
- 暗号鍵は SOPS に置く。n8n が自動生成する鍵はデータ用ボリュームの中にしかなく、ボリュームを失うと鍵も失う。SOPS にあれば、age 鍵から取り出せる。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| Home Assistant のオートメーションだけで済ませる | HA の外のサービス（Slack、GitHub、HTTP API）との連携は書きにくい |
| 専用 VM に置く | VM が 1 台増え、メモリの余白を食う。n8n は軽い |
| PostgreSQL を別コンテナで置く | 個人利用で SQLite で足りる。コンテナが 1 つ増えて運用が重くなる |
| 認証情報も Git に書き出す | 暗号化されていても、公開リポジトリに置く利点が小さい |
| ワークフローも守らない | 作り直しの手間が大きい。JSON を書き出すだけで守れる |

## 影響と再検討の条件

- **失うもの**: VM を失うと、ユーザー、認証情報、実行履歴が消える。ワークフローは最後に `make n8n-workflows-pull` した時点まで戻せる。認証情報は入れ直す。手順は [n8n](../services/n8n.md#復旧)。
- **設定の運用**: 画面で作ったワークフローは、`make n8n-workflows-pull` で Git に取り込まないと守られない。
- **認証**: n8n 自身のログインのみ。Authelia は使わない（[ADR-0008](0008-no-authelia.md)）。Webhook は、LAN 内と Tailscale からだけ届く。外部サービスからの Webhook 受信は、外部に公開しない方針なので使えない。
- **同居のリスク**: Homepage、Home Assistant と同じ VM を共有する。
- **再検討の条件**: 次のいずれかになったら見直す。
  - 外部サービスからの Webhook を受けたくなった（公開の方針を決め直す）。
  - ワークフローが増え、SQLite では遅い、または実行履歴を長く残したくなった。
  - 別ストレージ（USB ディスク、NAS）を導入した（データ全体を守る）。
  - `vm-apps` のメモリが逼迫した。

関連: [n8n](../services/n8n.md)、[ADR-0001](0001-no-vm-backup.md)、[ADR-0011](0011-home-assistant-on-vm-apps.md)
