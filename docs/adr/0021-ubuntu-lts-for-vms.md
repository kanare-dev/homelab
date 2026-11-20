# 0021. VM の OS は Ubuntu Server LTS にし、LTS の入れ替えは VM の作り直しで行う

- ステータス: 採用
- 日付: 2026-11-01

## 背景

全 VM は、cloud-init 付きの Ubuntu Server 24.04 LTS（Noble）のテンプレート（VMID 9000）から Terraform で作っている（[インフラ構成](../architecture/02-infrastructure.md)、[`terraform/proxmox/README.md`](../../terraform/proxmox/README.md)）。選んだ理由が残っていなかった。Debian 13 は選択肢になりえた。また Ubuntu 26.04 LTS が 2026-04-23 に出て、26.04.1（2026-08）以降は 24.04 からのアップグレード経路も開いている。PVE ホストは Debian 13 ベースで、VM と OS の系統が異なる。

## 決定

- VM の OS は Ubuntu Server の LTS とする。今は 24.04 を使い続ける。
- LTS を入れ替えるときは、`do-release-upgrade` によるその場更新はせず、新しい LTS の cloud image でテンプレートを作り直し、VM を 1 台ずつ作り直す。
- 26.04 への移行は、`vm-dev` で Ansible の適用を確認してから始める（[ロードマップ](../operations/roadmap/01-backlog.md)）。急がない。

## 理由

- 公式の cloud image には、cloud-init と qemu-guest-agent が付いているので、Terraform の流れにそのまま組み込める。
- Docker、Tailscale、Ansible など、使うソフトウェアの手順や情報が、Ubuntu 向けに最も多い。
- LTS の標準サポートは 5 年間である。24.04 は 2029 年 4 月まで続くので、急いで入れ替える理由がない。
- VM のバックアップを取っていない（[ADR 0001](0001-no-vm-backup.md)）。その場で更新して失敗すると、元に戻せない。Terraform と Ansible で構成を定義してあるので、VM を作り直すほうが、安全で、再現もできる。

## 代替案

- Debian 13 は、PVE ホストと同じ系統で、素の状態が軽く、snap もない。cloud 向けのイメージもあり、cloud-init も使える。ただ、Docker を載せるだけの VM では、Ubuntu との差が小さい。テンプレートと Ansible の `common` ロールを作り直す手間に見合う利点がないので、見送った。
- その場更新（`do-release-upgrade`）は、手間が小さい。しかし、バックアップがなく、失敗すると戻せないので、見送った。
- Ubuntu の非 LTS は、半年ごとに入れ替える手間が出るので、見送った。

## 影響と再検討の条件

- 24.04 のサポートが終わる（2029 年 4 月）1 年前までに、26.04 以降への移行を終える。
- Debian を再検討する条件は、snap が実際の問題になったとき、VM のメモリが足りなくなって OS 本体の使用量が効いてきたとき、PVE ホストと揃えて運用を単純にしたくなったときである。
- VM のバックアップ（`vzdump` など）を導入したら、その場更新も選べるようになる。

詳細: [インフラ構成](../architecture/02-infrastructure.md)、[見送り中の項目](../operations/roadmap/03-deferred.md)
