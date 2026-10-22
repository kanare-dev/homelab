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
          size       = "60G"
          storage    = "local-lvm"
          discard    = true # INC-2026-10-22: thin pool 回収用
          emulatessd = true
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

  # 普段は停止しておく（8GB の RAM を使うため）。使うときは UI か qm start で起動する
  # 起動したまま terraform apply すると停止されるので注意
  vm_state = "stopped"

  # 起動順序・遅延は指定なし（-1）。実機の設定と一致させ、差分を出さない
  startup_shutdown {
    order            = -1
    startup_delay    = -1
    shutdown_timeout = -1
  }

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
