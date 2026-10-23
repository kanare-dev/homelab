# セキュリティ

脅威の想定、守る対象、現在の対策と未対応の項目を整理する。**リポジトリは公開**であることが設計の前提。機密値の操作手順は [運用 Runbook](../operations/runbooks/secrets.md#秘密情報管理) を参照。

## 想定する脅威

| 脅威 | 例 | 主な対策 |
| --- | --- | --- |
| 公開リポジトリからの漏えい | 平文の API トークン・鍵・パスワードをコミットする | SOPS 暗号化、gitleaks、`make lint-all` |
| LAN 内の侵害の拡大 | IoT 機器や来客の端末から、サーバーや管理画面に届く | UFW（現在）、VLAN 分割（計画） |
| 外部からの不正アクセス | 管理画面・SSH への侵入 | 外部公開しない。入口は Tailscale のみ |
| 認証情報の窃取 | 端末紛失、SSH 鍵・age 鍵の流出 | 鍵認証のみ、鍵の退避と再発行手順 |
| ソフトウェアの脆弱性 | OS・コンテナの未更新 | 手動更新（弱点として認識） |

家庭内の個人利用を前提とし、標的型攻撃や物理的な侵入は想定しない。

## 守る対象

| 対象 | 重要度の理由 |
| --- | --- |
| age 秘密鍵 | 全ての SOPS 暗号文を復号できる。漏れると、Git 履歴の暗号文も含めて全シークレットが読まれる |
| Proxmox の root・API トークン | 全 VM を操作できる |
| Cloudflare API トークン | DNS を書き換えられる（DNS-01 用） |
| Tailscale のアカウント・認証鍵 | LAN への入口 |
| Slack Webhook URL | 通知の偽造 |
| `vm-code`（Claude Code、リポジトリの作業コピー） | 開発用の認証情報が置かれる |

## 秘密情報の管理

詳細は [運用 Runbook](../operations/runbooks/secrets.md#秘密情報管理) と、リポジトリ直下の `CLAUDE.md`。

- 機密値は **SOPS + age** で暗号化して Git に置く（`*.sops.yml`）。キー名は平文、値だけが暗号化される。
- Ansible は `community.sops` の vars プラグインで、Terraform は `carlpett/sops` プロバイダーで、実行時に復号する。VM 上の `.env` は Ansible がテンプレートから生成する。
- 平文のシークレットファイルを作らない。`sops -d` の出力を保存しない。値はチャット・ログ・文書に書かない（文字数・ハッシュ・一部の文字も含む）。
- SOPS 内のシークレットの一覧は Runbook の表が正。SOPS の外にあるものは、非公開の台帳（リポジトリ外）で管理する。
- CI では復号しない（age 秘密鍵を CI に置かない）。暗号化されていることだけを確認する（[CI/CD](../services/cicd.md)）。

### 鍵の保管と退避

| 項目 | 内容 |
| --- | --- |
| age 秘密鍵 | Mac の `~/Library/Application Support/sops/age/keys.txt`（`chmod 600`）。リポジトリに入れない |
| 退避先 | iCloud Keychain（Mac が壊れても復元できるようにする） |
| 別の Mac での復元・ローテーション | [運用 Runbook](../operations/runbooks/secrets.md#別の-mac-で復元する) |
| 鍵が漏れたとき | 鍵の差し替えに加え、**各シークレット自体を再発行する**（Git 履歴に旧鍵で復号できる暗号文が残る） |

## アクセス制御

### ホストへのログイン

| 項目 | 設定 | 管理場所 |
| --- | --- | --- |
| SSH | 鍵認証のみ（`PasswordAuthentication no`）、root ログイン禁止 | `ansible/roles/common/`、`group_vars/all.yml` |
| VM のパスワード | `ubuntu` / `root` はロック。緊急用パスワードは設定していない（2026-10-22 に見送り） | [運用 Runbook](../operations/runbooks/troubleshooting.md#vm-が応答しない) |
| コンソール | Proxmox のコンソールからはログインできない。入るときは SSH | 同上 |

### Web 画面

| 画面 | 認証 | 備考 |
| --- | --- | --- |
| Proxmox / Grafana / AdGuard / code-server | 各サービスのログイン | Grafana と code-server のパスワードは SOPS 管理 |
| Prometheus / Alertmanager | **認証なし** | LAN 内からのみ到達できる前提 |
| Homepage | 認証なし | 同上 |
| ルーター | ルーターのログイン | Caddy から転送先まで HTTP（LAN 内） |

ログインの一元化（Authelia）は導入しない（[ADR 0008](../adr/0008-no-authelia.md)）。

### Terraform の権限

Terraform は Proxmox の API トークン（`terraform@pam!terraform-token`）で操作する。トークンの値は SOPS で管理する。Proxmox の TLS 検証は無効（`pm_tls_insecure = true`。自己署名証明書のため、LAN 内に限る）。

## ネットワークの防御

### ファイアウォール（UFW）

全 VM で既定は**受信拒否**。必要なポートだけを `ufw_allowed_ports`（`group_vars/<group>/vars.yml`）で許可する。SSH（22/tcp）は常に許可。

| VM | 許可するポート |
| --- | --- |
| `vm-infra` | 22, 53（tcp/udp）, 80, 443, 51820/udp, 9100, 3000（LAN と Docker ブリッジのみ） |
| `vm-monitoring` | 22, 3000, 9090, 9093, 9100 |
| `vm-apps` | 22, 3001, 9100 |
| `vm-code` | 22, 9100。8080（code-server）、3001（CloudCLI）、5173（開発用サーバ）、60000–61000/udp（mosh）は `192.168.11.0/24` のみ |
| `vm-dev` | 22, 9100 |

Proxmox ホストの UFW / Proxmox ファイアウォールの設定は、このリポジトリでは管理していない。

### 経路と暗号化

- 外部には何も公開しない（二重 NAT でポート開放もしていない）。外出先からは Tailscale（WireGuard）で入る（[外部接続](03-network.md)）。
- LAN 内の Web は、Caddy が Let's Encrypt の正規証明書で HTTPS 化する。バックエンドへの通信は HTTP の場合がある（ルーター、Homepage など）。
- Proxmox は自己署名証明書のため、Caddy が `tls_insecure_skip_verify` で接続する。

### セグメンテーション

現在は `192.168.11.0/24` の 1 セグメントに全機器が載る。IoT・ゲスト・管理機器の分離は [VLAN 設計](08-vlan-design.md)（設計段階、未適用）。

## 監査・検知

| 対象 | 仕組み |
| --- | --- |
| 平文シークレットの混入 | gitleaks（CI と `make lint-all`） |
| SOPS ファイルの暗号化漏れ | `make sops-encrypted-check`（CI と同じ） |
| 名前解決 | AdGuard のクエリログ（7 日保持） |
| ホストの異常 | node_exporter のメトリクスとアラート。認証ログなど、**セキュリティ専用のログ収集はしていない** |

## 未対応・要確認の項目

| 項目 | 内容 | 方針 |
| --- | --- | --- |
| node_exporter（9100）の許可元 | 全 VM で `from` の指定がなく、どこからでも許可 | 監視 VM（と必要な端末）に限定するか検討。VLAN 化で自然に絞れる |
| Grafana・Prometheus 等のポートの許可元 | 同上（`vm-monitoring`、`vm-apps`） | 同上 |
| `vm-infra` の 51820/udp | `# WireGuard` のコメント付きで許可しているが、WireGuard 単体は構成に含まれない（VPN は Tailscale） | 用途を確認し、不要なら閉じる |
| Tailscale の ACL | 既定のまま。`192.168.11.1`（ルーター）にも届く | ACL で管理画面を除外する（未実施。[DNS 構成](../services/dns.md#ルーター管理画面)） |
| 認証の一元化 | Prometheus・Homepage は認証なし | 導入しない（[ADR 0008](../adr/0008-no-authelia.md)）。ポートの許可元の絞り込みは別途検討 |
| OS・コンテナの更新 | 手動。コンテナイメージは `latest` | 定期更新の手順とタイミングを決める |
| ルーターへの通信 | Caddy からの転送が平文 HTTP | LAN 内のみのため受け入れ。TP-Link への移行で再設計 |
| Proxmox ホストのファイアウォール | リポジトリで管理していない | 現状を確認し、方針を決める |

## 関連

- [運用 Runbook: 秘密情報管理](../operations/runbooks/secrets.md#秘密情報管理)
- [VLAN 設計](08-vlan-design.md)
- [外部接続](03-network.md)
