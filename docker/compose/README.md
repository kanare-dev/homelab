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
└── reverse-proxy/           # vm-infra 上で実行（または Ansible の caddy role を使用）
    ├── docker-compose.yml
    └── Caddyfile
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

| サービス | URL | デフォルト認証 |
|---|---|---|
| Prometheus | `http://192.168.11.13:9090` | なし |
| Grafana | `http://192.168.11.13:3000` | admin / changeme |

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

## 注意: Reverse Proxy の二重管理について

Caddy は以下の 2 通りの方法でデプロイできる:

1. **Ansible の `caddy` role**（推奨） — VM にネイティブインストール
2. **Docker Compose** — コンテナとして実行

本リポジトリでは Ansible role を推奨する。Docker Compose 版は参考実装として配置している。
両方を同時に使用しないこと。
