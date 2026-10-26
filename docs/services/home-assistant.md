# Home Assistant

スマートホームの機器をまとめて操作・自動化する。`vm-apps` に Container 版で置く。判断の記録: [ADR-0011](../adr/0011-home-assistant-on-vm-apps.md)。

## 構成

| 項目 | 内容 |
| --- | --- |
| 置き場所 | `vm-apps`（`192.168.11.20`）の `/opt/homeassistant` |
| 種類 | Home Assistant Container（アドオンは使えない） |
| イメージ | `ghcr.io/home-assistant/home-assistant:2026.10.4`（バージョンを固定する） |
| ネットワーク | `network_mode: host`（機器の自動検出に mDNS / SSDP が要るため） |
| URL | `https://ha.lab.kanare.dev`（Caddy 経由。証明書は Caddy が取得） |
| 実使用 | メモリ約 370MB、設定ディレクトリ約 1.3MB（2026-10-26、導入直後） |
| 定義 | `docker/compose/homeassistant/`、`ansible/playbooks/apps.yml` |

## アクセス経路とファイアウォール

```text
Mac / スマホ ─ HTTPS ─> Caddy（vm-infra :443） ─ HTTP ─> vm-apps :8123（Home Assistant）
```

- `vm-apps` の 8123 は、`vm-infra`（Caddy）からだけ許可する（`group_vars/apps/vars.yml` の `ufw_allowed_ports`）。IP とポートの直打ち（`http://192.168.11.20:8123`）は届かない。
- Home Assistant は host ネットワークで動くため、Docker の公開ポートではない。`ufw_docker` ロールの `DOCKER-USER` による絞り込みは効かず、**UFW の受信ルールで絞る**。
- Caddy 経由のリクエストを受けるには、Home Assistant に Caddy を信頼させる必要がある（次節）。
- 外部には公開しない。外出先からは Tailscale 経由で使う（[ADR-0005](../adr/0005-tailscale-only-remote-access.md)）。
- 認証は Home Assistant のログインのみ。Authelia は使わない（[ADR-0008](../adr/0008-no-authelia.md)）。

## 設定の管理

守る対象は設定の YAML だけで、Git に置く（[ADR-0011](../adr/0011-home-assistant-on-vm-apps.md)）。

| ファイル | 置き場所（Git） | 反映と更新 |
| --- | --- | --- |
| `configuration.yaml` | `docker/compose/homeassistant/config/` | Ansible が毎回上書きする。変更は Git で行う |
| `automations.yaml` / `scripts.yaml` / `scenes.yaml` | 同上 | **画面から編集される**ので、Ansible は無いときだけ作る。画面で変更したら `make ha-config-pull` で Git に取り込む |
| `.storage/http`（HTTP の設定。Caddy を信頼する） | `docker/compose/homeassistant/storage/http` | 初期値。Ansible は無いときだけ置く |

`make ha-config-pull` は、`vm-apps` の 3 つの YAML を読み出して Git の作業ツリーに書く（HA が末尾の改行を省くので補う）。差分を確認してからコミットする。

### HTTP の設定（Caddy を信頼する）

Home Assistant 2026.10 以降、`http:` の設定は初回起動のときだけ YAML から `.storage/http` に取り込まれる。以後は YAML が**無視される**ので、`configuration.yaml` に `trusted_proxies` を書いても効かない。信頼する Caddy の IP は `storage/http` の初期値で与える。

- 初期値を変えて既存のインスタンスに反映するには、コンテナを止め、`/opt/homeassistant/config/.storage/http` を退避してから、`make setup-apps` を実行する（無ければ初期値が置かれる）。
- 設定が合っていないと、Caddy 経由は HTTP 400 になる。ログに `your HTTP integration is not set-up for reverse proxies` が出る。

### Git に入らないもの

`/opt/homeassistant/config` の次のものは Git に入らない。VM を失うと消える。

- `.storage/`（ユーザー、機器と統合の登録、ダッシュボード、トークン）
- 履歴のデータベース（`home-assistant_v2.db`）

統合のトークンは SOPS にも入れない。HA の画面に直接入力し、`.storage/` にだけ保存する。再発行の手段は非公開の台帳に記録する（[秘密情報管理](../operations/runbooks/secrets.md)）。

## 統合

| 統合 | 接続方法 | 備考 |
| --- | --- | --- |
| SwitchBot Cloud | SwitchBot のクラウド API（トークンとシークレット）。Hub 経由 | クラウドに依存し、Bluetooth より反応が遅い。API の上限は 1 日 10,000 回 |
| Spotify | 公式統合（Spotify の開発者アプリの Client ID / Secret） | 再生の操作には Premium が要る |

- Matter としてテレビ（Google TV）やルーターが検出されることがあるが、コントローラー側の機器で、取り込む必要はない。Matter 対応機器を使うときは、`python-matter-server` を別コンテナで動かす（Container 版の制約）。
- SwitchBot Cloud は、外部 URL が無いと webhook を使えず、`SwitchBot Cloud webhook not configured because no external URL is available` と警告する。外部に公開しない方針なので、そのままにする（状態はポーリングで更新される）。

## 機器の検出と VLAN

現在は全機器が同じ LAN にあるため、mDNS / SSDP の検出が届く。[VLAN 設計](../architecture/08-vlan-design.md) に移行すると、`vm-apps`（Servers）から Clients・IoT の機器が見えなくなる。

- SwitchBot Cloud と Spotify はクラウド経由なので影響しない。
- Google Cast（テレビ）や Matter、LAN 内の機器を使うときは、次のどちらかを決める必要がある（未決。[ロードマップ](../operations/roadmap.md)）。
  - Servers ↔ IoT / Clients に mDNS の中継と、必要なポートの許可を追加する。
  - Home Assistant を IoT または Clients に置く。
- host ネットワークで動くので、UFW の受信拒否が機器からの応答を落とすことがある。検出が必要になったときに、実機で確認してポートを許可する（推測で開けない）。

## 監視

- `blackbox_http` で `https://ha.lab.kanare.dev` を外形監視する（`service="homeassistant"`、`host="vm-apps"`）。失敗は `ServiceProbeFailed` で通知される（[監視・アラート](monitoring.md)）。
- Homepage に「Home」の Home Assistant タイルがある。
- コンテナのログは 10MB × 3 ファイル（`docker-compose.yml` の `x-logging`）。履歴は HA の recorder が既定で 10 日分だけ残して削除する。

## 更新

1. [リリースノート](https://www.home-assistant.io/blog/categories/release-notes/) の破壊的変更を確認する。
2. `docker/compose/homeassistant/docker-compose.yml` のイメージのタグを変える。
3. `make setup-apps` を実行する（compose の変更で再起動される）。
4. `https://ha.lab.kanare.dev` が開き、`probe_success` が 1 に戻ることを確認する。

## 復旧

VM を作り直したとき、または `/opt/homeassistant` を失ったとき。

1. `make setup-apps` を実行する。ディレクトリ、`configuration.yaml`、`.storage/http` の初期値、YAML の 3 ファイルが Git から置かれ、コンテナが起動する。
2. `https://ha.lab.kanare.dev` を開き、ユーザーを作り直す（初期設定の画面）。
3. 統合を追加し直す（SwitchBot Cloud、Spotify）。トークンは SwitchBot アプリと Spotify の開発者画面で再発行できる。
4. ダッシュボードや機器・エンティティの名前は失われているので、必要なら設定し直す。

失うもの: ユーザー、統合の登録、ダッシュボード、機器の名前、履歴。守れるもの: `configuration.yaml` とオートメーション・スクリプト・シーン（最後に `make ha-config-pull` した時点まで）。

## 既知の制約

- アドオンストアは使えない（Container 版）。必要なものは別コンテナで動かす。
- `.storage/` と履歴はバックアップしていない（[ADR-0011](../adr/0011-home-assistant-on-vm-apps.md)）。
- `vm-apps` の他のコンテナ（Homepage）と同じ VM を共有する。Home Assistant の異常がメモリを使い切ると、Homepage にも影響する。
