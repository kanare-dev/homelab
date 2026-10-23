# homelab リポジトリのルール

## シークレットの扱い（INC-2026-10-22 の再発防止）

機密値は SOPS + age で暗号化して Git に置く（`*.sops.yml`。詳細は `docs/runbook.md` の「秘密情報管理」）。復号できるのは **age 秘密鍵だけ**で、Mac が単一障害点になるため、鍵の退避を最優先で守る。台帳は非公開（実体は iCloud Drive の `homelab/secrets-inventory.md`。リポジトリ内の `private/secrets-inventory.md` はそこへのシンボリックリンクで、Git 管理外）。

次のいずれかが起きたら、**作業を終える前に**ユーザーへ促し、台帳を更新すること。

- **age 鍵を新しく生成・ローテーションしたとき**: ユーザーに iCloud Keychain（パスワードアプリ）への登録を促す（`homelab / sops age key`。命名は台帳 §4 の規則）。台帳も更新する。
- **シークレットを `*.sops.yml` に追加・再発行したとき**: 台帳に追記する（名前・場所・用途・復旧方法。**値は書かない**）。Keychain への個別登録は不要（age 鍵があれば復元できる）。追記はユーザーが `sops <ファイル>` で行う（値をチャットに貼らせない）。
- **SOPS に入れない Git 管理外のものを新しく作ったとき**: `*.tfstate`、SSH 鍵、証明書、Proxmox の root パスワードなど。台帳に追記し、再発行できないものは Keychain 登録を促す。

守ること:

- シークレットの値をチャット出力、コミット、ログ、ドキュメントに書かない。確認が必要なときは、値を変数に入れて API で検証する（値は表示しない）。**文字数・ハッシュ・一部の文字も、リポジトリのファイルには書かない**（このリポジトリは公開）。
- 平文のシークレットファイル（`.env` など）を新しく作らない。`sops -d` の出力をファイルに保存しない。
- age 秘密鍵（`keys.txt`）をリポジトリに入れない。値を Keychain に入れる手順は、画面に値を出さない方法（`pbcopy < file` など）を案内する。
- 新しいシークレットは、対応する `group_vars/<group>/secrets.sops.yml`（Terraform は `terraform/proxmox/secrets.sops.yml`）に追加する。Ansible では `.env.j2` などのテンプレートから参照する。

## 運用ドキュメント

- 監視・アラート: `docs/monitoring.md`
- 障害記録: `docs/incidents/`
- 設定変更で監視や容量に影響する場合は、`docs/monitoring.md` の「容量の上限設定」の表も更新する。
