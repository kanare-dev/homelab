# DNS 構成

## 概要

vm-infra (192.168.11.11) 上で3層の DNS スタックを運用する。

```text
client
  └─► AdGuard Home  0.0.0.0:53             ← フィルタリング・クエリログ・WebUI
         ├─► CoreDNS  127.0.0.1:5353       ← lab.kanare.dev 権威 DNS
         └─► Unbound  127.0.0.1:5335       ← 外部フル再帰解決
```

| サービス | 役割 | バインドアドレス | 実装 |
|---|---|---|---|
| AdGuard Home | フロントエンド・フィルタリング | 0.0.0.0:53, :3000 | Docker (host network) |
| CoreDNS | lab.kanare.dev 権威 DNS | 127.0.0.1:5353 | systemd |
| Unbound | 外部フル再帰解決 | 127.0.0.1:5335 | Docker (host network) |

## 各サービスの詳細

### AdGuard Home

- クライアントからの DNS クエリをすべて受け付ける（port 53）
- 広告・トラッカードメインをブロックリストでフィルタリング
- クエリログ・統計を Web UI (`:3000`) で可視化
- upstream の振り分けルール:
  - `lab.kanare.dev` → CoreDNS (127.0.0.1:5353)
  - それ以外 → Unbound (127.0.0.1:5335)
- Web UI: http://192.168.11.11:3000 / https://adguard.lab.kanare.dev
- 設定ファイル: `/opt/dns/adguard/conf/AdGuardHome.yaml`

### CoreDNS

- `lab.kanare.dev` ゾーンのみを管理する権威 DNS
- ループバック (`127.0.0.1`) のみリッスンし、外部から直接アクセス不可
- ゾーンファイル: `/etc/coredns/lab.kanare.dev.zone`
- Corefile: `/etc/coredns/Corefile`

### Unbound

- ルートヒント (`root.hints`) からフル再帰解決を行う
- 1.1.1.1 / 8.8.8.8 などの外部リゾルバに依存しない
- DNSSEC 検証・プライバシー強化設定を有効化
- ループバック (`127.0.0.1`) のみリッスンし、外部から直接アクセス不可
- 設定ファイル: `/opt/dns/unbound/unbound.conf`

## DNS レコード (lab.kanare.dev)

| ホスト名 | IP | 備考 |
|---|---|---|
| `grafana` | 192.168.11.11 | Caddy 経由 |
| `prometheus` | 192.168.11.11 | Caddy 経由 |
| `pve` | 192.168.11.11 | Caddy 経由 |
| `infra` | 192.168.11.11 | vm-infra |
| `vm-infra` | 192.168.11.11 | vm-infra |
| `vm-monitoring` | 192.168.11.13 | vm-monitoring |
| `home` | 192.168.11.11 | Caddy 経由 |
| `vm-apps` | 192.168.11.20 | vm-apps |
| `adguard` | 192.168.11.11 | Caddy 経由 |

レコードの追加・変更は `ansible/inventory/group_vars/infra/vars.yml` の `dns_records` を編集し、`ansible-playbook playbooks/infra.yml` を実行する。

## ファイル構成

```text
ansible/
├── roles/coredns/
│   ├── templates/
│   │   ├── Corefile.j2          # CoreDNS 設定テンプレート
│   │   └── zone.j2              # ゾーンファイルテンプレート
│   ├── defaults/main.yml        # デフォルト変数 (listen_port: 5353)
│   └── tasks/main.yml           # インストール・設定タスク
├── inventory/group_vars/infra/
│   └── vars.yml                 # dns_records, coredns_listen_* を定義
└── playbooks/infra.yml          # DNS スタックのデプロイ・AdGuard upstream 設定

docker/compose/dns/
├── docker-compose.yml           # AdGuard Home + Unbound
├── adguard/conf/                # AdGuardHome.yaml (サーバー上で管理)
└── unbound/
    ├── unbound.conf             # Unbound 設定
    └── root.hints               # ルートヒント (IANA)
```

## 運用手順

### DNS レコードを追加する

1. `ansible/inventory/group_vars/infra/vars.yml` の `dns_records` に追記
2. `ansible-playbook playbooks/infra.yml` を実行
3. CoreDNS が自動再起動され、新レコードが反映される

### 動作確認

```bash
# CoreDNS を直接確認（AdGuard を経由しない）
dig @127.0.0.1 -p 5353 grafana.lab.kanare.dev

# Unbound を直接確認
dig @127.0.0.1 -p 5335 example.com

# AdGuard 経由で内部ドメイン解決
dig @192.168.11.11 grafana.lab.kanare.dev

# AdGuard 経由で外部ドメイン解決
dig @192.168.11.11 example.com
```

### AdGuard のキャッシュをクリアする

Web UI: **設定 → DNS 設定 → DNS キャッシュの設定 → キャッシュをクリア**

または:

```bash
ssh vm-infra "docker restart adguardhome"
```

### root.hints を更新する

Unbound が使うルートヒントは定期的に更新が推奨される。

```bash
INTERNIC_IP=$(dig +short A www.internic.net @8.8.8.8 | tail -1)
curl --resolve "www.internic.net:443:${INTERNIC_IP}" \
  -sSo docker/compose/dns/unbound/root.hints \
  https://www.internic.net/domain/named.root
# ansible-playbook で反映
ansible-playbook playbooks/infra.yml
```

## Tailscale との連携

Tailscale 経由でリモートアクセスする場合、`lab.kanare.dev` の名前解決を vm-infra に向ける必要がある。

Tailscale Admin Console → DNS → **Add nameserver** で以下を設定:
- Nameserver: vm-infra の Tailscale IP
- Restrict to domain: `lab.kanare.dev`

これにより VPN 接続中も `grafana.lab.kanare.dev` などの内部ドメインが解決される。
