# Omada 導入・VLAN 化

[ロードマップ](README.md)の大型計画である。ER605、SG2210P、EAP（AP）を使って Omada のネットワークを作り、VLAN で分離する。OPNsense は、別の大型計画（[OPNsense 導入](08-network-opnsense.md)）に分け、この計画が完了したあと、機器が買いやすくなってから進める。設計は完了しているが、機器はまだ購入しておらず、着手もしていない。

詳しい内容は、設計書と ADR に書いている。この文書には、進める順序とチェック項目だけを書く。

機器を購入したあとの具体的な作業（AS-IS と TO-BE の構成図、ポートの割り当て、配線の付け替え、戻し方）は、[ER605・SG2210P の移行計画](10-er605-sg2210p-migration-plan.md)（検討中）にある。

| 内容 | 参照先 |
| --- | --- |
| VLAN・アドレスの設計、段階ごとの手順、戻し方、費用 | [VLAN 設計](../../architecture/08-vlan-design.md) |
| アドレス体系を `10.x` にする判断 | [ADR 0003](../../adr/0003-vlan-address-scheme.md) |
| 全ホストを一斉に切り替える判断 | [ADR 0004](../../adr/0004-vlan-cutover-all-at-once.md) |
| ルーターは ER605 を先に、OPNsense は後にする判断（OPNsense は[別計画](08-network-opnsense.md)） | [ADR 0009](../../adr/0009-router-er605-first.md) |

## 目的

ルーター、スイッチ、AP を、Omada でまとめて管理する。管理、サーバー、クライアント、IoT、ゲストのネットワークを VLAN で分け、セグメント間の通信を制限する。

## 基本方針

- 機器は、買う順に 4 つの段階に分ける。段階 1〜2 の間は、IP を変えない。
- VLAN への切り替えは、全ホストを一斉に行う（段階 3）。
- 家の入口のルーターは、当面 ER605 で運用する。OPNsense への置き換えは、[別の計画](08-network-opnsense.md)で扱う。
- 各段階に着手する前に、戻し方を決めておく。戻し先は、直前の段階の状態である。

## 導入の段階

### 段階 1: ルーターの交換と Omada コントローラー

- [ ] ER605 **V2** を購入する（型番と、コントローラーのバージョンとの対応を購入前に確認する）
- [ ] Omada コントローラーを Proxmox 上の VM として立てる
- [ ] ER605 の LAN アドレスを `192.168.11.1/24` に変更してから、コントローラーで採用する
- [ ] ルーターを Buffalo から ER605 に交換し、Buffalo を AP モードにする（IP は変えない）
- [ ] 設計書・構成図を更新する

### 段階 2: Managed Switch

- [ ] SG2210P を購入する（購入前に版数を確認する。Omada コントローラーに対応しない版がある。PoE の電力予算は 61W 前後で版により異なる。将来の AP の台数を確認する）
- [ ] スイッチをコントローラーで採用し、Proxmox などをつなぐ（VLAN は使わない）
- [ ] 設計書・構成図を更新する

### 段階 3: VLAN と `10.x` への一斉切り替え

- [ ] コントローラーモードの ACL で、LAN → LAN を制限できるか実機で確認する（公式 FAQ では可能。段階 3 の前。詳細は VLAN 設計の未決事項）
- [ ] mDNS の中継（Trusted ↔ IoT）が動くか確認する。動かなければ、段階 4 まで有線のテレビを Trusted に置く
- [ ] TO-BE の構成図を描く
- [ ] 物理設置（ThinkCentre・ルーター・スイッチの置き場所、通気、電源、ケーブル）を決める
- [ ] 戻し手順を書く（戻し先は段階 2 の状態。Omada のバックアップと `terraform state` を事前に保存する）
- [ ] VLAN10 Management / VLAN20 Servers / VLAN30 Trusted / VLAN40 Lab / VLAN50 IoT / VLAN60 Guests へ全ホストを一斉に切り替える（VLAN70 DMZ は VLAN とルールだけ作る。詳細は [DMZ と外部公開](07-dmz.md)）
- [ ] 設計書・構成図・Terraform・Ansible・DNS の IP を更新する

### 段階 4: AP（EAP）

- [ ] AP の機種を選ぶ（Wi-Fi 6 世代の日本での入手性・価格・技適を、段階 3 の後に確認する）
- [ ] AP を設置し、SSID と VLAN を対応させる（設置場所は電波の届き方で決める）
  - SSID は 3 つで始める（検討中）: Trusted（VLAN30）/ IoT（VLAN50、2.4GHz のみ、クライアント間分離）/ Guest（VLAN60、クライアント間分離、LAN 向けは全遮断）
  - Lab（VLAN40）の SSID は、無線で繋ぐ検証機が出てから追加する。SSID を増やすとビーコンの電波オーバーヘッドが増えるため、最小構成で始める
  - Management（VLAN10）と Servers（VLAN20）は有線のみ。SSID は出さない
- [ ] Buffalo を退役または予備にする

## 関連する検討

- Home Assistant が機器を検出する方法と、VLAN との関係を決める必要がある。Servers から Trusted と IoT へ mDNS を中継するか、Home Assistant の置き場所を変えるかのどちらかになる。Cast や Matter を使う前に決める。
- GPU 搭載 PC の VLAN とファイアウォールルールは、[GPU 搭載ゲーミング PC](05-gpu-pc.md) の Phase 5 で扱う。
- 通信の収集と可視化は、[ネットワーク通信の収集・可視化](06-network-traffic-analysis.md)で扱う。Buffalo を AP モードにして、Wi-Fi の通信をスイッチに通す構成（段階 1〜2）が、通信を取得する位置の第一候補である。そのため、ER605 の導入を先に進める。
- DMZ の VLAN は、[DMZ と外部公開](07-dmz.md)で扱う。VLAN 設計に DMZ を足すかどうかは、段階 3 の前に決める。
- Cloudflare Tunnel と Split-Horizon DNS は、共有したいというニーズが出るまで着手しない（ロードマップの方針）。
