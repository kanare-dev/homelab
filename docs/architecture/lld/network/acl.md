# ACL の名前と説明の付け方

この文書では、Omada のゲートウェイの ACL（LAN → LAN）に作るルールについて、名前と説明の付け方を決める。ルールの元になる許可表は、[第5章 ネットワーク](../../hld/05-network.md#通信ポリシー)にある。**リハーサル（[Runbook](../../../operations/runbooks/22-network-stage-3-rehearsal.md)）でも、本番（[段階 3 の Runbook](../../../operations/runbooks/21-network-cutover-stage-3.md)）でも、同じ書き方にする。**

- **評価は上から順**。順序が分かるように、**名前の頭に番号を付ける**（間を空けて振り、あとで間に足せるようにする）。
  - `1xx`: 個別の許可（許可表の「許可」「のみ」の行）
  - `9xx`: 末尾の拒否ルール。**必ず最後に置き、VLAN ごとに 1 件だけ作る。** 番号は、9 に VLAN ID の十の位を続けた `910`〜`970` にする。Lab、Guests、IoT、DMZ から他の VLAN への通信を拒否して隔離するときも、このルールを使う
- **名前**: `<番号>-<送信元>-to-<宛先>[-<内容>]`。英小文字、数字、ハイフンだけにする（例: `150-trusted-to-servers`）。
- **説明**: `送信元 → 宛先 : 動作（内容）（根拠）` を 1 行にする。**何のためのルールか**と、**根拠の文書**（この「通信ポリシー」など）を添える。
- **検証用のルール**（リハーサル）は、名前の頭に `rh-`、説明の頭に `[リハーサル]` を付ける（例: `rh-010-trusted-to-lan`）。リハーサルのあとに、一覧から探して、無効にする。本番のルールには、この印を付けない。
- **種類に「すべて（Any）」の選択肢はなく、宛先は、送信元に選んだネットワーク以外からしか選べない**（Controller モード。公式の資料にも「すべて」は無い）。「ネットワーク」は選んだネットワークに一致し、「!ネットワーク」は選んだネットワーク**以外のすべて**に一致する。**末尾の拒否（`9xx`）は、VLAN ごとに 1 件**作る。送信元 = ネットワーク（その VLAN）、宛先 = !ネットワーク（その VLAN）。新しい VLAN を足しても、既存の `9xx` に自動で含まれ、足す VLAN の `9xx` を 1 件作ればよい。ルールに一致しない通信は、暗黙の許可（permit）になる。インターネット宛が拒否されないことは、リハーサルで確認した（2026-11-06。VLAN50 から `ping 1.1.1.1` が通り、`192.168.11.x` 宛は拒否された）。
- **ゲートウェイ自身（`10.77.<VLAN>.1`）宛の通信は、この ACL（LAN → LAN）の対象外**で、他の VLAN からも届く（リハーサルで、VLAN50 から `10.77.30.1` に ping が通ることを確認した）。ゲートウェイの管理画面などを遮断したいときは、宛先の種類に「ゲートウェイ管理ページ」を使う別のルールが要る（Controller モードの ACL の、宛先だけの選択肢。ER605 は、採用すると本体の画面を使えないので、優先度は低い）。
- 秘密の値と、機器の MAC アドレスは書かない。
- 入力できる文字数と、日本語が使えるかは、Omada 6.3 で未確認。保存して、表示を見て確かめる。切れるなら、短くする。
- Trusted → Servers・Lab（`150`、`151`）は、プロトコルもポートも限らない。ポートの絞り込みは、各ホストの UFW を正とする（[ADR-0034](../../../adr/0034-acl-for-vlan-boundaries-ufw-for-ports.md)）。ACL のルールは、VLAN をまたぐ組み合わせが増えるときと、Management への通信を増やすときだけ足す。
- **未確認（Omada 6.3）**: プロトコルに ICMP だけを選べるか（`156-trusted-to-mgmt-icmp`）。IP グループに範囲（`10.77.10.2–.9`）を書けるか。書けなければ、`10.77.10.0/29` と `10.77.10.8/31` の 2 件に分ける（`10.77.10.0/29` には、ゲートウェイの `.1` と `vm-omada` の `.3` も含まれる。`.1` は ACL の対象外で、`vm-omada` の 80/443 は待ち受けていないので、実害はない）。ACL を絞る日の前に、画面で確かめる。
- Management から外への通信は、ACL の末尾の拒否（`910`）では止まらない（宛先がインターネットのため）。Management のホストの DNS（ルーター）と NTP（インターネット）は、この ACL の影響を受けない。

本番のルールの例を、次の表に示す（2026-11-26 に、[通信ポリシー](../../hld/05-network.md#通信ポリシー)の見直しと [ADR-0034](../../../adr/0034-acl-for-vlan-boundaries-ufw-for-ports.md) に合わせて改めた）。許可表の行ごとに、同じ形で作る。送信元・宛先が 1 台のホストや帯のときは、IP グループ（または IP-Port グループ）を作って指定する。ポートと送信元の組み合わせが違うものは、ルールを分ける。

| 名前 | 説明 |
| --- | --- |
| `130-servers-to-mgmt-caddy` | `Servers → Management : vm-infra から Omada(8043)・Proxmox(8006) の管理画面のみ許可（個別の許可）` |
| `131-servers-to-mgmt-metrics` | `Servers → Management : vm-monitoring から Proxmox・vm-omada の node_exporter(9100) のみ許可（個別の許可）` |
| `140-servers-to-lab-ssh` | `Servers → Lab : vm-infra から SSH/mosh/Web を許可。Tailscale 経由の vm-dev 用（個別の許可）` |
| `141-servers-to-lab-metrics` | `Servers → Lab : vm-monitoring から node_exporter(9100) のみ許可（個別の許可）` |
| `150-trusted-to-servers` | `Trusted → Servers : 許可。ポートは各ホストの UFW で絞る（ADR-0034）` |
| `151-trusted-to-lab` | `Trusted → Lab : 許可。ポートは各ホストの UFW で絞る（ADR-0034）` |
| `153-trusted-to-mgmt` | `Trusted → Management : Proxmox の 8006/22、vm-omada の 22 を許可（個別の許可）` |
| `154-trusted-to-mgmt-devices` | `Trusted → Management : 機器の帯(.2-.9)の 80/443 を許可。単体動作に戻したときの本体の画面用（個別の許可）` |
| `156-trusted-to-mgmt-icmp` | `Trusted → Management : ICMP を許可。切り分け用（個別の許可）` |
| `160-trusted-to-iot` | `Trusted → IoT : 許可。AirPlay・Cast の制御用（通信ポリシー）` |
| `170-lab-to-servers-dns` | `Lab → Servers : DNS(53) を vm-infra へのみ許可（個別の許可）` |
| `171-iot-to-servers-dns` | `IoT → Servers : DNS(53) を vm-infra へのみ許可（個別の許可）` |
| `172-guests-to-servers-dns` | `Guests → Servers : DNS(53) を vm-infra へのみ許可（個別の許可）` |
| `910-deny-from-mgmt` | `Management → 他 VLAN : 拒否（末尾。Management から他の VLAN への許可は無い）（通信ポリシー）` |
| `920-deny-from-servers` | `Servers → 他 VLAN : 拒否（末尾）（通信ポリシー）` |
| `930-deny-from-trusted` | `Trusted → 他 VLAN : 拒否（末尾）（通信ポリシー）` |
| `940-deny-from-lab` | `Lab → 他 VLAN : 拒否（隔離。DNS などの許可は 1xx で先に通す）（通信ポリシー）` |
| `950-deny-from-iot` | `IoT → 他 VLAN : 拒否（隔離）（通信ポリシー）` |
| `960-deny-from-guests` | `Guests → 他 VLAN : 拒否（隔離）（通信ポリシー）` |
| `970-deny-from-dmz` | `DMZ → 他 VLAN : 拒否（隔離）（通信ポリシー）` |
