# 移行性

環境を別のハードウェア・ネットワーク・バージョンへ移すときの、前提・影響範囲・手順を整理する。構成をコードで持つため、**移行の基本は「新しい環境でコードを流し直す」**こと。ネットワークの移行（VLAN・ルーター交換）の詳細は [VLAN 設計](../07_network/vlan-design.md) が正。

## 方針

- VM とサービスは、Terraform と Ansible で再作成できる状態を保つ。ディスクのコピーによる移行はしない。
- 環境に固有の値（IP、ゲートウェイ、ドメイン）は変数に寄せる。ただし寄せ切れていない箇所があるため、一覧で管理する。
- 引き継ぐ必要があるのは、**コードにないデータ**だけ。何があるかを先に把握する。

## 環境に依存するもの

| 種類 | 内容 | 定義場所 |
| --- | --- | --- |
| IP・ゲートウェイ・DNS | `192.168.11.0/24`、`gateway`、`dns_server` | `ansible/inventory/group_vars/all.yml`、`terraform/proxmox/variables.tf` / `terraform.tfvars`、`hosts.yml` |
| ドメイン | `lab.kanare.dev`（`domain`） | `group_vars/all.yml`、`dns_records`、Caddyfile |
| Proxmox | ノード名 `pve`、テンプレート `ubuntu-cloud`（VMID 9000）、ストレージ `local-lvm` | `terraform.tfvars`、`terraform/proxmox/README.md` |
| ルーターの IP | 構成表、管理画面のリンク、Caddy の転送先 | [DNS 構成](../07_network/dns.md#ルーターを付け替えるとき) の表 |
| 外部サービスのアカウント | Cloudflare、Tailscale、Slack | SOPS（値）と各サービスの管理画面（設定） |

## コードに入っていないデータ

| データ | 場所 | 移行の扱い |
| --- | --- | --- |
| age 秘密鍵 | 運用者の Mac（iCloud Keychain に退避） | 必須。新しい Mac には [運用 Runbook](../runbook.md#別の-mac-で復元する) の手順で復元 |
| SSH 鍵 | 運用者の Mac（`~/.ssh/id_ed25519_homelab` など） | 必須。Terraform が VM に公開鍵を配る |
| Terraform の state | Mac のローカル（`terraform.tfstate`） | 新しい環境を作り直すなら不要。既存の VM を引き継ぐなら必要（[災害対策](../10_disaster-recovery/disaster-recovery.md#リポジトリの外にあるもの)） |
| Proxmox のテンプレート VM（9000） | Proxmox ホスト | 手順書から再作成（`terraform/proxmox/README.md`） |
| Tailscale の登録 | Tailscale 側と `vm-infra` | 再登録（`tailscale_authkey`）。subnet route の承認と split DNS は管理画面で設定 |
| Prometheus の履歴 | `vm-monitoring` のボリューム | 引き継がなくてもよい（保持 30 日） |
| AdGuard の手作業の設定 | `vm-infra` | `playbooks/infra.yml` が設定する範囲を超える手作業は、移行前に確認する |
| Caddy の証明書 | `vm-infra` のボリューム | 新環境で再取得される |
| `vm-code` の未 push の作業 | `vm-code` | 置かない運用。移行前に push する |
| `vm-windows` | Proxmox のディスク | 検証用。必要なら Proxmox のバックアップ機能で個別に移す |

## 移行シナリオ

### A. Proxmox ホストの交換（ハードウェア更新）

1. 新ホストに Proxmox VE を入れ、IP を `192.168.11.10` にする。
2. テンプレート VM（9000）と API トークンを作り直す（`terraform/proxmox/README.md`）。
3. `make setup-proxmox` で PVE の設定（収集スクリプトなど）を反映する。
4. `terraform apply` で VM を作り、`make setup` で全 VM を構成する。順序は `vm-infra` → `vm-monitoring` → 残り。
5. Tailscale の再登録と、subnet route の承認を行う。
6. 動作確認（DNS、Grafana、アラート、外出先からの接続）。
7. 旧ホストを止める。

手順の詳細は [災害対策](../10_disaster-recovery/disaster-recovery.md) の再構築手順と共通。

### B. ルーターの交換・VLAN 化

[VLAN 設計](../07_network/vlan-design.md) の段階に従う（設計段階、未適用）。

- 全ホストのアドレスを `10.<VLAN>.0.0/24` に変える。一斉切り替えとし、事前準備と切り戻し手順を用意する。
- 影響を受ける箇所の一覧は [VLAN 設計: 影響を受けるリポジトリ内の箇所](../07_network/vlan-design.md#影響を受けるリポジトリ内の箇所)。
- ルーター単体の付け替え（IP が変わる場合）は [DNS 構成](../07_network/dns.md#ルーターを付け替えるとき)。

### C. 引っ越し（上流ネットワークが変わる）

- LAN の内側（`192.168.11.0/24` または VLAN 後のアドレス）は変えずに持ち込める。変わるのは WAN 側だけ。
- 新居の上流が `192.168.11.0/24` と被ると、Tailscale 経由の接続が不安定になる。被る場合は VLAN 化後の `10.x` 系に移行してから引っ越す。
- 二重 NAT でなくなっても、外部公開はしない方針（[外部接続](../08_external-connectivity/external-connectivity.md)）。

### D. Proxmox VE のバージョンアップ

- 現在は 8.x。メジャーアップグレードは、公式の手順に従ってホスト上で行う。
- 事前に、`ansible/roles/proxmox/` のパッチ（Web UI の警告除去）が新しいバージョンで一致しないことを確認する。一致しなければ何もしない作りになっている。
- 事前に `terraform/proxmox` の Provider（`telmate/proxmox`）が新バージョンに対応しているか確認する。
- 再起動を伴うため、停止してよい時間帯に行う。

### E. ハイパーバイザーの変更（Proxmox 以外へ）

想定していない。移行するなら、VM 作成部分（`terraform/proxmox/`）を差し替える。Ansible・Docker Compose の層は、Ubuntu が動けばそのまま使える。

## OS・ミドルウェアの更新方針

| 対象 | 現状 | 備考 |
| --- | --- | --- |
| Ubuntu（ゲスト） | テンプレート 9000 から作成。更新は `apt` で手動 | LTS の入れ替えは、新しいテンプレートから VM を作り直す形が基本 |
| Docker イメージ | `latest`。更新は `docker compose pull` で手動 | バージョン固定は未実施（[信頼性](../03_reliability/reliability.md#既知の弱点と対応状況)） |
| Terraform Provider | `3.0.2-rc07`（RC を固定） | 更新は `terraform init -upgrade` と `plan` で確認 |
| Ansible・コレクション | `ansible/requirements.yml` | CI の ansible-lint で検査 |

## 移行前のチェックリスト

- [ ] 移行対象の VM に、コードにないデータがないか確認した（上の表）
- [ ] `vm-code` / `vm-dev` の未 push の作業を push した
- [ ] age 秘密鍵と SSH 鍵を、新しい環境で使える
- [ ] `terraform plan` と `make check`（Ansible のドライラン）が差分なしで通る
- [ ] 切り戻しの手順を用意した（旧環境を残す、または旧構成のコミットを控える）
- [ ] `make lint-all` が通る
