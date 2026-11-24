# Proxmox ホストの名前を `pve01` に変える

**状態: 計画（未実施）。** Proxmox ホストのホスト名を `pve` から `pve01`、FQDN を `pve01.lab.kanare.dev` に変える。将来、Proxmox のホストを増やしても名前が重ならないようにするためである。管理画面の `https://pve.lab.kanare.dev` は、今のまま使う。

- **VM は、再起動の間、止まる。** ホスト名の変更は、再起動を挟む。止まる時間は、再起動と VM の起動を合わせて、数分から 10 分ほどと見込んでいる（未確認）。
- **変更後は、`/etc/pve/nodes/` の下に、新しいノードのディレクトリができる。** VM の設定は、古いノード名のディレクトリに残るので、手で `pve01` の下へ移す（手順 4）。移すまで、管理画面から VM が消えて見える。
- 秘密の値と、機器の MAC アドレスは書かない（台帳へ）。

## 決めたこと

| 項目 | 変更前 | 変更後 |
| --- | --- | --- |
| ホスト名（`hostname`） | `pve` | `pve01` |
| FQDN（`hostname -f`） | `pve.lab.kanare.dev` | `pve01.lab.kanare.dev` |
| Proxmox のノード名 | `pve` | `pve01` |
| 管理画面の URL | `https://pve.lab.kanare.dev` | 変えない |
| Ansible のインベントリ名、`~/.ssh/config` の `Host` | `pve` | `pve01` |

`pve.lab.kanare.dev` は、ホストの名前ではなく、**管理画面のサービス名**として残す。CoreDNS の `pve` のレコードは、今までどおり Caddy（`10.77.20.10`）を指し、Caddy が `10.77.10.10:8006` へ転送する。ホストの名前を変えても、この経路には影響しない。ホストが増えたときも、`pve.lab.kanare.dev` は、どのホストの管理画面を開くかを、Caddy の側で選べる。

`pve01.lab.kanare.dev` には、CoreDNS に A レコード（`10.77.10.10`）を足す。ホストへ直接入る SSH のためである。

**変えないもの**: LVM のボリュームグループ名 `pve`（`pve/data`）は、ホスト名とは別のものである。変えると、起動できなくなるおそれがあるので、触らない。Proxmox の認証レルム `pve`（`homepage@pve!homepage-token` の `@pve`）も、ノード名とは別なので、変えない。

## 影響するもの

| 場所 | 影響 | 直し方 |
| --- | --- | --- |
| `/etc/hostname`、`/etc/hosts` | ホスト名が自分の IP に引けないと、`pve-cluster` などが起動しない | 手順 2 |
| `/etc/pve/nodes/pve/` | VM の設定（`qemu-server/*.conf`）が、旧ノード名の下に残る。管理画面と `qm list` から VM が消える | 手順 4 で `pve01` の下へ移す |
| ホストの TLS 証明書（自己署名） | ノード名が古いまま | `pvecm updatecerts -f`（手順 4） |
| `terraform/proxmox/terraform.tfvars` ほか | `proxmox_node` が古いと、API が「ノードが無い」と返す。変えると、telmate が VM の差分（`target_node`）を出すかもしれない | 手順 5。`plan` で確かめる。**差分が出たら、`apply` しない** |
| `ansible/inventory/hosts.yml` | インベントリ名 | 手順 5 |
| `docker/compose/monitoring/prometheus/prometheus.yml` | `host: "pve"` のラベルが変わる。`instance` ラベルもこの値になる（`relabel_configs`）ので、過去のメトリクスとは、別の系列になる | 手順 5。変更の前後で、系列が分かれることは受け入れる |
| `docker/compose/homepage/config/services.yaml` | `node: pve`、`instance="pve"` のクエリが合わなくなる | 手順 5 |
| `~/.ssh/config`（リポジトリの外） | `Host pve` | 手順 5 |
| 文書と図 | ホスト名の記述、as-is の図 | 手順 6 |

## 今の状態（未確認。実施の直前に確認する）

次のコマンドで確かめて、結果をこの節に書き直す。

- `hostname`、`hostname -f`、`cat /etc/hostname /etc/hosts`。`/etc/hosts` は、`10.77.10.10 pve.lab.kanare.dev pve` のはずである。
- `ls /etc/pve/nodes`（`pve` だけのはず）。`pvecm status` は、単体のノードなので、クラスターの設定が無いというエラーになるのが正常である。
- `grep -rn "pve" /etc/pve/storage.cfg /etc/pve/jobs.cfg /etc/pve/vzdump.cron`。`nodes pve` のようにノード名で制限している行があれば、手順 4 で直す。
- `ls /etc/pve/nodes/pve/qemu-server /etc/pve/nodes/pve/lxc`。VM の設定の一覧。LXC は無いはずである。
- `cat /etc/mailname`、`grep -n "pve" /etc/postfix/main.cf`。メールの設定にホスト名が入っていれば、直す。
- `qm list`。全 VM の VMID と状態（running のはず）。

## 0. 準備（当日の前）

- [ ] 手順 5 の**コードの変更を、ブランチで用意する**（適用は、ホスト名を変えたあと）。
- [ ] 物理コンソール（キーボードとモニター）を、すぐ繋げられる。Mac に、有線の口（SG2210P の p6、緊急用）がある。
- [ ] Terraform の telmate が、`proxmox_node` の変更をどう扱うかを、**先に調べる**。`terraform.tfvars` を `pve01` にして `terraform plan` を実行しても、今の状態（ノードは `pve`）では、API がノードを見つけられず、エラーになる。差分の出方は、ホスト名を変えたあとにしか確かめられない。出た差分が VM の再作成や移行なら、`apply` しない（戻し方は、手順 5 の注意）。
- [ ] 平日の 9〜18 時を避ける。作業の間は、VM の上のサービス（DNS、Home Assistant など）が止まる。
- [ ] 作業中に出るアラート（`TargetDown`、`PveVmStopped` など）は、想定内。

## 1. 退避する

`pve` に、SSH で入る（`ssh pve`）。

```bash
cp -a /etc/hostname /root/hostname.bak-$(date +%Y%m%d)
cp -a /etc/hosts /root/hosts.bak-$(date +%Y%m%d)
# /etc/pve は、秘密（priv）を除いて退避する
tar czf /root/etc-pve.bak-$(date +%Y%m%d).tgz -C /etc pve --exclude=pve/priv
ls -l /root/*.bak-*
```

退避したファイルを、Mac の iCloud Drive の `homelab/` にもコピーする（`scp`）。`/etc/pve` の退避には、VM の設定が入っている。公開しない（Git に入れない）。

## 2. ホスト名の設定を書き換える

**`hostnamectl` は使わない。** 実行中のホスト名がその場で変わり、停止の途中で、旧ノード名の VM を扱えなくなるおそれがある。ファイルだけを書き換えて、再起動で反映する。

```bash
echo pve01 > /etc/hostname
sed -i 's/^10\.77\.10\.10 .*/10.77.10.10 pve01.lab.kanare.dev pve01/' /etc/hosts
cat /etc/hostname /etc/hosts
```

`/etc/hosts` の `10.77.10.10` の行が、`10.77.10.10 pve01.lab.kanare.dev pve01` だけになっていることを、目で確かめる。**この行が違うと、再起動のあと、Proxmox のサービスが起動しない。**

## 3. 再起動する

```bash
reboot
```

再起動の途中で、Proxmox は VM を、`startup` の順序（[VM の自動起動・停止](01-vm-startup-shutdown.md)）で、安全に停止する。起動したあと、ホストは `pve01` として立ち上がるが、`onboot` の VM は、**まだ起動しない**（設定が、旧ノード名の下にあるため）。

2〜3 分待って、`ssh root@10.77.10.10`。Mac の `~/.ssh/config` は、まだ `Host pve` のまま。IP で入る。

## 4. VM の設定を移して、起動する

```bash
hostname; hostname -f          # pve01、pve01.lab.kanare.dev
ls /etc/pve/nodes              # pve と pve01
systemctl is-active pve-cluster pveproxy pvedaemon
ls /etc/pve/nodes/pve/qemu-server
```

`pve-cluster` が active でなければ、`/etc/hosts` を疑う（「うまくいかないときの見方」）。

```bash
mv /etc/pve/nodes/pve/qemu-server/*.conf /etc/pve/nodes/pve01/qemu-server/
ls /etc/pve/nodes/pve/qemu-server   # 空であること
ls /etc/pve/nodes/pve/lxc           # 空であること（LXC は無いはず）
rmdir /etc/pve/nodes/pve/qemu-server /etc/pve/nodes/pve/lxc 2>/dev/null
rm -r /etc/pve/nodes/pve            # 旧ノードが、管理画面に、オフラインで残るのを防ぐ
pvecm updatecerts -f                # 証明書を、新しいノード名で作り直す
systemctl restart pveproxy
qm list                             # 全 VM が見える。stopped のはず
```

`/etc/pve/storage.cfg` などに `nodes pve` の行があれば、`pve01` に直す。

VM を起動する。`onboot` の VM を、`startup` の順序で起動するには、次を使う。

```bash
systemctl restart pve-guests
```

起動しない VM があれば、[VM の自動起動・停止](01-vm-startup-shutdown.md)の順序で、`qm start <vmid>` する。

## 5. 参照先を付け替える

手順 0 で用意したブランチの変更を、反映する。

1. `ansible/inventory/hosts.yml` の `pve` を `pve01` にする（`ansible_host` は変えない）。`ansible/README.md` の記述も直す。
2. CoreDNS の `dns_records`（`ansible/inventory/group_vars/infra/vars.yml`）に `{ name: "pve01", ip: "10.77.10.10" }` を足す。`pve` のレコードは、変えない。`ansible-playbook playbooks/infra.yml` で反映する。
3. `terraform/proxmox/terraform.tfvars` の `proxmox_node` と、`variables.tf` の既定値を `pve01` にする。`cd terraform/proxmox && terraform plan` を実行する。**変更が 0 件なら、そのまま終える。** `target_node` の差分が出たら、`apply` せず、内容を読む。
   - 差分が `target_node` の更新だけなら、`terraform apply -refresh-only` で状態を実機に合わせて、`plan` を取り直す。
   - VM の再作成（`must be replaced`）が出たら、止める。`terraform.tfvars` を `pve` に戻して、原因を調べる。
4. `docker/compose/monitoring/prometheus/prometheus.yml` の `host: "pve"` を、2 か所とも `pve01` にする。`docker/compose/homepage/config/services.yaml` の `node: pve`、`instance="pve"` のクエリを `pve01` にする（`homepage@pve` の `pve` は、認証レルムなので、変えない）。`ansible-playbook playbooks/site.yml --limit pve01,vm-infra,vm-monitoring,vm-apps` で反映する（Prometheus は、再起動する）。
5. `~/.ssh/config` の `Host pve` を `Host pve01` にする。`ssh pve01` で入れる。
6. 確認: `https://pve.lab.kanare.dev` が開く。Prometheus で `host="pve01"` の `node` の target が up。Homepage の Proxmox のタイルが表示される。`dig pve01.lab.kanare.dev` が `10.77.10.10`。

## 6. 文書を直す

実機の設定を変えたので、同じ変更で、実施の結果を反映する（CLAUDE.md の決まり）。

- [ ] [ThinkCentre の設定](../../architecture/lld/platform/proxmox-host.md)（「予定」を「確認済み」にして、予測が外れた点を書き、変更履歴に 1 行足す）。
- [ ] [IP アドレス一覧](../../architecture/lld/network/ip-addresses.md)、[DNS 構成](../../architecture/lld/network/dns.md)（`pve01` のレコード）、`README.md`（構成の表）。
- [ ] `ssh pve` と書いてある文書: [監視・アラート](../../architecture/lld/platform/monitoring.md)、[障害時の切り分け](11-troubleshooting.md)、[Homepage](../../architecture/lld/apps/homepage.md)、[システム構成・環境](../../architecture/hld/03-operations.md)（ノード名）。
- [ ] as-is の構成図（ホスト名）。`docs/diagrams/as-is-diagram/make-as-is-diagram.py` を直し、`python3 docs/diagrams/as-is-diagram/make-as-is-diagram.py --png` で書き出して、ライトとダークの PNG で崩れていないかを見る。物理構成図の `Proxmox（pve）` も直す。
- [ ] この文書の「実績」を書く。

## 戻し方

ホスト名を変えたあと、うまくいかないときは、次の順で戻す。

```bash
# 物理コンソールか、IP の SSH で
cp -a /root/hostname.bak-YYYYMMDD /etc/hostname
cp -a /root/hosts.bak-YYYYMMDD /etc/hosts
reboot
```

起動後は、ホストが `pve` に戻り、`/etc/pve/nodes/pve/` が作り直される。手順 4 で VM の設定を移していた場合は、`pve01` の下から戻す。

```bash
mv /etc/pve/nodes/pve01/qemu-server/*.conf /etc/pve/nodes/pve/qemu-server/
rm -r /etc/pve/nodes/pve01
pvecm updatecerts -f
systemctl restart pveproxy pve-guests
```

手順 4 の `rm -r /etc/pve/nodes/pve` を実行したあとでも、VM の設定は `pve01` の下に移してあるので、失われていない。設定そのものを失ったときは、手順 1 の `/etc/pve` の退避（`.tgz`）から、`nodes/pve/qemu-server/*.conf` を取り出す。コードの変更（手順 5）を反映していた場合は、その変更も、元に戻す。

## うまくいかないときの見方

- **再起動のあと、管理画面も SSH も、入れない**: ホスト名の解決を疑う前に、`ssh root@10.77.10.10`（IP）で届くかを見る。届かなければ、物理コンソール。
- **`pve-cluster` や `pveproxy` が起動しない**: `hostname -f` と、`getent hosts $(hostname)`。`/etc/hosts` の行が `10.77.10.10 pve01.lab.kanare.dev pve01` でなければ、直して、`systemctl restart pve-cluster pveproxy pvedaemon`。
- **管理画面は開くが、VM が一つも見えない**: 手順 4 の `mv` が済んでいない。`ls /etc/pve/nodes/pve/qemu-server` に、設定が残っている。
- **管理画面に、オフラインの `pve` が残る**: `/etc/pve/nodes/pve` が残っている。中が空であることを確かめて、`rm -r` する。
- **ブラウザが、証明書の警告を出す**: `pvecm updatecerts -f` のあと、`systemctl restart pveproxy`。Caddy 経由の `pve.lab.kanare.dev` は、`tls_insecure_skip_verify` なので、影響しない。
- **Prometheus で `pve` の系列が止まる**: 想定内。`host="pve01"` の系列に切り替わっている。Grafana のダッシュボードが `host` を固定していれば、直す。

## 未確認

- Terraform（telmate）が、`proxmox_node` の変更で、既存の VM にどんな差分を出すか。手順 5 の 3 で、実機を変えたあとに確かめる。
- `/etc/pve/storage.cfg`、`jobs.cfg`、`vzdump.cron` に、ノード名で制限した行があるか。「今の状態」で確かめる。
- 再起動を挟んだ、VM の停止から全 VM の復帰までの時間。
- `pve-guests` の再起動で、`startup` の順序どおりに、全 VM が上がるか。

## 実績

実施したあとに書く。予測が外れた点（所要時間、差分の出方など）を、ここに残す。
