# VLAN 設計

TP-Link（ルーター + Managed Switch + AP、Omada 管理）への移行と同時に、ネットワークを VLAN で分割する設計書。**設計段階で、まだ何も適用していない。** 現在の構成は [README.md](../README.md) を参照。

## 目的

- IoT・ゲスト・クライアント・サーバー・管理機器を分け、侵害されたときの影響範囲を狭める。
- 管理画面（ルーター、スイッチ、AP、Proxmox、Omada コントローラー）を、管理用ネットワークだけに閉じる。
- `192.168.11.x` という Buffalo ルーターの初期値に引きずられたアドレス体系を、VLAN ID と一致する体系に直す。

## 前提と制約

- Proxmox ホスト（Lenovo ThinkCentre M70q Tiny）の物理 NIC は 1 つ。複数の VLAN に VM を置くため、スイッチのポートを trunk にし、Proxmox のブリッジを VLAN-aware にする。
- DNS（AdGuard Home）、Caddy、Tailscale は `vm-infra` 1 台に載っている。ここが止まると全 VLAN の名前解決が止まる（INC-2026-10-22）。移行後もこの構造は変わらないので、VLAN を増やすほど `vm-infra` への依存が目立つ。
- 設定の大半は Omada コントローラーの中に入り、Git では管理できない。バックアップが唯一の記録になる。

## VLAN 一覧

VLAN ID とサブネットの第 3 オクテットを揃える。各ホストの末尾オクテットは現在の値を引き継ぎ、移行時に覚え直す量を減らす。

| VLAN | 名前 | サブネット | ゲートウェイ | DHCP プール | 置くもの |
|---|---|---|---|---|---|
| 10 | Management | `192.168.10.0/24` | `.1` | なし（固定のみ） | ルーター、Managed Switch、AP、Omada コントローラー、Proxmox ホスト |
| 20 | Servers | `192.168.20.0/24` | `.1` | なし（固定のみ） | `vm-infra`、`vm-monitoring`、`vm-apps`、`vm-dev`、`vm-code` |
| 30 | Clients | `192.168.30.0/24` | `.1` | `.100–.199` | Mac、スマホ、iPad などの日常端末 |
| 40 | IoT | `192.168.40.0/24` | `.1` | `.100–.199` | ESP32 などの IoT デバイス |
| 50 | Guests | `192.168.50.0/24` | `.1` | `.100–.199` | 来客の端末 |

### 固定アドレス

| ホスト | 現在 | 移行後 | VLAN |
|---|---|---|---|
| ルーター | `192.168.11.1` | `192.168.10.1` | 10 |
| Managed Switch / AP / Omada コントローラー | — | `192.168.10.2–.9` 付近（採番は機器購入後に確定） | 10 |
| Proxmox | `192.168.11.10` | `192.168.10.10` | 10 |
| `vm-infra` | `192.168.11.11` | `192.168.20.11` | 20 |
| `vm-monitoring` | `192.168.11.13` | `192.168.20.13` | 20 |
| `vm-apps` | `192.168.11.20` | `192.168.20.20` | 20 |
| `vm-dev` | `192.168.11.21` | `192.168.20.21` | 20 |
| `vm-code` | `192.168.11.22` | `192.168.20.22` | 20 |
| ESP32 | `192.168.11.100` | `192.168.40.100` | 40 |

各 VLAN のゲートウェイはルーターの VLAN インターフェース（`.1`）。ルーター自身の管理アドレスは Management の `192.168.10.1`。

## 配置の方針

- **Proxmox ホストは Management に置く。** 管理面（`:8006`）が VM と同じネットワークに載らない。
- **VM は VLAN タグ付きで割り当てる。** Proxmox のブリッジ（`vmbr0`）を VLAN-aware にし、VM ごとに VLAN ID を指定する。Terraform の VM モジュールに `vlan_id` を持たせる。
- **スイッチの Proxmox 向けポートは trunk。** Management を native（untagged）、Servers をタグ付きで通す。
- **Omada コントローラーは Management の VM（または LXC）に置く。** 管理機器と同じ面に置き、Clients・Servers から直接触れないようにする。

## 通信ポリシー

ファイアウォールの許可表。送信元から宛先への新規接続の可否を示す。戻りの通信（確立済み）は常に許可する。**表にない組み合わせは拒否**（デフォルト拒否）。

| 送信元 ＼ 宛先 | Management | Servers | Clients | IoT | Guests | インターネット |
|---|---|---|---|---|---|---|
| **Management** | 許可 | DNS(53)、NTP のみ | 拒否 | 拒否 | 拒否 | 許可（更新用） |
| **Servers** | 下記「Servers → Management」 | 許可 | 拒否 | 下記「Servers → IoT」 | 拒否 | 許可 |
| **Clients** | 管理ポートのみ（80/443/8006/22） | Web(80/443)、SSH(22)、mosh(UDP 60000–61000)、DNS(53) | 許可 | 許可 | 拒否 | 許可 |
| **IoT** | 拒否 | DNS(53) を `vm-infra` へのみ | 拒否 | 許可 | 拒否 | 許可 |
| **Guests** | 拒否 | DNS(53) を `vm-infra` へのみ | 拒否 | 拒否 | 許可（端末間は隔離） | 許可 |

### 個別の許可

- **Servers → Management**:
  - `vm-infra`（Caddy）→ ルーター `:80`、Proxmox `:8006`（`router.lab.kanare.dev`、`pve.lab.kanare.dev` の転送先）。
  - `vm-monitoring`（Prometheus）→ Proxmox などの `:9100`（node_exporter）。
- **Servers → IoT**: `vm-monitoring` → ESP32 `:80`（メトリクスの取得）。IoT からサーバーへの取得は許可しない。
- **全 VLAN → `vm-infra:53`**: どの VLAN も DNS は AdGuard に向ける。DHCP が配る DNS サーバーは `192.168.20.11`。
- **Guests・IoT の隔離**: 他の VLAN の RFC1918 アドレス（`192.168.0.0/16` など）への通信は、DNS を除きすべて拒否する。

## 外出先からのアクセス（Tailscale）

- `vm-infra` が subnet router として広告するのは **Servers（`192.168.20.0/24`）のみ**。Management は広告しない。ルーター・スイッチ・AP・Proxmox の管理面には外から届かない。
- split DNS（`lab.kanare.dev` → `vm-infra`）は現状のまま。
- **残る課題**: `router.lab.kanare.dev` と `pve.lab.kanare.dev` は Caddy（Servers にいる）が Management へ転送するため、外出先からも Caddy 経由で管理画面に届いてしまう。Caddy の該当ブロックで送信元を Clients に限る（`remote_ip`）などで塞げるが、Tailscale 経由のときに Caddy が見る送信元アドレスは検証していない。移行時に確認する（未決事項を参照）。

## 影響を受けるリポジトリ内の箇所

`192.168.11.` を含むファイルは現時点で 25 ほどある。移行時はこの一覧を使って洗い出す。

| 領域 | 場所 | 内容 |
|---|---|---|
| Terraform | `terraform/proxmox/`（`variables.tf`、`terraform.tfvars.example`、`modules/vm/variables.tf`） | VM の IP・ゲートウェイ・`vlan_id` |
| Ansible | `ansible/inventory/`（`hosts.yml`、`group_vars/*`、`host_vars/*`）、`playbooks/infra.yml` | ホストの IP、`gateway`、UFW の許可元（`from: 192.168.11.0/24`）、DNS レコード、Tailscale の `--advertise-routes` |
| リバースプロキシ | `docker/compose/reverse-proxy/Caddyfile` | 各サービスの転送先 |
| 監視 | `docker/compose/monitoring/prometheus/`（`prometheus.yml`、`alerts.yml`） | scrape 対象、アラート内の IP |
| Homepage | `docker/compose/homepage/` | ウィジェットの URL、`dns:` |
| 運用ツール | `tools/lab/lab.yaml` | ホスト一覧 |
| ドキュメント | `README.md`、`docs/dns.md`、`docs/monitoring.md`、`docs/runbook.md`、`docs/cicd.md`、`diagrams/drawio/architecture.drawio.svg` | IP の記載、構成図 |

`README.md` の「IP アドレス規約」は、この設計に合わせて書き換える。

## 移行手順（案）

作業のたびに、ロックアウトしたときの戻し方（旧ルーターに戻す手順）を用意してから進める。

1. **機器の準備**: TP-Link のルーター、スイッチ、AP を揃える。Omada コントローラーを動かす VM（または LXC）を決める。現行ネットワーク（`192.168.11.0/24`）上で先に立ち上げ、動作を確認する。
2. **コントローラーのバックアップ運用を決める**: 自動バックアップの保存先を Mac だけにしない。
3. **切り替え方式を決める**: 新ルーターを検証用に並行して立てて試すか、時間を決めて一斉に切り替えるかを決める（未決事項を参照）。
4. **Proxmox の準備**: `vmbr0` を VLAN-aware にする。スイッチ側のポートを trunk にする。Proxmox ホスト自身の IP を Management に移す。
5. **VM を 1 台ずつ移す**: 影響の小さい `vm-dev` から。`vm-infra`（DNS）は最後から 2 番目、Tailscale の経路変更を伴うので手順を分けて行う。
6. **DNS とゲートウェイを切り替える**: DHCP が配る DNS サーバーを `192.168.20.11` にする。AdGuard の upstream と CoreDNS のゾーン（`dns_records`）を新 IP に直す。
7. **Tailscale の経路を差し替える**: `--advertise-routes=192.168.20.0/24` に変え、Admin Console で新しい経路を承認し、旧経路を外す。
8. **ファイアウォールを段階的に締める**: 最初は全許可で疎通を確認し、ログを見ながら許可表の内容に絞る。
9. **監視を更新する**: Prometheus の scrape 対象、アラート、`docs/monitoring.md` を更新する。Omada コントローラーの死活監視を追加する。
10. **ドキュメントを更新する**: 上の「影響を受ける箇所」を直し、旧アドレスを残さない。

## 未決事項

- [ ] **アドレス体系**: `192.168.<VLAN>.0/24` で進める案。外出先で接続する別のネットワークと重なると、Tailscale の subnet route が競合しうる。`192.168.10.x` や `192.168.20.x` は一般的な範囲なので、`10.x` 系にする案もある。
- [ ] **切り替え方式**: 並行構築して検証するか、時間を決めて一斉に切り替えるか。家族がいる場合は停止時間の許容範囲も決める。
- [ ] **管理画面への外部到達**: 上記の Caddy 経由の到達をどう扱うか（`remote_ip` で制限、Tailscale の ACL、現状維持のどれか）。
- [ ] **mDNS / ブロードキャスト**: スマホから IoT 機器を見つける、AirPlay や Chromecast を使うなど、VLAN をまたいで mDNS が必要になる機器がないか。ある場合は Omada の mDNS 機能を検討する。
- [ ] **Wi-Fi の SSID**: VLAN ごとに SSID を分けるか、1 つの SSID で端末ごとに VLAN を割り当てるか。AP の機種と Omada の機能で決まる。
- [ ] **機種の選定**: ルーター、スイッチ、AP の機種。Omada の対応表とコントローラーのバージョンの互換性を購入前に公式ドキュメントで確認する。
- [ ] **Omada コントローラーの置き場所**: VM か LXC か Docker か。
- [ ] **OPNsense の扱い**: ロードマップにある。TP-Link ルーターでファイアウォールを賄うか、OPNsense を別に立てるか。

## シークレットの扱い

次の作業でシークレットが発生する。作ったら `CLAUDE.md` のルールに従い、iCloud Keychain への登録（ユーザー）と台帳 `private/secrets-inventory.md` への追記（Claude）を行う。

- Omada コントローラーの管理者アカウント
- 各機器（ルーター、スイッチ、AP）の管理者パスワード
- Wi-Fi のパスフレーズ（SSID ごと）
- Omada コントローラーのバックアップファイル（暗号化と保存先を決める）
- Tailscale の authkey（経路変更で再発行する場合）
