# homelab リポジトリのルール

## シークレット

- 機密値は SOPS + age で暗号化して Git に置く（`*.sops.yml`。詳細は `docs/operations/runbooks/secrets.md`）。復号できるのは age 秘密鍵だけ。
- 新しいシークレットは、`group_vars/<group>/secrets.sops.yml`（Terraform は `terraform/proxmox/secrets.sops.yml`）に追加する。追記はユーザーが `sops <ファイル>` で行い、値をチャットに貼らせない。
- 値は、チャット・コミット・ログ・ドキュメントに書かない。文字数・ハッシュ・一部の文字も書かない（リポジトリは公開）。確認が必要なときは、値を変数に入れて API で検証する。
- 平文のシークレットファイル（`.env` など）を作らない。`sops -d` の出力をファイルに保存しない。age 秘密鍵（`keys.txt`）をリポジトリに入れない。

### 記録と退避

- SOPS 内のシークレットの一覧は `docs/operations/runbooks/secrets.md` の表が正。追加・削除したら表を更新する。
- SOPS の外にあるもの（`*.tfstate`、SSH 鍵、証明書、Proxmox の root パスワードなど）は、非公開の台帳（`private/secrets-inventory.md`。実体は iCloud Drive で、Git 管理外）に追記する。
- iCloud Keychain への登録が必要なのは、age 鍵と、再発行できず SOPS にも入れないものだけ。作業を終える前にユーザーへ促す。値を画面に出さない方法（`pbcopy < file` など）を案内する。

## 運用ドキュメント

- 設計書: `docs/architecture/`（方式設計）、`docs/services/`（サービス別の詳細）。構成を変えたら、該当する設計書を同じ変更で更新する。目次は `docs/architecture/README.md`、`docs/README.md`。
- 設計判断: 重要な判断（方式の選択、リスクの受け入れ、方針の変更）は `docs/adr/` に ADR として残す。書き方は `docs/adr/README.md`。判断を変えるときは新しい ADR を追加し、古い方を「置き換え済み」にする。
- Runbook: 手順は `docs/operations/runbooks/`。
- 構成図: 最新版の ASCII 図を `docs/architecture/overview.md` の冒頭に置く。VM・サービス・IP を変えたら、この図と同じ文書の表を更新する。SVG（`diagrams/drawio/`）は手動で更新するため古くなりうる。更新が必要なことはユーザーに伝える。
- `README.md`: ディレクトリやファイルを追加・削除・改名したら、「リポジトリ構成」を更新する。管理画面リンク、設計書の一覧も同様。細かい設計内容は README に書かず、設計書に書く。
- 監視・アラート: `docs/services/monitoring.md`
- 障害記録: `docs/operations/incidents/`
- 新しい設計書・手順を追加したら、`docs/README.md` と該当ディレクトリの README の一覧も更新する。
- 設定変更で監視や容量に影響する場合は、`docs/services/monitoring.md` の「容量の上限設定」の表も更新する。

## Lint

- push する前に `make lint-all` をローカルで通す（CI の `.github/workflows/lint.yml` と同じチェック）。失敗したまま push しない。
- `make hooks` で pre-push フック（`.githooks/pre-push`）を有効にできる。
