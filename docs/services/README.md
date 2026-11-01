# services

サービスごとの詳細設計。構成、設定、運用上の注意、制約をまとめる。全体の方式は [architecture/](../architecture/README.md)、手順は [運用 Runbook](../operations/runbooks/README.md)、設計判断は [ADR](../adr/README.md) に書く。

## 文書

| 番号 | 文書 | 内容 |
| --- | --- | --- |
| 01 | [DNS](01-dns.md) | AdGuard Home・Unbound・CoreDNS の 3 層構成 |
| 02 | [リバースプロキシと TLS](02-reverse-proxy-tls.md) | Caddy による入口と、Let's Encrypt の証明書 |
| 03 | [監視・アラート](03-monitoring.md) | Prometheus・Alertmanager・Grafana、アラート一覧、容量の上限設定 |
| 04 | [Homepage](04-homepage.md) | LAN 内サービスのダッシュボード |
| 05 | [Home Assistant](05-home-assistant.md) | スマートホームの操作と自動化 |
| 06 | [n8n](06-n8n.md) | ワークフローの自動実行と週次レポート |
| 09 | [FreshRSS](09-freshrss.md) | RSS リーダー。購読リストの退避 |
| 07 | [CI/CD](07-cicd.md) | Terraform + Ansible のフローと CI の方針 |
| 08 | [vm-code](08-vm-code.md) | 常用リモート開発環境 |
| 10 | [MOTD](10-motd.md) | SSH ログイン時の表示（ホスト名のバナーとシステム情報） |

## 運用

- 新しいサービスを追加したら、次の番号を振り、この表と `docs/README.md` を更新する
- 構成を変えたら、該当する文書を同じ変更で更新する
