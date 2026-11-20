# 移行性

この文書では、環境を別のハードウェア、ネットワーク、バージョンへ移すときの、前提、影響範囲、手順を整理する。構成をコードで管理しているので、**移行の基本は、新しい環境でコードを流し直すこと**である。ネットワークの移行（VLAN 化やルーターの交換）の詳細は、[VLAN 設計](08-vlan-design.md)が正である。

## 方針

- VM とサービスは、Terraform と Ansible でいつでも作り直せるようにしておく。ディスクをコピーして移行することはしない。
- 環境に固有の値（IP、ゲートウェイ、ドメイン）は、変数にまとめる。ただし、まとめきれていない箇所があるので、一覧にして管理する。
- 引き継ぐ必要があるのは、**コードに入っていないデータ**だけである。どのようなデータがあるかを、先に把握しておく。

## 環境に依存するもの

| 種類 | 内容 | 定義場所 |
| --- | --- | --- |
| IP・ゲートウェイ・DNS | VM ごとの `ip`・`gateway`・`nameserver`・`vlan_id`、`ansible_host`、`static_ip` | `terraform/proxmox/terraform.tfvars`、`ansible/inventory/hosts.yml`、`host_vars` |
| ドメイン | `lab.kanare.dev`（`domain`） | `group_vars/all/vars.yml`、`dns_records`、Caddyfile |
| Proxmox | ノード名 `pve`、テンプレート `ubuntu-cloud`（VMID 9000）、ストレージ `local-lvm` | `terraform.tfvars`、`terraform/proxmox/README.md` |
| ルーターの IP | 構成表、管理画面のリンク、Caddy の転送先 | [DNS 構成](../services/network/dns.md#ルーターを付け替えるとき) の表 |
| 外部サービスのアカウント | Cloudflare、Tailscale、Slack | SOPS（値）と各サービスの管理画面（設定） |

## コードに入っていないデータ

| データ | 場所 | 移行の扱い |
| --- | --- | --- |
| age 秘密鍵 | 運用者の Mac（iCloud Keychain に退避） | 必須。新しい Mac には、[運用 Runbook](../operations/runbooks/03-secrets.md#別の-mac-で復元する)の手順で復元する |
| SSH 鍵 | 運用者の Mac（`~/.ssh/id_ed25519_homelab` など） | 必須。Terraform が VM に公開鍵を配る |
| Terraform の state | Mac のローカル（`terraform.tfstate`） | 新しい環境を作り直すなら不要。既存の VM を引き継ぐなら必要（[災害対策](07-disaster-recovery.md#リポジトリの外にあるもの)） |
| Proxmox のテンプレート VM（9000） | Proxmox ホスト | 手順書から再作成（`terraform/proxmox/README.md`） |
| Tailscale の登録 | Tailscale 側と `vm-infra` | 再登録（`tailscale_authkey`）。subnet route の承認と split DNS は管理画面で設定 |
| Prometheus の履歴 | `vm-monitoring` のボリューム | 引き継がなくてもよい（保持 30 日） |
| AdGuard の手作業の設定 | `vm-infra` | `playbooks/infra.yml` が設定する範囲を超える手作業は、移行前に確認する |
| Caddy の証明書 | `vm-infra` のボリューム | 新環境で再取得される |
| `vm-code` の未 push の作業 | `vm-code` | 置かない運用。移行前に push する |

## 移行シナリオ

### A. Proxmox ホストの交換（ハードウェア更新）

1. 新ホストに Proxmox VE を入れ、IP を `10.77.10.10`（`vmbr0.10`、VLAN10）にする。
2. テンプレート VM（9000）と API トークンを作り直す（`terraform/proxmox/README.md`）。
3. `make setup-proxmox` で PVE の設定（収集スクリプトなど）を反映する。
4. `terraform apply` で VM を作り、`make setup` で全 VM を構成する。順序は `vm-infra` → `vm-monitoring` → 残り。
5. Tailscale を再登録し、subnet route を承認する。
6. DNS、Grafana、アラート、外出先からの接続が動くことを確認する。
7. 旧ホストを止める。

この手順は、[災害対策](07-disaster-recovery.md)の再構築手順と共通である。詳しくはそちらを参照してほしい。

### B. ルーターの交換・VLAN 化

[VLAN 設計](08-vlan-design.md)の段階に従って進める（設計の段階であり、未適用）。

- 全ホストのアドレスを `10.77.<VLAN>.0/24` に変える。一斉に切り替えるので、事前の準備と、切り戻しの手順を用意しておく。
- 影響を受ける箇所の一覧は、[VLAN 設計: 影響を受けるリポジトリ内の箇所](08-vlan-design.md#影響を受けるリポジトリ内の箇所)にある。
- ルーターだけを付け替える場合（IP が変わるとき）は、[DNS 構成](../services/network/dns.md#ルーターを付け替えるとき)を参照してほしい。

### C. 引っ越し（上流ネットワークが変わる）

- LAN の内側（`192.168.11.0/24`、または VLAN 化後のアドレス）は、変えずに新居へ持ち込める。変わるのは WAN 側だけである。
- 新居の上流が `192.168.11.0/24` と重なると、Tailscale 経由の接続が不安定になる。重なる場合は、VLAN 化後の `10.77.x.x` に移行してから引っ越す。
- 二重 NAT でなくなっても、外部には公開しない方針は変えない（[外部接続](03-network.md)）。

### D. Proxmox VE のバージョンアップ

- 現在は 8.x を使っている。メジャーアップグレードは、公式の手順に従って、ホスト上で行う。
- 作業の前に、`ansible/roles/proxmox/` のパッチ（Web UI の警告の除去）が、新しいバージョンのコードと一致しないことを確認する。一致しない場合、パッチは何もしない作りになっている。
- 作業の前に、`terraform/proxmox` の Provider（`telmate/proxmox`）が、新しいバージョンに対応しているかを確認する。
- 再起動が必要になるので、サービスを止めてよい時間帯に行う。

### E. ハイパーバイザーの変更（Proxmox 以外へ）

Proxmox 以外に移すことは、想定していない。移す場合は、VM を作る部分（`terraform/proxmox/`）だけを差し替える。Ansible と Docker Compose の層は、Ubuntu が動けば、そのまま使える。

## OS・ミドルウェアの更新方針

| 対象 | 現状 | 備考 |
| --- | --- | --- |
| Ubuntu（ゲスト） | テンプレート 9000 から作成。更新は `apt` で手動 | LTS の入れ替えは、新しいテンプレートから VM を作り直す形が基本 |
| Docker イメージ | `latest`。更新は `docker compose pull` で手動 | バージョン固定は未実施（[信頼性](04-reliability.md#既知の弱点と対応状況)） |
| Terraform Provider | `3.0.2-rc07`（RC を固定） | 更新は `terraform init -upgrade` と `plan` で確認 |
| Ansible・コレクション | `ansible/requirements.yml` | CI の ansible-lint で検査 |

## 移行前のチェックリスト

- [ ] 移行対象の VM に、コードにないデータがないか確認した（上の表）
- [ ] `vm-code` / `vm-dev` の未 push の作業を push した
- [ ] age 秘密鍵と SSH 鍵を、新しい環境で使える
- [ ] `terraform plan` と `make check`（Ansible のドライラン）が差分なしで通る
- [ ] 切り戻しの手順を用意した（旧環境を残す、または旧構成のコミットを控える）
- [ ] `make lint-all` が通る
