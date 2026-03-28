variable "proxmox_api_url" {
  description = "Proxmox API URL"
  type        = string
}

variable "proxmox_api_token_id" {
  description = "Proxmox API token ID (e.g. terraform@pam!terraform-token)"
  type        = string
  sensitive   = true
}

variable "proxmox_api_token_secret" {
  description = "Proxmox API token secret"
  type        = string
  sensitive   = true
}

variable "proxmox_node" {
  description = "Proxmox node name"
  type        = string
  default     = "pve"
}

variable "template_name" {
  description = "Name of the VM template to clone"
  type        = string
  default     = "ubuntu-cloud"
}

variable "ssh_public_key" {
  description = "SSH public key for VM access (default: ~/.ssh/id_ed25519_homelab.pub)"
  type        = string
  default     = null
}

variable "gateway" {
  description = "Default gateway IP"
  type        = string
  default     = "192.168.11.1"
}

variable "nameserver" {
  description = "DNS server IP"
  type        = string
  default     = "192.168.11.11"
}

variable "vms" {
  description = "Map of VMs to create"
  type = map(object({
    vmid    = number
    ip      = string
    cores   = number
    memory  = number
    disk    = string
    tags    = list(string)
    start_at_node_boot = optional(bool, true)
    startup_order      = optional(number, -1)
    startup_delay      = optional(number, 0)
    shutdown_timeout   = optional(number, 60)
  }))
}
