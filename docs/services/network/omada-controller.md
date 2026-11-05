# Omada コントローラー（vm-omada）

Omada コントローラーの詳細設計。ER605・SG2210P・将来の AP を一元管理する。設定の大半はコントローラーの中にあり、Git では管理しない（Open API でのコード化は[検討中](../../operations/roadmap/01-backlog.md)）。**この文書を、設定値の正とする。** 製品の仕様は[ER605](../../hardware/er605/spec.md)・[SG2210P](../../hardware/sg2210p/spec.md)の資料、機器ごとの設定は[ER605 の設定](../../hardware/er605/settings.md)・[SG2210P の設定](../../hardware/sg2210p/settings.md)、移行の手順は[移行計画](../../operations/roadmap/10-er605-sg2210p-migration-plan.md)にある。

> [!NOTE]
> 作成日は 2026-11-03。**秘密の値（管理者のパスワード、バックアップの暗号化の鍵、TP-Link ID のパスワード）と、機器の MAC アドレスは書かない**（リポジトリは公開）。Keychain の名前は `private/secrets-inventory.md`（台帳）にある。

## 運用

- コントローラーまたは機器の設定を変えたら、**同じ変更でこの文書（と、機器の文書）を更新**し、[変更履歴](#変更履歴)に 1 行足す。
- 設定を変えたあとは、手動バックアップを取る。画面の Settings > Maintenance の「Backup & Restore」で保存する（メニューの名前は 6.3 で未確認）。保存先は iCloud Drive の `homelab/`（暗号化なし。運用者が受け入れ。[バックログ](../../operations/roadmap/01-backlog.md)）。ファイル名は `omada-bk-YYYYMMDD.cfg`（案）。直近の 3 世代ほどを残す。
- 自動バックアップは、毎週日曜 03:00（`vm-omada` の `/opt/omada/data/autobackup`）。VM のディスクの中なので、VM が壊れると一緒に失われる。
- 画面には、`ssh -L 8043:localhost:8043 vm-omada` のあと `https://localhost:8043` で入る（`omada.lab.kanare.dev` は未作成。段階 1・2 のあとに作る）。

## 構成

| 項目 | 値 |
| --- | --- |
| VM | `vm-omada`（VMID 112、`192.168.11.12`。VLAN 化のあとは `10.77.10.3`、VLAN10）。2 vCPU、メモリ 3GB、ディスク 20G。起動は自動（順序 6） |
| コントローラー | Omada Controller 6.3.0.111。Docker（`mbentley/omada-controller:6.3.0.111`、host ネットワーク）。`docker/compose/omada/docker-compose.yml`、Ansible の `omada.yml` |
| データ | `/opt/omada/data`、ログ `/opt/omada/logs` |
| 反映 | `make setup-omada` |
| ポート | 管理 HTTPS 8043、管理 HTTP 8088、ポータル 8843。機器との通信は UDP 29810（自動検出）、TCP 29811〜29816。UFW で絞る（`ansible/inventory/group_vars/omada/vars.yml`） |
| 監視 | `node_exporter` を Prometheus が見ている（`TargetDown`）。画面（HTTPS）の外形監視は未導入（[監視・アラート](../platform/monitoring.md)） |

## 設定値（現在）

| 項目 | 値 |
| --- | --- |
| 管理者アカウント | パスワードは Keychain（`homelab / omada admin`） |
| サイト | 1 つ。名前は未確認 |
| LAN（Settings > Wired Networks > LAN） | `192.168.11.1/24`、DHCP `.60`〜`.99`、リース 48 時間、DNS は `192.168.11.11` だけ（2026-11-03 に運用者が設定。画面の値は未確認） |
| 採用している機器 | なし（2026-11-03 に、ER605 を一度採用して更新し、取り外した）。段階 1・2 で ER605 と SG2210P を採用する予定 |
| Omada Cloud（クラウドアクセス） | **有効**（試用中。最終的に無効にするかもしれない。[外部サービスの表](../../architecture/03-network.md#外部サービスへの依存)）。TP-Link ID は台帳 |
| Open API | 使っていない |
| 時刻（NTP）、地域、自動更新 | 未確認 |

## 見直したい項目・未確認

- 自動バックアップの保存先を、`vm-omada` の外にも広げるか（[バックログ](../../operations/roadmap/01-backlog.md)）。
- Omada Cloud を使い続けるか。
- 設定のコード化（Open API、コミュニティ製の Terraform プロバイダー）。
- サイト名、時刻、地域、自動更新の設定値を、画面から書き写す。

## 変更履歴

| 日付 | 内容 |
| --- | --- |
| 2026-11-03 | `vm-omada` を立てた（6.3.0.111）。ER605 を一度採用してファームウェアを更新し、取り外した |
| 2026-11-03 | コントローラーの LAN の設定を、ER605 の LAN に合わせた（運用者の申告）。採用前のバックアップを iCloud Drive に保存した |
| 2026-11-03 | この文書を作成 |
