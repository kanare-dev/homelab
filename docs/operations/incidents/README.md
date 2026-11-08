# 障害記録

障害の経緯・原因・再発防止を残す。復旧の手順は [Runbook](../runbooks/README.md)、設計の変更は [architecture/](../../architecture/01-overview.md) と [ADR](../../adr/README.md) に書き、ここには**何が起きたか**だけを書く。

## 一覧

| ID | タイトル | 状態 | 発生日 |
| --- | --- | --- | --- |
| [INC-2026-10-22](2026-10-22-lvm-thin-exhaustion.md) | Proxmox LVM-thin プール枯渇による全 VM 停止 | 解決済み | 2026-09-09 |
| [INC-2026-10-22-b](2026-10-22-pve-webui-broken-by-ansible-patch.md) | Ansible のパッチで `proxmoxlib.js` が壊れ、PVE の管理画面が開けなくなった | 解決済み | 2026-10-22 |
| [INC-2026-10-25](2026-10-25-nic-hardware-unit-hang.md) | PVE ホストの NIC（e1000e）が送信停止し、LAN と全 VM が使えなくなった | 対応中 | 2026-10-25 |
| [INC-2026-11-08](2026-11-08-sg2210p-native-vlan-overwrite.md) | Omada で VLAN を作った操作で、SG2210P の p2 の Native が書き換わり、Proxmox と全 VM が LAN から消えた | 解決済み | 2026-11-08 |

## 書き方

- ファイル名は `YYYY-MM-DD-<英語のタイトル>.md`。日付は発生日。ID は `INC-YYYY-MM-DD` で、同じ日に複数あれば `-b`、`-c` を付ける。
- 書式は [INC-2026-10-22](2026-10-22-lvm-thin-exhaustion.md) に合わせる。冒頭の表（状態・発生・発見・復旧・直接原因・根本原因・影響）、要約、時系列、調査結果、原因分析、対応、アクションアイテム、ポストモーテム、関連ドキュメントの順に書く。
- **確定（観測した事実）**、**推定**、**未確認**を区別する。時刻が分からないときは推測せず「未確認」と書く。
- blameless。個人ではなく仕組みを対象にする。
- 機密値（トークン、パスワードなど）は書かない。
- 記録を追加したら、この表と [docs/README.md](../../README.md)、[Runbook の README](../runbooks/README.md) の障害記録へのリンクを更新する。再発防止で構成を変えたら [04-reliability.md](../../architecture/04-reliability.md) の表にも足す。
