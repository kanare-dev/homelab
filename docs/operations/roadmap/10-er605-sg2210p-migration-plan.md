# ER605・SG2210P の移行計画

[ロードマップ](README.md)の大型計画 [Omada 導入・VLAN 化](04-network-omada-vlan.md)の段階 1〜3 を、実機を手に入れた前提で具体化した計画。AS-IS と TO-BE の構成図、機器の設定、配線の付け替えを段階ごとに書く。

**状態: 検討中（未適用）。** 方針（段階の分け方、`10.77.<VLAN>.0/24`、一斉切り替え、ER605 を先に導入）は採用済みで、[VLAN 設計](../../architecture/08-vlan-design.md)と ADR（[0004](../../adr/0004-vlan-cutover-all-at-once.md)、[0009](../../adr/0009-router-er605-first.md)、[0015](../../adr/0015-vlan-address-scheme-10-77.md)、[0022](../../adr/0022-vlan-set-and-ids.md)）が正。この文書の「ポートの割り当て」「作業の順序」「戻し方」は、まだ採用していない案。採用したら、設計書の該当箇所に移し、ここは設計書へのリンクに置き換える（[文書の運用](../../README.md#文書の運用)）。

## 前提

機器は ER605 と SG2210P を購入済み。AP は段階 4 で買う（この文書の対象外）。

| 項目 | 内容 | 確認 |
| --- | --- | --- |
| 現在の有線 | Buffalo の LAN ポートに、Proxmox とメインディスプレイ（MacBook や仕事用の Windows ノート PC を接続する）。テレビは無線 | 運用者に確認済み |
| 設置場所 | Buffalo はテレビの裏。ER605 と SG2210P は Proxmox のそばに置く | 運用者に確認済み |
| 上流 | 建物の共用ルーター（`172.22.0.1`）。ER605 の WAN は DHCP で受ける | 設計書より |
| ER605 の版 | V2 | **本体の表示で確認する**（[段階 0](#段階-0-事前準備)） |
| SG2210P の版 | Omada に対応する版（v3.2 または v5 以降。v4 は非対応という記載がある） | **本体の表示で確認する** |
| 長いケーブル | 3 本ある。A: 壁 → Buffalo の WAN、B: Buffalo → Proxmox、C: Buffalo → メインディスプレイ | 運用者に確認済み。A と B は移行で使い回す（[ケーブル](#ケーブルと電源)） |

設計書の「テレビは有線で接続している」という記載は、実際は無線のため食い違っている（[未確認・要判断](#未確認要判断の事項)）。

## AS-IS（現在）

```text
 建物の共用ルーター (172.22.0.1)
        │ 壁の LAN ポート
        │ WAN
 ┌──────┴────────────────────────────────┐
 │ Buffalo WSR-1800AX4P（テレビの裏）     │  192.168.11.1/24
 │ ルーターモード / DHCP / NAT / Wi-Fi    │  DHCP プール .60–.99
 └───┬──────────────┬─────────────────────┘
     │ LAN          │ LAN                       Wi-Fi: スマホ、Mac、テレビ（無線）、
     │              │                                   ESP32（現在は未使用）
     │              └── メインディスプレイ ── MacBook / 仕事用 Windows PC
     │
 ┌───┴──────────────────────────────────────────────┐
 │ Proxmox ThinkCentre M70q（NIC 1 つ、192.168.11.10） │
 │  vm-infra .11 / vm-monitoring .13 / vm-apps .20     │
 │  vm-code .22 / vm-dev .21 / vm-windows              │
 └─────────────────────────────────────────────────────┘
```

- 全部が `192.168.11.0/24` の 1 つのネットワーク。VLAN なし。
- VM のゲートウェイとホスト DNS は Buffalo（`192.168.11.1`）。
- 管理画面は `router.lab.kanare.dev`（Caddy → `192.168.11.1:80`）。

## TO-BE（段階ごとの到達点）

### 段階 1 の後: ER605 に交換、Buffalo は AP

```text
 共用ルーター ─ WAN ─ ER605 V2 (192.168.11.1/24)
                      │ LAN               │ LAN
                      │                   └── Buffalo（AP モード、192.168.11.2、テレビの裏）
                      │                          ├── メインディスプレイ
                      │                          └── Wi-Fi（SSID は今のまま）
                      └── Proxmox (192.168.11.10)
                           └── vm-omada (192.168.11.12)  ← 新設。ER605 を採用する
```

IP は変えない。Buffalo の Wi-Fi 設定は今のままなので、端末側の設定変更は要らない。

### 段階 2 の後: SG2210P を追加

```text
 共用ルーター ─ WAN ─ ER605 V2 (192.168.11.1/24)
                      │ LAN
                 SG2210P（VLAN なし。192.168.11.x、DHCP）
                  ├─ p2 ── Proxmox (192.168.11.10) ── vm-omada ほか
                  └─ p3 ── Buffalo（AP モード）── メインディスプレイ、Wi-Fi
```

ネットワークは 1 つのまま。配線をスイッチ経由にして、段階 3 の作業を減らすのが目的。

### 段階 3 の後: VLAN と `10.77.x.x`（有線の最終形）

```text
 共用ルーター ─ WAN ─ ER605 V2（VLAN ごとに GW .1、ACL で通信を制限）
                      │ p1: trunk（VLAN 10/20/30/40/50/60/70 を tag 付き）
                 SG2210P (10.77.10.2)
                  ├─ p2 ── Proxmox ［trunk: native=10、tag=20/40/50/70］
                  │          ├─ VLAN10 Management : Proxmox 10.77.10.10 / vm-omada 10.77.10.3
                  │          ├─ VLAN20 Servers    : vm-infra .11 / vm-monitoring .13 / vm-apps .20 / vm-code .22
                  │          ├─ VLAN40 Lab        : vm-dev 10.77.40.21 ほか
                  │          └─ VLAN70 DMZ        : （VLAN とルールだけ。置くものは後）
                  ├─ p3 ── Buffalo（AP モード）［access: VLAN30 Trusted］
                  │          ├─ メインディスプレイ（Trusted）
                  │          └─ Wi-Fi 全端末（Trusted。段階 4 まで SSID は 1 つ）
                  ├─ p4–p6 空き（予備、リハーサル用）
                  └─ p7–p8 空き（段階 4 の AP 用に PoE を残す）
```

`vm-omada` の `10.77.10.3` と SG2210P の `10.77.10.2` は案（[VLAN 設計](../../architecture/08-vlan-design.md#固定アドレス)の採番は機器購入後に確定とされている）。

### 段階 4 の後

AP を SG2210P の p7（PoE）に繋ぎ、SSID を 3 つ（Trusted / IoT / Guest）にする。詳細は [04 の段階 4](04-network-omada-vlan.md#段階-4-apeap)。テレビは IoT の SSID に移し、そのとき Trusted ↔ IoT の mDNS 中継を実機で確認する。

## ケーブルと電源

今ある長いケーブル 3 本（A: 壁 → Buffalo の WAN、B: Buffalo → Proxmox、C: Buffalo → ディスプレイ）を使い回す。新しい長いケーブルは要らない。並行稼働はしないので、A と B は付け替えるだけでよい。

| 区間 | 段階 | ケーブル | 備考 |
| --- | --- | --- | --- |
| 壁の LAN ポート → ER605 WAN | 1 | A を使い回す | ER605 は Proxmox のそばに置く。A が壁から ER605 の置き場所まで届くか、置く前に確認する |
| ER605 LAN → Buffalo（AP の上流側） | 1 | B を使い回す | B は Buffalo から Proxmox のそばまで届いている。段階 2 では、同じ B を SG2210P p3 に付け替える |
| ER605 LAN → Proxmox | 1 | 短いケーブルを 1 本買う（0.5〜1m） | 段階 2 で SG2210P p2 に付け替える |
| ER605 LAN → SG2210P p1 | 2 | 短いケーブルを 1 本買う（0.3〜0.5m） | |
| メインディスプレイ → Buffalo LAN | — | C のまま | AP モードの Buffalo は有線ハブとして働くので、付け替えない |
| テレビ → Buffalo LAN | 後で | 運用者がそのうち買う | 有線のテレビは、AP モードの Buffalo のポートでは Trusted になる（[未確認・要判断](#未確認要判断の事項)） |
| リハーサル用 | 3 | 短いケーブル × 2 | p5・p6 に繋ぐ検証端末用 |

- 電源は ER605（DC アダプター）、SG2210P、Buffalo、ThinkCentre。電源タップの空きと、停電時の扱い（UPS なし）を確認する。
- ケーブルは CAT6 以上。ラベルを両端に貼る（`ER605-LAN1` など）。

## 段階 0: 事前準備

ネットワークを止めない作業。

- [ ] ER605 の版を本体の表示で確認する（V2 であること）。SG2210P の版も確認する（v4 でないこと）。
- [ ] 現在の Buffalo の設定を控える。値は `private/secrets-inventory.md` の側に置き、リポジトリには書かない。
  - 設定のバックアップファイル（管理画面の「設定保存」）
  - DHCP のプール、固定割り当て（予約）の一覧、DHCP が配る DNS サーバー
  - WAN の取得方法、SSID 名、暗号化方式（パスフレーズは台帳へ）
- [ ] ER605 のファームウェアを更新する。先に更新し、LAN の IP は後で変える。
  - 初期の LAN は `192.168.0.1`。Buffalo の `192.168.11.0/24` とも上流の `172.22.x.x` とも被らない。
  - ER605 の WAN を Buffalo の空き LAN ポートに繋ぎ（一時的な二重ルーター）、Mac を ER605 の LAN に繋いで更新する。
  - **ER605 の LAN を `192.168.11.1` に変えるのは、WAN を外してから。** WAN 側（Buffalo の LAN）と同じ範囲になると、ルーターが正しく動かない。
- [ ] ER605 の LAN を `192.168.11.1/24` に変え、DHCP プールと配る DNS を Buffalo の今の値に合わせる。管理画面のパスワードを変える（台帳へ）。
- [ ] `vm-omada` を立てる（Terraform の `vms` に追加。IP は `192.168.11.12`、VMID は `112`）。
  - 案: Ubuntu VM + Docker Compose で Omada コントローラーを動かす。VM か LXC か Docker かは VLAN 設計の未決事項で、ここで決める。
  - コントローラーは、mDNS の中継に v5.9 以降が要る（設計書より）。ER605 V2 と SG2210P の対応を公式の対応表で確認してから版を選ぶ。
  - バックアップの保存先を決める（Mac だけにしない）。
- [ ] `vm-omada` のホスト DNS と、バックアップ、監視（Prometheus の scrape、死活監視）を設計に加える。
- [ ] 停止してよい時間帯を決める（段階 1 は 30 分〜1 時間の見込み）。

## 段階 1: ER605 に交換、Buffalo は AP

アドレスは変えない。止まる時間は、配線の付け替えと ER605 の起動を合わせて 10 分前後の見込み。

### 段階 1 の作業

1. 家族や他の利用者に、止めることを伝える。
2. Buffalo を AP（ブリッジ）モードにする。IP は `192.168.11.2` の固定にする（案）。Buffalo の機種によって、背面のスイッチで切り替える場合と、管理画面で切り替える場合がある。**モードを変えると、Wi-Fi の設定が初期化されないか、段階 0 の控えと見比べて確認する。**
3. 配線を付け替える。
   - 壁の LAN ポート → ER605 の WAN（ケーブル A）
   - ER605 の LAN → Proxmox（短い新しいケーブル）
   - ER605 の LAN → Buffalo（ケーブル B。AP モードの Buffalo の上流側。WAN ポートも LAN として働く場合があるので、取扱説明書で確認する）
   - メインディスプレイは Buffalo の LAN に繋いだまま
4. ER605 を起動する。まだコントローラーに採用していないので、ER605 の GUI のまま、ルーター・DHCP・NAT として動く。
5. 確認する（コントローラーに採用する前に）。
   - Mac を取得し直し（DHCP の更新）、インターネットと Proxmox（`192.168.11.10`）に届く。
   - Wi-Fi の端末が、今の SSID のまま繋がる。
   - 外出先（Tailscale）から入れる。
6. `vm-omada` から ER605 を採用する（同じ `192.168.11.0/24` なので自動で見つかる）。**採用すると、ER605 の GUI は使えなくなる。** 採用後にファームウェア、時刻（NTP）、管理者アカウントを設定する。
7. Omada コントローラーのバックアップを取り、Mac 以外にも保存する。

### 同じ変更で直すもの

[DNS 構成の「ルーターを付け替えるとき」](../../services/01-dns.md#ルーターを付け替えるとき)に従う。

- `docker/compose/reverse-proxy/Caddyfile`: `router.lab.kanare.dev` の転送先を、Omada コントローラーの管理画面（HTTPS、`tls_insecure_skip_verify`）に変える。名前を `omada.lab.kanare.dev` に変えるか、`router` を残すかを決める。
- Homepage の Router タイルと `siteMonitor`、`docs/architecture/02-infrastructure.md` の機器表、`README.md`、`docs/architecture/01-overview.md` の構成図（ASCII と SVG）。
- Prometheus の `blackbox_icmp`（`192.168.11.1` は ER605 の IP になるだけで、そのまま動く）。

### 段階 1 の確認

- [ ] インターネット、DNS（`*.lab.kanare.dev`）、Caddy 経由の各サービス
- [ ] Prometheus の全ターゲットが `up`、`GatewayUnreachable` が出ていない
- [ ] Healthchecks.io の heartbeat が途切れていない
- [ ] 外出先から Tailscale 経由で入れる
- [ ] テレビ（無線）の AirPlay・Cast（同じネットワークなので、今までどおり動く）

### 段階 1 の戻し方

Buffalo をルーターモードに戻し、壁の LAN ポート → Buffalo の WAN、Buffalo の LAN → Proxmox・ディスプレイに戻す。ER605 は電源を抜くだけでよい（コントローラーで「忘れる」のは後でよい）。Buffalo の設定は段階 0 のバックアップから戻す。

## 段階 2: SG2210P を追加

VLAN は使わない。止まるのは、Proxmox と Buffalo のケーブルを付け替える間の数十秒。

### 段階 2 の作業

1. 先に SG2210P を ER605 の LAN に繋ぎ、コントローラーで採用する（Proxmox はまだ ER605 に繋いだまま）。ファームウェアを更新する。
2. ポートの割り当てを設定する（VLAN なしなので、全ポートが既定の VLAN）。

   | ポート | 接続先 | 備考 |
   | --- | --- | --- |
   | p1 | ER605 LAN | アップリンク |
   | p2 | Proxmox | 段階 3 で trunk にする |
   | p3 | Buffalo（AP） | 段階 3 で access VLAN30 にする |
   | p4–p6 | 空き | 段階 3 のリハーサル用 |
   | p7–p8 | 空き | 段階 4 の AP 用に PoE を残す |
   | p9–p10 | SFP（使わない） | |

3. Proxmox のケーブルを ER605 から SG2210P の p2 に、Buffalo のケーブルを ER605 から SG2210P の p3 に付け替える。
4. 付け替えのあと、Proxmox のリンクが戻ることと、`INC-2026-10-25` の NIC 送信停止（e1000e）が再発していないことを確認する。物理コンソール（キーボードとモニター）を繋げられるようにしておく。

### 段階 2 の確認

- [ ] Proxmox、全 VM、`vm-omada` に Mac から届く。インターネットに出られる。
- [ ] Wi-Fi の端末とメインディスプレイが繋がる。
- [ ] Prometheus の全ターゲットが `up`。
- [ ] コントローラーの管理画面で、ER605 と SG2210P が接続済みに見える。

### 段階 2 の戻し方

ケーブルを ER605 に繋ぎ直す（段階 1 の状態）。

## 段階 3: VLAN と `10.77.x.x` への一斉切り替え

切り替え方式は [ADR-0004](../../adr/0004-vlan-cutover-all-at-once.md)（全ホストを一斉に）のまま。**ホストのアドレス付け替えは 1 回だけ。** その前に、アドレスを変えない準備とリハーサルを済ませて、当日の作業を減らす。

### 3-A. 準備（アドレスを変えない）

- [ ] **リハーサル**: 検証端末を SG2210P の p5（VLAN30 の access）と p6（VLAN50 の access）に繋ぎ、本番の VLAN と同じ設定で次を確かめる。ホストは動かさない。
  - Gateway ACL（LAN → LAN）で、Trusted → IoT は通り、IoT → Trusted は拒否される。ルールの評価が上から順で、戻りの通信が通る。
  - 末尾の全拒否が効く。
  - DHCP が VLAN ごとに配る（DNS は `10.77.20.11`）。
- [ ] **コントローラーの IP 変更への追従**: `vm-omada` が `192.168.11.12` から `10.77.10.3` に変わったとき、ER605 と SG2210P が付いてくるか。付いてこない場合の手順（コントローラーの接続先の再設定、または機器のリセットと再採用）を、リハーサルで確かめて書く。
- [ ] **Proxmox の準備**: `vmbr0` を VLAN-aware にする（`bridge-vlan-aware yes`）。IP は `192.168.11.10` のまま。SG2210P p2 は VLAN なしのまま。1 つの検証用 VM をタグ付きで繋ぎ、動作を確かめる。
  - **Management の VM（`vm-omada`）は VLAN ID を指定せず、untagged で繋ぐ（案）。** p2 の native VLAN10 は untagged で出るため、タグ付き VLAN10 の VM にはフレームが届かない。ホスト（Proxmox）と同じ untagged の側に置く。リハーサルで確かめる。
  - `bridge-vlan-aware` への変更は、物理コンソールから行う。
- [ ] **コードの準備**: 別ブランチで Terraform・Ansible・Caddyfile・Prometheus・Homepage・ドキュメントを新アドレスに書き換える（一覧は[設計書](../../architecture/08-vlan-design.md#影響を受けるリポジトリ内の箇所)）。`vlan_id` を Terraform の VM モジュールに追加する。Management の VM は `vlan_id` を null にする。
- [ ] **Omada に本番設定を作る（有効にしない）**: VLAN 10/20/30/40/50/60/70、DHCP、ACL、mDNS、スイッチのポートプロファイル。
- [ ] **バックアップ**: Omada、Proxmox の `/etc/network/interfaces`、`terraform.tfstate`、Buffalo の設定を、Mac 以外にも保存する。
- [ ] **戻しの手順**（下記）を書き、時刻を決める。
- [ ] Tailscale の ACL・経路の承認の手順を確認する（`--advertise-routes=10.77.20.0/24,10.77.40.0/24`）。

### 3-B. 設定の対応表

**ER605（VLAN インターフェース）**

| VLAN | 名前 | ゲートウェイ | DHCP | 配る DNS |
| --- | --- | --- | --- | --- |
| 10 | Management | `10.77.10.1` | なし | — |
| 20 | Servers | `10.77.20.1` | なし | — |
| 30 | Trusted | `10.77.30.1` | `.100–.199` | `10.77.20.11` |
| 40 | Lab | `10.77.40.1` | `.100–.199` | `10.77.20.11` |
| 50 | IoT | `10.77.50.1` | `.100–.199` | `10.77.20.11` |
| 60 | Guests | `10.77.60.1` | `.100–.199`（リースは数時間） | `10.77.20.11` |
| 70 | DMZ | `10.77.70.1` | なし | — |

通信の許可は[通信ポリシー](../../architecture/08-vlan-design.md#通信ポリシー)の表のとおり。既定の LAN（VLAN1、`192.168.11.0/24`）は、切り替えが終わるまで旧ネットワークとして残す（切り替え中の戻り先と、機器への到達に使う）。切り替えて動作を確認したら、DHCP を止めて使わない。Omada で既定の LAN を消せるかは要確認。

**SG2210P（ポートプロファイル）**

| ポート | 接続先 | 設定 |
| --- | --- | --- |
| p1 | ER605 | untagged VLAN1、tagged 10/20/30/40/50/60/70 |
| p2 | Proxmox | untagged（native）VLAN10、tagged 20/40/50/70 |
| p3 | Buffalo（AP） | access VLAN30（untagged） |
| p4 | 空き | 未使用（シャットダウン） |
| p5–p6 | リハーサル | 作業後に未使用にする |
| p7–p8 | 空き | 段階 4 で AP の trunk にする |

スイッチ自身の管理 VLAN は 10（`10.77.10.2`）。

**Proxmox**

| 項目 | 現在 | 切り替え後 |
| --- | --- | --- |
| `vmbr0` | VLAN-aware ではない | VLAN-aware |
| ホストの IP | `192.168.11.10/24`、GW `192.168.11.1` | `10.77.10.10/24`、GW `10.77.10.1` |
| VM の VLAN | なし | `vm-infra`・`vm-monitoring`・`vm-apps`・`vm-code` は 20、`vm-dev` は 40、`vm-omada` は untagged（Management） |

### 3-C. 当日の作業

1. 最終のバックアップを取る。`vm-dev`・`vm-windows` を止める。
2. Omada: 本番の設定を有効にする（VLAN、DHCP、ACL は最初は緩めの全許可）。SG2210P の p1・p3 を新しい設定にする。Buffalo は Trusted に入り、Wi-Fi の端末は `10.77.30.x` を受け取る。
3. Proxmox（物理コンソールで）: IP を `10.77.10.10` に変え、ネットワークを再起動する。同時に p2 を native VLAN10 にする。
4. `vm-omada` を `10.77.10.3` にする。ER605・SG2210P が追従することを確かめる（3-A の手順）。
5. `terraform apply` で VM の IP と VLAN を変える。**`vm-infra` を最初にする**（DNS を先に戻す）。
6. `ansible-playbook` で DNS レコード、UFW、Tailscale の経路、Caddy、Prometheus を反映する。Tailscale の新しい経路は Admin Console で承認し、旧経路を外す。
7. 疎通を確認する（次の一覧）。
8. ACL を許可表の内容に絞る。ログを見ながら 1 つずつ絞る。
9. 旧ネットワーク（VLAN1）の DHCP を止める。リハーサル用のポートを未使用にする。

### 3-D. 確認

- [ ] 各 VLAN の DHCP と名前解決（`*.lab.kanare.dev`）
- [ ] 各 VLAN から Servers への接続（許可表のとおり）と、拒否すべき通信が拒否されること
- [ ] Caddy 経由の各サービス、Omada・Proxmox の管理画面
- [ ] Prometheus の全ターゲット、アラート（`GatewayUnreachable` は新しい IP に直す）
- [ ] 外出先から Tailscale 経由で `vm-code`・`vm-dev` に入れる
- [ ] メインディスプレイ、MacBook、Wi-Fi の端末（Trusted）
- [ ] テレビ（無線、Trusted）の AirPlay・Cast
- [ ] Healthchecks.io の heartbeat

### 3-E. 戻し方

戻す判断の時刻を、作業の前に決めておく。時刻までに疎通が取れなければ戻す。

1. SG2210P のポートを段階 2 の設定（VLAN なし）に戻す。ER605 の VLAN は無効にし、既定の LAN（`192.168.11.0/24`）を有効に戻す。
2. Proxmox を物理コンソールから `192.168.11.10`（元の `/etc/network/interfaces`）に戻す。
3. `terraform.tfstate` を戻して `terraform apply`（旧アドレスのコードが入ったブランチで）。
4. コントローラーが使えない場合は、ER605 をリセットして GUI から `192.168.11.1` を設定する。さらに戻す場合は段階 1 の戻し方（Buffalo をルーターモードに戻す）。

## 未確認・要判断の事項

| 項目 | 内容 |
| --- | --- |
| ケーブル A の長さ | 壁から ER605 の置き場所まで届くか。Buffalo（テレビの裏）より ER605 のほうが壁から遠い場合は、足りない可能性がある |
| テレビが無線 | 設計書は有線を前提にしている。段階 3 で mDNS の中継（有線のテレビ → IoT ポート）を試す計画は成り立たない。テレビは段階 4 の IoT の SSID に移してから確かめる。それまで Trusted で今までどおり動く。有線にするケーブルは運用者がそのうち買う |
| 仕事用 Windows PC | メインディスプレイの LAN 1 本を、MacBook と仕事用 PC が共有する。**VLAN はポート単位なので、同じディスプレイに繋がる 2 台は、同じ VLAN になる**（分けるにはポートを分ける必要がある）。当面は Trusted のままにする（案）。分けたい場合の選択肢: (1) 仕事用 PC に USB の有線 LAN アダプターを付け、別のポートから別の VLAN に繋ぐ、(2) スイッチの MAC ベースの VLAN（SG2210P が対応するか、ドック経由で MAC が安定するかは未確認）、(3) 仕事用 PC を Wi-Fi の Guests に置く（ディスプレイは使えなくなる）。会社のルールで自宅 LAN との分離が求められるかを確認してから決める |
| Management の VM の繋ぎ方 | native VLAN10 の untagged で繋ぐ案（3-A）。実機で確かめる |
| コントローラーの IP 変更 | ER605・SG2210P が追従するか。リハーサルで確かめる |
| 既定の LAN（VLAN1）の扱い | 消せるか。消せなければ、使わない状態で残す |
| ディスプレイの接続先 | Buffalo の LAN に付けたまま（案、付け替え不要）。Wi-Fi の通信取得の位置に影響する場合は、[ネットワーク通信の収集・可視化](06-network-traffic-analysis.md)で扱う |
| Proxmox の NIC | `INC-2026-10-25` の e1000e の送信停止。ポートを付け替えるたびに、再発していないことを確認する |

## 採用までの流れ

1. この計画を確認し、ポートの割り当てと作業の順序を決める（運用者）。
2. 採用したら、設計書の「導入の段階」「切り替え手順」に移し、必要な判断は ADR に残す。この文書は設計書へのリンクに置き換える。
3. 段階 0 から順に進める。段階が終わるたびに、設計書・構成図・README を更新する。
