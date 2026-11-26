# DNS 構成

## 概要

vm-infra（10.77.20.10）の上で、3 層の DNS スタックを運用している。3 層にした理由と、他の候補との比較は、[ADR 0020](../../../adr/0020-dns-three-layer-stack.md) に書いている。

```text
client
  └─► AdGuard Home  0.0.0.0:53             ← フィルタリング・クエリログ・WebUI
         ├─► CoreDNS  127.0.0.1:5353       ← lab.kanare.dev 権威 DNS
         └─► Unbound  127.0.0.1:5335       ← 外部フル再帰解決
```

| サービス | 役割 | バインドアドレス | 実装 |
| --- | --- | --- | --- |
| AdGuard Home | フロントエンド・フィルタリング | 0.0.0.0:53, :3000 | Docker (host network) |
| CoreDNS | lab.kanare.dev 権威 DNS | 127.0.0.1:5353 | systemd |
| Unbound | 外部フル再帰解決 | 127.0.0.1:5335 | Docker (host network) |

## 各サービスの詳細

### AdGuard Home

AdGuard Home は、クライアントからの DNS クエリをすべて受け付ける（port 53）。広告とトラッカーのドメインは、ブロックリストを使ってフィルタリングする。クエリログと統計は、Web UI（`:3000`）で見られる。

クエリの転送先（upstream）は、名前によって振り分ける。`lab.kanare.dev` は CoreDNS（127.0.0.1:5353）に、それ以外は Unbound（127.0.0.1:5335）に転送する。

- Web UI: <http://10.77.20.10:3000> と <https://adguard.lab.kanare.dev>
- 設定ファイル: `/opt/dns/adguard/conf/AdGuardHome.yaml`
- fallback DNS: `1.1.1.1` と `9.9.9.9`。upstream（CoreDNS と Unbound）がすべて失敗したときだけ使う。2026-10-22 に、Unbound が約 3 分間応答せず、インターネット全体の名前解決が止まったので、追加した（`playbooks/infra.yml` で設定している）。

### CoreDNS

CoreDNS は、`lab.kanare.dev` ゾーンだけを管理する権威 DNS である。ループバック（`127.0.0.1`）でだけ待ち受けるので、外部から直接アクセスすることはできない。

- ゾーンファイル: `/etc/coredns/lab.kanare.dev.zone`
- Corefile: `/etc/coredns/Corefile`

### Unbound

Unbound は、ルートヒント（`root.hints`）から、フルの再帰解決を行う。1.1.1.1 や 8.8.8.8 のような外部のリゾルバには依存しない。DNSSEC の検証と、プライバシーを強化する設定も有効にしてある。CoreDNS と同じく、ループバック（`127.0.0.1`）でだけ待ち受けるので、外部から直接アクセスすることはできない。

設定ファイルは `/opt/dns/unbound/unbound.conf` で、主な設定は次のとおりである。

- `serve-expired: yes`（TTL 1 時間）: 上流が応答しないときに、期限切れのキャッシュを返す。
- `use-syslog: no`、`verbosity: 1`、`log-servfail: yes`: 失敗を `docker logs unbound` に残す（ログは、docker のログの上限で循環する）。`use-syslog: no` を指定しないと、コンテナ内に syslog がないため、ログが出ない。
- `do-ip6: no`: vm-infra には IPv6 の経路がない。有効にすると、権威サーバーの IPv6 アドレスへ、届かない送信を繰り返して、`max-sends` の上限を使い切ってしまう。その結果、`SERVFAIL`（`exceeded the maximum number of sends`）や、20 秒のタイムアウトが起きる。

### fallback DNS の限界

AdGuard の fallback DNS が使われるのは、upstream に**接続できない**とき（タイムアウトなど）だけ。Unbound が `SERVFAIL` を返した場合は、その応答がそのまま利用者に返り、fallback は働かない。Unbound の失敗は `UnboundProbeFailing`（[monitoring.md](../platform/monitoring.md)）で検知する。

## DNS レコード (lab.kanare.dev)

| ホスト名 | IP | 備考 |
| --- | --- | --- |
| `grafana` | 10.77.20.10 | Caddy 経由 |
| `prometheus` | 10.77.20.10 | Caddy 経由 |
| `alertmanager` | 10.77.20.10 | Caddy 経由 |
| `pve` | 10.77.20.10 | Caddy 経由（Proxmox の管理画面。ホスト名ではなくサービス名） |
| `pve01` | 10.77.10.10 | Proxmox ホストへの直接の接続（SSH 用）。2026-11-24 から |
| `infra` | 10.77.20.10 | vm-infra |
| `vm-infra` | 10.77.20.10 | vm-infra |
| `vm-monitoring` | 10.77.20.11 | vm-monitoring |
| `home` | 10.77.20.10 | Caddy 経由 |
| `vm-apps` | 10.77.20.20 | vm-apps |
| `ha` | 10.77.20.10 | Caddy 経由（Home Assistant） |
| `n8n` | 10.77.20.10 | Caddy 経由（n8n） |
| `rss` | 10.77.20.10 | Caddy 経由（FreshRSS） |
| `adguard` | 10.77.20.10 | Caddy 経由 |
| `code` | 10.77.20.10 | Caddy 経由（code-server） |
| `cloudcli` | 10.77.20.10 | Caddy 経由（CloudCLI） |
| `vm-code` | 10.77.20.30 | vm-code（SSH / mosh の直接アクセス用） |
| `omada` | 10.77.20.10 | Caddy 経由（Omada コントローラーの管理画面。[管理画面](#管理画面omada-コントローラー)）。旧 `router` は廃止 |
| `rtr01` | 10.77.10.1 | ER605（ルーター）。直接 |
| `sw01` | 10.77.10.2 | SG2210P（スイッチ）。直接 |
| `vm-omada` | 10.77.10.3 | vm-omada。直接（管理画面は `omada` で開く） |
| `ap01` | 10.77.30.50 | Buffalo（AP モード）。直接 |
| `vm-dev` | 10.77.40.10 | vm-dev。直接（手動起動。止まっている間は繋がらない） |

レコードの追加・変更は `ansible/inventory/group_vars/infra/vars.yml` の `dns_records` を編集し、`ansible-playbook playbooks/infra.yml` を実行する。

固定 IP を持つホストには、すべて `<ホスト名>.lab.kanare.dev` の A レコードを付け、そのホストを直接指す（[ADR-0036](../../../adr/0036-a-record-for-every-fixed-ip-host.md)）。新しいホストを足すときも、同じ変更でレコードを足す。ただし、名前を引くのは `vm-infra` なので、`vm-infra` が止まると名前は引けない。監視の対象（Prometheus、blackbox-exporter）と、緊急時の手順書は、IP で書く。

`.dev` のドメインは、ブラウザに HSTS preload として登録されていて、`http://` で開いても `https://` に書き換えられる。HTTPS に応答しない機器（Buffalo の管理画面は HTTP だけ）は、ホスト名ではブラウザで開けないので、管理画面は IP で開く（例: `http://10.77.30.50`）。ホスト名は、`ssh`、`ping` など、ブラウザ以外の用途に使う。

## Cloudflare 上のレコード

公開ドメイン `kanare.dev` のゾーンは Cloudflare で管理している。`lab.kanare.dev` の内部名は Cloudflare には置かず、CoreDNS だけが持つ（LAN と Tailscale の Split DNS からのみ引ける）。

| 項目 | 内容 |
| --- | --- |
| ゾーン | `kanare.dev`（Cloudflare DNS） |
| 用途 | Caddy が Let's Encrypt の DNS-01 チャレンジで、`_acme-challenge` の TXT を一時的に作成・削除する（[リバースプロキシと TLS](reverse-proxy-tls.md)） |
| 認証 | API トークン `cloudflare_api_token`（SOPS 管理。[シークレット](../../../operations/runbooks/03-secrets.md)） |
| 管理方法 | ダッシュボードで手動管理。Terraform などのコードにはしていない |
| 常設レコード | このリポジトリには一覧を持たない。`kanare.dev` 本体のレコードは、Cloudflare のダッシュボードが正 |

## VM のホスト DNS

全 VM のホスト DNS は、AdGuard ではなくルーター（各 VLAN のゲートウェイ。Servers は `10.77.20.1`、Lab は `10.77.40.1`）を指している。そのため VM 内のホストから `*.lab.kanare.dev` は引けない。AdGuard の障害時にも、Slack 通知・apt・`docker pull` が使えるようにするため。判断の記録: [ADR 0007](../../../adr/0007-vm-host-dns-is-router.md)。

AdGuard を使いたいコンテナは `docker-compose.yml` の `dns:` で個別に指定する（例: blackbox-exporter、n8n、FreshRSS）。

## 管理画面（Omada コントローラー）

`https://omada.lab.kanare.dev` で、Omada コントローラー（ER605・SG2210P の管理画面）を開ける。`omada` の DNS レコードは `vm-omada` ではなく Caddy（vm-infra）を指す。

```text
ブラウザ ─► omada.lab.kanare.dev (10.77.20.10, Caddy が HTTPS で受ける)
              └─► Caddy ─► https://10.77.10.3:8043 (vm-omada、HTTPS。自己署名証明書)
```

- 以前は `router.lab.kanare.dev` が Buffalo の管理画面を向いていた。ER605 をコントローラーに採用すると、本体の画面が使えなくなるため、2026-11-06 に `omada.lab.kanare.dev` に付け替え、`router` は廃止した（決定: 運用者）。
- Caddy から `vm-omada` までは HTTPS。自己署名証明書のため、`tls_insecure_skip_verify` を付ける（`pve` と同じ形）。`vm-omada` の UFW は、8043 を Caddy（`vm-infra`）から許可している（`ansible/inventory/group_vars/omada/vars.yml`）。
- Buffalo（AP モード）の画面は、`http://10.77.30.50` を直接開く（Caddy は通さない）。
- Homepage の Omada タイルは `https://omada.lab.kanare.dev` を監視している。
- 外出先（Tailscale）からも名前を引ける。Tailscale の subnet route が `10.77.20.0/24`、`10.77.40.0/24` を通すため、Servers・Lab の IP にも届く。Management には届かない。

### ルーターを付け替えるとき

IP が変わる場合、直す場所は次のとおり。`dns_records` の `omada`（Caddy を指す）と Homepage のリンクは変えない。

| 場所 | 内容 |
| --- | --- |
| `docker/compose/reverse-proxy/Caddyfile` | `omada.lab.kanare.dev` の `reverse_proxy` の転送先（`vm-omada` の IP） |
| `terraform/proxmox/terraform.tfvars` | VM ごとの `gateway`・`nameserver`（DNS 障害時に経路が壊れないよう、名前ではなく IP のまま） |
| `README.md` | ルーターの IP（構成表） |
| `docker/compose/homepage/config/services.yaml` | Omada の `description` |

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

1. `ansible/inventory/group_vars/infra/vars.yml` の `dns_records` に、レコードを追記する。
2. `ansible-playbook playbooks/infra.yml` を実行する。
3. CoreDNS が自動で再起動され、新しいレコードが反映される。

### 動作確認

```bash
# CoreDNS を直接確認（AdGuard を経由しない）
dig @127.0.0.1 -p 5353 grafana.lab.kanare.dev

# Unbound を直接確認
dig @127.0.0.1 -p 5335 example.com

# AdGuard 経由で内部ドメイン解決
dig @10.77.20.10 grafana.lab.kanare.dev

# AdGuard 経由で外部ドメイン解決
dig @10.77.20.10 example.com
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
| --- | --- |
| vm-infra の Tailscale IP | `100.118.14.37` |
| 起動オプション | `tailscale up --advertise-routes=10.77.20.0/24,10.77.40.0/24 --accept-dns=false` |
| Subnet route | Admin Console で `10.77.20.0/24`、`10.77.40.0/24` を承認済み |
| Key expiry | vm-infra は無効化（期限切れで外出先から繋がらなくなるのを防ぐ） |
| Split DNS | Admin Console → DNS → Nameserver `100.118.14.37`、Restrict to domain `lab.kanare.dev` |

- `--accept-dns=false`: vm-infra 自身が AdGuard を DNS として使うため、Tailscale に resolv.conf を書き換えさせない。
- IP 転送 (`net.ipv4.ip_forward = 1`) は有効化済み。
- スマホは Tailscale をオンにしたまま、自宅 Wi-Fi でもモバイル回線でも `https://home.lab.kanare.dev` に接続できる。

### 注意

- Tailscale がオンの間、iOS は Wi-Fi の DNS ではなく Tailscale の DNS 設定を使う。Split DNS が無いと `lab.kanare.dev` は NXDOMAIN になる。
- スマホの DNS に `1.1.1.1` を併記しない。`lab.kanare.dev` を知らないため、NXDOMAIN を返して名前解決が失敗することがある。
- Caddy は 443 番ポートのみで待ち受ける。`http://` では接続できないので `https://` を使う。
