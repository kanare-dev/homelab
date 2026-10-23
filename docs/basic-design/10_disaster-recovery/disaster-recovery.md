# 災害対策

ホストの故障、ストレージの破損、設備の喪失（火災・盗難など）、運用者の端末の紛失といった**大きな障害から、環境を取り戻す**ための方針と手順を整理する。VM 単体の障害の対応は [運用 Runbook](../../runbook.md#障害時切り分け)。

## 方針

- **VM のバックアップは取らず、コードから再構築する。** 理由は [運用 Runbook](../../runbook.md#バックアップ) に記録した決定（2026-10-22）のとおり。
- 守る対象は、**再構築できないもの**（age 秘密鍵、SSH 鍵、Terraform の state、各サービスのアカウント）。
- 復旧の目標は、サービスの完全な再現ではなく、**基盤（DNS・リバースプロキシ・監視）を再構築できること**。

## 想定する災害

| 災害 | 失うもの | 復旧の方針 |
| --- | --- | --- |
| NVMe の故障・thin pool の破損 | 全 VM、全データ | 再構築（新しいディスクに Proxmox を入れ直す） |
| ホストの故障（NVMe は無事） | 一時的に全サービス | ホストを交換し、ディスクを移すか再構築する |
| 設備の喪失（火災・盗難・水害） | ホストと LAN 機器すべて | 新しいハードウェアで再構築。構成は GitHub から取り戻す |
| 運用者の Mac の紛失・故障 | age 秘密鍵、SSH 鍵、Terraform の state（Mac 上にあるもの） | iCloud Keychain と非公開の台帳から復元 |
| 外部アカウントの喪失 | Cloudflare、Tailscale、Slack | 各サービスで再取得し、SOPS の値を更新する |
| 誤操作・誤設定（`terraform destroy` など） | 対象の VM | 再構築。`destroy` は `Makefile` にあるため、実行前に対象を確認する |

## バックアップの状況

| 対象 | 取得方法 | 保管先 | 状況 |
| --- | --- | --- | --- |
| 構成（コード） | Git | GitHub | 取得済み（push するたびに） |
| 機密値 | SOPS 暗号文として Git | GitHub | 取得済み。復号には age 秘密鍵が必要 |
| age 秘密鍵 | 手動 | iCloud Keychain | 取得済み |
| SSH 鍵、Terraform の state、証明書など Git に入らないもの | 手動 | 非公開の台帳（`private/secrets-inventory.md`。実体は iCloud Drive、Git 管理外） | 台帳で管理 |
| VM のディスク | **なし** | — | 取得しない（方針による） |
| Prometheus / Grafana / AdGuard のデータ | **なし** | — | 取得しない。履歴は失ってよい |
| PVE ホストの設定 | **なし** | — | `ansible/roles/proxmox/` で再現できる範囲のみ。ストレージ設定などは手作業 |

**再検討する条件**: NAS や外部ストレージを追加したとき、VM に再現できないデータを置くようになったとき、`vm-windows` を実用に使い始めたとき（[運用 Runbook](../../runbook.md#バックアップ)）。そのときは Proxmox Backup Server か `vzdump` を別ストレージ向けに設定する。ロードマップの「バックアップ自動化」「NAS の導入」に該当する。

## 目標（暫定）

| 項目 | 目標 | 備考 |
| --- | --- | --- |
| RPO（失ってよいデータの範囲） | 最後の `git push` まで。VM 内のデータは対象外 | `vm-code` には未 push の作業を置かない |
| RTO（復旧までの時間） | 基盤の再構築を、数時間〜1 日 | 実測していない。ホストの再構築の演習は未実施 |
| 優先順位 | ① `vm-infra`（DNS・Caddy・Tailscale）② `vm-monitoring` ③ `vm-apps` ④ `vm-code` | 起動順序と同じ |

## リポジトリの外にあるもの

再構築に必要で、**Git に入っていない**もの。実体と所在は非公開の台帳で管理する（値は、この文書にもチャットにも書かない）。

| 必要なもの | 用途 | 所在 |
| --- | --- | --- |
| age 秘密鍵 | SOPS の復号 | Mac と iCloud Keychain |
| SSH 秘密鍵 | VM への接続 | Mac（`~/.ssh/`） |
| Terraform の state | 既存 VM の引き継ぎ | Mac（`terraform/proxmox/`、Git 管理外）。台帳に記載 |
| Proxmox の root パスワード | ホストの管理 | 非公開の台帳 |
| Cloudflare・Tailscale・Slack のアカウント | 外部サービス | 各サービス。認証情報は運用者が管理 |
| GitHub のアクセス | リポジトリの取得 | 個人アカウント |

## 再構築の手順（ホストを失った場合）

前提: Mac（または別の端末）で GitHub からクローンでき、age 秘密鍵が使える。

1. **端末を用意する**: `brew install sops age terraform ansible`、`ansible-galaxy collection install -r ansible/requirements.yml`。age 秘密鍵を `~/Library/Application Support/sops/age/keys.txt` に復元し、`make secrets-check` で確認する（[運用 Runbook](../../runbook.md#別の-mac-で復元する)）。SSH 鍵も復元する。
2. **Proxmox VE を入れる**: 新しいハードウェアに Proxmox VE 8.x をインストールし、IP を `192.168.11.10` にする（LAN の IP 体系は変えない）。ストレージは `local-lvm`（thin pool）が使える構成にする。
3. **テンプレートと API トークンを作る**: `terraform/proxmox/README.md` の手順で、cloud-init テンプレート（VMID 9000）と `terraform@pam` の API トークンを作る。トークンの値は `sops terraform/proxmox/secrets.sops.yml` で更新する。
4. **ホストを構成する**: `make setup-proxmox`（収集スクリプト、node_exporter）。
5. **VM を作る**: `terraform init && terraform plan && terraform apply`。state がない場合は新規作成になる（既存の VM が残っていると衝突するため、事前に確認する）。
6. **基盤を構成する**: `make setup-infra`（DNS、Caddy、Tailscale）→ `make setup-monitoring` → `make setup-apps` → `make setup-code`。全体は `make setup`。
7. **Tailscale を再登録する**: `tailscale_authkey` で登録し、管理画面で subnet route（`192.168.11.0/24`）の承認と、`vm-infra` の key expiry 無効化、split DNS の設定を確認する（[DNS 構成](../07_network/dns.md#tailscale-との連携)）。
8. **確認する**: `dig @192.168.11.11 grafana.lab.kanare.dev`、`https://grafana.lab.kanare.dev`、Prometheus の Targets、Slack のテスト通知（[運用 Runbook](../../runbook.md#slack-アラート通知)）、外出先（モバイル回線）からの接続。
9. **記録する**: 障害記録を `docs/incidents/` に書く。台帳に変更があれば更新する。

### 証明書の再取得に関する注意

新しい `vm-infra` の Caddy は、証明書を新規に取得する。Let's Encrypt には発行回数の制限がある。再構築を繰り返す場合は、`caddy_data` ボリュームを残すか、ステージング環境（テスト用 CA）で試してから本番に切り替える。

## 部分的な障害の復旧

| 状況 | 手順 |
| --- | --- |
| 1 台の VM が壊れた | VM を削除して `terraform apply`、`make setup-<group>`。`vm-infra` は最後にする |
| thin pool が枯渇した | [運用 Runbook](../../runbook.md#thin-pool-が-90-を超えたとき)、[障害記録](../../incidents/2026-10-22-lvm-thin-exhaustion.md) |
| PVE の Web UI が壊れた | [運用 Runbook](../../runbook.md#pve-の管理画面が開かないとき) |
| 通知が届かない（監視 VM が止まっている） | Proxmox の UI で VM の状態を確認する。気づく手段は症状と目視のみ |

## 訓練と未整備の項目

| 項目 | 状況 |
| --- | --- |
| ホスト全体の再構築の演習 | **未実施**。手順は設計時点の想定で、実機で通したことがない |
| age 秘密鍵の復元の確認 | 手順あり（`make secrets-check`）。別の Mac での実施は未確認 |
| オフサイトのバックアップ | なし（構成は GitHub、秘密は iCloud が実質のオフサイト） |
| 停電時の自動シャットダウン | なし（UPS 未導入。ロードマップ） |
| ホストの設定（ストレージ、ネットワーク）の記録 | 手作業の部分が文書化されていない。再構築の演習で洗い出す |

最初の演習として、**`vm-dev` を削除して Terraform と Ansible で作り直す**ことで、VM 単位の再構築手順を確かめられる（`vm-dev` は破壊検証用）。
