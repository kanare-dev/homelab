# Docker Compose — サービス定義

各 VM 上で動作するサービスを Docker Compose で定義する。

## ディレクトリ構成

```
docker/compose/
├── README.md
├── monitoring/              # vm-monitoring 上で実行
│   ├── docker-compose.yml
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       └── provisioning/
│           └── datasources/
│               └── prometheus.yml
├── reverse-proxy/           # vm-infra 上で実行（Ansible の infra.yml がデプロイ）
│   ├── docker-compose.yml
│   └── Caddyfile
├── dns/                     # vm-infra 上で実行: AdGuard Home + Unbound（Ansible の infra.yml がデプロイ）
│   └── docker-compose.yml
└── homepage/                # vm-apps 上で実行（Ansible の apps.yml がデプロイ）
    ├── docker-compose.yml
    └── config/
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
|---|---|---|
| Prometheus | `http://192.168.11.13:9090` | なし |
| Grafana | `http://192.168.11.13:3000` | admin / Ansible Vault 管理（`group_vars/monitoring/vault.yml`） |

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

機密値は `.env` ファイルで管理する（Git には含めない）:

```bash
cp .env.example .env
# .env を編集
```

## Reverse Proxy のデプロイ方式について

Caddy は Docker Compose（本ディレクトリの `reverse-proxy/`）としてのみ運用する。
`ansible/playbooks/infra.yml` がこのディレクトリの `docker-compose.yml` / `Caddyfile` を
`vm-infra` の `/opt/reverse-proxy` にコピーし、コンテナを起動する。
Ansible role としての Caddy ネイティブインストールはかつて存在したが未使用のため削除済み。
