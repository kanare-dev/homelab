# 0013. 全 VM の `ubuntu` にコンソール用パスワードを設定する

- ステータス: 採用
- 日付: 2026-10-31

## 背景

VM は cloud-init で作っており、`ubuntu` のパスワードはロックされていた。SSH は鍵認証のみ（`PasswordAuthentication no`）で、緊急用のパスワードも設定していなかった（2026-10-22 に見送り）。

運用してみて、次の2つで困った。

- SSH が使えないとき（鍵の紛失、sshd や UFW の設定ミス、ネットワーク設定の誤り）に、Proxmox のコンソールからもログインできない。VM のディスクをホスト側から開くなどの回り道が要る。
- `sudo -v` を使うスクリプトが動かない。vm-code で Homebrew のインストーラが `[sudo] password for ubuntu:` を求めてきた。`ubuntu` には `NOPASSWD:ALL` があるが、標準の `%sudo ALL=(ALL:ALL) ALL` も当たる。`sudo -v` は後者を見るので、パスワードを要求する。

## 決定

- 全 VM（`infra`、`monitoring`、`apps`、`dev`、`code`）の `ubuntu` に、共通のパスワードを設定する。Ansible の `common` ロールで入れる。
- Git に置くのは SHA-512 のハッシュだけ。`ansible/inventory/group_vars/all/secrets.sops.yml` の `vm_user_password_hash` に SOPS で暗号化して入れる。平文は iCloud Keychain `homelab / vm ubuntu password` に退避する。
- SSH のパスワード認証は無効のまま。パスワードを使うのは、Proxmox のコンソールと `sudo -v` だけ。
- `root` はロックしたまま。コンソールで入ったら `sudo -i`（パスワード不要）で昇格する。
- Proxmox ホスト（`pve`）は対象外。root のパスワードは別に管理している。

## 理由

- SSH が壊れたときに、コンソールから入れる。Ansible も SSH も使えない状況では、コンソールが最後の入口になる。
- 平文を Keychain に置く理由は、ハッシュから元に戻せないため。Ansible が使えない障害の最中に、SOPS からは取り出せない。
- 共通にすると、1つ覚えるだけで済む。VM は同じ Mac からしか触らず、ホスト間の横移動を防ぐ意味は薄い。
- SSH は鍵のみのままなので、パスワードを設定しても、ネットワーク越しに総当たりされる経路は増えない。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| 設定しない（従来どおり） | コンソールから入れない。復旧に回り道が要る |
| `sudoers` に `Defaults` を足して `sudo -v` を通す | コンソールの問題が残る。個別のスクリプトのために設定を曲げることになる |
| VM ごとに別のパスワード | 管理する値が5つに増える。緊急時にどれか迷う |
| `NONINTERACTIVE=1` などで毎回回避する | 緊急用の入口にならない。回避は都度の手間 |
| SSH のパスワード認証も有効にする | 鍵のみという方針を崩し、攻撃面が増える |

## 影響と再検討の条件

- **増えるもの**: 管理するシークレットが1つ。[secrets.md](../operations/runbooks/secrets.md) の表と、Keychain の項目に載せる。
- **漏れたとき**: 新しいパスワードのハッシュを作って SOPS を書き換え、`site.yml` を流し直す。Git 履歴に旧ハッシュが残るので、旧パスワードは使わない。
- **再検討の条件**: VM に別のユーザーが増えるとき。外部から VM に入れる経路（SSH のパスワード認証など）を開けるとき。
- 手順は [障害時切り分け](../operations/runbooks/troubleshooting.md#vm-が応答しない)。方式は [セキュリティ](../architecture/05-security.md#ホストへのログイン)。
