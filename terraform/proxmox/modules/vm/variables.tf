variable "name" {
  description = "VM name"
  type        = string
}

variable "vmid" {
  description = "Proxmox VM ID"
  type        = number
}

variable "target_node" {
  description = "Proxmox node to deploy on"
  type        = string
}

variable "clone" {
  description = "Template name to clone from"
  type        = string
}

variable "cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "memory" {
  description = "Memory in MB"
  type        = number
  default     = 2048
}

variable "disk" {
  description = "Disk size (e.g. 20G)"
  type        = string
  default     = "20G"
}

variable "storage" {
  description = "Storage pool name"
  type        = string
  default     = "local-lvm"
}

variable "bridge" {
  description = "Network bridge"
  type        = string
  default     = "vmbr0"
}

variable "ip_address" {
  description = "Static IP with CIDR (e.g. 192.168.11.11/24)"
  type        = string
}

variable "gateway" {
  description = "Gateway IP (the router address on the VM's VLAN)"
  type        = string
}

variable "vlan_id" {
  description = "VLAN ID of the network interface. No default: omitting it is an error. Set null explicitly for an untagged VM (VLAN1)."
  type        = number
  nullable    = true

  validation {
    condition     = var.vlan_id == null ? true : (var.vlan_id >= 2 && var.vlan_id <= 4094)
    error_message = "vlan_id must be null (untagged) or between 2 and 4094."
  }
}

variable "nameserver" {
  description = "DNS server IP"
  type        = string
}

variable "ssh_public_key" {
  description = "SSH public key"
  type        = string
}

variable "tags" {
  description = "Tags for the VM"
  type        = list(string)
  default     = []
}

variable "start_at_node_boot" {
  description = "Start the VM automatically when Proxmox boots"
  type        = bool
  default     = true
}

variable "startup_order" {
  description = "Boot order (-1 = disabled)"
  type        = number
  default     = -1
}

variable "startup_delay" {
  description = "Seconds to wait after start before booting next VM"
  type        = number
  default     = 0
}

variable "shutdown_timeout" {
  description = "Seconds to wait for graceful shutdown"
  type        = number
  default     = 60
}
