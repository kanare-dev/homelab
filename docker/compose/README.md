# Docker Compose — サービス定義

各 VM 上で動作するサービスを Docker Compose で定義する。

## ディレクトリ構成

```text
docker/compose/
├── README.md
├── monitoring/              # vm-monitoring 上で実行
│   ├── docker-compose.yml
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── alertmanager/
│   │   └── alertmanager.yml
│   ├── blackbox/            # 外形監視（HTTPS / DNS のプローブ定義）
│   │   └── blackbox.yml
│   └── grafana/
│       └── provisioning/
│           └── datasources/
│               └── prometheus.yml
├── reverse-proxy/           # vm-infra 上で実行（Ansible の infra.yml がデプロイ）
│   ├── docker-compose.yml
│   └── Caddyfile
├── dns/                     # vm-infra 上で実行: AdGuard Home + Unbound（Ansible の infra.yml がデプロイ）
│   └── docker-compose.yml
├── homeassistant/           # vm-apps 上で実行（Ansible の apps.yml がデプロイ）
│   ├── docker-compose.yml
│   ├── config/              # configuration.yaml と、画面で編集される YAML（make ha-config-pull で取り込む）
│   └── storage/http         # .storage/http の初期値（Caddy を信頼する設定）
├── n8n/                     # vm-apps 上で実行（Ansible の apps.yml がデプロイ）
│   ├── docker-compose.yml
│   └── workflows/           # ワークフローの JSON（make n8n-workflows-pull で取り込む。初回の取り込み後に作られる）
└── homepage/                # vm-apps 上で実行（Ansible の apps.yml がデプロイ）
    ├── docker-compose.yml
    ├── config/
    └── icons/               # 公式アイコンを加工したもの（Prometheus の炎を白抜きにしたもの）
```

## 起動方法

### Monitoring（vm-monitoring 上で実行）

```bash
cd monitoring
docker compose up -d

# ログ確認
docker compose logs -f

# 停止
docker compose down
```

起動後のアクセス先:

| サービス | URL | 認証 |
| --- | --- | --- |
| Prometheus | `http://192.168.11.13:9090` | なし |
| Grafana | `http://192.168.11.13:3000` | admin / SOPS 管理（`group_vars/monitoring/secrets.sops.yml`） |

### Reverse Proxy（vm-infra 上で実行）

```bash
cd reverse-proxy
docker compose up -d
```

## ネットワーク方針

- 各 Compose プロジェクトは独自の bridge ネットワークを作成
- VM 間の通信はホストネットワーク（192.168.11.0/24）経由
- Prometheus は各 VM の node_exporter（`:9100`）に直接アクセス
- Reverse Proxy は各サービスの公開ポートに直接アクセス

## 環境変数

機密値は SOPS で暗号化した `ansible/inventory/group_vars/<group>/secrets.sops.yml` で管理する。
`.env` はリポジトリに置かず、Ansible が `ansible/playbooks/templates/*.env.j2` から生成して VM 上の `/opt/<stack>/.env` に配置する（`docs/operations/runbooks/secrets.md` 参照）。

## Reverse Proxy のデプロイ方式について

Caddy は Docker Compose（本ディレクトリの `reverse-proxy/`）としてのみ運用する。
`ansible/playbooks/infra.yml` がこのディレクトリの `docker-compose.yml` / `Caddyfile` を
`vm-infra` の `/opt/reverse-proxy` にコピーし、コンテナを起動する。
Ansible role としての Caddy ネイティブインストールはかつて存在したが未使用のため削除済み。
