# 0008. Authelia でログインを一元化する（提案）

- ステータス: 提案（運用者の判断待ち。採用したら「採用」に更新する）
- 日付: 2026-10-24

## 背景

Web 画面の認証がサービスごとにばらばらで、Prometheus・Alertmanager・Homepage は認証がない（[セキュリティ](../architecture/05-security.md#web-画面)）。外出先からは Tailscale 経由で Caddy の入口に届く。VLAN 設計では、Omada コントローラーなど管理画面のログイン画面が Caddy 経由で外から届くことも、受け入れたリスクとして残っている（[VLAN 設計](../architecture/08-vlan-design.md#管理画面への外部到達リスクを受け入れる)）。

ロードマップの Authelia を、Caddy の `forward_auth` で入れるかどうかを決める。

## 決定（案）

`vm-infra` に Authelia を Docker Compose で追加し、`auth.lab.kanare.dev` で公開する。Caddy の `forward_auth` で、次のサービスに適用する。

| 対象 | 適用 | 理由 |
| --- | --- | --- |
| Prometheus、Homepage | する | 認証がないため |
| Grafana、AdGuard、code-server、CloudCLI | しない（各サービスのログインを維持） | 独自の認証がある。code-server / CloudCLI は WebSocket とモバイルからの接続があり、前段のログインと相性が悪い |
| PVE、Omada、ルーター | しない | Authelia が落ちたときに、基盤を直すための管理画面に入れなくなる。**非常口は前段に置かない** |

- 認証は 2 要素（TOTP または passkey）を必須にする。ユーザーは自分 1 人で、ユーザー情報はファイルで持つ。通知はメールではなくファイルに出す。
- Authelia の秘密値（セッション鍵、暗号化鍵、パスワードのハッシュ）は SOPS で管理する。

## 理由

- 認証のない画面に、2 要素を後付けできる。
- 新しいサービスを足すときは、Caddy に数行足すだけで保護できる。
- `vm-infra` は Caddy の置き場所で、Authelia が同居しても障害の範囲は広がらない（Caddy が止まれば、どのみち Web の入口は止まる）。

## 代替案

| 案 | 長所 | 短所 |
| --- | --- | --- |
| Authelia（案） | 2 要素、複数サービスで共通のログイン | コンテナ・設定・秘密値が増える。落ちると対象サービスに入れない |
| Caddy の `basic_auth` | 数行で済む。部品が増えない | 2 要素なし。パスワードのハッシュを Caddyfile に持つ |
| Authentik / Keycloak | OIDC で各サービスと連携できる | 1.5GB の `vm-infra` には重い。1 人の利用には過剰 |
| 何もしない | 追加の手間なし | 認証なしの画面が残る |

## 影響と再検討の条件

- **Caddy を通る経路だけが保護される。** `192.168.11.13:9090` のようにポート直打ちなら、前段のログインを素通りできる。意味を持たせるなら、バックエンドのポートを `vm-infra` からだけ許可する UFW 設定（`from 192.168.11.11`）が前提になる。これは [セキュリティ](../architecture/05-security.md#未対応要確認の項目) の未対応項目と重なるので、一緒に進める。
- Authelia が落ちると、対象の Prometheus・Homepage に Caddy 経由で入れない（ポート直打ちは、UFW を絞るまで開ける）。
- 守る対象が Prometheus と Homepage の 2 つだけなら、効果に対して部品が多い。`basic_auth` で足りるなら、そちらにする。サービスが増えたとき、または管理画面を前段で守りたくなったときに、改めて判断する。
- VLAN 移行（[ADR 0004](0004-vlan-cutover-all-at-once.md)）で、`auth.lab.kanare.dev` の転送先とアドレスが変わる。

詳細: [リバースプロキシと TLS](../services/reverse-proxy-tls.md)
