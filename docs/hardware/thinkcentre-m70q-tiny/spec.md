# Lenovo ThinkCentre M70q Tiny

Proxmox ホスト（`pve`、`192.168.11.10`）のミニ PC。全 VM がこの 1 台に載る。公式の資料へのリンクと、Lenovo の仕様書（PSREF）の仕様をまとめる。このホストの設定値は [settings.md](settings.md)、使い方は[インフラ構成](../../architecture/02-infrastructure.md)、ネットワークの接続は[VLAN 設計](../../architecture/08-vlan-design.md)、ラックへの収納は[10 インチラック](../rack-10inch/README.md)にある。

> [!NOTE]
> 確認日は 2026-11-03。仕様は Lenovo PSREF の ThinkCentre M70q（2023-09-27 版）による。PSREF は M70q のすべての構成をまとめた資料で、搭載できる部品の候補を載せている。**この機体の構成は、下の「この機体」にまとめた。** マシンタイプは 11DU（SKU は `SG6P00`）。PSREF は、構成ごとの違いをマシンタイプ別には載せていないので、この機体の部品は PSREF の表と突き合わせていない。

## 公式の資料

| 資料 | リンク |
| --- | --- |
| 仕様書（PSREF、PDF） | [ThinkCentre_M70q_Spec.PDF](https://psref.lenovo.com/syspool/Sys/PDF/ThinkCentre/ThinkCentre_M70q/ThinkCentre_M70q_Spec.PDF)（2023-09-27 版、9 ページ） |
| 仕様書（PSREF、Web） | [ThinkCentre M70q Gen 1](https://psref.lenovo.com/Product/ThinkCentre/ThinkCentre_M70q_Gen_1) |

PSREF の Web ページは、表示にブラウザーが要る（取得は PDF のほうが確実）。

## この機体

構成の正は、[インフラ構成](../../architecture/02-infrastructure.md)。ここは PSREF と突き合わせるための要約。

| 項目 | 内容 | PSREF との関係 |
| --- | --- | --- |
| CPU | Intel Core i5-10400T（6 コア 12 スレッド） | PSREF の候補に載っている。基本 2.0GHz、最大 3.6GHz、キャッシュ 12MB、メモリは DDR4-2666 まで |
| メモリ | 24GB（8GB + 16GB、DDR4-3200） | PSREF の注記: 搭載メモリの定格は 3200MHz でも、CPU の対応により 2666MHz か 2933MHz で動く。i5-10400T は DDR4-2666 まで |
| ストレージ | 256GB NVMe SSD 1 枚 | M.2 スロットの NVMe |
| NIC | 1 つ（Intel I219、ドライバ `e1000e`） | PSREF: Gigabit Ethernet、Intel Ethernet Connection I219-V、RJ-45 × 1、Wake-on-LAN 対応 |
| マシンタイプ | 11DU（SKU は `SG6P00`） | ホストで `dmidecode -s system-product-name` を実行すると `11DUSG6P00`、`dmidecode -s system-version` は `ThinkCentre M70q`（2026-11-03 に確認）。先頭の 4 文字がマシンタイプ |

## 仕様（PSREF）

### 性能

| 項目 | 内容 |
| --- | --- |
| プロセッサー（候補） | Celeron G5900T / G5905T、Pentium Gold G6400T / G6500T、Core i3-10100T / 10300T、i5-10400T / 10500T / 10600T、i7-10700T、i9-10900T |
| i5-10400T | 6 コア 12 スレッド、基本 2.0GHz、最大 3.6GHz、キャッシュ 12MB、メモリ DDR4-2666、内蔵グラフィックス Intel UHD Graphics 630 |
| チップセット | Intel H470 |
| メモリ | DDR4 SO-DIMM スロット × 2（デュアルチャネル）。最大 64GB（Lenovo の現行のメモリでの測定値、DDR4-2933） |
| ストレージ | 最大 2 台: 2.5 インチ HDD × 1（最大 1TB、SATA 6Gb/s、7.2K rpm）+ M.2 SSD × 1（最大 2TB）。M.2 は 2242 / 2280、PCIe 3.0 x2 または x4 の NVMe。Intel Optane Memory は任意。RAID は非対応 |
| 光学ドライブ / カードリーダー | USB 外付けの DVD（別売）/ なし |
| グラフィックス出力 | HDMI × 1、DisplayPort × 1、任意の追加ポート × 1（VGA / 2 つ目の DP / 2 つ目の HDMI / USB-C）。最大 3 画面 |
| オーディオ | HD Audio（Realtek ALC233VB または ALC897Q）、スピーカー 1.5W × 1 |

### 接続

| 項目 | 内容 |
| --- | --- |
| 有線 LAN | Gigabit Ethernet、Intel I219-V、RJ-45 × 1。増設用の LAN は用意されていない |
| 無線 | M.2 カード（Realtek RTL8822CE、Intel Wireless-AC 9462 / 9560、Intel Wi-Fi 6 AX201）または無し |
| 前面ポート | USB-C 3.2 Gen 1 × 1、USB 3.2 Gen 2 × 1（常時給電、急速充電）、ヘッドホン / マイクのコンボジャック × 1 |
| 背面ポート | USB 3.2 Gen 2 × 1、USB 3.2 Gen 1 × 3、HDMI × 1、DisplayPort × 1、Ethernet（RJ-45）× 1 |
| 任意の背面ポート | ポート 1（VGA / 2 つ目の DP / 2 つ目の HDMI / シリアル / DP 機能付き USB-C のどれか）、ポート 2（シリアル）。2 つを使って DP を 2 つ、または USB 3.2 Gen 1 を 2 つにもできる |
| 拡張スロット | M.2 スロット × 2（WLAN 用 1、SSD 用 1）。PCIe スロットはない |

### 電源・形状・環境

| 項目 | 内容 |
| --- | --- |
| 電源 | 外付けアダプター 65 W / 90 W / 135 W（効率 89%、自動切り替え）。構成による |
| 形状 | Tiny（1L） |
| 寸法（幅 × 奥行 × 高さ） | 179 × 183 × 34.5 / 37 mm（ゴム足つき）。VESA マウント + 光学ドライブ箱つきは 187 × 183.8 × 66.5 mm |
| 重量 | 約 1.25 kg（本体のみ） |
| ベイ | 2.5 インチ × 1 |
| 設置 | 縦置きスタンド（任意）、VESA マウント（75mm / 100mm、任意） |
| 動作環境 | 温度 5 ℃〜35 ℃、湿度 20〜80%、高度 0〜3048 m |
| 保管環境 | 温度 -40 ℃〜60 ℃、湿度 10〜90% |
| セキュリティ | ディスクリート TPM 2.0、ケンジントンロック、筐体侵入スイッチ、BIOS パスワード、USB ポートの無効化 |
| 管理 | vPro ではない |
| 認証 | ENERGY STAR 8.0、ErP Lot 3、RoHS、TCO Certified。MIL-STD-810H の試験に合格 |
| 保証 | 構成による（1 年または 3 年） |
| 任意の部品 | ダストフィルター、電源アダプターのケージ。工具なしで筐体を開けられる構成がある |

## このホームラボでの使い方との対応

| 論点 | 分かること |
| --- | --- |
| NIC の増設 | PCIe スロットがなく、増設用の LAN もない（M.2 は WLAN 用と SSD 用）。OPNsense 用には別の PC が要る（[OPNsense 導入](../../operations/roadmap/08-network-opnsense.md)）。通信の取得でも、Proxmox に USB NIC を足さない方針（[ネットワーク通信の収集・可視化](../../operations/roadmap/06-network-traffic-analysis.md)） |
| 単一の NIC と VLAN | NIC は 1 つで、SG2210P の p2 を trunk にして使う（[移行計画](../../operations/roadmap/10-er605-sg2210p-migration-plan.md)）。この NIC（I219）では `e1000e` の送信停止が起きた（[INC-2026-10-25](../../operations/incidents/2026-10-25-nic-hardware-unit-hang.md)）。ポートを付け替えるたびに再発を確認する |
| ストレージの余地 | M.2 の NVMe は 1 枚で、2.5 インチ HDD のベイが 1 つある（この機体で空いているかは未確認）。冗長化はしない方針（[システム概要](../../architecture/01-overview.md#前提と制約)） |
| メモリの速度 | 3200MHz のメモリを載せていても、i5-10400T では 2666MHz で動く（PSREF の注記） |
| ラックへの収納 | 本体の幅は 179mm。10 インチラックに収まる（[10 インチラック](../rack-10inch/README.md)）。動作温度は 35 ℃ まで。ラックの中で熱がこもらないようにする |
| 電源 | 外付けアダプター。ラックに電源タップ用の棚は無い（[ラックの導入](../../operations/roadmap/09-rack.md)） |
