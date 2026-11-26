# 0036. 固定 IP を持つホストには、すべてホスト名の A レコードを付ける

- ステータス: 採用（2026-11-27 に適用）
- 日付: 2026-11-27

## 背景

`lab.kanare.dev` のゾーン（CoreDNS）には、サービスの名前（`grafana`、`omada` など。Caddy を指す）と、ホストの名前（そのホストを直接指す）がある。ホストの名前は、`vm-infra`、`vm-monitoring`、`vm-apps`、`vm-code`、`pve01` にだけ付いていた。`vm-omada`、`vm-dev`、ルーター、スイッチ、AP には無く、名前を引けるホストと引けないホストが混ざっていた。`vm-dev` は、手動で起動する VM なので、レコードを置いていなかった。

ネットワーク機器の名前を `rtr01`、`sw01`、`ap01` に決めたこと（[ADR-0035](0035-network-device-names-by-role.md)）を受けて、運用者は、ホストの名前の扱いを揃えることにした（[ロードマップ 15](../operations/roadmap/15-host-names-and-dns-records.md) の案 1）。

## 決定

1. 固定 IP を持つホストには、すべて `<ホスト名>.lab.kanare.dev` の A レコードを付け、そのホストを直接指す。新しいホストを足すときも、同じ変更でレコードを足す。
2. 今回、`rtr01`（`10.77.10.1`）、`sw01`（`10.77.10.2`）、`vm-omada`（`10.77.10.3`）、`ap01`（`10.77.30.50`）、`vm-dev`（`10.77.40.10`）を足す。`vm-dev` も、手動起動だが、名前は付ける（止まっている間は、引けても繋がらない）。
3. 名前は、普段の操作（`ssh`、`ping`、`traceroute`、ログ）を読みやすくするために使う。**監視の対象（Prometheus、blackbox-exporter）と、緊急時の手順書は、IP で書く。**
4. ネットワーク機器の管理画面は開かない（Omada が管理している）ので、Caddy の転送は足さない。A レコードだけにする。

## 理由

- 「固定 IP を持つものには、ホスト名のレコードがある」という一つの決まりにすると、新しいホストのときに迷わない。構成図の斜体のホスト名とも、そのまま対応する。
- 名前を引くのは `vm-infra`（AdGuard Home と CoreDNS）で、`vm-infra` が止まると名前は引けない。Management の緊急用 DHCP プールは、ルーターを DNS として配るので、緊急時には、もともと `*.lab.kanare.dev` を引けない（[ADR-0027](0027-servers-octet-bands-and-emergency-dns.md)）。障害のときに頼る監視と手順を IP にしておけば、DNS の障害が、ほかの障害の調査を妨げない。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| 今のまま（よく SSH する VM と `pve01` だけに付ける） | 名前を引けるホストと引けないホストが混ざり、新しいホストのたびに判断が要る |
| 監視の対象も名前で書く | `vm-infra` が止まると、ネットワーク機器の監視まで止まる。障害の切り分けが難しくなる |
| ルーターのローカル DNS（ER605 の Domain Name）に登録する | 名前解決は `vm-infra` の CoreDNS に集めている（[Omada コントローラーと管理対象機器](../architecture/lld/network/omada-controller.md)）。2 か所で管理することになる |

## 結果

- `ansible/inventory/group_vars/infra/vars.yml` の `dns_records` に 5 件を足し、`ansible-playbook playbooks/infra.yml` で反映する。反映すると CoreDNS が再起動し、数秒、`*.lab.kanare.dev` が引けなくなる。
- 反映したら、このステータスを「採用」にする。

詳細: [DNS](../architecture/lld/network/dns.md)、[IP アドレス一覧](../architecture/lld/network/ip-addresses.md#fqdn-の宛先)、[ロードマップ 15](../operations/roadmap/15-host-names-and-dns-records.md)
