# 0043. AP（EAP653）は SG2210P の p3 に繋ぎ、ネイティブを Management にし、IP を `10.77.10.4` にする

- ステータス: 採用（実機への適用は、段階 4 で行う）
- 日付: 2026-11-28

## 背景

2026-11-28 に、運用者は、Omada の AP（EAP653）を購入した。[ロードマップ 04 の段階 4](../operations/roadmap/04-network-omada-vlan.md#段階-4-apeap) で、Buffalo（AP モード）を EAP653 に置き換え、SSID ごとに Trusted・IoT・Guests の VLAN を出す（SSID の名前は [ADR-0042](0042-ssid-names-by-vlan.md)）。

置き換える前に、AP を繋ぐスイッチのポート、ポートの VLAN、AP の IP を決める必要があった。以前の計画では、AP は SG2210P の p7 に繋ぐことになっていた。

## 決定

1. EAP653 は、SG2210P の **p3** に繋ぐ。p3 は今、Buffalo が access（VLAN30）で使っている。Buffalo を外し、同じケーブル（ケーブル B）で EAP653 を繋ぐ。
2. p3 は trunk にする。**ネイティブ（タグなし）を Management（VLAN10）**にし、Trusted（30）、IoT（50）、Guests（60）をタグ付きで通す。AP の管理の通信は、タグなしの Management に流す。
3. AP の IP は **`10.77.10.4`** にする。Management のネットワーク機器の帯（`.2–.9`。[ADR-0025](0025-address-octets-by-role.md)）の、空いている最初の番号である。ホスト名は `ap01` にする（[ADR-0035](0035-network-device-names-by-role.md)）。
4. 将来、Management にネットワーク機器を足すときも、`.5` から順に番号を振る。機器の種類ごとに番号の帯は分けない。

## 理由

- p3 なら、新しいケーブルが要らない。AP も、今の Buffalo の位置から置き始められる。その位置なら、電波がどう届くかが分かっている。p5〜p7 は予備のまま残る。
- ネイティブを Management にすると、工場出荷の状態の AP が、タグなしで Management の緊急用 DHCP プール（`.240–.250`）から IP を受け取る。コントローラー（`vm-omada`、`10.77.10.3`）と同じ L2 にいるので、そのまま見つけて採用できる。採用したあとに、IP を `.4` の固定にする。
- `.3` に `vm-omada` が入っていて、`.2`（スイッチ）と `.4`（AP）の間に、VM が挟まる。しかし、この帯は、機器を管理するネットワークのためのものであり、コントローラーが入っていても役割は外れない。`vm-omada` の IP を変えると、管理している機器がコントローラーを見失い、採用し直すことになる。VMID（`1003`。[ADR-0026](0026-vmid-from-vlan-and-octet.md)）も `.3` から決めている。番号の並びのためにかける手間ではない。
- Management の機器は、1〜2 台ずつしか増えない。種類ごとに番号の帯を分けても、得るものが少ない（Servers 以外の VLAN を連番にしたのと同じ理由。[ADR-0027](0027-servers-octet-bands-and-emergency-dns.md)）。

## 受け入れるリスク

- p3 は、部屋に出ている AP に繋がる。ネイティブが Management なので、AP を外して、そのケーブルに PC を挿すと、Management に入り、緊急用プールから IP を受け取れる。p8（復旧ポート）と違い、スイッチのそばではない場所に、Management の口が出ることになる。今の家の中で、他人がそのケーブルに PC を挿すことは考えにくいので、受け入れる。物理的に触られる心配が出たら、下の代替案 2 に切り替える（検討中として [ロードマップ 04](../operations/roadmap/04-network-omada-vlan.md#段階-4-apeap) に残す）。
- p3 で Buffalo と差し替えるので、Buffalo と EAP653 を並べて動かす時間は作れない。p3 の設定の変更と、機器の差し替えの間は、Wi-Fi が止まる。止まる時間を短くするため、EAP653 の SSID と VLAN は、コントローラーで先に作っておく。戻すときは、p3 を access（VLAN30）に戻し、Buffalo を挿し直す。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| p7 に繋ぐ（以前の計画） | 新しいケーブルが要る。Buffalo と並べて動かせる利点はあるが、同じ SSID を 2 台で出す時間に、端末がどちらに繋がるかが定まらない |
| 1. ネイティブを `Blackhole` にし、AP の管理 VLAN をタグ付きの 10 にする | ケーブルに何を挿しても、どこにも入れない。しかし、工場出荷の AP はタグなしで通信するので、そのままでは採用できない。いったんネイティブを Management にして採用し、AP の管理 VLAN を 10 にしてから、ポートを `Blackhole` に変える 2 段階になる。順番を間違えると、AP を見失い、初期化からやり直すことになる。物理的に触られる心配が出たときの強化策として残す |
| 2. ネイティブを Trusted（30）にし、管理をタグ付きの 10 にする | 工場出荷の AP が Trusted で IP を受け取り、コントローラーを見つけるのに Trusted → Management の通信が要る。[通信ポリシー](../architecture/hld/05-network.md#通信ポリシー)に反する |
| コントローラーを `.10–.49` に移し、`.3` を AP にする | 管理している機器を採用し直すことになる。番号の並びのためにかける手間ではない |
| 種類ごとに番号の帯を決める（スイッチ、AP など） | 機器が少ないので、帯を分ける意味が薄い |

## 結果

- 段階 4 の前に、p3 と AP の設定値を、Omada のパラメーターシートに書く。書く前に、画面で項目と選択肢を確かめる（[ADR-0044](0044-verify-parameters-on-screen-before-writing.md)）。
- 実機を変えたら、[IP アドレス一覧](../architecture/lld/network/ip-addresses.md)、`ap01.lab.kanare.dev` の A レコード（[ADR-0036](0036-a-record-for-every-fixed-ip-host.md)。今は Buffalo の `10.77.30.50` を指す）、as-is の構成図、物理構成図を直す。

詳細: [ロードマップ 04](../operations/roadmap/04-network-omada-vlan.md#段階-4-apeap)、[EAP653 の資料](../architecture/lld/hardware/eap653.md)
