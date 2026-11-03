# 0023. Proxmox 向けの trunk は、全 VLAN をタグ付きにする

- ステータス: 採用（VLAN は未適用）
- 日付: 2026-11-03

## 背景

[VLAN 設計](../architecture/08-vlan-design.md)の初版は、SG2210P の Proxmox 向けポート（p2）を、Management を native（untagged）、そのほかの VLAN をタグ付きにする trunk としていた。Proxmox ホストは `vmbr0` に直接 IP を付け、ホストが落ちたときに、タグなしで届くようにするためだった。

[移行計画](../operations/roadmap/10-er605-sg2210p-migration-plan.md)の検討で、次の問題が見えた。

- Terraform で `vlan_id` を付け忘れた VM は、タグなしで出て、native の Management に入る。最も強い VLAN に、事故で入る。
- Management の VM（`vm-omada`）は、タグなしで繋ぐ特別扱いになる。Proxmox のブリッジは、タグ付きの VLAN10 の VM と、タグなしのホストを、別の面として扱うため。

## 決定

p2 は、**通す VLAN のすべてをタグ付き**にする（「全 VLAN」は、p2 が通す VLAN の 10・20・40・50・70 のすべて。VM を置かない Trusted と Guests は、p2 に通さない）。

- Proxmox ホストの Management の IP は、`vmbr0` ではなく、タグ付きの `vmbr0.10`（`10.77.10.10/24`、ゲートウェイ `10.77.10.1`）に付ける。`vmbr0` は VLAN-aware で、IP を持たない。
- 全 VM（`vm-omada` を含む）は、VLAN ID を必ず指定する。Terraform の VM モジュールの `vlan_id` は、必須（既定値なし）にする。
- p2 の native（untagged）は、未使用の VLAN1（旧 LAN。切り替え後は DHCP を止めて、他へ通さない）のままにする。タグなしの通信は、どこの VLAN にも入らない。p2 に tagged で足すのは、10・20・40・50・70。

## 理由

- 付け忘れが、通信できないという形で、すぐに分かる。事故で Management に入ることがない。
- 全 VM が、同じ書き方（`vlan_id` を必ず指定）になり、特別扱いが無くなる。
- 切り替えの前後で、p2 のタグなしの設定（VLAN1）が変わらない。タグ付きの VLAN を足すだけなので、戻しが簡単（ホストの設定を `vmbr0` に戻せば、旧 LAN に戻る）。

## 代替案

| 案 | 長所 | 短所 |
| --- | --- | --- |
| Management を native（初版の案） | ホストの設定が単純で、VLAN の設定を間違えても、タグなしで届く | 付け忘れた VM が Management に入る。Management の VM が特別扱いになる |
| 全 VLAN をタグ付き（採用） | 事故の影響が小さい。書き方が揃う | ホストが `vmbr0.10` になり、設定を間違えると、物理コンソールで直す必要がある |

## 影響と再検討の条件

- ホストのネットワークの設定を間違えると届かなくなる。移行計画の 3-A のリハーサルで先に試し、物理コンソールを用意しておく。
- Terraform の VM モジュールに `vlan_id` を必須で追加する。既存の VM は、切り替え当日に、VLAN ID を指定して適用する。
- ホストが届かなくなる事故が繰り返される場合は、native に戻す（新しい ADR で置き換える）。

詳細: [VLAN 設計](../architecture/08-vlan-design.md#配置の方針)
