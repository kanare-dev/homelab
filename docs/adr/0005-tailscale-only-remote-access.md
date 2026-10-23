# 0005. 外出先からのアクセスは Tailscale のみにする

- ステータス: 採用
- 日付: 記録なし

## 背景

自宅は集合住宅の二重 NAT 環境で、外からポート開放ができない。外出先から LAN のサービス（Homepage、`vm-code` など）を使いたい。数年のうちに引っ越す予定があり、新居の上流は未定。

## 決定

- 外出先からのアクセスは、`vm-infra` を subnet router にした **Tailscale のみ**で行う。
- Cloudflare Tunnel などによる外部公開は、Tailscale を入れていない他人と共有する具体的なニーズが出たサービスに限る。ニーズが出るまで着手しない（保留）。

## 理由

- 二重 NAT でも、Tailscale は外向きの接続だけで成立する。引っ越し先で CGNAT などになっても変わらず使える。
- 自分専用のアクセスは Tailscale で完結し、外部公開は不要。

## 代替案

| 案 | 状況 |
|---|---|
| Cloudflare Tunnel + Split-Horizon DNS | 保留（共有ニーズが出てから） |
| WireGuard を自前で運用 | 二重 NAT でポート開放できないため、代替として Tailscale を採用 |

## 影響と再検討の条件

- Tailscale のコントロールプレーンに依存する（[外部接続](../architecture/network.md#外部サービスへの依存)）。
- Tailscale の ACL は既定のまま（管理画面の除外は未実施）。
- 他人と共有したいサービスが出たら、そのサービスだけ Cloudflare Tunnel を検討する。

詳細: [ネットワーク設計](../architecture/network.md)、[DNS 構成](../services/dns.md#tailscale-との連携)
