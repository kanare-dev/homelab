# 段階 4: Buffalo を EAP653 に置き換え、SSID ごとに VLAN を出す（2026-11）

[Omada 導入・VLAN 化の段階 4](../roadmap/04-network-omada-vlan.md#段階-4-apeap) の手順書である。SG2210P の p3 に繋いでいる Buffalo（AP モード）を外し、EAP653 を繋いで、Omada コントローラーに採用する。この手順書では、Trusted の `Onda` を EAP653 に移すところまでを行う。IoT への機器の移動（テレビ、SwitchBot Hub 2、Tapo C200）と、mDNS の中継の有効化は、落ち着いてから別の日に行う。

| 変更 | 設定値（パラメーターシート） | 判断 |
| --- | --- | --- |
| SSID を 3 つ作る（`Onda`、`Onda-IoT`、`Onda-Guest`） | [ネットワーク > SSID](../../architecture/lld/network/omada/network.md#ssid未適用) | [ADR-0045](../../adr/0045-ssid-onda-transition-and-no-iot-isolation.md) |
| SG2210P の p3 を trunk にする（ネイティブ Management、タグ 30・50・60） | [SG2210P > ポート](../../architecture/lld/network/omada/device-sw01.md#ポート) | [ADR-0043](../../adr/0043-ap-on-p3-native-management.md) |
| EAP653 を採用し、`ap01`・`10.77.10.4` にする | 採用したあとに画面で確かめて書く（下の手順 4） | [ADR-0043](../../adr/0043-ap-on-p3-native-management.md) |

- **文書が先**の変更である（Omada の GUI と VLAN。[ADR-0033](../../adr/0033-docs-first-by-change-type-and-diagram-order.md)）。この手順書の PR をマージしてから、実機を変える。
- 手順 2 から手順 3 の途中まで、Wi-Fi が止まる。止まる時間は、AP の採用とプロビジョニングにかかる時間で、数分の見込み（未確認）。
- SSID のセキュリティキー（パスフレーズ）は、**運用者が入力する**。Claude は入力しない。台帳の値を `pbcopy` でクリップボードに入れて貼り、画面と会話に値を出さない。

## 役割

| 作業 | 誰が |
| --- | --- |
| Omada の画面の操作（セキュリティキーの入力を除く） | Claude（Chrome）。保存の前に、入力した値を運用者に見せて確かめる |
| セキュリティキーの入力 | 運用者 |
| Buffalo と EAP653 の差し替え（ケーブルの抜き差し） | 運用者 |
| 端末の繋ぎ直し、電波の確認 | 運用者 |

## 0. 準備

1. この手順書の PR がマージされている。
2. Mac を有線で繋ぐ（ディスプレイ経由。SG2210P の p4、Trusted）。Wi-Fi が止まっても、作業を続けられるようにする。
3. Omada のバックアップ（設定とサイト）を取り、iCloud Drive に日付つきで保存する。
4. Buffalo の設定のバックアップが、今の状態で取れているかを確かめる（無ければ取る。[WSR-1800AX4P の設定](../../architecture/lld/network/wsr-1800ax4p.md)）。戻すときに使う。
5. 台帳に、`Onda`（Buffalo と同じ値）、`Onda-IoT`、`Onda-Guest` のパスフレーズがあることを確かめる。`Onda-IoT` と `Onda-Guest` の値は、まだ無ければ新しく作って台帳に足す（チャットに貼らない）。
6. 今の状態を控える。
   - `make omada-export` を流し、`git status` で、書き出しに差分が無いことを確かめる。
   - Prometheus の全ターゲットが `up`、アラートが `Watchdog` だけ。
   - EAP653 の箱から本体と取り付けキットを出しておく。PoE で給電するので、電源アダプターは要らない。

## 1. SSID を 3 つ作る（Wi-Fi は止まらない）

ネットワーク設定 > WLAN > SSID > 「SSID を追加」で、[パラメーターシート](../../architecture/lld/network/omada/network.md#ssid未適用)の表のとおりに、`Onda`、`Onda-IoT`、`Onda-Guest` を作る。AP がまだ無いので、作っても電波は出ない。

1. Claude が、セキュリティキー以外の項目を入力する。
2. 運用者が、セキュリティキーを貼る。
3. Claude が、入力した値をスクリーンショットで運用者に見せ、運用者が確かめてから「適用」を押す。

確認:

- [ ] SSID の一覧に 3 つが出る（VLAN の列が 30、50、60）
- [ ] `rtr01` と `sw01` が「接続しました」のまま

## 2. Buffalo を外し、p3 を trunk にする（ここから Wi-Fi が止まる）

**順番を守る。** Buffalo を繋いだまま p3 を trunk にすると、Buffalo がネイティブの Management をそのまま無線に流し、Wi-Fi の端末が Management に入ってしまう（Management の緊急用プール `.240–.250` から IP を受け取る）。

1. 運用者が、Buffalo のケーブル（ケーブル B。p3 側に繋がっている）を、**Buffalo 側で**抜く。Buffalo の電源も切る。
2. Claude が、デバイス > `sw01` > ポート > ポート 3 を編集で、次のとおりにする。
   - 「VLAN設定」: カスタム
   - ネイティブネットワーク: `Management(Default)(10)`
   - ネットワークタグ設定: カスタム
   - タグ付きネットワーク: Trusted(30)、IoT(50)、Guests(60)
   - 「ポート設定」は変えない（PoE は有効のまま）
3. Claude が、入力した値を運用者に見せ、運用者が確かめてから「適用」を押す。

確認:

- [ ] ポートの一覧で、p3 のタイプが「トランク」、ネイティブネットワークが `Management(Default)(10)`
- [ ] `sw01` が「接続しました」のまま
- [ ] Mac（有線）からインターネットに出られる

## 3. EAP653 を繋ぎ、採用する

1. 運用者が、ケーブル B を EAP653 の LAN ポートに挿す。PoE で電源が入る。置き場所は、まず今の Buffalo の位置にする（天井や壁への取り付けは、電波を見てから）。
2. EAP653 が起動し、Management の緊急用プール（`10.77.10.240`〜`.250`）から IP を受け取り、コントローラーに「保留中」（採用待ち）として出るのを待つ。数分かかる見込み。
3. Claude が、デバイスの一覧で EAP653 を「採用」する。
4. 採用とプロビジョニングが終わり、「接続しました」になるのを待つ。手順 1 で作った SSID が、ここで配られる。

確認:

- [ ] EAP653 が「接続しました」
- [ ] デバイスの一覧のモデル欄に、ハードウェアの版が出る（[EAP653 の資料](../../architecture/lld/hardware/eap653.md)の「未確認」を埋める）
- [ ] 運用者の端末（iPhone など）から `Onda` が見え、繋ぎ直さずに繋がる
- [ ] `Onda` の端末が `10.77.30.x` を受け取り、インターネットに出られる

**`EAP653` が「保留中」に出てこない場合**: p3 の設定（ネイティブが Management か）と、PoE の給電（EAP653 の LED が点くか）を確かめる。15 分待っても出なければ、下の「戻し方」で Buffalo に戻し、記録を残してから日を改める。

## 4. AP の名前と IP を決める

採用したあとに、AP の設定の画面が出る。**先に画面で項目と選択肢を確かめ、パラメーターシートに書いてから保存する**（[ADR-0044](../../adr/0044-verify-parameters-on-screen-before-writing.md)）。この会話のなかで、パラメーターシートの差分を運用者に見せて確かめる。PR は、手順 6 でまとめる。

決めている値（[ADR-0043](../../adr/0043-ap-on-p3-native-management.md)）:

| 項目 | 値 | 画面の場所と項目名 |
| --- | --- | --- |
| デバイス名 | `ap01` | 未確認（デバイスの詳細のデバイス名の編集の見込み） |
| IP | 静的。`10.77.10.4/24`、ゲートウェイ `10.77.10.1`、DNS `10.77.10.1` | 未確認（AP の「設定」タブの IP 設定の見込み）。DNS は `sw01` と同じにする |
| 管理 VLAN | 無効（タグなしの Management を使う） | 未確認 |

1. Claude が、画面で上の項目を探し、選べる値を確かめる（保存しない）。
2. パラメーターシート（新しく `omada/device-ap01.md` を作る見込み）に値を書き、運用者が確かめる。
3. Claude が、デバイス名と IP を設定して保存する。IP を変えると、AP がいったん切れて、`10.77.10.4` で戻る。

確認:

- [ ] EAP653 が `ap01`、`10.77.10.4` で「接続しました」
- [ ] Mac から `ping 10.77.10.4` が通る（Trusted → Management の ICMP は許可している。[通信ポリシー](../../architecture/hld/05-network.md#個別の許可)）
- [ ] `Onda` の端末が繋がったまま

## 5. 端末を繋ぎ直す

1. 運用者が、今 `Onda-Forte` に繋いでいた端末を、`Onda` に繋ぎ直す。
2. WPA3 に対応した端末が WPA3 で繋がっているかを、Omada のクライアントの一覧で見る（表示があれば）。

確認:

- [ ] 普段使う Wi-Fi の端末が、すべて `Onda` に繋がる
- [ ] テレビの AirPlay・Cast が、今までどおり動く（テレビはまだ Trusted にいる）
- [ ] Prometheus の全ターゲットが `up`、アラートが `Watchdog` だけ

## 6. 書き出しと文書の仕上げ

1. `make omada-export` を流し、`git diff docs/architecture/lld/network/omada/snapshot/` で、次の差分だけが出ることを確かめる。
   - `network.json`: SSID が 3 つ増える。
   - `device-sw01.json`: p3 のネイティブが Management、タグがカスタム（30、50、60）になる。
   - `devices.json`: EAP653（`ap01`、`10.77.10.4`）が増える。`device-ap01.json` が増える（書き出しのスクリプトが AP に対応していれば。対応していなければ、`tools/omada-export.py` を直す）。

   予想と違う差分が出たら、その値が何かを確かめてから、パラメーターシートに書く。
2. パラメーターシートの「未適用」を外し、SSID の表に Open API のキーを足す。[変更履歴](../../architecture/lld/network/omada-controller.md#変更履歴)に 1 行足す。
3. ほかの文書とコードを直す。
   - [IP アドレス一覧](../../architecture/lld/network/ip-addresses.md): `ap01` を `10.77.10.4`（EAP653）にし、Buffalo の行を外す。
   - `ansible/inventory/group_vars/infra/vars.yml` の `dns_records`: `ap01` を `10.77.10.4` にする。`make setup-infra` で `vm-infra` に配り、`dig ap01.lab.kanare.dev` で確かめる。
   - [第5章 ネットワーク](../../architecture/hld/05-network.md#配置の方針)の「Wi-Fi は、Buffalo（AP モード）が出す…」の段落を、EAP653 に書き換える。
   - [WSR-1800AX4P の設定](../../architecture/lld/network/wsr-1800ax4p.md)と[機器の一覧](../../architecture/lld/hardware/README.md): Buffalo を退役（予備）にする。
   - as-is の構成図と物理構成図: p3 の先を EAP653 にする。
4. 書き出し、文書、コード、図を、1 つの PR にまとめる。
5. Omada のバックアップを取り直し、iCloud Drive に保存する。

## 戻し方

- **手順 1 のあと**: SSID を消せば元に戻る。AP が無いので、残しておいても害は無い。
- **手順 2 以降（Wi-Fi が使えない、AP が採用できない）**:
  1. EAP653 からケーブル B を抜く。
  2. p3 を編集し、「VLAN設定」を「プロファイルに従う」（`access-trusted`。ネイティブ Trusted(30)、タグはすべてブロック）に戻して適用する。**Buffalo を挿す前に戻す。**
  3. Buffalo の電源を入れ、ケーブル B を Buffalo の INTERNET ポートに挿す。`Onda` と `Onda-Forte` が、今までどおり出る。
  4. コントローラーで EAP653 を「忘れる」かは、そのときに決める。
- **コントローラーや機器に入れない**: Mac を復旧ポート（SG2210P の p8）に繋ぎ、`https://10.77.10.3:8043` から入る。それでも戻せなければ、手順 0 のバックアップから戻す。

## 実施の記録

（未実施）
