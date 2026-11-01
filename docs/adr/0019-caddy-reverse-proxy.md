# 0019. リバースプロキシに Caddy を使う

- ステータス: 採用
- 日付: 2026-11-01（導入時の判断は記録なし。現行構成の理由を整理し直した）

## 背景

LAN 内の Web 画面（Grafana、Proxmox、AdGuard Home など）を、`https://<name>.lab.kanare.dev` の正規の証明書で開けるようにする入口が要る（[リバースプロキシと TLS](../services/02-reverse-proxy-tls.md)）。Caddy を採用して稼働しているが、nginx、Nginx Proxy Manager、Traefik、Cloudflare Tunnel と比べた記録が残っていなかったため、選んだ理由を明文化する。導入当時の検討記録は無く、以下は現在の要件に照らして評価し直したもの。

要件は次のとおり。

- 外から 80/443 に届かない（二重 NAT）ため、DNS-01 で正規の証明書を取る。
- サービスが少ないので、FQDN ごとに個別取得する。取得と更新は自動にする。
- 設定は Git で管理し、Ansible で配置して再現できるようにする。
- `vm-infra`（1.5GB）に載るので軽くする。

## 決定

リバースプロキシと TLS 終端には Caddy を使う。Cloudflare DNS プラグインを `xcaddy` で組み込んだイメージをビルドする。

## 理由

- **証明書の取得・更新が組み込みで自動。** Caddyfile にサイト名を書くだけで、Let's Encrypt の取得と更新まで完結する。certbot や cron を別に持たなくてよい。
- **設定が短いテキスト 1 ファイル。** Caddyfile は 1 サービス数行で、Git 管理と Ansible での配置に向く。再作成は Git から行える。
- **DNS-01 は Cloudflare プラグインで足りる。** ドメインの DNS は Cloudflare にあり、API トークンを SOPS で管理している。
- **軽い。** 単一バイナリで、`vm-infra` の資源を圧迫しない。

## 代替案

| 案 | 判断 |
| --- | --- |
| nginx | 見送り。TLS は動くが、証明書の取得・更新に certbot などと DNS-01 の連携を別に組む必要がある。得るものは、Caddy にない機能が要るとき |
| Nginx Proxy Manager | 見送り。設定が DB と Web UI にあり、Git で差分管理・再現しにくい。GUI で足せる手軽さより、設定をコードで持つ方針を優先する |
| Traefik | 見送り。Docker ラベルによる動的な設定が強みだが、サービスが少なく入口が静的なので活かせない。設定の概念も多い |
| Cloudflare Tunnel | 用途が違う。外部公開の手段で、LAN 内の入口ではない。外部公開が必要になれば別に判断する（[ADR 0005](0005-tailscale-only-remote-access.md)） |

## 影響と再検討の条件

- 入口は `vm-infra` の Caddy に集約され、その障害は全 Web 入口に影響する（[可用性](../architecture/04-reliability.md)）。
- Cloudflare プラグイン入りのイメージを自前でビルドするため、Caddy 本体の更新時にビルドが要る。
- 次のいずれかになったら、再検討する（新しい ADR を追加して、この ADR を置き換える）。
  - コンテナが頻繁に増減し、ラベルによる自動検出が欲しくなった（Traefik）。
  - Caddy にない機能（高度な負荷分散、WAF など）が要る。
  - Caddy のプラグインのビルドや更新が負担になった。

詳細: [リバースプロキシと TLS](../services/02-reverse-proxy-tls.md)
