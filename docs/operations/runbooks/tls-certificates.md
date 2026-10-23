# LAN 内 TLS

## 現在の構成

`vm-infra` 上の Caddy（Docker Compose）が Cloudflare DNS-01 チャレンジで Let's Encrypt 証明書を取得し、各サービスへのリバースプロキシを担う。

- 証明書はドメインごとに個別取得（`*.lab.kanare.dev` ワイルドカードではなく各 FQDN）
- クライアント側の設定不要。全デバイスからブラウザ警告なしにアクセス可能
- `CLOUDFLARE_API_TOKEN` 環境変数で Cloudflare API を認証（Ansible が `.env` を生成して配置）

| サービス | URL |
| --- | --- |
| Proxmox | <https://pve.lab.kanare.dev> |
| Grafana | <https://grafana.lab.kanare.dev> |
| Prometheus | <https://prometheus.lab.kanare.dev> |
| Homepage | <https://home.lab.kanare.dev> |
| AdGuard Home | <https://adguard.lab.kanare.dev> |
| code-server | <https://code.lab.kanare.dev> |
| CloudCLI | <https://cloudcli.lab.kanare.dev> |

設定ファイル: `docker/compose/reverse-proxy/Caddyfile`

## 証明書の状態確認

```bash
# Caddy のログで証明書取得状況を確認
ssh ubuntu@192.168.11.11 "cd /opt/reverse-proxy && docker compose logs caddy | grep -i tls"

# 証明書の有効期限を確認（例: grafana）
echo | openssl s_client -connect grafana.lab.kanare.dev:443 2>/dev/null \
  | openssl x509 -noout -dates
```

## 証明書の更新

Caddy は自動で更新するため通常は手動操作不要。
更新に失敗している場合は以下を確認する。

```bash
# Caddy コンテナの再起動（更新を強制トリガー）
ssh ubuntu@192.168.11.11 "cd /opt/reverse-proxy && docker compose restart caddy"

# Cloudflare API トークンが有効か確認（値は表示しない）
curl -s -H "Authorization: Bearer $(sops -d --extract '["cloudflare_api_token"]' ansible/inventory/group_vars/infra/secrets.sops.yml)" \
  "https://api.cloudflare.com/client/v4/zones?name=kanare.dev" | jq '.success'
```

## 新しいサービスを追加する

`docker/compose/reverse-proxy/Caddyfile` に以下のブロックを追記し、Caddy を再起動する。

```
newservice.lab.kanare.dev {
	reverse_proxy 192.168.11.XX:PORT
	tls {
		dns cloudflare {env.CLOUDFLARE_API_TOKEN}
		resolvers 1.1.1.1
	}
}
```

```bash
ssh ubuntu@192.168.11.11 "cd /opt/reverse-proxy && docker compose up -d --force-recreate caddy"
```

## Proxmox へのリバースプロキシについて

Proxmox のバックエンドは自己署名証明書のため、Caddyfile で `tls_insecure_skip_verify` を設定している。
これは LAN 内のみでのアクセスかつ Proxmox 自体の証明書管理が難しいための措置。
