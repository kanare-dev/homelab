# FreshRSS

RSS / Atom のフィードを集めて読む、セルフホストのリーダー。`vm-apps` に Docker Compose で置く。判断の記録: [ADR-0014](../adr/0014-freshrss-on-vm-apps.md)。

## 構成

| 項目 | 内容 |
| --- | --- |
| 置き場所 | `vm-apps`（`192.168.11.20`）の `/opt/freshrss` |
| イメージ | `freshrss/freshrss:1.30.4`（バージョンを固定する） |
| データベース | SQLite（`/opt/freshrss/data/users/<ユーザー>/db.sqlite`） |
| ネットワーク | bridge。コンテナの 80 を `8081` で公開し、`vm-infra`（Caddy）だけに許可する |
| URL | `https://rss.lab.kanare.dev`（Caddy 経由。証明書は Caddy が取得） |
| 実使用 | メモリ約 20MB（待機時、導入直後 2026-11-01） |
| 定義 | `docker/compose/freshrss/`、`ansible/playbooks/apps.yml` |

## アクセス経路とファイアウォール

```text
Mac / スマホ ─ HTTPS ─> Caddy（vm-infra :443） ─ HTTP ─> vm-apps :8081（FreshRSS :80）
```

- `vm-apps` の 8081 は Docker の公開ポートなので、UFW では絞れない。`ufw_docker` ロールの `DOCKER-USER` が、`vm-infra` 以外からの新規接続を破棄する（`group_vars/apps/vars.yml` の `docker_published_allow`）。IP とポートの直打ち（`http://192.168.11.20:8081`）は届かない。
- Caddy の裏で動かすため、`BASE_URL=https://rss.lab.kanare.dev` と `TRUSTED_PROXY=192.168.11.11`（Caddy の IP）を設定している。
- コンテナは `dns:` で AdGuard（`192.168.11.11`）を指定し、2 つ目にルーター（`192.168.11.1`）を置く（[ADR-0007](../adr/0007-vm-host-dns-is-router.md)）。フィードの取得は外部のサイトへ出るので、ルーターだけでも引ける。
- 外部には公開しない。外出先からは Tailscale 経由で使う（[ADR-0005](../adr/0005-tailscale-only-remote-access.md)）。
- 認証は FreshRSS のログインのみ。Authelia は使わない（[ADR-0008](../adr/0008-no-authelia.md)）。

## 設定とデータ

| 項目 | 管理 |
| --- | --- |
| `docker-compose.yml`（環境変数、バージョン） | Git。Ansible が配置し、変更するとコンテナが再起動される |
| ユーザー、パスワード、フィード、既読、記事 | `/opt/freshrss/data`。Git に入らない |
| 拡張機能 | `/opt/freshrss/extensions`。入れていない |
| 購読リスト（OPML） | `make freshrss-opml-pull` で iCloud Drive に退避する。Git には入れない |

- シークレットは SOPS に置かない。ログインのパスワードは Keychain に入れる。
- フィードの更新は、イメージ内の cron（`CRON_MIN=7,37`、毎時 7 分と 37 分）が行う。

## 初回のセットアップ

デプロイ後、`https://rss.lab.kanare.dev` を開くとインストール画面が出る。

1. 言語とデータベース（SQLite）を選ぶ。
2. 管理者のユーザー名とパスワードを決める。パスワードは Keychain に入れる。
3. 設定の「認証」で、ログイン方式が「フォーム」になっていることを確認する。
4. 設定の「アーカイブ」は既定値のまま使う（1 フィードあたり 200 件、最長 3 か月）。SQLite の肥大化は、この上限で抑える。thin pool は過剰割当なので、フィードが増えたら `/opt/freshrss/data` のサイズを見る。
5. 外部のアプリ（Reeder、NetNewsWire など）から使う場合は、設定の「プロフィール」で API パスワードを別に決め、「API を有効にする」（設定の「認証」）をオンにする。API の URL は `https://rss.lab.kanare.dev/api/greader.php`。

## 購読リストの退避

フィードを足す、または整理したら実行する。

```bash
make freshrss-opml-pull FRESHRSS_USER=<ユーザー名>
```

- `vm-apps` で `export-opml-for-user.php` を実行し、`~/Library/Mobile Documents/com~apple~CloudDocs/homelab/freshrss-subscriptions.opml` に書き出す。
- Git には入れない。公開リポジトリに、購読先とトークン入りの URL を出さないため。

## 監視

- `blackbox_http` で `https://rss.lab.kanare.dev` を外形監視する（`service="freshrss"`、`host="vm-apps"`）。失敗は `ServiceProbeFailed` で通知される（[監視・アラート](03-monitoring.md)）。
- Homepage の「Home」に FreshRSS のタイルがある。
- コンテナのログは 10MB × 3 ファイル（`docker-compose.yml` の `x-logging`）。

## 更新

1. [リリースノート](https://github.com/FreshRSS/FreshRSS/releases)の破壊的変更を確認する。
2. 先に `make freshrss-opml-pull` で購読リストを退避しておく。
3. `docker/compose/freshrss/docker-compose.yml` のイメージのタグを変える。
4. `make deploy-apps APP=freshrss` を実行する（compose の変更で再起動される）。
5. `https://rss.lab.kanare.dev` が開き、`probe_success` が 1 に戻ることを確認する。

## 復旧

VM を作り直したとき、または `/opt/freshrss` を失ったとき。

1. `make setup-apps` を実行する。ディレクトリと compose が置かれ、コンテナが起動する。
2. `https://rss.lab.kanare.dev` を開き、「初回のセットアップ」をやり直す。
3. 退避した OPML（iCloud Drive の `freshrss-subscriptions.opml`）を、画面の「購読管理」→「インポート」から取り込む。

失うもの: 既読、スター、記事、ユーザー、設定。守れるもの: 購読リスト（最後に `make freshrss-opml-pull` した時点まで）。

## 既知の制約

- 既読、スター、記事はバックアップしていない（[ADR-0014](../adr/0014-freshrss-on-vm-apps.md)）。
- `vm-apps` の他のコンテナ（Homepage、Home Assistant、n8n）と同じ VM を共有する。FreshRSS の異常がメモリを使い切ると、他にも影響する。
