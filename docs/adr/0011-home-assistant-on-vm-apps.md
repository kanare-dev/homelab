# 0011. Home Assistant を vm-apps に Container 版で置き、設定の YAML だけ Git で守る

- ステータス: 採用
- 日付: 2026-10-26

## 背景

SwitchBot（Hub あり）などの機器を一か所で操作・自動化し、Spotify の再生も画面から操作したい。ロードマップに「Home Assistant の本格運用、SwitchBot の統合」があり、`vm-apps` を常時起動して載せる想定だった。

`vm-apps` に試験導入し、SwitchBot Cloud と Spotify をつないで使い続ける見込みが立ったので、構成管理に載せる。

## 決定

- Home Assistant を `vm-apps` に **Container 版**（Docker Compose）で置く。バージョンを固定し、Ansible（`apps.yml`）で配置する。
- `https://ha.lab.kanare.dev` を Caddy 経由で公開し、`vm-apps` の 8123 は UFW で `vm-infra` からだけ許可する。外形監視に加える。
- バックアップは、**設定の YAML だけを Git で守る**。VM 全体のバックアップは取らない（[ADR-0001](0001-no-vm-backup.md) のまま）。`.storage/` と履歴は守らない。

## 理由

- `vm-apps` は割当 4GB に対して実使用が少なく、Home Assistant（約 370MB）が収まる。ホスト全体の余白（約 1.5GB）を減らさずに済む。
- 既存の構成（Docker Compose、Ansible、Caddy、blackbox）にそのまま乗る。専用 VM を増やすと、ホストのメモリの余白が減る。
- 使う統合（SwitchBot Cloud、Spotify）はクラウド経由で、Container 版で足りる。アドオンを使う予定はない。
- 守りたいのは自動化などの記述（YAML）で、これは Git に置ける。統合の登録や履歴は、再設定すれば戻せるか、失っても困らない。別ストレージがない現状では、これ以上の備えは過剰になる。

## 代替案

| 案 | 採らなかった理由 |
| --- | --- |
| Home Assistant OS の専用 VM | アドオンと標準のバックアップが使える。ただし VM が 1 台増え、メモリの余白（約 1.5GB）を食う。アドオンの必要が出たら再検討する |
| `vm-dev` に置く | 手動起動で、破壊検証用。常時稼働に向かない |
| Supervised 版 | 非推奨。ホスト OS の管理が絡む |
| `.storage/` と履歴も外付けディスクなどに退避する | 別ストレージがない。USB ディスクの導入は、この ADR の範囲外（[バックアップ・復旧](../operations/backup-restore.md)に容量の見積もりがある） |

## 影響と再検討の条件

- **失うもの**: VM を失うと、ユーザー、統合の登録、ダッシュボード、機器の名前、履歴が消える。統合のトークンは再発行して入れ直す。手順は [Home Assistant](../services/home-assistant.md#復旧)。
- **設定の運用**: 画面から編集した自動化は、`make ha-config-pull` で Git に取り込まないと守られない。
- **HTTP の設定**: Home Assistant 2026.10 以降、`http:` は初回だけ YAML から取り込まれ、以後は `.storage/http` が使われる。Caddy を信頼する設定は、初期値のファイルを Git に置いて与える。
- **機器の検出と VLAN**: 現在は同一 LAN で mDNS が届く。[VLAN 設計](../architecture/08-vlan-design.md)に移行すると、Servers の `vm-apps` から Clients・IoT の機器が見えなくなる。クラウド経由の統合は影響しない。Cast や Matter を使うときに、mDNS の中継か、置き場所の変更を決める。
- **同居のリスク**: Homepage と同じ VM を共有する。
- **再検討の条件**: 次のいずれかになったら見直す。
  - アドオンが必要になった（HA OS の専用 VM を検討する）。
  - 別ストレージ（USB ディスク、NAS）を導入した（`.storage/` も含めて守る）。
  - ローカル機器（Cast、Matter、IoT）を使い始めた（VLAN 上の置き場所を決める）。
  - `vm-apps` のメモリが逼迫した。

関連: [Home Assistant](../services/home-assistant.md)、[ADR-0001](0001-no-vm-backup.md)、[ADR-0005](0005-tailscale-only-remote-access.md)
