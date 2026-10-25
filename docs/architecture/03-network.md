# ネットワーク設計

アドレス・命名規約と、外部との接続をまとめる。個別のサービスは [DNS 構成](../services/dns.md)、[リバースプロキシと TLS](../services/reverse-proxy-tls.md)。次期構成は [VLAN 設計](08-vlan-design.md)（未適用）。

## IP アドレス規約（`192.168.11.0/24`）

| 範囲 | 用途 | 例 |
| --- | --- | --- |
| `192.168.11.1` | ルーター / ゲートウェイ | — |
| `192.168.11.10–19` | インフラ（Proxmox、基盤 VM） | `.10` Proxmox、`.11` `vm-infra`、`.13` `vm-monitoring` |
| `192.168.11.20–59` | サーバー / 検証用 VM | `.20` `vm-apps`、`.21` `vm-dev`、`.22` `vm-code` |
| `192.168.11.60–99` | DHCP プール | 動的割当 |
| `192.168.11.100–149` | IoT デバイス | `.100` ESP32 |
| `192.168.11.150–254` | 予約 / 実験用 | — |

VM の IP は Terraform（`terraform.tfvars`）で固定する。VMID は IP の末尾オクテットに 100 を足した値。

## ドメイン命名規約

内部 DNS は `lab.kanare.dev` ゾーン（CoreDNS が権威。[DNS 構成](../services/dns.md)）。サービスは `<サービス名>.lab.kanare.dev`、VM は `<VM 名>.lab.kanare.dev` で引く。

| FQDN | DNS の解決先 | 実際の宛先 | 用途 |
| --- | --- | --- | --- |
| `alertmanager.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.13:9093` | Alertmanager |
| `pve.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.10:8006` | Proxmox Web UI |
| `home.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.20:3001` | Homepage |
| `grafana.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.13:3000` | Grafana |
| `prometheus.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.13:9090` | Prometheus |
| `adguard.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.11:3000` | AdGuard Home Web UI |
| `code.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.22:8080` | code-server |
| `cloudcli.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.22:3001` | CloudCLI |
| `router.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.1:80` | ルーター管理画面（[DNS 構成](../services/dns.md#ルーター管理画面)） |
| `infra.lab.kanare.dev` / `vm-infra.lab.kanare.dev` | `192.168.11.11` | 同左 | `vm-infra` への直接アクセス |
| `vm-monitoring.lab.kanare.dev` | `192.168.11.13` | 同左 | `vm-monitoring` への直接アクセス |
| `vm-apps.lab.kanare.dev` | `192.168.11.20` | 同左 | `vm-apps` への直接アクセス |
| `vm-code.lab.kanare.dev` | `192.168.11.22` | 同左 | SSH / mosh の直接アクセス（Moshi など） |

`vm-dev` と `vm-windows` には DNS レコードを置いていない（手動起動のため）。Caddy 経由の FQDN には、証明書を FQDN ごとに取得する（[リバースプロキシと TLS](../services/reverse-proxy-tls.md)）。

## 外部接続の方針

判断の記録: [ADR-0005](../adr/0005-tailscale-only-remote-access.md)

- **外部には何も公開しない。** 自宅の外から入る経路は Tailscale だけにする。
- 公開が必要になるのは、Tailscale を入れていない他人と共有するサービスができたときだけ。その場合も、そのサービスに限って Cloudflare Tunnel を検討する（ロードマップ。現在は保留）。
- 外部サービスへの依存は最小にし、依存先が止まったときの影響を把握しておく。

## 回線と WAN

| 項目 | 内容 |
| --- | --- |
| 構成 | 建物の共用ルーター → Buffalo ルーター → 自宅 LAN（二重 NAT） |
| ポート開放 | できない（上流を制御できない） |
| グローバル IP | 利用しない（固定でも、自分で使える形でもない） |
| 引っ越し | 数年のうちに予定あり。新居の上流は未定のため、WAN 側の設計は VLAN 設計と切り離している（[VLAN 設計](08-vlan-design.md#wan-側は設計から切り離す)） |

## 外出先からのアクセス（Tailscale）

```text
外出先の端末 ──(Tailscale / WireGuard)──► vm-infra（subnet router）──► 192.168.11.0/24
                                           └─ split DNS: lab.kanare.dev → vm-infra
```

| 項目 | 設定 |
| --- | --- |
| 入口 | `vm-infra` の Tailscale（subnet router）。`192.168.11.0/24` を広告 |
| 名前解決 | split DNS で `lab.kanare.dev` を `vm-infra` に向ける |
| 認証 | Tailscale のアカウント。`vm-infra` の key expiry は無効 |
| 到達できる範囲 | LAN 全体（ACL は既定。ルーターにも届く。絞り込みは未実施） |
| 秘密情報 | `tailscale_authkey`（SOPS 管理） |
| 利用例 | スマホ・Mac から `https://home.lab.kanare.dev`、`vm-code` への SSH / mosh / CloudCLI / code-server |

- 設定の詳細と注意点（iOS の DNS、`1.1.1.1` を併記しない理由など）は [DNS 構成](../services/dns.md#tailscale-との連携)。
- VLAN 移行後は、広告するのを Servers（`10.20.0.0/24`）のみにする（[VLAN 設計](08-vlan-design.md#外出先からのアクセスtailscale)）。

## 外部サービスへの依存

| 依存先 | 用途 | 認証・秘密情報 | 止まったときの影響 |
| --- | --- | --- | --- |
| Tailscale（コントロールプレーン） | 外出先からの接続の確立、端末の認証 | アカウント、認証鍵（SOPS） | 外出先から LAN に入れない。LAN 内は影響なし |
| Cloudflare（DNS） | `kanare.dev` のゾーン。Caddy の DNS-01 チャレンジ | API トークン（SOPS） | 証明書の新規取得・更新ができない。既存の証明書は期限まで使える |
| Let's Encrypt | `*.lab.kanare.dev` 各 FQDN の証明書 | なし | 同上 |
| Slack | アラート通知（Incoming Webhook） | Webhook URL（SOPS） | 通知が届かない。`AlertmanagerNotificationsFailing` は Slack に出ない |
| Healthchecks.io | 外部 Heartbeat。`Watchdog` の途絶を検知する（[ADR-0010](../adr/0010-external-heartbeat.md)） | ping URL（SOPS） | 監視 VM・ホスト・回線の停止を外から検知できなくなる。サービス自体は影響なし |
| GitHub | リポジトリ、CI（lint のみ） | 個人アカウント | 構成の取得・push ができない。稼働中のサービスは影響なし |
| NTP（`ntp.nict.jp`、`time.google.com`） | 時刻同期 | なし | 時刻がずれる。TLS・ログの時刻に影響 |
| DNS ルートサーバー | Unbound の再帰解決（`root.hints`） | なし | 外部ドメインが引けない。fallback（`1.1.1.1` / `9.9.9.9`）は、接続できない場合だけ働く |
| パッケージ・イメージの配布元 | apt、Docker Hub、ghcr.io | なし | 更新・再構築ができない。稼働中のサービスは影響なし |

## 外向きの通信

| 通信 | 発信元 | 備考 |
| --- | --- | --- |
| Cloudflare API・ACME | `vm-infra`（Caddy） | 証明書の取得・更新 |
| Tailscale | `vm-infra` ほか | NAT 越えを含む |
| Slack Webhook | `vm-monitoring`（Alertmanager） | HTTPS |
| Heartbeat（Healthchecks.io） | `vm-monitoring`（Alertmanager） | HTTPS。`Watchdog` を 5 分毎に送る |
| DNS（再帰解決） | `vm-infra`（Unbound） | ルートから再帰。IPv6 は無効（`do-ip6: no`） |
| NTP | 全 VM | `systemd-timesyncd` |
| apt / Docker pull | 各 VM | 更新時 |

外向きの通信の制限（egress フィルタ）は、現在はしていない。VLAN 化の際に、Management からの外向きは更新用に限る計画（[VLAN 設計](08-vlan-design.md#通信ポリシー)）。

## 検討中・保留の項目

| 項目 | 状況 |
| --- | --- |
| Cloudflare Tunnel + Split-Horizon DNS で外部公開 | 保留（共有したい具体的なニーズが出てから） |
| 外部監視（Heartbeat） | 導入済み（[ADR-0010](../adr/0010-external-heartbeat.md)、[監視・アラート](../services/monitoring.md#外部-heartbeat)） |
| Tailscale の ACL で管理画面を除外 | 未実施 |
| 引っ越し後の上流ネットワーク対応 | 未定（[移行性](06-migration.md)） |
