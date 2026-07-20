# Ansible — 構成管理

Ansible で各 VM の初期セットアップとサービスデプロイを行う。

## 前提条件

- Ansible >= 2.15
- 対象 VM に SSH 鍵認証でログイン可能
- Python 3 が対象 VM にインストール済み

## ディレクトリ構成

```
ansible/
├── ansible.cfg          # Ansible 設定
├── inventory/
│   ├── hosts.yml        # ホスト一覧
│   ├── group_vars/      # グループ変数
│   │   ├── all.yml
│   │   ├── apps.yml
│   │   ├── dev.yml
│   │   ├── code/        # vars.yml + vault.yml（暗号化）
│   │   ├── infra/       # vars.yml + vault.yml（暗号化）
│   │   └── monitoring/  # vars.yml + vault.yml（暗号化）
│   └── host_vars/       # ホスト固有変数
│       ├── pve.yml
│       ├── vm-code.yml
│       ├── vm-infra.yml
│       └── vm-monitoring.yml
├── roles/
│   ├── common/          # 共通セットアップ（パッケージ, SSH, UFW, NTP）
│   ├── docker/          # Docker CE インストール
│   ├── node_exporter/   # Prometheus node_exporter
│   ├── coredns/         # CoreDNS
│   ├── code_tools/      # git, mosh, gh, Node.js, Claude Code CLI, CloudCLI, code-server
│   └── proxmox/         # Proxmox ホスト自体の設定
└── playbooks/
    ├── site.yml         # 全体実行
    ├── proxmox.yml      # Proxmox ホスト用
    ├── infra.yml        # infra VM 用
    ├── monitoring.yml   # monitoring VM 用
    ├── apps.yml         # apps VM 用
    └── code.yml         # code VM 用
```

## 使い方

```bash
# 全 VM を一括セットアップ
ansible-playbook playbooks/site.yml

# 特定の VM だけ実行
ansible-playbook playbooks/infra.yml
ansible-playbook playbooks/monitoring.yml

# ドライラン（変更を適用しない）
ansible-playbook playbooks/site.yml --check --diff

# 特定のタグだけ実行
ansible-playbook playbooks/site.yml --tags docker

# 接続テスト
ansible all -m ping
```

## Roles 一覧

| Role | 内容 | 適用先 |
|---|---|---|
| `common` | パッケージ, SSH 硬化, UFW, NTP, hostname | 全 VM |
| `docker` | Docker CE + Compose Plugin | 全 VM |
| `node_exporter` | Prometheus node_exporter | 全 VM + Proxmox ホスト |
| `coredns` | CoreDNS | infra |
| `code_tools` | git, mosh, gh, Node.js, Claude Code CLI, CloudCLI, code-server | code |
| `proxmox` | Proxmox ホスト自体の設定 | proxmox |

Caddy（リバースプロキシ）は Ansible role ではなく、`infra.yml` が Docker Compose（`docker/compose/reverse-proxy/`）としてデプロイする。

## 秘密情報の管理

機密変数は Ansible Vault で暗号化する:

```bash
# 暗号化
ansible-vault encrypt inventory/group_vars/all.yml

# 暗号化ファイルを使って実行
ansible-playbook playbooks/site.yml --ask-vault-pass
```
