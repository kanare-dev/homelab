# 段階 3 の当日の作業（VLAN と `10.77.x.x` への一斉切り替え）

VLAN を有効にし、全ホストの IP を `192.168.11.x` から `10.77.<VLAN>.x` に付け替える日の手順。**ホストのアドレス付け替えは 1 回だけ**（[ADR-0004](../../adr/0004-vlan-cutover-all-at-once.md)）。段階 1・2（[当日の作業](20-network-cutover-stage-1-2.md)）が済んでいることが前提。作業時間は、数時間を見込む。

- 当日の順にチェックしながら進めるための文書。手順の根拠と、決めた経緯は[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)の「段階 3」と、[第5章 ネットワーク](../../architecture/hld/05-network.md)にある。手順を変えたら、計画も同じ変更で直す。
- 新しい IP は [IP アドレス一覧](../../architecture/lld/network/ip-addresses.md)、設定の対応表（ER605 の VLAN インターフェース、SG2210P のポート、Proxmox）は計画の「3-B」にある。
- 秘密の値と、機器の MAC アドレスは、この文書に書かない（台帳へ。[シークレット](03-secrets.md)）。
- **管理系（Proxmox ホスト、`vm-omada`、ER605・SG2210P）は、段階 3 では動かさない**（[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。手順 3・4 は、段階 3b に移した（この文書では行わない。下書きとして残す）。今の LAN（VLAN1）は、止めず、消さない。
- **ACL は、当日は全許可のまま切り替え、絞るのは別の日に行う**（[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）。手順 8 は、別の日の作業。
- **この文書は、実機でのリハーサルの前に書いた。** リハーサルの結果は、[リハーサル](22-network-stage-3-rehearsal.md)にある。結果で、手順が変わりうる。

## 0. 前提の確認（開始の前に）

計画の「3-A. 準備」が、すべて済んでいること。

- [x] **リハーサルが済んでいる**: 検証端末を SG2210P の p5（VLAN30）と p6（VLAN50）に繋ぎ、本番と同じ設定で次を確かめた。（2026-11-06・11-09。結果は[リハーサル](22-network-stage-3-rehearsal.md)）
  - Gateway ACL で、Trusted → IoT は通り、IoT → Trusted は拒否される。戻りの通信が通る。末尾の全拒否が効く。
  - DHCP が VLAN ごとに配る（DNS は `10.77.20.10`）。
- **（段階 3b の前提に移した。段階 3 では不要）コントローラーの IP 変更への追従を確かめる**: `vm-omada` が `192.168.11.12` から `10.77.10.3` に変わったとき、ER605 と SG2210P が付いてくる。付いてこない場合の手順（接続先の再設定、または機器のリセットと再採用）を、リハーサルで確かめて書いてある。
- [x] **Proxmox の準備が済んでいる**（[ADR-0023](../../adr/0023-proxmox-trunk-all-tagged.md)）: `vmbr0` が VLAN-aware（IP は `192.168.11.10`・タグなしのまま）。SG2210P p2 に tagged 10/20/40/50/70 を足してある。1 つの検証用 VM をタグ付きで繋いで、動作を確かめた。（2026-11-17 までに確認した。`vmbr0` は VLAN-aware、p2 の tagged は 2026-11-11、タグ付きの VM は `vm-dev` のリハーサルと、手順 5 の全 VM）
- [x] **コードの準備が済んでいる**: 別ブランチで、Terraform（`vlan_id` は必須で、全 VM に指定。`vm-omada` は、段階 3b まで、タグなし（VLAN1）を明示する）、Ansible、Caddyfile、Prometheus、Homepage、ドキュメントを、新アドレスに書き換えてある（一覧は[設計書](../roadmap/10-er605-sg2210p-migration-plan.md)）。 UFW の許可元も、新しいアドレスに直す（`vm-infra` の 8043、`vm-monitoring` の 9100。`vm-omada` は段階 3 で動かさないので、**直し忘れやすい**。[ロードマップ 13](../roadmap/13-defer-management-vlan.md)）。（2026-11-17。手順 5・6 で実機に流した）
- [x] **新アドレスのコードを、現行のブランチに取り込んだ**（2026-11-17。作業用のブランチ `stage3/new-addresses` は、取り込んだあと削除した）。`terraform plan` が、5 台の in-place 更新（`vm-omada` は変わらない）になっている。
- [x] **Omada に本番の設定を作ってある（有効にはしていない）**（2026-11-11。一覧は[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md#omada-の本番設定の一覧段階-3-の準備画面操作)）: VLAN 10/20/30/40/50/60/70（端末は繋いでいない）、DHCP、mDNS の中継（無効のまま）、スイッチのポートプロファイル `access-trusted`（どのポートにも未割り当て）。**ACL は作っていない**（当日は全許可。[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）。設定したあとのバックアップ: `omada_backup_...2026-11-11_21-48-24.cfg` と `sitebackup_...2026-11-11_21-48-31.cfg`（iCloud Drive）。
- [x] **今の LAN の DHCP の DNS をルーターにした**（2026-11-17。変更後に確認した。運用者の報告）。手順の確認:（決定済み。変えるのは、手順 2 で Wi-Fi の端末が Trusted に移ったあと）。
- [x] **バックアップが、Mac 以外にもある**（iCloud Drive の `homelab/`。2026-11-11 に取得）: Omada（`omada_backup_...2026-11-11_21-06-24.cfg` と `sitebackup_...2026-11-11_21-04-37.cfg`）、Proxmox の `/etc/network/interfaces`（`pve-interfaces-bk-20261111.txt`）、`terraform.tfstate`（`terraform.tfstate-bk-20261111`）、Buffalo の設定（`wsr-1800ax4p-bk-20261103*.bin`）。Omada に本番の設定を作る前の状態なので、**当日の手順 1 で、もう一度取る**。
  - **取り直した（2026-11-17）**: Omada（`omada_backup_...2026-11-17_20-55-01.cfg` と `sitebackup_...2026-11-17_20-55-17.cfg`）、Proxmox の `/etc/network/interfaces`（`pve-interfaces-bk-20261117.txt`）、`terraform.tfstate`（`terraform.tfstate-bk-20261117`）。Buffalo は、段階 3 で設定を変えていないので、取り直さない。手順 2 の直前に設定を変えたら、その分だけ取り直す。
- [x] Tailscale の経路の承認の手順を確認してある（`--advertise-routes=10.77.20.0/24,10.77.40.0/24,192.168.11.0/24`。手順は 6.2）。2026-11-11 に Admin Console で確認した: `vm-infra` は `192.168.11.0/24` が承認済みで、Expiry disabled。**自動承認（Auto approvers）は無い**ので、新しい 2 経路は当日に手動で承認する。
- [x] 戻し方（下記）を読んだ。（実施済み。2026-11-17。運用者の報告）

## 1. 開始

- **戻す時刻は決めない**（決定 2026-11-10、[ADR-0030](../../adr/0030-stage3-no-rollback-deadline.md)）。完了するまで作業する。
- [x] 作業中にインターネットが要るとき（調べもの、ファームウェアの取得）に、端末を建物（壁）の Wi-Fi に繋げることを確かめておく。（実施済み。2026-11-17。運用者の報告）
- [x] 物理コンソール（キーボードとモニター）を、Proxmox にすぐ繋げられる状態にする（成功すれば使わない。ホストのネットワーク設定を誤ると、SSH も Web UI も使えなくなるための保険）。自動で元に戻るタイマーを仕掛ける方法もある（[リハーサル](22-network-stage-3-rehearsal.md)の B）。（実施済み。2026-11-17。運用者の報告）
- [x] Mac に、有線の口（手順 2 で Buffalo の画面に入るときに使う）と、固定 IP を振る手段がある。外出先との確認用に、スマホを用意する。（実施済み。2026-11-17。運用者の報告）
- [x] 作業中に出るアラート（`GatewayUnreachable`、`TargetDown`、`PveVmStopped`、Heartbeat）は、想定内。（実施済み。2026-11-17。運用者の報告）

### 要判断: DHCP が配る DNS のタイミング

計画（3-B）では、各 VLAN の DHCP が最初から DNS に `10.77.20.10`（`vm-infra`）を配る。一方、`vm-infra` が `10.77.20.10` に移るのは手順 5。**手順 2 から手順 5 の終わりまで**、新しく IP を取った Trusted の端末は、DNS の宛先が存在しないので、名前が引けない（IP を直接指定した通信はできる）。

- 案 1（計画どおり）: このまま進める。その間は、Wi-Fi の端末が名前解決できないことを許容する。
- 案 2: 手順 2 では、DHCP の DNS を `192.168.11.11`（旧 `vm-infra`）にしておき、手順 5 の後に `10.77.20.10` に切り替える（端末は、リースの更新が要る）。

決めた案: **案 1**（決定 2026-11-10）。手順 2〜5 の間、Wi-Fi の端末が名前を引けないことを許容する。

### 止まる範囲（見込み。未確認。管理系は動かさないので、手順 3・4 は、段階 3b）

| 手順 | 影響 |
| --- | --- |
| 2 | Buffalo の下の Wi-Fi 端末が `10.77.30.x` に切り替わる（再接続が要る）。上の「要判断」の DNS。Buffalo の管理画面には、届かなくなる |
| 3 | （段階 3b に移した。段階 3 では、止まらない） |
| 4 | （段階 3b に移した。段階 3 では、止まらない） |
| 5 | VM が 1 台ずつ、IP と VLAN が変わる間、止まる。`vm-infra` が移るまで、LAN の DNS が使えない |
| 5〜6 | DNS のレコード、Caddy、Prometheus を反映する（手順 6）まで、FQDN 経由のサービスと監視が、旧アドレスのまま |
| 6 | Tailscale の経路を承認するまで、外出先から入れない |

## 2. Omada の本番設定を有効にする

1. `vm-dev` を止める。最終のバックアップ（Omada、Proxmox の `/etc/network/interfaces`、`terraform.tfstate`）を取る。
2. Omada: 本番の設定を有効にする（VLAN、DHCP、ACL。**ACL は最初は緩め（全許可）**）。SG2210P の p1・p3 を、新しい設定にする。**ポートの設定は、ネットワークを作るウィザードの「Select Device Port」ではなく、ポートの画面（Devices → `sg2210p` → Ports → Edit Port）で行う**（ウィザードでポートを選ぶと、そのポートが、その VLAN のアクセスポート（Native が書き換わり、タグ付きは Block All）になる。トランクの p1・p2 は選ばない。[INC-2026-11-08](../incidents/2026-11-08-sg2210p-native-vlan-overwrite.md)）。変更のたびに、**Proxmox（p2）に届くか**を確認する。届かなくなったら、[障害時切り分け](11-troubleshooting.md#proxmox-ホストと全-vm-にlan-から届かない)の切り戻し（ER605 の LAN ポートに直結）。
   - p1: untagged VLAN1、tagged 10/20/30/40/50/60/70
   - p3（Buffalo）: access VLAN30（untagged）
   - p4（ディスプレイ）: access VLAN30（untagged）

   **実施の記録（2026-11-17）と、わかったこと**:
   - p1 は、untagged VLAN1・tagged 10〜70 で問題なし。p4、p3 の順に、`access-trusted` を割り当てた。
   - **ポートの編集画面で、プロファイルを選んだだけでは足りない。「VLAN設定」を「プロファイルに従う」にする**（「カスタム」のままだと、Native が Default(1)・タグ全許可の古い値が残り、VLAN30 にならない）。Apply の前に、Native が Trusted(30) になっていることを確かめる。
   - p4 を切り替えると、Mac の有線は `10.77.30.100` に移る。DHCP が配る DNS（`10.77.20.10`）は、手順 5 まで存在しないので、**名前が引けなくなる**（Claude など、名前で繋がるものが切れる）。切り替える前に、有線と Wi-Fi の DNS を、一時的に外部にしておく（`networksetup -setdnsservers <サービス名> 1.1.1.1`。手順 5 のあとに `Empty` で戻す）。
   - 確認した結果: Trusted の端末（`10.77.30.x`）から、ER605（`192.168.11.1`）、Proxmox（`192.168.11.10`）、`vm-omada`（`192.168.11.12`。`:8043` が HTTP 200）、`1.1.1.1` に届く。ER605 が、Trusted と今の LAN を中継している。
3. Buffalo は Trusted に入る。Wi-Fi の端末は、`10.77.30.x` を受け取る。**Buffalo の IP は `192.168.11.2` のまま残るので、管理画面には Trusted から届かなくなる**（Wi-Fi の中継は、IP と関係なく動く）。Buffalo は、段階 4 が当面来ないため、Trusted の AP として使い続ける。管理画面に入れる状態にしておく（下の 4）。
4. 落ち着いてから、Buffalo の IP を **`10.77.30.50/24`**（ゲートウェイ `10.77.30.1`、DNS `10.77.20.10`）に変える（案。未確認）。画面（`192.168.11.2`）への入り方は、次の順に試す。
   1. **Mac を有線（ディスプレイ経由、p4）にしたまま、Mac に `192.168.11.50/24` を一時的に足す**（2026-11-17 に、この方法で入れた）。p3（Buffalo）と p4 は、同じ VLAN30 の中なので、同じ LAN の中でつながる。
      - `sudo ifconfig <有線のインターフェース> alias 192.168.11.50 255.255.255.0`、`sudo route add -net 192.168.11.0/24 -interface <有線のインターフェース>`。そのあと `http://192.168.11.2` を開く。
      - **`/32` のホスト経路（`route add -host 192.168.11.2 -interface ...`）は使えない**。macOS が、Mac 自身の MAC に解決してしまい（自分宛てと見なす）、Buffalo に問い合わせが出ない。経路は、`/24` で足す。
      - **Mac の Tailscale は、オフにする。** `vm-infra` が `192.168.11.0/24` を広告しているので、オンだと、Mac が `192.168.11.2` への通信を Tailscale 経由（`vm-infra` から出る）にして、届かない。
      - この間は、Mac から今の LAN の他の機器（Proxmox など）に届かなくなる。終わったら、`sudo route delete -net 192.168.11.0/24`、`sudo ifconfig <有線のインターフェース> -alias 192.168.11.50`、`sudo arp -d 192.168.11.2` で戻す。
   2. 届かなければ、Mac を Buffalo の LAN ポートに直接繋ぎ、Mac に `192.168.11.x` の固定 IP を一時的に振って、画面を開く。

   確認: [x] Wi-Fi の端末が `10.77.30.x` で繋がる（Mac の Wi-Fi が `10.77.30.103`。2026-11-17）　[x] Buffalo の画面に Trusted から入れる（`10.77.30.50` で、HTTP 200。Buffalo の IP を変え終えた。2026-11-17）　[ ] スマホなど、Mac 以外の Wi-Fi の端末も `10.77.30.x` で繋がる

## 3. Proxmox のホストを `vmbr0.10` に移す（段階 3b に移した。段階 3 では行わない）

> **段階 3b に移した**（[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。以下は、段階 3b の手順の下書き。リハーサルの結果（C-1）は反映済み。

**物理コンソール（または、自動で元に戻るタイマー）を、使える状態にして行う。**

1. 現在の `/etc/network/interfaces` を、退避する（戻すときに使う）。
2. `vmbr0` の IP を外し、タグ付きの `vmbr0.10` に `10.77.10.10/24`（ゲートウェイ `10.77.10.1`）を設定する。
3. 反映する。**`ifreload -a -n`（ドライラン）は、VLAN を作る設定ではエラーになる**（ifupdown2 の不具合。リハーサルで確認）ので、事前の検証には使えない。リハーサルでは、`ifup vmbr0.10` で `vmbr0.10` だけを上げて成功した（[リハーサル C-1](22-network-stage-3-rehearsal.md#c-1-vmbr010-の試験)）。当日は、`vmbr0` の IP を変えるので、`ifreload -a`（または再起動）が要る。物理コンソールかタイマーを必ず使う。
4. 確認: [ ] Proxmox が `10.77.10.10` で、Mac（Trusted）から届く。[ ] `nic0` が up で、e1000e の送信停止（`INC-2026-10-25`）が再発していない（`dmesg` に `Hardware Unit Hang` が出ていない）　[ ] VM が動き続けている

届かないとき: `vmbr0.10` を外し、退避した `/etc/network/interfaces` に戻す（[戻し方](#戻し方)の 2）。

p2 のスイッチ側の設定は、準備（手順 0）のまま（untagged VLAN1、tagged 10/20/40/50/70）で、変更は要らない。

## 4. `vm-omada` を `10.77.10.3` にする（段階 3b に移した。段階 3 では行わない）

> **段階 3b に移した**（[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。機器の接続先を直す手段が決まってから行う（[リハーサルの C-2](22-network-stage-3-rehearsal.md)）。以下は、下書き。

1. `vm-omada` の IP を `10.77.10.3`、VLAN を 10（`tag=10`）にする。
2. ER605・SG2210P が追従することを確かめる（手順 0 で確かめた手順）。追従しないときは、そこで書いた手順に従う（接続先の再設定、または機器のリセットと再採用）。

確認: [ ] コントローラーの画面で、ER605・SG2210P が接続済み。[ ] コントローラーに `10.77.10.3` で入れる

## 5. VM の IP と VLAN を変える（Terraform）

**`vm-infra` を最初にする**（DNS を先に戻す）。

0. `vm-omada` は、変えない（段階 3b まで、`192.168.11.12`・タグなし）。今の LAN の DHCP が配る DNS は、ルーター（`192.168.11.1`）にする（決定。[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。Wi-Fi の端末が Trusted に移った（手順 2 のあと）ら変える。今は、Wi-Fi の端末が AdGuard を外れるので、変えない。
1. `terraform apply` で、`vm-infra` の IP（`10.77.20.10`）と VLAN（20）を変える。VM ごとに分けるときは、`-target='module.vm["vm-infra"]'` のように指定する。`vm_state` は `ignore_changes` なので、止まっている `vm-dev` は、`apply` で起動しない（`vm-dev` だけの `apply` で確認済み。[リハーサルの D](22-network-stage-3-rehearsal.md#d-vm-dev-で-terraform-apply-を試す2026-11-11)）。**`apply` の前に、`plan` を見て、各 VM の VLAN タグの差分（`0 -> 20` など）が出ていること**を確かめる。apply で VM が再起動するときは、[apply による再起動](15-terraform-apply-restart.md)。
2. `vm-infra` が上がったら確認する: [ ] `10.77.20.10` で届く　[ ] AdGuard が `:53` で応答する
3. 残りの VM を、順に変える。

   | VM | IP | VLAN |
   | --- | --- | --- |
   | `vm-infra` | `10.77.20.10` | 20 |
   | `vm-monitoring` | `10.77.20.11` | 20 |
   | `vm-apps` | `10.77.20.20` | 20 |
   | `vm-code` | `10.77.20.30` | 20 |
   | `vm-dev`（止めたまま） | `10.77.40.10` | 40 |

   VMID は変えない（付け替えは、切り替えのあとの VM の作り直しで行う。[ADR-0026](../../adr/0026-vmid-from-vlan-and-octet.md)）。

   **実施の記録（2026-11-17）**: 新アドレスのコードを `docs/stage3-prep` に取り込み（`stage3/new-addresses` に本線を merge してから、本線を fast-forward）、`terraform plan` が「5 台の in-place 更新」になることを確かめた。`vm-infra`、`vm-monitoring`、`vm-apps`、`vm-code`、`vm-dev` の順に、`-target` で 1 台ずつ `apply` した。**IP とタグの変更でも、VM は自動で再起動する**（[Runbook 15](15-terraform-apply-restart.md)）。新しい IP で届くまで、約 12 秒（ping の 4 回目）。`vm-dev` は停止したまま、設定だけ変わった。最後の `terraform plan` は `No changes`。`vm_ips` の出力は、`-target` の途中では、ほかの VM の値が先に新しくなって見える。

   `vm-dev` は止めたまま、IP と VLAN の設定だけを変えられる（`vm-dev` だけの `apply` で確認済み。2026-11-11。[リハーサルの D](22-network-stage-3-rehearsal.md#d-vm-dev-で-terraform-apply-を試す2026-11-11)）。

## 6. Ansible で反映する

0. Mac の `~/.ssh/config` の `HostName` を、新しいアドレスに直す（`vm-infra` `10.77.20.10`、`vm-monitoring` `10.77.20.11`、`vm-apps` `10.77.20.20`、`vm-code` `10.77.20.30`、`vm-dev` `10.77.40.10`。`pve`・`vm-omada` は、段階 3b まで変えない）。IP を直接指定するときは、`-i ~/.ssh/id_ed25519_homelab` を付ける（`Host *` の `IdentitiesOnly yes` のため）。

1. `ansible-playbook` を流して、DNS のレコード、UFW、Caddy、Prometheus（scrape 対象）、Tailscale の経路を反映する（Terraform の VM ごとの `gateway`・`nameserver` は、手順 5 の `terraform apply` で変わる）。
2. **Tailscale**: 新しい経路（`10.77.20.0/24`、`10.77.40.0/24`）を、Admin Console で承認する。**旧経路（`192.168.11.0/24`）は外さない**（管理系が今の LAN に残るため。外すのは段階 3b のあと。[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。

   1. `ansible-playbook` の Tailscale の手順（`tailscale up --advertise-routes=10.77.20.0/24,10.77.40.0/24,192.168.11.0/24`）が終わると、新しい 2 経路は「承認待ち」になる（承認するまで、外出先からは届かない）。
   2. [Admin Console](https://login.tailscale.com/admin/machines) → Machines → `vm-infra` の「…」→ **Edit route settings** で、新しい 2 経路にチェックを入れて Save する。旧経路は、承認済みのまま。
   3. Split DNS（Nameserver `100.118.14.37`、`lab.kanare.dev`）と key expiry の無効化は、変えない（宛先は Tailscale の IP なので、`vm-infra` の LAN の IP が変わっても影響しない）。
   4. 外出先（スマホを Wi-Fi から外し、Tailscale をオン）から、`https://home.lab.kanare.dev` が開き、`vm-dev` に SSH で入れることを確かめる。

   確認: [x] `*.lab.kanare.dev` が新しい IP に解決される　[x] Caddy 経由のサービスが開く　[x] 外出先から、Tailscale 経由で入れる（`home.lab.kanare.dev`。2026-11-17）

**実施の記録（2026-11-17）と、わかったこと**:

- `~/.ssh/config` の `HostName` を直したあと、新しい IP の host key は、初回接続で `known_hosts` に入った（`StrictHostKeyChecking=accept-new`）。
- 先に `ansible-playbook playbooks/site.yml --check --diff` で確かめ、差分（Prometheus の scrape 対象、アラート、Caddyfile、CoreDNS のゾーン、UFW の許可元、Tailscale の経路）が、期待どおりであることを見た。`vm-dev` は停止中なので `unreachable` になる。本番は `--limit '!vm-dev'` で流した（`failed=0`）。
- チェックモードでだけ、`vm-monitoring` の「Download Node Exporter Full dashboard」が HTTP 405 で失敗した（grafana.com が確認用の要求を拒否するとみられる）。本番では通った。
- **Home Assistant の `trusted_proxies` は、Ansible では直らない**（`.storage/http` は、無いときだけ置く設定）。`vm-apps` の `/opt/homeassistant/config/.storage/http` の `trusted_proxies` を、旧 `vm-infra`（`192.168.11.11/32`）から `10.77.20.10/32` に、手で直す必要がある。直さないと、Caddy 経由で 400 になり、`ServiceProbeFailed`（ha）が出る。直し方: バックアップを取り、HA のコンテナを止めて、ファイルを直し、起動する。
- Tailscale の経路の承認は、2026-11-17 に済んだ（新しい 2 経路と、旧経路が承認済み）。
- **停止中の VM（`vm-dev`）は、Ansible の対象外になる。** 起動したときに、`ansible-playbook playbooks/site.yml --limit vm-dev` を流さないと、UFW の許可元が旧アドレス（`192.168.11.13`）のまま残り、Prometheus の `:9100` が `down` になる（2026-11-17 に、`vm-dev` を起動して流した。`up` を確認した）。

## 7. 疎通の確認

- [ ] 各 VLAN の DHCP と名前解決（`*.lab.kanare.dev`）。Trusted は確認した（Mac の有線・Wi-Fi が `10.77.30.x`、DNS `10.77.20.10` で、内部の名前が引ける。2026-11-17）。Lab は、`vm-dev` の中で、一時的な macvlan から DHCP を試して確認した（`10.77.40.100`、リース 24 時間、GW `10.77.40.1`、DNS `10.77.20.10`。2026-11-17）。Servers・DMZ は DHCP なし、IoT・Guests は、端末を繋いでいないので未確認
- [ ] 各 VLAN から Servers への接続（許可表のとおり）。Trusted → Servers と、Lab（`vm-dev`）→ Servers（`ping`、Caddy の 443）・旧 LAN（Proxmox の `:8006`）は確認した（ACL は全許可。2026-11-17）。IoT・Guests・DMZ は、端末を繋いでいない
- [x] Caddy 経由の各サービス、Omada・Proxmox の管理画面（2026-11-17。`home`・`grafana`・`omada`・`ha` が開く。Proxmox は `https://192.168.11.10:8006`）。**`vm-omada` の `:8043` へは、直接つなげない**（UFW は Caddy の `10.77.20.10` と、旧 LAN `192.168.11.0/24` からだけ許可）。管理画面へは、`https://omada.lab.kanare.dev`
- [x] Prometheus の全ターゲットが `up`（27 のうち 26。`down` は停止中の `vm-dev` だけ）。アラートは `Watchdog` だけ。`GatewayUnreachable` の宛先は、`10.77.20.1`（2026-11-17）
- [x] 外出先から Tailscale 経由で入れる（`https://home.lab.kanare.dev` に、外出先から入れた。2026-11-17。運用者の確認）。`vm-code`・`vm-dev` の SSH は、自宅の Mac から（Tailscale のサブネット経路が有効な状態で）通ることを確認した（`vm-dev` は起動して確認し、停止した。2026-11-17）。外出先（モバイル回線）からの SSH は、未確認
- [x] **自宅の Wi-Fi（Trusted）で、Tailscale をオンにした MacBook の通信経路を確かめた（2026-11-17。結論は下）**: 「サブネット経路を使う」がオンだと、Servers（`10.77.20.0/24`）・Lab（`10.77.40.0/24`）・旧 LAN（`192.168.11.0/24`）への通信が、ER605 を通らず Tailscale 経由（`vm-infra` が送信元）になる。`route -n get 10.77.20.10` で `interface: utun6` になり、`RouteAll: true` だった。
  - **決定（2026-11-17）: 自宅と外出先で設定を切り替えない。** Tailscale は常にオン、「サブネット経路を使う」もオンのままにする。自宅でも外出先でも、同じ設定と同じ経路になる。
  - 受け入れること: (1) この Mac の通信は、ER605 の ACL の対象にならない（ACL が守る相手は、Lab・IoT・Guests・DMZ の信用しない端末。運用者の Mac は、もともと Trusted で、Servers に入れる側）。(2) 自宅でも、`vm-infra` が止まると、Mac から Servers・Proxmox に入れない（保険は、緊急用の入口 p6。手順 8 の前提）。(3) 手順 8 の ACL の確認は、**この Mac では行わず、別の端末**（Trusted のスマホ、Lab の `vm-dev`）で行う。
- [x] メインディスプレイ、MacBook、Wi-Fi の端末（Trusted）（2026-11-17。Mac の有線（p4）・Wi-Fi が `10.77.30.x`、スマホの Wi-Fi から `home.lab.kanare.dev` が開く）
- [ ] テレビ（無線、Trusted）の AirPlay・Cast
- [x] Healthchecks.io の heartbeat（2026-11-17。運用者の確認で ok）
- （気づき）AdGuard のキャッシュと、Mac の DNS キャッシュに、旧 IP が残る。`vm-infra` を移したあと、AdGuard の画面で、キャッシュをクリアする（設定 > DNS 設定）。Mac は、Wi-Fi をオフ・オンにする（`sudo` が使えれば、`dscacheutil -flushcache` と `killall -HUP mDNSResponder`）。Chrome は、`chrome://net-internals/#dns` で、ホストのキャッシュをクリアする
- （気づき）VM のホスト DNS は、ルーター（`10.77.20.1`）なので、VM から内部の名前が引けない。**既定の設計**（[ADR-0007](../../adr/0007-vm-host-dns-is-router.md)）。AdGuard が要るコンテナだけ、`docker-compose.yml` の `dns:` で指定している（[ロードマップ 01](../roadmap/01-backlog.md#ネットワークdns)）。

## 8. ACL を絞る（別の日）

**当日は行わない**（[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）。当日は、ACL を全許可のまま（`rh-` のルールは無効のまま。ルールに一致しない通信は暗黙に許可される）にする。段階 3 のあと数日動かして落ち着いてから、別の日に行う。**段階 3 の完了から 2 週間以内を目安に、優先して行う（決定 2026-11-11）。**

前提（絞る日の前に）:

- [ ] **今の LAN（VLAN1）の ACL を作って、実機で確かめた**（[ADR-0028](../../adr/0028-defer-management-vlan10.md)）: 段階 3b までの暫定。ルールの案は[ロードマップ 13](../roadmap/13-defer-management-vlan.md#今の-lan-の-acl段階-3b-までの暫定)にある。
- [ ] **緊急用の入口を決めて、届くことを確かめた**（[ADR-0028](../../adr/0028-defer-management-vlan10.md)）: `vm-infra` が止まったとき、または ACL を絞り間違えたときに、直接 Proxmox・`vm-omada`・ER605 に入れる口。空きポートを 1 つ決める（今は p5〜p8 が、今の LAN に入る設定）。そのポートに繋いだ端末が、今の LAN の DHCP でアドレスを受け取り、`192.168.11.10`（Proxmox）、`192.168.11.12`（`vm-omada`）、`192.168.11.1`（ER605）に届く。決めたポート: **p6**（決定 2026-11-10）

ACL を、[通信ポリシー](../../architecture/hld/05-network.md#通信ポリシー)の許可表の内容に絞る。**ログを見ながら、1 つずつ絞る**。絞るたびに、手順 7 の主な項目を確かめる。ルールの名前と説明は、[ACL の名前と説明の付け方](../../architecture/lld/network/acl.md)に従う（リハーサルの `rh-` のルールは、ここで削除し、本番のルールを作る）。絞り間違えて Trusted から管理系に届かなくなったら、緊急用の入口から `vm-omada` に入り、そのルールを無効にする。

- [ ] 拒否すべき通信が拒否される（Lab・Guests・IoT・DMZ から内部へ。IoT → Trusted。Trusted → Guests）（**確認は、運用者の Mac では行わない**。Mac は Tailscale 経由で ER605 の ACL を通らないため、「拒否されるはずなのに通る」と見える。Trusted のスマホ、Lab の `vm-dev` など、Mac 以外の端末で確かめる。手順 7 の決定）
- [ ] 許可すべき通信が通る（Trusted → Servers、Servers → 今の LAN（管理系）の Caddy と node_exporter、Tailscale 経由の Lab）

## 9. 旧ネットワークを片づける

- [ ] 旧ネットワーク（VLAN1、`192.168.11.0/24`）は、**止めない・消さない**（管理系が使う。[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。段階 3b のあとに、消せるか確かめる
- [x] リハーサル用のポート（p5・p6）は、未使用に戻してある（2026-11-09）
- [x] **コントローラーのバックアップを取り**、iCloud Drive に保存した（2026-11-17 22:01。`omada_backup_...2026-11-17_22-01-59.cfg` と `sitebackup_...2026-11-17_22-01-49.cfg`。p3・p4 の `access-trusted` の割り当てが入った状態）

## 10. 作業の後始末

1. **同じ変更で直す**（[設計書](../roadmap/10-er605-sg2210p-migration-plan.md)）:
   - Prometheus の scrape 対象とアラート、[監視・アラート](../../architecture/lld/platform/monitoring.md)を更新し、Omada コントローラーの死活監視を足す。
   - 各文書に残る旧アドレス（`192.168.11.`）を直す。[IP アドレス一覧](../../architecture/lld/network/ip-addresses.md)の「現在」を「移行後」に合わせる（移行が済んだことを書く）。
   - 構成図: to-be の構成図（`to-be-diagram/`）を確認する。現状の構成図（`as-is-diagram/`）は、実機に合わせて更新する（段階 3 の分は、2026-11-17 に作成した）。`as-is-diagram/` は、削除せず、実機の状態に保つ（2026-11-19 に方針を変えた）。
2. 機器の設定文書を、実際の値に合わせる: [ER605](../../architecture/lld/network/omada-controller.md#er605ルーター)、[SG2210P](../../architecture/lld/network/omada-controller.md#sg2210pスイッチ)、[Buffalo](../../architecture/lld/network/wsr-1800ax4p.md)、[ThinkCentre](../../architecture/lld/platform/proxmox-host.md)。変更履歴に 1 行ずつ足す。
3. 実際の所要時間と、リハーサルや当日の結果（追従の可否、`vmbr0.10`、既定の LAN を消せたか）を、[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)に記録する。
4. Buffalo は、段階 4（AP の導入）まで、AP として使い続ける。

## 戻し方

戻す時刻は決めない（[ADR-0030](../../adr/0030-stage3-no-rollback-deadline.md)）。この手順は、機器の故障など、その日のうちに完了できない事情が出たときに使う。上から順に戻す。

1. **SG2210P のポートを、段階 2 の設定（VLAN なし）に戻す。** ER605 の VLAN は無効にし、既定の LAN（`192.168.11.0/24`）を有効に戻す。
2. **Proxmox を、物理コンソールから `192.168.11.10`（退避した `/etc/network/interfaces`）に戻す**（段階 3 では、ホストを動かしていないので、通常は不要）。
3. **`terraform.tfstate` を戻し、`terraform apply` する**（旧アドレスのコードが入ったブランチで）。
4. **コントローラーが使えないとき**: ER605 をリセットして、GUI から `192.168.11.1` を設定する。さらに戻す場合は、段階 1・2 の戻し方（Buffalo をルーターモードに戻す。[当日の作業](20-network-cutover-stage-1-2.md#戻し方)）。

戻したあとに、Proxmox、全 VM、インターネット、DNS、Tailscale を確認する。
