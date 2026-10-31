# 完了済みの項目

[ロードマップ](README.md)のうち、完了した項目。詳細は設計書・ADR に移してあり、ここでは一行にまとめる。

## インフラ基盤

- [x] ハードウェア調達、Proxmox VE インストール（`192.168.11.10`）、メモリ増設（8GB → 24GB）
- [x] ネットワーク設計と IP 規約の確定（`README.md`）、DNS ドメイン `lab.kanare.dev` の決定
- [x] Cloud-init テンプレート VM、SSH 鍵ペア、Proxmox API トークン（`terraform/proxmox/README.md`）
- [x] 秘密情報管理方針（SOPS + age。[secrets Runbook](../runbooks/03-secrets.md)）
- [x] バックアップ方針（VM 全体は取らない。VM 外の再現不能データだけ台帳で守る。[ADR 0001](../../adr/0001-no-vm-backup.md)）
- [x] CI（lint のみ。`plan` / `apply` は自動化しない。[ADR 0006](../../adr/0006-ci-lint-only.md)、[CI/CD](../../services/cicd.md)）
- [x] AS-IS の構成図（[概要](../../architecture/01-overview.md) の ASCII 図と `docs/diagrams/`）

## サービス

- [x] `vm-infra` / `vm-monitoring` / `vm-dev` の構成を Terraform + Ansible で完全再現できるようにした
- [x] DNS: CoreDNS（`lab.kanare.dev` の権威 DNS）+ AdGuard Home + Unbound（[DNS](../../services/dns.md)）
- [x] Caddy（Docker Compose、Cloudflare DNS-01 で Let's Encrypt 証明書）と `pve.lab.kanare.dev`（[リバースプロキシと TLS](../../services/reverse-proxy-tls.md)）
- [x] Tailscale を `vm-infra` にサブネットルーターとして導入（二重 NAT のため WireGuard の代わり。[ADR 0005](../../adr/0005-tailscale-only-remote-access.md)）
- [x] Authelia は導入しない（[ADR 0008](../../adr/0008-no-authelia.md)）。認証のない画面が必要になったら `basic_auth` を検討する
- [x] `vm-apps` を常時起動し、Homepage を `home.lab.kanare.dev` で稼働（[Homepage](../../services/homepage.md)）
- [x] 常用リモート開発環境を `vm-dev` から分離し、`vm-code` として切り出した（[vm-code](../../services/vm-code.md)）
- [x] Home Assistant を `vm-apps` に導入し、SwitchBot Cloud と Spotify をつなぐ（[ADR 0011](../../adr/0011-home-assistant-on-vm-apps.md)、[Home Assistant](../../services/home-assistant.md)）
- [x] n8n を `vm-apps` に導入し、週次レポート `weekly-report` を `#homelab-reports` に送る（[ADR 0012](../../adr/0012-n8n-on-vm-apps.md)、[n8n](../../services/n8n.md)）。アラートの通知は Alertmanager の直送のままにする（通知の経路が他の VM の障害に左右されないため。[ADR 0007](../../adr/0007-vm-host-dns-is-router.md)、[ADR 0010](../../adr/0010-external-heartbeat.md)）

## 監視・可観測性

- [x] Prometheus + Grafana、`node_exporter`、ダッシュボード（Node Exporter Full, Prometheus Overview）、`grafana.lab.kanare.dev` / `prometheus.lab.kanare.dev`
- [x] blackbox_exporter による外形監視と、Unbound の応答失敗を検知するアラート
- [x] Alertmanager から個人 Slack への通知
- [x] 外部 Heartbeat（Healthchecks.io）でホスト・NIC・監視 VM の停止を外から検知（[ADR 0010](../../adr/0010-external-heartbeat.md)、[INC-2026-10-25](../incidents/2026-10-25-nic-hardware-unit-hang.md)）

詳細は [監視・アラート](../../services/monitoring.md)。
