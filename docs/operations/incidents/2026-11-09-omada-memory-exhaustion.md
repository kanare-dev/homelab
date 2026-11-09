# INC-2026-11-09: vm-omada がメモリ枯渇で固まり、Omada の画面と監視が止まった

| 項目 | 内容 |
| --- | --- |
| 状態 | **対応中**（再起動で復旧済み。恒久対応の反映（`make setup-omada`、`terraform apply`）と、その後の観察が残る。§5） |
| 発生 | 2026-11-09 06:11 ごろ（node_exporter の最後のスクレイプ。VM が応答しなくなった）。メモリの逼迫は 01:46 から |
| 発見 | 2026-11-09 朝（運用者が Slack の通知で気づいた。就寝中のため、夜間は対応していない） |
| 復旧 | 2026-11-09 08:59 ごろ（Proxmox から `qm reset 112` で強制再起動） |
| 直接原因 | `vm-omada`（3GB、スワップ無し）の利用可能メモリが 90MB 前後（約 3%）まで減ったまま、約 4.5 時間続き、**スラッシング**（プログラムのページを読み直し続ける状態）で VM が固まった |
| 根本原因 | Omada コントローラー（Java と MongoDB を同梱）のメモリの**上限が無かった**。Java ヒープ最大 1GB と MongoDB キャッシュ最大 974MB を足すと、3GB の VM に収まらず、スワップも無いため、緩衝なしで固まった。**推定**（プロセス別の履歴が無く、実測では確認していない） |
| 影響 | 約 2 時間 50 分（06:11〜08:59）、Omada の画面と管理が使えなかった。ER605・SG2210P は設定を持って動き続けた。データ損失は確認されず |

> 書式は [INC-2026-10-22](2026-10-22-lvm-thin-exhaustion.md) に合わせる。**確定（観測した事実）**、**推定**、**未確認**を区別する。blameless。

## 要約

`vm-omada` の利用可能メモリが 01:46 に急減して 90MB 前後になり、`HostMemoryCritical` が 01:48 から約 1 時間おきに通知された。06:11 以降は node_exporter が応答しなくなり、`TargetDown`（06:14）、`ServiceProbeFailed`（06:59）が発火した。

当初は OOM による停止と見られたが、**カーネルの OOM killer は動いておらず**、メモリ不足のスラッシングで VM が固まっていた（ping は通るが、SSH と Omada の画面は応答しない）。

## 1. 調査の方法

VM に SSH できなかったので、次の順に調べた。

1. **VM の外から**: ping（通る）、SSH（バナー交換でタイムアウト）、`qm status 112 --verbose`（`running`。Proxmox 側では異常なし）で、「止まった」のではなく「固まった」と判断した。
2. **Prometheus の履歴**（`vm-monitoring` のコンテナから `query_range` を実行）: `node_memory_*`（利用可能メモリ、`AnonPages`、キャッシュ）、`node_vmstat_oom_kill`、`pgmajfault`、ディスク読み取り、CPU を、11/3〜11/9 の範囲で見た。ここで、**階段状の増加**と、**OOM kill が 0 のまま**であることが分かった。
3. **Alertmanager の API**: 発火中のアラートの `startsAt` を見た（`TargetDown` は 06:14、`ServiceProbeFailed` は 06:59）。
4. **再起動後**に、永続化されていた journald（`journalctl -b -1`）、`sar`（`/var/log/sysstat/sa09`。10 分間隔のシステムのメモリとページング）、Omada の `server.log`・`mongod.log` を読み、`docker exec omada` でイメージの `entrypoint.sh` を見て、メモリの設定の変数があるかを確かめた。

## 2. 時系列

時刻は JST。

| 時刻 | 事象 | 区分 |
| --- | --- | --- |
| 11-03 16:54 | `vm-omada` を起動。この時点で、プロセスのメモリ（`AnonPages`）は約 2.1GB（3GB の約 70%） | 確定 |
| 11-07 00:00 ごろ | `AnonPages` が約 +90MB。以降、戻らない | 確定 |
| 11-08 17:15〜17:45 | `AnonPages` が約 +45MB。以降、戻らない（INC-2026-11-08 の復旧作業と同じ時間帯） | 確定 |
| **11-09 01:46** | `AnonPages` が **1 分で 2,284MB → 2,612MB（+327MB）**。`sar` の確保済みメモリ（`kbcommit`）も同量増えた。一瞬だけ CPU とディスク読み取りが上がり、利用可能メモリが 約 400MB → 約 90MB | 確定 |
| 01:48 | `HostMemoryCritical`（5% 未満が 2 分）が発火。以降、約 1 時間おきに再通知（critical は 1 時間毎） | 確定 |
| 01:46〜06:10 | 利用可能メモリは 90MB 前後のまま。Omada のログに異常なし。MongoDB のスロークエリはゼロ | 確定 |
| 06:05:29〜06:11:54 | Omada の `server.log` の更新が止まる | 確定 |
| 06:10:59 | MongoDB のスロークエリが初めて出る（`omada.user`、`omada.client` など） | 確定 |
| 06:11 | node_exporter の最後のスクレイプ。以降、`up = 0` | 確定 |
| 06:12〜08:59 | journald が `Under memory pressure, flushing caches` を出し続ける | 確定 |
| 06:14 | `TargetDown`（`vm-omada`）が発火（Alertmanager の `startsAt`） | 確定 |
| 06:14〜06:15 | Omada に「スレッドプールが満杯」「DB 操作の失敗」のエラーが連続 | 確定 |
| 06:24 | `sar`: ディスク読み込み 約 1.5GB/s、メジャーフォルト 約 1 万回/秒、ページキャッシュ 12MB | 確定 |
| 06:59 | `ServiceProbeFailed`（`https://omada.lab.kanare.dev`）が発火 | 確定 |
| 朝 | 運用者が Slack の通知で気づく。7:19 ごろの通知を見た（Alertmanager 上の `TargetDown` の開始は 06:14。7:19 は再通知か Slack の表示時刻。**未確認**） | 運用者の報告 |
| 08:59 | `qm reset 112` で強制再起動。Omada が正常に起動 | 確定 |

## 3. 調査結果

### 3.1 OOM ではなく、スラッシング

- `node_vmstat_oom_kill` は、最後のスクレイプ（06:11）まで 0。前回起動分のカーネルログ（`journalctl -b -1 -k`）に、`oom`、`Out of memory`、`Killed process`、`hung task` の記録は**無かった**。
- ping には応答し、`qm status` は `running`、Proxmox の `pressurememory*` は 0（ホスト側の圧力ではない）。ゲストの中だけで起きていた。
- Proxmox の累計のディスク読み取りは約 14TB（稼働 5.7 日）。実行ファイルのページを、追い出されては読み直すことを繰り返した結果と整合する。**推定**。
- ゲストにスワップは無い（`SwapTotal = 0`）。メモリが尽きても、退避先が無く、OOM killer が動く前に、スラッシングで応答できなくなった。

### 3.2 なぜメモリが足りなかったか

| 項目 | 値 | 出典 |
| --- | --- | --- |
| Java ヒープ | 最大 1GB（`-Xmx1024m`。イメージの固定値） | `ps`（再起動後） |
| Java のヒープ外（メタスペース、スレッド等） | 数百 MB | 推定。再起動直後の Java の RSS は約 1.27GB |
| MongoDB（WiredTiger）のキャッシュ | 最大 974MB | `mongod.log` の `cache_size=974M` |
| OS、Docker、node_exporter | 数百 MB | 推定 |
| 合計（最大） | 3GB 近く、または超える | |

- コンテナに `mem_limit` は無く、Java・MongoDB のメモリを絞る設定も無かった（`docker/compose/omada/docker-compose.yml`）。
- 再起動直後で、Java が約 1.27GB、mongod が約 225MB。mongod のキャッシュは、運用するほど埋まる。

### 3.3 階段状に増えて戻らなかった

`AnonPages`: 約 2.1GB（11/3〜11/6）→ 約 2.2GB（11/7）→ 約 2.28GB（11/8）→ 2.61GB（11/9 01:46）。いずれも、増えたあと**戻らなかった**。

- 01:46 の +327MB は、利用者の操作が無い夜間に、1 分で起きた。この前後の `server.log` には、ファームウェア確認とデバイス状態の更新しか無く、原因を示すログは無い。
- **どのプロセスが増えたかは未確認**（プロセス別のメモリの履歴が無い）。Java ヒープの拡張が最有力だが、推定。
- 06:10 ごろの引き金（MongoDB が重いクエリを出し始めたこと）も**未確認**。

### 3.4 通知の挙動

- メモリの警告は、01:48 から出ていた（`HostMemoryCritical`）。運用者は就寝中で、見たのは朝だった。**homelab であり、夜間に起きて対応する運用はしない**（運用者の方針）。通知の経路の問題ではない。
- 01:46〜06:11 の間、VM は固まっておらず、Omada は動いていた。朝に気づいても、再起動までの影響は、06:11〜08:59 の分だった。

## 4. 復旧と恒久対応

### 4.1 復旧（適用済み）

`qm reset 112`（運用者の許可を得て実行）。再起動後に、Omada が起動し、`docker stats` で約 1.46GiB を確認した。データ（`/opt/omada/data`）は、ディスク上にあり、失われなかった。

### 4.2 恒久対応（リポジトリに反映。適用は未了）

| # | 内容 | 場所 | 状態 |
| --- | --- | --- | --- |
| 1 | VM のメモリを 3GB → **4GB** | `terraform/proxmox/terraform.tfvars` | 反映済み（`terraform apply` と VM の再起動は未実施） |
| 2 | Java ヒープの最大を **768MB** | `docker-compose.yml`（`JAVA_MAX_HEAP_SIZE`） | 反映済み（`make setup-omada` は未実施） |
| 3 | MongoDB の WiredTiger キャッシュを **0.25GB** | 同（`MONGOD_EXTRA_ARGS=--wiredTigerCacheSizeGB 0.25`） | 同上 |
| 4 | コンテナの `mem_limit` を **2.5GB**（`memswap_limit` も同じ） | 同 | 同上 |

- 見積り（ピーク）: Java ヒープ 768MB + ヒープ外 約 400MB + MongoDB キャッシュ 256MB + 本体 約 150MB ≒ 1.6GB。OS 側に約 300MB。**4GB の VM に、約 2GB の余裕**ができる。ヒープ外の見積りは**推定**で、実測で確認する（§5 の #3）。
- **スワップは足さない**。コンテナに `mem_limit` が付くので、超えたらコンテナだけが OOM で落ち、`restart: unless-stopped` で戻る（VM は固まらない）。スワップは、固まるまでの時間を延ばすだけで、今回のような「気づかず長時間固まる」状態を、むしろ長引かせる。足りなければ、スワップではなく、上限かメモリを見直す。
- DB の大きさは約 300MB（`/opt/omada/data/db`）。キャッシュ 0.25GB で、大きく困らない見込み。クエリが遅くなれば、0.5GB に上げる。

## 5. アクションアイテム

| # | 内容 | 状態 |
| --- | --- | --- |
| 1 | `terraform apply`（`vm-omada` の 4GB）と `make setup-omada`（コンテナの上限）を適用する | 未実施（運用者の作業。メモリの変更には VM の再起動が要る） |
| 2 | 適用後、`docker stats` と Prometheus で、Java・MongoDB のメモリが、上限の内側に収まることを数日見る | 未実施 |
| 3 | プロセス別のメモリの履歴が無いので、`vm-omada` だけに cAdvisor（コンテナ別）か process-exporter（プロセス別。Java と MongoDB を分けられる）を入れるかを検討する（今回、増えたプロセスを特定できなかった。[バックログ](../roadmap/01-backlog.md)） | 検討中（未決定） |
| 4 | 01:46 の +327MB の正体（Java ヒープの拡張か、別の処理か）を、適用後の観察で確かめる | 未確認 |
| 5 | `HostMemoryLow`（warning）が、固まる前に鳴っていたかを確認する（今回の通知は、`HostMemoryCritical` だけが記録にある） | 未確認 |

## 6. ポストモーテム

- **うまくいったこと**: Prometheus の履歴が、固まる前の増え方を残していた。journald と `sar` が永続化されていて、再起動後に、固まっていた間の様子を読めた。
- **うまくいかなかったこと**: Omada のイメージに、メモリの上限の設定が無いのに、設計時に、VM の大きさとの見合いを見積もらなかった（作った側の不足）。プロセス別のメモリの履歴が無く、増えた原因を特定できなかった。
- **運が良かったこと**: Omada が止まっても、ER605・SG2210P は設定を持って動き続けた。データ損失がなかった。

## 関連ドキュメント

- [Omada コントローラー](../../services/network/omada-controller.md)（メモリの上限、変更履歴）
- [監視・アラート](../../services/platform/monitoring.md)（`HostMemoryLow` / `HostMemoryCritical`、容量の上限設定）
- [インフラ構成](../../architecture/02-infrastructure.md)（VM のメモリ）
- [INC-2026-11-08](2026-11-08-sg2210p-native-vlan-overwrite.md)（前日の障害。コントローラーが Proxmox の上にある件）
