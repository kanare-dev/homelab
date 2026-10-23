# 外部接続

homelab と外部（インターネット、クラウドサービス、外出先の端末）との接続を整理する。LAN 内の設計は [ネットワーク](../07_network/dns.md) を参照。

## 方針

- **外部には何も公開しない。** 自宅の外から入る経路は Tailscale だけにする。
- 公開が必要になるのは、Tailscale を入れていない他人と共有するサービスができたときだけ。その場合も、そのサービスに限って Cloudflare Tunnel を検討する（ロードマップ。現在は保留）。
- 外部サービスへの依存は最小にし、依存先が止まったときの影響を把握しておく。

## 回線と WAN

| 項目 | 内容 |
| --- | --- |
| 構成 | 建物の共用ルーター → Buffalo ルーター → 自宅 LAN（二重 NAT） |
| ポート開放 | できない（上流を制御できない） |
| グローバル IP | 利用しない（固定でも、自分で使える形でもない） |
| 引っ越し | 数年のうちに予定あり。新居の上流は未定のため、WAN 側の設計は VLAN 設計と切り離している（[VLAN 設計](../07_network/vlan-design.md#wan-側は設計から切り離す)） |

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

- 設定の詳細と注意点（iOS の DNS、`1.1.1.1` を併記しない理由など）は [DNS 構成](../07_network/dns.md#tailscale-との連携)。
- VLAN 移行後は、広告するのを Servers（`10.20.0.0/24`）のみにする（[VLAN 設計](../07_network/vlan-design.md#外出先からのアクセスtailscale)）。

## 外部サービスへの依存

| 依存先 | 用途 | 認証・秘密情報 | 止まったときの影響 |
| --- | --- | --- | --- |
| Tailscale（コントロールプレーン） | 外出先からの接続の確立、端末の認証 | アカウント、認証鍵（SOPS） | 外出先から LAN に入れない。LAN 内は影響なし |
| Cloudflare（DNS） | `kanare.dev` のゾーン。Caddy の DNS-01 チャレンジ | API トークン（SOPS） | 証明書の新規取得・更新ができない。既存の証明書は期限まで使える |
| Let's Encrypt | `*.lab.kanare.dev` 各 FQDN の証明書 | なし | 同上 |
| Slack | アラート通知（Incoming Webhook） | Webhook URL（SOPS） | 通知が届かない。`AlertmanagerNotificationsFailing` は Slack に出ない |
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
| DNS（再帰解決） | `vm-infra`（Unbound） | ルートから再帰。IPv6 は無効（`do-ip6: no`） |
| NTP | 全 VM | `systemd-timesyncd` |
| apt / Docker pull | 各 VM | 更新時 |

外向きの通信の制限（egress フィルタ）は、現在はしていない。VLAN 化の際に、Management からの外向きは更新用に限る計画（[VLAN 設計](../07_network/vlan-design.md#通信ポリシー)）。

## 検討中・保留の項目

| 項目 | 状況 |
| --- | --- |
| Cloudflare Tunnel + Split-Horizon DNS で外部公開 | 保留（共有したい具体的なニーズが出てから） |
| 外部監視（Heartbeat など） | 見送り（[監視・アラート](../05_operations-maintainability/monitoring.md#外部監視を導入しない判断2026-10-22)） |
| Tailscale の ACL で管理画面を除外 | 未実施 |
| 引っ越し後の上流ネットワーク対応 | 未定（[移行性](../09_migration/migration.md)） |
