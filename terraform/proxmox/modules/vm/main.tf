resource "proxmox_vm_qemu" "vm" {
  name        = var.name
  vmid        = var.vmid
  target_node = var.target_node
  clone       = var.clone
  agent       = 1
  os_type     = "cloud-init"

  cores   = var.cores
  sockets = 1
  memory  = var.memory

  scsihw = "virtio-scsi-single"

  disks {
    scsi {
      scsi0 {
        disk {
          size    = var.disk
          storage = var.storage
        }
      }
    }
  }

  network {
    model  = "virtio"
    bridge = var.bridge
  }

  ipconfig0  = "ip=${var.ip_address},gw=${var.gateway}"
  nameserver = var.nameserver
  sshkeys    = var.ssh_public_key
  tags       = join(",", var.tags)

  lifecycle {
    ignore_changes = [
      network,
    ]
  }
}
