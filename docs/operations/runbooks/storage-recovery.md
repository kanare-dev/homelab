# thin pool が 90% を超えたとき

1. `lvs -o lv_name,data_percent,metadata_percent pve/data` で現状確認。
2. 各 VM で `sudo fstrim -av`（discard 有効が前提。`qm config <id>` で `discard=on` を確認）。
3. 足りなければ `vgs` で空きを確認し `lvextend -L +<size> pve/data`。VG に空きが無ければディスク追加または VM ディスクの縮小を検討。

詳細は `docs/operations/incidents/2026-10-22-lvm-thin-exhaustion.md` を参照。
