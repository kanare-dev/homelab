# 段階 1・2 の当日の作業（ER605・SG2210P の導入）

Buffalo を ER605 に交換し、Buffalo を AP（ブリッジ）モードにし、SG2210P を追加する日の手順。**IP アドレスは変えない。VLAN も使わない。** 全体の目安は 1〜2 時間。

- 当日の順にチェックしながら進めるための文書。手順の根拠と、決めた経緯は[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)の「段階 1・2」にある。手順を変えたら、計画も同じ変更で直す。
- 到達点の構成は、[物理構成図](../../diagrams/physical-diagram/physical-diagram.png)（配線）と、計画の「段階 2 の後」。この作業のあとの VLAN 化（段階 3）は、この文書の対象外。
- 秘密の値（管理者のパスワードなど）と、機器の MAC アドレスは、この文書に書かない（台帳へ。[シークレット](03-secrets.md)）。

## 0. 前提の確認（開始の前に）

事前準備は、2026-11-03 に済んでいる。当日の朝に、**抜けていないかだけ**を確かめる。

- [ ] `vm-omada` が動いていて、コントローラーの画面に入れる（`ssh -L 8043:localhost:8043 vm-omada` のあと `https://localhost:8043`）
- [ ] コントローラーの LAN の設定が、ER605 の LAN（`192.168.11.1/24`）に合っている（[Omada コントローラー](../../services/network/omada-controller.md)）
- [ ] ER605 が、スタンドアロンで設定済み（LAN `192.168.11.1/24`、DHCP `.60`〜`.99`・リース 48 時間・DNS `192.168.11.11` だけ。[ER605 の設定](../../hardware/er605/settings.md)）
- [ ] Buffalo の設定のバックアップ（`wsr-1800ax4p-bk-YYYYMMDD.bin`）と、コントローラーのバックアップがある（iCloud Drive）。EasyMesh は無効にしてある
- [ ] 短いケーブルが 2 本ある（ER605 p2 ↔ SG2210P p1 は接続済み、SG2210P p2 ↔ Proxmox は SG2210P 側だけ挿してある）。長いケーブル A・B・C は、今の配線のまま
- [ ] 手元に、物理コンソール（キーボードとモニター。Proxmox に繋ぐ）と、Mac（有線で繋げる口）がある

## 1. 開始

- [ ] **「ここまでに終わらなければ戻す」という時刻を決める**（開始から 1〜2 時間後）。決めた時刻: ______
- [ ] 作業中に出るアラートを、想定しておく。Proxmox のリンクが切れる間は、`vm-monitoring` も止まるので、`GatewayUnreachable`（2 分以上）や `TargetDown` が出うる。作業が長引くと、Healthchecks.io の Heartbeat からも通知が届く（想定内）。

## 2. Buffalo を AP モードにする

**Buffalo の WAN のケーブルを抜いた状態で行う**（ルーターのまま、ER605 の `192.168.11.1` と重ならないようにする。ケーブル A は、まだどこにも挿さない）。

1. 背面の MANUAL/AUTO スイッチを **MANUAL** にする（電源 ON のまま）。
2. 背面の ROUTER/AP/WB スイッチを **AP** にする（電源 ON のまま）。前面の ROUTER ランプが消灯することを確認する。
3. マニュアルの手順どおり、Buffalo に接続している機器を再起動する。

IP の固定は、ここではしない（画面に入れるのは、手順 6 のあと）。

## 3. ER605 だけを確認する

SG2210P、Proxmox、Buffalo を繋ぐ**前**に、ER605 単体で動くことを見る（切り分けのため）。

1. 壁の LAN ポート → ER605 の p1（WAN。**ケーブル A**）。
2. Mac を、ER605 の p3 に有線で直接繋ぐ（今 Mac が繋がっているケーブルを、一時的に挿し替える）。
3. ER605 を起動する（まだコントローラーに採用していないので、本体の画面のまま、ルーター・DHCP・NAT として動く）。
4. 次を確かめる。
   - [ ] ER605 の WAN が、上流（`172.22.0.0/21`）から IP を取れている（画面は `http://192.168.11.1`）
   - [ ] Mac が DHCP を取り直せて（Wi-Fi は切っておく）、インターネットに届く
   - [ ] Mac に配られた DNS が `192.168.11.11` **だけ**（`scutil --dns`）
   - [ ] ER605 の画面の Network > Interface で、**p2 が LAN として動いている**
5. **WAN が IP を取れないとき**: 建物の共用ルーターが、最初に繋いだ機器の MAC を覚えている可能性がある。ER605 の WAN の MAC アドレスの設定に、Buffalo の WAN の MAC（Buffalo の画面か、本体のラベル）を入れて、取り直す。

## 4. 本配線にする

Mac を p3 から外し、次の順で付け替える。ケーブルの両端にラベルを貼る（`ER605-LAN1` など）。

1. **Proxmox**: SG2210P の p2 に挿してある短いケーブルの、Proxmox 側の端を、Proxmox に挿す。
2. **Buffalo**: ケーブル B の Proxmox 側の端を外し、SG2210P の p3 に挿す（Buffalo 側の端は、そのまま）。Buffalo の接続先のポートは、取扱説明書に指定がなく、公式 FAQ では AP モードで INTERNET も LAN として動く（[Buffalo の資料](../../hardware/wsr-1800ax4p/spec.md)）。計画と物理構成図では INTERNET ポートにしている。
3. **メインディスプレイ**（Dell U2725QE）: ケーブル C の Buffalo 側の端を外し、SG2210P の p4 に挿す。

| 区間 | ケーブル |
| --- | --- |
| 壁 → ER605 p1（WAN） | A（長尺） |
| ER605 p2 → SG2210P p1 | 短い（接続済み） |
| SG2210P p2 → Proxmox | 短い |
| SG2210P p3 → Buffalo | B（長尺） |
| SG2210P p4 → ディスプレイ | C（長尺） |

## 5. 配線の確認（ER605 の画面のまま、SG2210P も未採用）

- [ ] **Proxmox のリンクが戻った**。物理コンソールで、`nic0` が up で、e1000e の送信停止（`INC-2026-10-25`）が再発していない（`dmesg` に `Hardware Unit Hang` が出ていない）
- [ ] Mac から、Proxmox（`192.168.11.10`）、全 VM、`vm-omada`（`192.168.11.12`）に届く。インターネットに出られる
- [ ] Wi-Fi の端末が、`Onda` で繋がる
- [ ] 外出先（Tailscale）から入れる（スマホを Wi-Fi から外して確認する）

**不具合が出たとき**: SG2210P を疑う。Proxmox と Buffalo を SG2210P から外し、ER605 の p3、p4 に直接挿す。直れば SG2210P が原因（結果を記録する）。直らなければ、[戻し方](#戻し方)。

## 6. Buffalo の IP を固定する

ER605 の貸出一覧で、Buffalo の IP を調べて、ブラウザで開く。AP モードの既定の IP は、公式には書かれていない（「エアステーション設定ツール」の手順も、Mac 用は公式に見つかっていない）。

- [ ] 「詳細設定」→「LAN」→「LAN」で、IP を **`192.168.11.2`** の固定にする。取扱説明書には、AP モードでは、デフォルトゲートウェイと DNS サーバーアドレスに、ルーターの IP と同じ値を設定するとある。ルーターは ER605（`192.168.11.1`）。
- [ ] Wi-Fi の設定（SSID、バンドステアリング Lite）が残っている

## 7. ER605 を採用する

`vm-omada` のコントローラーに、ER605 を採用する（同じ `192.168.11.0/24` にいるので、自動で見つかる）。**採用すると、ER605 の画面は使えなくなる。**

1. コントローラーの Devices で、ER605 を採用する。**SG2210P も候補に出るが、まだ採用しない。**
2. **採用の直後に確認する**:
   - [ ] LAN が `192.168.11.1/24` のまま
   - [ ] DHCP の設定（プール `.60`〜`.99`、リース 48 時間、DNS `192.168.11.11`）が変わっていない
3. LAN が `192.168.0.1/24` に変わって届かなくなったときは、**無理に直さず**、[戻し方](#戻し方)に戻す。
4. ファームウェア、時刻（NTP）、管理者アカウントを設定する。

## 8. SG2210P を採用する

1. コントローラーで、SG2210P を採用する。ファームウェアを更新する。
2. ポートの割り当てを設定する（VLAN なしなので、全ポートが既定の VLAN）。

   | ポート | 接続先 | 備考 |
   | --- | --- | --- |
   | p1 | ER605 p2 | アップリンク |
   | p2 | Proxmox | 段階 3 で trunk にする |
   | p3 | Buffalo（AP） | 段階 3 で access VLAN30 にする |
   | p4 | メインディスプレイ（Dell U2725QE） | 段階 3 で access VLAN30 にする |
   | p5–p6 | 空き | 段階 3 のリハーサル用 |
   | p7–p8 | 空き | 段階 4 の AP 用に PoE を残す |
   | p9–p10 | SFP（使わない） | |

3. 採用のあとも、手順 5 の確認が通ること（Proxmox のリンクが戻ったまま、など）を見る。

## 9. 完了の確認

- [ ] インターネット、DNS（`*.lab.kanare.dev`）、Caddy 経由の各サービス
- [ ] 新しく DHCP を取った端末の DNS が `192.168.11.11` だけ
- [ ] Proxmox、全 VM、`vm-omada` に Mac から届く。Proxmox のリンクが戻り、e1000e の送信停止が再発していない
- [ ] 採用のあとも、ER605 の LAN が `192.168.11.1/24`、DHCP のプールとリースが変わっていない
- [ ] コントローラーの管理画面で、ER605 と SG2210P が接続済みに見える
- [ ] Prometheus の全ターゲットが `up`、`GatewayUnreachable` が出ていない
- [ ] Healthchecks.io の heartbeat が途切れていない
- [ ] 外出先から Tailscale 経由で入れる
- [ ] Wi-Fi の端末（`Onda`）とメインディスプレイが繋がる。テレビ（無線）の AirPlay・Cast が、今までどおり動く

## 10. 作業の後始末

1. **コントローラーのバックアップを取る**。画面の Settings > Maintenance の「Backup & Restore」で保存して、iCloud Drive の `homelab/` に置く（`omada-bk-YYYYMMDD.cfg`）。
2. **同じ変更で直す**（[DNS 構成の「ルーターを付け替えるとき」](../../services/network/dns.md#ルーターを付け替えるとき)）:
   - `docker/compose/reverse-proxy/Caddyfile`: `router.lab.kanare.dev` の転送先を、Omada コントローラーの管理画面（HTTPS、`tls_insecure_skip_verify`）に変える。名前を `omada.lab.kanare.dev` に変えるか、`router` を残すかを決める。`ansible-playbook playbooks/infra.yml` で反映する。
   - Homepage の Router タイルと `siteMonitor`（`docker/compose/homepage/config/services.yaml`）。
   - `docs/architecture/02-infrastructure.md` の機器表、`README.md`、`docs/architecture/01-overview.md` の構成図（ASCII と SVG）。
   - [IP アドレス一覧](../../architecture/09-ip-addresses.md): `192.168.11.2` を Buffalo（AP モード、固定）として確認する。
3. **機器の設定文書の「未確認」を埋める**: [ER605](../../hardware/er605/settings.md)（p2 が LAN として動くか、上流が MAC で絞っていたか、採用後の値）、[SG2210P](../../hardware/sg2210p/settings.md)（標準の設定でスイッチとして動いたか）、[Buffalo](../../hardware/wsr-1800ax4p/settings.md)（AP モードでの IP と入り方、SSID が残ったか）。変更履歴に 1 行ずつ足す。
4. 切り分けの結果（SG2210P を疑ったかなど）と、実際の所要時間を、[移行計画](../roadmap/10-er605-sg2210p-migration-plan.md)に記録する。

## 戻し方

決めた時刻までに終わらないとき、または確認が通らないとき。

- **SG2210P だけを外す**: Proxmox と Buffalo を、ER605 の p3、p4 に直接挿す。メインディスプレイ（C）は Buffalo の LAN に戻す。
- **全部戻す**: Buffalo をルーターモードに戻し（スイッチを ROUTER に）、壁の LAN ポート → Buffalo の WAN（A）、Buffalo の LAN → Proxmox（B）・ディスプレイ（C）に戻す。ER605 と SG2210P は電源を抜くだけでよい（コントローラーで「忘れる」のは後でよい）。Buffalo の設定は、段階 0 のバックアップから戻す（SSID は、バンドステアリング Lite のあとの値になっている）。

戻したあとに、Proxmox のリンクと、全 VM、インターネット、Tailscale を確認する。
