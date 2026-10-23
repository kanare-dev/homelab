# リバースプロキシと TLS

`vm-infra` 上の Caddy が、LAN 内サービスの入口と HTTPS 化を担う。操作手順（証明書の確認・更新、サービスの追加）は [運用 Runbook](../operations/runbooks/tls-certificates.md#lan-内-tls)。

## 構成

```text
client ─► https://<name>.lab.kanare.dev (192.168.11.11:443, Caddy)
            └─► 各サービス（HTTP。Proxmox のみ自己署名 HTTPS）
```

| 項目 | 内容 |
| --- | --- |
| 実装 | Caddy（Docker Compose。`docker/compose/reverse-proxy/`）。`xcaddy` で Cloudflare DNS プラグインを組み込んだイメージをビルドする |
| 待ち受け | 80、443（tcp/udp）。サービスは HTTPS のみ（`auto_https disable_redirects`。`http://` では接続できない） |
| 証明書 | Let's Encrypt。Cloudflare の DNS-01 チャレンジで取得し、**FQDN ごとに個別取得**（ワイルドカードではない） |
| 認証 | Cloudflare の API トークン（`cloudflare_api_token`、SOPS 管理）。Ansible が `.env` を生成して配置 |
| 更新 | Caddy が自動更新する。証明書とキーは `caddy_data` ボリューム |
| クライアント側の設定 | 不要。正規の証明書なので、全端末でブラウザの警告が出ない |

## 設計判断

| 判断 | 理由 |
| --- | --- |
| DNS-01 を使う | LAN 内のサービスで、外から 80/443 に届かない（二重 NAT）。DNS 経由の検証なら公開不要で正規の証明書が取れる |
| FQDN ごとに取得する | ワイルドカード（`*.lab.kanare.dev`）は使わず、サービスごとに個別取得している（サブドメインが少ない） |
| 入口を `vm-infra` に集約する | 新しいサービスも同じ入口に追加できる。一方で、`vm-infra` の障害が全 Web 入口に影響する（[可用性](../architecture/04-reliability.md)） |
| Proxmox は `tls_insecure_skip_verify` | バックエンドが自己署名証明書のため。LAN 内に限る（[セキュリティ](../architecture/05-security.md)） |
| ルーター管理画面も Caddy 経由にする | `.dev` は HSTS プリロードで HTTP が使えない。ルーターは 443 に対応しないため、Caddy で HTTPS 化する（[DNS 構成](dns.md#ルーター管理画面)） |

## 転送先

FQDN と転送先の対応は [アドレス・命名規約](../architecture/03-network.md#ドメイン命名規約)、定義は `Caddyfile` が正。

## 依存と影響

- Cloudflare / Let's Encrypt が止まると、新規取得・更新ができない。既存の証明書は期限まで使える（[外部接続](../architecture/03-network.md#外部サービスへの依存)）。
- Caddy が止まると、`*.lab.kanare.dev` の Web 画面に入れない。各サービスの IP:ポート直打ちでは開ける。
