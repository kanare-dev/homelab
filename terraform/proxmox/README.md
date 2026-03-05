# Terraform — Proxmox VM プロビジョニング

Proxmox VE 上に VM を作成する Terraform 構成。

## 前提条件

1. Proxmox VE 8.x が稼働中
2. Cloud-init 対応のテンプレート VM を作成済み
3. Terraform 用 API トークンを発行済み

### API トークンの作成手順

Proxmox の Web UI または CLI で以下を実行:

```bash
# Proxmox ホスト上で
pveum user add terraform@pam
pveum aclmod / -user terraform@pam -role PVEVMAdmin
pveum user token add terraform@pam terraform-token --privsep=0
```

発行された Token ID と Secret を `terraform.tfvars` に設定する。

### Cloud-init テンプレートの作成

```bash
# Ubuntu Cloud Image をダウンロード
wget https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img

# VM を作成してテンプレート化
qm create 9000 --name ubuntu-cloud --memory 2048 --cores 2 --net0 virtio,bridge=vmbr0
qm importdisk 9000 jammy-server-cloudimg-amd64.img local-lvm
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0
qm set 9000 --ide2 local-lvm:cloudinit
qm set 9000 --boot c --bootdisk scsi0
qm set 9000 --serial0 socket --vga serial0
qm set 9000 --agent enabled=1
qm template 9000
```

## 使い方

```bash
# 初期化
terraform init

# tfvars を準備
cp terraform.tfvars.example terraform.tfvars
# terraform.tfvars を編集

# 差分確認
terraform plan

# 適用
terraform apply

# 削除
terraform destroy
```

## ファイル構成

| ファイル | 内容 |
|---|---|
| `versions.tf` | Provider 設定・バージョン制約 |
| `variables.tf` | 入力変数定義 |
| `main.tf` | VM モジュール呼び出し |
| `outputs.tf` | 出力値 |
| `terraform.tfvars.example` | 変数値のサンプル |
| `modules/vm/` | VM リソース定義モジュール |
