# 第6章 セキュリティ

この章では、想定する脅威、守る対象、現在の対策、未対応の項目を整理する。**リポジトリを公開している**ことが、設計の前提になる。機密値の操作手順は、[運用 Runbook](../../operations/runbooks/03-secrets.md#秘密情報管理)を参照してほしい。

## 想定する脅威

| 脅威 | 例 | 主な対策 |
| --- | --- | --- |
| 公開リポジトリからの漏えい | 平文の API トークン・鍵・パスワードをコミットする | SOPS 暗号化、gitleaks、`make lint-all` |
| LAN 内の侵害の拡大 | IoT 機器や来客の端末から、サーバーや管理画面に届く | UFW（現在）、VLAN 分割（計画） |
| 外部からの不正アクセス | 管理画面・SSH への侵入 | 外部公開しない。入口は Tailscale のみ（例外: Omada Cloud。Omada コントローラーの管理画面に、TP-Link ID の認証だけで入れる） |
| 認証情報の窃取 | 端末紛失、SSH 鍵・age 鍵の流出 | 鍵認証のみ、鍵の退避と再発行手順 |
| ソフトウェアの脆弱性 | OS・コンテナの未更新 | 手動更新（弱点として認識） |

家庭内での個人利用を前提にしているので、標的型攻撃や物理的な侵入は想定しない。

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

詳しくは、[運用 Runbook](../../operations/runbooks/03-secrets.md#秘密情報管理)と、リポジトリ直下の `CLAUDE.md` に書いている。

- 機密値は **SOPS + age** で暗号化して、Git に置く（`*.sops.yml`）。キー名は平文のままで、値だけが暗号化される。
- Ansible は `community.sops` の vars プラグインで、Terraform は `carlpett/sops` プロバイダーで、実行時に復号する。VM 上の `.env` は Ansible がテンプレートから生成する。
- 平文のシークレットファイルは作らない。`sops -d` の出力も保存しない。値は、チャット、ログ、文書に書かない（文字数、ハッシュ、一部の文字も書かない）。
- SOPS 内のシークレットの一覧は、Runbook の表が正である。SOPS の外にあるものは、リポジトリの外にある非公開の台帳で管理する。
- CI では復号しない。age 秘密鍵を CI に置かず、暗号化されていることだけを確認する（[CI/CD](../lld/dev/cicd.md)）。

### 鍵の保管と退避

| 項目 | 内容 |
| --- | --- |
| age 秘密鍵 | Mac の `~/Library/Application Support/sops/age/keys.txt`（`chmod 600`）。リポジトリに入れない |
| 退避先 | iCloud Keychain（Mac が壊れても復元できるようにする） |
| 別の Mac での復元・ローテーション | [運用 Runbook](../../operations/runbooks/03-secrets.md#別の-mac-で復元する) |
| 鍵が漏れたとき | 鍵の差し替えに加え、**各シークレット自体を再発行する**（Git 履歴に旧鍵で復号できる暗号文が残る） |

## アクセス制御

### ホストへのログイン

| 項目 | 設定 | 管理場所 |
| --- | --- | --- |
| SSH | 鍵認証のみ（`PasswordAuthentication no`）、root ログイン禁止 | `ansible/roles/common/`、`group_vars/all/vars.yml` |
| VM のパスワード | `ubuntu` に全 VM 共通のパスワードを設定（ハッシュは SOPS）。使うのはコンソールと `sudo -v` だけで、SSH のパスワード認証は無効のまま。`root` はロック（[ADR-0013](../../adr/0013-vm-console-password.md)） | `ansible/roles/common/`、[秘密情報管理](../../operations/runbooks/03-secrets.md) |
| コンソール | Proxmox のコンソールから `ubuntu` でログインできる。`root` は入れない（`sudo -i` で昇格する） | 同上 |

### Web 画面

| 画面 | 認証 | 備考 |
| --- | --- | --- |
| Proxmox / Grafana / AdGuard / code-server | 各サービスのログイン | Grafana と code-server のパスワードは SOPS 管理 |
| Prometheus / Alertmanager | **認証なし** | LAN 内からのみ到達できる前提 |
| Home Assistant | Home Assistant のログイン | LAN 内からのみ到達できる（Caddy 経由）。外出先は Tailscale |
| FreshRSS | FreshRSS のログイン | LAN 内からのみ到達できる（Caddy 経由）。外出先は Tailscale。シークレットは持たない |
| n8n | n8n のログイン | LAN 内からのみ到達できる（Caddy 経由）。外出先は Tailscale。認証情報の暗号鍵は SOPS 管理 |
| Homepage | 認証なし | 同上 |
| ルーター | ルーターのログイン | Caddy から転送先まで HTTP（LAN 内） |

ログインの一元化（Authelia）は導入しない（[ADR 0008](../../adr/0008-no-authelia.md)）。

### Terraform の権限

Terraform は Proxmox の API トークン（`terraform@pam!terraform-token`）で操作する。トークンの値は SOPS で管理する。Proxmox の TLS 検証は無効（`pm_tls_insecure = true`。自己署名証明書のため、LAN 内に限る）。

## ネットワークの防御

### ファイアウォール（UFW）

全 VM で、受信は既定で**拒否**する。必要なポートだけを、`ufw_allowed_ports`（`group_vars/<group>/vars.yml`）で許可する。SSH（22/tcp）は、常に許可する。

| VM | 許可するポート |
| --- | --- |
| `vm-infra` | 22, 53（tcp/udp）, 80, 443, 51820/udp。9100 は `vm-monitoring` のみ、3000 は LAN と Docker ブリッジのみ |
| `vm-monitoring` | 22。9100 は自分自身と Prometheus コンテナ（`172.16.0.0/12`）のみ。3000・9090・9093 は下の「Docker の公開ポート」 |
| `vm-apps` | 22。9100 は `vm-monitoring` のみ。8123（Home Assistant）は `vm-infra`（Caddy）のみ。3001（Homepage）、5678（n8n）、8081（FreshRSS）は下の「Docker の公開ポート」 |
| `vm-code` | 22。9100 は `vm-monitoring` のみ。8080（code-server）、3001（CloudCLI）、5173（開発用サーバ）、60000–61000/udp（mosh）は Trusted（`10.77.30.0/24`）と `vm-infra`（`10.77.20.10`。Tailscale 経由の接続の送信元）のみ |
| `vm-dev` | 22。9100 は `vm-monitoring` のみ |

許可する送信元は `from:` で指定する。ufw は、定義にないルールを自動では消さない。そのため、以前の「どこからでも許可」というルールは、`ufw_removed_ports` に書いて、`common` ロールに削除させる。

#### Docker の公開ポート

Docker の `ports:` で公開したポートへの通信は、NAT によって、UFW の受信ルールより前に通ってしまう。そのため、`ufw_allowed_ports` に `from:` を書いても効かない。そこで `ufw_docker` ロールが、`/etc/ufw/after.rules` の `DOCKER-USER` チェーンに、許可した送信元以外から公開ポートに来た接続を破棄するルールを入れる。許可する送信元は、`docker_published_allow`（`group_vars/<group>/vars.yml`）に書く。

| VM | 公開ポート | 許可元 |
| --- | --- | --- |
| `vm-monitoring` | 3000（Grafana）、9090（Prometheus）、9093（Alertmanager） | `vm-infra`（Caddy）のみ |
| `vm-apps` | 3001（Homepage）、5678（n8n）、8081（FreshRSS） | `vm-infra`（Caddy）のみ |

- Home Assistant（8123）は host ネットワークで動くので、Docker の公開ポートには当たらない。この絞り込みは効かないため、UFW の受信ルールで `vm-infra` だけに許可している。
- IP アドレスとポートを直接指定した接続（例: `http://10.77.20.11:9090`）は届かない。Mac からは、`https://<名前>.lab.kanare.dev` で開く。
- `vm-infra` の 80 番と 443 番（Caddy）は、全サービスの入口なので、LAN に開けたままにしている。
- 設定を確認するには、`ssh <vm> sudo iptables -S DOCKER-USER` を実行する。

Proxmox ホストの UFW と Proxmox ファイアウォールの設定は、このリポジトリでは管理していない。

### 経路と暗号化

- 外部には何も公開しない（二重 NAT でポート開放もしていない）。外出先からは Tailscale（WireGuard）で入る（[外部接続](05-network.md)）。
- LAN 内の Web サービスは、Caddy が Let's Encrypt の正規の証明書を使って HTTPS で提供する。Caddy からバックエンドへの通信は、HTTP の場合がある（ルーター、Homepage など）。
- Proxmox は自己署名証明書を使っているので、Caddy は `tls_insecure_skip_verify` を指定して接続する。

### セグメンテーション

ネットワークは、Management（`10.77.10.0/24`）、Servers（`10.77.20.0/24`）、Trusted（`10.77.30.0/24`）、Lab（`10.77.40.0/24`）などの VLAN に分けている。ただし ACL は全許可のままで、絞り込みは未実施である（[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）。IoT、ゲスト、管理機器を分離する設計は、[第5章 ネットワーク](05-network.md)にまとめており、ACL を絞るときに適用する。

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
| Proxmox ホストの node_exporter（9100）・SSH・8006 | ファイアウォールが無効で、LAN からどこからでも届く | 上の「Proxmox ホストのファイアウォール」と合わせて方針を決める |
| `vm-infra` の 51820/udp | `# WireGuard` のコメント付きで許可しているが、WireGuard 単体は構成に含まれない（VPN は Tailscale） | 用途を確認し、不要なら閉じる |
| Tailscale の ACL | 既定のまま。Caddy 経由で、Omada コントローラーと Proxmox の管理画面のログイン画面に届く | ACL で管理画面を除外する（未実施。[DNS 構成](../lld/network/dns.md#管理画面omada-コントローラー)） |
| 認証の一元化 | Prometheus・Homepage は認証なし | 導入しない（[ADR 0008](../../adr/0008-no-authelia.md)）。ポートの許可元の絞り込みは別途検討 |
| OS・コンテナの更新 | 手動。コンテナイメージは `latest` | 定期更新の手順とタイミングを決める |
| ルーターへの通信 | Caddy からの転送が平文 HTTP | LAN 内のみのため受け入れ。TP-Link への移行で再設計 |
| Proxmox ホストのファイアウォール | リポジトリで管理していない | 現状を確認し、方針を決める |

## 関連

- [運用 Runbook: 秘密情報管理](../../operations/runbooks/03-secrets.md#秘密情報管理)
- [第5章 ネットワーク](05-network.md)
- [外部接続](05-network.md)
