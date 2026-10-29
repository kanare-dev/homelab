# Homepage

LAN 内サービスへのリンクと、状態のウィジェットを 1 画面にまとめるダッシュボード。`vm-apps` に Docker Compose で置く。

## 構成

| 項目 | 内容 |
| --- | --- |
| 置き場所 | `vm-apps`（`192.168.11.20`）の `/opt/homepage` |
| イメージ | `ghcr.io/gethomepage/homepage:latest` |
| ネットワーク | bridge。3001 を公開し、`vm-infra`（Caddy）だけに許可する（`group_vars/apps/vars.yml` の `docker_published_allow`） |
| URL | `https://home.lab.kanare.dev`（Caddy 経由）。`HOMEPAGE_ALLOWED_HOSTS` でこのホスト名だけを許可している |
| 定義 | `docker/compose/homepage/`（`config/`、`icons/`）、`ansible/playbooks/apps.yml`、`ansible/playbooks/templates/homepage.env.j2` |

- コンテナは `dns:` で AdGuard（`192.168.11.11`）を指定している。ホストの DNS（ルーター）は `*.lab.kanare.dev` を引けず、指定しないと `siteMonitor` とウィジェットが失敗する（[ADR-0007](../adr/0007-vm-host-dns-is-router.md)）。
- 外部には公開しない。認証はない（LAN 内と Tailscale 経由のみ。[ADR-0005](../adr/0005-tailscale-only-remote-access.md)、[ADR-0008](../adr/0008-no-authelia.md)）。
- 設定ファイルを変えたら `make setup-apps` で反映する。Ansible がファイルを配置して、コンテナを再起動する。

## 画面の構成

| 設定ファイル | 内容 |
| --- | --- |
| `config/services.yaml` | サービスのタイル（Infrastructure / Hosts / Network / Monitoring / Development / Home / Automation）。各タイルは `siteMonitor` で死活を表示する |
| `config/widgets.yaml` | 画面上部の情報バー。左から、名前（`kanare-lab`）、天気、日時 |
| `config/bookmarks.yaml` | リンク集 |
| `config/settings.yaml` | タイトル、テーマ、言語、グループの並べ方（Hosts は横に 5 列） |

## ウィジェット

| タイル / 情報 | 取得元 | 認証 |
| --- | --- | --- |
| Proxmox VE | `https://192.168.11.10:8006`（API トークン `homepage@pve!homepage-token`） | SOPS（`homepage_proxmox_token`） |
| AdGuard Home | `http://192.168.11.11:3000` | SOPS（`homepage_adguard_password`） |
| Hosts（`pve`、`vm-infra`、`vm-monitoring`、`vm-apps`、`vm-code`） | Prometheus の `node_exporter` から、CPU・メモリ・ディスク（`/`）の使用率を出す（アイコンは Ubuntu、`pve` は Proxmox）。手動起動の `vm-dev` は、停止中に値が取れないため含めない。Grafana のダッシュボードと同じ元データで、こちらは現在値の一覧向き | なし |
| Prometheus | `https://prometheus.lab.kanare.dev`。監視対象の up / down 数。手動起動の `vm-dev` は down に数えない（`TargetDown` と同じ条件） | なし |
| Alertmanager | 同上（ウィジェットの種類は `prometheusmetric`）。Prometheus の `ALERTS` から、発報中（`Watchdog` を除く）と保留中の件数を出す。Alertmanager 専用のウィジェットはないため | なし |
| Healthchecks.io | `https://healthchecks.io` の API。外部 Heartbeat（[監視・アラート](monitoring.md#外部-heartbeat)）の状態 | SOPS（`homepage_healthchecks_api_key`。読み取り専用キー） |
| Home Assistant | `https://ha.lab.kanare.dev`。SwitchBot Hub 2 の温度・湿度（`sensor.switchbot_hub_2_temperature` / `sensor.switchbot_hub_2_humidity`） | SOPS（`homepage_ha_token`。HA の長期アクセストークン `homepage`） |
| 天気 | Open-Meteo（東京の座標。リポジトリが公開なので、市区町村レベルに留める） | なし（キー不要） |

- Prometheus は、`vm-apps` から `9090` に直接届かない（`vm-monitoring` の `DOCKER-USER` が Caddy だけを許可している）。そのため Caddy 経由の URL を使う。
- シークレットは `homepage.env.j2` が `/opt/homepage/.env` に `HOMEPAGE_VAR_*` として書き出し、`services.yaml` が `{{HOMEPAGE_VAR_*}}` で参照する。値は Git に入れない（[秘密情報管理](../operations/runbooks/secrets.md)）。

### ウィジェットを足すとき

1. シークレットが要るなら、先にユーザーが `sops ansible/inventory/group_vars/apps/secrets.sops.yml` で追記する。`monitoring` など別グループのファイルに入れると、`vm-apps` から読めない。
2. `homepage.env.j2` に `HOMEPAGE_VAR_*` を足し、`services.yaml` か `widgets.yaml` にウィジェットを書く。
3. `make setup-apps` で反映する。表示が空のときは `docker logs homepage` を見る。
4. `docs/operations/runbooks/secrets.md` の表と、この文書のウィジェットの表を更新する。

### 見送ったもの

- **Tailscale のウィジェット**: API キーの有効期間が最長 90 日で、失効するとウィジェットが黙って壊れる。OAuth クライアントのトークンは短命で、Homepage が受け付けない。更新の手間に見合わないので入れていない。
- **Grafana のウィジェット**: 認証情報が増える割に、画面で得られる情報が少ないため見送った。

## 注意点

- `latest` を使っているため、再作成のたびにバージョンが変わりうる。設定の書式が変わって表示が壊れたら、`docker logs homepage` で原因を確認する。
- `vm-apps` の他のコンテナ（Home Assistant、n8n）と同じ VM を共有する。メモリを使い切ると Homepage にも影響する。
- Docker ソケット（`/var/run/docker.sock`）を読み取り専用でマウントしている。Docker の統合を使う場合のためで、現在のタイルは使っていない。
