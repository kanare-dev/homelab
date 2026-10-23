# 秘密情報管理

機密値は **SOPS + age** で暗号化して Git で管理する（このリポジトリは公開だが、暗号文のみを置く）。復号できる鍵は age 秘密鍵 1 つで、Mac にだけある。

## 暗号化しているファイル

値だけが暗号化され、キー名は平文で読める。シークレットを追加・削除したら、この表も更新する（非公開の台帳には書かない）。

| ファイル | キー | 使い道 |
| --- | --- | --- |
| `ansible/inventory/group_vars/code/secrets.sops.yml` | `code_server_password` | code-server のログイン |
| `ansible/inventory/group_vars/infra/secrets.sops.yml` | `cloudflare_api_token`, `tailscale_authkey` | Caddy の DNS-01、Tailscale 登録 |
| `ansible/inventory/group_vars/monitoring/secrets.sops.yml` | `grafana_admin_password`, `slack_webhook_url` | Grafana、Alertmanager |
| `ansible/inventory/group_vars/apps/secrets.sops.yml` | `homepage_proxmox_token`, `homepage_adguard_password` | Homepage のウィジェット |
| `terraform/proxmox/secrets.sops.yml` | `proxmox_api_token_secret` | Terraform の Proxmox 認証 |

仕組み:

- **Ansible**: `community.sops` の vars プラグイン（`ansible.cfg` で有効化）が `group_vars/*/secrets.sops.yml` を実行時に復号し、通常の変数として使う。VM 上の `.env` はテンプレート（`ansible/playbooks/templates/*.env.j2`）から生成する。
- **Terraform**: `versions.tf` の `data "sops_file"`（`carlpett/sops` プロバイダー）が `secrets.sops.yml` を読む。
- 暗号化の対象と宛先の公開鍵は、リポジトリ直下の `.sops.yaml` で決まる（`*.sops.yml` / `*.sops.yaml`）。

## age 秘密鍵

| 項目 | 内容 |
| --- | --- |
| 場所（macOS） | `~/Library/Application Support/sops/age/keys.txt`（SOPS が自動で探す場所。環境変数は不要） |
| 公開鍵 | `.sops.yaml` に記載（公開してよい） |
| 退避先 | iCloud Keychain `homelab / sops age key` |
| 権限 | `chmod 600`。リポジトリには絶対に入れない |

## 日常の操作

```bash
# 事前準備（初回のみ）
brew install sops age
ansible-galaxy collection install -r ansible/requirements.yml

# 編集（復号 → $EDITOR → 再暗号化。平文ファイルは残らない）
sops ansible/inventory/group_vars/monitoring/secrets.sops.yml

# 新しいシークレットを追加する: 上のコマンドで開いて `キー: 値` を追記する
# 新しい group_vars ディレクトリに作る場合も、ファイル名を secrets.sops.yml にすれば .sops.yaml が自動で適用される
sops ansible/inventory/group_vars/<group>/secrets.sops.yml

# 全ファイルが復号できるか確認する（値は表示しない）
make secrets-check
```

値を画面に出さずに使う例:

```bash
# Cloudflare API トークンが有効か確認する
curl -s -H "Authorization: Bearer $(sops -d --extract '["cloudflare_api_token"]' ansible/inventory/group_vars/infra/secrets.sops.yml)" \
  "https://api.cloudflare.com/client/v4/zones?name=kanare.dev" | jq '.success'
```

## 別の Mac で復元する

1. `brew install sops age` と `ansible-galaxy collection install -r ansible/requirements.yml` を実行する。
2. iCloud Keychain の `homelab / sops age key` の値を、`~/Library/Application Support/sops/age/keys.txt` に保存する（`chmod 600`）。
3. `make secrets-check` が成功すれば復元完了。

## 鍵をローテーションする

1. `age-keygen -o <新しい鍵ファイル>` で新しい鍵を作り、`.sops.yaml` の公開鍵を差し替える。
2. 全ての `*.sops.yml` で `sops updatekeys -y <ファイル>` を実行する。
3. 旧鍵が漏れた場合は、Git 履歴に旧鍵で復号できる暗号文が残る。**各シークレット自体も再発行する。**
