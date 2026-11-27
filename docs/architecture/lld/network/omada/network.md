# ネットワーク（Omada のパラメーターシート）

画面の場所は、サイト > 構成 > ネットワーク設定 > インターネット・LAN・WLAN である。実機の値は [`snapshot/network.json`](snapshot/network.json) にある。表の読み方は [README](README.md#表の読み方) にある。VLAN の設計は[第5章 ネットワーク](../../../hld/05-network.md)、アドレスの一覧は [IP アドレス一覧](../ip-addresses.md)にある。

## インターネット（WAN）

WAN は ER605 の p1（WAN1）の 1 本だけである。上流は建物の共用ルーターで、DHCP で住所を受け取る（二重 NAT）。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `enable` | `true` | インターネットへの接続を有効にする | |
| `interval` / `unit` | `2` / `0` | WAN の接続を確かめる間隔と、その単位 | 既定。単位の値の意味は未確認 |
| `wanPortSettings[0].portName` | `WAN1` | WAN のポート | p1 |
| `…wanPortIpv4Setting.protoType` | `1` | IPv4 の接続の種類。0 は静的、1 は DHCP、2 は PPPoE など | 上流の共用ルーターから DHCP で受け取る（2026-11-06 に、`172.22.0.0/21` の範囲の住所を取れた） |
| `…ipv4Dhcp.mtu` | `1500` | MTU | 既定 |
| `…ipv4Dhcp.unicastDhcp` | `false` | DHCP をユニキャストで受け取る | 既定 |
| `…ipv4Dhcp.dhcpOptions`、`wanMultipleIps` | なし | DHCP のオプション、複数の住所 | 使わない |
| `…wanPortIpv4Setting.vlanId` / `qosTagEnable` | `0` / `false` | WAN に VLAN のタグを付ける | 使わない |
| `…wanPortIpv6Setting.enable` | `false` | WAN の IPv6 | 使わない（[ADR-0017](../../../../adr/0017-ipv6-disabled.md)） |
| `…wanPortMacSetting.method` | `0` | WAN の MAC アドレスの決め方。0 は機器の MAC のまま（と見込む。未確認） | MAC クローンは不要だった。上流は MAC で絞っていない（2026-11-06 に確認） |
| `lteWanSettings`、`usbLteSettings` | なし | モバイル回線の WAN | 使わない |

## LAN

LAN のネットワークは、VLAN ごとに 1 つ作っている。すべて ER605 がゲートウェイ（`.1`）になる（`purpose` は `1`。インターフェースとして作る方式）。

| 名前 | VLAN | ゲートウェイ（`gatewaySubnet`） | DHCP（`dhcpSettingsVO`） | 配る DNS（`priDns`） | リース（`leasetime`、分） |
| --- | --- | --- | --- | --- | --- |
| Management(Default) | 10 | `10.77.10.1/24` | 有効。`.240`〜`.250` | `10.77.10.1`（手動） | 60 |
| Servers | 20 | `10.77.20.1/24` | 無効 | — | — |
| Trusted | 30 | `10.77.30.1/24` | 有効。`.100`〜`.199` | `10.77.20.10`（手動） | 2880（48 時間） |
| Lab | 40 | `10.77.40.1/24` | 有効。`.100`〜`.149` | `10.77.20.10`（手動） | 1440（24 時間） |
| IoT | 50 | `10.77.50.1/24` | 有効。`.100`〜`.149` | `10.77.20.10`（手動） | 1440（24 時間） |
| Guests | 60 | `10.77.60.1/24` | 有効。`.100`〜`.199` | `10.77.20.10`（手動） | 240（4 時間） |
| DMZ | 70 | `10.77.70.1/24` | 無効 | — | — |
| Blackhole | 999 | `10.77.99.1/24` | 無効 | — | — |

- **既定のネットワーク**は Management(Default)（`primary` が `true`）である。2026-11-20 に、既定のネットワーク（VLAN1）を VLAN10 に統合した（[ADR-0032](../../../../adr/0032-merge-default-network-into-management-vlan10.md)）。Management の DHCP は、復旧ポート（SG2210P の p8）に繋いだ端末のためにある。
- **配る DNS**: Management は、ルーター自身（`10.77.10.1`）を配る。`vm-infra` が止まっても、管理系の名前解決を止めないためである。ほかの VLAN は、AdGuard（`10.77.20.10`）だけを配り、予備の DNS（`1.1.1.1` など）は配らない（[ADR-0024](../../../../adr/0024-dhcp-dns-single-no-fallback.md)、[ADR-0027](../../../../adr/0027-servers-octet-bands-and-emergency-dns.md)）。2 番目の DNS（`sndDns`）は空である。
- **Servers と DMZ** は DHCP を使わない。Servers のホストの住所は、Terraform で固定している。DMZ には、まだ何も置いていない。
- 配るドメイン名（`domain`）は設定していない。固定の割り当て（予約）は無い（[送信](transmission.md)）。
- すべてのネットワークで、IGMP スヌーピング、MLD スヌーピング、DHCP L2 リレー、DHCP ガード、ポータル、レート制限は無効、IPv6 は設定していない。
- `accessControlRule`（そのネットワークがアクセス制御のルールで使われているか）は、Blackhole だけ `false` である。値の意味は、仕様書の「Show AccessControlRule is enabled or not」以上は分からない（未確認）。
- **ずれ（2026-11-28 に発見）**: 以前の文書は、Blackhole を「ER605 のポートには割り当てない」と書いていた。実機では、Blackhole の `interfaceIds` に、ほかのネットワークと同じく ER605 の LAN 側のポート p2〜p5 が入っている。SG2210P の p1 は、タグ付きから Blackhole（999）を除いているので、VLAN 999 の通信は ER605 に届かない。通信への影響は無い見込みである。文書と実機のどちらに合わせるかは、未決定である。

## WLAN

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `wlans[0].name` | `既定` | WLAN グループ | 既定。SSID は作っていない。Wi-Fi は、Omada の外の Buffalo（AP モード）が出している（[WSR-1800AX4P](../wsr-1800ax4p.md)） |

## そのほかのサービス

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `upnp.enable` | `false` | UPnP | 外に何も公開しない方針なので、無効のままにする（2026-11-27 に画面でも確認） |
| `dns-proxy.enable` | `false` | DNS プロキシの拡張（DNSSEC、DoH、DoT、DNS の上書き） | 使わない。名前解決は AdGuard（`vm-infra`）で行う |
| `ddns` | なし | ダイナミック DNS | 使わない |
| `igmp.enable` / `igmp.version` | `true` / `2` | WAN 側の IGMP プロキシ（IPTV 向け）と、その版 | 既定。IPTV は使わない。有効になっているが、使う機器は無い（無効にするかは未決定） |
| `lan-multicasts` | なし | LAN のマルチキャストの設定 | 使わない |
| mDNS の中継 | 下の注 | | |

- **mDNS の中継**（一般設定 > mDNS）は、API の呼び方を確かめていないので、書き出していない。値は[一般設定](general.md#mdns-の中継)に手で書いている。
