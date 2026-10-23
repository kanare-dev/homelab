# 信頼性

壊れにくさ（障害の予防）と、壊れたときの検知・再発防止の仕組みを整理する。止まったあとの復旧は [可用性](../02_availability/availability.md) と [災害対策](../10_disaster-recovery/disaster-recovery.md)。

## 方針

- **構成をコードで持つ**。手作業の変更を減らし、再現できないものを作らない。
- **容量の上限を設ける**。ログ・時系列データ・ストレージが無限に増える状態を残さない（INC-2026-10-22）。
- **障害は検知を先に整える**。復旧が数分で済んでも、検知が遅れれば損失が大きい。
- 障害から得た再発防止は、`docs/incidents/` に記録し、設計書とコードに反映する。

## 変更時の信頼性確保

| 対象 | 仕組み |
| --- | --- |
| 構成の再現性 | Terraform（VM）と Ansible（OS・コンテナ）。冪等に作り、`terraform apply` が `No changes.` になる状態を保つ |
| 静的チェック | `make lint-all`（ansible-lint、yamllint、SOPS 暗号化の確認）。push 前にローカルで通す。CI（`.github/workflows/lint.yml`）も同じチェック。詳細は [CI/CD](../05_operations-maintainability/cicd.md) |
| 変更前の確認 | `terraform plan`、`ansible-playbook --check`（`make check`） |
| 再起動を伴う変更 | 1 台ずつ適用する。`vm-infra` は最後 |
| 設定の履歴 | Git。機密値は SOPS で暗号化して同じリポジトリに置く |

## データの保護

| データ | 場所 | 保護 | 失ったとき |
| --- | --- | --- | --- |
| 構成（コード） | Git（GitHub） | リモートに複製 | — |
| 機密値 | SOPS 暗号化ファイル（Git） | age 秘密鍵で復号。鍵は Git の外に退避 | 鍵を失うと復号できない（[セキュリティ](../06_security/security.md#鍵の保管と退避)） |
| Prometheus の時系列 | `vm-monitoring` の Docker ボリューム | 保持 30 日 / 5GB。バックアップなし | 履歴が消える。再構築で稼働に影響なし |
| Grafana | 同上 | ダッシュボードは provisioning でコード化 | 手作業で作った設定だけ消える |
| AdGuard の設定・クエリログ | `vm-infra`（`/opt/dns/adguard/`） | クエリログは 7 日保持。設定は `playbooks/infra.yml` で再現できる範囲 | 手作業で追加したフィルタ設定が消える |
| Caddy の証明書 | `vm-infra` の Docker ボリューム | 再取得できる | 再取得まで一時的に HTTPS が使えない |
| VM 全体 | `local-lvm` | **バックアップを取らない**（[運用 Runbook](../../runbook.md#バックアップ)） | 再構築する |

## 容量の上限

ログ・時系列データ・ストレージの上限は [監視・アラート](../05_operations-maintainability/monitoring.md#容量の上限設定) の表を正とする。

- thin pool は過剰割当（約 1.4 倍）。仮想ディスクに `discard` を有効にし、毎週 `fstrim.timer` で未使用ブロックを返す。
- 過剰割当が 1.5 倍を超えると `LvmThinPoolOverprovisioned`（warning）。

## 障害の検知

アラートの一覧と待ち時間は [監視・アラート](../05_operations-maintainability/monitoring.md#監視している項目) を正とする。信頼性の観点では、次の「監視の盲点」を塞ぐ仕組みが重要。

| 盲点 | 対策 |
| --- | --- |
| 収集が止まって、アラートが何も出ない | `PveStorageMetricsStale` / `Missing`、`UnboundProbeStale` / `Missing` |
| 通知経路が壊れている | `Watchdog`（常時 firing）、`AlertmanagerNotificationsFailing` |
| fallback で隠れる障害 | `UnboundProbeFailing`（未キャッシュの名前を Unbound に直接引く） |
| 収集スクリプトの不正な出力 | 変更時は PVE 上で一時ディレクトリに出力して確認する（[監視・アラート](../05_operations-maintainability/monitoring.md#収集スクリプトを変更するときの注意)） |
| 監視 VM 自身・ホストの停止 | **塞げていない**（外部監視は見送り） |

## 既知の弱点と対応状況

| 弱点 | 状況 |
| --- | --- |
| コンテナイメージが `latest` | 更新で意図せず挙動が変わる。バージョン固定は未実施 |
| Docker イメージ・OS の更新が手動 | 手順は [運用 Runbook](../../runbook.md#更新手順)。定期実施の仕組みはない |
| NTP の時刻ずれの監視がない | `ntp.nict.jp` / `time.google.com` に同期するが、ずれの検知は未実施 |
| 復旧手順の訓練 | VM 停止と Unbound 障害の検知は実機で確認済み。ホストの再構築は未実施（[災害対策](../10_disaster-recovery/disaster-recovery.md)） |

## 障害から得た再発防止

| 障害 | 再発防止 |
| --- | --- |
| [thin pool 枯渇（INC-2026-10-22）](../../incidents/2026-10-22-lvm-thin-exhaustion.md) | `discard` 有効化、`fstrim`、容量アラート、VM 停止アラート、Slack 通知、容量の上限設定 |
| [PVE 管理画面の破損（INC-2026-10-22-b）](../../incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md) | パッチを「判定式の置換」にして冪等化。復旧手順を Runbook に記載 |
