# homelab

Proxmox 上に複数 VM を構築し、IaC（Terraform + Ansible）と Docker Compose で再現可能に運用する homelab リポジトリ。

## 技術スタック

| レイヤ | 採用技術 | 用途 |
|---|---|---|
| ハイパーバイザ | Proxmox VE | VM の作成・実行・管理 |
| IaC | Terraform | Proxmox 上の VM プロビジョニング |
| 構成管理 | Ansible | OS 初期設定、Docker、node_exporter、監視基盤のデプロイ |
| コンテナ実行 | Docker Compose | Prometheus、Grafana、リバースプロキシの起動 |
| 監視 | Prometheus, Grafana, node_exporter | VM / ホスト / IoT デバイスのメトリクス収集と可視化 |
| ネットワーク | CoreDNS, Caddy, WireGuard | 内部 DNS、リバースプロキシ、VPN |
| IoT | ESP32, BME280, Prometheus metrics | 温湿度・気圧の収集と公開 |
| 秘密情報管理 | SOPS + age, Ansible Vault | 機密情報の暗号化と運用 |

## 思想

- **再現可能性** — すべての構成をコードで管理し、いつでも同じ環境を再構築できる
- **最小構成から育てる** — 初期は雛形として使い、実運用に合わせて段階的に拡張する
- **ドキュメント駆動** — このリポジトリを読めば全体像・IP 設計・セットアップ手順・運用方法が分かる
- **観測可能性** — Prometheus + Grafana で全 VM・サービスの状態を可視化する

## ハードウェア

| 機器 | モデル | スペック | IP | 備考 |
|---|---|---|---|---|
| ルーター | Buffalo WSR-1800AX4P | — | `192.168.11.1` | Wi-Fi 6 対応 |
| サーバー | Lenovo ThinkCentre M70q Tiny | i5-10400T / 8GB RAM / 256GB NVMe | `192.168.11.10` | Proxmox VE ホスト。メモリ増設予定 |
| IoT | ESP32 | — | `192.168.11.100` | — |

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────┐
│  LAN: 192.168.11.0/24          GW: 192.168.11.1         │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  vm-infra    │  │ vm-monitoring│  │  vm-apps     │   │
│  │  .11         │  │  .13         │  │  .20         │   │
│  │  CoreDNS     │  │  Prometheus  │  │  app services│   │
│  │  Caddy       │  │  Grafana     │  │              │   │
│  │  WireGuard   │  │  exporters   │  │              │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │           │
│  ┌──────┴─────────────────┴─────────────────┴────────┐  │
│  │              Proxmox VE (.10)                     │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │  vm-dev      │  │  IoT devices │                     │
│  │  .21         │  │  .100~       │                     │
│  │  playground  │  │  ESP32 etc.  │                     │
│  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## 管理画面リンク

| サービス | URL | 備考 |
|---|---|---|
| ルーター | [http://192.168.11.1](http://192.168.11.1) | ルーター設定画面 |
| Proxmox | [https://192.168.11.10:8006](https://192.168.11.10:8006) | Proxmox VE 管理画面 |
| Grafana | [http://192.168.11.13:3000](http://192.168.11.13:3000) | 監視ダッシュボード |
| Prometheus | [http://192.168.11.13:9090](http://192.168.11.13:9090) | メトリクス確認 |
| ESP32 | [http://192.168.11.100](http://192.168.11.100) | ESP32 出力画面 |

## IP アドレス規約

| 範囲 | 用途 | 例 |
|---|---|---|
| `192.168.11.1` | ルーター / ゲートウェイ | — |
| `192.168.11.10–19` | インフラ（Proxmox, VM） | `.10` Proxmox, `.11` vm-infra, `.13` vm-monitoring |
| `192.168.11.20–59` | サーバー / VM | `.20` vm-apps, `.21` vm-dev |
| `192.168.11.60–99` | DHCP プール | 動的割当 |
| `192.168.11.100–149` | IoT デバイス | `.100` 01-esp32 |
| `192.168.11.150–254` | 予約 / 実験用 | — |

## VM 一覧

| 名前 | VMID | IP | 役割 | 主なサービス | 依存関係 |
| --- | --- | --- | --- | --- | --- |
| Proxmox | — | `192.168.11.10` | ハイパーバイザ | Proxmox VE | — |
| vm-infra | `111` | `192.168.11.11` | インフラ基盤 | CoreDNS, Caddy, WireGuard | Proxmox |
| vm-monitoring | `113` | `192.168.11.13` | 監視 | Prometheus, Grafana, node_exporter | Proxmox, vm-infra (DNS) |
| vm-apps | `120` | `192.168.11.20` | アプリケーション | 各種サービス | Proxmox, vm-infra |
| vm-dev | `121` | `192.168.11.21` | 開発・実験 | playground | Proxmox, vm-infra |

## 推奨アーキテクチャ: Plan B（VM 分割ベース）

本リポジトリでは **Plan B（VM 分割ベース）** を推奨する。

### 推奨理由

| 観点 | 説明 |
|---|---|
| 責務分離 | VM ごとに役割が明確。infra / monitoring / apps / dev の境界が分かりやすい |
| セキュリティ | VM レベルで障害隔離・ネットワーク分離が可能 |
| 運用 | 1 つの VM を再起動・更新しても他に影響しない |
| 拡張性 | 新しい役割が必要になったら VM を追加するだけ |
| 学習効果 | 実務のマイクロサービス / マルチサーバー構成に近い |

### 代替案: Plan A（役割ベース）

Plan A は VM 数を最小化し、1 つの edge VM に DNS・VPN・reverse proxy をまとめ、1 つの services VM に監視・アプリをまとめる構成。

| VM | IP | 内容 |
|---|---|---|
| Proxmox | `.10` | ハイパーバイザ |
| edge | `.11` | VPN + reverse proxy + DNS |
| services | `.20` | Grafana + Prometheus + 他 |

**Plan A が適するケース**: リソースが限られている（RAM 16GB 以下）、VM 管理のオーバーヘッドを減らしたい場合。Plan A から始めて Plan B に移行するのも良い。

## DNS 方針

### 推奨: CoreDNS

- 軽量で設定がシンプル
- Corefile ベースで IaC との相性が良い
- Kubernetes でも標準採用されており学習価値が高い

代替: dnsmasq（さらに軽量）、AdGuard Home（広告ブロック付き）

### ドメイン命名規約

内部 DNS に `lab.kanare.dev` ゾーンを使用する。

| FQDN | IP | 用途 |
|---|---|---|
| `pve.lab.kanare.dev` | `192.168.11.10` | Proxmox Web UI |
| `infra.lab.kanare.dev` | `192.168.11.11` | インフラ VM |
| `grafana.lab.kanare.dev` | `192.168.11.13` | Grafana（reverse proxy 経由） |
| `prometheus.lab.kanare.dev` | `192.168.11.13` | Prometheus（reverse proxy 経由） |
| `apps.lab.kanare.dev` | `192.168.11.20` | アプリケーション VM |
| `dev.lab.kanare.dev` | `192.168.11.21` | 開発 VM |

> [!TIP]
> Split DNS を使えば、外部からは `kanare.dev` の公開レコード、LAN 内では `lab.kanare.dev` の内部レコードを返すように使い分けられる。

## Reverse Proxy 方針

### 推奨: Caddy

| 観点 | 理由 |
|---|---|
| 自動 HTTPS | Let's Encrypt / 内部 CA による自動証明書管理 |
| 設定の簡潔さ | Caddyfile は数行で reverse proxy を定義できる |
| パフォーマンス | Go 製で十分高速 |
| homelab 向き | LAN 内でも自己署名証明書を自動生成し TLS を有効化できる |

代替: Traefik（Docker ラベル連携が強力）、Nginx（実績豊富だが設定が冗長）

## Monitoring 方針

### Prometheus + Grafana

- **Prometheus**: 各 VM の node_exporter および IoT デバイスからメトリクスを pull 方式で収集
- **Grafana**: ダッシュボードで可視化（Node Exporter Full ダッシュボードを推奨）
- **node_exporter**: 全 VM に Ansible role でデプロイ
- **ESP32**: Prometheus 形式でセンサデータを export（`/metrics` エンドポイント）
- **alertmanager**: 将来的に追加（Slack / Discord 通知）

```
┌─ vm-monitoring ─────────────────────────────────┐
│                                                 │
│  Prometheus ──scrape──▶ node_exporter (各VM)    │
│      │       ──scrape──▶ ESP32 (IoT sensors)    │
│      ▼                                          │
│  Grafana (dashboard)                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

## リポジトリ構成

```
homelab/
├── README.md
├── LICENSE
├── Makefile
├── .gitignore
├── .env.example
├── .sops.yaml
├── terraform/
│   └── proxmox/
│       ├── README.md
│       ├── versions.tf
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       ├── terraform.tfvars.example
│       └── modules/
│           └── vm/
│               ├── main.tf
│               ├── variables.tf
│               └── outputs.tf
├── ansible/
│   ├── README.md
│   ├── ansible.cfg
│   ├── inventory/
│   │   ├── hosts.yml
│   │   ├── group_vars/
│   │   │   ├── all.yml
│   │   │   ├── infra.yml
│   │   │   └── monitoring.yml
│   │   └── host_vars/
│   │       ├── vm-infra.yml
│   │       └── vm-monitoring.yml
│   ├── roles/
│   │   ├── common/
│   │   ├── docker/
│   │   ├── node_exporter/
│   │   ├── caddy/
│   │   └── coredns/
│   └── playbooks/
│       ├── site.yml
│       ├── infra.yml
│       ├── monitoring.yml
│       └── apps.yml
├── docker/
│   └── compose/
│       ├── README.md
│       ├── monitoring/
│       │   ├── docker-compose.yml
│       │   └── prometheus/
│       │       └── prometheus.yml
│       └── reverse-proxy/
│           ├── docker-compose.yml
│           └── Caddyfile
├── diagrams/
│   └── architecture.drawio
└── docs/
    ├── runbook.md
    └── day0-day1-day2.md
```

## Quick Start

### 前提条件

- [Terraform](https://www.terraform.io/) >= 1.5
- [Ansible](https://docs.ansible.com/) >= 2.15
- [Docker](https://docs.docker.com/) + Docker Compose
- Proxmox VE 8.x が `192.168.11.10` で稼働済み

> [!IMPORTANT]
> Terraform の Proxmox provider には API トークンが必要。`terraform/proxmox/README.md` の手順に従い、事前に Proxmox 側でトークンを発行すること。

### 1. リポジトリをクローン

```bash
git clone https://github.com/<your-user>/homelab.git
cd homelab
```

### 2. VM をプロビジョニング（Terraform）

```bash
cd terraform/proxmox
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars を編集して実際の値を設定
make plan   # 差分確認
make apply  # VM 作成
```

### 3. VM を構成（Ansible）

```bash
cd ansible
# inventory/hosts.yml を環境に合わせて編集
make setup  # 全 VM の初期セットアップ
```

### 4. サービス起動（Docker Compose）

```bash
# monitoring VM 上で
cd docker/compose/monitoring
docker compose up -d

# infra VM 上で
cd docker/compose/reverse-proxy
docker compose up -d
```

詳細な手順は `docs/day0-day1-day2.md` を参照。

## セキュリティ

- **秘密情報は Git に入れない** — `.env`, `terraform.tfvars`, Ansible Vault ファイルは `.gitignore` で除外
- **SOPS + age** を推奨 — 暗号化した状態で Git 管理可能（`.sops.yaml` 参照）
- **Ansible Vault** — `ansible-vault encrypt` で変数ファイルを暗号化
- **LAN 内 TLS** — Caddy の内部 CA 機能でローカル証明書を自動発行
- **SSH 鍵認証のみ** — パスワード認証は無効化（`common` role で設定）
- **ファイアウォール** — `ufw` を各 VM で有効化し、必要なポートのみ開放
