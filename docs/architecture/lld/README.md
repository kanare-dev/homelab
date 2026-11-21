# 詳細設計（LLD）

サービスごとの詳細設計と、IP アドレスのような具体的な値をまとめる。構成、設定、運用上の注意、制約を扱う。全体の方式は[基本設計](../hld/README.md)、手順は [運用 Runbook](../../operations/runbooks/README.md)、設計判断は [ADR](../../adr/README.md) に書く。機器の仕様と公式資料は [hardware/](hardware/README.md) にある。機器の設定値は、ネットワーク機器が `network/`、Proxmox ホストが `platform/` にある。

役割ごとにフォルダを分け、ファイル名は `<サービス名>.md`（番号は付けない）にする。

## 文書

### network/: ネットワークの入口と管理

| 文書 | 内容 |
| --- | --- |
| [DNS](network/dns.md) | AdGuard Home・Unbound・CoreDNS の 3 層構成 |
| [リバースプロキシと TLS](network/reverse-proxy-tls.md) | Caddy による入口と、Let's Encrypt の証明書 |
| [IP アドレス一覧](network/ip-addresses.md) | アドレスの範囲、VLAN、ホスト、FQDN の宛先、DHCP。**IP アドレスの正** |
| [Omada コントローラー](network/omada-controller.md) | `vm-omada` の構成、サイトの設定値、バックアップの運用、Omada Cloud。管理対象の ER605・SG2210P の設定値 |
| [Buffalo WSR-1800AX4P](network/wsr-1800ax4p.md) | AP モードで使う Wi-Fi の入口の設定値 |

### platform/: 基盤の運用

| 文書 | 内容 |
| --- | --- |
| [監視・アラート](platform/monitoring.md) | Prometheus・Alertmanager・Grafana、アラート一覧、容量の上限設定 |
| [Proxmox ホスト](platform/proxmox-host.md) | ThinkCentre M70q Tiny 上の Proxmox VE の設定値（IP、NIC、ストレージ、BIOS の確認項目） |
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

### hardware/: 機器の仕様と資料

| 文書 | 内容 |
| --- | --- |
| [hardware/README.md](hardware/README.md) | 機器の一覧、仕様の置き方の決まり。ThinkCentre、ER605、SG2210P、Buffalo の仕様と公式資料。導入前の機器・用品（10 インチラック） |

## 運用

- 新しいサービスを追加したら、役割に合うフォルダに `<サービス名>.md` で置き、この表と `docs/README.md` を更新する。合うフォルダが無ければ、新しい役割のフォルダを作り、この README に節を足す。
- 構成を変えたら、該当する文書を同じ変更で更新する。
