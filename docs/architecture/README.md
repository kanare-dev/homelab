# アーキテクチャ（方式設計）

homelab の方式設計。構成の全体像から読み、必要な観点へ進む。サービスごとの詳細は [services/](../services/dns.md)、設計判断の経緯は [adr/](../adr/README.md)、運用手順は [operations/](../operations/runbooks/README.md)。

## 目次

| 文書 | 内容 |
| --- | --- |
| [システム概要](01-overview.md) | 構成図、目的、この構成にした理由、前提と制約 |
| [インフラ構成](02-infrastructure.md) | 物理・論理構成、ソフトウェア構成、資源の配分、拡張の方針 |
| [ネットワーク設計](03-network.md) | IP アドレス・ドメイン命名規約、外部接続（Tailscale、外部サービスへの依存） |
| [可用性・信頼性](04-reliability.md) | 単一障害点、起動順序、変更の確かさ、障害の検知、再発防止 |
| [セキュリティ](05-security.md) | 脅威の想定、秘密情報、アクセス制御、未対応の項目 |
| [移行性](06-migration.md) | ハード・ネットワーク・バージョンの移行シナリオ |
| [災害対策](07-disaster-recovery.md) | 想定する災害、バックアップの状況、再構築の手順 |
| [VLAN 設計](08-vlan-design.md) | 次期のネットワーク分割（設計段階。未適用） |

## 設計の観点と文書の対応

設計の網羅性を確認するための対応表。観点をまたぐ内容は、正とする文書に書き、ほかからはリンクする。

| 観点 | 正とする文書 |
| --- | --- |
| システム構成・環境 | [システム概要](01-overview.md)、[インフラ構成](02-infrastructure.md) |
| 可用性 | [可用性・信頼性](04-reliability.md) |
| 信頼性 | [可用性・信頼性](04-reliability.md) |
| 性能・拡張性 | [インフラ構成](02-infrastructure.md#拡張の方針) |
| 運用・保守性 | [監視・アラート](../services/monitoring.md)、[CI/CD](../services/cicd.md)、[運用 Runbook](../operations/runbooks/README.md) |
| セキュリティ | [セキュリティ](05-security.md) |
| ネットワーク | [ネットワーク設計](03-network.md)、[DNS](../services/dns.md)、[リバースプロキシと TLS](../services/reverse-proxy-tls.md)、[VLAN 設計](08-vlan-design.md) |
| 外部接続 | [ネットワーク設計](03-network.md#外部接続の方針) |
| 移行性 | [移行性](06-migration.md) |
| 災害対策 | [災害対策](07-disaster-recovery.md) |

## 運用ルール

- 設計を変えたら、該当する文書を同じ変更で更新する。
- 数値の根拠がない目標は「暫定」と明記する。実測が取れたら更新する。
- 機密値は書かない（リポジトリは公開）。
