terraform {
  required_providers {
    proxmox = {
      source = "telmate/proxmox"
    }
  }
}

resource "proxmox_vm_qemu" "vm" {
  name        = var.name
  vmid        = var.vmid
  target_node = var.target_node
  clone       = var.clone
  agent       = 0
  os_type     = "cloud-init"

  cpu {
    cores   = var.cores
    sockets = 1
  }
  memory   = var.memory

  scsihw   = "virtio-scsi-single"
  bootdisk = "scsi0"

  disks {
    scsi {
      scsi0 {
        disk {
          size    = var.disk
          storage = var.storage
        }
      }
    }
    ide {
      ide2 {
        cloudinit {
          storage = var.storage
        }
      }
    }
  }

  network {
    id     = 0
    model  = "virtio"
    bridge = var.bridge
  }

  ipconfig0  = "ip=${var.ip_address},gw=${var.gateway}"
  nameserver = var.nameserver
  sshkeys    = trimspace(var.ssh_public_key)
  tags       = join(",", var.tags)

  lifecycle {
    ignore_changes = [
      network,
      startup_shutdown,
    ]
  }
}
