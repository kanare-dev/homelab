# vm-code（常用リモート開発環境）

`vm-code`（`192.168.11.22`、vmid 122、`vm-dev` 同等スペック）は、Claude Code やブラウザ版 VS Code で外出先から開発するための常用環境。

## 分離した理由

`vm-dev` は「破壊検証用」と「Claude Code + モバイル remote control による外出先からの常用開発」を兼ねていた。破壊検証中に常用環境を壊すリスクがあるため、常用環境を `vm-code` に切り出した。`vm-dev` は Ansible・Docker・ネットワーク設定の破壊検証用として使う。

## 構成

- Terraform（`terraform.tfvars`）で VM を定義する
- Ansible ロール `code_tools` で、git / mosh / gh / Node.js / Claude Code CLI / CloudCLI（`@cloudcli-ai/cloudcli`、siteboon/claudecodeui）/ code-server / moshi-hook を再現可能にプロビジョニングする
- `make setup-code` で単独プロビジョニングできる

## アクセス経路

CLI・ブラウザ・モバイルの 3 経路をカバーする。

| 経路 | 入口 |
| --- | --- |
| CLI | SSH / mosh（`vm-code.lab.kanare.dev`） |
| ブラウザ | code-server（`code.lab.kanare.dev`） |
| モバイル | CloudCLI（`cloudcli.lab.kanare.dev`）、iOS の Moshi アプリ |

- iOS の Moshi アプリからは、専用鍵（`code_extra_authorized_keys`）と直接 DNS レコード（`vm-code.lab.kanare.dev`）で SSH / mosh 接続する。`moshi-hook` を systemd --user サービスとして常駐させて連携する（ペアリングのみ手動）
- アクセスは Tailscale 経由に限定する。UFW で該当ポートを、LAN / Tailscale サブネットルート経由の `192.168.11.0/24` からのみ許可する。Cloudflare Tunnel 等での外部公開はしない（[ADR 0005](../adr/0005-tailscale-only-remote-access.md)）
