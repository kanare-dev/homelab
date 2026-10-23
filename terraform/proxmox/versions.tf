terraform {
  required_version = ">= 1.5.0"

  required_providers {
    proxmox = {
      source  = "telmate/proxmox"
      version = "3.0.2-rc07"
    }
    sops = {
      source  = "carlpett/sops"
      version = "~> 1.1"
    }
  }
}

# 機密値は secrets.sops.yml（SOPS + age で暗号化）から読む
data "sops_file" "secrets" {
  source_file = "${path.module}/secrets.sops.yml"
}

provider "proxmox" {
  pm_api_url          = var.proxmox_api_url
  pm_api_token_id     = var.proxmox_api_token_id
  pm_api_token_secret = data.sops_file.secrets.data["proxmox_api_token_secret"]
  pm_tls_insecure     = true
}
