# 段階 3 の当日の作業（VLAN と `10.77.x.x` への一斉切り替え）

VLAN を有効にし、全ホストの IP を `192.168.11.x` から `10.77.<VLAN>.x` に付け替える日の手順。**ホストのアドレス付け替えは 1 回だけ**（[ADR-0004](../../adr/0004-vlan-cutover-all-at-once.md)）。段階 1・2（[当日の作業](20-network-cutover-stage-1-2.md)）が済んでいることが前提。作業時間は、数時間を見込む。

- 当日の順にチェックしながら進めるための文書。手順の根拠と、決めた経緯は[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)の「段階 3」と、[VLAN 設計](../../architecture/08-vlan-design.md)にある。手順を変えたら、計画も同じ変更で直す。
- 新しい IP は [IP アドレス一覧](../../architecture/09-ip-addresses.md)、設定の対応表（ER605 の VLAN インターフェース、SG2210P のポート、Proxmox）は計画の「3-B」にある。
- 秘密の値と、機器の MAC アドレスは、この文書に書かない（台帳へ。[シークレット](03-secrets.md)）。
- **管理系（Proxmox ホスト、`vm-omada`、ER605・SG2210P）は、段階 3 では動かさない**（[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。手順 3・4 は、段階 3b に移した（この文書では行わない。下書きとして残す）。今の LAN（VLAN1）は、止めず、消さない。
- **ACL は、当日は全許可のまま切り替え、絞るのは別の日に行う**（[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）。手順 8 は、別の日の作業。
- **この文書は、実機でのリハーサルの前に書いた。** リハーサルの結果は、[リハーサル](22-network-stage-3-rehearsal.md)にある。結果で、手順が変わりうる。

## 0. 前提の確認（開始の前に）

計画の「3-A. 準備」が、すべて済んでいること。

- [ ] **リハーサルが済んでいる**: 検証端末を SG2210P の p5（VLAN30）と p6（VLAN50）に繋ぎ、本番と同じ設定で次を確かめた。
  - Gateway ACL で、Trusted → IoT は通り、IoT → Trusted は拒否される。戻りの通信が通る。末尾の全拒否が効く。
  - DHCP が VLAN ごとに配る（DNS は `10.77.20.10`）。
- [ ] **（段階 3b に移した。段階 3 では不要）コントローラーの IP 変更への追従を確かめた**: `vm-omada` が `192.168.11.12` から `10.77.10.3` に変わったとき、ER605 と SG2210P が付いてくる。付いてこない場合の手順（接続先の再設定、または機器のリセットと再採用）を、リハーサルで確かめて書いてある。
- [ ] **Proxmox の準備が済んでいる**（[ADR-0023](../../adr/0023-proxmox-trunk-all-tagged.md)）: `vmbr0` が VLAN-aware（IP は `192.168.11.10`・タグなしのまま）。SG2210P p2 に tagged 10/20/40/50/70 を足してある。1 つの検証用 VM をタグ付きで繋いで、動作を確かめた。
- [ ] **コードの準備が済んでいる**: 別ブランチで、Terraform（`vlan_id` は必須で、全 VM に指定。`vm-omada` は、段階 3b まで、タグなし（VLAN1）を明示する）、Ansible、Caddyfile、Prometheus、Homepage、ドキュメントを、新アドレスに書き換えてある（一覧は[設計書](../../architecture/08-vlan-design.md#影響を受けるリポジトリ内の箇所)）。 UFW の許可元も、新しいアドレスに直す（`vm-infra` の 8043、`vm-monitoring` の 9100。`vm-omada` は段階 3 で動かさないので、**直し忘れやすい**。[ロードマップ 13](../roadmap/13-defer-management-vlan.md)）。
- [ ] **新アドレスのコードを、現行のブランチに取り込んだ**（[ブランチ運用](../roadmap/10-er605-sg2210p-migration-plan.md#段階-3-のブランチ運用)）。`terraform plan` が、5 台の in-place 更新（`vm-omada` は変わらない）になっている。
- [x] **Omada に本番の設定を作ってある（有効にはしていない）**（2026-11-11。一覧は[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md#omada-の本番設定の一覧段階-3-の準備画面操作)）: VLAN 10/20/30/40/50/60/70（端末は繋いでいない）、DHCP、mDNS の中継（無効のまま）、スイッチのポートプロファイル `access-trusted`（どのポートにも未割り当て）。**ACL は作っていない**（当日は全許可。[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）。設定したあとのバックアップ: `omada_backup_...2026-11-11_21-48-24.cfg` と `sitebackup_...2026-11-11_21-48-31.cfg`（iCloud Drive）。
- [ ] **今の LAN の DHCP の DNS をルーターにする手順を確認した**（決定済み。変えるのは、手順 2 で Wi-Fi の端末が Trusted に移ったあと）。
- [x] **バックアップが、Mac 以外にもある**（iCloud Drive の `homelab/`。2026-11-11 に取得）: Omada（`omada_backup_...2026-11-11_21-06-24.cfg` と `sitebackup_...2026-11-11_21-04-37.cfg`）、Proxmox の `/etc/network/interfaces`（`pve-interfaces-bk-20261111.txt`）、`terraform.tfstate`（`terraform.tfstate-bk-20261111`）、Buffalo の設定（`wsr-1800ax4p-bk-20261103*.bin`）。Omada に本番の設定を作る前の状態なので、**当日の手順 1 で、もう一度取る**。
- [x] Tailscale の経路の承認の手順を確認してある（`--advertise-routes=10.77.20.0/24,10.77.40.0/24,192.168.11.0/24`。手順は 6.2）。2026-11-11 に Admin Console で確認した: `vm-infra` は `192.168.11.0/24` が承認済みで、Expiry disabled。**自動承認（Auto approvers）は無い**ので、新しい 2 経路は当日に手動で承認する。
- [ ] 戻し方（下記）を読んだ。

## 1. 開始

- **戻す時刻は決めない**（決定 2026-11-10、[ADR-0030](../../adr/0030-stage3-no-rollback-deadline.md)）。完了するまで作業する。
- [ ] 作業中にインターネットが要るとき（調べもの、ファームウェアの取得）に、端末を建物（壁）の Wi-Fi に繋げることを確かめておく。
- [ ] 物理コンソール（キーボードとモニター）を、Proxmox にすぐ繋げられる状態にする（成功すれば使わない。ホストのネットワーク設定を誤ると、SSH も Web UI も使えなくなるための保険）。自動で元に戻るタイマーを仕掛ける方法もある（[リハーサル](22-network-stage-3-rehearsal.md)の B）。
- [ ] Mac に、有線の口（手順 2 で Buffalo の画面に入るときに使う）と、固定 IP を振る手段がある。外出先との確認用に、スマホを用意する。
- [ ] 作業中に出るアラート（`GatewayUnreachable`、`TargetDown`、`PveVmStopped`、Heartbeat）は、想定内。

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
3. Buffalo は Trusted に入る。Wi-Fi の端末は、`10.77.30.x` を受け取る。**Buffalo の IP は `192.168.11.2` のまま残るので、管理画面には Trusted から届かなくなる**（Wi-Fi の中継は、IP と関係なく動く）。
4. 落ち着いてから、Mac を Buffalo の LAN ポートに直接繋ぎ、Mac に `192.168.11.x` の固定 IP を一時的に振って、Buffalo の画面（`192.168.11.2`）を開く。Buffalo の IP を **`10.77.30.50/24`**（ゲートウェイ `10.77.30.1`、DNS `10.77.20.10`）に変える（案。未確認）。

   確認: [ ] Wi-Fi の端末が `10.77.30.x` で繋がる　[ ] Buffalo の画面に Trusted から入れる

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
1. `terraform apply` で、`vm-infra` の IP（`10.77.20.10`）と VLAN（20）を変える。VM ごとに分けるときは、`-target='module.vm["vm-infra"]'` のように指定する。`-target` を付けないと、手動起動の `vm-dev` も `running` にする差分が一緒に適用される（[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)）。apply で VM が再起動するときは、[apply による再起動](15-terraform-apply-restart.md)。
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

   `vm-dev` は止めたまま、IP と VLAN の設定だけを変えられるかは、未確認（apply で起動してしまわないか、リハーサルで確かめる）。

## 6. Ansible で反映する

1. `ansible-playbook` を流して、DNS のレコード、UFW、Caddy、Prometheus（scrape 対象）、Tailscale の経路を反映する（Terraform の `gateway` と `ansible/inventory/group_vars/all/vars.yml` の `gateway` も、新しい値）。
2. **Tailscale**: 新しい経路（`10.77.20.0/24`、`10.77.40.0/24`）を、Admin Console で承認する。**旧経路（`192.168.11.0/24`）は外さない**（管理系が今の LAN に残るため。外すのは段階 3b のあと。[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。

   1. `ansible-playbook` の Tailscale の手順（`tailscale up --advertise-routes=10.77.20.0/24,10.77.40.0/24,192.168.11.0/24`）が終わると、新しい 2 経路は「承認待ち」になる（承認するまで、外出先からは届かない）。
   2. [Admin Console](https://login.tailscale.com/admin/machines) → Machines → `vm-infra` の「…」→ **Edit route settings** で、新しい 2 経路にチェックを入れて Save する。旧経路は、承認済みのまま。
   3. Split DNS（Nameserver `100.118.14.37`、`lab.kanare.dev`）と key expiry の無効化は、変えない（宛先は Tailscale の IP なので、`vm-infra` の LAN の IP が変わっても影響しない）。
   4. 外出先（スマホを Wi-Fi から外し、Tailscale をオン）から、`https://home.lab.kanare.dev` が開き、`vm-dev` に SSH で入れることを確かめる。

   確認: [ ] `*.lab.kanare.dev` が新しい IP に解決される　[ ] Caddy 経由のサービスが開く　[ ] 外出先（スマホを Wi-Fi から外す）から、Tailscale 経由で入れる

## 7. 疎通の確認

- [ ] 各 VLAN の DHCP と名前解決（`*.lab.kanare.dev`）
- [ ] 各 VLAN から Servers への接続（許可表のとおり）
- [ ] Caddy 経由の各サービス、Omada・Proxmox の管理画面
- [ ] Prometheus の全ターゲットが `up`。`GatewayUnreachable` は、新しい IP に直す
- [ ] 外出先から Tailscale 経由で、`vm-code`・`vm-dev` に入れる
- [ ] **自宅の Wi-Fi（Trusted）で、Tailscale をオンにした MacBook の通信経路を確かめる**: Tailscale の「サブネット経路を使う」がオンだと、Servers（`10.77.20.0/24`）・Lab（`10.77.40.0/24`）への通信が、ER605 を通らず Tailscale 経由（`vm-infra` が送信元）になりうる。そうなると、手順 8 で絞る ACL が効かない。経路は `tailscale status` や `route -n get 10.77.20.10` で見る。経路が Tailscale 経由なら、自宅では「サブネット経路を使う」をオフにする（外出先でだけ使う）。手順 8 の前に結論を出す。
- [ ] メインディスプレイ、MacBook、Wi-Fi の端末（Trusted）
- [ ] テレビ（無線、Trusted）の AirPlay・Cast
- [ ] Healthchecks.io の heartbeat

## 8. ACL を絞る（別の日）

**当日は行わない**（[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）。当日は、ACL を全許可のまま（`rh-` のルールは無効のまま。ルールに一致しない通信は暗黙に許可される）にする。段階 3 のあと数日動かして落ち着いてから、別の日に行う。**遅くとも段階 4 の前に済ませる。**

前提（絞る日の前に）:

- [ ] **今の LAN（VLAN1）の ACL を作って、実機で確かめた**（[ADR-0028](../../adr/0028-defer-management-vlan10.md)）: 段階 3b までの暫定。ルールの案は[ロードマップ 13](../roadmap/13-defer-management-vlan.md#今の-lan-の-acl段階-3b-までの暫定)にある。
- [ ] **緊急用の入口を決めて、届くことを確かめた**（[ADR-0028](../../adr/0028-defer-management-vlan10.md)）: `vm-infra` が止まったとき、または ACL を絞り間違えたときに、直接 Proxmox・`vm-omada`・ER605 に入れる口。空きポートを 1 つ決める（今は p5〜p8 が、今の LAN に入る設定）。そのポートに繋いだ端末が、今の LAN の DHCP でアドレスを受け取り、`192.168.11.10`（Proxmox）、`192.168.11.12`（`vm-omada`）、`192.168.11.1`（ER605）に届く。決めたポート: **p6**（決定 2026-11-10）

ACL を、[通信ポリシー](../../architecture/08-vlan-design.md#通信ポリシー)の許可表の内容に絞る。**ログを見ながら、1 つずつ絞る**。絞るたびに、手順 7 の主な項目を確かめる。ルールの名前と説明は、[ACL の名前と説明の付け方](../../architecture/08-vlan-design.md#acl-の名前と説明の付け方)に従う（リハーサルの `rh-` のルールは、ここで削除し、本番のルールを作る）。絞り間違えて Trusted から管理系に届かなくなったら、緊急用の入口から `vm-omada` に入り、そのルールを無効にする。

- [ ] 拒否すべき通信が拒否される（Lab・Guests・IoT・DMZ から内部へ。IoT → Trusted。Trusted → Guests）
- [ ] 許可すべき通信が通る（Trusted → Servers、Servers → 今の LAN（管理系）の Caddy と node_exporter、Tailscale 経由の Lab）

## 9. 旧ネットワークを片づける

- [ ] 旧ネットワーク（VLAN1、`192.168.11.0/24`）は、**止めない・消さない**（管理系が使う。[ADR-0028](../../adr/0028-defer-management-vlan10.md)）。段階 3b のあとに、消せるか確かめる
- [x] リハーサル用のポート（p5・p6）は、未使用に戻してある（2026-11-09）
- [ ] **コントローラーのバックアップを取り**、iCloud Drive に保存する（`omada-bk-YYYYMMDD.cfg`）

## 10. 作業の後始末

1. **同じ変更で直す**（[設計書](../../architecture/08-vlan-design.md#切り替え後)）:
   - Prometheus の scrape 対象とアラート、[監視・アラート](../../services/platform/monitoring.md)を更新し、Omada コントローラーの死活監視を足す。
   - 各文書に残る旧アドレス（`192.168.11.`）を直す。[IP アドレス一覧](../../architecture/09-ip-addresses.md)の「現在」を「移行後」に合わせる（移行が済んだことを書く）。
   - 構成図: メインの構成図（`main-diagram/`）を確認し、**移行前の構成図（`pre-migration-diagram/`）を削除する**。
2. 機器の設定文書を、実際の値に合わせる: [ER605](../../hardware/er605/settings.md)、[SG2210P](../../hardware/sg2210p/settings.md)、[Buffalo](../../hardware/wsr-1800ax4p/settings.md)、[ThinkCentre](../../hardware/thinkcentre-m70q-tiny/settings.md)。変更履歴に 1 行ずつ足す。
3. 実際の所要時間と、リハーサルや当日の結果（追従の可否、`vmbr0.10`、既定の LAN を消せたか）を、[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)に記録する。
4. Buffalo は、段階 4（AP の導入）まで、AP として使い続ける。

## 戻し方

戻す時刻は決めない（[ADR-0030](../../adr/0030-stage3-no-rollback-deadline.md)）。この手順は、機器の故障など、その日のうちに完了できない事情が出たときに使う。上から順に戻す。

1. **SG2210P のポートを、段階 2 の設定（VLAN なし）に戻す。** ER605 の VLAN は無効にし、既定の LAN（`192.168.11.0/24`）を有効に戻す。
2. **Proxmox を、物理コンソールから `192.168.11.10`（退避した `/etc/network/interfaces`）に戻す**（段階 3 では、ホストを動かしていないので、通常は不要）。
3. **`terraform.tfstate` を戻し、`terraform apply` する**（旧アドレスのコードが入ったブランチで）。
4. **コントローラーが使えないとき**: ER605 をリセットして、GUI から `192.168.11.1` を設定する。さらに戻す場合は、段階 1・2 の戻し方（Buffalo をルーターモードに戻す。[当日の作業](20-network-cutover-stage-1-2.md#戻し方)）。

戻したあとに、Proxmox、全 VM、インターネット、DNS、Tailscale を確認する。
