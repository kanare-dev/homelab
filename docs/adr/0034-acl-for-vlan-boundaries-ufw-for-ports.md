# 0034. ゲートウェイの ACL は VLAN の境界と UFW の無い宛先を守り、ポートの絞り込みは UFW を正とする

- ステータス: 採用（未適用）
- 日付: 2026-11-26

## 背景

段階 3b が完了し（2026-11-20）、ER605 の ACL（LAN → LAN）を、[通信ポリシー](../architecture/hld/05-network.md#通信ポリシー)の許可表に絞る準備をしている（[ADR-0029](0029-stage3-acl-allow-all-then-tighten.md)）。

許可表を実機の通信に合わせて見直したところ（2026-11-26）、Trusted → Servers の行に、各 VM の UFW と同じポート（`vm-code` の 8080・3001・5173、AdGuard の画面の 3000 など）を、ACL にも書く形になっていた。この形では、ポートを足すたびに、Ansible の UFW と Omada の画面の ACL の両方を直す必要がある。段階 3 でも、UFW の許可元の直し忘れで、通信が止まったことが何度もあった。

運用者は、ACL を入れたあとも UFW を残すのかを問い、ACL と UFW の役割を決めることになった。

前提となる事実は、次のとおりである。

- ER605 の ACL が見るのは、VLAN をまたぐ通信だけである。同じ VLAN の中の通信（Servers の VM どうし）と、Tailscale の subnet router（`vm-infra`）が SNAT して出す通信は、ACL を通らない。
- ACL は Omada の画面で設定し、コードで管理していない。設定の間違いや、コントローラー・機器の作り直しで、全許可に戻ることがある（[INC-2026-11-08](../operations/incidents/2026-11-08-sg2210p-native-vlan-overwrite.md) のような、意図しない上書きも起きている）。
- Servers と Lab の VM には、すべて UFW があり、Ansible でポートと許可元を絞っている。Docker で公開したポートは、`ufw_docker` が `DOCKER-USER` で絞っている。
- Proxmox ホスト（`pve01`）には、ホストのファイアウォールが無い（2026-11-26 に確認。Proxmox ファイアウォールは無効、`iptables` の INPUT は全許可、UFW は入っていない）。
- Trusted には、段階 4 で IoT に移すまで、テレビと SwitchBot Hub 2 も入っている。

## 決定

1. **UFW は、ACL を入れたあとも残す。** 同じ VLAN の中の通信と Tailscale 経由の通信は、UFW でしか守れない。ACL が全許可に戻ったときの、最後の守りにもなる。
2. **ポートの絞り込みは、UFW を正とする。** ホストごとに、どのポートを誰に開けるかは、Ansible の UFW の設定（`ansible/inventory/group_vars/*/vars.yml`）に書く。
3. **ACL の細かさは、送信元の信用と、宛先に UFW があるかで決める。**

   | 通信 | ACL | 理由 |
   | --- | --- | --- |
   | Trusted → Servers・Lab | VLAN 単位で全許可（ICMP を含む） | 宛先の VM には UFW があり、ポートまで絞っている。ACL に同じポートを書いても、守りはほとんど増えない |
   | Trusted → Management | ホストとポートまで絞る | `pve01` に UFW が無く、Management を守れるのは ACL だけである |
   | Servers → Management・Lab | ホストとポートまで絞る | 重要な側や別の VLAN への越境で、ルールが数件しかなく、ほとんど変わらない |
   | Lab・IoT・Guests・DMZ → 他の VLAN | `vm-infra` の DNS(53) だけを許可し、残りは拒否する | 信用しない端末を閉じ込める。ACL の一番の役目である |
   | Management → 他の VLAN | 拒否 | Management のホストは、DNS をルーターに、NTP をインターネットに向けるので、他の VLAN を使わない |

4. 新しいポートを開けるときは、UFW だけを直す。ACL を直すのは、VLAN をまたぐ通信の組み合わせが新しく増えるときと、Management への通信を増やすときである。

## 理由

- ACL と UFW に同じポートを書くと、防げる範囲はほとんど変わらないのに、片方だけ直し忘れて通信が止まる。ACL を直すには Omada の画面を操作する必要があり、変更の diff も残らない（[ADR-0033](0033-docs-first-by-change-type-and-diagram-order.md)）。
- ポートを UFW に寄せると、許可の大半がコードで管理され、レビューできる。
- ACL は、UFW では守れないもの（VLAN の境界をまたぐ信用しない端末と、UFW の無い Management）に集中させる。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| ACL と UFW の両方に、同じポートまで書く（見直す前の許可表） | 二重管理になり、直し忘れで通信が止まる。UFW が間違って開いた場合しか、違いが出ない |
| ACL を入れたら UFW を外す | 同じ VLAN の中の通信と、Tailscale 経由の通信が守れなくなる。ACL が全許可に戻ったときに、守りが無くなる |
| Trusted → Management も VLAN 単位で許可する | `pve01` にホストのファイアウォールが無いので、Management のポートを絞る手段が無くなる |

## 影響と再検討の条件

- Trusted の端末が乗っ取られたとき、Servers・Lab へ届くかは、UFW の許可だけで決まる。段階 4 までは、テレビと SwitchBot Hub 2 も Trusted にいる。このリスクを受け入れる。段階 4 でこれらを IoT に移せば、Trusted は運用者の端末だけになる。
- [通信ポリシー](../architecture/hld/05-network.md#通信ポリシー)の許可表と、[ACL の名前と説明の付け方](../architecture/lld/network/acl.md)のルールの例を、この方針に合わせた。
- 再検討の条件: `pve01` にホストのファイアウォール（Proxmox ファイアウォールなど）を入れたら、Trusted → Management も粗くできるか見直す。Trusted に、運用者が管理しない端末が増えたら（来客の端末を Trusted に入れるなど）、Trusted → Servers を絞り直す。
