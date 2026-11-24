# terraform apply が VM を再起動するとき

`vga` など一部の設定の変更は、`terraform apply` が**対象の VM を自動で再起動する**。対象が複数だと、ほぼ同時に再起動する（2026-10-22 は 5 台が約 26 秒の間に再起動し、DNS と監視が 1 分弱止まった）。

- apply の前に `terraform plan` で、変更が VM の再起動を伴うか確認する。
- 再起動を伴う場合は、`-target='module.vm["<名前>"]'` で 1 台ずつ apply する。DNS の `vm-infra` は最後にする。

## apply のあとに `ubuntu` がロックされる

`ipconfig0`、`nameserver`、`sshkeys` など、cloud-init ドライブに入る設定を `terraform apply` で変えると、Proxmox がドライブを作り直す。cloud-init は、これを新しいインスタンスとみなして初回起動の処理をやり直し、既定ユーザー `ubuntu` をもう一度ロックする。ハッシュは消えず、先頭に `!` が付くだけなので、`sudo passwd -S ubuntu` は `L` を返し、コンソールからパスワードで入れなくなる。SSH は鍵認証なので、影響を受けない。

2026-11 に、全 VM で `L` になっているのを確認した（`/etc/shadow` の先頭 3 文字は `!$6`）。原因は、10/31 のパスワード設定のあとに流した `terraform apply` と推測している。どの apply かは特定していない。

apply で cloud-init の設定が変わったら、あとで `ansible/` から `ansible-playbook playbooks/site.yml` を流す。`common` ロールが `password_lock: false` で、ロックを外す。確認は、各 VM で `sudo passwd -S ubuntu` を実行し、`P` が返ることを見る。

Ansible を流せないときは、SSH で VM に入り、`sudo usermod -U ubuntu` を実行すれば、ロックだけを外せる。SSH も使えない場合は、パスワードでコンソールに入れないので、ホストから VM のディスクを開いて直す。
