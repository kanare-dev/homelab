# roadmap

README に書く現行構成は `24GB` に増設済みのホストを前提とし、このファイルではその先の拡張計画を整理する。

---

## 完了済み

### インフラ基盤

- [x] ハードウェア調達
- [x] Proxmox VE インストール（`192.168.11.10`）
- [x] ネットワーク設計確定（IP 規約は `README.md` 参照）
- [x] SSH 鍵ペア生成
- [x] Cloud-init テンプレート VM を作成（`terraform/proxmox/README.md` 参照）
- [x] Proxmox API トークン発行
- [x] 初期構成は `vm-infra` + `vm-monitoring` + `vm-dev` に絞る
- [x] 秘密情報管理方針を決定（SOPS + age を採用）
- [x] DNS ドメイン（`lab.kanare.dev`）を決定

### サービス構築

- [x] `vm-infra` と `vm-monitoring` の構成を Terraform + Ansible で完全再現できるようにする
- [x] CoreDNS で `lab.kanare.dev` 内部ゾーンを運用する
- [x] Caddy を Docker Compose 化し、Cloudflare DNS-01 チャレンジで Let's Encrypt 証明書を取得する
- [x] `pve.lab.kanare.dev` を Caddy 経由で解決できるようにする
- [x] `vm-monitoring`: Prometheus + Grafana デプロイ
- [x] 常時起動する VM に `node_exporter` デプロイ
- [x] Grafana ダッシュボード設定（Node Exporter Full, Prometheus Overview）
- [x] Reverse Proxy 経由のアクセス確認（`grafana.lab.kanare.dev`, `prometheus.lab.kanare.dev`）
- [x] Tailscale を vm-infra にサブネットルーターとして導入し、外出先からホームラボにアクセスできるようにする（二重NAT環境のためWireGuardの代替）

---

## ネットワーク・DNS

- [ ] 方針: 自分専用アクセスは Tailscale のみで完結させ、Cloudflare Tunnel による外部（公開）公開は「Tailscale を入れていない他人と共有する」具体的なニーズが出たサービスのみに限定する
- [ ] Cloudflare Tunnel の導入・Split-Horizon DNS 構成は保留（上記の方針により、共有ニーズが出るまで着手しない）
- [x] Authelia によるログインの一元化は導入しない（[ADR 0008](../adr/0008-no-authelia.md)）。認証のない画面が必要になったら `basic_auth` を検討する
- [x] Tailscale は SSH 等の管理アクセス・日常のリモートアクセス双方の主経路として継続利用する
- [x] DNS を AdGuard Home + Unbound に移行する（CoreDNS は権威 DNS として継続）
  - AdGuard Home: 広告ブロック・クエリログ・WebUI（port 53 / 3000）
  - Unbound: フルリゾルバ（1.1.1.1 等に依存せずルートから再帰解決・プライバシー向上、port 5335）
  - CoreDNS: `lab.kanare.dev` 権威 DNS として継続（port 5353、127.0.0.1 バインドに変更）
  - vm-infra 上の Docker Compose に AdGuard + Unbound を追加
- [x] VLAN とアドレス体系の設計（[VLAN 設計](../architecture/08-vlan-design.md)、[ADR 0003](../adr/0003-vlan-address-scheme.md)、[ADR 0004](../adr/0004-vlan-cutover-all-at-once.md)）。設計のみで、未適用
- [ ] 導入の段階 1: ルーターを Buffalo から ER605 に交換し、Omada コントローラーを立てる（IP は変えない）
- [ ] 導入の段階 2: Managed Switch を追加する（VLAN は使わない）
- [ ] 導入の段階 3: VLAN と `10.x` への一斉切り替え（VLAN10 Management / VLAN20 Servers / VLAN30 Clients / VLAN40 IoT / VLAN50 Guests）
- [ ] 導入の段階 4: Omada の AP を導入し、Buffalo を退役または予備にする
- [ ] OPNSense の導入（N100 で学習用に。VLAN の段階 3 のあとに、止まっても影響が小さい役割から。[ADR 0009](../adr/0009-router-er605-first.md)）

## 監視・可観測性

- [x] blackbox_exporter で外形監視を追加する（Caddy 経由の HTTPS・証明書の期限・AdGuard の名前解決。[monitoring.md](../services/monitoring.md#外形監視blackbox)）
- [x] Unbound の応答失敗を検知するアラートを追加する（AdGuard の fallback DNS で隠れる障害を、未キャッシュの名前を Unbound に直接引くプローブで検知する。[monitoring.md](../services/monitoring.md)）
- [x] Alertmanager を追加して個人Slackで監視通知を受け取れるようにする（[monitoring.md](../services/monitoring.md)）
- [x] 外部 Heartbeat（Healthchecks.io）で、ホスト・NIC・監視 VM の停止を外から検知する（[ADR 0010](../adr/0010-external-heartbeat.md)、[INC-2026-10-25](incidents/2026-10-25-nic-hardware-unit-hang.md)）
- [ ] uptime-kuma の導入（見送り中。2026-10-27 時点では導入しない）
  - 現状: HTTPS と DNS の外形監視は blackbox-exporter + Alertmanager で行い、停止の検知は外部 Heartbeat（Healthchecks.io）が担う（[monitoring.md](../services/monitoring.md)）
  - 見送る理由: 死活監視と通知が blackbox-exporter と重なり、二重管理になる。Alertmanager の `inhibit_rules`（VM 停止・DNS 障害時の抑制）が使えず、障害のたびに通知が増える。vm-apps に置くと監視対象と同じホストで止まり、ホスト停止は検知できない
  - 導入を検討する条件（どれか 1 つでも該当したら着手を判断する）:
    - 家族など Grafana を見ない人向けに、ステータスページが必要になった
    - 外形監視のターゲット追加（`prometheus.yml` の編集とデプロイ）が負担になった
    - 回線断・停電を家の外から検知したくなり、外部の VPS を用意できた（[monitoring.md](../services/monitoring.md) の案 C）
- [ ] Loki + Grafana Alloy でログ収集基盤を構築する（見送り中。2026-10-26 時点では導入しない）
  - 現状: ログは各ホストの journald（200M・1 か月）と Docker のログ上限（10MB × 3）に分散している。横断検索の手段はなく、調べるときは VM ごとに `ssh` して `journalctl` / `docker logs` を使う
  - 見送る理由: INC-2026-10-25 の原因は PVE の journald（永続化済み）で追えた。ホストの NIC が止まると転送もできず、集約していても効果はなかった。ストレージの過剰割当（約 1.44 倍）が残っており、増え続けるログを足すリスクがある。収集エージェントを全ホストに入れる運用の手間も増える
  - 導入を検討する条件（どれか 1 つでも該当したら着手を判断する）:
    - 複数 VM をまたぐ原因調査に、手間を感じる場面が増えた
    - ストレージ障害でログごと消え、原因が追えなかった
    - アラートの前後のログを Grafana でメトリクスと並べて見たくなった
    - thin pool の過剰割当を解消した（容量に余裕ができた）
  - 導入するときの方針（案）: `vm-monitoring` に Loki、全ホストに Grafana Alloy（Promtail は後継の Alloy に移行済み）。保持期間 14 日、容量の上限 3GB 程度から始める。ADR を追加し、`monitoring.md` の「容量の上限設定」の表も更新する
- [ ] telegraf + InfluxDB の導入

## インフラ・IaC・運用

- [x] AS-IS の構成図を描く（[概要](../architecture/01-overview.md) の ASCII 図と `docs/diagrams/`）
- [ ] TO-BE の構成図を描く（VLAN 適用後。段階 3 の前に用意する）
- [ ] メモリの配分を見直しする（`vm-windows` は停止前提なので、常時起動する VM だけで見積もる）
- [ ] homepage のデプロイを効率化する（`make setup-apps` は `common` / `docker` / `node_exporter` ロールも毎回流れる）
  - `playbooks/apps.yml` の homepage 関連タスクに `tags: [homepage]` を付け、`--tags homepage` で設定だけ反映できるようにする
  - Makefile に `deploy-homepage` ターゲットを追加する
  - 末尾の無条件 `restarted` を、設定ファイル変更時のみ動く handler（`notify`）にする。homepage は設定を自動で再読み込みするため、再起動自体が不要な可能性もある
- [ ] `vm-dev` を Ansible、Docker、ネットワーク設定の破壊検証用として運用する
- [x] 常用リモート開発環境を `vm-dev` から分離し、新VM `vm-code`（`192.168.11.22`, vmid 122, vm-dev 同等スペック）として切り出す
  - 背景: `vm-dev` は「破壊検証用」と「Claude Code + モバイル remote control による外出先からの常用開発」を兼ねてしまっており、破壊検証中に常用環境を壊すリスクがあるため分離する
  - Terraform（`terraform.tfvars`）で VM 定義、Ansible ロール `code_tools` で git / mosh / gh / Node.js / Claude Code CLI / CloudCLI（`@cloudcli-ai/cloudcli`, siteboon/claudecodeui）/ code-server / moshi-hook を再現可能にプロビジョニング
  - code-server（ブラウザ版 VS Code、`code.lab.kanare.dev`）と CloudCLI（Claude Code のモバイル/Web UI、`cloudcli.lab.kanare.dev`）を同居させ、CLI・ブラウザ・モバイルの3経路をカバー
  - iOS の Moshi アプリからは専用鍵（`code_extra_authorized_keys`）と直接 DNS レコード（`vm-code.lab.kanare.dev`）でSSH/mosh接続し、`moshi-hook` を systemd --user サービスとして常駐させて連携する（ペアリングのみ手動）
  - アクセス経路は Tailscale のみに限定（UFW で該当ポートを LAN/Tailscale サブネットルート経由の `192.168.11.0/24` からのみ許可、Cloudflare Tunnel 等での外部公開はしない）
  - `make setup-code` で単独プロビジョニング可能
- [x] バックアップ方針を決める（VM 全体は取らない。VM 外の再現不能データだけ台帳で守る。[ADR 0001](../adr/0001-no-vm-backup.md)）。PBS / restic による自動化は、別ディスクや NAS を用意するまで見送り
- [x] CI を整える（lint のみ。`plan` / `apply` は自動化しない。[ADR 0006](../adr/0006-ci-lint-only.md)、[CI/CD](../services/cicd.md)）
- [ ] VM テンプレートの Packer 化

## 可視化・管理 UI

- [ ] Portainer で Docker の状態を可視化する
- [ ] Traefik の導入

## ハードウェア・拡張

- [x] メモリ増設（8GB → 24GB: 8GB + 16GB 追加）
- [ ] ThinkCentre Tiny をラックに搭載する
- [ ] NAS の導入（TrueNAS）
- [ ] UPS 導入と自動シャットダウン

## メモリ増設後

- [x] `vm-apps` を常時起動し、各種アプリを載せる（Homepage を `home.lab.kanare.dev` で稼働中）
- [ ] k3s などのクラスタ構成を検討する（学習用クラスタとして分離運用し、Grafana/PVE/AdGuardHome 等の安定稼働中サービスは当面 Docker Compose のまま維持する方針）
- [ ] より重いワークロードや複数アプリを分離運用する

## ホームオートメーション

- [x] Home Assistant を `vm-apps` に導入し、SwitchBot Cloud と Spotify をつなぐ（[ADR-0011](../adr/0011-home-assistant-on-vm-apps.md)、[Home Assistant](../services/home-assistant.md)）
- [ ] Home Assistant の機器の検出と VLAN を決める（Servers から Clients・IoT への mDNS の中継か、置き場所の変更。Cast や Matter を使う前に）
- [ ] Home Assistant の `.storage/` と履歴を守る（別ストレージの導入後。ADR-0011 の再検討の条件）
- [x] n8n を `vm-apps` に導入する（[ADR-0012](../adr/0012-n8n-on-vm-apps.md)、[n8n](../services/n8n.md)）
- [x] n8n の週次レポート（`weekly-report`）を `#homelab-reports` に送る（毎週月曜 9:00。[n8n](../services/n8n.md#ワークフロー)）
  - アラートの通知は Alertmanager の直送のままにする。n8n を経由させると、通知の経路が他の VM の障害に左右されるため（[ADR-0007](../adr/0007-vm-host-dns-is-router.md)、[ADR-0010](../adr/0010-external-heartbeat.md) の考え方）
- [ ] MQTT (Mosquitto) + ESP32 連携

  ```plaintext
  ESP32 → MQTT → HomeAssistant → Prometheus → Grafana
  ```

- [ ] IPカメラ + Frigate の導入
- [ ] メディアサーバの導入（Jellyfin / Plex / Emby）
- [ ] テレビの統合
