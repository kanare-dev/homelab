# TP-Link ER605 V2.30

Omada のギガビット VPN ルーター（ゲートウェイ）。移行では、Buffalo に替わって家の入口のルーターになり、VLAN のゲートウェイ・DHCP・ACL を担う。公式の資料へのリンクと、データシートの仕様をまとめる。移行の手順は[ER605・SG2210P の移行計画](../../operations/roadmap/10-er605-sg2210p-migration-plan.md)、VLAN の設計は[VLAN 設計](../../architecture/08-vlan-design.md)、ルーターを選んだ判断は[ADR-0009](../../adr/0009-router-er605-first.md)にある。

> [!NOTE]
> 確認日は 2026-11-03。購入したのは **ER605 V2.30**。**底面のラベルは `UN` / `2.30` だが、出荷時のファームウェアは日本向け（JP）版**（2.2.8 Build 20260128 Rel.11283）で、更新に使えるのも JP 版のファイルだけ（[ファームウェアの更新](#ファームウェアの更新解決済み)）。仕様は、公式サイトで最新のデータシート（2025-09-02 掲載、グローバル版の V2.2）による。JP 版 V2.30 のデータシートは、見つけられなかった。同じ V2 系なので、数値は近いと見るが、差は未確認。数値は原文のまま載せている。

## 公式の資料

| 資料 | リンク |
| --- | --- |
| データシート（グローバル版 V2.2、PDF） | [ER605(UN)2.20_Datasheet.pdf](https://static.tp-link.com/upload/product-overview/2025/202509/20250902/ER605%28UN%292.20_Datasheet.pdf)（URL の括弧は `%28` `%29`。2025-09-02 掲載） |
| データシートの掲載ページ | [ER605(UN)_V2_Datasheet](https://support.omadanetworks.com/us/document/1940/) |
| 製品ページ（日本） | [Omada Networks: ER605](https://www.omadanetworks.com/jp/business-networking/omada-router-wired-router/er605/) |
| サポート（V2 のファームウェア・マニュアル） | [ER605 V2](https://support.omadanetworks.com/us/product/er605/v2/) |
| サポート（V2.30 のファームウェア） | [ER605 V2.30](https://support.omadanetworks.com/us/product/er605/v2.30/?resourceType=download) |
| **JP 版 V2.30 のファームウェア（この個体はこちら）** | [ER605 V2.30（日本）](https://support.omadanetworks.com/jp/download/firmware/er605/v2.30/) |
| JP 版 2.4.2 のリリースノート | [ER605(JP)_V2_2.4.2_Release Note.pdf](https://static.tp-link.com/upload/firmware/2026/202606/20260603/ER605%28JP%29_V2_2.4.2_Release%20Note.pdf) |
| グローバル版（UN）2.4.10 のリリースノート（この個体には使えない） | [ER605(UN)_V2_2.4.10_Release Note.pdf](https://static.tp-link.com/upload/firmware/2026/202610/20261020/ER605%28UN%29_V2_2.4.10_Release%20Note.pdf) |
| サポート（版数の一覧） | [ER605（日本）](https://support.omadanetworks.com/jp/product/er605/) |

データシートの PDF はリポジトリに入れない（リンクのみ）。ファームウェアのリリースノートは、サポートページで版数別に公開されている。

## ファームウェアとコントローラー

| 項目 | 内容 |
| --- | --- |
| 現在のファームウェア | **2.4.2 Build 20260511 Rel.77362**（JP 版。2026-11-03 にコントローラーから更新） |
| JP 版 V2.30 の最新（確認日時点） | 2.4.2 Build 20260511 Rel.77362（2026-06-03 掲載）。V2.30 向けの JP 版は、2.2.8 Build 20260128（初版）と 2.4.2 の 2 つだけ |
| グローバル版（UN）との違い | UN 版の最新は 2.4.10 Build 20260916。**JP 版の個体に、UN 版のファイルは入れられない**（検証で拒否される）。JP 版は、UN 版より遅れて公開される |
| 更新条件（JP 版 2.4.2） | 更新元は 2.2.8 Build 20260128 Rel.11283 以降（リリースノート） |
| コントローラーとの対応 | JP 版 2.4.2 のリリースノートの推奨は 6.2.0.17。`vm-omada` は 6.3.0.111 で、採用と更新に問題はなかった。ER605 が動く最低のコントローラーの版は、公式の資料に見つけられなかった |
| 動作モード | スタンドアロン（本体の GUI で設定）とコントローラーモード（Omada で設定）。**コントローラーに採用すると、本体の GUI は使えなくなる**（[VLAN 設計](../../architecture/08-vlan-design.md)） |

JP 版 2.4.2 の新機能: V6plus/DS-Lite のダイヤルアップ、DHCP サーバーの IP プールの複数範囲、コントローラーでの DHCP クライアント一覧の表示、コントローラーから切断したときの本体 UI での設定、SIP ALG のポート設定。

## ファームウェアの更新（解決済み）

出荷時の 2.2.8 Build 20260128 Rel.11283 から、JP 版 2.4.2 に更新できた（2026-11-03）。

### 原因

**グローバル版（UN）のファイルを使っていた。** 底面のラベルは `UN` / `2.30` だが、出荷時のファームウェアは JP 版の V2.30 の初版で、更新の検証は、ファームウェアの地域の区分で行われ、UN 版のファイルを「無効」として拒否していた。ラベルと中身の地域が食い違う理由は、確認できていない（ラベルはハードウェアの系統、地域はファームウェアで決まる、という見立て）。

気づいた手がかり:

- 出荷時のビルド（2.2.8 Build 20260128）が、UN 版の一覧に無く、JP 版の一覧の初版と一致した（運用者の指摘）。
- コントローラーのログで、クラウドがこの個体に、JP 版の 2.4.2（リリースノートは「ER605(JP) v2.20/v2.30」）を提示していた。

### 試した結果

| 方法 | ファイル | 結果 |
| --- | --- | --- |
| 本体の管理画面（Chrome、Safari） | UN 版の 2.3.3、2.3.2、2.4.3、2.4.10 | 「アップグレードに失敗しました。アップグレードファイルを確認して、やり直してください」 |
| コントローラー 6.3.0 の手動更新（1 回目） | UN 版の 2.4.10 | 「デバイスがアップデートファイルのダウンロードに失敗しました」。`vm-omada` の UFW が 8043 を Caddy だけに許可していたため。LAN に許可して解決 |
| コントローラー 6.3.0 の手動更新（2 回目） | UN 版の 2.4.10 | ダウンロードは成功。ER605 の検証で拒否（`stage=DOWNVAL`、`errcode=-2`、`FIRMWARE_VALIDATION_FAILED`）。画面は「アップデートファイルが無効です」 |
| コントローラー 6.3.0 の手動更新（3 回目） | **JP 版の 2.4.2** | **成功**（検証を通過、書き込み、再起動、再接続。約 7 分） |

### 更新の手順（JP 版の個体）

1. [JP 版 V2.30 のファームウェア](https://support.omadanetworks.com/jp/download/firmware/er605/v2.30/)から、`ER605(JP)_V2.30_...` の ZIP をダウンロードして展開する（中の `.bin` を使う）。
2. ER605 をコントローラーに採用する。
3. コントローラーの Devices で ER605 を選び、手動（ローカルファイル）で `.bin` を指定して更新する。
4. 更新中（5〜10 分）は、電源を抜かない。
5. コントローラーへの更新は、機器が `vm-omada` の HTTPS 管理ポート（8043）から、ファイルをダウンロードする。**`vm-omada` の UFW で、機器のネットワークからの 8043 を許可しておく**（[vm-omada の設定](../../../ansible/inventory/group_vars/omada/vars.yml)）。

次回以降は、まず、サポートページの JP 版（`ER605(JP)_V2.30`）の一覧で、新しいファームウェアが出ていないか確認する。

## 仕様（データシート。グローバル版 V2.2）

### ハードウェア

| 項目 | 内容 |
| --- | --- |
| 製品名 | Omada Gigabit VPN Gateway |
| インターフェース | ギガビット WAN × 1、ギガビット LAN/WAN × 2、ギガビット LAN × 2（合計 5 ポート）。USB 2.0 × 1（LTE のドングルに対応） |
| ポート番号と種類 | p1 が WAN、p2 と p3 が WAN/LAN（切り替え）、p4 と p5 が LAN。運用者が本体で確認した（2026-11-06）。この家での使い方は、[ER605 の設定](settings.md#ポート) |
| ネットワークメディア | 1000BASE-T: UTP カテゴリー 5e / 6（最大 100 m）。100BASE-TX、10BASE-T も対応 |
| 電源 | 外付けの DC アダプター 12 V / 1 A |
| 最大消費電力 | 7.94 W |
| Flash / DRAM | 128 MB NAND / 256 MB DDR |
| LED | PWR、SYS、WAN（Link/Act）、LAN（Link/Act）、USB |
| ボタン | リセットボタン |
| 寸法（幅 × 奥行 × 高さ） | 158 × 101 × 25 mm |
| 動作環境 | 温度 0 ℃〜40 ℃、湿度 10〜90 %（結露なし） |
| 保管環境 | 温度 -40 ℃〜70 ℃、湿度 5〜90 %（結露なし） |
| 認証 | CE、FCC、RoHS（PSE の記載はない） |
| 同梱品 | ER605、電源アダプター、RJ-45 の LAN ケーブル、クイックインストールガイド |

### 性能（データシートの測定値。実際の値は環境による）

| 項目 | 内容 |
| --- | --- |
| 同時セッション数 / 毎秒の新規セッション | 150,000 / 1,800 |
| DPI のスループット | TCP: 944 Mbps、UDP: 940 Mbps |
| NAT のスループット（固定 IP） | 上り 941.64 Mbps、下り 944.35 Mbps、双方向 1775.32 Mbps |
| NAT のスループット（DHCP） | 上り 941.23 Mbps、下り 943.85 Mbps、双方向 1782.27 Mbps |
| NAT のスループット（PPPoE） | 上り 938.83 Mbps、下り 940.27 Mbps、双方向 1781.77 Mbps |
| パケット転送レート | 66 バイト: 上り 1,388,815 pps、下り 1,388,806 pps。1518 バイト: 上り 81,067 pps、下り 81,069 pps |
| IPsec VPN | ESP-SHA1-AES256: 239.39 Mbps、ESP-SHA256-AES256: 250.94 Mbps、ESP-SHA384-AES256: 31.44 Mbps、ESP-SHA512-AES256: 53.57 Mbps |
| WireGuard / OpenVPN | 82.62 Mbps / 15.90 Mbps |
| L2TP / PPTP / GRE | L2TP: 暗号化なし 558.60 Mbps、暗号化 143.60 Mbps。PPTP: 暗号化なし 616.33 Mbps、暗号化 49.83 Mbps。GRE: 暗号化なし 460.97 Mbps、暗号化 161.83 Mbps |

### 機能

| 分類 | 内容 |
| --- | --- |
| 規格・プロトコル | IEEE 802.3 / 802.3u / 802.3ab / 802.3x / 802.1q、TCP/IP、DHCP、ICMP、NAT、PPPoE、NTP、HTTP/HTTPS、DNS、IPSec、PPTP、L2TP、OpenVPN、SNMP |
| WAN の接続方式 | 固定 IP、動的 IP、PPPoE（MRU 設定に対応）、PPTP、L2TP |
| DHCP | DHCP サーバー、DHCP オプションのカスタマイズ、アドレスの予約、複数 IP インターフェース、マルチネット DHCP、WAN の DHCP 60。DHCPv6 PD サーバーはスタンドアロンのみ |
| VLAN | 802.1Q VLAN、ブリッジ VLAN |
| mDNS | mDNS リピーター（`mDNS Repeater`）に対応 |
| ファイアウォール・ACL | ステートフル ACL、IP / FQDN ベースのアクセス制御、攻撃防御（TCP/UDP/ICMP フラッド、スキャン、WAN からの ping 遮断）、IP-MAC バインディング、ARP 検査、URL フィルタ |
| DNS | DNS プロキシ（DNSSEC、DoH、DoT） |
| NAT | 1 対 1 NAT、マルチネット NAT、ポート転送、NAT-DMZ、UPnP、ALG（FTP / H.323 / SIP / IPsec / PPTP） |
| ルーティング | スタティックルーティング、ポリシールーティング。RIP と OSPF はスタンドアロンのみ |
| 負荷分散 | インテリジェントな負荷分散、アプリケーション最適化ルーティング、リンクバックアップ、オンライン検出 |
| QoS・帯域 | QoS、IP ごとのセッション制限と帯域制御 |
| VPN | IPsec（LAN 対 LAN、20 トンネル）、PPTP（16）、L2TP（16）、OpenVPN（16）、WireGuard、GRE（スタンドアロンのみ）、SD-WAN（コントローラーモードのみ） |
| IPv6 | 固定 / SLAAC / DHCPv6 / PPPoE / 6to4 / パススルーなど |
| 認証ポータル | 認証なし、簡易パスワード、ホットスポット（ローカルユーザー / バウチャー / SMS / RADIUS）、外部 RADIUS、外部ポータル、LDAP。簡易パスワード・バウチャー・SMS・RADIUS・外部ポータルは、コントローラーモードのみ。LDAP は、スタンドアロンのみ |
| 管理 | Web 管理画面、リモート管理、設定のエクスポートとインポート、SNMP v1/v2c/v3、ping と traceroute、ポートミラーリング、Syslog、DDNS。CLI と NTP 同期は、スタンドアロンのみ |
| Omada SDN | ハードウェアコントローラー（OC200 / OC300）とソフトウェアコントローラーに対応。自動検出、設定の一元化、状態の監視、異常の警告、再起動のスケジュール、キャプティブポータル。ゼロタッチプロビジョニングは、クラウドベースのコントローラーだけ |

## このホームラボでの使い方との対応

| 論点 | データシートから分かること |
| --- | --- |
| ポート数 | WAN × 1、LAN/WAN × 2、LAN × 2。WAN を 1 つ使っても、LAN は 3 つ以上確保できる（[VLAN 設計](../../architecture/08-vlan-design.md)）。移行計画では、LAN の 1 本を SG2210P の p1（trunk）に使う。段階 1 の間は、Proxmox と Buffalo も ER605 の LAN に繋ぐ |
| 回線の速度 | NAT のスループットが約 940 Mbps で、家の回線（下り約 530 Mbps、上り約 600 Mbps）に足りる（[ADR-0009](../../adr/0009-router-er605-first.md)） |
| mDNS の中継 | mDNS リピーターに対応。Trusted ↔ IoT の中継に使う。必要なコントローラーの版（ゲートウェイの mDNS は v5.6 以降）は[VLAN 設計](../../architecture/08-vlan-design.md)の未決事項にある |
| VLAN 間の通信の制限 | ステートフル ACL と IP ベースのアクセス制御に対応。コントローラーモードの Gateway ACL で、LAN → LAN を制限できるかは、実機で確認する（[VLAN 設計](../../architecture/08-vlan-design.md)の未決事項） |
| IPv6 | 本機は対応するが、家では IPv6 を無効にする方針（[ADR-0017](../../adr/0017-ipv6-disabled.md)） |
| VPN | Tailscale を使うので、本機の VPN 機能は使わない。参考までに、WireGuard は 82.62 Mbps |
| ポートミラーリング | 管理機能にポートミラーリングの記載があるが、使える範囲は未確認。通信の取得は、SG2210P のミラーリングを第一候補にしている（[ネットワーク通信の収集・可視化](../../operations/roadmap/06-network-traffic-analysis.md)） |
| スタンドアロンだけの機能 | CLI、NTP 同期、RIP / OSPF、GRE、LDAP、DHCPv6 PD サーバー。コントローラーに採用したあとは使えない。NTP は、コントローラー側の設定で行う |
| 設置 | ファンレス。動作温度は 40 ℃ まで。寸法 158 × 101 × 25 mm で、10 インチラックに収まる（[10 インチラック](../rack-10inch/README.md)）。電源は外付けアダプター |
