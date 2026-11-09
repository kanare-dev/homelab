# 0027. Servers の第 4 オクテットを役割の帯で分け、緊急用プールの DNS はルーターにする

- ステータス: 採用（未適用。段階 3 で適用）
- 日付: 2026-11-09
- [ADR-0025](0025-address-octets-by-role.md) のうち、`vm-apps`・`vm-code` の割り当て（`.12`、`.13`）と、Management の緊急用プールが配る DNS を置き換える。ほかは変えない

## 背景

ADR-0025 で、Servers の VM を `.10`〜`.13` の連番にした（`vm-infra`、`vm-monitoring`、`vm-apps`、`vm-code`）。見直したところ、2 つの問題が見つかった。

- 連番は、導入の順で決まっている。ADR-0025 が避けたかった「番号に意味が無い」状態が、Servers の中に残る。VMID が第 4 オクテットから決まる（[ADR-0026](0026-vmid-from-vlan-and-octet.md)）ので、番号は VM の作り直しなしには変えられない。最初に決めておく価値がある。
- Management の緊急用プールは、DNS に `10.77.20.10`（`vm-infra`）を配る。しかし、緊急用プールを使うのは、`vm-infra` が止まっているか、Servers に届かない障害のときで、そのとき名前を引けない。

`vm-code` は常時稼働にしたいので Servers に置くが、DNS・Caddy・監視・アプリの VM とは、性質が違う（Claude Code が任意のコマンドを実行する開発環境）。

## 決定

1. Servers の固定アドレス（`.10–.49`）を、役割の帯に分ける。

   | 範囲 | 役割 | 割り当て |
   | --- | --- | --- |
   | `.10–.19` | 基盤・運用 | `vm-infra` が `.10`、`vm-monitoring` が `.11` |
   | `.20–.29` | アプリ | `vm-apps` が `.20` |
   | `.30–.39` | 開発・作業用 | `vm-code` が `.30` |
   | `.40–.49` | 未使用 | 将来の拡張 |

   新しい VM は、役割の帯の空きに置く。VMID は、[ADR-0026](0026-vmid-from-vlan-and-octet.md) のとおり、`vm-apps` が 2020、`vm-code` が 2030。
2. この帯の分け方は、**番号の整理のためで、ネットワークの隔離ではない。** 同じ VLAN の中の通信は、ER605 の ACL を通らない。
3. 帯を分けるのは、Servers だけ。ほかの VLAN は、台数が少ないので連番にする（Lab は `vm-dev` が `.10`）。
4. Management の緊急用プール（`.240–.250`）は、DNS にルーター（`10.77.10.1`）を配る。ほかの VLAN は、ADR-0024 のとおり、`10.77.20.10` を配る（緊急用プールだけが例外）。
5. Buffalo は、`10.77.30.50`（Trusted）のままにする。Buffalo は VLAN に対応せず、管理 IP と Wi-Fi の端末が同じ VLAN になるため、Management に置けない。段階 4 で Omada の AP に替えるまでの暫定の例外で、AP は Management（`10.77.10.4–.9`）に置ける見込み（実機で確認する）。

## 理由

- 帯を分けておくと、VM が増えても、番号が役割の順に並ぶ。番号から役割が分かる。
- `vm-infra` が `.10` なのは、DHCP が配る DNS として、すでに決めてあるから。変えない。
- `vm-code` は、Lab に移す案もあった。常時稼働にしたいので、Servers に置く。隔離は、今は求めない。
- 緊急用プールがルーターの DNS を配れば、`vm-infra` が止まっていても、外部の名前を引ける。VM のホスト DNS をルーターにしている理由（[ADR-0007](0007-vm-host-dns-is-router.md)：復旧作業を DNS 障害から切り離す）と同じ。

## 代替案

| 案 | 判断 |
| --- | --- |
| Servers を連番のままにする（`.10`〜`.13`） | 見送り。導入順で決まった番号が、VMID に固定される |
| `vm-code` を Lab に移す | 見送り。常時稼働にしたい。隔離は求めていない。必要になったら再検討する（VMID も変わる） |
| 緊急用プールの DNS を `vm-infra` のままにする | 見送り。障害時に引けない。Management から Servers への 53 番の許可も要る |
| 緊急用プールに DNS を配らない | 見送り。ファームウェアの取得などで外部の名前が要るとき、手で指定することになる |
| 緊急用プールが公開 DNS（`1.1.1.1` など）を直接配る | 見送り。外への 53 番を許可する例外が増える。ほかの VLAN と配り方が違う |

## 影響と再検討の条件

- 緊急用プールを使うときは、`*.lab.kanare.dev` を引けない。管理機器は IP で開く（[ER605](../hardware/er605/settings.md)、[Proxmox](../architecture/09-ip-addresses.md) など）。
- 要確認: ER605 の DNS プロキシ（上流への転送）が、Management で有効か。段階 3 の確認の項目に入れる。
- 書き換えの対象: [IP アドレス一覧](../architecture/09-ip-addresses.md)、[VLAN 設計](../architecture/08-vlan-design.md)、[移行計画](../operations/roadmap/10-er605-sg2210p-migration-plan.md)、[Runbook 21](../operations/runbooks/21-network-cutover-stage-3.md)、構成図（`docs/diagrams/main-diagram/`）。
- 段階 3 の前に、Ansible・Terraform・Caddy・Prometheus の IP を、新しい値（`vm-apps` が `10.77.20.20`、`vm-code` が `10.77.20.30`）で用意する。
- `vm-code` を隔離したくなったら、(1) 他の VM の UFW で、`vm-code` からの受信を絞る、(2) Lab か専用の VLAN に移す、のいずれかを、新しい ADR で決める。

詳細: [IP アドレス一覧](../architecture/09-ip-addresses.md)、[IP 割り当てと DHCP の見直し](../operations/roadmap/12-ip-address-and-dhcp-review.md)
