# 0020. DNS は AdGuard Home・CoreDNS・Unbound の3層にする

- ステータス: 採用
- 日付: 2026-11-01（導入時の判断は記録なし。現行構成の理由を整理し直した）

## 背景

`vm-infra` で、LAN の DNS を AdGuard Home（入口）、CoreDNS（`lab.kanare.dev` の権威）、Unbound（外部の再帰解決）の3層で動かしている（[DNS 構成](../services/network/dns.md)）。Pi-hole、Technitium DNS Server、BIND9 などと比べた記録や、3層に分けた理由の記録は残っていなかったため、現在の要件に照らして理由を明文化する。導入当時の検討記録は無い。

要件は次のとおり。

- 広告・トラッカーのブロックと、クエリログ・統計の Web UI が欲しい。
- `*.lab.kanare.dev` の内部名を、Git と Ansible で管理して再現できるようにする。
- 外部の名前解決は、特定の公開リゾルバ（1.1.1.1 など）に依存せず、DNSSEC 検証とプライバシーに配慮する。
- `vm-infra`（1.5GB）に載る軽さにする。

## 決定

次の3層にする。クライアントのクエリはすべて AdGuard Home が受け、`lab.kanare.dev` は CoreDNS へ、それ以外は Unbound へ振り分ける。

| 層 | 役割 |
| --- | --- |
| AdGuard Home | 入口。フィルタリング、クエリログ、Web UI |
| CoreDNS | `lab.kanare.dev` のみの権威 DNS。ゾーンは Ansible のテンプレートから生成する |
| Unbound | ルートヒントからのフル再帰解決、DNSSEC 検証 |

## 理由

- **役割ごとに最適な部品を選べる。** 広告ブロックと UI は AdGuard、権威は CoreDNS、再帰は Unbound と、それぞれ得意なものに任せる。1つが不調でも、切り分けと入れ替えがしやすい。実際に Unbound が約3分応答しなかったときも、fallback DNS を足すだけで済んだ。
- **内部名をコードで管理できる。** CoreDNS のゾーンは `dns_records`（`group_vars/infra/vars.yml`）から生成する。GUI の設定に内部名が埋もれず、差分が Git で読める。
- **外部の公開リゾルバに依存しない。** Unbound がルートから再帰するため、上流の障害やログの送信先を気にしなくてよい。
- **どれも軽い。** 3つを足しても `vm-infra` の資源に収まる。

## 代替案

| 案 | 判断 |
| --- | --- |
| Pi-hole + Unbound | 見送り。役割は AdGuard Home とほぼ同じ。AdGuard の Web UI とフィルタ設定が好みで、すでに稼働している |
| Technitium DNS Server | 見送り。権威・再帰・ブロックを1つで担えるが、設定の中心が GUI で、Git と Ansible での管理に向かない。1つに集約すると障害の影響範囲も広がる |
| BIND9 | 見送り。権威・再帰を1つで担える本格派だが、広告ブロックと UI は別に要り、この規模には設定が重い |
| AdGuard の DNS rewrite だけで内部名を持つ（CoreDNS を外す） | 簡単で部品も減る。有力な代替案。ただし内部名が AdGuard の設定ファイルに入り、ゾーンとして管理しにくい。権威と入口を分ける設計と、学習の面から CoreDNS を残している |
| 公開リゾルバ（1.1.1.1 など）を上流にする（Unbound を外す） | 見送り。上流への依存と、問い合わせ内容の送信が残る。fallback としてだけ使う |

## 影響と再検討の条件

- DNS の3層がすべて `vm-infra` 1台に載る。`vm-infra` が止まると名前解決が止まる。そのため VM のホスト DNS はルーターを向ける（[ADR 0007](0007-vm-host-dns-is-router.md)）。
- 障害時の切り分けが、3層ぶん増える（[監視](../services/platform/monitoring.md)の `dns-lab` と `dns-external` で層を分けて検知する）。
- 次のいずれかになったら、再検討する（新しい ADR を追加して、この ADR を置き換える）。
  - 内部名が少なく、運用が重いと感じ、CoreDNS を DNS rewrite に畳みたくなった。
  - [VLAN 化](../operations/roadmap/04-network-omada-vlan.md)や DMZ で、DNS の置き場所や参照先を変える必要が出た（DMZ の DNS は未決事項）。
  - Cloudflare Tunnel による外部公開で、Split-Horizon DNS が必要になった（[ADR 0005](0005-tailscale-only-remote-access.md)）。
  - `vm-infra` の単一障害点を解消するため、DNS を冗長化したくなった。

詳細: [DNS 構成](../services/network/dns.md)
