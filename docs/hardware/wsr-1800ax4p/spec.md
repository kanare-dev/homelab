# Buffalo WSR-1800AX4P

Wi-Fi 6 対応の家庭用 Wi-Fi ルーター（AirStation）。現在は家のルーターで、移行では ER605 に交換して、AP（ブリッジ）モードの Wi-Fi の入口として使い続ける。公式の資料へのリンクと、製品ページの仕様をまとめる。設定値は[WSR-1800AX4P の設定](settings.md)（詳細設計）、移行の手順は[ER605・SG2210P の移行計画](../../operations/roadmap/10-er605-sg2210p-migration-plan.md)、VLAN の設計は[VLAN 設計](../../architecture/08-vlan-design.md)にある。

> [!NOTE]
> 確認日は 2026-11-03。仕様は Buffalo の製品ページ（仕様表）による。数値は原文のまま載せている。ファームウェアの版数は確認していない。色違いの型番は WSR-1800AX4P-WH（ホワイト）と WSR-1800AX4P-BK（ブラック）で、仕様は同じ。

## 公式の資料

| 資料 | リンク |
| --- | --- |
| 製品ページ（ホワイト） | [WSR-1800AX4P-WH](https://www.buffalo.jp/product/detail/wsr-1800ax4p-wh.html) |
| 製品ページ（ブラック） | [WSR-1800AX4P-BK](https://www.buffalo.jp/product/detail/wsr-1800ax4p-bk.html) |
| 仕様表（印刷用ページ） | [仕様書](https://www.buffalo.jp/product/detail/print/wsr-1800ax4p-wh.html) |
| 取扱説明書の一覧 | [マニュアル](https://www.buffalo.jp/product/detail/manual/wsr-1800ax4p-wh.html) |
| ユーザーマニュアル（Web 版） | [WSR-1800AX4P シリーズ ユーザーマニュアル](https://www.buffalo.jp/s3/guide/wsr-1800ax4p/99/ja/mobile_index.html) |
| よくあるご質問 | [FAQ](https://www.buffalo.jp/product/detail/faq/wsr-1800ax4p-wh.html) |
| ソフトウェア（ファームウェアなど） | [ダウンロード](https://www.buffalo.jp/product/detail/software/wsr-1800ax4p-wh.html) |
| モードの切り替え（WSR-1800AX4P を含む） | [Wi-Fiルーターのモード設定について](https://www.buffalo.jp/support/faq/detail/124146909.html) |
| AP（ブリッジ）モードにする方法（機種ごとに手順が違う） | [Wi-Fiルーターのルーター機能を使用しないでAPモード（ブリッジモード）として使用する方法](https://www.buffalo.jp/support/faq/detail/290.html) |

## 仕様（製品ページ）

### 無線 LAN

| 項目 | 内容 |
| --- | --- |
| 製品名 | Wi-Fi 6（11ax）対応 Wi-Fi ルーター 1201+573Mbps AirStation |
| 発売時期 | 2023 年 9 月 |
| 準拠規格（最大転送速度） | 5GHz: IEEE 802.11ax 1201Mbps（80MHz 2x2）、802.11ac 866Mbps（80MHz 2x2）、802.11n 300Mbps（40MHz 2x2）、802.11a 54Mbps。2.4GHz: 802.11ax 573Mbps（40MHz 2x2）、802.11n 300Mbps（40MHz 2x2）、802.11g 54Mbps、802.11b 11Mbps（理論上の最大値） |
| 伝送方式 | CCK、DSSS、OFDM、OFDMA、MIMO |
| チャンネル（2.4GHz / 5GHz） | W52: 36/40/44/48ch、W53: 52/56/60/64ch、W56: 100〜140ch（100/104/108/112/116/120/124/128/132/136/140）、W56（新電波法対応）: 144ch。W52/W53 は電波法により屋外使用禁止 |
| アンテナ | 内蔵。5GHz 2 本、2.4GHz 2 本 |
| セキュリティー | OPEN / WPA / WPA/WPA2-mixed / WPA2 / WPA2/WPA3 / WPA3 |
| そのほか | Any 接続拒否、プライバシーセパレーター、MAC アクセス制限（最大 64 台）、バンドステアリング Lite、干渉波自動回避、ビームフォーミング、MU-MIMO、TWT |
| アクセスモード | インフラストラクチャーモード、中継機能 |
| メッシュ | Wi-Fi EasyMesh |

### 有線 LAN とルーター機能

| 項目 | 内容 |
| --- | --- |
| ポート | LAN ポート: 最大 1Gbps × 4、INTERNET ポート: 最大 1Gbps × 1（RJ-45 型 8 極） |
| WAN 側の IP 取得 | 手動 / DHCP / PPPoE / DHCPv6-PD / IPv6（IPoE / IPv4 over IPv6） |
| IPv4 over IPv6 | OCN バーチャルコネクト、v6 プラス、IPv6 オプション、transix、クロスパスに対応 |
| セキュリティー | ステートフルパケットインスペクション（SPI）、パケットフィルタリング、VPN マルチパススルー（PPTP） |
| その他の機能 | 回線自動判別切替、ネット脅威ブロッカー 2 ベーシック（1 年間無料）、キッズタイマー、ゲストポート、USB 共有、スマート引っ越し +（無線引っ越し）、AirStation アプリ |
| 動作モード | ルーター / ブリッジ（AP）。背面のスイッチで切り替える |

製品ページの注記: 一部の機能は、ルーターとして動作しているときだけ使える。詳細は取扱説明書で確認する。

### ハードウェア

| 項目 | 内容 |
| --- | --- |
| 電源 / 消費電力 | AC100V 50/60Hz / 最大 11.0W |
| 外形寸法（幅 × 高さ × 奥行） | 36.5 × 160 × 160mm（本体のみ、突起物を除く） |
| 質量 | 約 373g（本体のみ） |
| 動作保証環境 | 温度 0〜40℃、湿度 10〜85% |
| 設置 | スタンド付き、壁掛けに対応（ネジは別売）。屋内限定 |
| 認証 | VCCI Class B |
| 保証期間 | 1 年間 |
| 付属品 | スタンド、AC アダプター、LAN ケーブル（0.5m）、取扱説明書（保証書は取扱説明書に記載） |

## VLAN とマルチ SSID

- 製品ページの仕様に、**VLAN（タグ VLAN）の記載はない**。SSID の数の記載もない。非対応と明記した資料は見つけていないが、家庭用のルーターなので、SSID に VLAN を割り当てることはできないと見る。AP（ブリッジ）モードでも、繋いだスイッチのポートの VLAN に入る。
- 計画では、VLAN ごとの SSID は、Omada の AP を導入してから作る（[移行計画](../../operations/roadmap/10-er605-sg2210p-migration-plan.md)）。

## AP（ブリッジ）モードでの動作

| 項目 | 内容 |
| --- | --- |
| 切り替え | 背面の AUTO/MANUAL スイッチを MANUAL にし、ROUTER/AP/WB スイッチを AP にする。前面の ROUTER ランプが消灯する。AUTO のままだと、ルーター機能の入り切りはスイッチに関係なく自動で決まる |
| 使えなくなる機能 | DHCP サーバー、静的 IP マスカレード（アドレス変換）、パケットフィルタ、PPPoE マルチセッション、IP Unnumbered（FAQ の記載。機種ごとの違いに注意） |
| 上流のケーブル | FAQ には、INTERNET ポートに差したケーブルは、モードを切り替えたあともそのままにする（他の LAN ポートへ差し替えなくてよい）とある。WSR-1800AX4P で同じか、取扱説明書で確認する。**2026-11-06 に、[ユーザーマニュアル](https://www.buffalo.jp/s3/guide/wsr-1800ax4p/99/ja/index.html)を確認した**: AP モードの手順（ルーター機能の停止）に、接続するポートの指定は無い。端子の説明は、LAN 端子が「パソコンやハブなどを接続」、INTERNET 端子が「プロバイダーから提供された機器（光回線終端装置やモデムなど）を接続」。機種を限定しない公式 FAQ（[ブリッジモードのポート](https://www.buffalo.jp/support/faq/detail/985.html)）には、ブリッジモードでは INTERNET ポートを含めてすべてのポートが LAN ポートとして動くとある。この機種に限った記述は無い。[物理構成図](../../diagrams/physical-diagram/physical-diagram.png)は、INTERNET ポートで描いた |
| 設定画面 | ブリッジモードの設定画面を開くには、公式は「エアステーション設定ツール」を勧めている（[ダウンロード](https://www.buffalo.jp/support/other/airset.html)、[表示方法](https://www.buffalo.jp/support/faq/detail/129.html)） |
| 設定画面の IP アドレス | このモードでの IP アドレスの割り当て（DHCP か固定か、既定値）は、FAQ に書かれていない。取扱説明書で確認する |

## この構成での使い方との対応

| 論点 | 分かること |
| --- | --- |
| ER605 への交換 | 背面のスイッチで AP モードに切り替える。DHCP サーバーと NAT は止まるので、ER605 が担う |
| SSID と無線設定 | 今の SSID・暗号化を引き継げるか、モード切り替えで設定が残るかは、取扱説明書と実機で確認する（[移行計画](../../operations/roadmap/10-er605-sg2210p-migration-plan.md)の段階 1） |
| ゲストポート | 製品ページに機能の記載はあるが、「一部機能はルーター動作時のみ」という注記もあり、AP モードで使えるかは取扱説明書で確認が要る。使う計画には入れていない |
| プライバシーセパレーター | 無線の端末どうしの通信を遮断する機能。SSID ごとの設定かどうかは取扱説明書で確認する |
| 有線ポート | AP モードでは有線のハブとして働く。現在 Buffalo の LAN ポートに繋いでいるメインディスプレイ（Dell U2725QE）は、段階 2 で SG2210P の p4 に移す。Buffalo は Wi-Fi の入口だけにする |
| 通信の取得 | AP モードにすると、無線の通信もスイッチを通る（[ネットワーク通信の収集・可視化](../../operations/roadmap/06-network-traffic-analysis.md)） |
| 設置 | 屋内限定。動作保証環境は 0〜40℃。壁掛けの金具は別売 |
| 後継機 | 製品ページに、後継モデルとして WSR-3000AX4L の記載がある |
