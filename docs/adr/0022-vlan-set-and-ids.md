# 0022. VLAN を 7 本（Trusted と Lab を含む）にし、ID を信頼度の順に振る

- ステータス: 採用（VLAN は未適用）。`vm-dev` などのホストの末尾オクテットは、[0025](0025-address-octets-by-role.md) で変わった（`vm-dev` は `10.77.40.10`）
- 日付: 2026-11-02
- [ADR 0015](0015-vlan-address-scheme-10-77.md) の VLAN の構成と ID を置き換える。アドレス体系 `10.77.<VLAN>.0/24` は変えない

## 背景

ADR 0015 の時点の構成は 6 本（Management / Servers / Clients / IoT / Guests / DMZ）で、ID は追加した順に振っていた（DMZ が 60）。次の 2 点を見直したい。

- 一時的な検証用 VM や開発環境（`vm-dev`）を、常時稼働のサーバーと分けたい。壊れてもよく、信用しない領域を持ちたい。
- 日常端末の区分は、Clients より Trusted のほうが役割を表せる。

まだ何も適用していないので、ID の振り直しに運用上の費用はかからず、文書の修正だけで済む。

## 決定

VLAN を次の 7 本にする。ID は信頼度の高い順（内側から外側）に振り、外部に触れる Guests と DMZ を末尾に置く。

| VLAN | 名前 | 変更 |
| --- | --- | --- |
| 10 | Management | 変更なし |
| 20 | Servers | 変更なし |
| 30 | Trusted | Clients を改名 |
| 40 | Lab | 新規 |
| 50 | IoT | 40 から移動 |
| 60 | Guests | 50 から移動 |
| 70 | DMZ | 60 から移動 |

- `vm-dev` は Lab（`10.77.40.21`）、`vm-code` と `vm-apps` は Servers に置く。
- Lab は DHCP プール `.100–.199` を持つ（使い捨ての VM 用）。Terraform で固定する VM は `.10–.99`。
- Lab は、他の VLAN への新規接続を原則拒否する（DNS を除く）。Trusted からは入れる。
- 外出先から `vm-dev` に入れるように、Tailscale の subnet route は Servers と Lab の 2 つを広告する。この通信は subnet router（`vm-infra`）が送信元になるため、Servers → Lab の許可が要る。
- コンテナ・K8s 用の VLAN（Containers）は作らない。

詳細: [VLAN 設計](../architecture/08-vlan-design.md#vlan-一覧)

## 理由

- 検証用 VM は壊れる、または侵害される可能性が高い。常時稼働のサーバーと同じ VLAN に置くと、そこから Servers 内の `vm-infra`（DNS、Caddy、Tailscale）に直接届いてしまう。
- ID を信頼度の順に振ると、ID を見ただけで、内側か外側かがわかる。ファイアウォールのルールも書きやすい。
- 未適用の今なら、ID の振り直しは文書の修正だけで済む。適用後は、ホストの IP や Omada の設定を直す羽目になる。

## 代替案

- 既存の ID を動かさず、Lab を 70 として末尾に足す: 修正は最小だが、ID が追加した順になり、信頼度とは無関係になる。
- Lab を作らず、`vm-dev` を Servers に置く: VLAN は 6 本のまま。ただし、検証用 VM から `vm-infra` に直接届く。
- Containers VLAN（K8s ノード用）を作る: 用途が定まっていないので作らない。k3s を数台立てる程度なら Servers でよい。

## 影響と再検討の条件

- 許可表は 6×7 から 7×8 になる。ADR 0015 の時点の「VLAN の数の妥当性」の判断（運用してから負荷を見て見直す）は引き継ぐ。
- DMZ は VLAN60 から VLAN70 に変わる（[ADR 0016](0016-dmz-placement.md)、[DMZ と外部公開](../operations/roadmap/07-dmz.md)）。
- ESP32 とテレビは `10.77.50.x`、`vm-dev` は `10.77.40.21` になる。
- Tailscale の ACL（管理画面の外部到達の見直し）は、Servers と Lab の 2 つの範囲を前提に書く。
- Containers VLAN は、次のいずれかが起きたときに再検討する。K8s の Pod や LoadBalancer の通信を、他の VLAN と別のルールで制限したくなった。LoadBalancer 用の IP 帯を独立して持ちたくなった。ノードが増えて Servers と混ぜたくなくなった。そのときは ID `80` を使う。
