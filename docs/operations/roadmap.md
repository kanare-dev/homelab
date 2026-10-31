# roadmap

README に書く現行構成は `24GB` に増設済みのホストを前提とし、このファイルではその先の拡張計画を整理する。着手済みの項目は、詳細を設計書・ADR に移して一行にまとめる。

| 文書 | 内容 |
| --- | --- |
| このファイル | 領域ごとの未着手の項目と、完了済みの一覧 |
| [Omada 導入・VLAN 化・OPNsense 導入](roadmap/network-omada-vlan.md) | 大型計画。ER605・SG2008P・AP、VLAN、OPNsense の段階とチェック項目 |
| [GPU 搭載ゲーミング PC](roadmap/gpu-pc.md) | 大型計画。目的、構成、Phase 1〜6 |
| [見送り中の項目](roadmap/deferred.md) | 見送った理由と、再検討する条件 |

---

## 未着手

### ネットワーク・DNS

- 方針: 自分専用アクセスは Tailscale のみで完結させる（[ADR 0005](../adr/0005-tailscale-only-remote-access.md)）。Cloudflare Tunnel による外部公開は、Tailscale を入れていない他人と共有する具体的なニーズが出たサービスに限る。それまで Cloudflare Tunnel と Split-Horizon DNS には着手しない
- Omada 導入・VLAN 化・OPNsense 導入は大型計画として扱う（下の「大型計画」）

### インフラ・IaC・運用

- [ ] メモリの配分を見直す（`vm-windows` は停止前提なので、常時起動する VM だけで見積もる）
- [ ] `vm-dev` を Ansible、Docker、ネットワーク設定の破壊検証用として運用する（[vm-code](../services/vm-code.md) と分離済み）
- [ ] homepage のデプロイを効率化する（`make setup-apps` は `common` / `docker` / `node_exporter` ロールも毎回流れる）
  - `playbooks/apps.yml` の homepage 関連タスクに `tags: [homepage]` を付け、`--tags homepage` で設定だけ反映できるようにする
  - Makefile に `deploy-homepage` ターゲットを追加する
  - 末尾の無条件 `restarted` を、設定ファイル変更時のみ動く handler（`notify`）にする。homepage は設定を自動で再読み込みするため、再起動自体が不要な可能性もある
- [ ] k3s などのクラスタ構成を検討する（学習用クラスタとして分離運用し、Grafana / PVE / AdGuard Home 等の安定稼働中サービスは当面 Docker Compose のまま維持する）。より重いワークロードや複数アプリの分離運用もここで扱う

### ハードウェア・拡張

- [ ] ThinkCentre Tiny をラックに搭載する
- [ ] NAS の導入（TrueNAS）。導入後は、PBS / restic による自動バックアップ（[ADR 0001](../adr/0001-no-vm-backup.md)）と、Home Assistant の `.storage/` と履歴の保護（[ADR 0011](../adr/0011-home-assistant-on-vm-apps.md) の再検討の条件）も見直す
- [ ] UPS 導入と自動シャットダウン

### ホームオートメーション

- [ ] Home Assistant の機器の検出と VLAN を決める（[VLAN 化](roadmap/network-omada-vlan.md)と合わせて。Servers から Clients・IoT への mDNS の中継か、置き場所の変更。Cast や Matter を使う前に）
- [ ] MQTT (Mosquitto) + ESP32 連携

  ```plaintext
  ESP32 → MQTT → HomeAssistant → Prometheus → Grafana
  ```

- [ ] IP カメラ + Frigate の導入
- [ ] メディアサーバーの導入（Jellyfin / Plex / Emby）
- [ ] テレビの統合

### 大型計画

- [ ] [Omada 導入・VLAN 化・OPNsense 導入](roadmap/network-omada-vlan.md)
- [ ] [GPU 搭載ゲーミング PC 兼ホームサーバー](roadmap/gpu-pc.md)

---

## 完了済み

### インフラ基盤

- [x] ハードウェア調達、Proxmox VE インストール（`192.168.11.10`）、メモリ増設（8GB → 24GB）
- [x] ネットワーク設計と IP 規約の確定（`README.md`）、DNS ドメイン `lab.kanare.dev` の決定
- [x] Cloud-init テンプレート VM、SSH 鍵ペア、Proxmox API トークン（`terraform/proxmox/README.md`）
- [x] 秘密情報管理方針（SOPS + age。[secrets Runbook](runbooks/secrets.md)）
- [x] バックアップ方針（VM 全体は取らない。VM 外の再現不能データだけ台帳で守る。[ADR 0001](../adr/0001-no-vm-backup.md)）
- [x] CI（lint のみ。`plan` / `apply` は自動化しない。[ADR 0006](../adr/0006-ci-lint-only.md)、[CI/CD](../services/cicd.md)）
- [x] AS-IS の構成図（[概要](../architecture/01-overview.md) の ASCII 図と `docs/diagrams/`）

### サービス

- [x] `vm-infra` / `vm-monitoring` / `vm-dev` の構成を Terraform + Ansible で完全再現できるようにした
- [x] DNS: CoreDNS（`lab.kanare.dev` の権威 DNS）+ AdGuard Home + Unbound（[DNS](../services/dns.md)）
- [x] Caddy（Docker Compose、Cloudflare DNS-01 で Let's Encrypt 証明書）と `pve.lab.kanare.dev`（[リバースプロキシと TLS](../services/reverse-proxy-tls.md)）
- [x] Tailscale を `vm-infra` にサブネットルーターとして導入（二重 NAT のため WireGuard の代わり。[ADR 0005](../adr/0005-tailscale-only-remote-access.md)）
- [x] Authelia は導入しない（[ADR 0008](../adr/0008-no-authelia.md)）。認証のない画面が必要になったら `basic_auth` を検討する
- [x] `vm-apps` を常時起動し、Homepage を `home.lab.kanare.dev` で稼働（[Homepage](../services/homepage.md)）
- [x] 常用リモート開発環境を `vm-dev` から分離し、`vm-code` として切り出した（[vm-code](../services/vm-code.md)）
- [x] Home Assistant を `vm-apps` に導入し、SwitchBot Cloud と Spotify をつなぐ（[ADR 0011](../adr/0011-home-assistant-on-vm-apps.md)、[Home Assistant](../services/home-assistant.md)）
- [x] n8n を `vm-apps` に導入し、週次レポート `weekly-report` を `#homelab-reports` に送る（[ADR 0012](../adr/0012-n8n-on-vm-apps.md)、[n8n](../services/n8n.md)）。アラートの通知は Alertmanager の直送のままにする（通知の経路が他の VM の障害に左右されないため。[ADR 0007](../adr/0007-vm-host-dns-is-router.md)、[ADR 0010](../adr/0010-external-heartbeat.md)）

### 監視・可観測性

- [x] Prometheus + Grafana、`node_exporter`、ダッシュボード（Node Exporter Full, Prometheus Overview）、`grafana.lab.kanare.dev` / `prometheus.lab.kanare.dev`
- [x] blackbox_exporter による外形監視と、Unbound の応答失敗を検知するアラート
- [x] Alertmanager から個人 Slack への通知
- [x] 外部 Heartbeat（Healthchecks.io）でホスト・NIC・監視 VM の停止を外から検知（[ADR 0010](../adr/0010-external-heartbeat.md)、[INC-2026-10-25](incidents/2026-10-25-nic-hardware-unit-hang.md)）

詳細は [監視・アラート](../services/monitoring.md)。
