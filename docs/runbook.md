# 運用 Runbook

homelab の日常運用・障害対応・バックアップに関する手順書。

## VM 自動起動・停止

### 概要

Proxmox の `onboot` および `startup` 設定で、ホスト起動・停止時の VM 制御を自動化している。
設定は Terraform で管理し、`terraform/proxmox/terraform.tfvars` の `onboot` / `startup` フィールドで定義する。

### 起動順序

ホスト (Proxmox) 起動時、以下の順で VM が自動起動する。依存関係（DNS → モニタリング → アプリ）に従った順序。

| 順序 | VM | onboot | startup | 役割 |
|------|----|----|---------|------|
| 1 | vm-infra | true | `order=1,up=30,down=60` | DNS・リバースプロキシ（他 VM が依存） |
| 2 | vm-monitoring | true | `order=2,up=20,down=60` | Prometheus・Grafana |
| 3 | vm-apps | true | `order=3,up=20,down=60` | Homepage ダッシュボード |
| 4 | vm-dev | false | `order=4,up=10,down=30` | 開発用（手動起動のみ） |

`up` は次の VM を起動するまでの待機秒数。`down` はシャットダウン信号送信後の最大待機秒数。

### シャットダウン順序

ホストのシャットダウン時は `order` の**逆順**で ACPI シャットダウン信号が送られる（vm-apps → vm-monitoring → vm-infra）。

### 設定の反映

```bash
# Terraform で設定を適用（vm-infra の例）
cd terraform/proxmox
terraform plan   # 差分確認（onboot / startup の変更が表示される）
terraform apply
```

### 手動での VM 起動・停止

```bash
# 個別起動（Proxmox ホスト上）
ssh root@192.168.11.10 "qm start <vmid>"

# 個別停止（ACPI シャットダウン）
ssh root@192.168.11.10 "qm shutdown <vmid>"

# 全 VM を起動順に一括起動
for vmid in 111 113 120; do
  ssh root@192.168.11.10 "qm start $vmid"
  sleep 30
done
```

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

`vm-infra` 上の Caddy（Docker Compose）が Cloudflare DNS-01 チャレンジで Let's Encrypt 証明書を取得し、各サービスへのリバースプロキシを担う。

- 証明書はドメインごとに個別取得（`*.lab.kanare.dev` ワイルドカードではなく各 FQDN）
- クライアント側の設定不要。全デバイスからブラウザ警告なしにアクセス可能
- `CLOUDFLARE_API_TOKEN` 環境変数（`.env`）で Cloudflare API を認証

| サービス | URL |
| --- | --- |
| Proxmox | <https://pve.lab.kanare.dev> |
| Grafana | <https://grafana.lab.kanare.dev> |
| Prometheus | <https://prometheus.lab.kanare.dev> |

設定ファイル: `docker/compose/reverse-proxy/Caddyfile`

### 証明書の状態確認

```bash
# Caddy のログで証明書取得状況を確認
ssh ubuntu@192.168.11.11 "cd /opt/reverse-proxy && docker compose logs caddy | grep -i tls"

# 証明書の有効期限を確認（例: grafana）
echo | openssl s_client -connect grafana.lab.kanare.dev:443 2>/dev/null \
  | openssl x509 -noout -dates
```

### 証明書の更新

Caddy は自動で更新するため通常は手動操作不要。
更新に失敗している場合は以下を確認する。

```bash
# Caddy コンテナの再起動（更新を強制トリガー）
ssh ubuntu@192.168.11.11 "cd /opt/reverse-proxy && docker compose restart caddy"

# Cloudflare API トークンが有効か確認（.env が正しいか）
ssh ubuntu@192.168.11.11 "cat /opt/reverse-proxy/.env"
```

### 新しいサービスを追加する

`docker/compose/reverse-proxy/Caddyfile` に以下のブロックを追記し、Caddy を再起動する。

```
newservice.lab.kanare.dev {
	reverse_proxy 192.168.11.XX:PORT
	tls {
		dns cloudflare {env.CLOUDFLARE_API_TOKEN}
		resolvers 1.1.1.1
	}
}
```

```bash
ssh ubuntu@192.168.11.11 "cd /opt/reverse-proxy && docker compose up -d --force-recreate caddy"
```

### Proxmox へのリバースプロキシについて

Proxmox のバックエンドは自己署名証明書のため、Caddyfile で `tls_insecure_skip_verify` を設定している。
これは LAN 内のみでのアクセスかつ Proxmox 自体の証明書管理が難しいための措置。
