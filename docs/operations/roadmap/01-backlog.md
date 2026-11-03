# 未着手の項目

[ロードマップ](README.md)のうち、領域ごとの未着手の項目。大型計画は別の文書にある。

## ネットワーク・DNS

- 方針: 自分専用アクセスは Tailscale のみで完結させる（[ADR 0005](../../adr/0005-tailscale-only-remote-access.md)）。Cloudflare Tunnel による外部公開は、Tailscale を入れていない他人と共有する具体的なニーズが出たサービスに限る。それまで Cloudflare Tunnel と Split-Horizon DNS には着手しない
- Omada 導入・VLAN 化と OPNsense 導入は、それぞれ大型計画として扱う（下の「大型計画」）

## インフラ・IaC・運用

- [ ] 学習用に Traefik を `vm-apps` 上で試す。既存の入口（`vm-infra` の Caddy、[ADR 0019](../../adr/0019-caddy-reverse-proxy.md)）は置き換えず、`vm-apps` のコンテナ向けの別の入口として並べる。Docker ラベルによる自動検出、ダッシュボード、ミドルウェアを触るのが目的。Caddy を置き換えるかは、試したあとに新しい ADR で判断する
- [ ] VM の OS を Ubuntu 26.04 LTS に移行する（[ADR 0021](../../adr/0021-ubuntu-lts-for-vms.md)）。新しい cloud image で `ubuntu-cloud`（VMID 9000）を作り直し、まず `vm-dev` で Ansible が通るか確認してから、VM を 1 台ずつ作り直す。その場更新はしない。24.04 のサポートは 2029 年 4 月までなので急がない
- [ ] PVE ホストを 9.1 → 9.2 に更新する。保留 248 パッケージ（セキュリティ修正 61 件）が溜まっている。QEMU 10 → 11 とカーネル更新で、全 VM の停止を伴う再起動が要る。見送りの理由と再検討の条件は[障害記録 §4.3](../incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md)。バックアップ（`vzdump`）を先に入れる順番が望ましい
- [ ] thin pool の過剰割当を解消する（`LvmThinPoolOverprovisioned`）。`vm-omada`（20G）を足した 2026-11-03 に、割当の合計が 243.5G、pool（155.6G）に対する比率が 1.57 になり、しきい値 1.5 を超えた（使用率は 53%）。次の 2 つで、比率を 1.18 程度に下げる。(1) `vm-dev` のディスクを 30G → 10G に小さくする（Terraform は縮小できないので、停止中の `vm-dev` を作り直す。残したいデータの有無を先に確認する）。(2) `vm-windows`（60G）を削除する（Windows 11 は最低 64GB 要るので小さくできない）。ISO から作り直すのは手間なので、**検討中**: セットアップ済みの状態を vzdump でバックアップして（保存先は pool の外。空き容量は未確認）から削除し、必要になったら復元する。テンプレートにしても、割当サイズは減らないので、比率は下がらない。将来 Proxmox のメモリを増やしたら、また使うかもしれない。VG の空きは 2G しかなく、pool は拡張できない。しきい値を上げることは、1.6 が INC-2026-10-22 の障害時の値なので、しない。解消したら、[インフラ構成](../../architecture/02-infrastructure.md)の「約 1.4 倍」の記載と[監視](../../services/03-monitoring.md)の現在値を直す
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
