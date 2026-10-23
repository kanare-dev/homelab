# VM のコンソールが「接続しました／切断しました」を繰り返すとき

PVE の noVNC コンソールが接続と切断を高速で繰り返し、画面が出ない場合。

- **原因:** テンプレート（9000）は `vga: serial0` だが、Terraform でクローンした VM には `serial0` デバイスが付かない。表示デバイスが無いので noVNC が切断される。
- **対処:** `terraform/proxmox/modules/vm/main.tf` で `vga { type = "std" }` を指定している。VM を新しく作るときも同じ。
- **確認:** `qm config <vmid> | grep vga` が `vga: type=std` であること。
