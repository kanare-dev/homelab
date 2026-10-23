# 0008. Authelia を導入しない

- ステータス: 採用（導入を見送る）
- 日付: 2026-10-24

## 背景

Web 画面の認証がサービスごとにばらばらで、Prometheus・Alertmanager・Homepage は認証がない（[セキュリティ](../architecture/05-security.md#web-画面)）。ロードマップにあった Authelia（Caddy の `forward_auth` によるログインの一元化と 2 要素認証）を入れるかどうかを検討した。

## 決定

Authelia は導入しない。認証のない画面は、当面そのままにする。

## 理由

- **メリットが小さい。** Authelia は各サービスの手前に置く追加の玄関で、各サービスのログインはなくならない。Grafana は OIDC で連携できるが、AdGuard・CloudCLI は各自のログインが残る。得られるのは、認証のない画面への鍵と、2 要素認証の一元化だけ。
- 守る対象は Prometheus と Homepage の 2 つで、いずれも Tailscale に認証済みの自分の端末からしか届かない。
- `vm-infra` に、コンテナ・設定・秘密値が増える。Authelia が落ちると対象に入れなくなる。
- Caddy を通る経路だけが保護され、ポート直打ち（例: `192.168.11.13:9090`）は素通りになる。意味を持たせるには UFW の絞り込みが別途必要で、それは Authelia と独立して効果がある。

## 代替案

| 案 | 判断 |
| --- | --- |
| Authelia（Caddy の `forward_auth`） | 見送り（上記） |
| Caddy の `basic_auth` | 必要になったら第一候補。数行で足り、部品が増えない。2 要素認証はない |
| Authentik / Keycloak | 1.5GB の `vm-infra` と 1 人の利用に対して過剰 |
| バックエンドのポートを UFW で `vm-infra` からだけ許可する | Authelia と独立に効果がある。[セキュリティ](../architecture/05-security.md#未対応要確認の項目)の未対応項目として扱う |

## 影響と再検討の条件

- Prometheus・Alertmanager・Homepage は、認証なしのまま。LAN と Tailscale の端末から届く。
- 次のいずれかになったら、再検討する（新しい ADR を追加して、この ADR を置き換える）。
  - Tailscale に参加する端末や人が増え、認証なしの画面を見せたくなくなった。
  - 認証のないサービスが増えた。
  - 管理画面（Omada など）に、2 要素認証を前段でかけたくなった（[VLAN 設計](../architecture/08-vlan-design.md#管理画面への外部到達リスクを受け入れる)）。
- VLAN の導入後は、Tailscale の ACL で端末ごと・宛先ごとにアクセスを絞る方針が、同じ脅威への対策になる。

詳細: [セキュリティ](../architecture/05-security.md)
