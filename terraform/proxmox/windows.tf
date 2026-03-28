resource "proxmox_vm_qemu" "windows" {
  name        = "vm-windows"
  vmid        = 130
  target_node = var.proxmox_node

  # Windows 11 requires UEFI + q35 machine type
  bios    = "ovmf"
  machine = "pc-q35-9.2"
  os_type = "win11"

  # TPM 2.0 (required for Windows 11)
  tpm_state {
    storage = "local-lvm"
    version = "v2.0"
  }

  cpu {
    cores   = 4
    sockets = 1
    type    = "host"
  }
  memory = 8192

  scsihw = "virtio-scsi-single"

  # NOTE: EFI disk cannot be managed by this provider version.
  # After terraform apply, add manually via Proxmox UI:
  #   VM → Hardware → Add → EFI Disk → Storage: local-lvm, Pre-Enroll keys: off

  disks {
    # Main Windows system disk
    scsi {
      scsi0 {
        disk {
          size    = "60G"
          storage = "local-lvm"
        }
      }
    }

    # Windows 11 ISO + VirtIO drivers ISO (detach after OS install)
    ide {
      ide0 {
        cdrom {
          iso = "local:iso/Win11_25H2_Japanese_x64_v2.iso"
        }
      }
      ide1 {
        cdrom {
          iso = "local:iso/virtio-win-0.1.285.iso"
        }
      }
    }
  }

  network {
    id     = 0
    model  = "virtio"
    bridge = "vmbr0"
  }

  # QEMU guest agent
  agent = 1

  start_at_node_boot = false

  tags = "windows,desktop"

  lifecycle {
    # Ignore disk changes after OS install (ISOs will be detached manually)
    ignore_changes = [
      network,
      disks,
    ]
  }
}

output "windows_vm_id" {
  value = proxmox_vm_qemu.windows.id
}
