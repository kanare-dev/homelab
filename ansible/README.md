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
├── requirements.yml     # 必要な Ansible コレクション
├── inventory/
│   ├── hosts.yml        # ホスト一覧
│   ├── group_vars/      # グループ変数
│   │   ├── all.yml
│   │   ├── dev.yml
│   │   ├── apps/        # vars.yml + secrets.sops.yml（SOPS 暗号化）
│   │   ├── code/        # 同上
│   │   ├── infra/       # 同上
│   │   └── monitoring/  # 同上
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
│   ├── code_tools/      # git, mosh, gh, Node.js, Claude Code CLI, CloudCLI, code-server, moshi-hook
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

### Lint

```bash
# 初回のみ: ansible-lint が見つけられる場所にコレクションを入れる
ansible-galaxy collection install -r requirements.yml -p ~/.ansible/collections --force

make lint   # リポジトリ直下で実行
```

## Roles 一覧

| Role | 内容 | 適用先 |
|---|---|---|
| `common` | パッケージ, SSH 硬化, UFW, NTP, hostname | 全 VM |
| `docker` | Docker CE + Compose Plugin | 全 VM |
| `node_exporter` | Prometheus node_exporter | 全 VM + Proxmox ホスト |
| `coredns` | CoreDNS | infra |
| `code_tools` | git, mosh, gh, Node.js, Claude Code CLI, CloudCLI, code-server, moshi-hook | code |
| `proxmox` | Proxmox ホスト自体の設定 | proxmox |

Caddy（リバースプロキシ）は Ansible role ではなく、`infra.yml` が Docker Compose（`docker/compose/reverse-proxy/`）としてデプロイする。

## 秘密情報の管理

機密変数は SOPS + age で暗号化した `group_vars/<group>/secrets.sops.yml` に置く。`community.sops` の vars プラグイン（`ansible.cfg` で有効）が実行時に自動で復号するため、パスワードの入力やオプションは不要。

```bash
# 初回のみ: 必要なコレクションを入れる
ansible-galaxy collection install -r requirements.yml

# 編集（復号 → エディタ → 再暗号化）
sops inventory/group_vars/monitoring/secrets.sops.yml
```

age 秘密鍵の場所、別の Mac での復元、ローテーションは `docs/runbook.md` の「秘密情報管理」を参照。
