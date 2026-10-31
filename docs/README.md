# docs

| ディレクトリ | 内容 |
| --- | --- |
| [architecture/](architecture/README.md) | 方式設計。構成図、インフラ、ネットワーク、可用性・信頼性、セキュリティ、移行性、災害対策 |
| [services/](services/01-dns.md) | サービスごとの詳細設計: [DNS](services/01-dns.md)、[リバースプロキシと TLS](services/02-reverse-proxy-tls.md)、[監視・アラート](services/03-monitoring.md)、[Home Assistant](services/05-home-assistant.md)、[Homepage](services/04-homepage.md)、[n8n](services/06-n8n.md)、[vm-code](services/08-vm-code.md)、[CI/CD](services/07-cicd.md) |
| [operations/](operations/runbooks/README.md) | 運用。[Runbook](operations/runbooks/README.md)、[バックアップの手順](operations/runbooks/06-backup-restore.md)、[障害記録](operations/incidents/2026-10-22-lvm-thin-exhaustion.md)（[INC-2026-10-25](operations/incidents/2026-10-25-nic-hardware-unit-hang.md)）、[ロードマップ](operations/roadmap/README.md)（[Omada・VLAN・OPNsense](operations/roadmap/04-network-omada-vlan.md)、[GPU 搭載 PC](operations/roadmap/05-gpu-pc.md)、[見送り中の項目](operations/roadmap/03-deferred.md)） |
| [adr/](adr/README.md) | 設計判断の記録（ADR） |
| [homelab-service-list.md](homelab-service-list.md) | ホームラボで使えるツールの一覧（候補集。このリポジトリの構成ではない） |
| screenshots/ | README・監視文書で使う画像 |
