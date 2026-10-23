# 0007. VM のホスト DNS はルーターにする

- ステータス: 採用
- 日付: 記録なし（理由は 2026-10-24 に運用者が確認して記録）

## 背景

全 VM の DNS は、Terraform の cloud-init（`nameserver = "192.168.11.1"`）でルーター（Buffalo）を指している。AdGuard Home（`vm-infra`）を向ける案もあった。外形監視の導入（blackbox-exporter）で、`*.lab.kanare.dev` を引けないことが問題になり、見直した。

## 決定

VM のホスト DNS は、ルーターのままにする。AdGuard を使いたいコンテナ（blackbox-exporter）だけ、`docker-compose.yml` の `dns:` で個別に指定する。

## 理由

- **通知経路を DNS 障害に巻き込まない。** Alertmanager は Slack の宛先（`hooks.slack.com`）をホストの DNS で引く。`vm-monitoring` が AdGuard に依存すると、AdGuard の停止時に `DnsProbeFailed` が発報しても Slack に届かない。
- **復旧作業を止めない。** apt や `docker pull` が、AdGuard の停止中も使える。
- **起動順序の循環を避ける。** AdGuard の置き場所である `vm-infra` 自身は、自分の DNS に依存できない。

## 代替案

| 案 | 長所 | 短所 |
| --- | --- | --- |
| ルーター DNS（採用） | 通知・復旧が DNS 障害から独立している。VM 内で `lab.kanare.dev` を引けない | 内部の名前は、個別にコンテナの `dns:` などで指定する |
| 全 VM を AdGuard のみ | 全 VM が内部の名前を引ける | AdGuard 停止で通知・復旧が止まる |
| AdGuard とルーターの併記 | 内部の名前を引け、停止時は外部の名前だけ引ける | AdGuard の障害が、フォールバックで見えにくくなる |

## 影響と再検討の条件

- VM 内のホストから `*.lab.kanare.dev` は引けない。必要なコンテナは `dns:` で AdGuard を指定する。
- VLAN 移行（[ADR 0004](0004-vlan-cutover-all-at-once.md)）で DHCP が配る DNS が `10.20.0.11` に変わる。そのとき、VM のホスト DNS を見直す（新しい ADR を追加して、この ADR を置き換える）。

詳細: [DNS](../services/dns.md)、[監視・アラート](../services/monitoring.md#外形監視blackbox)
