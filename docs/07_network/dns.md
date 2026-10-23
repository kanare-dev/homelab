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
- fallback DNS: `1.1.1.1` / `9.9.9.9`。upstream（CoreDNS・Unbound）が全て失敗したときだけ使う。2026-10-22 に Unbound が約 3 分間応答せず、インターネット全体の名前解決が止まったため追加（`playbooks/infra.yml` で設定）

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
- `serve-expired: yes`（TTL 1 時間）: 上流が応答しないとき、期限切れのキャッシュを返す
- `use-syslog: no` / `verbosity: 1` / `log-servfail: yes`: 失敗を `docker logs unbound` に残す（ログは docker のログ上限で回る）。`use-syslog: no` が無いと、コンテナ内に syslog が無いためログが出ない
- `do-ip6: no`: vm-infra には IPv6 の経路がない。有効だと、権威サーバーの IPv6 アドレスへの到達不能な送信が `max-sends` の上限を使い切り、`SERVFAIL`（`exceeded the maximum number of sends`）や 20 秒のタイムアウトになる

### fallback DNS の限界

AdGuard の fallback DNS が使われるのは、upstream に**接続できない**とき（タイムアウトなど）だけ。Unbound が `SERVFAIL` を返した場合は、その応答がそのまま利用者に返り、fallback は働かない。Unbound の失敗は `UnboundProbeFailing`（[monitoring.md](../05_operations-maintainability/monitoring.md)）で検知する。

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
| `code` | 192.168.11.11 | Caddy 経由（code-server） |
| `cloudcli` | 192.168.11.11 | Caddy 経由（CloudCLI） |
| `router` | 192.168.11.11 | Caddy 経由（ルーター管理画面）。ルーター本体は `192.168.11.1`（[ルーター管理画面](#ルーター管理画面)） |

レコードの追加・変更は `ansible/inventory/group_vars/infra/vars.yml` の `dns_records` を編集し、`ansible-playbook playbooks/infra.yml` を実行する。

## ルーター管理画面

`https://router.lab.kanare.dev` でルーターの設定画面を開ける。`router` の DNS レコードはルーター本体ではなく Caddy（vm-infra）を指す。

```text
ブラウザ ─► router.lab.kanare.dev (192.168.11.11, Caddy が HTTPS で受ける)
              └─► Caddy ─► 192.168.11.1:80 (ルーター本体、HTTP)
```

- `.dev` は TLD ごと HSTS プリロードされており、ブラウザは `http://` を `https://` に書き換える。ルーターは 443 で待ち受けないため、DNS を直接ルーターに向けるとブラウザから開けない。Caddy で HTTPS 化している。
- Caddy からルーターまでの通信は平文の HTTP（LAN 内のみ）。
- IP 直打ちの `http://192.168.11.1` でも開ける。
- Homepage の Router タイルは `https://router.lab.kanare.dev` を監視している。
- 外出先（Tailscale）からも名前を引ける。Tailscale の subnet route が `192.168.11.0/24` を通すため、ルーターの IP にも届く。遮断するには Tailscale の ACL で `192.168.11.1` を除外する（未実施）。

### ルーターを付け替えるとき

IP が変わる場合、直す場所は次のとおり。`dns_records` の `router`（Caddy を指す）と Homepage のリンクは変えない。

| 場所 | 内容 |
|---|---|
| `docker/compose/reverse-proxy/Caddyfile` | `router.lab.kanare.dev` の `reverse_proxy` の転送先 |
| `ansible/inventory/group_vars/all.yml` | `gateway`（DNS 障害時に経路が壊れないよう、名前ではなく IP のまま） |
| `terraform/proxmox/variables.tf` / `terraform.tfvars` | `gateway` |
| `README.md` | ルーターの IP（構成表・管理画面リンク） |
| `docker/compose/homepage/config/services.yaml` | Router の `description`（機種名） |

Caddyfile を直したら `ansible-playbook playbooks/infra.yml` で反映する。ルーター側が HTTPS 専用になった場合は、転送先を `https://...` にして `tls_insecure_skip_verify` を付ける（`pve` と同じ形）。

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

外出先から `lab.kanare.dev` と LAN のサービスを使うため、vm-infra を subnet router にし、split DNS を設定している（2026-10-22 に動作確認済み）。

| 項目 | 設定 |
|---|---|
| vm-infra の Tailscale IP | `100.118.14.37` |
| 起動オプション | `tailscale up --advertise-routes=192.168.11.0/24 --accept-dns=false` |
| Subnet route | Admin Console で `192.168.11.0/24` を承認済み |
| Key expiry | vm-infra は無効化（期限切れで外出先から繋がらなくなるのを防ぐ） |
| Split DNS | Admin Console → DNS → Nameserver `100.118.14.37`、Restrict to domain `lab.kanare.dev` |

- `--accept-dns=false`: vm-infra 自身が AdGuard を DNS として使うため、Tailscale に resolv.conf を書き換えさせない。
- IP 転送 (`net.ipv4.ip_forward = 1`) は有効化済み。
- スマホは Tailscale をオンにしたまま、自宅 Wi-Fi でもモバイル回線でも `https://home.lab.kanare.dev` に接続できる。

### 注意

- Tailscale がオンの間、iOS は Wi-Fi の DNS ではなく Tailscale の DNS 設定を使う。Split DNS が無いと `lab.kanare.dev` は NXDOMAIN になる。
- スマホの DNS に `1.1.1.1` を併記しない。`lab.kanare.dev` を知らないため、NXDOMAIN を返して名前解決が失敗することがある。
- Caddy は 443 番ポートのみで待ち受ける。`http://` では接続できないので `https://` を使う。
