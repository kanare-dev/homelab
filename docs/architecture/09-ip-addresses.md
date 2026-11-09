# IP アドレス一覧

homelab の IP アドレスを、1 か所にまとめた一覧。アドレスの範囲、VLAN、ホスト、FQDN の宛先を、**現在**と**移行後**（ER605・SG2210P を入れて VLAN に分けたあと）の両方で示す。**IP アドレスの一覧は、この文書を正とする。**

- 設計の理由は、[VLAN 設計](08-vlan-design.md)と ADR（[0015](../adr/0015-vlan-address-scheme-10-77.md)、[0022](../adr/0022-vlan-set-and-ids.md)、[0024](../adr/0024-dhcp-dns-single-no-fallback.md)、[0025](../adr/0025-address-octets-by-role.md)、[0026](../adr/0026-vmid-from-vlan-and-octet.md)、[0027](../adr/0027-servers-octet-bands-and-emergency-dns.md)）にある。移行の手順は、[移行計画](../operations/roadmap/10-er605-sg2210p-migration-plan.md)。
- 実際に設定している値は、VM の IP が `terraform/proxmox/terraform.tfvars`、ホストが `ansible/inventory/`、Caddy の転送先が `docker/compose/reverse-proxy/Caddyfile`、DNS のレコードが CoreDNS のゾーンにある（[更新のしかた](#更新のしかた)）。
- 秘密の値と、機器の MAC アドレスは書かない。

| 体系 | 状態 | 範囲 |
| --- | --- | --- |
| 現在 | 稼働中 | `192.168.11.0/24`（1 つのネットワーク。VLAN なし） |
| 移行後 | 採用済み・未適用 | `10.77.0.0/16`（VLAN ごとに `10.77.<VLAN>.0/24`） |

アドレスの付け替えは、段階 3 で全ホストを一斉に切り替える（[ADR-0004](../adr/0004-vlan-cutover-all-at-once.md)）。段階 1・2（ER605・SG2210P の導入）では、IP を変えない。 **ただし、管理系（Proxmox ホスト、`vm-omada`、ER605・SG2210P）は、段階 3 では今のアドレス（`192.168.11.x`）のまま残し、`10.77.10.x` への移行は、段階 3b で行う**（[ADR-0028](../adr/0028-defer-management-vlan10.md)）。下の「移行後」の Management の値は、段階 3b のあとの値。

## 現在のアドレス

`192.168.11.0/24`。

| 範囲 | 用途 | 例 |
| --- | --- | --- |
| `192.168.11.1` | ルーター / ゲートウェイ | ER605（2026-11-06 に Buffalo から交換。同じ `.1`） |
| `192.168.11.10–19` | インフラ（Proxmox、基盤 VM） | `.10` Proxmox、`.11` `vm-infra`、`.12` `vm-omada`、`.13` `vm-monitoring` |
| `192.168.11.20–59` | サーバー / 検証用 VM | `.20` `vm-apps`、`.21` `vm-dev`、`.22` `vm-code` |
| `192.168.11.60–99` | DHCP プール | 動的割当 |
| `192.168.11.100–149` | IoT デバイス | `.100` ESP32 |
| `192.168.11.150–254` | 予約 / 実験用 | — |

- VM の IP は Terraform（`terraform.tfvars`）で固定する。現在の VMID は、IP の末尾オクテットに 100 を足した値。移行後は、`VLAN ID × 100 + 第 4 オクテット`（[ADR-0026](../adr/0026-vmid-from-vlan-and-octet.md)）。VMID の付け替えは、段階 3 では行わず、VM を作り直すときに行う（[ホスト別の IP](#ホスト別の-ip)に、現在と移行後の VMID を並べた）。
- 段階 1 以降、ER605 の DHCP が配る DNS サーバーは `192.168.11.11`（`vm-infra`。[ER605 の設定](../hardware/er605/settings.md)）。

## 移行後のアドレス

`10.77.<VLAN>.0/24`。VLAN ID とサブネットの第 3 オクテットを揃える（第 2 オクテットは `77` で固定）。第 4 オクテットは、現在の値を引き継がず、役割で決める（[ADR-0025](../adr/0025-address-octets-by-role.md)、[ADR-0027](../adr/0027-servers-octet-bands-and-emergency-dns.md)）。

### VLAN 一覧

VLAN の ID は、信頼度の高い順（内側から外側）に振る。外部に触れるもの（Guests、DMZ）を末尾に置く（[ADR-0022](../adr/0022-vlan-set-and-ids.md)）。

| VLAN | 名前 | サブネット | ゲートウェイ | DHCP プール | 置くもの |
| --- | --- | --- | --- | --- | --- |
| 10 | Management | `10.77.10.0/24` | `.1` | `.240–.250`（緊急用） | ルーター、Managed Switch、AP、Omada コントローラー、Proxmox ホスト |
| 20 | Servers | `10.77.20.0/24` | `.1` | なし（固定のみ） | 常時稼働のサーバー: `vm-infra`、`vm-monitoring`、`vm-apps`、`vm-code` |
| 30 | Trusted | `10.77.30.0/24` | `.1` | `.100–.199` | 母艦 PC、スマホ、タブレットなどの日常端末 |
| 40 | Lab | `10.77.40.0/24` | `.1` | `.100–.149` | 一時的な検証用 VM、開発環境（`vm-dev`） |
| 50 | IoT | `10.77.50.0/24` | `.1` | `.100–.149` | ESP32、テレビ（AirPlay / Google TV）などのデバイス |
| 60 | Guests | `10.77.60.0/24` | `.1` | `.100–.199` | 来客の端末 |
| 70 | DMZ | `10.77.70.0/24` | `.1` | なし（固定のみ） | ハニーポット、公開用の Web サーバー、`cloudflared`（[DMZ と外部公開](../operations/roadmap/07-dmz.md)）。VLAN とルールは段階 3 で作り、置くものは 07 の計画で追加する |

各 VLAN のゲートウェイは、ルーターの VLAN インターフェース（`.1`）。ルーター自身の管理アドレスは、Management の `10.77.10.1`。

### アドレス帯の区切り

全 VLAN で同じ区切りにする。

| 範囲 | 用途 |
| --- | --- |
| `.1` | ゲートウェイ（ルーターの VLAN インターフェース） |
| `.2–.9` | ネットワーク機器（Management のみ使う。他の VLAN では未使用） |
| `.10–.49` | 固定アドレス（VM、サーバーなど） |
| `.50–.99` | DHCP 予約（Mac、テレビ、ESP32 など。プールの外に置くので、予約とプールが衝突しない） |
| `.100–.149` / `.100–.199` | DHCP プール（範囲は VLAN ごと。上の表。DHCP を使う VLAN のみ） |
| `.200–.254` | 予備（将来の拡張）。Management の `.240–.250` は緊急用プール |

### Servers の固定アドレスの帯

Servers（`10.77.20.0/24`）の固定アドレス（`.10–.49`）は、役割の帯に分ける（[ADR-0027](../adr/0027-servers-octet-bands-and-emergency-dns.md)）。新しい VM は、役割の帯の空きに置く。帯は番号の整理のためで、ネットワークの隔離ではない（同じ VLAN の中の通信は、ER605 の ACL を通らない）。ほかの VLAN は、台数が少ないので連番にする。

| 範囲 | 役割 | 割り当て |
| --- | --- | --- |
| `.10–.19` | 基盤・運用 | `vm-infra` が `.10`、`vm-monitoring` が `.11` |
| `.20–.29` | アプリ | `vm-apps` が `.20` |
| `.30–.39` | 開発・作業用 | `vm-code` が `.30` |
| `.40–.49` | 未使用 | 将来の拡張 |

### DHCP

- DHCP が配る DNS サーバーは、`10.77.20.10`（`vm-infra`）。フォールバックは配らない（[ADR-0024](../adr/0024-dhcp-dns-single-no-fallback.md)）。**例外: Management の緊急用プールは、ルーター（`10.77.10.1`）を配る**（[ADR-0027](../adr/0027-servers-octet-bands-and-emergency-dns.md)）。`vm-infra` が止まっていても、外部の名前を引ける。`*.lab.kanare.dev` は引けないので、管理機器は IP で開く。
- リース時間は VLAN ごとに決める。Management の緊急用プールは 1 時間、Trusted は 24〜48 時間、Lab と IoT は 24 時間、Guests は 4 時間。Guests は短くして、来客の端末の情報を長く保持しない。
- Lab は、Terraform で固定 IP を振る VM（`vm-dev` など）と、手で立てる使い捨ての VM が混在する。前者は `.10–.49`、後者は DHCP の `.100–.149` に入れる。
- Trusted の常用機（Mac など）は、DHCP 予約（`.50–.99`）で固定する。
- Servers・DMZ は DHCP を配らない。DMZ に侵入した端末が自動でアドレスを得るのを避ける。
- Management は、平時は使わない緊急用プール（`.240–.250`）だけを置く。Mac を直結する緊急の作業と、工場出荷時の機器の採用のため。工場出荷時の機器が DHCP の無い VLAN でどう振る舞うかを実機で確認できたら、外す（[ロードマップ](../operations/roadmap/12-ip-address-and-dhcp-review.md)）。Management に出せるのは SG2210P の物理ポートだけで、使わないポートは Management にしない。

## ホスト別の IP

| ホスト | 現 VMID | 移行後の VMID | 現在 | 移行後 | VLAN | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| ルーター | — | — | `192.168.11.1`（ER605） | `10.77.10.1`（ER605） | 10 | 2026-11-06 に、Buffalo に替わって ER605 が `192.168.11.1` を持った |
| Managed Switch（SG2210P） | — | — | —（段階 2 から DHCP） | `10.77.10.2` | 10 | |
| Omada コントローラー（`vm-omada`） | 112 | 1003 | `192.168.11.12` | `10.77.10.3` | 10 | |
| AP | — | — | — | `10.77.10.4–.9` | 10 | 採番は購入後に確定する |
| Proxmox（`pve`） | — | — | `192.168.11.10` | `10.77.10.10` | 10 | 移行後は、タグ付きの `vmbr0.10` に付ける |
| `vm-infra` | 111 | 2010 | `192.168.11.11` | `10.77.20.10` | 20 | DNS、Caddy、Tailscale |
| `vm-monitoring` | 113 | 2011 | `192.168.11.13` | `10.77.20.11` | 20 | |
| `vm-apps` | 120 | 2020 | `192.168.11.20` | `10.77.20.20` | 20 | |
| `vm-code` | 122 | 2030 | `192.168.11.22` | `10.77.20.30` | 20 | |
| `vm-dev` | 121 | 4010 | `192.168.11.21` | `10.77.40.10` | 40 | 手動起動 |
| Buffalo（AP モード） | — | — | `192.168.11.2`（固定。2026-11-06 に、ルーターの `192.168.11.1` から変更） | `10.77.30.50`（段階 4 で退役するまで） | 30 | Trusted。`.2–.9` は Management だけなので、予約の帯 `.50–.99` を使う |
| ESP32 | — | — | `192.168.11.100` | `10.77.50.50` | 50 | 現在は停止中 |
| テレビ | — | — | DHCP | `10.77.50.x` | 50 | DHCP 予約（`.50–.99`）で固定。無線 |
| `ubuntu-cloud` | 9000 | 9000 | — | — | — | VM のテンプレート。IP なし |

Mac、スマホなどの日常端末は、DHCP で受け取る（移行後は Trusted。常用機は予約）。

## FQDN の宛先

内部 DNS は `lab.kanare.dev` ゾーン（CoreDNS が権威）。名前の付け方は [ネットワーク設計](03-network.md#ドメイン命名規約)。Caddy 経由の FQDN は、DNS が Caddy（現在 `192.168.11.11`、移行後 `10.77.20.10`）に解決し、Caddy が宛先へ転送する。

| FQDN | 用途 | 現在の宛先 | 移行後の宛先 |
| --- | --- | --- | --- |
| `alertmanager.lab.kanare.dev` | Alertmanager | `192.168.11.13:9093` | `10.77.20.11:9093` |
| `grafana.lab.kanare.dev` | Grafana | `192.168.11.13:3000` | `10.77.20.11:3000` |
| `prometheus.lab.kanare.dev` | Prometheus | `192.168.11.13:9090` | `10.77.20.11:9090` |
| `pve.lab.kanare.dev` | Proxmox Web UI | `192.168.11.10:8006` | `10.77.10.10:8006` |
| `home.lab.kanare.dev` | Homepage | `192.168.11.20:3001` | `10.77.20.20:3001` |
| `ha.lab.kanare.dev` | Home Assistant | `192.168.11.20:8123` | `10.77.20.20:8123` |
| `n8n.lab.kanare.dev` | n8n | `192.168.11.20:5678` | `10.77.20.20:5678` |
| `rss.lab.kanare.dev` | FreshRSS | `192.168.11.20:8081` | `10.77.20.20:8081` |
| `adguard.lab.kanare.dev` | AdGuard Home Web UI | `192.168.11.11:3000` | `10.77.20.10:3000` |
| `code.lab.kanare.dev` | code-server | `192.168.11.22:8080` | `10.77.20.30:8080` |
| `cloudcli.lab.kanare.dev` | CloudCLI | `192.168.11.22:3001` | `10.77.20.30:3001` |
| `router.lab.kanare.dev` | ルーター管理画面（Buffalo。2026-11-06 に廃止） | 廃止（`omada.lab` に付け替えた） | 廃止 |
| `omada.lab.kanare.dev` | Omada コントローラーの管理画面（HTTPS） | `192.168.11.12:8043`（Caddy が転送。2026-11-06 に新設） | `10.77.10.3:8043` |
| `infra.lab.kanare.dev` / `vm-infra.lab.kanare.dev` | `vm-infra` への直接アクセス | `192.168.11.11` | `10.77.20.10` |
| `vm-monitoring.lab.kanare.dev` | `vm-monitoring` への直接アクセス | `192.168.11.13` | `10.77.20.11` |
| `vm-apps.lab.kanare.dev` | `vm-apps` への直接アクセス | `192.168.11.20` | `10.77.20.20` |
| `vm-code.lab.kanare.dev` | SSH / mosh の直接アクセス（Moshi など） | `192.168.11.22` | `10.77.20.30` |

`vm-dev` には DNS レコードを置いていない（手動起動のため）。

## その他のアドレス

| 項目 | アドレス | 備考 |
| --- | --- | --- |
| 建物の共用ルーター | `172.22.0.1` | 上流。ER605 の WAN は DHCP で受ける（二重 NAT）。上流が `10.x` を配っていると、`10.77.0.0/16` と被りうる（[ADR-0015](../adr/0015-vlan-address-scheme-10-77.md)） |
| Tailscale の広告範囲 | 現在 `192.168.11.0/24`、移行後 `10.77.20.0/24` と `10.77.40.0/24` | `vm-infra` が subnet router。移行後は、Management に届かないようにする（[ネットワーク設計](03-network.md#外出先からのアクセスtailscale)） |
| AdGuard のフォールバック DNS | `1.1.1.1`、`9.9.9.9` | upstream に接続できないときだけ使う。DHCP では配らない（[DNS 構成](../services/network/dns.md)） |

## 更新のしかた

IP アドレスを変えたら（ホストの追加・削除、移行を含む）、**同じ変更で、この文書を更新する**。あわせて、実際の設定を直す。

| 直すもの | 場所 |
| --- | --- |
| VM の IP | `terraform/proxmox/terraform.tfvars` |
| ホスト | `ansible/inventory/`（`hosts.yml`、`group_vars/`、`host_vars/`） |
| Caddy の転送先 | `docker/compose/reverse-proxy/Caddyfile` |
| DNS のレコード | CoreDNS のゾーン（[DNS 構成](../services/network/dns.md)） |
| 監視の対象 | Prometheus の scrape 対象（[監視・アラート](../services/platform/monitoring.md)） |
| 機器の設定値 | [ER605](../hardware/er605/settings.md)、[SG2210P](../hardware/sg2210p/settings.md)、[Buffalo](../hardware/wsr-1800ax4p/settings.md)、[ThinkCentre](../hardware/thinkcentre-m70q-tiny/settings.md) の `settings.md` |
| 構成図 | [メインの構成図](../diagrams/main-diagram/make-main-diagram.py)、[物理構成図](../diagrams/physical-diagram/make-physical-diagram.py)（生成スクリプトの「配置」） |

移行（段階 3）の切り替えの手順と、直す箇所の一覧は、[VLAN 設計](08-vlan-design.md)にある。
