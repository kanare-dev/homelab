# 未着手の項目

[ロードマップ](README.md)のうち、領域ごとの未着手の項目。大型計画は別の文書にある。

## ネットワーク・DNS

- 方針: 自分専用アクセスは Tailscale のみで完結させる（[ADR 0005](../../adr/0005-tailscale-only-remote-access.md)）。Cloudflare Tunnel による外部公開は、Tailscale を入れていない他人と共有する具体的なニーズが出たサービスに限る。それまで Cloudflare Tunnel と Split-Horizon DNS には着手しない
- Omada 導入・VLAN 化・OPNsense 導入は大型計画として扱う（下の「大型計画」）

## インフラ・IaC・運用

- [ ] メモリの配分を見直す（`vm-windows` は停止前提なので、常時起動する VM だけで見積もる）
- [ ] `vm-dev` を Ansible、Docker、ネットワーク設定の破壊検証用として運用する（[vm-code](../../services/vm-code.md) と分離済み）
- [ ] homepage のデプロイを効率化する（`make setup-apps` は `common` / `docker` / `node_exporter` ロールも毎回流れる）
  - `playbooks/apps.yml` の homepage 関連タスクに `tags: [homepage]` を付け、`--tags homepage` で設定だけ反映できるようにする
  - Makefile に `deploy-homepage` ターゲットを追加する
  - 末尾の無条件 `restarted` を、設定ファイル変更時のみ動く handler（`notify`）にする。homepage は設定を自動で再読み込みするため、再起動自体が不要な可能性もある
- [ ] k3s などのクラスタ構成を検討する（学習用クラスタとして分離運用し、Grafana / PVE / AdGuard Home 等の安定稼働中サービスは当面 Docker Compose のまま維持する）。より重いワークロードや複数アプリの分離運用もここで扱う

## ハードウェア・拡張

- [ ] ThinkCentre Tiny をラックに搭載する
- [ ] NAS の導入（TrueNAS）。導入後は、PBS / restic による自動バックアップ（[ADR 0001](../../adr/0001-no-vm-backup.md)）と、Home Assistant の `.storage/` と履歴の保護（[ADR 0011](../../adr/0011-home-assistant-on-vm-apps.md) の再検討の条件）も見直す
- [ ] UPS 導入と自動シャットダウン

## ホームオートメーション

- [ ] Home Assistant の機器の検出と VLAN を決める（[VLAN 化](04-network-omada-vlan.md)と合わせて。Servers から Clients・IoT への mDNS の中継か、置き場所の変更。Cast や Matter を使う前に）
- [ ] MQTT (Mosquitto) + ESP32 連携

  ```plaintext
  ESP32 → MQTT → HomeAssistant → Prometheus → Grafana
  ```

- [ ] IP カメラ + Frigate の導入
- [ ] メディアサーバーの導入（Jellyfin / Plex / Emby）
- [ ] テレビの統合

## 大型計画

- [ ] [Omada 導入・VLAN 化・OPNsense 導入](04-network-omada-vlan.md)
- [ ] [GPU 搭載ゲーミング PC 兼ホームサーバー](05-gpu-pc.md)
