# services

サービスごとの詳細設計。構成、設定、運用上の注意、制約をまとめる。全体の方式は [architecture/](../architecture/README.md)、手順は [運用 Runbook](../operations/runbooks/README.md)、設計判断は [ADR](../adr/README.md) に書く。機器（ルーター、スイッチ、Proxmox ホストなど）の設定値は、[hardware/](../hardware/README.md) にある。

役割ごとにフォルダを分け、ファイル名は `<サービス名>.md`（番号は付けない）にする。

## 文書

### network/: ネットワークの入口と管理

| 文書 | 内容 |
| --- | --- |
| [DNS](network/dns.md) | AdGuard Home・Unbound・CoreDNS の 3 層構成 |
| [リバースプロキシと TLS](network/reverse-proxy-tls.md) | Caddy による入口と、Let's Encrypt の証明書 |
| [Omada コントローラー](network/omada-controller.md) | `vm-omada` の構成、サイトの設定値、バックアップの運用、Omada Cloud |

### platform/: 基盤の運用

| 文書 | 内容 |
| --- | --- |
| [監視・アラート](platform/monitoring.md) | Prometheus・Alertmanager・Grafana、アラート一覧、容量の上限設定 |
| [MOTD](platform/motd.md) | SSH ログイン時の表示（ホスト名のバナーとシステム情報） |

### apps/: アプリ

| 文書 | 内容 |
| --- | --- |
| [Homepage](apps/homepage.md) | LAN 内サービスのダッシュボード |
| [Home Assistant](apps/home-assistant.md) | スマートホームの操作と自動化 |
| [n8n](apps/n8n.md) | ワークフローの自動実行と週次レポート |
| [FreshRSS](apps/freshrss.md) | RSS リーダー。購読リストの退避 |

### dev/: 開発環境と CI/CD

| 文書 | 内容 |
| --- | --- |
| [CI/CD](dev/cicd.md) | Terraform + Ansible のフローと CI の方針 |
| [vm-code](dev/vm-code.md) | 常用リモート開発環境 |

## 運用

- 新しいサービスを追加したら、役割に合うフォルダに `<サービス名>.md` で置き、この表と `docs/README.md` を更新する。合うフォルダが無ければ、新しい役割のフォルダを作り、この README に節を足す。
- 構成を変えたら、該当する文書を同じ変更で更新する。
- 以前は、番号つきのファイル名（`01-dns.md` など）で、フォルダを分けていなかった。2026-11-06 に、番号を外してフォルダ分けに変えた（機器の設定値は、同じ日に [hardware/](../hardware/README.md) に移した）。
