# 第2章 信頼性

この章では、どこが止まると何が使えなくなるか、壊れにくくするための仕組み、障害の検知と再発防止、大きな障害からの復旧（災害対策）をまとめる。手順は[運用 Runbook](../../operations/runbooks/README.md)で説明している。個人の homelab なので、**SLA や稼働率は約束せず**、ベストエフォートで運用する。

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
| `vm-monitoring` | 監視と通知が止まる。サービス自体は影響なし | **Slack には届かない**。外部 Heartbeat が Slack とメールで通知する | [監視・アラート](../lld/platform/monitoring.md#限界既知の弱点) |
| `vm-omada` | Omada の画面と管理が使えない。ER605・SG2210P は設定を持って動き続ける | `TargetDown`、`HostMemory*`、`ServiceProbeFailed`（Slack） | INC-2026-11-09。メモリ枯渇で固まった。VM 4GB と、コンテナの上限（Java ヒープ・MongoDB キャッシュ・`mem_limit`）で対処 |
| Unbound | 外部ドメインの名前解決が `SERVFAIL` になる（fallback は効かない） | `UnboundProbeFailing`（Slack） | [DNS 構成](../lld/network/dns.md#fallback-dns-の限界) |
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
- 手動で操作する手順は、[運用 Runbook](../../operations/runbooks/01-vm-startup-shutdown.md#vm-自動起動停止)に書いている。

## 部分障害への備え

| 対象 | 仕組み |
| --- | --- |
| DNS の上流断 | AdGuard の fallback DNS（`1.1.1.1` / `9.9.9.9`）。upstream に**接続できない**ときだけ働く |
| Unbound の一時的な応答なし | `serve-expired: yes`（TTL 1 時間）で、期限切れのキャッシュを返す |
| `terraform apply` による VM の再起動 | 再起動を伴う変更は 1 台ずつ適用し、`vm-infra` は最後にする（[運用 Runbook](../../operations/runbooks/15-terraform-apply-restart.md#terraform-apply-が-vm-を再起動するとき)） |
| 外出先からの到達 | Tailscale の key expiry を `vm-infra` で無効化（期限切れで繋がらなくなるのを防ぐ） |

## 変更時の信頼性確保

| 対象 | 仕組み |
| --- | --- |
| 構成の再現性 | Terraform（VM）と Ansible（OS・コンテナ）。冪等に作り、`terraform apply` が `No changes.` になる状態を保つ |
| 静的チェック | `make lint-all`（ansible-lint、yamllint、SOPS 暗号化の確認）。push 前にローカルで通す。CI（`.github/workflows/lint.yml`）も同じチェック。詳細は [CI/CD](../lld/dev/cicd.md) |
| 変更前の確認 | `terraform plan`、`ansible-playbook --check`（`make check`） |
| 再起動を伴う変更 | 1 台ずつ適用する。`vm-infra` は最後 |
| 設定の履歴 | Git。機密値は SOPS で暗号化して同じリポジトリに置く |

## データの保護

| データ | 場所 | 保護 | 失ったとき |
| --- | --- | --- | --- |
| 構成（コード） | Git（GitHub） | リモートに複製 | — |
| 機密値 | SOPS 暗号化ファイル（Git） | age 秘密鍵で復号。鍵は Git の外に退避 | 鍵を失うと復号できない（[セキュリティ](06-security.md#鍵の保管と退避)） |
| Prometheus の時系列 | `vm-monitoring` の Docker ボリューム | 保持 30 日 / 5GB。バックアップなし | 履歴が消える。再構築で稼働に影響なし |
| Grafana | 同上 | ダッシュボードは provisioning でコード化 | 手作業で作った設定だけ消える |
| AdGuard の設定・クエリログ | `vm-infra`（`/opt/dns/adguard/`） | クエリログは 7 日保持。設定は `playbooks/infra.yml` で再現できる範囲 | 手作業で追加したフィルタ設定が消える |
| Caddy の証明書 | `vm-infra` の Docker ボリューム | 再取得できる | 再取得まで一時的に HTTPS が使えない |
| VM 全体 | `local-lvm` | **バックアップを取らない**（[ADR-0001](../../adr/0001-no-vm-backup.md)） | 再構築する |

## 容量の上限

ログ、時系列データ、ストレージの上限は、[監視・アラート](../lld/platform/monitoring.md#容量の上限設定)の表が正である。

- thin pool には、容量より多くのディスクを割り当てている（約 1.4 倍）。仮想ディスクに `discard` を有効にし、毎週 `fstrim.timer` で未使用のブロックを返している。
- 割り当てが 1.5 倍を超えると、`LvmThinPoolOverprovisioned`（warning）が出る。

## 障害の検知

アラートの一覧と待ち時間は、[監視・アラート](../lld/platform/monitoring.md#監視している項目)が正である。信頼性の面では、次の表にある「監視の盲点」を塞ぐ仕組みが重要になる。

| 盲点 | 対策 |
| --- | --- |
| 収集が止まって、アラートが何も出ない | `PveStorageMetricsStale` / `Missing`、`UnboundProbeStale` / `Missing` |
| 通知経路が壊れている | `Watchdog`（常時 firing）、`AlertmanagerNotificationsFailing` |
| fallback で隠れる障害 | `UnboundProbeFailing`（未キャッシュの名前を Unbound に直接引く） |
| 収集スクリプトの不正な出力 | 変更時は PVE 上で一時ディレクトリに出力して確認する（[監視・アラート](../lld/platform/monitoring.md#収集スクリプトを変更するときの注意)） |
| 監視 VM 自身・ホストの停止 | 外部 Heartbeat で検知（[ADR-0010](../../adr/0010-external-heartbeat.md)） |

## 既知の弱点と対応状況

| 弱点 | 状況 |
| --- | --- |
| コンテナイメージが `latest` | 更新で意図せず挙動が変わる。バージョン固定は未実施 |
| Docker イメージ・OS の更新が手動 | 手順は [運用 Runbook](../../operations/runbooks/02-updates.md#更新手順)。定期実施の仕組みはない |
| NTP の時刻ずれの監視がない | `ntp.nict.jp` / `time.google.com` に同期するが、ずれの検知は未実施 |
| 復旧手順の訓練 | VM 停止と Unbound 障害の検知は実機で確認済み。ホストの再構築は未実施（[災害対策](02-reliability.md)） |

## 障害から得た再発防止

| 障害 | 再発防止 |
| --- | --- |
| [thin pool 枯渇（INC-2026-10-22）](../../operations/incidents/2026-10-22-lvm-thin-exhaustion.md) | `discard` 有効化、`fstrim`、容量アラート、VM 停止アラート、Slack 通知、容量の上限設定 |
| [PVE 管理画面の破損（INC-2026-10-22-b）](../../operations/incidents/2026-10-22-pve-webui-broken-by-ansible-patch.md) | パッチを「判定式の置換」にして冪等化。復旧手順を Runbook に記載 |
| [PVE の NIC 送信停止（INC-2026-10-25）](../../operations/incidents/2026-10-25-nic-hardware-unit-hang.md) | NIC のオフロード（TSO/GSO/GRO）を無効化。外部 Heartbeat（Healthchecks.io）を導入 |
| [vm-omada のメモリ枯渇（INC-2026-11-09）](../../operations/incidents/2026-11-09-omada-memory-exhaustion.md) | VM を 4GB に増設。Omada コンテナに Java ヒープ・MongoDB キャッシュ・`mem_limit` の上限を設定 |

## 目標（暫定）

数値の根拠にできる実測は、まだない。運用しながら見直していく。

| 項目 | 目標 | 根拠 |
| --- | --- | --- |
| 障害の検知 | VM 停止は約 4 分で Slack に通知 | 2026-10-22 の実機テストの結果（[監視・アラート](../lld/platform/monitoring.md#動作確認の記録)） |
| 復旧 | VM 単体の障害は、気づいてから数分〜数十分で復旧 | INC-2026-10-22 の復旧実績（pool 拡張から VM 再開まで約 10 秒） |
| 稼働率 | 目標を置かない | 単一ホスト・UPS なしで、約束できる根拠がない |

## 受け入れたリスクと再検討の条件

| リスク | 判断 | 再検討の条件 |
| --- | --- | --- |
| ホスト・監視 VM の停止が Slack に通知されない | 外部 Heartbeat で補完している（[ADR-0010](../../adr/0010-external-heartbeat.md)、旧判断は [ADR-0002](../../adr/0002-no-external-monitoring.md)） | Healthchecks.io の無料枠の条件が変わったとき |
| 停電でホストが止まる | 受け入れ（UPS 未導入） | ロードマップの「UPS 導入と自動シャットダウン」に着手するとき |
| `vm-infra` への集中 | 受け入れ | DNS を別ホスト（Raspberry Pi など）に分けるとき。VLAN 化で影響範囲がさらに広がる（[第5章 ネットワーク](05-network.md#前提と制約)） |

## 災害対策

ここでは、ホストの故障、ストレージの破損、設備の喪失（火災や盗難など）、運用者の端末の紛失といった**大きな障害から、環境を取り戻す**ための方針と手順を整理する。VM 単体の障害への対応は、[運用 Runbook](../../operations/runbooks/11-troubleshooting.md#障害時切り分け)で説明している。

### 災害対策の方針

- **VM のバックアップは取らず、コードから再構築する。** 判断と理由は、[ADR-0001](../../adr/0001-no-vm-backup.md)（2026-10-22）に書いている。
- 守る対象は、**再構築できないもの**である（age 秘密鍵、SSH 鍵、Terraform の state、各サービスのアカウント）。
- 復旧の目標は、サービスを完全に再現することではなく、**基盤（DNS、リバースプロキシ、監視）を再構築できること**に置く。

### 想定する災害

| 災害 | 失うもの | 復旧の方針 |
| --- | --- | --- |
| NVMe の故障・thin pool の破損 | 全 VM、全データ | 再構築（新しいディスクに Proxmox を入れ直す） |
| ホストの故障（NVMe は無事） | 一時的に全サービス | ホストを交換し、ディスクを移すか再構築する |
| 設備の喪失（火災・盗難・水害） | ホストと LAN 機器すべて | 新しいハードウェアで再構築。構成は GitHub から取り戻す |
| 運用者の Mac の紛失・故障 | age 秘密鍵、SSH 鍵、Terraform の state（Mac 上にあるもの） | iCloud Keychain と非公開の台帳から復元 |
| 外部アカウントの喪失 | Cloudflare、Tailscale、Slack | 各サービスで再取得し、SOPS の値を更新する |
| 誤操作・誤設定（`terraform destroy` など） | 対象の VM | 再構築。`destroy` は `Makefile` にあるため、実行前に対象を確認する |

### バックアップの状況

| 対象 | 取得方法 | 保管先 | 状況 |
| --- | --- | --- | --- |
| 構成（コード） | Git | GitHub | 取得済み（push するたびに） |
| 機密値 | SOPS 暗号文として Git | GitHub | 取得済み。復号には age 秘密鍵が必要 |
| age 秘密鍵 | 手動 | iCloud Keychain | 取得済み |
| SSH 鍵、Terraform の state、証明書など Git に入らないもの | 手動 | 非公開の台帳（`private/secrets-inventory.md`。実体は iCloud Drive、Git 管理外） | 台帳で管理 |
| VM のディスク | **なし** | — | 取得しない（方針による） |
| Prometheus / Grafana / AdGuard のデータ | **なし** | — | 取得しない。履歴は失ってよい |
| Home Assistant の設定（YAML） | Git（`make ha-config-pull`） | GitHub | 取得済み。画面で編集したら取り込む必要がある（[ADR-0011](../../adr/0011-home-assistant-on-vm-apps.md)） |
| Home Assistant の登録情報・履歴（`.storage/`、DB） | **なし** | — | 取得しない。統合を入れ直す（[復旧](../lld/apps/home-assistant.md#復旧)） |
| n8n のワークフロー（JSON） | Git（`make n8n-workflows-pull`） | GitHub | 取得済み。画面で作ったら取り込む必要がある（[ADR-0012](../../adr/0012-n8n-on-vm-apps.md)） |
| FreshRSS の購読リスト（OPML） | iCloud Drive（`make freshrss-opml-pull`） | iCloud | 取得済み。フィードを足したら取り込む必要がある。Git には入れない（[ADR-0014](../../adr/0014-freshrss-on-vm-apps.md)） |
| FreshRSS のユーザー・既読・スター・記事（`/opt/freshrss/data`） | **なし** | — | 取得しない。購読リストを取り込み直す（[復旧](../lld/apps/freshrss.md#復旧)） |
| n8n のユーザー・認証情報・実行履歴（`/opt/n8n/data`） | **なし** | — | 取得しない。認証情報を入れ直す（[復旧](../lld/apps/n8n.md#復旧)）。暗号鍵は SOPS にある |
| PVE ホストの設定 | **なし** | — | `ansible/roles/proxmox/` で再現できる範囲のみ。ストレージ設定などは手作業 |

バックアップの方針を再検討する条件は、[ADR-0001](../../adr/0001-no-vm-backup.md#影響と再検討の条件)に書いてある。その条件に当たったときは、Proxmox Backup Server か `vzdump` を、別のストレージに向けて設定する。これは、ロードマップの「NAS の導入」に当たる（[未着手の項目](../../operations/roadmap/01-backlog.md)）。

### 災害対策の目標（暫定）

| 項目 | 目標 | 備考 |
| --- | --- | --- |
| RPO（失ってよいデータの範囲） | 最後の `git push` まで。VM 内のデータは対象外 | `vm-code` には未 push の作業を置かない |
| RTO（復旧までの時間） | 基盤の再構築を、数時間〜1 日 | 実測していない。ホストの再構築の演習は未実施 |
| 優先順位 | ① `vm-infra`（DNS・Caddy・Tailscale）② `vm-monitoring` ③ `vm-apps` ④ `vm-code` | 起動順序と同じ |

### リポジトリの外にあるもの

ここに挙げるのは、再構築に必要なのに、**Git に入っていない**ものである。実体と所在は、非公開の台帳で管理する（値は、この文書にもチャットにも書かない）。

| 必要なもの | 用途 | 所在 |
| --- | --- | --- |
| age 秘密鍵 | SOPS の復号 | Mac と iCloud Keychain |
| SSH 秘密鍵 | VM への接続 | Mac（`~/.ssh/`） |
| Terraform の state | 既存 VM の引き継ぎ | Mac（`terraform/proxmox/`、Git 管理外）。台帳に記載 |
| Proxmox の root パスワード | ホストの管理 | 非公開の台帳 |
| Cloudflare・Tailscale・Slack のアカウント | 外部サービス | 各サービス。認証情報は運用者が管理 |
| GitHub のアクセス | リポジトリの取得 | 個人アカウント |

### 再構築の手順（ホストを失った場合）

前提として、Mac（または別の端末）で GitHub からクローンでき、age 秘密鍵が使えるものとする。

1. **端末を用意する**: `brew install sops age terraform ansible`、`ansible-galaxy collection install -r ansible/requirements.yml`。age 秘密鍵を `~/Library/Application Support/sops/age/keys.txt` に復元し、`make secrets-check` で確認する（[運用 Runbook](../../operations/runbooks/03-secrets.md#別の-mac-で復元する)）。SSH 鍵も復元する。
2. **Proxmox VE を入れる**: 新しいハードウェアに Proxmox VE 9.x をインストールし、IP を `10.77.10.10`（タグ付きの `vmbr0.10`、VLAN10。[手順書 24](../../operations/runbooks/24-pve-move-to-vmbr0-10.md)）にする。`/etc/hosts` の `pve` の行も同じ IP にする。ストレージは `local-lvm`（thin pool）が使える構成にする。
3. **テンプレートと API トークンを作る**: `terraform/proxmox/README.md` の手順で、cloud-init テンプレート（VMID 9000）と `terraform@pam` の API トークンを作る。トークンの値は `sops terraform/proxmox/secrets.sops.yml` で更新する。
4. **ホストを構成する**: `make setup-proxmox`（収集スクリプト、node_exporter）。
5. **VM を作る**: `terraform init && terraform plan && terraform apply`。state がない場合は新規作成になる（既存の VM が残っていると衝突するため、事前に確認する）。
6. **基盤を構成する**: `make setup-infra`（DNS、Caddy、Tailscale）→ `make setup-monitoring` → `make setup-apps` → `make setup-code`。全体は `make setup`。
7. **Tailscale を再登録する**: `tailscale_authkey` で登録し、管理画面で subnet route（`10.77.20.0/24`、`10.77.40.0/24`）の承認と、`vm-infra` の key expiry 無効化、split DNS の設定を確認する（[DNS 構成](../lld/network/dns.md#tailscale-との連携)）。
8. **確認する**: `dig @10.77.20.10 grafana.lab.kanare.dev`、`https://grafana.lab.kanare.dev`、Prometheus の Targets、Slack のテスト通知（[運用 Runbook](../../operations/runbooks/05-slack-alerts.md#slack-アラート通知)）、外出先（モバイル回線）からの接続。
9. **記録する**: 障害記録を `docs/operations/incidents/` に書く。台帳に変更があれば更新する。

#### 証明書の再取得に関する注意

新しい `vm-infra` の Caddy は、証明書を新しく取得する。Let's Encrypt には、証明書の発行回数に制限がある。再構築を繰り返す場合は、`caddy_data` ボリュームを残しておくか、ステージング環境（テスト用の CA）で試してから、本番に切り替える。

### 部分的な障害の復旧

| 状況 | 手順 |
| --- | --- |
| 1 台の VM が壊れた | VM を削除して `terraform apply`、`make setup-<group>`。`vm-infra` は最後にする |
| thin pool が枯渇した | [運用 Runbook](../../operations/runbooks/12-storage-recovery.md#thin-pool-が-90-を超えたとき)、[障害記録](../../operations/incidents/2026-10-22-lvm-thin-exhaustion.md) |
| PVE の Web UI が壊れた | [運用 Runbook](../../operations/runbooks/13-pve-webui-recovery.md#pve-の管理画面が開かないとき) |
| 通知が届かない（監視 VM が止まっている） | Proxmox の UI で VM の状態を確認する。気づく手段は症状と目視のみ |

### 訓練と未整備の項目

| 項目 | 状況 |
| --- | --- |
| ホスト全体の再構築の演習 | **未実施**。手順は設計時点の想定で、実機で通したことがない |
| age 秘密鍵の復元の確認 | 手順あり（`make secrets-check`）。別の Mac での実施は未確認 |
| オフサイトのバックアップ | なし（構成は GitHub、秘密は iCloud が実質のオフサイト） |
| 停電時の自動シャットダウン | なし（UPS 未導入。ロードマップ） |
| ホストの設定（ストレージ、ネットワーク）の記録 | 手作業の部分が文書化されていない。再構築の演習で洗い出す |

最初の演習としては、**`vm-dev` を削除して、Terraform と Ansible で作り直す**とよい。VM 単位の再構築手順を確かめられる（`vm-dev` は破壊検証用の VM である）。
