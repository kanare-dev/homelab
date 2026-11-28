# 0042. Wi-Fi の SSID は `Onda-<VLAN の名前>` で付ける

- ステータス: 採用（実機への適用は、AP（EAP653）を導入する段階 4 で行う）
- 日付: 2026-11-28

## 背景

2026-11-03 に、運用者は、Buffalo（AP モード）の SSID を `Onda`（WPA2）と `Onda-Forte`（WPA3）に変えた。名前は、`canale` の由来のイタリア語から取った。Onda は波、Forte は強いという意味である。どちらも Trusted（VLAN30）に入る。

2026-11-28 に、運用者は、Omada の AP（EAP653）を購入した。これで、[ロードマップ 04 の段階 4](../operations/roadmap/04-network-omada-vlan.md#段階-4-apeap) で、IoT と Guests の SSID を出せるようになる。ロードマップには、VLAN ごとの SSID を `Onda-iot`、`Onda-guest` にする案が書いてあった。しかし、この案は、`Forte`（先頭が大文字のイタリア語）と書き方がそろっていなかった。また、SSID を足すたびに名前を考えずに済むように、付け方を規約として決めることにした。

## 決定

1. SSID の名前は、共通の `Onda` に、ハイフンと接尾辞を続けた形にする。接尾辞のない `Onda` は、Trusted の SSID とする。
2. 接尾辞には、その SSID が入る VLAN の名前（[第5章 ネットワーク](../architecture/hld/05-network.md#vlan-の構成)の英語の名前）を、表記のまま使う。ただし、Guests は、来客が画面で読む名前なので、単数の `Guest` にする。
3. `Forte` は、Trusted の WPA3 版を表す例外とする。IoT と Guests には、WPA3 版の SSID を作らない（IoT の機器の多くは WPA2 にしか対応しない）。
4. 名前に使う文字は、ASCII の英字、数字、ハイフンに限る。空白は使わない。長さは 32 バイト以内にする。大文字と小文字は、下の表の表記に固定する。
5. Management、Servers、DMZ の SSID は出さない（有線だけにする）。
6. 名前は次のとおりとする。

   | SSID | VLAN | 暗号化 | 状態 |
   | --- | --- | --- | --- |
   | `Onda` | 30 Trusted | WPA2 Personal | 使用中（Buffalo） |
   | `Onda-Forte` | 30 Trusted | WPA3 Personal | 使用中（Buffalo） |
   | `Onda-IoT` | 50 IoT | WPA2 Personal | 段階 4 で作る |
   | `Onda-Guest` | 60 Guests | WPA2 Personal | 段階 4 で作る |
   | `Onda-Lab` | 40 Lab | 未定 | 無線で繋ぐ検証機が出たときに作る |

7. パスフレーズは、SSID ごとに変え、台帳に記録する。リポジトリには書かない。

## 理由

- 同じ SSID を出す AP が増えても、運用で手がかりになるのは名前だけである。接尾辞が VLAN の名前と 1 対 1 で対応していれば、文書と画面を突き合わせるときに迷わない。
- Guest の SSID は、来客が自分の端末で選ぶ。英語の方が伝わりやすい。
- リポジトリは公開しているので、名前を分かりにくくしても、構成を隠す効果はほとんどない。
- `Onda` と `Onda-Forte` は、端末をつなぎ直し済みである。EAP653 で同じ名前とパスフレーズの SSID を出せば、Buffalo から切り替えるときに、端末をつなぎ直さずに済む。そのため、この 2 つの名前は変えずに、規約の中で位置づけた。
- 空白や記号を避けるのは、IoT の機器には、それらを含む SSID に繋げないものがあるからである。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| 接尾辞をイタリア語でそろえる（`Onda-Cose`、`Onda-Ospiti`、`Onda-Prova`） | `Forte` と言葉がそろう一方で、来客に伝わりにくい。文書に VLAN との対応表が必要になる。名前から用途を隠す効果も、リポジトリが公開なので薄い |
| 小文字の英語（`Onda-iot`、`Onda-guest`） | ロードマップに書いていた案である。`Forte` や VLAN の名前の表記と、大文字と小文字がそろわない |
| すべての SSID を VLAN の名前にする（`Onda-Trusted` など） | 使用中の `Onda` と `Onda-Forte` の名前が変わり、全端末をつなぎ直すことになる |

## 結果

- 段階 4 では、EAP653 に、上の表の名前で SSID を作る。`Onda` と `Onda-Forte` は、Buffalo と同じパスフレーズにする。
- SSID を足すときは、この規約で名前を決め、[第5章 ネットワーク](../architecture/hld/05-network.md#ssid-の命名規約)の表を更新する。
- Omada の SSID の設定は GUI でしか変えられないので、文書を先に直し、マージしてから実機を変える（[ADR-0033](0033-docs-first-by-change-type-and-diagram-order.md)）。

詳細: [第5章 ネットワーク](../architecture/hld/05-network.md#ssid-の命名規約)、[ロードマップ 04](../operations/roadmap/04-network-omada-vlan.md)、[ADR-0035](0035-network-device-names-by-role.md)（ネットワーク機器のホスト名）
