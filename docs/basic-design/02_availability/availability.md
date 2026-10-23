# 可用性

どこが止まると何が使えなくなるか、どう気づき、どう戻すかを整理する。個人の homelab であり、**SLA・稼働率の約束はしない**（ベストエフォート）。

## 方針

- 冗長化（HA クラスタ、2 台目のホスト）はしない。単一障害点は認識したうえで受け入れ、**早く気づいて早く戻せる**ことを優先する。
- ホストと VM の再起動後に、人手なしでサービスが立ち上がるようにする。
- 受け入れたリスクと、再検討の条件を文書に残す。

## 単一障害点と影響

| 障害点 | 影響 | 検知 | 備考 |
| --- | --- | --- | --- |
| Proxmox ホスト（ハード・電源・NVMe） | 全サービス停止 | **通知されない**（監視 VM も止まる） | UPS なし。DNS・Homepage が使えない症状で気づく |
| thin pool 枯渇 | 全 VM が `io-error` で一時停止 | `LvmThinPoolData*`（Slack） | INC-2026-10-22。容量アラートで枯渇前に検知する |
| `vm-infra` | 全 LAN の名前解決、`*.lab.kanare.dev` の入口（Caddy）、外出先からのアクセス（Tailscale）が止まる | `TargetDown`、`PveVmStopped`（Slack） | DNS・リバースプロキシ・VPN が 1 台に集中している |
| `vm-monitoring` | 監視と通知が止まる。サービス自体は影響なし | **通知されない** | [監視・アラート](../05_operations-maintainability/monitoring.md#限界既知の弱点) |
| Unbound | 外部ドメインの名前解決が `SERVFAIL` になる（fallback は効かない） | `UnboundProbeFailing`（Slack） | [DNS 構成](../07_network/dns.md#fallback-dns-の限界) |
| ルーター・回線 | インターネットと外出先からの接続が止まる。LAN 内は動く | なし | 二重 NAT のため、建物側の障害も含む |
| Cloudflare / Let's Encrypt | 新規・更新の証明書が取れない | Caddy のログ | 証明書は期限の前に更新するため、短時間の障害では影響しない |

## 起動・停止の設計

ホストの起動で、依存順に VM が立ち上がる。順序と待機秒数は Terraform（`terraform.tfvars`）で管理する。

| 順序 | VM | 自動起動 | 待機（up / down 秒） |
| --- | --- | --- | --- |
| 1 | `vm-infra` | する | 30 / 60 |
| 2 | `vm-monitoring` | する | 20 / 60 |
| 3 | `vm-apps` | する | 20 / 60 |
| 4 | `vm-dev` | しない | 10 / 30 |
| 5 | `vm-code` | する | 10 / 30 |

- 停止は逆順。DNS（`vm-infra`）が最後に止まり、最初に起動する。
- 各 VM のコンテナは `restart: unless-stopped`。VM が起動すれば、コンテナも自動で戻る。
- 手動操作は [運用 Runbook](../../runbook.md#vm-自動起動停止)。

## 部分障害への備え

| 対象 | 仕組み |
| --- | --- |
| DNS の上流断 | AdGuard の fallback DNS（`1.1.1.1` / `9.9.9.9`）。upstream に**接続できない**ときだけ働く |
| Unbound の一時的な応答なし | `serve-expired: yes`（TTL 1 時間）で、期限切れのキャッシュを返す |
| `terraform apply` による VM の再起動 | 再起動を伴う変更は 1 台ずつ適用し、`vm-infra` は最後にする（[運用 Runbook](../../runbook.md#terraform-apply-が-vm-を再起動するとき)） |
| 外出先からの到達 | Tailscale の key expiry を `vm-infra` で無効化（期限切れで繋がらなくなるのを防ぐ） |

## 目標（暫定）

数値の根拠となる実測はまだない。運用しながら見直す。

| 項目 | 目標 | 根拠 |
| --- | --- | --- |
| 障害の検知 | VM 停止は約 4 分で Slack に通知 | 2026-10-22 の実機テストの結果（[監視・アラート](../05_operations-maintainability/monitoring.md#動作確認の記録)） |
| 復旧 | VM 単体の障害は、気づいてから数分〜数十分で復旧 | INC-2026-10-22 の復旧実績（pool 拡張から VM 再開まで約 10 秒） |
| 稼働率 | 目標を置かない | 単一ホスト・UPS なしで、約束できる根拠がない |

## 受け入れたリスクと再検討の条件

| リスク | 判断 | 再検討の条件 |
| --- | --- | --- |
| ホスト・監視 VM の停止が通知されない | 受け入れ（[外部監視を導入しない判断](../05_operations-maintainability/monitoring.md#外部監視を導入しない判断2026-10-22)） | 不在中に長時間気づけず困った、常時稼働が必要なサービスを載せた |
| 停電でホストが止まる | 受け入れ（UPS 未導入） | ロードマップの「UPS 導入と自動シャットダウン」に着手するとき |
| `vm-infra` への集中 | 受け入れ | DNS を別ホスト（Raspberry Pi など）に分けるとき。VLAN 化で影響範囲がさらに広がる（[VLAN 設計](../07_network/vlan-design.md#前提と制約)） |

## 関連

- [信頼性](../03_reliability/reliability.md)
- [災害対策](../10_disaster-recovery/disaster-recovery.md)
