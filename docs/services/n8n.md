# n8n

サービスどうしをつなぐワークフローを、画面で組んで自動実行する。`vm-apps` に Docker Compose で置く。判断の記録: [ADR-0012](../adr/0012-n8n-on-vm-apps.md)。

## 構成

| 項目 | 内容 |
| --- | --- |
| 置き場所 | `vm-apps`（`192.168.11.20`）の `/opt/n8n` |
| イメージ | `docker.n8n.io/n8nio/n8n:2.44.7`（バージョンを固定する） |
| データベース | SQLite（`/opt/n8n/data/database.sqlite`） |
| ネットワーク | bridge。5678 を公開し、`vm-infra`（Caddy）だけに許可する |
| URL | `https://n8n.lab.kanare.dev`（Caddy 経由。証明書は Caddy が取得） |
| 実使用 | メモリ約 360MB（2026-10-30、導入直後） |
| 定義 | `docker/compose/n8n/`、`ansible/playbooks/apps.yml` |

## アクセス経路とファイアウォール

```text
Mac / スマホ ─ HTTPS ─> Caddy（vm-infra :443） ─ HTTP ─> vm-apps :5678（n8n）
```

- `vm-apps` の 5678 は Docker の公開ポートなので、UFW では絞れない。`ufw_docker` ロールの `DOCKER-USER` が、`vm-infra` 以外からの新規接続を破棄する（`group_vars/apps/vars.yml` の `docker_published_allow`）。IP とポートの直打ち（`http://192.168.11.20:5678`）は届かない。
- Caddy の裏で動かすため、`N8N_HOST`、`N8N_PROTOCOL=https`、`WEBHOOK_URL`、`N8N_PROXY_HOPS=1` を設定している。Webhook の URL は `https://n8n.lab.kanare.dev/webhook/...` の形になる。
- n8n のコンテナは `dns:` で AdGuard（`192.168.11.11`）を指定している。ホストの DNS（ルーター）は `*.lab.kanare.dev` を引けないので、指定しないとワークフローから `https://ha.lab.kanare.dev` などを呼べない（HTTP Request ノードの「The connection cannot be established」）。
- 2 つ目の DNS にルーター（`192.168.11.1`）を指定している。AdGuard が応答しないときだけ使われ、Slack など外部サービスへの通知は止まらない（[ADR-0007](../adr/0007-vm-host-dns-is-router.md)）。ルーターは `*.lab.kanare.dev` を引けないので、その間は内部サービス（`ha.lab.kanare.dev` など）を呼べない。
- 外部には公開しない。外出先からは Tailscale 経由で使う（[ADR-0005](../adr/0005-tailscale-only-remote-access.md)）。外部サービスからの Webhook は受けられない。
- 認証は n8n のログインのみ。Authelia は使わない（[ADR-0008](../adr/0008-no-authelia.md)）。

## 設定とシークレット

| 項目 | 管理 |
| --- | --- |
| `docker-compose.yml`（環境変数、バージョン） | Git。Ansible が配置し、変更するとコンテナが再起動される |
| `N8N_ENCRYPTION_KEY`（認証情報の暗号鍵） | SOPS（`group_vars/apps/secrets.sops.yml` の `n8n_encryption_key`）。`/opt/n8n/.env` に生成される（権限 0600） |
| ユーザー、認証情報、実行履歴 | `/opt/n8n/data`。Git に入らない |
| ワークフロー | 画面で作る。`make n8n-workflows-pull` で Git（`docker/compose/n8n/workflows/`）に取り込む |

- 暗号鍵を失うと、保存した認証情報を復号できない。SOPS に入っているので、age 鍵があれば取り出せる（[秘密情報管理](../operations/runbooks/secrets.md)）。
- 暗号鍵は、データを作る前に設定する。後から変えると、既存の認証情報が読めなくなる。
- ワークフローに API トークンなどを直接書かない。認証情報（Credentials）の機能を使う。書き出した JSON は公開リポジトリに入る。

### ワークフローの取り込み

画面でワークフローを作る、または変えたら実行する。

```bash
make n8n-workflows-pull
git diff docker/compose/n8n/workflows   # 秘密が入っていないか確認してからコミットする
```

- `vm-apps` で `n8n export:workflow --backup` を実行し、1 ワークフロー 1 ファイルの JSON を `docker/compose/n8n/workflows/` に置き換える。削除したワークフローは、Git からも消える。
- ワークフローが 0 件のときは、n8n がエラーを返して止まる。Git の中身は変わらない。
- 認証情報（Credentials）は書き出さない。n8n が JSON に入れる所有者の情報（`shared`。氏名とメールアドレスを含む）と `meta.instanceId` は、`jq` で取り除く。公開リポジトリに入れないため。

## ワークフロー

| 名前 | 内容 | 状態 |
| --- | --- | --- |
| `test-hello` | 手動実行で HTTP を叩く確認用 | 動作確認用。不要になったら削除してよい |
| `weekly-report` | 毎週月曜 9:00 に Prometheus へ問い合わせ、稼働率・リソース・証明書の期限・アラートを 1 通にまとめて Slack に送る | 有効（Publish 済み）。`#homelab-reports` に送る |

### weekly-report

```text
スケジュール → クエリ定義（Code） → Prometheus に問い合わせ（HTTP Request × 8） → 文面を作る（Code） → Slack に送る
```

- `https://prometheus.lab.kanare.dev/api/v1/query` を、内部の名前で呼ぶ（コンテナの `dns:` が AdGuard を指すため。上の「アクセス経路」）。
- 失敗の判定は、稼働率ではなく失敗した分数（`sum_over_time((1 - probe_success)[7d:1m])`）で行う。導入して 7 日に満たないサービスで、割合が大きく振れるため。
- アラートの時間は、サンプル数 × 15 秒（Prometheus の評価間隔）で、ターゲットごとの合計（延べ）。`Watchdog` は常に発火するので除く。
- 印（⚠️）の基準はコードの中にある: 失敗 10 分以上、ディスクが先週より 5 ポイント以上増加または 80% 以上、メモリ 85% 以上、証明書の残り 21 日未満（Caddy は 30 日前に更新する）。
- Slack は Bot トークン方式で送る（Incoming Webhook の URL は秘密で JSON に入る恐れがあるため使わない）。アラート用の `#homelab-alerts` とは分け、`#homelab-reports` に送る。
  - Slack アプリ `homelab-n8n` の Bot Token Scopes は `chat:write` と `chat:write.public` だけ。パブリックチャンネルなら、Bot の招待なしで送れる。プライベートチャンネルにする場合は、`/invite @homelab-n8n` で招待する。
  - n8n の Credentials（Slack API）の Access Token に、Bot User OAuth Token（`xoxb-`）を入れる。値は n8n の中にだけあり、Git に入らない。書き出した JSON には、認証情報の ID と名前（`slack-homelab-n8n`）だけが入る。
  - 送り先は、チャンネル ID の直接指定（By ID）。ノードの「From list」は、一覧の取得に `channels:read` と `groups:read` が要るので使えない。権限を最小に保つため、そのままにしている。チャンネル ID は秘密ではない。
  - トークンを失った、または漏らしたときは、Slack アプリの OAuth & Permissions で Reinstall to Workspace して再発行し、n8n の Credentials を入れ替える。
- アラートの通知は Alertmanager の直送のままにする。n8n を経由させると、通知の経路が `vm-infra`（Caddy）と `vm-apps` の障害に左右される（[ADR-0007](../adr/0007-vm-host-dns-is-router.md)、[ADR-0010](../adr/0010-external-heartbeat.md)）。n8n は、止まっても困らない追加の用途に使う。

## 監視

- `blackbox_http` で `https://n8n.lab.kanare.dev` を外形監視する（`service="n8n"`、`host="vm-apps"`）。失敗は `ServiceProbeFailed` で通知される（[監視・アラート](monitoring.md)）。
- Homepage に「Automation」の n8n タイルがある。
- コンテナのログは 10MB × 3 ファイル（`docker-compose.yml` の `x-logging`）。実行履歴は 7 日（`EXECUTIONS_DATA_MAX_AGE=168`）で自動削除する。

## 初回のセットアップ

デプロイ後、`https://n8n.lab.kanare.dev` を開くと、オーナーアカウントの作成画面が出る。メールアドレスとパスワードを決める。パスワードは Keychain に入れる。

## 更新

1. [リリースノート](https://docs.n8n.io/release-notes/)の破壊的変更を確認する。
2. `docker/compose/n8n/docker-compose.yml` のイメージのタグを変える。
3. 先に `make n8n-workflows-pull` で取り込んでおく。
4. `make setup-apps` を実行する（compose の変更で再起動される）。
5. `https://n8n.lab.kanare.dev` が開き、`probe_success` が 1 に戻ることを確認する。

## 復旧

VM を作り直したとき、または `/opt/n8n` を失ったとき。

1. `make setup-apps` を実行する。ディレクトリ、compose、暗号鍵を含む `.env` が置かれ、コンテナが起動する。
2. `https://n8n.lab.kanare.dev` を開き、オーナーアカウントを作り直す。
3. `docker/compose/n8n/workflows/` の JSON を取り込む。

   ```bash
   scp -i ~/.ssh/id_ed25519_homelab -r docker/compose/n8n/workflows ubuntu@192.168.11.20:/tmp/n8n-workflows
   ssh -i ~/.ssh/id_ed25519_homelab ubuntu@192.168.11.20 \
     'sudo docker cp /tmp/n8n-workflows n8n:/tmp/ && sudo docker exec n8n n8n import:workflow --separate --input=/tmp/n8n-workflows && rm -rf /tmp/n8n-workflows'
   ```

4. 認証情報（Credentials）を入れ直す。トークンは各サービスで再発行できる。
5. インポートしたワークフローは無効の状態なので、確認して有効にする。

失うもの: ユーザー、認証情報、実行履歴。守れるもの: ワークフロー（最後に `make n8n-workflows-pull` した時点まで）。

## 既知の制約

- 外部サービスからの Webhook は受けられない（外部に公開しない方針）。
- 認証情報とユーザー、実行履歴はバックアップしていない（[ADR-0012](../adr/0012-n8n-on-vm-apps.md)）。
- `vm-apps` の他のコンテナ（Homepage、Home Assistant）と同じ VM を共有する。n8n の異常がメモリを使い切ると、他にも影響する。
