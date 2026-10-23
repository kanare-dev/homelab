# terraform apply が VM を再起動するとき

`vga` など一部の設定の変更は、`terraform apply` が**対象の VM を自動で再起動する**。対象が複数だと、ほぼ同時に再起動する（2026-10-22 は 5 台が約 26 秒の間に再起動し、DNS と監視が 1 分弱止まった）。

- apply の前に `terraform plan` で、変更が VM の再起動を伴うか確認する。
- 再起動を伴う場合は、`-target='module.vm["<名前>"]'` で 1 台ずつ apply する。DNS の `vm-infra` は最後にする。
- `vm-windows` は `vm_state = "stopped"` を指定している。起動したまま apply すると停止される。
