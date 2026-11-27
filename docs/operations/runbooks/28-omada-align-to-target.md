# Omada の設定を、あるべき姿にそろえる（2026-11）

パラメーターシートを作ったとき（2026-11-28）に、あるべき姿と違う設定が 3 つ見つかった。この手順書で、実機をパラメーターシートの値にそろえる。

| 変更 | パラメーターシート | 影響 |
| --- | --- | --- |
| 1. WAN の IGMP プロキシを無効にする | [ネットワーク](../../architecture/lld/network/omada/network.md#そのほかのサービス) | 無い見込み（IPTV を使う機器が無い） |
| 2. SG2210P の SFP ポート（p9・p10）を塞ぐ | [SG2210P](../../architecture/lld/network/omada/device-sw01.md#ポート) | 無い見込み（何も挿していない） |
| 3. LAN の Blackhole を、ゲートウェイを持たない VLAN にする | [ネットワーク](../../architecture/lld/network/omada/network.md#lan) | ER605 の設定が配り直される。短い切断があるかもしれない（未確認） |

- **文書が先**の変更である（VLAN とルーター。[ADR-0033](../../adr/0033-docs-first-by-change-type-and-diagram-order.md)）。パラメーターシートの PR をマージしてから、実機を変える。
- 通信の許可と拒否は変えない。`make acl-check` の 35 件は、前後で同じ結果になるはずである。

## 0. 準備

1. Omada のバックアップ（設定とサイト）を取り、iCloud Drive に日付つきで保存する。
2. Mac の Tailscale を止める（`tailscale down`）。`make acl-check` は、Tailscale が経路を持っていると止まる。
3. 今の状態を控える。
   - `make omada-export` を流し、`git status` で書き出しに差分が無いことを確かめる（実機とパラメーターシートの「未適用」以外が一致している）。
   - `make acl-check` が 35 件すべて PASS する。
   - Prometheus の全ターゲットが `up`、アラートが `Watchdog` だけ。

## 1. IGMP プロキシを無効にする

画面で、IGMP（IPTV）の設定を開き、IGMP を無効にして保存する。画面の場所は未確認である（API は `setting/service/igmp`。ネットワーク設定 > インターネットの近くの見込み）。

確認: [ ] インターネットに出られる（`curl -sI https://example.com`）　[ ] Prometheus の `internet-cloudflare`・`internet-google` が `up`

## 2. SFP ポート（p9・p10）を塞ぐ

デバイス > `sw01` > ポートで、p9 と p10 を、p5〜p7 と同じ設定にする。

- 「VLAN設定」: カスタム
- ネイティブネットワーク: `Blackhole`
- ネットワークタグ設定: すべてブロック

確認: [ ] `sw01` が「接続しました」のまま　[ ] p1〜p8 の設定が変わっていない（手順 4 の書き出しで確かめる）

## 3. Blackhole を、ゲートウェイを持たない VLAN にする

ネットワーク設定 > LAN で、`Blackhole` を編集する。

1. 「DHCPサーバーデバイス」を「無し」にする。IP アドレスの欄が消えるかを見る（消えなければ、手順を止めて記録する）。
2. 「次へ」で「デバイスポートを選択」に進み、`rtr01` の「すべて選択解除」を押す。`sw01` の選択は変えない。
3. 「次へ」で確認の画面に進み、保存する。

ER605 の設定が配り直される。過去に LAN を変えたときは、ER605 の再接続に約 2 分かかった（2026-11-19）。

確認:

- [ ] `rtr01` と `sw01` が「接続しました」に戻る
- [ ] `make acl-check` が 35 件すべて PASS する
- [ ] Prometheus の全ターゲットが `up`、アラートが `Watchdog` だけ
- [ ] Mac（Trusted）、`vm-dev`（Lab）がインターネットに出られる

## 4. 書き出して確かめる

`make omada-export` を流し、`git diff docs/architecture/lld/network/omada/snapshot/` で、次の差分だけが出ることを確かめる。

- `network.json`: `igmp.enable` が `false` になる。`Blackhole` の `gatewaySubnet` と `interfaceIds` が無くなる（または空になる）。ほかのキー（`purpose` など）も変わるかもしれない。変わったものは、下の記録に書く。
- `device-sw01.json`: p9・p10 の `nativeNetworkId` が `Blackhole`、`networkTagsSetting` が `1` になる。`vlan-membership` で、Management のネイティブと、20〜70・999 のタグ付きから 9・10 が外れ、Blackhole のネイティブに 9・10 が入る。

予想と違う差分が出たら、その値が何かを確かめてから、パラメーターシートに書く。

## 5. 仕上げ

1. パラメーターシートの「未適用」を外し、[変更履歴](../../architecture/lld/network/omada-controller.md#変更履歴)に 1 行足す。書き出しと一緒にコミットする。
2. Omada のバックアップを取り直し、iCloud Drive に保存する。
3. Mac の Tailscale を戻す（`tailscale up`）。

## 戻し方

- **1・2**: 画面で、元の値（IGMP は有効、p9・p10 はネイティブ Management・タグをすべて許可）に戻す。
- **3**: `Blackhole` を編集し、「DHCPサーバーデバイス」を `rtr01`、IP を `10.77.99.1/24` にして、`rtr01` の LAN 側のポート 4 つを選び直す。
- **コントローラーや機器に入れない**: Mac を復旧ポート（SG2210P の p8）に繋ぎ、`https://10.77.10.3:8043` から入る。それでも戻せなければ、手順 0 のバックアップから戻す。

## 実施の記録

（未実施）
