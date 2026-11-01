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

- 公式の cloud image が cloud-init と qemu-guest-agent つきで、Terraform の流れにそのまま載っている
- Docker、Tailscale、Ansible など、使うソフトの手順と情報が最も多い
- LTS は標準サポート 5 年。24.04 は 2029 年 4 月まで続くので、急ぐ理由がない
- VM のバックアップがない（[ADR 0001](0001-no-vm-backup.md)）。その場更新は失敗すると戻せない。Terraform と Ansible で定義済みなので、作り直す方が安全で再現できる

## 代替案

- Debian 13: PVE ホストと同系統で、素の状態は軽く、snap がない。cloud 向けイメージもあり、cloud-init は使える。ただ、Docker を載せるだけの VM では差が小さい。テンプレートと Ansible の `common` ロールの作り直しに見合う利点がない。見送り
- その場更新（`do-release-upgrade`）: 手間は小さいが、バックアップがなく戻せない。見送り
- Ubuntu の非 LTS: 半年ごとに入れ替える手間が出る。見送り

## 影響と再検討の条件

- 24.04 のサポート終了（2029 年 4 月）の 1 年前までに、26.04 以降へ移行を終える
- Debian を再検討する条件: snap が実害になった、VM のメモリが逼迫して OS の素のフットプリントが効いてきた、PVE ホストと揃えて運用を単純にしたくなった
- VM のバックアップ（`vzdump` など）を入れたら、その場更新も選べる

詳細: [インフラ構成](../architecture/02-infrastructure.md)、[見送り中の項目](../operations/roadmap/03-deferred.md)
