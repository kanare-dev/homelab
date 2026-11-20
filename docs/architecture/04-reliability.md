# 可用性・信頼性

この文書では、どこが止まると何が使えなくなるか、壊れにくくするための仕組み、障害の検知と再発防止をまとめる。大きな障害からの復旧は [災害対策](07-disaster-recovery.md)で、手順は [運用 Runbook](../operations/runbooks/README.md)で説明している。個人の homelab なので、**SLA や稼働率は約束せず**、ベストエフォートで運用する。

## 方針

- 冗長化（HA クラスタや 2 台目のホスト）はしない。単一障害点があることを理解したうえで受け入れ、**早く気づいて、早く戻せる**ことを優先する。
- ホストや VM が再起動したあと、人の手を借りずにサービスが立ち上がるようにする。
- 構成をコードで管理し、手作業で変更する場面を減らす。再現できないものは作らない。
- 容量に上限を設ける。ログ、時系列データ、ストレージが際限なく増える状態を放置しない（INC-2026-10-22）。
- 障害は、復旧の手順より先に、検知の仕組みを整える。復旧が数分で済んでも、気づくのが遅れれば損失は大きいからである。
- 受け入れたリスクと、それを再検討する条件を、文書に残す。

## 単一障害点と影響

| 障害点 | 影響 | 検知 | 備考 |
| --- | --- | --- | --- |
| Proxmox ホスト（ハード・電源・NVMe） | 全サービス停止 | **Slack には届かない**（監視 VM も止まる）。外部 Heartbeat（Healthchecks.io）が Slack とメールで通知する | UPS なし |
| PVE ホストの NIC（`e1000e`） | ホストと全 VM が LAN から消える。OS は動いている | **Slack には届かない**（監視 VM も外に出られない）。外部 Heartbeat（ADR-0010）が Slack とメールで通知する | INC-2026-10-25。TSO/GSO/GRO を無効化して対処 |
| thin pool 枯渇 | 全 VM が `io-error` で一時停止 | `LvmThinPoolData*`（Slack） | INC-2026-10-22。容量アラートで枯渇前に検知する |
| `vm-infra` | 全 LAN の名前解決、`*.lab.kanare.dev` の入口（Caddy）、外出先からのアクセス（Tailscale）が止まる | `TargetDown`、`PveVmStopped`（Slack） | DNS・リバースプロキシ・VPN が 1 台に集中している |
| `vm-monitoring` | 監視と通知が止まる。サービス自体は影響なし | **Slack には届かない**。外部 Heartbeat が Slack とメールで通知する | [監視・アラート](../services/platform/monitoring.md#限界既知の弱点) |
| `vm-omada` | Omada の画面と管理が使えない。ER605・SG2210P は設定を持って動き続ける | `TargetDown`、`HostMemory*`、`ServiceProbeFailed`（Slack） | INC-2026-11-09。メモリ枯渇で固まった。VM 4GB と、コンテナの上限（Java ヒープ・MongoDB キャッシュ・`mem_limit`）で対処 |
| Unbound | 外部ドメインの名前解決が `SERVFAIL` になる（fallback は効かない） | `UnboundProbeFailing`（Slack） | [DNS 構成](../services/network/dns.md#fallback-dns-の限界) |
| ルーター・回線 | インターネットと外出先からの接続が止まる。LAN 内は動く | なし | 二重 NAT のため、建物側の障害も含む |
| Cloudflare / Let's Encrypt | 新規・更新の証明書が取れない | Caddy のログ | 証明書は期限の前に更新するため、短時間の障害では影響しない |

## 起動・停止の設計

ホストを起動すると、VM が依存関係の順に立ち上がる。順序と待機秒数は、Terraform（`terraform.tfvars`）で管理している。

| 順序 | VM | 自動起動 | 待機（up / down 秒） |
| --- | --- | --- | --- |
| 1 | `vm-infra` | する | 30 / 60 |
| 2 | `vm-monitoring` | する | 20 / 60 |
| 3 | `vm-apps` | する | 20 / 60 |
| 4 | `vm-dev` | しない | 10 / 30 |
| 5 | `vm-code` | する | 10 / 30 |
| 6 | `vm-omada` | する | 10 / 60 |

- 停止するときは、起動と逆の順に止める。DNS を担う `vm-infra` は、最初に起動し、最後に止まる。
- 各 VM のコンテナには `restart: unless-stopped` を設定している。VM が起動すれば、コンテナも自動で起動する。
- 手動で操作する手順は、[運用 Runbook](../operations/runbooks/01-vm-startup-shutdown.md#vm-自動起動停止)に書いている。

## 部分障害への備え

| 対象 | 仕組み |
| --- | --- |
| DNS の上流断 | AdGuard の fallback DNS（`1.1.1.1` / `9.9.9.9`）。upstream に**接続できない**ときだけ働く |
| Unbound の一時的な応答なし | `serve-expired: yes`（TTL 1 時間）で、期限切れのキャッシュを返す |
| `terraform apply` による VM の再起動 | 再起動を伴う変更は 1 台ずつ適用し、`vm-infra` は最後にする（[運用 Runbook](../operations/runbooks/15-terraform-apply-restart.md#terraform-apply-が-vm-を再起動するとき)） |
| 外出先からの到達 | Tailscale の key expiry を `vm-infra` で無効化（期限切れで繋がらなくなるのを防ぐ） |

## 変更時の信頼性確保

| 対象 | 仕組み |
| --- | --- |
| 構成の再現性 | Terraform（VM）と Ansible（OS・コンテナ）。冪等に作り、`terraform apply` が `No changes.` になる状態を保つ |
| 静的チェック | `make lint-all`（ansible-lint、yamllint、SOPS 暗号化の確認）。push 前にローカルで通す。CI（`.github/workflows/lint.yml`）も同じチェック。詳細は [CI/CD](../services/dev/cicd.md) |
| 変更前の確認 | `terraform plan`、`ansible-playbook --check`（`make check`） |
| 再起動を伴う変更 | 1 台ずつ適用する。`vm-infra` は最後 |
| 設定の履歴 | Git。機密値は SOPS で暗号化して同じリポジトリに置く |

## データの保護

| データ | 場所 | 保護 | 失ったとき |
| --- | --- | --- | --- |
| 構成（コード） | Git（GitHub） | リモートに複製 | — |
| 機密値 | SOPS 暗号化ファイル（Git） | age 秘密鍵で復号。鍵は Git の外に退避 | 鍵を失うと復号できない（[セキュリティ](05-security.md#鍵の保管と退避)） |
| Prometheus の時系列 | `vm-monitoring` の Docker ボリューム | 保持 30 日 / 5GB。バックアップなし | 履歴が消える。再構築で稼働に影響なし |
| Grafana | 同上 | ダッシュボードは provisioning でコード化 | 手作業で作った設定だけ消える |
| AdGuard の設定・クエリログ | `vm-infra`（`/opt/dns/adguard/`） | クエリログは 7 日保持。設定は `playbooks/infra.yml` で再現できる範囲 | 手作業で追加したフィルタ設定が消える |
| Caddy の証明書 | `vm-infra` の Docker ボリューム | 再取得できる | 再取得まで一時的に HTTPS が使えない |
| VM 全体 | `local-lvm` | **バックアップを取らない**（[ADR-0001](../adr/0001-no-vm-backup.md)） | 再構築する |

## 容量の上限

ログ、時系列データ、ストレージの上限は、[監視・アラート](../services/platform/monitoring.md#容量の上限設定)の表が正である。

- thin pool には、容量より多くのディスクを割り当てている（約 1.4 倍）。仮想ディスクに `discard` を有効にし、毎週 `fstrim.timer` で未使用のブロックを返している。
- 割り当てが 1.5 倍を超えると、`LvmThinPoolOverprovisioned`（warning）が出る。

## 障害の検知

アラートの一覧と待ち時間は、[監視・アラート](../services/platform/monitoring.md#監視している項目)が正である。信頼性の面では、次の表にある「監視の盲点」を塞ぐ仕組みが重要になる。

| 盲点 | 対策 |
| --- | --- |
| 収集が止まって、アラートが何も出ない | `PveStorageMetricsStale` / `Missing`、`UnboundProbeStale` / `Missing` |
| 通知経路が壊れている | `Watchdog`（常時 firing）、`AlertmanagerNotificationsFailing` |
| fallback で隠れる障害 | `UnboundProbeFailing`（未キャッシュの名前を Unbound に直接引く） |
| 収集スクリプトの不正な出力 | 変更時は PVE 上で一時ディレクトリに出力して確認する（[監視・アラート](../services/platform/monitoring.md#収集スクリプトを変更するときの注意)） |
| 監視 VM 自身・ホストの停止 | 外部 Heartbeat で検知（[ADR-0010](../adr/0010-external-heartbeat.md)） |

## 既知の弱点と対応状況

| 弱点 | 状況 |
| --- | --- |
| コンテナイメージが `latest` | 更新で意図せず挙動が変わる。バージョン固定は未実施 |
| Docker イメージ・OS の更新が手動 | 手順は [運用 Runbook](../operations/runbooks/02-updates.md#更新手順)。定期実施の仕組みはない |
| NTP の時刻ずれの監視がない | `ntp.nict.jp` / `time.google.com` に同期するが、ずれの検知は未実施 |
| 復旧手順の訓練 | VM 停止と Unbound 障害の検知は実機で確認済み。ホストの再構築は未実施（[災害対策](07-disaster-recovery.md)） |

## 障害から得た再発防止

| 障害 | 再発防止 |
| --- | --- |
| [thin pool 枯渇（INC-2026-10-22）](../operations/incidents/2026-10-22-lvm-thin-exhaustion.md) | `discard` 有効化、`fstrim`、容量アラート、VM 停止アラート、Slack 通知、容量の上限設定 |
| [PVE 管理画面の破損（INC-2026-10-22-b）](../operations/incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md) | パッチを「判定式の置換」にして冪等化。復旧手順を Runbook に記載 |
| [PVE の NIC 送信停止（INC-2026-10-25）](../operations/incidents/2026-10-25-nic-hardware-unit-hang.md) | NIC のオフロード（TSO/GSO/GRO）を無効化。外部 Heartbeat（Healthchecks.io）を導入 |
| [vm-omada のメモリ枯渇（INC-2026-11-09）](../operations/incidents/2026-11-09-omada-memory-exhaustion.md) | VM を 4GB に増設。Omada コンテナに Java ヒープ・MongoDB キャッシュ・`mem_limit` の上限を設定 |

## 目標（暫定）

数値の根拠にできる実測は、まだない。運用しながら見直していく。

| 項目 | 目標 | 根拠 |
| --- | --- | --- |
| 障害の検知 | VM 停止は約 4 分で Slack に通知 | 2026-10-22 の実機テストの結果（[監視・アラート](../services/platform/monitoring.md#動作確認の記録)） |
| 復旧 | VM 単体の障害は、気づいてから数分〜数十分で復旧 | INC-2026-10-22 の復旧実績（pool 拡張から VM 再開まで約 10 秒） |
| 稼働率 | 目標を置かない | 単一ホスト・UPS なしで、約束できる根拠がない |

## 受け入れたリスクと再検討の条件

| リスク | 判断 | 再検討の条件 |
| --- | --- | --- |
| ホスト・監視 VM の停止が Slack に通知されない | 外部 Heartbeat で補完している（[ADR-0010](../adr/0010-external-heartbeat.md)、旧判断は [ADR-0002](../adr/0002-no-external-monitoring.md)） | Healthchecks.io の無料枠の条件が変わったとき |
| 停電でホストが止まる | 受け入れ（UPS 未導入） | ロードマップの「UPS 導入と自動シャットダウン」に着手するとき |
| `vm-infra` への集中 | 受け入れ | DNS を別ホスト（Raspberry Pi など）に分けるとき。VLAN 化で影響範囲がさらに広がる（[VLAN 設計](08-vlan-design.md#前提と制約)） |
