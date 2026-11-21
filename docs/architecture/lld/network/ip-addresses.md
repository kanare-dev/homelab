# IP アドレス一覧

この文書は、homelab の IP アドレスを 1 か所にまとめた一覧である。アドレスの範囲、VLAN、ホスト、FQDN の宛先を示す。**IP アドレスについては、この文書が正である。**

- 設計の理由は、[第5章 ネットワーク](../../hld/05-network.md)と ADR（[0015](../../../adr/0015-vlan-address-scheme-10-77.md)、[0022](../../../adr/0022-vlan-set-and-ids.md)、[0024](../../../adr/0024-dhcp-dns-single-no-fallback.md)、[0025](../../../adr/0025-address-octets-by-role.md)、[0026](../../../adr/0026-vmid-from-vlan-and-octet.md)、[0027](../../../adr/0027-servers-octet-bands-and-emergency-dns.md)）にある。移行の手順は、[移行計画](../../../operations/roadmap/10-er605-sg2210p-migration-plan.md)。
- 実際に設定している値は、VM の IP が `terraform/proxmox/terraform.tfvars`、ホストが `ansible/inventory/`、Caddy の転送先が `docker/compose/reverse-proxy/Caddyfile`、DNS のレコードが CoreDNS のゾーンにある（[更新のしかた](#更新のしかた)）。
- 秘密の値と、機器の MAC アドレスは書かない。

アドレスは、`10.77.0.0/16` を VLAN ごとに `10.77.<VLAN>.0/24` に分けて使っている。ER605 の既定のネットワークは Management（VLAN10、`10.77.10.0/24`）に統合しており、VLAN1 は使わない（[ADR-0032](../../../adr/0032-merge-default-network-into-management-vlan10.md)）。`10.77.99.0/24` は `Blackhole`（VLAN 999）で、DHCP はなく、どこにも繋がない。

## アドレス体系

VLAN ID とサブネットの第 3 オクテットを揃える（第 2 オクテットは `77` で固定）。第 4 オクテットは、現在の値を引き継がず、役割で決める（[ADR-0025](../../../adr/0025-address-octets-by-role.md)、[ADR-0027](../../../adr/0027-servers-octet-bands-and-emergency-dns.md)）。

## VLAN 一覧

VLAN の ID は、信頼度の高い順（内側から外側）に振る。外部に触れるもの（Guests、DMZ）を末尾に置く（[ADR-0022](../../../adr/0022-vlan-set-and-ids.md)）。

| VLAN | 名前 | サブネット | ゲートウェイ | DHCP プール | 置くもの |
| --- | --- | --- | --- | --- | --- |
| 10 | Management | `10.77.10.0/24` | `.1` | `.240–.250`（緊急用） | ルーター、Managed Switch、AP、Omada コントローラー、Proxmox ホスト |
| 20 | Servers | `10.77.20.0/24` | `.1` | なし（固定のみ） | 常時稼働のサーバー: `vm-infra`、`vm-monitoring`、`vm-apps`、`vm-code` |
| 30 | Trusted | `10.77.30.0/24` | `.1` | `.100–.199` | 母艦 PC、スマホ、タブレットなどの日常端末 |
| 40 | Lab | `10.77.40.0/24` | `.1` | `.100–.149` | 一時的な検証用 VM、開発環境（`vm-dev`） |
| 50 | IoT | `10.77.50.0/24` | `.1` | `.100–.149` | テレビ（AirPlay / Google TV）などのデバイス |
| 60 | Guests | `10.77.60.0/24` | `.1` | `.100–.199` | 来客の端末 |
| 70 | DMZ | `10.77.70.0/24` | `.1` | なし（固定のみ） | ハニーポット、公開用の Web サーバー、`cloudflared`（[DMZ と外部公開](../../../operations/roadmap/07-dmz.md)）。VLAN は作成済みで、置くものは 07 の計画で追加する |
| 999 | Blackhole | `10.77.99.0/24` | `.1` | なし | 使わないポートの native。どこにも繋がない |

各 VLAN のゲートウェイは、ルーターの VLAN インターフェース（`.1`）。ルーター自身の管理アドレスは、Management の `10.77.10.1`。

## アドレス帯の区切り

全 VLAN で同じ区切りにする。

| 範囲 | 用途 |
| --- | --- |
| `.1` | ゲートウェイ（ルーターの VLAN インターフェース） |
| `.2–.9` | ネットワーク機器（Management のみ使う。他の VLAN では未使用） |
| `.10–.49` | 固定アドレス（VM、サーバーなど） |
| `.50–.99` | DHCP 予約（Mac、テレビなど。プールの外に置くので、予約とプールが衝突しない） |
| `.100–.149` / `.100–.199` | DHCP プール（範囲は VLAN ごと。上の表。DHCP を使う VLAN のみ） |
| `.200–.254` | 予備（将来の拡張）。Management の `.240–.250` は緊急用プール |

## Servers の固定アドレスの帯

Servers（`10.77.20.0/24`）の固定アドレス（`.10–.49`）は、役割の帯に分ける（[ADR-0027](../../../adr/0027-servers-octet-bands-and-emergency-dns.md)）。新しい VM は、役割の帯の空きに置く。帯は番号の整理のためで、ネットワークの隔離ではない（同じ VLAN の中の通信は、ER605 の ACL を通らない）。ほかの VLAN は、台数が少ないので連番にする。

| 範囲 | 役割 | 割り当て |
| --- | --- | --- |
| `.10–.19` | 基盤・運用 | `vm-infra` が `.10`、`vm-monitoring` が `.11` |
| `.20–.29` | アプリ | `vm-apps` が `.20` |
| `.30–.39` | 開発・作業用 | `vm-code` が `.30` |
| `.40–.49` | 未使用 | 将来の拡張 |

## DHCP

- DHCP が配る DNS サーバーは、`10.77.20.10`（`vm-infra`）。フォールバックは配らない（[ADR-0024](../../../adr/0024-dhcp-dns-single-no-fallback.md)）。**例外: Management の緊急用プールは、ルーター（`10.77.10.1`）を配る**（[ADR-0027](../../../adr/0027-servers-octet-bands-and-emergency-dns.md)）。`vm-infra` が止まっていても、外部の名前を引ける。`*.lab.kanare.dev` は引けないので、管理機器は IP で開く。
- リース時間は VLAN ごとに決める。Management の緊急用プールは 1 時間、Trusted は 48 時間、Lab と IoT は 24 時間、Guests は 4 時間。Guests は短くして、来客の端末の情報を長く保持しない。
- Lab は、Terraform で固定 IP を振る VM（`vm-dev` など）と、手で立てる使い捨ての VM が混在する。前者は `.10–.49`、後者は DHCP の `.100–.149` に入れる。
- Trusted の常用機（Mac など）は、DHCP 予約（`.50–.99`）で固定する。
- Servers・DMZ は DHCP を配らない。DMZ に侵入した端末が自動でアドレスを得るのを避ける。
- Management は、平時は使わない緊急用プール（`.240–.250`）だけを置く。Mac を直結する緊急の作業と、工場出荷時の機器の採用のため。工場出荷時の機器が DHCP の無い VLAN でどう振る舞うかを実機で確認できたら、外す（[ロードマップ](../../../operations/roadmap/12-ip-address-and-dhcp-review.md)）。Management に出せるのは SG2210P の物理ポートだけで、使わないポートは Management にしない。

## VMID

VM の IP は Terraform（`terraform.tfvars`）で固定する。VMID の規則は、`VLAN ID × 100 + 第 4 オクテット`（[ADR-0026](../../../adr/0026-vmid-from-vlan-and-octet.md)）である。今の VM の VMID は、以前の規則（IP の末尾オクテットに 100 を足した値）のままで、VM を作り直すときに付け替える。下の[ホスト別の IP](#ホスト別の-ip)に、現在の VMID と作り直し後の VMID を並べた。

## ホスト別の IP

| ホスト | 現 VMID | 作り直し後の VMID | IP | VLAN | 備考 |
| --- | --- | --- | --- | --- | --- |
| ルーター | — | — | `10.77.10.1`（ER605） | 10 | VLAN10 のゲートウェイ。既定のネットワークと同じ（[ADR-0032](../../../adr/0032-merge-default-network-into-management-vlan10.md)） |
| Managed Switch（SG2210P） | — | — | `10.77.10.2` | 10 | 静的 |
| Omada コントローラー（`vm-omada`） | 112 | 1003 | `10.77.10.3` | 10 | NIC 1 枚（VLAN10） |
| AP | — | — | `10.77.10.4–.9` | 10 | 採番は購入後に確定する |
| Proxmox（`pve`） | — | — | `10.77.10.10` | 10 | タグ付きの `vmbr0.10` |
| `vm-infra` | 111 | 2010 | `10.77.20.10` | 20 | DNS、Caddy、Tailscale |
| `vm-monitoring` | 113 | 2011 | `10.77.20.11` | 20 | |
| `vm-apps` | 120 | 2020 | `10.77.20.20` | 20 | |
| `vm-code` | 122 | 2030 | `10.77.20.30` | 20 | |
| `vm-dev` | 121 | 4010 | `10.77.40.10` | 40 | 手動起動 |
| Buffalo（AP モード） | — | — | `10.77.30.50` | 30 | Trusted。`.2–.9` は Management だけなので、予約の帯 `.50–.99` を使う。Omada の AP を導入するまでの構成 |
| テレビ | — | — | `10.77.50.x` | 50 | DHCP 予約（`.50–.99`）で固定。無線 |
| `ubuntu-cloud` | 9000 | 9000 | — | — | VM のテンプレート。IP なし |

Mac、スマホなどの日常端末は、DHCP で受け取る（Trusted。常用機は予約）。

## FQDN の宛先

内部 DNS は `lab.kanare.dev` ゾーン（CoreDNS が権威）。名前の付け方は [第5章 ネットワーク](../../hld/05-network.md#ドメイン命名規約)。Caddy 経由の FQDN は、DNS が Caddy（`10.77.20.10`）に解決し、Caddy が宛先へ転送する。

| FQDN | 用途 | 宛先 |
| --- | --- | --- |
| `alertmanager.lab.kanare.dev` | Alertmanager | `10.77.20.11:9093` |
| `grafana.lab.kanare.dev` | Grafana | `10.77.20.11:3000` |
| `prometheus.lab.kanare.dev` | Prometheus | `10.77.20.11:9090` |
| `pve.lab.kanare.dev` | Proxmox Web UI | `10.77.10.10:8006`（2026-11-19 から。Caddy が転送） |
| `home.lab.kanare.dev` | Homepage | `10.77.20.20:3001` |
| `ha.lab.kanare.dev` | Home Assistant | `10.77.20.20:8123` |
| `n8n.lab.kanare.dev` | n8n | `10.77.20.20:5678` |
| `rss.lab.kanare.dev` | FreshRSS | `10.77.20.20:8081` |
| `adguard.lab.kanare.dev` | AdGuard Home Web UI | `10.77.20.10:3000` |
| `code.lab.kanare.dev` | code-server | `10.77.20.30:8080` |
| `cloudcli.lab.kanare.dev` | CloudCLI | `10.77.20.30:3001` |
| `omada.lab.kanare.dev` | Omada コントローラーの管理画面（HTTPS） | `10.77.10.3:8043`（Caddy が転送。2026-11-19 から） |
| `infra.lab.kanare.dev` / `vm-infra.lab.kanare.dev` | `vm-infra` への直接アクセス | `10.77.20.10` |
| `vm-monitoring.lab.kanare.dev` | `vm-monitoring` への直接アクセス | `10.77.20.11` |
| `vm-apps.lab.kanare.dev` | `vm-apps` への直接アクセス | `10.77.20.20` |
| `vm-code.lab.kanare.dev` | SSH / mosh の直接アクセス（Moshi など） | `10.77.20.30` |

`vm-dev` には DNS レコードを置いていない（手動起動のため）。

## その他のアドレス

| 項目 | アドレス | 備考 |
| --- | --- | --- |
| 建物の共用ルーター | `172.22.0.1` | 上流。ER605 の WAN は DHCP で受ける（二重 NAT）。上流が `10.x` を配っていると、`10.77.0.0/16` と被りうる（[ADR-0015](../../../adr/0015-vlan-address-scheme-10-77.md)） |
| Tailscale の広告範囲 | `10.77.20.0/24`、`10.77.40.0/24` だけ | `vm-infra` が subnet router。Management には届かない（[第5章 ネットワーク](../../hld/05-network.md#外出先からのアクセスtailscale)） |
| AdGuard のフォールバック DNS | `1.1.1.1`、`9.9.9.9` | upstream に接続できないときだけ使う。DHCP では配らない（[DNS 構成](dns.md)） |

## 更新のしかた

IP アドレスを変えたら（ホストの追加・削除、移行を含む）、**同じ変更で、この文書を更新する**。あわせて、実際の設定を直す。

| 直すもの | 場所 |
| --- | --- |
| VM の IP | `terraform/proxmox/terraform.tfvars` |
| ホスト | `ansible/inventory/`（`hosts.yml`、`group_vars/`、`host_vars/`） |
| Caddy の転送先 | `docker/compose/reverse-proxy/Caddyfile` |
| DNS のレコード | CoreDNS のゾーン（[DNS 構成](dns.md)） |
| 監視の対象 | Prometheus の scrape 対象（[監視・アラート](../platform/monitoring.md)） |
| 機器の設定値 | [ER605](../hardware/er605/settings.md)、[SG2210P](../hardware/sg2210p/settings.md)、[Buffalo](../hardware/wsr-1800ax4p/settings.md)、[ThinkCentre](../hardware/thinkcentre-m70q-tiny/settings.md) の `settings.md` |
| 構成図 | [現状の構成図](../../../diagrams/as-is-diagram/make-as-is-diagram.py)、[to-be の構成図](../../../diagrams/to-be-diagram/make-to-be-diagram.py)、[物理構成図](../../../diagrams/physical-diagram/make-physical-diagram.py)（生成スクリプトの「配置」） |
