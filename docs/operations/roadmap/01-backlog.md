# 未着手の項目

[ロードマップ](README.md)のうち、領域ごとの未着手の項目。大型計画は別の文書にある。

## ネットワーク・DNS

- 方針: 自分専用アクセスは Tailscale のみで完結させる（[ADR 0005](../../adr/0005-tailscale-only-remote-access.md)）。Cloudflare Tunnel による外部公開は、Tailscale を入れていない他人と共有する具体的なニーズが出たサービスに限る。それまで Cloudflare Tunnel と Split-Horizon DNS には着手しない
- [ ] **検討中**: Omada Cloud（クラウドアクセス）を使い続けるか、無効にするか。2026-11-03 から、便利そうなので当面は有効にして試している。最終的に無効にするかもしれない。判断の材料は、使い勝手と、リスク（Tailscale と Caddy を通らず、TP-Link ID の認証だけで、コントローラーの管理画面に外から入れる経路が増える。[VLAN 設計](../../architecture/08-vlan-design.md#管理画面への外部到達リスクを受け入れる)）。決めたら ADR に残し、無効にするときは、[外部サービスの表](../../architecture/03-network.md#外部サービスへの依存)・[構成図](../../diagrams/pre-migration-diagram/layout-architecture.py)・[システム概要](../../architecture/01-overview.md)の Omada Cloud と、「外から入る経路は Tailscale だけ」の例外の記述（`03-network.md`、`05-security.md`、`01-overview.md`）を消す
- [x] Wi-Fi の SSID の名前を `Onda` と `Onda-Forte` に変える（**2026-11-03 に実施**。移行の前に、運用者が変えた。[VLAN 設計](../../architecture/08-vlan-design.md)に記録）。SwitchBot Hub 2 は繋ぎ直し済み（`Onda` に接続）。WPA3 の名前は `Onda-Forte` で設定済み。残り: テレビと仕事用 PC は、運用者が気づいたときに繋ぎ直す（段階 1 の確認の前に、繋ぎ直しておく）。Buffalo 本体のバックアップの取り直しは、運用者が行う。理由は、名前が長くて打ち込みにくいこと、飽きたこと、もう少し homelab らしい名前にしたいこと。**あわせて、バンドステアリング Lite（2.4GHz と 5GHz で共通の SSID にする Buffalo の機能）を使いたい**。調べた範囲では、Lite は信号の強さだけで帯域を切り替え、ルーター全体の設定で、端末ごとには指定できず、既定は無効。使うには共通の SSID を設定する。**共通 SSID の名前を自由に決められるかは未確認**（第三者の記事では `Buffalo-XXXX` と `Buffalo-XXXX-WPA3` という名前になる。このリポジトリの設定の記録にも、共通 SSID は MAC アドレス由来の既定名とある）。AP モードで使えるか、WPA2 と WPA3 の組み合わせがどうなるかも未確認。Buffalo の画面で、バンドステアリング Lite の項目に、名前の入力欄があるかを見る。今の `Ceci n'est pas un Wi-Fi [2.4]` / `[5]` / `[2.4+]` / `[5+]` の 4 つは、WPA2 の 2 つも残す（[VLAN 設計](../../architecture/08-vlan-design.md)）。時期は、**移行（段階 1〜3）が落ち着いてから**。移行の最中に変えると、不具合の原因が、ネットワークの変更なのか、SSID の変更なのか、切り分けられなくなる。変えると、全端末が繋ぎ直しになる。SwitchBot Hub は、Wi-Fi の設定をアプリでやり直す必要がある可能性が高い（未確認）。段階 4 で Omada の AP を入れるときは、VLAN ごとの SSID（Trusted / IoT / Guest）を作り直すので、**そこで使う名前を今のうちに決めて、Buffalo に先に付けておけば、端末は 1 回の繋ぎ直しで済む**（AP を替えても、SSID とパスワードが同じなら、端末は設定を変えずに繋がる）。名前の案は、Trusted は今の名前の系統、IoT と Guest は空白や記号のない ASCII（IoT は 2.4GHz のみ）。
- Omada 導入・VLAN 化と OPNsense 導入は、それぞれ大型計画として扱う（下の「大型計画」）

## インフラ・IaC・運用

- [ ] **検討中**: `docs/services/` の文書を、種類ごとにフォルダ分けする（2026-11-03、運用者の希望）。例: インフラ（DNS、リバースプロキシ、監視、Omada、ER605、SG2210P、Buffalo）とアプリ（Homepage、Home Assistant、n8n、FreshRSS）と開発環境（vm-code、CI/CD、MOTD）。分け方と名前はまだ決めていない。移すときは、文書へのリンク（`docs/`、`README.md`、`CLAUDE.md`、設計書、ADR、ロードマップ、`make md-links` の対象）と、`docs/services/README.md` の番号・一覧を、同じ変更で直す。ファイル名の番号（01〜14）を残すか、フォルダごとに振り直すかも決める。リンクの数が多いので、一度にまとめて行い、`make md-links` で漏れを確認する。
- [ ] 学習用に Traefik を `vm-apps` 上で試す。既存の入口（`vm-infra` の Caddy、[ADR 0019](../../adr/0019-caddy-reverse-proxy.md)）は置き換えず、`vm-apps` のコンテナ向けの別の入口として並べる。Docker ラベルによる自動検出、ダッシュボード、ミドルウェアを触るのが目的。Caddy を置き換えるかは、試したあとに新しい ADR で判断する
- [ ] VM の OS を Ubuntu 26.04 LTS に移行する（[ADR 0021](../../adr/0021-ubuntu-lts-for-vms.md)）。新しい cloud image で `ubuntu-cloud`（VMID 9000）を作り直し、まず `vm-dev` で Ansible が通るか確認してから、VM を 1 台ずつ作り直す。その場更新はしない。24.04 のサポートは 2029 年 4 月までなので急がない
- [ ] PVE ホストを 9.1 → 9.2 に更新する。保留 248 パッケージ（セキュリティ修正 61 件）が溜まっている。QEMU 10 → 11 とカーネル更新で、全 VM の停止を伴う再起動が要る。見送りの理由と再検討の条件は[障害記録 §4.3](../incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md)。バックアップ（`vzdump`）を先に入れる順番が望ましい
- [x] thin pool の過剰割当を解消した（`LvmThinPoolOverprovisioned`。**2026-11-05 に実施**）。`vm-omada`（20G）を足した 2026-11-03 に、割当の合計が 243.5G、pool（155.6G）に対する比率が 1.57 になり、しきい値 1.5 を超えていた。(1) `vm-dev` のディスクを 30G → 10G にした（Terraform は縮小できないので、`terraform apply -replace='module.vm["vm-dev"].proxmox_vm_qemu.vm'` で作り直し、`ansible-playbook playbooks/site.yml --limit vm-dev` で再構成した。残すデータは無かった）。(2) `vm-windows`（60G、VMID 130）を削除した。vzdump を 1 回取ったが、復元しない方針にして 2026-11-06 に消した（必要になったら ISO から作り直す。手順は[バックアップの手順](../runbooks/06-backup-restore.md#vm-windows-の削除と作り直し2026-11-05)）。結果は、割当の合計 163.5G、比率は約 1.05、pool の使用率は 54.5% → 33.7%。メモリも、`vm-windows` を起動すると 24GB を超える状態が解消した。しきい値は、1.6 が INC-2026-10-22 の障害時の値なので、上げていない。作り直すと 60G の割当が戻り、比率は約 1.5 になるので、`vm-dev` を縮めるなど、割当を空けてから作る
- [ ] **検討中**: ER605・SG2210P の設定（VLAN、DHCP、ACL、ポートの割り当て）をコード化できるか（2026-11-03、運用者の疑問）。調べた範囲では、(1) Omada コントローラーに **Open API**（REST。OAuth のクライアント認証。設定は Global view > Settings > Platform Integration > Open API）がある。(2) **公式の Terraform プロバイダーはない**（TP-Link の担当者は、その方法をサポートしないと回答している）。(3) コミュニティ製の [Tohaker/terraform-provider-omada](https://github.com/Tohaker/terraform-provider-omada) がある（コントローラー v5.x・v6.x 対応とされる。VLAN・ACL・ポートの設定を扱えるかは**未確認**）。移行（段階 1〜3）のあとに、コントローラーの Open API の文書（コントローラーの画面から開ける）で、VLAN・ACL・DHCP・スイッチのポートのエンドポイントがあるかを見て、プロバイダーの対応範囲と照らす。コード化できない部分は、設計書の許可表と設定値の表を正にして、バックアップを併用する（Buffalo と同じ運用）。コード化するなら、クライアントの鍵は SOPS に入れる。
- [ ] **検討中**: Omada コントローラーのバックアップの保存先を、iCloud Drive から S3 などに広げるか。今は手で取って、iCloud Drive に暗号化せずに置く（決定 2026-11-03。運用者は、今の段階では厳密さを求めない）。設定の唯一の記録がコントローラーの中にあり（[VLAN 設計](../../architecture/08-vlan-design.md)）、Mac だけだと、Mac と `vm-omada` が同時に失われたときに戻せない。S3 にするなら、バックアップファイルを暗号化してから置く（設定と認証情報が入るため）。バックアップ全般の方針（[ADR 0001](../../adr/0001-no-vm-backup.md)、NAS・PBS・restic の検討）と合わせて決める
- [ ] `vm-omada` の Omada コントローラーの画面（HTTPS）の外形監視を、blackbox に加える。`vm-omada` の OS の死活は、2026-11-03 に Prometheus の scrape に入れて、`TargetDown` で見ている（`up` が 1 になることを確認済み）。残りは、Caddy と DNS に `omada.lab.kanare.dev` を足したあとに、`prometheus.yml` の `blackbox_http` に足すこと（段階 1 の「同じ変更で直すもの」と一緒にやる）。足したら、[監視・アラート](../../services/03-monitoring.md)の注記を消す
- [ ] k3s などのクラスタ構成を検討する（学習用クラスタとして分離運用し、Grafana / PVE / AdGuard Home 等の安定稼働中サービスは当面 Docker Compose のまま維持する）。より重いワークロードや複数アプリの分離運用もここで扱う

## ハードウェア・拡張

- [ ] NAS の導入（TrueNAS）。導入後は、PBS / restic による自動バックアップ（[ADR 0001](../../adr/0001-no-vm-backup.md)）と、Home Assistant の `.storage/` と履歴の保護（[ADR 0011](../../adr/0011-home-assistant-on-vm-apps.md) の再検討の条件）も見直す
- [ ] UPS 導入と自動シャットダウン

## ホームオートメーション

- [ ] Home Assistant の機器の検出と VLAN を決める（[VLAN 化](04-network-omada-vlan.md)と合わせて。Servers から Trusted・IoT への mDNS の中継か、置き場所の変更。Cast や Matter を使う前に）
- [ ] MQTT (Mosquitto) + ESP32 連携

  ```plaintext
  ESP32 → MQTT → HomeAssistant → Prometheus → Grafana
  ```

- [ ] IP カメラ + Frigate の導入
- [ ] メディアサーバーの導入（Jellyfin / Plex / Emby）
- [ ] テレビの統合

## 大型計画

- [ ] [Omada 導入・VLAN 化](04-network-omada-vlan.md)
- [ ] [GPU 搭載ゲーミング PC 兼ホームサーバー](05-gpu-pc.md)
- [ ] [ネットワーク通信の収集・可視化](06-network-traffic-analysis.md)（ntopng などでパケットレベルの通信を可視化）
- [ ] [DMZ と外部公開](07-dmz.md)（DMZ の VLAN にハニーポットや公開用 Web サーバーを置く）
- [ ] [OPNsense 導入](08-network-opnsense.md)（Omada・VLAN 化のあと。補助的に検証し、ER605 の後継にする）
- [ ] [ラックの導入と 3D プリントのマウント](09-rack.md)（10 インチラックに ThinkCentre Tiny・ER605・SG2210P を載せる。マウントは業者に印刷を頼む）
