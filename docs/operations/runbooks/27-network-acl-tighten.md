# ゲートウェイの ACL を絞る

段階 3 のあと全許可のまま運用している ER605 のゲートウェイ ACL（LAN → LAN）を、[通信ポリシー](../../architecture/hld/05-network.md#通信ポリシー)の内容に絞る（[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)、[ADR-0034](../../adr/0034-acl-for-vlan-boundaries-ufw-for-ports.md)）。[段階 3 の当日の作業](21-network-cutover-stage-3.md)の手順 8 を、この手順書で置き換える。

- 作るルールとグループの値は、[Omada コントローラーの設定値](../../architecture/lld/network/omada-controller.md#ゲートウェイの-acl)を正とする。名前と説明の付け方は、[ACL の名前と説明の付け方](../../architecture/lld/network/acl.md)にある。
- **文書が先**の変更である（[ADR-0033](../../adr/0033-docs-first-by-change-type-and-diagram-order.md)）。この手順書と設定値をマージしてから、実機を変える。
- 期限の目安は、段階 3 の完了（2026-11-17）から 2 週間以内（決定 2026-11-11）。
- 所要時間は、確認を含めて 2 時間ほどの見込み（未確認）。止まるのは、絞り間違えた通信だけである。

## 考え方

許可のルール（`1xx`）を先に全部作り、そのあとで、末尾の拒否のルール（`9xx`）を、**影響の小さい VLAN から 1 件ずつ**有効にする。ルールに一致しない通信は暗黙に許可されるので、許可のルールを作るだけでは、何も止まらない。通信が止まり始めるのは、`9xx` を足したときである。

`9xx` を足す順は、端末の無い VLAN（DMZ、Guests、IoT）、Lab、Servers、Trusted、Management とする。足すたびに、その VLAN から出る通信を確かめる。おかしければ、そのルールを**削除せず、無効にする**。

## 確認に使う端末

**Tailscale をオンにした Mac では、確認しない。** その Mac から Servers・Lab への通信は、ER605 を通らず、Tailscale の subnet router（`vm-infra`）を経由するので、ACL を確かめたことにならない（[段階 3 の手順 7](21-network-cutover-stage-3.md#7-疎通の確認)）。

| 端末 | VLAN | 使い方 |
| --- | --- | --- |
| Mac（**Tailscale をオフ**にする） | Trusted | Trusted からの許可と拒否を確かめる。作業中に Omada の画面を開く |
| iPhone（Wi-Fi、**Tailscale をオフ**） | Trusted | Mac の代わり。Homepage などが開くかを見る |
| iPhone（モバイル回線、Tailscale をオン） | 外出先 | Tailscale 経由の通信（`vm-infra` が送信元）を確かめる |
| `vm-dev`（`10.77.40.10`、VMID 121） | Lab | Lab からの拒否を確かめる。手動起動なので、作業の前に起動する |
| `vm-infra`、`vm-monitoring` | Servers | SSH で入り、Servers からの通信を確かめる |
| `pve01`、`vm-omada` | Management | SSH で入り、Management からの通信を確かめる |
| Mac（復旧ポート p8） | Management | 絞り間違えて Omada の画面に入れなくなったときの入口 |

IoT・Guests・DMZ には端末が無いので、その VLAN からの拒否は、実機では確かめられない。ルールが有効で、ほかの VLAN と同じ形であることを、画面で確かめるだけにする。

## 0. 前の日までに

- [x] この手順書と、[設定値](../../architecture/lld/network/omada-controller.md#ゲートウェイの-acl)の PR をマージした（2026-11-26。#43）。
- [x] Homepage の Proxmox ウィジェットを、Caddy 経由（`https://pve.lab.kanare.dev`）に変えて、値が取れることを確かめた（2026-11-26）。
- [x] `pve01` の DNS をルーター（`10.77.10.1`）に、NTP を `ntp_servers` に変えた（2026-11-26。#44。[Proxmox ホスト](../../architecture/lld/platform/proxmox-host.md)）。

## 1. 準備（当日）

復旧ポートと画面の確認（1・2）は、前の日ではなく、当日の最初に行う（運用者の判断。2026-11-26）。どちらも実機を変えないので、当日に回しても、作業の順番は崩れない。

1. **復旧ポート p8 から、Omada の画面に入れる**ことを確かめる。Mac を p8 に繋ぐと、DHCP で `10.77.10.240`〜`.250` を受け取り、`https://10.77.10.3:8043` が開く。p8 と `vm-omada` は同じ VLAN（Management）なので、ACL を通らない。`vm-omada` の UFW は、`10.77.10.0/24` からの 8043 を許可している。**入れなければ、ここで作業をやめる**（絞り間違えたときの戻り道が無いため）。確かめたら、Mac を元の接続に戻す。
2. 6.3 の画面（サイト > 構成 > ネットワーク設定 > セキュリティ > ACL の「ゲートウェイ ACL」）で、グループ（IP グループ、IP-Port グループ）が作れること、ACL のプロトコルに ICMP と「TCP と UDP」を選べること、送信元・宛先にグループを選べることを確かめる（保存はしない）。選べないものがあれば、その場でルールを分ける（例: 「TCP と UDP」が選べなければ、TCP と UDP の 2 件にする）。分けたルールは、下の「実施の記録」に書き、実施のあとに[設定値](../../architecture/lld/network/omada-controller.md#ゲートウェイの-acl)の表を直す。通信の許可の範囲は変えないので、文書が先の原則（[ADR-0033](../../adr/0033-docs-first-by-change-type-and-diagram-order.md)）から外れない。
3. Omada のバックアップ（設定とサイト）を取り、iCloud Drive に日付つきで保存する。
4. `vm-dev` を起動する: `ssh root@10.77.10.10 "qm start 121"`。起動したら、Prometheus のターゲットが `up` になることを見る。
5. 今の状態を控える。Prometheus の全ターゲットが `up`、アラートが `Watchdog` だけであること。Homepage の各ウィジェットに値が出ていること。
6. Mac の Tailscale をオフにする。Mac から `ping 10.77.20.10`、`ping 10.77.10.10` が通り、`route -n get 10.77.20.10` の `interface` が `utun` でないことを確かめる。`utun` のままなら、`tailscale down` で止める（本番では、画面でオフにしたあとも `utun` のままだった）。
7. リハーサルの `rh-` のルール 7 件（無効のまま）を、削除する。

## 2. グループと許可のルールを作る

1. [設定値](../../architecture/lld/network/omada-controller.md#ゲートウェイの-acl)の表のとおりに、グループを 10 件作る。
2. 許可のルール（`130`〜`172`）を、表の順に作り、有効にする。
3. 一覧の順番が、表と同じであることを確かめる。

確認: [ ] Prometheus の全ターゲットが `up` のまま　[ ] Homepage と Caddy 経由のサービスが開く（何も止まっていないこと）

## 3. 末尾の拒否を、1 件ずつ足す

各段階で、`python3 tools/acl-check.py --deny <有効にした VLAN>` を流すと、下の確認項目の多くを自動で確かめられる（例: 3-2 のあとは `--deny dmz,guests,iot,lab`）。手順 1 の前に `--deny none` で流し、すべて届くことを確かめておく。

各ルールは、[設定値](../../architecture/lld/network/omada-controller.md#ゲートウェイの-acl)の表のとおりに作る（送信元はその VLAN、宛先は「!ネットワーク」でその VLAN）。足したら、下の確認を行い、問題が無ければ次に進む。

### 3-1. DMZ、Guests、IoT（`970`、`960`、`950`）

端末が無いので、止まる通信は無い見込み。

- [ ] 3 件を足したあと、Prometheus の全ターゲットが `up` のまま
- [ ] 3 件が有効で、送信元と宛先が、ほかの `9xx` と同じ形である

### 3-2. Lab（`940`）

`vm-dev` で確かめる。

- [ ] `dig @10.77.20.10 home.lab.kanare.dev` と `dig +tcp @10.77.20.10 home.lab.kanare.dev` が引ける（`170` の DNS の許可）。`getent hosts` では確かめない。`vm-dev` のホスト DNS はルーター（`10.77.40.1`）で、`lab.kanare.dev` は ACL と関係なく引けない（[ADR-0007](../../adr/0007-vm-host-dns-is-router.md)）
- [ ] `curl -sk https://10.77.20.10` がタイムアウトする（Lab → Servers の 443 は拒否）
- [ ] `ping -c 2 10.77.30.1` は通るが、Trusted の端末（Mac の `10.77.30.x`）への ping は通らない（ゲートウェイ自身の住所は ACL の対象外）
- [ ] `ping -c 2 10.77.10.10` が通らない（Lab → Management は拒否）
- [ ] `ping -c 2 1.1.1.1` と `curl -sI https://deb.debian.org` が通る（インターネットは止まらない）
- [ ] Mac から `ssh vm-dev` で入れる（`151`。Trusted → Lab の許可と、戻りの通信）
- [ ] Prometheus の `vm-dev` のターゲットが `up`（`141`）

### 3-3. Servers（`920`）

- [ ] `https://omada.lab.kanare.dev` と `https://pve.lab.kanare.dev` が開く（`130`）
- [ ] Prometheus の `pve01` と `vm-omada` のターゲットが `up`（`131`）
- [ ] Homepage の Proxmox ウィジェットに値が出る（Caddy 経由）
- [ ] Prometheus の `building-router`（`172.22.0.1`）、`internet-cloudflare`、`internet-google` の監視が `up` のまま（`!ネットワーク` が、WAN 側のプライベートアドレスを止めないか。**未確認**の項目）
- [ ] iPhone（モバイル回線、Tailscale をオン）から、`https://home.lab.kanare.dev` が開き、`vm-dev` に SSH で入れる（`140`）。mosh を使うなら、mosh でも入れる（`142`）
- [ ] `vm-infra` から `nc -vz -w 3 10.77.30.<Mac の番号> 22` などで、Servers → Trusted が拒否される（Mac で `sshd` を動かしていなければ、ping で代える）
- [ ] Healthchecks.io の heartbeat と、Slack への通知が途切れていない（インターネット宛は止まらない）

### 3-4. Trusted（`930`）

Mac（Tailscale をオフ）と iPhone（Wi-Fi、Tailscale をオフ）で確かめる。

- [ ] `https://home.lab.kanare.dev`、`https://grafana.lab.kanare.dev`、`https://ha.lab.kanare.dev` が開く（`150`）
- [ ] `ssh vm-code` で入り、code-server（8080）と CloudCLI（3001）が開く（`150`。ポートは `vm-code` の UFW が絞る）
- [ ] AdGuard の画面（`http://10.77.20.10:3000`）が開く
- [ ] `ssh pve01`、`ssh vm-omada` で入れる。`https://10.77.10.10:8006` が開く（`153`）
- [ ] `ping 10.77.10.10` が通る（`156`）
- [ ] `https://10.77.10.2`（SG2210P の本体の画面）が開き、「コントローラーで管理されている」と表示される（`154`）
- [ ] `https://10.77.10.3:8043` は開かない（`vm-omada` の UFW が止める。Omada は Caddy 経由で開く）
- [ ] Mac から `nc -vz -w 3 10.77.10.10 9100` が拒否される（Trusted → Management は、`153`・`154`・`156` 以外は拒否）
- [ ] Wi-Fi の端末（テレビを含む）がインターネットに出られる。テレビの AirPlay・Cast が、今までどおり動く（テレビは Trusted なので、影響しない見込み）

### 3-5. Management（`910`）

- [ ] Omada の画面で、ER605 と SG2210P が「接続済み」のまま（機器とコントローラーは同じ VLAN なので、ACL を通らない）
- [ ] `pve01` で `getent hosts deb.debian.org` が引け、`chronyc sources` に `^*` の行がある（DNS はルーター `10.77.10.1`、NTP はインターネット。2026-11-26 に変えた。[Proxmox ホスト](../../architecture/lld/platform/proxmox-host.md)）
- [ ] `vm-omada` で `getent hosts deb.debian.org` が引ける（DNS はルーター `10.77.10.1`）
- [ ] `pve01` から `ping -c 2 10.77.20.10` が通らない（Management → Servers は拒否）

## 4. 仕上げ

1. Prometheus の全ターゲットが `up`、アラートが `Watchdog` だけであることを確かめる。
2. Omada のバックアップを取り直し、iCloud Drive に保存する。
3. `vm-dev` を止める: `ssh root@10.77.10.10 "qm shutdown 121"`。
4. Mac の Tailscale をオンに戻す。

## 戻し方

- **1 件の通信だけが止まった**: 原因になった `9xx` を無効にする。足りない許可が分かったら、設定値の表に足し、`1xx` を作ってから、`9xx` を有効に戻す。
- **Trusted から Omada の画面に入れなくなった**: Mac を復旧ポート p8 に繋ぎ、`https://10.77.10.3:8043` から入って、最後に足した `9xx` を無効にする。
- **全体を戻す**: `9xx` をすべて無効にする。許可のルール（`1xx`）は、残しても通信を止めない。全許可（段階 3 のあとの状態）に戻る。
- **コントローラーに入れない**: 準備の手順 3 で取ったバックアップから戻す。ER605 に ACL が残ったままでも、p8 と `vm-omada` は同じ VLAN なので、コントローラーには届く。

## 実施のあとに直す文書

- [Omada コントローラーの設定値](../../architecture/lld/network/omada-controller.md#ゲートウェイの-acl): 節の見出しと本文の「未適用」を外し、未確認の項目の結果を書き、変更履歴に 1 行足す。
- [通信ポリシー](../../architecture/hld/05-network.md#通信ポリシー)と[第6章 セキュリティ](../../architecture/hld/06-security.md#セグメンテーション): 「ACL は全許可のまま」の記述を、絞った日付に直す。
- [ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md) と [ADR-0034](../../adr/0034-acl-for-vlan-boundaries-ufw-for-ports.md): ステータスの「未適用」を外す（[ADR の一覧](../../adr/README.md)も）。
- [移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)の確認項目（各 VLAN から Servers への接続と、拒否すべき通信）と、[構成レビューの改善案](../roadmap/11-design-review-ideas.md)の #2 の状況。
- [VLAN 間の通信マトリクス](../../diagrams/README.md#vlan-間の通信マトリクスacl-matrix): 図の注記の「target policy」（目標）を、適用済みの書き方に直して書き出し直す（`make-acl-matrix.py`）。実機で絞った内容が許可表と違ったら、`MATRIX` も直す。
- `README.md`（リポジトリのトップ）: 通信マトリクスの図を載せる。**ACL を実際に絞るまでは載せない**（運用者の判断。2026-11-27）。
- この手順書: 結果と、予測が外れた点を、下の「実施の記録」に書く。

## 実施の記録

**2026-11-27 に実施した。** 末尾の拒否 7 件まで足し終え、ACL は[通信ポリシー](../../architecture/hld/05-network.md#通信ポリシー)の内容になった。段階 3 の完了（2026-11-17）から 10 日で、期限の目安（2 週間）に収まった。通信が止まったサービスは無く、Prometheus の 30 ターゲットは、作業の間ずっと `up` で、アラートは `Watchdog` だけだった。

確認には、許可と拒否の組み合わせを 35 件並べたテスト（`tools/acl-check.py`。今の本番の状態は `make acl-check` で確かめられる）を使った。送信元は、Mac（Trusted。Tailscale をオフ）、`vm-infra`・`vm-monitoring`（Servers）、`vm-dev`（Lab）、`pve01`・`vm-omada`（Management）で、TCP の接続、ping、DNS（UDP と TCP）を試した。各ケースの期待する結果は、許可のルールに当たるかと、送信元の VLAN の `9xx` が有効かで決まる。そのため、`9xx` を 1 件足すたびに、同じテストを流した。最初に全許可のまま流して、35 件すべてが届くことを確かめた。これで、拒否を期待するケースがあとで届かなくなったとき、UFW ではなく ACL が止めたと言える。各段階で、35 件すべてが期待どおりだった。

- 3-1（DMZ・Guests・IoT）: 端末が無いので、止まった通信は無い。
- 3-2（Lab）: `vm-dev` から Servers の 443、Management への ping と SSH、Mac への ping が止まった。DNS（`170`）、ゲートウェイ自身、インターネット、Lab へ入る通信（`140`・`141`・`151`）は通った。
- 3-3（Servers）: `vm-infra` から `pve01` の SSH と Mac への ping、`vm-monitoring` から Proxmox の 8006 が止まった。Caddy 経由の Omada・Proxmox、Prometheus の取得は通った。iPhone（モバイル回線、Tailscale をオン）から Homepage が開いた。iPhone からの SSH は試していないが、Tailscale 経由の通信は送信元が `vm-infra` になるので、テストの `vm-infra` → `vm-dev:22` と同じ通信である。mosh（`142`）は、使うときに確かめる。
- 3-4（Trusted）: Mac から、許可した Servers・Lab・Management の通信が通り、Proxmox の 9100 は止まった。AdGuard の画面（3000）、CloudCLI（3001）も開いた。SG2210P の本体の画面が開き、iPhone の AirPlay にテレビが表示された。
- 3-5（Management）: `pve01`・`vm-omada` から Servers が止まった。ルーターの DNS、NTP（`^*` の行あり）、インターネットは通った。ER605 と SG2210P は「接続しました」のままだった。

予測が外れた点と、分かったこと:

- 画面の場所は、Settings > Network Security ではなく、サイト > 構成 > ネットワーク設定 > セキュリティ > ACL の「ゲートウェイ ACL」だった。
- IP-Port グループは、サブネット（CIDR）の一覧と、ポートの一覧を別々に持ち、ポートはグループの全サブネットにかかる。範囲（`.2-.9`）も書けない。そのため、ホストごとにポートが違う `grp-mgmt-caddy` と `grp-mgmt-admin` を、2 つずつに分けた（グループは 10 件から 12 件。許可の範囲は同じ）。1 件のルールの宛先にグループを複数選べるので、ルールの数は変わらなかった。プロトコルは複数選べ、「TCP と UDP」を 1 件で作れた。
- 一覧に表示されるのは「説明」の欄なので、名前を説明の欄に入れた。
- `!ネットワーク` の拒否は、WAN 側のプライベートアドレス（`172.22.0.1`）宛を止めなかった。`building-router` の監視は `up` のまま。
- 3-2 の確認項目の `getent hosts home.lab.kanare.dev` は、ACL と関係なく失敗する（`vm-dev` のホスト DNS はルーター）。`dig @10.77.20.10` に直した。
- Mac の Tailscale を画面でオフにしたあとも、`10.77.20.0/24` への経路が `utun` に残っていた。手順 6 の `route` の確認で気づき、`tailscale down` で止めた。
- `vm-dev` は、作業の前から起動していた（準備の手順 4 は不要だった）。
