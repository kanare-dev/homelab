# Proxmox ホストを VLAN10（`vmbr0.10`、`10.77.10.10`）に移す

**状態: 実施済み（2026-11-19）。** 段階 3b の残り。Proxmox ホスト（`pve`）の IP を、今の LAN の `192.168.11.10`（`vmbr0`、タグなし）から、Management の `10.77.10.10/24`（タグ付きの `vmbr0.10`）に移す。`vm-omada`・SG2210P・ER605 の移行は、[段階 3b の作業](23-network-stage-3b-management-vlan10.md)で済んでいる（2026-11-19）。

- ホストの設定を変えるだけで、**VM は動き続ける**（ブリッジ `vmbr0` は変えない）。止まるのは、ホストへの接続（Web UI、SSH、Terraform、Prometheus の `pve` の監視、Homepage の表示）だけで、数分。
- **物理コンソールと、自動で元に戻るタイマーを使う。** 誤ると、SSH も Web UI も使えなくなる。
- この作業は、[既定の LAN の付け替え](../roadmap/13-defer-management-vlan.md#既定の-lan-のアドレス検討中)（案 A・案 B どちらも）の**前**に行う。ホストが移れば、旧 LAN（`192.168.11.0/24`）には、ER605 の住所以外、何も残らない。
- 秘密の値と、機器の MAC アドレスは書かない（台帳へ）。

## 今の状態（2026-11-19 に確認）

- `/etc/network/interfaces`: `vmbr0` に `192.168.11.10/24`、ゲートウェイ `192.168.11.1`、`bridge-ports nic0`、`bridge-vlan-aware yes`、`bridge-vids 2-4094`。`nic0` の `post-up ethtool -K nic0 tso off gso off gro off` は、Ansible の管理（[INC-2026-10-25](../incidents/2026-10-25-nic-hardware-unit-hang.md)）。
- `/etc/hosts`: `192.168.11.10 pve.lab.kanare.dev pve`。**Proxmox は、ホスト名が自分の IP に引けないと、サービスが壊れる**ので、**IP を変えるときは、この行も直す。**
- `pve-firewall` は無効（`disabled/running`）、UFW は無い。8006・22・9100 は、どこからでも届く。
- VLAN10 の経路は、実績がある: `vm-omada` が `vmbr0` のタグ付き VLAN10 で動いている（SG2210P の p2 の tagged に VLAN10 が入っている）。ER605 の VLAN10（`10.77.10.1`）がゲートウェイ。
- 退避済みのファイル: iCloud Drive の `homelab/pve-interfaces-bk-20261111.txt`、`...-20261117.txt`（今の LAN の設定。当日の直前に、取り直す）。

## 0. 準備（当日の前）

- [ ] 次の**コードの変更を、ブランチで用意する**（適用は、移したあと）。
  - `terraform/proxmox/terraform.tfvars` の `proxmox_api_url` → `https://10.77.10.10:8006/api2/json`。
  - `ansible/inventory/hosts.yml` の `pve` の `ansible_host` → `10.77.10.10`。
  - `docker/compose/reverse-proxy/Caddyfile` の `pve.lab.kanare.dev` の転送先 → `https://10.77.10.10:8006`。
  - `docker/compose/monitoring/prometheus/prometheus.yml` の `proxmox` の targets → `10.77.10.10:9100`。
  - `docker/compose/homepage/config/services.yaml` の URL と説明 → `10.77.10.10`。
  - `~/.ssh/config`（リポジトリの外）の `pve` の `HostName`。
- [ ] 物理コンソール（キーボードとモニター）を、すぐ繋げられる。Mac に、有線の口（SG2210P の p6、緊急用。native VLAN1）がある。モバイル回線のスマホがある。
- [ ] 作業の間、Proxmox の Web UI や Terraform を使う作業は、しない。VM の起動・停止の作業中でない。
- [ ] 作業中に出るアラート（Proxmox の `TargetDown`、`PveVmStopped` ではないもの）は、想定内。VM は動き続ける。

## 1. 退避と、自動で戻すタイマー

`pve` に、SSH で入る（`ssh pve`。この接続は、手順 3 で切れる）。

```bash
cp /etc/network/interfaces /root/interfaces.bak-$(date +%Y%m%d)
cp /etc/hosts /root/hosts.bak-$(date +%Y%m%d)
# 10 分後に、退避を書き戻して、反映する（成功したら、手順 5 で止める）
systemd-run --unit=netrevert --on-active=10m /bin/sh -c \
  'cp /root/interfaces.bak-YYYYMMDD /etc/network/interfaces && cp /root/hosts.bak-YYYYMMDD /etc/hosts && ifreload -a'
systemctl list-timers netrevert.timer
```

（`YYYYMMDD` は、実際の日付に直す。）タイマーが仕掛かっていることを、`list-timers` で確認する。**タイマーは、成功しても、止めない限り、10 分後に発火して、元に戻す。**

## 2. 設定を書き換える

`/etc/network/interfaces` を、次のとおりにする（`nic0` の `post-up`（Ansible の管理）はそのまま）。

```text
auto lo
iface lo inet loopback

iface nic0 inet manual
    # BEGIN ANSIBLE MANAGED: e1000e hang workaround (INC-2026-10-25)
    post-up ethtool -K nic0 tso off gso off gro off
    # END ANSIBLE MANAGED: e1000e hang workaround (INC-2026-10-25)

auto vmbr0
iface vmbr0 inet manual
	bridge-ports nic0
	bridge-stp off
	bridge-fd 0
	bridge-vlan-aware yes
	bridge-vids 2-4094

auto vmbr0.10
iface vmbr0.10 inet static
	address 10.77.10.10/24
	gateway 10.77.10.1

source /etc/network/interfaces.d/*
```

`/etc/hosts` の行を、`10.77.10.10 pve.lab.kanare.dev pve` にする。

- `vmbr0` から IP とゲートウェイを外し、`vmbr0.10` に付ける。`vmbr0` は、IP を持たない VLAN-aware のブリッジのまま（`bridge-vids` に 10 が含まれる）。
- **`ifreload -a -n`（ドライラン）は、VLAN のインターフェースを作る設定では、エラーになる**（ifupdown2 の不具合。[リハーサル C-1](22-network-stage-3-rehearsal.md#c-1-vmbr010-の試験)）。事前の検証には使えない。`ifup vmbr0.10` は、リハーサルで成功している。

## 3. 反映する

```bash
ifreload -a
```

**この瞬間、Mac からの SSH が切れる**（IP が変わるため）。10 秒ほどで、新しい IP から届くはず。届かないときは、**物理コンソール**で、`ip -br a`、`ip route` を見る。10 分待つか、手で退避を書き戻して `ifreload -a`（下の「戻し方」）。

## 4. 確認する

Mac で、`ssh root@10.77.10.10`（ホスト鍵は、同じホストなので、同じ指紋のはず。`known_hosts` に新しい行が足される）。

- [ ] `ip -br a` で、`vmbr0.10` が `10.77.10.10/24`、`vmbr0` に IP が無い。
- [ ] `ip route` で、`default via 10.77.10.1 dev vmbr0.10`、`10.77.10.0/24 dev vmbr0.10`。旧 LAN の経路が無い。
- [ ] `ping -c3 10.77.10.1`、`ping -c3 8.8.8.8` が通る。
- [ ] `hostname -i` が `10.77.10.10`。`systemctl is-active pveproxy pvedaemon pve-cluster` がすべて `active`。
- [ ] `qm list` で、VM が running のまま。VM（`10.77.20.10`、`10.77.10.3` など）に、Mac から届く。
- [ ] `https://10.77.10.10:8006` で、Web UI が開く（ログインできる）。
- [ ] `dmesg | grep -i "Hardware Unit Hang"` に、新しい出力が無い（e1000e の送信停止が、再発していない）。
- [ ] `ethtool -k nic0 | grep -E "tcp-segmentation|generic-segmentation|generic-receive"` が、`off`。

## 5. タイマーを止める

**確認が通ったら、すぐに**止める。

```bash
systemctl stop netrevert.timer
systemctl list-timers netrevert.timer   # 何も出ないこと
```

## 6. 参照先を付け替える

手順 0 で用意したブランチの変更を、反映する。

1. Terraform: `cd terraform/proxmox && terraform plan`（`pve` の API に届き、変更が 0 件であること）。
2. Ansible: `ansible-playbook playbooks/site.yml --limit pve,vm-infra,vm-monitoring,vm-apps`（Caddy、Prometheus、Homepage の設定を反映する。**Prometheus は、再起動する**）。
3. `~/.ssh/config` の `pve` の `HostName` を直し、`ssh-keygen -R 192.168.11.10` で、古い `known_hosts` の行を消す。
4. 確認: `https://pve.lab.kanare.dev` が開く。Prometheus で `proxmox` の target が up。Homepage の Proxmox のタイルが表示される。

## 7. 文書を直す

実機の設定を変えたので、同じ変更で直す（CLAUDE.md の決まり）。

- [ ] [ThinkCentre の設定](../../hardware/thinkcentre-m70q-tiny/settings.md)（IP、Web UI の転送先、変更履歴）。
- [ ] [IP アドレス一覧](../../architecture/lld/network/ip-addresses.md)、[インフラ構成](../../architecture/02-infrastructure.md)、[システム全体像](../../architecture/01-overview.md)（as-is の図と注釈）、[VLAN 設計](../../architecture/08-vlan-design.md)、`README.md`（ホストの IP）。
- [ ] 手順書: [VM 自動起動・停止](01-vm-startup-shutdown.md)、[トラブルシュート](11-troubleshooting.md)（`ssh root@192.168.11.10` を `10.77.10.10` に）。
- [ ] 監視: [監視・アラート](../../architecture/lld/platform/monitoring.md)（`curl` の宛先）、Homepage の文書。
- [ ] as-is の構成図（`pve` の IP、`vmbr0.10`）。`docs/diagrams/as-is-diagram/make-as-is-diagram.py` を直し、PNG を書き出して確認する。
- [ ] [ロードマップ 13](../roadmap/13-defer-management-vlan.md) に、結果を書く。

## 戻し方

- **自動**: 手順 1 のタイマーが、10 分後に、退避を書き戻して `ifreload -a` する。
- **手動**（物理コンソール）: `cp /root/interfaces.bak-YYYYMMDD /etc/network/interfaces && cp /root/hosts.bak-YYYYMMDD /etc/hosts && ifreload -a`。`vmbr0` が `192.168.11.10/24` に戻る。
- 戻したあとは、Mac から `192.168.11.10`（ER605 経由）で届く。`/etc/hosts` も、戻っている。

## うまくいかないときの見方

- **`10.77.10.1` に届かない**: SG2210P の p2 の tagged に、VLAN10 が入っているか（[SG2210P の設定](../../hardware/sg2210p/settings.md)）。`bridge-vids` に 10 が含まれるか（`bridge vlan show`）。
- **Web UI は開くが、ログインできない・サービスが壊れる**: `/etc/hosts` が、新しい IP になっているか。`systemctl status pve-cluster pveproxy`。
- **Mac から届かない（ホストの中は、正常）**: ER605 の VLAN10 のゲートウェイと ACL（全許可のはず）。Mac が Trusted（`10.77.30.x`）にいるか。

## このあとの作業

- 既定の LAN の付け替え（案 A: `10.77.1.0/24`、案 B: VLAN10 に統合）。[ロードマップ 13](../roadmap/13-defer-management-vlan.md#既定の-lan-のアドレス検討中)。
- ACL を絞る（[ADR-0029](../../adr/0029-stage3-acl-allow-all-then-tighten.md)）。

## 実績（2026-11-19）

- 23:03〜23:07 に実施した（事前確認から、参照先の付け替えの完了まで）。**ホストの切り替え（退避、`ifreload -a`、確認、タイマー停止）は、約 2 分**。参照先の付け替えを含めて、約 5 分。見込み（30〜45 分）より、かなり短かった。
- 事前の確認（読み取りだけ）: `pveversion`（9.1.7）、`ifupdown2`（3.3.0）、VM の状態、実行中のタスクが 0 件、`dmesg` に `Hardware Unit Hang` が無いこと。設定は、iCloud Drive にも退避した。
- `ifreload -a` から、約 50 秒で、新しい IP に届いた（SSH の初回の接続は、鍵の指定が足りず、拒否された。`ssh pve`（`~/.ssh/config` の `HostName` を一時的に上書き）で入り直した）。`ifreload -a` は、設定を書き換えたあと、バックグラウンドで実行した（SSH が切れても、実行が続くようにするため）。
- 確認はすべて通った: 既定の経路が `10.77.10.1`（`vmbr0.10` 経由）、`hostname -i` が `10.77.10.10`、`pveproxy` などが active、VM は動き続けた、`vmbr0` 自身が VLAN 1 と 10 のメンバー、Web UI が 200、`omada.lab.kanare.dev`・`home.lab.kanare.dev` も変わらず。
- 参照先: Terraform の `plan` は、変更 0 件。Ansible は、`failed=0`（Caddy、Prometheus、Homepage を反映。Prometheus の `proxmox` が `10.77.10.10:9100` で up）。`~/.ssh/config` を直した（退避: `~/.ssh/config.bk-20261119b`）。
- **補正**: `ifreload -a` を実行する SSH のセッションは、切れる。`nohup ... &` で、バックグラウンドに回すと、確実。タイマーは、止めるまで 10 分あれば十分だった（確認に、約 2 分）。
