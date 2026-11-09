# 0026. VMID は `VLAN ID × 100 + 第 4 オクテット` にし、付け替えは VM の作り直しに合わせる

- ステータス: 採用（未適用。付け替えは、段階 3 の後の VM の作り直しで行う）
- 日付: 2026-11-09
- 現行の規則「VMID は、IP の末尾オクテットに 100 を足した値」を置き換える

## 背景

現在の VM は、VMID から IP が分かる（`111` → `192.168.11.11`）。規則は「末尾オクテット + 100」。

VLAN 化のあとは、第 4 オクテットを役割で決め直す（[ADR-0025](0025-address-octets-by-role.md)、[ADR-0027](0027-servers-octet-bands-and-emergency-dns.md)）ので、この規則が成り立たない。

| VM | 現 VMID | 移行後の IP | 「末尾 + 100」 |
| --- | --- | --- | --- |
| `vm-infra` | 111 | `10.77.20.10` | 110 |
| `vm-omada` | 112 | `10.77.10.3` | 103 |
| `vm-monitoring` | 113 | `10.77.20.11` | 111 |
| `vm-apps` | 120 | `10.77.20.20` | 120 |
| `vm-code` | 122 | `10.77.20.30` | 130 |
| `vm-dev` | 121 | `10.77.40.10` | 110 |

VLAN を含めない規則は、VLAN をまたぐと衝突する（`vm-infra` と `vm-dev` が、どちらも 110 になる）。

## 決定

1. VMID を `VLAN ID × 100 + 第 4 オクテット` にする。
   - 例: `10.77.20.10` の VM は `2010`、`10.77.10.3` の VM は `1003`、`10.77.40.10` の VM は `4010`。
   - 第 4 オクテットは 2 桁（`.1–.99`）に収まる。VM の固定アドレスは `.10–.49`、予約は `.50–.99` なので、問題ない。
2. 段階 3（一斉切り替え）では、VMID を変えない。VM を作り直すとき（[Ubuntu LTS の入れ替え](../operations/roadmap/01-backlog.md)など）に、新しい VMID に付け替える。新しい VM は、最初から新しい規則で作る。
3. 付け替えるまでは、[IP アドレス一覧](../architecture/09-ip-addresses.md#ホスト別の-ip)の VMID の列（現在と移行後）を正とする。
4. テンプレート `ubuntu-cloud`（9000）は変えない。VLAN ID に 90 を使うときは、範囲（`9000–9099`）が被るので、再検討する。

付け替えの対応:

| VM | 現 VMID | 新 VMID |
| --- | --- | --- |
| `vm-omada` | 112 | 1003 |
| `vm-infra` | 111 | 2010 |
| `vm-monitoring` | 113 | 2011 |
| `vm-apps` | 120 | 2020 |
| `vm-code` | 122 | 2030 |
| `vm-dev` | 121 | 4010 |

## 理由

- VMID から VLAN と役割が分かる。`qm start 2010` で `10.77.20.10` が引ける。
- 段階 3 で VMID も変えないのは、Terraform の見え方が変わるため。段階 3 では、VM の IP と VLAN を、同じ VM のまま変える（[Runbook 21](../operations/runbooks/21-network-cutover-stage-3.md)）。VMID を同時に変えると、Terraform には「VM の作り直し」と見え、一斉切り替えのリスクが増える。
- 作り直しは、`vm-dev` で実績がある（`terraform apply -replace`）。その機会に付け替えるなら、追加の手間が小さい。

## 代替案

| 案 | 判断 |
| --- | --- |
| A. VMID を据え置き、対応表を正にする | 見送り。VMID から IP が引けないままになる。ただし、コストはゼロで、VMID は不変という Proxmox の前提には合う |
| C. 「末尾 + 100」を続ける | 不可。VLAN をまたぐと衝突する |
| 段階 3 で、VMID も一緒に変える | 見送り。上の理由 |

## 影響と再検討の条件

- 第 4 オクテットが VMID に固定される。IP の番号を変えるときは、VM の作り直し（VMID の付け替え）を伴う。
- VM を別の VLAN に移すと、VMID も変わる（例: `vm-code` を Lab に移すと、2030 から 4011 になる）。
- 付け替えの手順は未検証。(1) 状態を持たない VM は、Terraform の作り直しで済む。(2) データを持つ VM は、`qm clone` で新しい VMID に複製し、Terraform の state を付け替える方法がある。VM のバックアップは取らない方針（[ADR-0001](0001-no-vm-backup.md)）なので、データを持つ VM は、先に `vm-dev` で手順を試す。
- 付け替えのたびに、Terraform の `terraform.tfvars`、[Runbook 01](../operations/runbooks/01-vm-startup-shutdown.md) のように VMID を直接書いている手順、[IP アドレス一覧](../architecture/09-ip-addresses.md)、各サービスの文書（`vm-omada` と `vm-code` の VMID の記述）を同じ変更で直す。
- 付け替えが面倒になったら、A に戻す（新しい ADR）。

詳細: [IP アドレス一覧](../architecture/09-ip-addresses.md)、[IP 割り当てと DHCP の見直し](../operations/roadmap/12-ip-address-and-dhcp-review.md)
