# アドレス・命名規約

IP アドレスとドメイン名の割り当て規約。名前の定義は `ansible/inventory/group_vars/infra/vars.yml` の `dns_records`、Caddy の転送先は `docker/compose/reverse-proxy/Caddyfile` が正。次期のアドレス体系（`10.<VLAN>.0.0/24`）は [VLAN 設計](vlan-design.md)（未適用）。

## IP アドレス規約（`192.168.11.0/24`）

| 範囲 | 用途 | 例 |
|---|---|---|
| `192.168.11.1` | ルーター / ゲートウェイ | — |
| `192.168.11.10–19` | インフラ（Proxmox、基盤 VM） | `.10` Proxmox、`.11` `vm-infra`、`.13` `vm-monitoring` |
| `192.168.11.20–59` | サーバー / 検証用 VM | `.20` `vm-apps`、`.21` `vm-dev`、`.22` `vm-code` |
| `192.168.11.60–99` | DHCP プール | 動的割当 |
| `192.168.11.100–149` | IoT デバイス | `.100` ESP32 |
| `192.168.11.150–254` | 予約 / 実験用 | — |

VM の IP は Terraform（`terraform.tfvars`）で固定する。VMID は IP の末尾オクテットに 100 を足した値。

## ドメイン命名規約

内部 DNS は `lab.kanare.dev` ゾーン（CoreDNS が権威。[DNS 構成](dns.md)）。サービスは `<サービス名>.lab.kanare.dev`、VM は `<VM 名>.lab.kanare.dev` で引く。

| FQDN | DNS の解決先 | 実際の宛先 | 用途 |
|---|---|---|---|
| `pve.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.10:8006` | Proxmox Web UI |
| `home.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.20:3001` | Homepage |
| `grafana.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.13:3000` | Grafana |
| `prometheus.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.13:9090` | Prometheus |
| `adguard.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.11:3000` | AdGuard Home Web UI |
| `code.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.22:8080` | code-server |
| `cloudcli.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.22:3001` | CloudCLI |
| `router.lab.kanare.dev` | `192.168.11.11`（Caddy） | `192.168.11.1:80` | ルーター管理画面（[DNS 構成](dns.md#ルーター管理画面)） |
| `infra.lab.kanare.dev` / `vm-infra.lab.kanare.dev` | `192.168.11.11` | 同左 | `vm-infra` への直接アクセス |
| `vm-monitoring.lab.kanare.dev` | `192.168.11.13` | 同左 | `vm-monitoring` への直接アクセス |
| `vm-apps.lab.kanare.dev` | `192.168.11.20` | 同左 | `vm-apps` への直接アクセス |
| `vm-code.lab.kanare.dev` | `192.168.11.22` | 同左 | SSH / mosh の直接アクセス（Moshi など） |

`vm-dev` と `vm-windows` には DNS レコードを置いていない（手動起動のため）。Caddy 経由の FQDN には、証明書を FQDN ごとに取得する（[リバースプロキシと TLS](reverse-proxy-tls.md)）。
