#!/usr/bin/env bash
# LVM thin pool と VM の io-error 状態を node_exporter の textfile collector 形式で出力する。
# INC-2026-10-22: thin pool 枯渇を検知できなかったため追加。systemd timer から 1 分間隔で実行する。
set -euo pipefail

OUT_DIR="${1:-/var/lib/node_exporter/textfile}"
OUT="${OUT_DIR}/pve_storage.prom"
TMP="$(mktemp "${OUT_DIR}/.pve_storage.XXXXXX")"
trap 'rm -f "$TMP"' EXIT

{
  echo "# HELP lvm_thin_pool_data_percent Data usage of the LVM thin pool in percent."
  echo "# TYPE lvm_thin_pool_data_percent gauge"
  echo "# HELP lvm_thin_pool_metadata_percent Metadata usage of the LVM thin pool in percent."
  echo "# TYPE lvm_thin_pool_metadata_percent gauge"
  echo "# HELP lvm_thin_pool_size_bytes Size of the LVM thin pool."
  echo "# TYPE lvm_thin_pool_size_bytes gauge"
  echo "# HELP lvm_thin_pool_provisioned_bytes Sum of virtual sizes of thin volumes in the pool."
  echo "# TYPE lvm_thin_pool_provisioned_bytes gauge"
  echo "# HELP lvm_thin_volume_data_percent Allocated percentage of a thin volume (VM disk)."
  echo "# TYPE lvm_thin_volume_data_percent gauge"
  echo "# HELP lvm_thin_volume_size_bytes Virtual size of a thin volume (VM disk)."
  echo "# TYPE lvm_thin_volume_size_bytes gauge"

  # lv_attr 先頭が 't' が thin pool、'V' が thin volume
  lvs --noheadings --nosuffix --units b --separator '|' \
      -o vg_name,lv_name,lv_size,data_percent,metadata_percent,pool_lv,lv_attr 2>/dev/null |
    awk -F'|' '
      { for (i = 1; i <= NF; i++) gsub(/^ +| +$/, "", $i) }
      substr($7,1,1) == "t" {
        pool[$1 "/" $2] = 1
        printf "lvm_thin_pool_data_percent{vg=\"%s\",pool=\"%s\"} %s\n", $1, $2, $4
        printf "lvm_thin_pool_metadata_percent{vg=\"%s\",pool=\"%s\"} %s\n", $1, $2, $5
        printf "lvm_thin_pool_size_bytes{vg=\"%s\",pool=\"%s\"} %s\n", $1, $2, $3
      }
      substr($7,1,1) == "V" && $6 != "" {
        prov[$1 "/" $6] += $3
        # 非アクティブなボリューム（テンプレート等）は使用率が空欄。空の値は textfile のパースエラーになるため出力しない
        if ($4 == "") next
        printf "lvm_thin_volume_data_percent{vg=\"%s\",pool=\"%s\",lv=\"%s\"} %s\n", $1, $6, $2, $4
        printf "lvm_thin_volume_size_bytes{vg=\"%s\",pool=\"%s\",lv=\"%s\"} %s\n", $1, $6, $2, $3
      }
      END {
        for (k in prov) {
          split(k, a, "/")
          printf "lvm_thin_pool_provisioned_bytes{vg=\"%s\",pool=\"%s\"} %d\n", a[1], a[2], prov[k]
        }
      }'

  echo "# HELP pve_vm_io_error 1 if the VM is paused by QEMU with io-error."
  echo "# TYPE pve_vm_io_error gauge"
  echo "# HELP pve_vm_running 1 if the VM is running. onboot label is the VM's onboot setting."
  echo "# TYPE pve_vm_running gauge"
  # テンプレート VM は対象外。停止中の VM も出力して「止まっている」ことを検知できるようにする
  qm list 2>/dev/null | awk 'NR > 1 { print $1, $2, $3 }' |
    while read -r vmid name status; do
      cfg="$(qm config "$vmid" 2>/dev/null || true)"
      if grep -q '^template: 1' <<<"$cfg"; then continue; fi
      onboot="$(awk '/^onboot:/ { print $2 }' <<<"$cfg")"
      [ "$onboot" = "1" ] || onboot=0
      if [ "$status" = "running" ]; then running=1; else running=0; fi
      printf 'pve_vm_running{vmid="%s",name="%s",onboot="%s"} %s\n' "$vmid" "$name" "$onboot" "$running"
      if [ "$running" = 1 ]; then
        state="$(qm status "$vmid" --verbose 2>/dev/null | awk '/^qmpstatus:/ { print $2 }')"
        if [ "$state" = "io-error" ]; then v=1; else v=0; fi
        printf 'pve_vm_io_error{vmid="%s",name="%s"} %s\n' "$vmid" "$name" "$v"
      fi
    done

  echo "# HELP pve_storage_metrics_last_run_timestamp_seconds Last successful run of this collector."
  echo "# TYPE pve_storage_metrics_last_run_timestamp_seconds gauge"
  echo "pve_storage_metrics_last_run_timestamp_seconds $(date +%s)"
} > "$TMP"

chmod 0644 "$TMP"
mv "$TMP" "$OUT"
trap - EXIT
