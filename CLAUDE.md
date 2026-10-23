# homelab リポジトリのルール

## シークレット

- 機密値は SOPS + age で暗号化して Git に置く（`*.sops.yml`。詳細は `docs/runbook.md` の「秘密情報管理」）。復号できるのは age 秘密鍵だけ。
- 新しいシークレットは、`group_vars/<group>/secrets.sops.yml`（Terraform は `terraform/proxmox/secrets.sops.yml`）に追加する。追記はユーザーが `sops <ファイル>` で行い、値をチャットに貼らせない。
- 値は、チャット・コミット・ログ・ドキュメントに書かない。文字数・ハッシュ・一部の文字も書かない（リポジトリは公開）。確認が必要なときは、値を変数に入れて API で検証する。
- 平文のシークレットファイル（`.env` など）を作らない。`sops -d` の出力をファイルに保存しない。age 秘密鍵（`keys.txt`）をリポジトリに入れない。

### 記録と退避

- SOPS 内のシークレットの一覧は `docs/runbook.md` の表が正。追加・削除したら表を更新する。
- SOPS の外にあるもの（`*.tfstate`、SSH 鍵、証明書、Proxmox の root パスワードなど）は、非公開の台帳（`private/secrets-inventory.md`。実体は iCloud Drive で、Git 管理外）に追記する。
- iCloud Keychain への登録が必要なのは、age 鍵と、再発行できず SOPS にも入れないものだけ。作業を終える前にユーザーへ促す。値を画面に出さない方法（`pbcopy < file` など）を案内する。

## 運用ドキュメント

- 設計書: `docs/README.md`（10 の観点で整理。構成を変えたら該当する文書も更新する）
- 監視・アラート: `docs/basic-design/05_operations-maintainability/monitoring.md`
- 障害記録: `docs/incidents/`
- 設定変更で監視や容量に影響する場合は、`docs/basic-design/05_operations-maintainability/monitoring.md` の「容量の上限設定」の表も更新する。

## Lint

- push する前に `make lint-all` をローカルで通す（CI の `.github/workflows/lint.yml` と同じチェック）。失敗したまま push しない。
- `make hooks` で pre-push フック（`.githooks/pre-push`）を有効にできる。
