# Day 0 / Day 1 / Day 2 手順

homelab の構築から運用までを 3 フェーズに分けて整理する。

## Day 0 — 計画・準備

Day 0 は「何を作るか」を決め、基盤を準備するフェーズ。

### チェックリスト

- [x] ハードウェア調達・ラッキング
- [x] Proxmox VE インストール（`192.168.11.10`）
- [x] ネットワーク設計確定（IP 規約は `README.md` 参照）
- [x] SSH 鍵ペア生成
- [x] このリポジトリをクローン
- [ ] Cloud-init テンプレート VM を作成（`terraform/proxmox/README.md` 参照）
- [ ] Proxmox API トークン発行
- [ ] `terraform.tfvars` を準備
- [ ] DNS ドメイン（`lab.kanare.dev`）を決定
- [ ] 秘密情報管理方針を決定（SOPS + age または Ansible Vault）

### 実行

```bash
# 1. Terraform で VM をプロビジョニング
cd terraform/proxmox
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars   # 実際の値を設定
terraform init
terraform plan
terraform apply
```

```bash
# 2. VM に SSH できることを確認
ssh ubuntu@192.168.11.11
ssh ubuntu@192.168.11.13
ssh ubuntu@192.168.11.20
ssh ubuntu@192.168.11.21
```

## Day 1 — 構築・デプロイ

Day 1 は VM の初期セットアップとサービスデプロイを行うフェーズ。

### チェックリスト

- [ ] Ansible inventory を環境に合わせて編集
- [ ] 全 VM に共通セットアップ（パッケージ, SSH 硬化, UFW, Docker）
- [ ] vm-infra: CoreDNS + Caddy デプロイ
- [ ] vm-monitoring: Prometheus + Grafana デプロイ
- [ ] 全 VM に node_exporter デプロイ
- [ ] DNS 名前解決テスト
- [ ] Grafana ダッシュボード設定
- [ ] Reverse Proxy 経由のアクセス確認

### 実行

```bash
# 1. Ansible で全 VM をセットアップ
cd ansible
ansible-playbook playbooks/site.yml

# 2. DNS 動作確認（vm-infra 上で）
dig @192.168.11.11 grafana.lab.kanare.dev

# 3. Monitoring 動作確認
# ブラウザで http://192.168.11.13:3000 にアクセス
# Grafana にログイン（admin / changeme → パスワード変更）
# "Node Exporter Full" ダッシュボードをインポート（ID: 1860）

# 4. Reverse Proxy 動作確認
# ブラウザで https://grafana.lab.kanare.dev にアクセス
```

### 推奨ダッシュボード（Grafana）

| ID | 名前 | 用途 |
|---|---|---|
| 1860 | Node Exporter Full | VM のシステムメトリクス |
| 3662 | Prometheus 2.0 Overview | Prometheus 自体の状態 |

## Day 2 — 運用・改善

Day 2 は継続的な運用と改善のフェーズ。

### 定期作業

| 頻度 | 作業 | コマンド |
|---|---|---|
| 毎日 | Grafana でメトリクス確認 | ブラウザ |
| 週次 | VM の `apt upgrade` | `ansible all -m apt -a "upgrade=yes update_cache=yes"` |
| 月次 | Docker イメージ更新 | `docker compose pull && docker compose up -d` |
| 月次 | Terraform state 確認 | `terraform plan`（差分がないことを確認） |
| 随時 | バックアップ検証 | `docs/runbook.md` 参照 |

### 改善ロードマップ

- [ ] Alertmanager 導入（Slack / Discord 通知）
- [ ] WireGuard VPN セットアップ
- [ ] ログ収集（Loki + Promtail）
- [ ] バックアップ自動化（Proxmox Backup Server or restic）
- [ ] VM テンプレートの Packer 化
- [ ] CI/CD パイプライン（GitHub Actions で lint + plan）
- [ ] Kubernetes クラスタ（k3s）への移行検討
- [ ] UPS 導入と自動シャットダウン
