proxmox_api_url      = "https://192.168.11.10:8006/api2/json"
proxmox_api_token_id = "terraform@pam!terraform-token"

proxmox_node  = "pve"
template_name = "ubuntu-cloud"

# ssh_public_key を省略すると ~/.ssh/id_ed25519_homelab.pub を読み込む
# ssh_public_key = "ssh-ed25519 AAAAC3... user@host"

vms = {
  # DNS・リバースプロキシ: 最初に起動、最後にシャットダウン
  "vm-infra" = {
    vmid               = 111
    ip                 = "10.77.20.10/24"
    gateway            = "10.77.20.1"
    nameserver         = "10.77.20.1"
    vlan_id            = 20
    cores              = 2
    memory             = 1536
    disk               = "20G"
    tags               = ["infra", "dns", "proxy"]
    start_at_node_boot = true
    startup_order      = 1
    startup_delay      = 30
    shutdown_timeout   = 60
  }
  # モニタリング: DNS 起動後に起動
  "vm-monitoring" = {
    vmid               = 113
    ip                 = "10.77.20.11/24"
    gateway            = "10.77.20.1"
    nameserver         = "10.77.20.1"
    vlan_id            = 20
    cores              = 2
    memory             = 2048
    disk               = "40G"
    tags               = ["monitoring", "prometheus", "grafana"]
    start_at_node_boot = true
    startup_order      = 2
    startup_delay      = 20
    shutdown_timeout   = 60
  }
  # アプリ: モニタリング起動後に起動
  "vm-apps" = {
    vmid               = 120
    ip                 = "10.77.20.20/24"
    gateway            = "10.77.20.1"
    nameserver         = "10.77.20.1"
    vlan_id            = 20
    cores              = 2
    memory             = 4096
    disk               = "40G"
    tags               = ["apps"]
    start_at_node_boot = true
    startup_order      = 3
    startup_delay      = 20
    shutdown_timeout   = 60
  }
  # 開発用: 手動起動のみ（start_at_node_boot = false）
  "vm-dev" = {
    vmid               = 121
    ip                 = "10.77.40.10/24"
    gateway            = "10.77.40.1"
    nameserver         = "10.77.40.1"
    vlan_id            = 40
    cores              = 2
    memory             = 1024
    disk               = "10G"
    tags               = ["dev", "playground"]
    start_at_node_boot = false
    startup_order      = 4
    startup_delay      = 10
    shutdown_timeout   = 30
  }
  # 常用リモート開発環境: Claude Code / code-server。常時起動、Tailscale経由のみアクセス
  "vm-code" = {
    vmid               = 122
    ip                 = "10.77.20.30/24"
    gateway            = "10.77.20.1"
    nameserver         = "10.77.20.1"
    vlan_id            = 20
    cores              = 2
    memory             = 4096
    disk               = "30G"
    tags               = ["code", "dev"]
    start_at_node_boot = true
    startup_order      = 5
    startup_delay      = 10
    shutdown_timeout   = 30
  }
  # Omada コントローラー（ER605・SG2210P・将来の AP を管理）: 常時起動。コントローラーが止まっても、機器は設定を持ったまま動き続ける
  "vm-omada" = {
    vmid               = 112
    ip                 = "192.168.11.12/24"
    gateway            = "192.168.11.1"
    nameserver         = "192.168.11.1"
    vlan_id            = null # 段階 3b まで、今の LAN（VLAN1、タグなし）に残す（ADR-0028）
    cores              = 2
    memory             = 4096 # INC-2026-11-09: 3GB で枯渇して固まった
    disk               = "20G"
    tags               = ["omada", "network"]
    start_at_node_boot = true
    startup_order      = 6
    startup_delay      = 10
    shutdown_timeout   = 60 # MongoDB を正常に止める
  }
}
