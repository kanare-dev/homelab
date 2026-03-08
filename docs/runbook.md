# 運用 Runbook

homelab の日常運用・障害対応・バックアップに関する手順書。

## バックアップ

### Proxmox VM バックアップ

Proxmox の組み込みバックアップ機能を使用する。

```bash
# 手動バックアップ（Proxmox ホスト上で実行）
vzdump <vmid> --storage local --compress zstd --mode snapshot

# 例: vm-infra (VMID 111) をバックアップ
vzdump 111 --storage local --compress zstd --mode snapshot
```

自動バックアップは Proxmox Web UI > Datacenter > Backup から設定:
- スケジュール: 毎日 02:00
- 保持: 最新 3 世代
- 圧縮: zstd

### Docker ボリュームバックアップ

```bash
# Prometheus データバックアップ
docker run --rm -v monitoring_prometheus_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/prometheus-backup-$(date +%Y%m%d).tar.gz -C /data .

# Grafana データバックアップ
docker run --rm -v monitoring_grafana_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup-$(date +%Y%m%d).tar.gz -C /data .
```

### 設定ファイルバックアップ

このリポジトリ自体が設定のバックアップ。ただし以下は別途保管:

- `terraform.tfvars`（暗号化して保管）
- Ansible Vault のパスワード
- SSH 秘密鍵
- `.env` ファイル

## 更新手順

### OS アップデート（全 VM）

```bash
# Ansible で一括実行
cd ansible
ansible all -m apt -a "upgrade=dist update_cache=yes" --become

# 再起動が必要な場合
ansible all -m reboot --become
```

### Docker イメージ更新

```bash
# vm-monitoring 上で
cd /opt/monitoring
docker compose pull
docker compose up -d

# 古いイメージの削除
docker image prune -f
```

### Terraform Provider 更新

```bash
cd terraform/proxmox
terraform init -upgrade
terraform plan   # 差分を確認
```

## 障害時切り分け

### VM が応答しない

```
1. ping で疎通確認
   $ ping 192.168.11.XX

2. Proxmox Web UI で VM のステータス確認
   → https://192.168.11.10:8006

3. Proxmox コンソールからログイン
   → Web UI > VM > Console

4. VM を再起動
   $ ssh root@192.168.11.10 "qm reboot <vmid>"

5. VM を強制停止・起動
   $ ssh root@192.168.11.10 "qm stop <vmid> && qm start <vmid>"
```

### サービスが応答しない

```
1. Docker コンテナのステータス確認
   $ docker compose ps

2. ログ確認
   $ docker compose logs --tail=50 <service>

3. コンテナ再起動
   $ docker compose restart <service>

4. コンテナ再作成
   $ docker compose up -d --force-recreate <service>
```

### DNS が引けない

```
1. CoreDNS のステータス確認
   $ ssh ubuntu@192.168.11.11 "systemctl status coredns"

2. CoreDNS のログ確認
   $ ssh ubuntu@192.168.11.11 "journalctl -u coredns --tail=50"

3. 直接クエリして確認
   $ dig @192.168.11.11 grafana.lab.kanare.dev

4. CoreDNS を再起動
   $ ssh ubuntu@192.168.11.11 "sudo systemctl restart coredns"
```

### Prometheus がスクレイプに失敗

```
1. Prometheus の Targets ページを確認
   → http://192.168.11.13:9090/targets

2. ターゲット VM の node_exporter を確認
   $ curl http://192.168.11.XX:9100/metrics

3. ファイアウォール確認
   $ ssh ubuntu@192.168.11.XX "sudo ufw status"

4. node_exporter を再起動
   $ ssh ubuntu@192.168.11.XX "sudo systemctl restart node_exporter"
```

### Grafana にログインできない

```
1. Grafana のステータス確認
   $ docker compose -f /opt/monitoring/docker-compose.yml ps grafana

2. パスワードリセット
   $ docker compose -f /opt/monitoring/docker-compose.yml exec grafana \
       grafana cli admin reset-admin-password <new-password>
```

## 秘密情報管理

### 方針

| 方法 | 用途 | 状態 |
|---|---|---|
| `.env` ファイル | Docker Compose 環境変数 | `.gitignore` で除外 |
| `terraform.tfvars` | Terraform 変数 | `.gitignore` で除外 |
| Ansible Vault | Ansible 変数の暗号化 | Git 管理可能 |
| SOPS + age | 汎用的な暗号化 | Git 管理可能（推奨） |

### SOPS + age の導入手順

```bash
# age 鍵の生成
age-keygen -o ~/.config/sops/age/keys.txt

# 公開鍵を .sops.yaml に設定（リポジトリルート）
# age: age1xxxxxxxxx...

# ファイルを暗号化
sops -e secrets.yml > secrets.enc.yml

# ファイルを復号
sops -d secrets.enc.yml

# 直接編集（復号 → エディタ → 再暗号化）
sops secrets.enc.yml
```

### Ansible Vault の使い方

```bash
# 暗号化
ansible-vault encrypt inventory/group_vars/all.yml

# 復号
ansible-vault decrypt inventory/group_vars/all.yml

# 暗号化したまま playbook 実行
ansible-playbook playbooks/site.yml --ask-vault-pass

# パスワードファイルを使う場合
echo "your-vault-password" > ~/.vault_password
chmod 600 ~/.vault_password
ansible-playbook playbooks/site.yml --vault-password-file ~/.vault_password
```

## LAN 内 TLS

### 現在の構成

Caddy の `tls internal`（ローカル CA）で証明書を自動発行している。
ブラウザはこの CA を信頼していないため、アクセスには以下のいずれかが必要。

### 選択肢

#### A. 各サービスに IP で直接アクセス（一番手軽）

| サービス | URL |
| --- | --- |
| Proxmox | <https://192.168.11.10:8006> |
| Grafana | <http://192.168.11.13:3000> |
| Prometheus | <http://192.168.11.13:9090> |

Proxmox は自己署名証明書のため初回ブラウザ警告が出るが、「続ける」で許可すれば使える。
リバースプロキシを使わないため、追加設定不要。

#### B. ローカル CA を Mac に信頼させる（`tls internal` のまま使う）

Caddy は起動時に独自のローカル CA（認証局）を自動生成し、それで `*.lab.kanare.dev` の証明書を発行する。
ブラウザはこの CA を知らないため「証明書エラー」になる。
解決策は Caddy の CA ルート証明書を Mac のキーチェーンに登録して信頼させること。

`/tmp/caddy-root.crt` は vm-infra 上の Caddy が生成したルート証明書を Mac にコピーしたもの。
Mac のキーチェーンへの登録が完了すれば `/tmp/` のファイルは不要（削除してよい）。

```bash
# Caddy のルート証明書を vm-infra から取得して /tmp に保存
ssh vm-infra "sudo cat /var/lib/caddy/.local/share/caddy/pki/authorities/local/root.crt" > /tmp/caddy-root.crt

# macOS のキーチェーンに登録（これ以降ブラウザが証明書を信頼する）
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain /tmp/caddy-root.crt

# 登録後は不要なので削除
rm /tmp/caddy-root.crt
```

登録されたか確認する場合:

```bash
security find-certificate -c "Caddy" /Library/Keychains/System.keychain
```

> **注意**: Caddy を再インストールしたり vm-infra を作り直したりすると CA が再生成されるため、
> この手順を再度実行する必要がある。

加えて、Proxmox（HTTPS）へのリバースプロキシは Caddy がバックエンドの自己署名証明書を検証できないため、
`infra.yml` の Caddy 設定で upstream を `https://192.168.11.10:8006` に変更し、
Caddyfile テンプレートに TLS 検証スキップの設定が必要。

#### C. Let's Encrypt DNS-01 チャレンジ（正規証明書・推奨）

`kanare.dev` を Cloudflare で管理しているため、Caddy に Cloudflare API トークンを渡すことで
`*.lab.kanare.dev` のワイルドカード証明書をブラウザが信頼する正規の証明書として発行できる。
クライアント側の設定不要で、全デバイスから証明書警告なしにアクセス可能になる。

→ `docs/roadmap.md` の改善ロードマップに記載済み。
