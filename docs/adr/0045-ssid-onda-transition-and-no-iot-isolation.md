# 0045. Trusted の SSID は WPA2/WPA3 の `Onda` 1 つにし、IoT の SSID では端末どうしを分離しない

- ステータス: 採用（実機への適用は、段階 4 で行う）
- 日付: 2026-11-28
- 置き換えるもの: [ADR-0042](0042-ssid-names-by-vlan.md)（命名規約はこの ADR に引き継ぐ。`Onda-Forte` の例外だけを外す）

## 背景

[ADR-0042](0042-ssid-names-by-vlan.md) では、Trusted に `Onda`（WPA2）と `Onda-Forte`（WPA3）の 2 つの SSID を出すことにしていた。2026-11-28 に、段階 4 のパラメーターシートを書く前に、Omada コントローラー（6.3 系）の SSID の作成画面を開き、項目と選択肢を確かめた（[ADR-0044](0044-verify-parameters-on-screen-before-writing.md)。保存はしていない）。

確かめた結果は次のとおりである。

- 2.4GHz と 5GHz の SSID で選べる WPA モードは、`WPA-PSK`、`WPA2-PSK`、`WPA/WPA2-PSK`、`WPA2-PSK/WPA3-SAE` の 4 つだった。WPA3 だけのモード（`WPA3-SAE`）は無かった。EAP653 は 6GHz に対応しない。このため、WPA3 だけの `Onda-Forte` は作れない。
- 端末どうしの分離を設定する項目は、SSID ごとには無かった。画面の説明では、「ゲストネットワーク」を有効にすると、無線の端末どうしの通信を止める。その結果、AirPlay、Chromecast、画面のミラーリング、無線のプリンターなどが使えなくなることがある。
- ゲストネットワークが、ほかに何を止めるか（プライベートアドレスへの通信など）は、公式の資料で確かめられなかった。もしプライベートアドレスを止めるなら、IoT と Guests の端末が `vm-infra`（`10.77.20.10`）の DNS を引けなくなる。

## 決定

1. Trusted の SSID は `Onda` の 1 つにする。WPA モードは `WPA2-PSK/WPA3-SAE` にし、PMF は「対応」にする。`Onda-Forte` はやめる。
2. SSID の命名規約は、[ADR-0042](0042-ssid-names-by-vlan.md) のものを引き継ぐ。ただし、`Forte` の例外は外す。名前は次のとおりとする。

   | SSID | VLAN | WPA モード | 状態 |
   | --- | --- | --- | --- |
   | `Onda` | 30 Trusted | `WPA2-PSK/WPA3-SAE`（PMF は対応） | Buffalo では WPA2 で使用中。段階 4 で EAP653 に移す |
   | `Onda-IoT` | 50 IoT | `WPA2-PSK`（2.4GHz のみ） | 段階 4 で作る |
   | `Onda-Guest` | 60 Guests | `WPA2-PSK` | 段階 4 で作る |
   | `Onda-Lab` | 40 Lab | 未定 | 無線で繋ぐ検証機が出たときに作る |

3. `Onda-IoT` では、ゲストネットワークを**無効**にする。IoT の中の端末どうしは分離しない。
4. `Onda-Guest` でゲストネットワークを有効にするかは、段階 4 で実機で試してから決める。Guests の端末が `vm-infra` の DNS を引けるかを確かめる（検討中。[ロードマップ 04](../operations/roadmap/04-network-omada-vlan.md#段階-4-apeap)）。

## 理由

- WPA3 だけのモードが選べない以上、`Onda-Forte` を残しても、`Onda` と同じ `WPA2-PSK/WPA3-SAE` になる。同じ VLAN に、同じ働きの SSID を 2 つ出す意味は無い。SSID が 1 つ減れば、ビーコンの電波も減る。
- `WPA2-PSK/WPA3-SAE` なら、WPA3 に対応した端末は WPA3 で繋がり、対応しない端末は WPA2 で繋がる。2026-11-03 に決めた「WPA2 の SSID は無くさない」（WPA3 に対応しない端末があるかもしれないため）も守れる。PMF を「必須」にすると、WPA2 の端末が繋がらなくなるので、「対応」にする。
- 今の IoT の機器（テレビ、SwitchBot Hub 2、Tapo C200）は、互いに通信しなくても動く。テレビを操作するのは Trusted の端末で、カメラを読むのは Servers の Frigate である。どちらも VLAN をまたぐので、ER605 の ACL を通る。分離そのものは害が無いが、Omada で分離をかける方法がゲストネットワークしかなく、その副作用（DNS が引けなくなるかもしれない、AirPlay が制限される）が確かめられていない。確実に動く方を先に選ぶ。

## 受け入れるリスク

- IoT の中では、端末どうしが直接通信できる。同じ SSID の端末どうしの通信は AP の中で折り返し、ER605 を通らないので、ACL が効かない。IoT の機器のどれかが乗っ取られると、同じ IoT のほかの機器（テレビ、SwitchBot Hub 2、カメラ）に届く。今は 3 台で、どれも重要なデータを持たないので、受け入れる。
- AP を採用したあとに、ゲストネットワークを有効にして DNS・Frigate・AirPlay が動くかを試す案と、EAP の ACL などで IoT の中の通信を絞る案を、検討中として[ロードマップ 04](../operations/roadmap/04-network-omada-vlan.md#段階-4-apeap) に残す。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| `Onda-Forte` を `WPA2-PSK/WPA3-SAE` にして、名前だけ残す | `Onda` と同じ働きになり、分ける意味が無い |
| `Onda` を `WPA2-PSK` のまま、`Onda-Forte` をやめる | WPA3 に対応した端末も WPA2 で繋がることになる |
| `Onda-IoT` でゲストネットワークを有効にする | 副作用が確かめられていない。DNS が引けなくなると、IoT の機器が動かない |

## 結果

- 段階 4 では、今 `Onda-Forte` に繋いでいる端末を、`Onda` に繋ぎ直す。`Onda` は Buffalo と同じパスフレーズにするので、`Onda` に繋いでいる端末は、そのまま移れる。
- [第5章 ネットワーク](../architecture/hld/05-network.md#ssid-の命名規約)の表と、Omada のパラメーターシート（[ネットワーク](../architecture/lld/network/omada/network.md#wlan)）に、未適用の値として書いた。

詳細: [ADR-0042](0042-ssid-names-by-vlan.md)、[ADR-0044](0044-verify-parameters-on-screen-before-writing.md)、[ロードマップ 04](../operations/roadmap/04-network-omada-vlan.md#段階-4-apeap)
