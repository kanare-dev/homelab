# 完了済みの項目

この文書には、[ロードマップ](README.md)の項目のうち、完了したものを載せる。詳しい内容は、設計書と ADR に移してあるので、ここでは 1 行にまとめる。

## インフラ基盤

- [x] ハードウェアを調達し、Proxmox VE を `192.168.11.10` にインストールして、メモリを 8GB から 24GB に増設した。
- [x] ネットワーク設計と IP の規約を確定し（`README.md`）、DNS のドメインを `lab.kanare.dev` に決めた。
- [x] cloud-init のテンプレート VM、SSH 鍵ペア、Proxmox の API トークンを用意した（`terraform/proxmox/README.md`）。
- [x] 秘密情報の管理方針を、SOPS と age に決めた（[secrets Runbook](../runbooks/03-secrets.md)）。
- [x] バックアップの方針を決めた。VM 全体は取らず、VM の外にある再現できないデータだけを、台帳で守る（[ADR 0001](../../adr/0001-no-vm-backup.md)）。
- [x] CI を導入した。lint だけを実行し、`plan` と `apply` は自動化しない（[ADR 0006](../../adr/0006-ci-lint-only.md)、[CI/CD](../../architecture/lld/dev/cicd.md)）。
- [x] 現状（AS-IS）の構成図を作った（[概要](../../architecture/hld/01-system.md)の ASCII 図と、`docs/diagrams/`）。
- [x] ネットワーク機器の名前を役割と番号（`rtr01`、`sw01`、`ap01`）にし、固定 IP を持つホストすべてに `<ホスト名>.lab.kanare.dev` の A レコードを付けた（[ADR-0035](../../adr/0035-network-device-names-by-role.md)、[ADR-0036](../../adr/0036-a-record-for-every-fixed-ip-host.md)、[ロードマップ 15](15-host-names-and-dns-records.md)）。

## サービス

- [x] `vm-infra` / `vm-monitoring` / `vm-dev` の構成を Terraform + Ansible で完全再現できるようにした
- [x] DNS を、CoreDNS（`lab.kanare.dev` の権威 DNS）、AdGuard Home、Unbound の組み合わせで構成した（[DNS](../../architecture/lld/network/dns.md)）。
- [x] Home Assistant の Prometheus 連携で SwitchBot Hub 2 の温度・湿度を Prometheus に集め、Grafana「Room Environment」で見られるようにし、湿度の異常（35% 未満・70% 超が 1 時間）を Slack に通知するようにした。使われていなかった ESP32 のダッシュボードは消した（[ADR-0037](../../adr/0037-room-sensors-via-home-assistant-prometheus.md)、[監視・アラート](../../architecture/lld/platform/monitoring.md#室内の温度湿度)）。
- [x] Caddy を Docker Compose で動かし、Cloudflare の DNS-01 チャレンジで Let's Encrypt の証明書を取得して、`pve.lab.kanare.dev` を公開した（[リバースプロキシと TLS](../../architecture/lld/network/reverse-proxy-tls.md)）。
- [x] Tailscale を、`vm-infra` にサブネットルーターとして導入した。二重 NAT のため、WireGuard の代わりに使う（[ADR 0005](../../adr/0005-tailscale-only-remote-access.md)）。
- [x] Authelia は導入しないことにした（[ADR 0008](../../adr/0008-no-authelia.md)）。認証のない画面が必要になったら、`basic_auth` を検討する。
- [x] `vm-apps` を常時起動にし、Homepage を `home.lab.kanare.dev` で動かした（[Homepage](../../architecture/lld/apps/homepage.md)）。
- [x] 常用リモート開発環境を `vm-dev` から分離し、`vm-code` として切り出した（[vm-code](../../architecture/lld/dev/vm-code.md)）
- [x] Home Assistant を `vm-apps` に導入し、SwitchBot Cloud と Spotify をつなぐ（[ADR 0011](../../adr/0011-home-assistant-on-vm-apps.md)、[Home Assistant](../../architecture/lld/apps/home-assistant.md)）
- [x] n8n を `vm-apps` に導入し、週次レポート `weekly-report` を `#homelab-reports` に送る（[ADR 0012](../../adr/0012-n8n-on-vm-apps.md)、[n8n](../../architecture/lld/apps/n8n.md)）。アラートの通知は Alertmanager の直送のままにする（通知の経路が他の VM の障害に左右されないため。[ADR 0007](../../adr/0007-vm-host-dns-is-router.md)、[ADR 0010](../../adr/0010-external-heartbeat.md)）
- [x] FreshRSS を `vm-apps` に導入する（[ADR 0014](../../adr/0014-freshrss-on-vm-apps.md)、[FreshRSS](../../architecture/lld/apps/freshrss.md)）。購読リストだけ iCloud Drive に退避する

## 監視・可観測性

- [x] Prometheus、Grafana、`node_exporter` を導入し、ダッシュボード（Node Exporter Full と Prometheus Overview）を `grafana.lab.kanare.dev` と `prometheus.lab.kanare.dev` で見られるようにした。
- [x] blackbox_exporter で外形監視を行い、Unbound が応答しなくなったことを検知するアラートを作った。
- [x] Alertmanager から、個人の Slack に通知するようにした。
- [x] 外部 Heartbeat（Healthchecks.io）を使い、ホスト、NIC、監視 VM の停止を、外から検知するようにした（[ADR 0010](../../adr/0010-external-heartbeat.md)、[INC-2026-10-25](../incidents/2026-10-25-nic-hardware-unit-hang.md)）。

詳しくは [監視・アラート](../../architecture/lld/platform/monitoring.md)を参照してほしい。
