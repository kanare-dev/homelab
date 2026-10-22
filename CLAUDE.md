# homelab リポジトリのルール

## シークレットの扱い（INC-2026-10-22 の再発防止）

Mac が単一障害点になっているため、シークレットを作るたびに退避を促す。台帳は非公開（リポジトリ外。iCloud Drive の `homelab/secrets-inventory.md`）。

次のいずれかが起きたら、**作業を終える前に**ユーザーへ次の 2 点を促すこと。

1. **iCloud Keychain（パスワードアプリ）に登録する**。命名は `homelab / <用途>`（台帳 §4 の規則）。
2. **非公開の台帳（iCloud Drive の `homelab/secrets-inventory.md`）に追記する**（名前・場所・用途・復旧方法。**値は書かない**）。台帳の更新は Claude が行い、Keychain 登録はユーザーが行う。

対象:

- パスワード、API トークン、Webhook URL、認証キー（Tailscale authkey など）、SSH 鍵、証明書を新しく生成・発行・追加したとき
- `ansible-vault` の変数（`vault_*`）を追加したとき（追記は `ansible-vault edit` でユーザーが行う）
- `.gitignore` 対象のローカル専用ファイル（`.env`、`terraform.tfvars`、`*.tfstate`、`vault_password` など）を新しく作ったとき
- 既存シークレットを再発行（ローテーション）したとき

守ること:

- シークレットの値をチャット出力、コミット、ログ、ドキュメントに書かない。確認が必要なときは、値を変数に入れて API で検証する（値は表示しない）。**文字数・ハッシュ・一部の文字も、リポジトリのファイルには書かない**（このリポジトリは公開）。
- 値を Keychain に入れる手順は、画面に値を出さない方法（`pbcopy < file` など）を案内する。
- 新しいシークレットを `vault.yml` に追加するときは `ansible-vault edit` を案内する（Claude は Vault のパスワードを知らない）。

## 運用ドキュメント

- 監視・アラート: `docs/monitoring.md`
- 障害記録: `docs/incidents/`
- 設定変更で監視や容量に影響する場合は、`docs/monitoring.md` の「容量の上限設定」の表も更新する。
