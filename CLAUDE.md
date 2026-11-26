# homelab リポジトリのルール

## シークレット

- 機密値は SOPS + age で暗号化して Git に置く（`*.sops.yml`。詳細は `docs/operations/runbooks/03-secrets.md`）。復号できるのは age 秘密鍵だけ。
- 新しいシークレットは、`group_vars/<group>/secrets.sops.yml`（Terraform は `terraform/proxmox/secrets.sops.yml`）に追加する。追記はユーザーが `sops <ファイル>` で行い、値をチャットに貼らせない。
- 値は、チャット・コミット・ログ・ドキュメントに書かない。文字数・ハッシュ・一部の文字も書かない（リポジトリは公開）。確認が必要なときは、値を変数に入れて API で検証する。
- 平文のシークレットファイル（`.env` など）を作らない。`sops -d` の出力をファイルに保存しない。age 秘密鍵（`keys.txt`）をリポジトリに入れない。

### 記録と退避

- SOPS 内のシークレットの一覧は `docs/operations/runbooks/03-secrets.md` の表が正。追加・削除したら表を更新する。
- SOPS の外にあるもの（`*.tfstate`、SSH 鍵、証明書、Proxmox の root パスワードなど）は、非公開の台帳（`private/secrets-inventory.md`。実体は iCloud Drive で、Git 管理外）に追記する。
- iCloud Keychain への登録が必要なのは、age 鍵と、再発行できず SOPS にも入れないものだけ。作業を終える前にユーザーへ促す。値を画面に出さない方法（`pbcopy < file` など）を案内する。

## 運用ドキュメント

- 検討と採用の分け方: 案・選択肢・リスクは、採用前は `docs/operations/roadmap/` に「検討中」と明記して書く。設計書と ADR に書くのは、ユーザーが採用を決めたあと（同じ変更で両方に移す）。会話に出ただけの案を設計書・ADR に書かない。詳細は `docs/README.md` の「文書の運用」。
- ネットワーク機器の設定値: ER605・SG2210P と Omada コントローラーの設定は `docs/architecture/lld/network/omada-controller.md`、Buffalo の設定は `docs/architecture/lld/network/wsr-1800ax4p.md`、ThinkCentre（Proxmox ホスト）の設定は `docs/architecture/lld/platform/proxmox-host.md` を正とする。機器の仕様と公式資料は `docs/architecture/lld/hardware/<型番>.md` に置く。**文書を、いつ更新するかは、変更の種類で分ける**: GUI でしか変えられない設定（Omada）と、壊れると影響が大きい変更（VLAN、ACL、DNS、ルーター）は、**文書が先**（変更後の値を PR で書き、マージしてから、実機を変える。実機で確かめていない項目は「未確認」と明記する）。コードで管理する設定（Terraform、Ansible、AdGuard の設定ファイル、Tailscale の ACL）と、小さく戻しやすい変更は、**同じ変更（同じ PR）**で文書を更新する。どちらも、実施のあと、「確認済み」にして、**予測が外れた点を同じ文書に書き**、変更履歴に 1 行足す。秘密の値と機器の MAC アドレスは書かない（台帳へ）。
- 設計書: 基本設計（HLD）は `docs/architecture/hld/`（第1章 システム構成・環境、第2章 信頼性、第3章 運用・保守、第4章 性能・拡張性、第5章 ネットワーク、第6章 セキュリティ。構成と方式の方針を書く）、詳細設計（LLD）は `docs/architecture/lld/`（サービス別の詳細と、IP アドレス一覧のような具体的な値を書く）。構成を変えたら、該当する設計書を更新する（タイミングは、上の「文書を、いつ更新するか」の分け方に従う）。目次は `docs/architecture/README.md`、`docs/README.md`。
- 設計判断: 重要な判断（方式の選択、リスクの受け入れ、方針の変更）は `docs/adr/` に ADR として残す。書き方は `docs/adr/README.md`。判断を変えるときは新しい ADR を追加し、古い方を「置き換え済み」にする。
- Runbook: 手順は `docs/operations/runbooks/`。
- 構成図: 現状の構成の正は、現状（as-is）の図（`docs/diagrams/as-is-diagram/`）とする。ASCII 図は正として扱わない。VM・サービス・IP を変えたら、as-is の図と、`docs/architecture/hld/01-system.md` の表を更新する。図と文書の記述が食い違っていたら、as-is の図を正として直す。構成図は 2 枚を保つ。**最終形（to-be）の図（`docs/diagrams/to-be-diagram/`）は、目指す姿として、計画・設計（ADR、ロードマップ）が変わったときに更新する。設計を変えるときは、先に to-be を更新して設計する（実機を変える前）。** **現状（as-is）の図（`docs/diagrams/as-is-diagram/`）は、削除せず、常に実機の状態を表し、to-be を追いかける**（実機が to-be に追いつけば、2 枚は、ほぼ同じ形になる）。as-is は、**実機を変えたとき**（IP、VLAN、ポート、VM・サービス。図に出る変更だけ）に、Claude Code が更新する（「to-be と一致したときだけ」にしない。途中の状態が続いても、実機と合わせるため）。コードで管理する変更は同じ PR、GUI だけの変更は、実機を変えたあとの PR で直す。`docs/diagrams/as-is-diagram/make-as-is-diagram.py` の「配置」を直して `python3 docs/diagrams/as-is-diagram/make-as-is-diagram.py --png` を実行し、書き出した PNG（ライトとダーク）で崩れていないか見てから、スクリプトと、書き出した HTML・PNG を一緒にコミットする。to-be も、直したら、同じ手順で書き出して確かめる（アイコン素材 `docs/diagrams/assets/` は Git 管理外。無ければ取得する）。
- `docs/README.md`: ディレクトリやファイルを追加・削除・改名したら、「リポジトリ構成」とディレクトリの表を更新する。`README.md`（リポジトリのトップ）は、最初の画面（ロゴ、説明、バッジ、構成図）を簡潔に保ち、設計書の一覧が変わったら「Documents」の表を更新する。細かい設計内容は README に書かず、設計書に書く。
- 監視・アラート: `docs/architecture/lld/platform/monitoring.md`
- 障害記録: `docs/operations/incidents/`
- サービスカタログ（`docs/homelab-service-catalog.md`）: ツールの導入・削除・見送りの判断、新しい候補が話題に出たとき、計画や検討の状況が変わったときは、同じ変更で表の「状況」（導入済み / 計画中 / 検討中 / 見送り / 未検討）を更新する。表に無いツールは行を追加する。会話に出たサービスは、導入するか分からなくても「未検討」で積極的に追記する（網羅するほどよい）。外したものは「廃止」にして行を残す。根拠は「根拠・備考」の列に、設計書・ADR・ロードマップへのリンクで示す。見送り・廃止の理由と再検討の条件は `docs/operations/roadmap/03-deferred.md` に書く。同じ役割のツールは末尾の「役割別の採用状況」も更新する。
- 新しい設計書・手順を追加したら、`docs/README.md` と該当ディレクトリの README の一覧も更新する。
- 設定変更で監視や容量に影響する場合は、`docs/architecture/lld/platform/monitoring.md` の「容量の上限設定」の表も更新する。

## 日本語ドキュメントの執筆規約

- 技術ドキュメントは、自然で読みやすい日本語の文章で記述する。
- 文体は常体（「だ」・「である」体）に統一する。「です」・「ます」は使わない。
- 名詞や体言止めを連続させず、原則として主語・述語の関係が明確な完全な文を書く。
- 「〜の実施」「〜による実現」「〜の確保」などの抽象的な名詞句を多用せず、誰が何をするのかを動詞で説明する。
- 箇条書きは独立した項目の列挙に限る。処理の流れ、設計意図、理由、仕組みは段落で説明する。
- 箇条書きでも、説明が必要な項目は助詞と述語を備えた文にする。
- 表のセルは、独立した項目の列挙として、体言止めでよい。ただし、「〜の実施」「〜の確保」のような抽象的な名詞句は避け、具体的な語で書く。
- 簡潔さを優先するあまり、助詞、接続詞、必要な説明を省略しない。
- 英語の技術文書を直訳したような不自然な言い回しを避ける。
- 見出しは簡潔でよいが、本文まで見出しのような名詞句にしない。
- 文書を保存する前に読み直し、名詞句の羅列、不自然な体言止め、文脈の飛躍を修正する。
- コード、設定値、コマンド、API名などの技術的な正確性は維持する。

## PR と main への直接 push

- ある程度規模の大きい変更は、ブランチを切って PR を作る。複数のファイルや設計書にまたがる変更、構成や設定値を変える変更、レビューしてから入れたい変更が当たる。「運用ドキュメント」で「文書が先」とした変更も、PR をマージしてから実機を変える。
- 簡単な変更は、PR を作らずに main へ直接 push してよい。誤字の修正、数行の文書の手直し、この CLAUDE.md への小さな追記などが当たる。
- どちらにするか迷ったら、PR を作る。PR は squash でマージし、マージしたブランチは消す。

## Lint

- push する前に `make lint-all` をローカルで通す（CI の `.github/workflows/lint.yml` と同じチェック）。失敗したまま push しない。
- pre-push フック（`.githooks/pre-push`）が `git push` のたびに `make lint-all` を実行する。Claude は push の前に lint を実行するか確認せず、そのまま `git push` する。フックが失敗したら、原因を直してから push し直す。`--no-verify` でフックを飛ばさない。
- フックは `make hooks`（`core.hooksPath` に相対パスの `.githooks` を設定する）で有効にする。リポジトリを移動したあとに絶対パスが残っていると、フックが黙って動かなくなる。`git config --get core.hooksPath` が `.githooks` を返すか確かめる。
- Markdown は `make md-lint`（markdownlint-cli2。ルールは `.markdownlint-cli2.yaml`）と `make md-links`（内部リンク・アンカーの検査）で確認できる。どちらも `make lint-all` に含まれる。
