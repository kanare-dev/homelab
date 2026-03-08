module "vm" {
  source   = "./modules/vm"
  for_each = var.vms

  name        = each.key
  vmid        = each.value.vmid
  target_node = var.proxmox_node
  clone       = var.template_name

  cores  = each.value.cores
  memory = each.value.memory
  disk   = each.value.disk

  ip_address       = each.value.ip
  gateway          = var.gateway
  nameserver       = var.nameserver
  ssh_public_key   = coalesce(var.ssh_public_key, trimspace(file(pathexpand("~/.ssh/id_ed25519_homelab.pub"))))
  tags             = each.value.tags
}
