# 更新手順

## OS アップデート（全 VM）

```bash
# Ansible で一括実行
cd ansible
ansible all -m apt -a "upgrade=dist update_cache=yes" --become

# 再起動が必要な場合
ansible all -m reboot --become
```

## Docker イメージ更新

```bash
# vm-monitoring 上で
cd /opt/monitoring
docker compose pull
docker compose up -d

# 古いイメージの削除
docker image prune -f
```

## Terraform Provider 更新

```bash
cd terraform/proxmox
terraform init -upgrade
terraform plan   # 差分を確認
```
