# 0014. FreshRSS を vm-apps に置き、購読リストだけ Git の外に退避する

- ステータス: 採用
- 日付: 2026-11-01

## 背景

RSS で情報を集める手段を、他社のサービスに依存せず自宅で持ちたい。`vm-apps` には Homepage、Home Assistant、n8n が載っており、同じ作り方でもう 1 つ足せるかを検討した。

## 決定

- FreshRSS を `vm-apps` に Docker Compose で置く。バージョンを固定し、Ansible（`apps.yml`）で配置する。
- データベースは SQLite（FreshRSS の既定）にする。
- `https://rss.lab.kanare.dev` を Caddy 経由で公開し、`vm-apps` の 8081 は `docker_published_allow` で `vm-infra` だけに許可する。外形監視と Homepage に加える。
- 認証は FreshRSS 自身のログインのみ。ユーザーの作成はブラウザの初回画面で行い、パスワードは SOPS に入れず Keychain に入れる。
- バックアップは、**購読リスト（OPML）だけを iCloud Drive に退避する**（`make freshrss-opml-pull`）。Git には入れない。VM 全体のバックアップは取らない（[ADR-0001](0001-no-vm-backup.md) のまま）。

## 理由

- `vm-apps` は割当 4GB に対して実使用が約 1.7GB で、FreshRSS（待機時で約 20MB。フィード更新中も 100MB 前後の見込み）が収まる。専用 VM を増やすと、ホストのメモリの余白が減る。
- 既存の構成（Docker Compose、Ansible、Caddy、blackbox、Homepage）にそのまま乗る。運用の型が増えない。
- 守りたいのは購読リストで、OPML として書き出せる。記事は元のサイトから再取得できる。
- OPML を Git に入れないのは、リポジトリが公開で、購読しているサイトが個人の関心を表すため。購読 URL に認証用のトークンが入る限定フィードもある。
- 初期ユーザーを環境変数で作る方式にすると、パスワードを SOPS に置くことになる。画面で作れば、秘密がリポジトリに現れない。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| Miniflux | PostgreSQL が必須で、コンテナが 1 つ増える。個人利用で SQLite で足りる（[ADR-0012](0012-n8n-on-vm-apps.md) と同じ判断） |
| Tiny Tiny RSS | 保守状況に不安がある |
| Feedly などのホスト型 | 自宅で持つ目的に合わない |
| OPML を Git に入れる | 公開リポジトリに購読リストと、トークン入りの URL が出る |
| 専用 VM に置く | VM が 1 台増え、メモリの余白を食う。FreshRSS は軽い |

## 影響と再検討の条件

- **失うもの**: VM を失うと、ユーザー、既読、スター、記事、設定が消える。購読リストは、最後に `make freshrss-opml-pull` した時点まで戻せる。既読とスターは戻らない。手順は [FreshRSS](../services/apps/freshrss.md#復旧)。
- **設定の運用**: フィードを足したら、`make freshrss-opml-pull` で退避しないと守られない。
- **認証**: FreshRSS 自身のログインのみ。Authelia は使わない（[ADR-0008](0008-no-authelia.md)）。外出先は Tailscale 経由（[ADR-0005](0005-tailscale-only-remote-access.md)）。
- **同居のリスク**: Homepage、Home Assistant、n8n と同じ VM を共有する。
- **再検討の条件**: 次のいずれかになったら見直す。
  - スターや既読の履歴を失いたくなくなった（データ全体を守る方法を探す）。
  - 別ストレージ（USB ディスク、NAS）を導入した。
  - フィード数や記事数が増え、SQLite では遅くなった。
  - `vm-apps` のメモリが逼迫した。

関連: [FreshRSS](../services/apps/freshrss.md)、[ADR-0001](0001-no-vm-backup.md)、[ADR-0012](0012-n8n-on-vm-apps.md)
