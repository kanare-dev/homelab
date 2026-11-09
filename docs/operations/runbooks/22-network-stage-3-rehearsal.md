# 段階 3 のリハーサル（VLAN 化の前に、実機で確かめる）

[段階 3 の当日の作業](21-network-cutover-stage-3.md)の前に、**当日に初めて試すものをなくす**ためのリハーサル。計画の「3-A. 準備」のうち、実機で確かめる項目を、手順にした。**既存のホスト（Proxmox、VM、Wi-Fi の端末）は、動かさない。IP も付け替えない。**

- 手順の根拠は[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)の「3-A. 準備」と「3-B. 設定の対応表」。結果は、計画の「3-A」のチェックボックスと、[段階 3 の Runbook](21-network-cutover-stage-3.md)に反映する。
- 秘密の値と、機器の MAC アドレスは、この文書に書かない（[シークレット](03-secrets.md)）。
- メニューの名前は、Omada のバージョンで変わる。近い名前の項目を探す。
- 各手順の「結果」には、日付と、実機で確かめた値を書く。

## 進み具合（2026-11-09 時点）

| 区分 | 内容 | 状況 |
| --- | --- | --- |
| A | VLAN30・50、DHCP、ACL を作って確かめる | 完了（後片づけも済み） |
| B | `vmbr0` を VLAN-aware にする | 6 だけ残っている（VLAN20・40・70 を作ってから） |
| C-1 | `vmbr0.10` の試験 | 完了（外した） |
| C-2 | `vm-omada` の IP 変更への追従 | 未実施（方法を決めるところから） |
| 後 | 結果の反映、`rh-` の ACL の削除 | 未実施 |

## 全体像

| 区分 | 内容 | 影響 | 戻すか |
| --- | --- | --- | --- |
| **A. 足すだけ** | VLAN30・50 と DHCP、ACL を作り、SG2210P の p5・p6 に繋いだ検証用の端末で確かめる | 既存のホストに影響しない | 戻さない（検証のあと、p5・p6 を空きに戻すだけ） |
| **B. 恒久的な準備** | Proxmox の `vmbr0` を VLAN-aware にし、SG2210P の p2 に tagged を足す | ほぼ無い。**設定を誤ると、Proxmox に届かなくなる** | 戻さない（当日の作業を減らす先行作業） |
| **C. 一時的な変更** | `vmbr0.10` の試験、`vm-omada` の IP 変更への追従 | **C-2 は、機器がコントローラーを見失いうる** | 戻す |

A だけなら、すぐ始めてよい。B と C は、時間に余裕のあるときに、1 つずつ行う。

## 0. 前提

- [x] 段階 1・2 が済んでいる（ER605 と SG2210P がコントローラーに採用済み。[段階 1・2](20-network-cutover-stage-1-2.md)）
- [x] コントローラーのバックアップが、直近にある（iCloud Drive）
- [x] 有線で繋げる検証用の端末（Mac）がある（USB の有線 LAN アダプターが要るかもしれない。検証中は Wi-Fi を切る）

## A. 足すだけ

### A-1. VLAN30 と VLAN50 を作る

コントローラー（`https://omada.lab.kanare.dev`）の Settings > Wired Networks > LAN で、ネットワークを足す。既存のデフォルトの LAN は、触らない。

| VLAN | 名前 | ゲートウェイ（ER605） | DHCP | リース | 配る DNS |
| --- | --- | --- | --- | --- | --- |
| 30 | Trusted | `10.77.30.1/24` | `.100`〜`.199` | 24〜48 時間 | `10.77.20.10` |
| 50 | IoT | `10.77.50.1/24` | `.100`〜`.149` | 24 時間 | `10.77.20.10` |

`10.77.20.10`（`vm-infra`）は、まだ存在しない。この段階では、DNS は引けない（配られる値が正しいことだけを確かめる）。

> **警告（INC-2026-11-08）: ウィザードの「Select Device Port」では、アクセスポートだけを選ぶ。トランクは選ばない。**
>
> - ポートを選ぶと、そのポートが「その VLAN のアクセスポート」になる。Native Network が、作るネットワークに書き換わり、タグ付きは Block All になる。
> - 選ぶのは、その VLAN の端末を直接繋ぐポート（p5・p6）だけ。複数の VLAN を通すトランク（p1＝ER605 へ、p2＝Proxmox）は選ばない。
> - タグ付きは、ポートのプロファイルが `All`（Allow All）なら、作った VLAN が自動で入る。
> - 事故: Management（VLAN10）を作るとき、p2 を「VLAN10 をタグ付きで通すつもり」で選んだ。p2 の Native が Management(10)、タグ付きが Block All になり、Proxmox のタグなしの通信が既定の LAN に届かなくなって、Proxmox と全 VM が LAN から消えた。
> - 作成のあと、SG2210P の p1〜p4 が、Native = Default(1)、Network Tags = Allow All のままであることを確認する。

- [x] 作ったあとも、今の LAN（`192.168.11.0/24`）、Proxmox、VM、Wi-Fi が、今までどおり動いている（`ping 192.168.11.10`、`ping 1.1.1.1`）

### A-2. 検証用のポートを設定する

Devices → `sg2210p` → ポートで、**p5 を access VLAN30（untagged）、p6 を access VLAN50（untagged）**にする。p5・p6 は空きポートなので、既存に影響しない。

- [x] p1（ER605 へのアップリンク）と p2〜p4 は、変更していない

### A-3. DHCP とインターネットを確かめる

Mac を p5 に有線で繋ぐ（Wi-Fi は切る）。

- [x] `10.77.30.100`〜`.199` の IP を受け取る（`ipconfig getifaddr <有線のインターフェース>`）
- [x] ゲートウェイが `10.77.30.1`
- [x] 配られた DNS が `10.77.20.10`（`scutil --dns | grep nameserver`）
- [x] `ping -c 3 10.77.30.1` が通る
- [x] `ping -c 3 1.1.1.1` が通る（IP で出られる）

Mac を p6 に繋ぎ替えて、同じことを確かめる（`10.77.50.100`〜`.149`、ゲートウェイ `10.77.50.1`）。

### A-4. ACL の評価順と、戻りの通信を確かめる

今は Servers のホストが `192.168.11.x` にいるので、**今の LAN（`192.168.11.0/24`）を Servers の代わりにして**試す。ゲートウェイの ACL（LAN → LAN。Settings > Network Security > ACL）に、次のルールを**上から順に**作る。

| 順 | 動作 | 送信元 | 宛先 | 名前 | 説明 |
| --- | --- | --- | --- | --- | --- |
| 1 | 許可 | VLAN30 | 今の LAN | `rh-010-trusted-to-lan` | `[リハーサル] Trusted → 今のLAN（Serversの代理） : 許可` |
| 2 | 許可 | VLAN30 | VLAN50 | `rh-020-trusted-to-iot` | `[リハーサル] Trusted → IoT : 許可` |
| 3 | 拒否 | VLAN50 | 今の LAN | `rh-030-iot-to-lan` | `[リハーサル] IoT → 今のLAN（Serversの代理） : 拒否` |
| 4 | 拒否 | VLAN50 | VLAN30 | `rh-040-iot-to-trusted` | `[リハーサル] IoT → Trusted : 拒否` |
| 5a | 拒否 | 今の LAN | !今の LAN | `rh-900-deny-from-lan` | `[リハーサル] 今のLAN → 他のネットワーク : 拒否（末尾）` |
| 5b | 拒否 | VLAN30 | !VLAN30 | `rh-901-deny-from-trusted` | `[リハーサル] Trusted → 他のネットワーク : 拒否（末尾）` |
| 5c | 拒否 | VLAN50 | !VLAN50 | `rh-902-deny-from-iot` | `[リハーサル] IoT → 他のネットワーク : 拒否（末尾）` |

名前と説明の付け方（検証用は `rh-` と `[リハーサル]` を付ける）は、[設計書](../../architecture/08-vlan-design.md#acl-の名前と説明の付け方)にある。本番でも同じ形にする。

ルールの作り方の注意:

- 種類（Source Type・Destination Type）に「すべて（Any）」はなく、宛先は、送信元に選んだネットワーク以外からしか選べない。
- そのため、末尾の拒否（5）は、**ネットワークごとに 1 件**作る。送信元はそのネットワーク、宛先は「!ネットワーク」（選んだネットワーク以外のすべて。公式の資料の例と同じ形）。「!ネットワーク」を選べなければ、ほかのネットワークをすべて選ぶ。
- ルールに一致しない通信は、暗黙の許可になる。だから 5 が要る。
- インターネットは、ネットワークの一覧に入らないので、5 の対象外の見込み。5c を作ったあと、p6 から `ping 1.1.1.1` が通ることで確かめる。
- 5a〜5c は**最後に足し、足したあと、既存の通信が生きているか確認する**（`ping 192.168.11.10`、`ping 1.1.1.1`、コントローラーの画面、Wi-Fi の端末）。おかしければ、**削除でなく無効にする**。

確認:

p5（VLAN30）の Mac で:

- [x] `192.168.11.13` などに届く（ルール 1。戻りの通信が通る）
- [x] `ssh` や `curl` で、双方向のやりとり（TCP）が成立する（`ssh vm-code`（`192.168.11.22`）が成功）

p6（VLAN50）の Mac で:

- [x] `192.168.11.13` に**届かない**（ルール 3）
- [x] `ping 1.1.1.1` は通る（5c の「!ネットワーク」でも、インターネット宛が拒否されない）
- [x] ルール 4（IoT → Trusted の拒否）: VLAN30 に実際のホストが要る。B の 7 で、検証用の VM（`vm-dev`、`tag=30`）を使って確認した

結果:

- 2026-11-06: p6 から `192.168.11.13` に届かない（ルール 3 が効いている）。p6 から `ping 1.1.1.1` は通る。p5 から `ssh vm-code` が成功し、戻りの通信は通る。評価は上から順（末尾の 5b より、許可のルール 1 が先に評価された）。
- 2026-11-08: B の 7 で、ルール 4 とルール 2 が期待どおりに動いた（B の 7 の結果）。

注意: **`10.77.30.1`（VLAN30 のゲートウェイ自身）宛の ping は、通る。** ゲートウェイ自身宛の通信は、ゲートウェイの ACL（LAN → LAN）の対象外で、ルール 4 の確認にならない（2026-11-06 に実機で確認）。

### A-5. 後片づけ

- [x] Mac を、元の接続に戻す（Wi-Fi を入れる）
- [x] p5・p6 を、空きポート（p7）と同じ設定に戻す（VLAN30・50 のアクセスポートのままにしない）
- [x] 作った ACL（7 件）は、検証用なので**無効**にする。削除は、リハーサルの最後（「リハーサルの後」）。ルール 4 の確認で、また有効にするため
- [x] コントローラーのバックアップを取る
- VLAN30・50 のネットワークと DHCP は、本番の設定として残す（当日に有効にする。[段階 3](21-network-cutover-stage-3.md)）

結果（2026-11-09）: A の後片づけのとき、p5（VLAN30）と p6（VLAN50）は、アクセスポートのまま残っていた。C-1 のあとで、p5・p6 を p7 と同じ設定（プロファイル「すべて」、Native Default(1)、タグ付き 10/30/50、タグなし Default(1)）に戻した。

## B. 恒久的な準備（`vmbr0` を VLAN-aware にする）

**時間に余裕のあるときに行う。** 稼働中の Proxmox のネットワーク設定を変える。誤ると Proxmox に届かなくなるので、次のどちらか（できれば両方）を用意する。

1. **物理コンソール**（キーボードとモニター）を、すぐ繋げられる状態にする。成功すれば使わない。
2. **自動で元に戻るタイマー**を仕掛ける（手順 2）。接続が切れても、決めた時間に、自動で元に戻る。

変更前の基準（2026-11-08）:

- Proxmox VE 9.1.7（カーネル 6.17.2-1-pve）、`ifupdown2` 3.3.0（`ifreload` が使える）
- `vmbr0` は VLAN-aware ではない（`vlan_filtering 0`）
- `bridge vlan show`: `nic0`、`vmbr0`、各 VM の `tap` が、すべて VLAN 1（PVID・untagged）
- `dmesg` に `Hardware Unit Hang` は無い
- `/etc/network/interfaces`: `nic0` は `inet manual`（Ansible の ethtool の行つき）。`vmbr0` は `192.168.11.10/24`、ゲートウェイ `192.168.11.1`、`bridge-ports nic0`、`bridge-stp off`、`bridge-fd 0`。末尾に `source /etc/network/interfaces.d/*`

事前の確認（2026-11-08。どれもネットワークに影響しない）:

- `systemd-run` のタイマーは動く（1 分後に実行された）。途中で止められる（`systemctl stop <unit>.timer`）。
- `ifreload -a -n`（実行せず表示だけ）は、そのときの設定で、エラーなく終わった。ただし、VLAN のインターフェースを作る設定では、`-n` はエラーになる（C-1 の結果）。
- SG2210P の p2 は、tagged に Trusted（30）と IoT（50）が入っていた（作った VLAN が自動で入る）。
- ER605 のネットワークは、Default、Trusted、IoT の 3 つ。検証用の ACL（`rh-`）は、すべて無効。

### 手順

1. [x] `/etc/network/interfaces` を退避する（例: `cp /etc/network/interfaces /root/interfaces.bak-YYYYMMDD`）。Mac 以外にも、写しを置く。
2. [x] **自動復旧のタイマーを仕掛ける。** たとえば、10 分後に退避を書き戻す一時タイマー（実際の復旧、つまり設定の書き戻しと `ifreload` は未検証）:

   ```bash
   systemd-run --unit=netrevert --on-active=10m /bin/sh -c 'cp /root/interfaces.bak-YYYYMMDD /etc/network/interfaces && ifreload -a'
   ```

   成功したら、`systemctl stop netrevert.timer` で止める。
3. [x] `vmbr0` のブロックに、次の 2 行を**足す**（ほかは変えない。IP は `192.168.11.10`・タグなしのまま）。`ifreload -a` で反映する（Proxmox の Node → System → Network → 「Apply Configuration」でもよい）。反映の前に、`ifreload -a -n` で、エラーが出ないことを見る。

   ```text
   auto vmbr0
   iface vmbr0 inet static
           address 192.168.11.10/24
           gateway 192.168.11.1
           bridge-ports nic0
           bridge-stp off
           bridge-fd 0
           bridge-vlan-aware yes      # 足す
           bridge-vids 2-4094         # 足す
   ```

4. [x] 確認する。
   - `ssh` と Web UI で、Proxmox に届く
   - `qm list` で、`vm-infra`、`vm-omada`、`vm-monitoring`、`vm-apps`、`vm-code` が running
   - `ip -d link show vmbr0 | grep -o "vlan_filtering [0-9]"` が `1`
   - `bridge vlan show` で、`nic0` に VLAN 2〜4094 が増え、各 `tap` は VLAN 1（PVID・untagged）のまま
   - `nic0` が up で、`dmesg` に `Hardware Unit Hang`（e1000e の送信停止。`INC-2026-10-25`）が無い

   結果（2026-11-08）: `vlan_filtering` が 1、各 `tap` は VLAN 1 のまま、VM が running、`dmesg` は基準どおり、SSH と Web UI が届いた。Slack にアラートは出ていない。`nic0` に VLAN 2〜4094 が出ている（1 行ずつ出て長いので、`bridge vlan show dev nic0 | wc -l` で行数を見る。`grep nic0` だと 2 行目以降が出ない）。
5. [x] **タイマーを止める**（成功したとき）。
6. [ ] SG2210P の p2 に、tagged 10/20/40/50/70 が入っていることを確認する（untagged VLAN1 は、そのまま。今の通信に影響しない）。
   - ポートの tagged は、コントローラーに作ったネットワークからしか選べない。**先に、そのネットワーク（VLAN）を作る。**
   - p2 のプロファイルが、作ったネットワークをすべて tagged にする設定なら、作ると自動で入る（VLAN10・30・50 で確認済み）。
   - **ウィザードの「Select Device Port」では、トランクの p2 を選ばない**（A-1 の警告）。アクセスポートだけ選ぶ。
   - VLAN10 は C-1 の 1 で作った。VLAN20・40・70 は、本番の設定を作るとき（段階 3 の準備）に作る。

   状況:
   - 2026-11-08: p2 には Trusted（30）と IoT（50）が入っている。B の 7（`tag=30`）に必要なのは VLAN30 だけなので、B の 7 に進んでよい。
   - 2026-11-09: p2 は、Native = Default(1)、Network Tags = 全て許可、タグ付き = Management(10)・Trusted(30)・IoT(50)、タグなし = Default(1)（VLAN 設定は「カスタム」）。VLAN10 も入っている。
   - 残り（20・40・70）は、そのネットワークを作るときに確認する。VLAN 設定が「カスタム」なので、**自動で入るかも、そのとき確かめる**（「全て許可」なので、通信は通るはず）。
7. [x] 検証用の VM（`vm-dev`）を、タグ付きで繋いで、動作を確かめる。今あるネットワークは Trusted（30）と IoT（50）なので、**VLAN30（`tag=30`）**にする。保留していたルール 4 の確認にも使う。

   1. Proxmox の画面で、`vm-dev`（VMID 121）→ Hardware → Network Device → Edit → **VLAN Tag を `30`**（ブリッジは `vmbr0` のまま）。
   2. `vm-dev` を起動し、画面のコンソールを開く。`vm-dev` は固定 IP（`192.168.11.21`）の設定なので、そのままでは VLAN30 に繋がらない。**試験の間だけ**、手で IP を付ける（再起動で消える）。インターフェース名は `ip -br a` で調べる。

      ```bash
      sudo ip addr flush dev <インターフェース>
      sudo ip addr add 10.77.30.20/24 dev <インターフェース>
      sudo ip route add default via 10.77.30.1
      ```

      `10.77.30.20` は、固定アドレスの帯（`.10`〜`.49`）で、DHCP のプール（`.100`〜）と重ならない。
   3. [x] `ping -c 3 10.77.30.1` と `ping -c 3 1.1.1.1` が通る（検証用の ACL は無効のまま）。
   4. [x] **ルール 4 の確認**: 検証用の ACL（`rh-` の 7 件）を有効にする。
      - p6（VLAN50）の Mac から `ping 10.77.30.20` が**届かない**（ルール 4、5c）。
      - `vm-dev` から p6 の Mac（`10.77.50.x`）への ping が**届く**（ルール 2。Mac のファイアウォールが ping を止めていないとき）。
   5. [x] **後片づけ**: 検証用の ACL を無効に戻す。`vm-dev` を停止する。Proxmox の画面で、**VLAN Tag を空に戻す**（Terraform の設定とずれたままにしない）。`vm-dev` は止めたままにする。

   結果（2026-11-08）:
   - `vm-dev` の `eth0` が `10.77.30.20/24` になり、`10.77.30.1` と `1.1.1.1` に、どちらも 0% 損失で ping が通った。`tag=30` のタグ付き通信が、`vmbr0` と p2 を通って、VLAN30 のゲートウェイとインターネットまで届く。
   - p6 の Mac から `ping 10.77.30.20` は 100% 損失（届かない）。`vm-dev` から p6 の Mac（`10.77.50.100`）への ping は、5 回とも通った（ttl=63。ER605 で 1 回ルーティングされている）。
   - ルール 4（IoT → Trusted の拒否）と、ルール 2（Trusted → IoT の許可）が、期待どおりに動いた。タグ付きの VM でも、A のアクセスポートと同じ結果になる。

## C. 一時的な変更（変更して、確かめて、戻す）

### C-1. `vmbr0.10` の試験

B が済んでいること。タイマー（B の 2）を仕掛けてから行う。

1. [x] ER605 に VLAN10（Management、`10.77.10.1/24`）を作る（A-1 と同じ要領。DHCP は、緊急用の `.240`〜`.250` だけ）。

   結果:
   - 2026-11-08: B の 6 で作り、INC-2026-11-08 が起きた（p2 は修復済み）。Omada の VLAN 一覧で、DHCP は `10.77.10.240`〜`.250`（11 件）。SG2210P の p2 のタグ付きに、VLAN10 が自動で入っている。
   - 2026-11-09（再開時の確認）: ER605 の p2〜p4 は、Native VLAN = Default(1)（ER605 のポートの画面には、Native VLAN しかない。p1 は WAN）。SG2210P の p2 は、B の 6 の 2026-11-09 のとおり。
2. [x] Proxmox の `vmbr0.10` に、`10.77.10.10/24` を**足す**（旧 `192.168.11.10` は残す）。試験用に、**別ファイル**（`/etc/network/interfaces.d/vmbr0-10-rehearsal`。末尾の `source /etc/network/interfaces.d/*` で読み込まれる）に書く。ゲートウェイは書かない（今のゲートウェイは `vmbr0` のまま）。返信が VLAN10 側から出るように、VLAN30 宛ての経路だけ足す。

   ```text
   auto vmbr0.10
   iface vmbr0.10 inet static
           address 10.77.10.10/24
           up ip route add 10.77.30.0/24 via 10.77.10.1 dev vmbr0.10
           down ip route del 10.77.30.0/24 via 10.77.10.1 dev vmbr0.10
   ```

   - タイマーは、外す手順を仕掛ける。

     ```bash
     systemd-run --unit=netrevert --on-active=10m /bin/sh -c 'ifdown vmbr0.10; rm -f /etc/network/interfaces.d/vmbr0-10-rehearsal; ifreload -a'
     ```

   - **`ifreload -a -n`（ドライラン）は、VLAN のインターフェースを作る設定だとエラーになる**（`NetlinkListenerWithCache.link_add_vlan_dry_run() takes from 4 to 5 positional arguments but 6 were given`。ifupdown2 の不具合で、設定ファイルの誤りではない）。`vmbr0.10` の検証に `-n` は使えない。
   - 反映は、`ifup vmbr0.10`（`vmbr0.10` だけを上げる）。
   - **外すとき**は、`ifdown vmbr0.10` → ファイルを削除 → `ifreload -a`。

   結果（2026-11-09）: `ifup vmbr0.10` が成功した。`vmbr0` の `192.168.11.10/24` は、そのまま残った。経路は `10.77.10.0/24` と `10.77.30.0/24 via 10.77.10.1` の 2 本。外す手順を仕掛けたタイマーは、発火させていない（試験のあと、手で外した）。経路なしで届くかは、試していない。
3. [x] 確認する。
   - Mac（VLAN30 の p5）から `10.77.10.10` に届く。検証用の ACL（`rh-`）は、無効のままで通る。
   - Proxmox の Web UI が `10.77.10.10:8006` で開く。

   結果（2026-11-09）:
   - Proxmox から `10.77.10.1` へ ping が通った（3 回とも 0% 損失）。
   - Mac（SG2210P の p5、VLAN30）から `ping 10.77.10.10` が通った（ttl=63。ER605 で 1 回ルーティング）。
   - `https://10.77.10.10:8006` で、ログイン画面が出た。
4. [x] **届かなければ、`vmbr0.10` を外す。** 旧 IP は残してあるので、今の通信は止まらない。（今回は届いた。手順 5 のとおり外した）
5. [x] 試験が済んだら、`vmbr0.10` を外す（当日に付け直す）。

   結果（2026-11-09）: **`vmbr0.10` で届いた。** `systemctl stop netrevert.timer` → `ifdown vmbr0.10` → ファイル削除 → `ifreload -a` で外した。外したあと、`vmbr0` は `192.168.11.10/24` だけ、`interfaces.d/` は空、`10.77` の経路なし、タイマーなし、5 台が running。

### C-2. `vm-omada` の IP 変更への追従（リスクが高い。方法は、実施前に決める）

`vm-omada` が `192.168.11.12` から `10.77.10.3` に変わったとき、ER605 と SG2210P がコントローラーに付いてくるか。**付いてこなかったとき、機器がコントローラーを見失い、機器のリセットと再採用が要るかもしれない**（段階 1 の戻し方と同じ手間）。

**確認済みの事実（2026-11-09）**:

- 機器は、採用されたときのコントローラーの住所（`192.168.11.12`）を覚えている。
- コントローラーの「コントローラーホスト名/IP」（設定 > システム設定 > コントローラーへのアクセス。今は手動で `192.168.11.12`）は、パスワードリセット用メールと RADIUS ポータル用で、**機器の接続先ではない**。`vm-omada` の IP を変えるときは、この値も直す。
- デバイスアカウント（機器の管理者。サイト共通）は、コントローラーの「ネットワーク設定 > サイト設定 > デバイスアカウント」にある。値は Keychain に登録済み（[台帳](03-secrets.md)の方針。値は書かない）。
- 採用済みの機器の Web UI には入れない。SG2210P（`192.168.11.62`）は、`This switch is being managed by Controller.`（403 Forbidden）。ER605 は未確認。
- SG2210P は SSH を受け付けない（ポート 22 が `Connection refused`）。
- Omada Discovery Utility 5.2.4（機器に接続先の Inform URL を設定するツール）は、**Mac（arm64）では動かない**。Java 17（`openjdk@17`）では起動するが、同梱の JavaFX が Windows 用で、画面が出ない（`no suitable pipeline found`）。公式の対象は、Windows と Linux（x86 64-bit、JRE 17）。

**機器の接続先を直す手段は、まだ決まっていない**（検討中。案は[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)の「3-A」）。決まるまで、`vm-omada` の IP 変更は実施しない。

- [ ] 機器の接続先を直す手段を決める（上の事実と、移行計画の検討中の案から）
- [ ] 実施する前に、次を決める: 方法（`vm-omada` の IP を一時的に変える、など）、失敗したときの復旧手順（接続先の再設定、リセットと再採用）、戻す時刻
- [ ] コントローラーのバックアップ、ER605・SG2210P の設定の控えを、取ってある
- [ ] 実施し、機器が付いてくるか確かめる: ______
- [ ] 付いてこなかった場合の復旧手順を、実際に試して、[段階 3 の Runbook](21-network-cutover-stage-3.md)の手順 4 に書く

**C-2 は、段階 3 の本番の直前ではなく、時間に余裕のあるときに、先に行う。**

## リハーサルの後

1. 結果を、[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)の「3-A」のチェックボックスと、「未確認・要判断の事項」に反映する。
2. [段階 3 の Runbook](21-network-cutover-stage-3.md)の、「要判断」（DHCP が配る DNS のタイミング）、手順 3（`vmbr0.10`）、手順 4（`vm-omada` の追従）を、結果に合わせて直す。
3. 終わった作業の、設定の変更を、各機器の `settings.md` の変更履歴に足す。
4. **検証用の ACL（`rh-` の 7 件）を削除する。** ルール 4 の確認は済んでいる。本番のルールは、[設計書](../../architecture/08-vlan-design.md#acl-の名前と説明の付け方)の決まり（`1xx`、`9xx`）で、別に作る（`rh-901`、`rh-902` を名前を直して流用せず、作り直す）。
