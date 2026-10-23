# 方式設計書（基本設計）

homelab の方式設計（基本設計）をまとめる。次の 10 の観点で整理している。ディレクトリ名の番号順に読めば、構成から災害対策まで一通り分かる。

| # | 観点 | ドキュメント |
| --- | --- | --- |
| 01 | システム構成・環境 | [system-overview.md](01_system-environment/system-overview.md) |
| 02 | 可用性 | [availability.md](02_availability/availability.md) |
| 03 | 信頼性 | [reliability.md](03_reliability/reliability.md) |
| 04 | 性能・拡張性 | [capacity-and-scaling.md](04_performance-scalability/capacity-and-scaling.md) |
| 05 | 運用・保守性 | [monitoring.md](05_operations-maintainability/monitoring.md)、[cicd.md](05_operations-maintainability/cicd.md) |
| 06 | セキュリティ | [security.md](06_security/security.md) |
| 07 | ネットワーク | [addressing.md](07_network/addressing.md)、[dns.md](07_network/dns.md)、[reverse-proxy-tls.md](07_network/reverse-proxy-tls.md)、[vlan-design.md](07_network/vlan-design.md) |
| 08 | 外部接続 | [external-connectivity.md](08_external-connectivity/external-connectivity.md) |
| 09 | 移行性 | [migration.md](09_migration/migration.md) |
| 10 | 災害対策 | [disaster-recovery.md](10_disaster-recovery/disaster-recovery.md) |

## 運用ルール

- 設計を変えたら、該当する観点の文書を同じ変更で更新する。
- 観点をまたぐ内容は、片方に正を置き、もう片方からリンクする（例: 監視のアラート一覧は 05 が正で、04 と 03 からリンクする）。
- 数値の根拠がない目標は「暫定」と明記する。実測が取れたら更新する。
- 機密値は書かない（リポジトリは公開）。
