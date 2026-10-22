# INC-2026-10-22: Proxmox LVM-thin プール枯渇による全 VM 停止

| 項目 | 内容 |
|---|---|
| 状態 | **復旧済み**（2026-10-22 14:56:46 に pool 拡張、15:30 頃までに全 VM を discard 有効で再起動）。恒久対応の一部が未完（§8.6） |
| 発生 | **2026-09-09 18:49:21 JST**（thin pool が `out-of-data-space` に遷移。PVE カーネルログで確認） |
| 発見 | 2026-10-22 01:00 頃（iPhone から `home.lab.kanare.dev` に到達不能）。**発生から約 42 日 6 時間後** |
| 調査実施 | 2026-10-22 14:54 JST 時点の PVE ホスト読み取り専用調査 |
| 影響 | VM 6 台が `io-error` で一時停止し、**約 42 日 20 時間**（9/9 18:49 → 10/22 14:56）サービス停止。DNS・監視・アプリ・開発環境・Windows すべて |
| 直接原因 | `local-lvm`（thin pool `pve/data`）の Data% が 100% に到達 |
| 根本原因 | 後述「根本原因分析」参照（オーバープロビジョニング + discard 未設定 + 容量監視なし） |

> 本ドキュメントはポストモーテム兼用の時系列記録。**確定（観測した事実）**と**推定**と**未確認**を区別して書く。
> 復旧後に「復旧作業」「再発防止の実装結果」「ポストモーテム」を追記する。

## 1. 時系列

| 時刻 (JST) | 事象 | 区分 |
|---|---|---|
| 2026-07-10 21:50 | PVE ホスト起動（以降、再起動なし） | 確定 |
| 2026-09-09 18:49:21 | `device-mapper: thin: reached low water mark` → `switching pool to out-of-data-space (queue IO) mode`。以降、書き込みが待たされる | 確定 |
| 2026-09-09 18:50:24 | `switching pool to out-of-data-space (error IO) mode`。書き込みがエラーになり、QEMU が VM を `io-error` で一時停止 | 確定 |
| 2026-09-09 〜20:00 | 各ゲストのログと Prometheus のデータ（最後のブロックは 19:00〜21:00）がここで途切れる | 確定 |
| 2026-09-10 〜 10-22 | **約 42 日間、VM 全停止のまま気づかれず**。アラートなし | 確定 |
| 10-22 01:00 頃 | iPhone から内部ドメイン・外部サイトとも名前解決できず障害に気づく | 確定 |
| 10-22 午前 | Proxmox UI で VM 6 台 `io-error`、`local-lvm` 100% を確認 | 確定 |
| 10-22 14:54 | PVE に SSH し読み取り専用で調査（本ドキュメント §2） | 確定 |
| 10-22 14:56:46 | `lvextend -L +14G pve/data` 実行。141.6 → 155.6 GiB、Data% 100 → 91.00 | 確定 |
| 10-22 14:56:46 | PVE カーネル: `switching pool to write mode`（pool 拡張を検知し復帰） | 確定 |
| 10-22 14:56:55 | `qm resume 111`（vm-infra）。DNS（内部・外部）が回復 | 確定 |
| 10-22 14:57:29〜14:58:32 | 113 → 120 → 122 → 121 → 130 の順に `qm resume`（各 15 秒間隔） | 確定 |
| 10-22 14:59 | 全 6 VM `running`。Homepage 200、Prometheus/Grafana 200、Windows ゲストエージェント応答 | 確定 |
| 10-22 午後 | 全 6 VM の `scsi0` に `qm set ... discard=on,ssd=1` を設定（再起動まで保留） | 確定 |
| 10-22 午後 | vm-dev(121) を shutdown → start → `fstrim -av`。ゲスト `/` で 24 GiB を trim。vm-dev ディスク割当 59.56% → 17.45%、pool 91.75% → 83.63% | 確定 |
| 10-22 午後 | 許可設定追加後、vm-apps(120)・vm-code(122)・vm-monitoring(113)・vm-infra(111) を順に shutdown → start → `fstrim -av`、`fstrim.timer` 有効化。trim 量: apps 33.9 / code 22.5 / monitoring 32.3 / infra 10.8 GiB | 確定 |
| 10-22 午後 | vm-windows(130): ACPI shutdown は即時完了せず（`VM quit/powerdown failed` 表示後に停止）。起動後 `Optimize-Volume -ReTrim` は "Not Supported"。ゲスト使用 34 GiB / 割当 35 GiB で回収余地は小さく問題なし | 確定 |
| 10-22 午後 | 全 VM 再起動完了。pool Data% 91.75 → **44.76**（Meta% 2.81）。Prometheus/Grafana 200、DNS・Homepage 正常 | 確定 |

## 2. 調査結果（2026-10-22 14:54 時点・読み取りのみ）

### 2.1 thin pool

```
data              141.60g  Data% 100.00  Meta% 4.28   (twi-aotzD-)
```

- **Data% が 100%、Metadata% は 4.28%**。枯渇したのはデータ領域でありメタデータではない。
- VG `pve` は 237.47 GiB で **未割当 (VFree) が 16.00 GiB** ある → プール拡張の余地あり。
- 物理ディスク (`nvme0n1`) の SMART は PASSED。ハード故障ではない。
- 記録上のストレージ状態: `local-lvm` 148,480,000 KiB / 使用 100% / 空き 0。`local`(dir) は 24% で余裕あり。

### 2.2 ディスクごとの消費（thin pool への実割当）

| VMID | 名前 | 仮想サイズ | Data% | 実割当(概算) |
|---|---|---:|---:|---:|
| 111 | vm-infra | 20 GiB | 92.21% | 18.4 GiB |
| 113 | vm-monitoring | 40 GiB | 90.36% | 36.1 GiB |
| 130 | vm-windows | 60 GiB | 60.00% | 36.0 GiB |
| 121 | vm-dev | 30 GiB | 59.50% | 17.9 GiB |
| 120 | vm-apps | 40 GiB | 41.29% | 16.5 GiB |
| 122 | vm-code | 30 GiB | 49.54% | 14.9 GiB |
| 9000 | ubuntu-cloud (テンプレート) | 3.5 GiB | 50.91% | 1.8 GiB |
| | **合計** | **223.5 GiB** | | **≈141.6 GiB** |

- **仮想ディスクの合計 (223.5 GiB) が thin pool (141.6 GiB) の約 1.6 倍** = 大幅なオーバープロビジョニング。各 VM が自分のディスク全体を使い切る方向に進めば、必ずプールが先に枯渇する構造だった。
- vm-infra (92%) と vm-monitoring (90%) は**自分のディスクのほぼ全域が割当済み**。VM 内の実使用量が本当にそこまで多いのか、削除済みブロックが返却されていないだけなのかは**未確認**（VM が停止中のため内部を確認できない）。

### 2.3 設定の問題（確定）

- **全 VM ディスク (`scsi0`) に `discard=on` が設定されていない**（`qm config` で確認）。VM 内でファイルを削除しても、thin pool 側の割当は戻らない。割当は単調増加し、時間とともにほぼ必ず上限に張り付く。
- **スナップショットは存在しない**（全 VM `current` のみ）。スナップショット起因の消費という仮説は**否定**。
- **vzdump バックアップのジョブ・ファイルなし**（`/var/lib/vz/dump` は空、`/etc/pve/jobs.cfg` なし）。VM のバックアップが存在しないため、復旧操作は慎重にする必要がある。
- Terraform (`terraform/proxmox/modules/vm/main.tf`, `windows.tf`) のディスク定義に discard の指定なし → 設定が IaC に起因して欠けている。
- LVM の `thin_pool_autoextend_threshold` は未設定（`/etc/lvm/lvm.conf` に該当行なし）。自動拡張も効かない。

### 2.4 監視の状態（リポジトリ確認）

- `docker/compose/monitoring/prometheus/prometheus.yml` に **`rule_files` も `alerting` もない**。Alertmanager も未導入。**そもそもアラートが 1 つも存在しなかった**（「機能していなかった」ではなく「無かった」）。
- node_exporter は pve を含む 5 台を収集しているが、**標準の node_exporter は LVM thin pool の Data% を出さない**。pve の `/` や `local` の使用率は見えても、今回枯渇した領域は監視対象外だった。
- `vm-code` (122) と `vm-windows` (130) は scrape 対象に入っていない。
- Prometheus は `retention.time=30d` のみで `retention.size` なし。`prom/prometheus:latest` を使用。
- Docker のログローテーション設定 (`logging: max-size`) はリポジトリ内のどの compose にも**ない**。

## 3. 根本原因分析

### 直接原因（確定）
thin pool `pve/data` の Data% が 100% に到達し、VM の書き込みが失敗、QEMU が 6 VM を `io-error` で一時停止した。

### 要因の整理

| # | 要因 | 区分 | 根拠 |
|---|---|---|---|
| 1 | thin pool がオーバープロビジョニング（223.5 GiB / 141.6 GiB） | 確定 | `lvs` と `qm config` |
| 2 | discard 無効で削除分が返却されない | 確定 | 全 `scsi0` に discard なし |
| 3 | thin pool 容量のアラートが存在しない | 確定 | prometheus.yml に rules なし |
| 4 | thin pool Data% を取得するメトリクスがない | 確定 | node_exporter 標準では不可 |
| 5 | 監視基盤自身が同一 pool 上にあり、同時に停止する | 確定 | vm-monitoring も `io-error` |
| 6 | 外部の死活監視・通知経路がない | 確定 | 通知基盤自体が未導入 |
| 7 | 実際にどの VM のどのデータが増えたか | **未確認** | VM 復旧後に調査 |
| 8 | PVE 起動（7/10）から約 61 日で pool が満杯になった（割当が増え続けた） | 確定 | PVE カーネルログ（9/9 18:49:21）。ただし何が増えたかは不明（#7） |
| 9 | 発生から発見まで約 42 日、気づく手段がなかった | 確定 | 通知なし。リポジトリの最終コミットは 7/22 で、利用頻度が低かったことが背景にある可能性（推定） |

### 当初仮説の評価

| 仮説 | 評価 |
|---|---|
| スナップショットの蓄積 | **否定**（存在しない） |
| TRIM/discard 未設定 | **確定**（要因 2）。ただし単独で原因とは言えず、実使用量との差は VM 復旧後に確認 |
| Prometheus TSDB / Docker ログ / 各種キャッシュ | 未確認（vm-monitoring が 90% で有力候補。VM 内確認待ち） |
| Windows の消費 | 未確認（60GiB 中 36GiB 割当。起動後に確認） |

## 3.5 復旧後の追加調査結果（VM 内の実使用量）

| VM | ゲスト内 `/` 使用量 | thin pool 割当（実測） | 差（回収可能の目安） |
|---|---:|---:|---:|
| vm-infra | 8.8 GiB | 18.4 GiB | ≈ 9.6 GiB |
| vm-monitoring | 5.5 GiB | 36.1 GiB | ≈ 30.6 GiB |
| vm-apps | 3.9 GiB | 16.5 GiB | ≈ 12.6 GiB |
| vm-dev | 4.1 GiB | 17.9 GiB | ≈ 13.8 GiB |
| vm-code | 5.6 GiB | 14.9 GiB | ≈ 9.3 GiB |
| vm-windows | 未調査 | 36.0 GiB | 未調査 |

- **ゲストの実データは合計でも約 28 GiB。それに対し 5 VM で約 97 GiB が割当済み**。差の約 76 GiB は、一度書かれた後に削除されたが discard されず pool に残ったブロック（推定の根拠は discard 未設定＋ゲスト内容量との乖離）。
- 特に vm-monitoring は実使用 5.5 GiB で、Docker volume も約 1.2 GiB。**容量を食っていたのは「データの増加」ではなく「回収されない割当」**。仮説（Prometheus TSDB 肥大化等）は否定的。
- 各ゲストは `/` が `rw` で、`dmesg` に I/O エラーや FS 再マウントの記録なし（ファイルシステム破損の兆候は確認できず）。
- 割当が積み上がった要因の候補（推定・未検証）: apt/Docker イメージの更新・ビルドキャッシュ、ログのローテーション等の書き換え・削除の繰り返し。vm-infra の Docker build cache 2.2GiB（reclaimable 2.1GiB）も一例。
- **ゲストの時計・稼働時間のずれ**: 復旧後、各ゲストの uptime が PVE から見たプロセス稼働時間より約 42.8 日短かった。ゲストが一時停止中は時間が進まないため、VM 全台が 9/9 から止まっていた裏付けになる（vm-monitoring のカーネルログにも `Long readout interval ... cs_nsec: 3697033686022505`（≈42.79 日）が記録されている）。復旧後は NTP で全ゲストが同期済み。
- **Prometheus**: 9/9 夜以降のメトリクスは存在しない。再開時に `Loading on-disk chunks failed ... out of sequence m-mapped chunk` が出て、head の mmap チャンクが破棄された。9/9 の停止直前の数時間分は欠落している可能性がある。永続化済みのブロック（〜9/9 19:00）は健全。
- 結論: **discard を有効化し `fstrim` を実行すれば、pool の使用量は理論上 50 GiB 前後まで下がる見込み**（vm-windows を除く）。

## 3.6 容量増加の有力候補: AdGuard Home のクエリログ

ログ上限の設定前に vm-infra を調べたところ、次の状態だった（確定した事実）。

| ファイル | サイズ | 更新日時（ゲスト時計） |
|---|---:|---|
| `/opt/dns/adguard/work/data/querylog.json.1` | **1,226,913,188 B（約 1.2 GB）** | 2026-09-09 19:15 |
| `querylog.json` | 約 0.5 MB | 10-22（復旧後） |

- 設定は `querylog.interval: 2160h`（**90 日保持**）、`file_enabled: true`。
- `querylog.json.1` の最終更新は pool 枯渇（9/9 18:49）の直後。ローテーションで巨大なファイルを書き換えていた可能性がある（**推定**）。
- ローテーションのたびに GB 単位のブロックを新規に書き込み、旧ブロックは discard されずに pool に残る。これは「書いて消すを繰り返す」典型的な割当増加の仕組みで、約 76 GiB の差の一因として有力。ただし、この 1 件だけで 76 GiB を説明できるわけではなく、他の要因も残る。
- 10-22 に保持を 168h（7 日）へ短縮し AdGuard を再起動すると、`querylog.json.1` は 1.2 GB → 約 0.77 MB に縮小した。

## 4. 暫定対応

実施済み内容を §1 に時系列で記載。VM 内データの削除は行っていない。

### 実施結果

- 拡張: `lvextend -L +14G pve/data`（VG の未割当 16 GiB のうち 14 GiB を使用。VG の空きは 2 GiB に）
- 再開: `qm resume` のみ。強制停止・リセットは行っていない（ゲスト FS を壊さない方針）
- 15:00 時点の pool: 155.6 GiB / Data% 91.69（空き約 13 GiB）

> **注意**: プールはまだ 91% で余裕は小さい。恒久対応（discard 有効化＋fstrim）までは、書き込み量の多い作業を避ける。

### 当初の手順案（参考・実施内容の記録）

### 手順

1. **thin pool を拡張する**（VG の未割当 16 GiB を使用）。メタデータ用の余裕を残すため 12〜15 GiB 程度に留める。

   ```bash
   # 事前確認
   vgs pve; lvs -o lv_name,data_percent,metadata_percent pve/data
   # 拡張 (例: +14G。pool は縮小できないので慎重に)
   lvextend -L +14G pve/data
   ```

2. 空きが出来たことを確認してから VM を復旧する。**強制リセットはせず、まず `qm resume`** を試す。

   ```bash
   qm resume 111   # DNS が最優先。その後 113 → 120 → 122 → 121 → 130
   ```

   resume で戻らない場合のみ、ゲスト FS の状態を見て `qm stop` → `qm start` を判断する。

3. 復旧後、各 VM で `df -h` / `docker system df` / `du` を実行し、**どこが容量を食っているか**を特定する（根本原因 #7）。

4. 各 VM で `fstrim -av` を実行して割当を回収し、続いて §5 の discard 設定を有効化する。

### リスク

- 拡張は +14G 程度では、現状 223.5 GiB のオーバープロビジョニングを解消しない。**暫定的な延命であり、根本対応までは再枯渇し得る**。
- バックアップが無いため、ゲスト FS が破損していた場合に戻せない。復旧前の追加バックアップは、空き容量が無く書き込みが危険なため現実的でない。拡張後に `local` (空き約 48 GiB) へ重要 VM だけ vzdump する選択肢はある。
- 停止期間中の書き込みは各ゲストのメモリ内バッファに残っている可能性があり、強制停止するとそれが失われる。

## 4.5 恒久対応の実装状況（2026-10-22 15:40 時点）

| 対策 | 状態 |
|---|---|
| VM ディスクの discard/ssd（PVE 設定・Terraform） | PVE 設定は適用済み。Terraform は変更済み、`plan` 未確認 |
| `fstrim.timer`（common ロール） | 全 VM で手動有効化済み。ロールへの追加は済み、Ansible 反映は未実施 |
| thin pool / VM io-error メトリクス（`pve-storage-metrics`） | **PVE に適用済み**。`lvm_thin_pool_data_percent` などが node_exporter から取得できる |
| Prometheus アラートルール 11 件（`alerts.yml`） | **vm-monitoring にデプロイ済み**（全ルール health=ok） |
| Alertmanager + Slack 通知 | **デプロイ済み**。テストアラート送信で `alertmanager_notifications_total{integration="slack"}=1`、失敗 0 を確認 |
| Prometheus `retention.size=5GB` / Docker ログ上限（monitoring） | **デプロイ済み** |
| vm-code を Prometheus の scrape 対象に追加 | **デプロイ済み**（up） |

## 5. 恒久対応（案）

| 優先 | 対策 | 実装場所 |
|---|---|---|
| 高 | thin pool Data%/Meta% を Prometheus に出す（textfile collector） | `ansible/roles/node_exporter`（pve 向け） |
| 高 | Prometheus ルール追加（Warning 75% / Critical 90%）+ Alertmanager 導入 | `docker/compose/monitoring` |
| 高 | 通知の経路を確保（Discord/Telegram Webhook）。送信テストする | 同上 |
| 高 | 全 VM ディスクに `discard=on,ssd=1` を設定し `fstrim.timer` を有効化 | `terraform/proxmox`, `ansible/roles/common` |
| 高 | オーバープロビジョニングの解消（pool 拡張 / ディスク縮小 / 不要 VM 削除）。ホストのディスク 237 GiB のうち `root` 69.5 GiB・`swap` 7.5 GiB の配分も見直し | 手動 + docs |
| 中 | `lvm.conf` の `thin_pool_autoextend_threshold` / `percent` 設定（VG に空きがある場合のみ有効） | `ansible/roles/proxmox` |
| 中 | Docker `logging` に `max-size`/`max-file`、journald `SystemMaxUse`、Prometheus `retention.size` | compose / `ansible/roles/common` |
| 中 | vm-code・vm-windows を監視対象へ追加 | `prometheus.yml` |
| 中 | vzdump スケジュール（`local` 以外のストレージ、または外部へ） | PVE / runbook |
| 低 | 外部 Heartbeat（監視 VM 停止も検知）、ホスト側からの死活通知 | **見送り（2026-10-22 判断）**。理由と選択肢は `docs/monitoring.md` に記録 |
| 低 | Runbook に本障害の復旧手順を追記 | `docs/runbook.md` |

## 6. 未確認事項・次の調査

- [x] 枯渇した正確な時刻 → **2026-09-09 18:49:21**（PVE カーネルログ）
- [x] 各 VM 内での実使用量と割当の差 → §3.5（実データ約 28 GiB に対し割当約 97 GiB）
- [x] vm-monitoring の容量 → 実使用 5.5 GiB。TSDB 肥大化ではなかった
- [x] vm-windows → ゲスト使用 34 GiB / 割当 35 GiB。回収余地は小さい
- [ ] **何の書き込み・削除の繰り返しで割当が約 76 GiB 増えたか**。有力候補は §3.6 の AdGuard クエリログ（確定ではない）。他の要因は特定できていない。discard 有効後の増加速度を Grafana で観察する
- [ ] Windows ゲストで discard（TRIM）が実際に有効か（`Optimize-Volume -ReTrim` は Not Supported）
- [ ] `ubuntu-cloud`(9000) が停止している理由（テンプレート VM のため通常は停止で正常）

## 7. 教訓

1. 利用者から見える症状（DNS 不達）と原因（基盤ストレージ枯渇）は別の階層にあった。下位から調べる。
2. thin provisioning は「ゲスト内の使用率」と「プールの使用率」が別物。プールを直接監視しなければ気づけない。
3. discard が無いと thin pool の割当は減らない。オーバープロビジョニングと組み合わさると枯渇は時間の問題になる。
4. 「アラートが機能していなかった」と思い込んでいたが、実際は**そもそも存在しなかった**。仮説を前提にせず設定を確認する。
5. 監視基盤が障害対象と同じ基盤にあると、障害時に通知も止まる。
6. **検知までの時間が最大の損失だった**。復旧は 10 分程度で済んだが、気づくまでに 42 日かかった。
7. **ログを調べるときは期間を広く取る**。初回調査では直近 1 週間だけを見て「該当記録なし」と判断し、発生時刻を誤って推定した（実際は 6 週間前）。時刻の手がかり（Prometheus のデータの途切れ、ゲストの uptime の差）と突き合わせて初めて訂正できた。

## 8. ポストモーテム

blameless（個人ではなく仕組みを対象とする）形式。事実は §1〜§3、ここでは評価と学びをまとめる。

### 8.1 要約

2026-09-09 18:49、Proxmox の LVM-thin プール `pve/data` が満杯になり、全 6 VM が `io-error` で一時停止した。DNS・監視・アプリを含む全サービスが停止したが、通知の仕組みが存在せず、利用者が 10/22 に気づくまで約 42 日続いた。復旧は pool の拡張（+14 GiB）と `qm resume` で数分で完了した。恒久対応として discard の有効化、容量回収、アラートと Slack 通知を導入した。

### 8.2 影響

| 項目 | 内容 |
|---|---|
| 停止期間 | 約 42 日 20 時間（2026-09-09 18:49 〜 10-22 14:56）。復旧後の計画再起動で各 VM が 1〜2 分停止 |
| 影響範囲 | DNS（内部・外部）、Reverse Proxy、Prometheus/Grafana、Homepage、開発・コード環境、Windows。LAN 内クライアントの名前解決もこの間は不安定だった可能性が高い |
| データ | ゲスト FS のエラーは確認できず、データ損失は見つかっていない。Prometheus の 9/9 夜以降のメトリクスは存在しない |
| 副次的影響 | 復旧直後は各ゲストの時計が 42 日遅れていた（NTP で同期済み）。証明書は 9/6 発行で有効期限 12/5 のため影響なし |

### 8.3 検知と対応の評価

| 指標 | 値 |
|---|---|
| 検知までの時間 | **約 42 日 6 時間**（9/9 18:49 → 10/22 01:00 頃）。検知手段はユーザーの手動確認のみ |
| 発見から復旧開始まで | 約 14 時間（調査着手時刻の記録なし） |
| 復旧操作 | 調査開始（14:54）から全 VM の resume 完了（14:58）まで約 4 分 |
| 恒久対応の開始 | 同日（discard 有効化、fstrim、監視導入まで 1 日以内） |

### 8.4 根本原因（5 Whys）

1. **なぜ全サービスが止まったか** → thin pool が満杯になり、VM ディスクへの書き込みが失敗して QEMU が VM を停止したから。
2. **なぜ pool が満杯になったか** → ゲストが書いて消したブロックが pool に返らず、割当だけが増え続けた（実データ約 28 GiB に対し割当約 97 GiB）から。さらに、仮想ディスク合計（223.5 GiB）が pool（141.6 GiB）の約 1.6 倍で、全体が増えれば先に pool が尽きる構成だった。
3. **なぜ返らなかったか** → 全 VM ディスクに `discard=on` を設定しておらず、ゲストの TRIM が pool に届かなかったから。
4. **なぜ気づけなかったか** → thin pool の使用率を測るメトリクスもアラートも存在せず、Alertmanager もなかったから。監視基盤自身も同じ pool 上にあり、障害時に止まる構成だったから。
5. **なぜ設計時に防げなかったか** → VM の作成時に「容量は使用量だけで決まる」と想定し、thin provisioning 固有のリスク（返却されない割当、過剰割当）を設計・チェックリストに含めていなかったから。

### 8.5 うまくいったこと / いかなかったこと / 幸運だったこと

**うまくいったこと**
- Terraform / Ansible / ドキュメントが揃っており、構成の把握と再現が早かった。
- PVE への SSH が生きていて、読み取り専用の調査から始められた。
- 強制リセットをせず、`qm resume` で再開した。ゲスト FS を壊さずに復旧できた。
- VG に未割当 16 GiB が残っており、データ削除なしで pool を拡張できた。
- 復旧後に VM 内の実使用量を調べ、原因が「データ増加」ではなく「割当が返らないこと」だと特定できた。

**うまくいかなかったこと**
- 検知手段がなく、42 日間気づけなかった。
- バックアップ（vzdump）がなく、FS が壊れていた場合に戻せなかった。
- 初回調査で、ログの検索期間を狭く取り、「カーネルログに記録なし」「約 104 日で蓄積」と誤って推定した。後続の調査で訂正した。
- 暫定対応の効果が限定的であること（pool 91%）の説明が必要だった。discard 有効化と fstrim の再起動を、複数回に分けて実施する必要があった。
- Windows の ACPI シャットダウンが遅く、再起動作業が止まった。

**幸運だったこと**
- pool が `error IO` モードに入り QEMU が VM を停止（`io-error`）した。ゲスト内で FS エラーが多発して破損する前に停止した。
- 42 日の停止中に、Let's Encrypt 証明書が失効しなかった（9/6 発行・12/5 期限）。
- 物理ディスクに故障がなかった（SMART PASSED）。

### 8.6 アクションアイテム

期限は提案値（案）。担当は全て kanare。

| # | アクション | 状態 | 期限（案） |
|---|---|---|---|
| 1 | pool を拡張して VM を復旧する | **完了**（10-22） | - |
| 2 | 全 VM ディスクに `discard=on,ssd=1`、各ゲストで `fstrim` と `fstrim.timer` | **完了**（10-22、PVE 設定・手動実行） | - |
| 3 | thin pool / VM 状態のメトリクス収集（`pve-storage-metrics`） | **完了**（10-22） | - |
| 4 | Prometheus ルールと Alertmanager、Slack 通知（テスト通知で動作確認済み） | **完了**（10-22） | - |
| 5 | Prometheus に `retention.size`、monitoring の Docker ログ上限 | **完了**（10-22） | - |
| 6 | `docs/monitoring.md` と Runbook の整備 | **完了**（10-22） | - |
| 7 | Terraform: `terraform plan` で discard の差分を確認し、状態を実機に合わせる | **完了**（10-22）。ディスクの差分なし。vm-windows の `startup_shutdown`（-1 → null）の既存ドリフトのみ残る（今回と無関係、未 apply） | - |
| 8 | Ansible: `common` ロール（fstrim.timer、journald 上限）を全 VM に適用して IaC で固定 | **完了**（10-22） | - |
| 9 | 他の compose（dns / homepage / reverse-proxy）の Docker ログ上限、journald の `SystemMaxUse`、AdGuard のクエリログ保持期間 | **完了**（10-22）。Docker は 10MB×3、journald は 200M/1か月、AdGuard は 90日→7日 | - |
| 10 | vzdump のスケジュール設定 | **見送り**（10-22 判断）。VM は IaC で再現でき、保存先が同一ディスクのため。NAS 追加時に再検討。方針は `docs/runbook.md` |  - |
| 16 | Mac にしかない再現不能データ（Vault パスワード、API トークン等）を iCloud Keychain に退避し、非公開の台帳で管理する。シークレット作成時に登録を促すルールを `CLAUDE.md` に追加 | **完了**（10-22）。台帳・ルール・Keychain 登録とも済み | 10-29 |
| 11 | Grafana に thin pool Data% / 割当比率 / 増加速度のパネルを追加し、割当の増加要因を観察する | **完了**（10-22）。ダッシュボード「Storage / Thin Pool」（14 パネル）。VM ディスク別の割当と増加ペースも表示。観察は継続 | - |
| 12 | オーバープロビジョニング方針（割当合計 / pool の上限）を決め、アラートにする | 未完 | 11-12 |
| 13 | `PveVmStopped` の実機テスト、Alertmanager 送信失敗の検知ルール | 未完 | 11-12 |
| 14 | Windows ゲストで discard が実際に効くか確認 | 未完 | 11-12 |
| 15 | 外部監視（監視 VM・ホスト停止の検知） | **見送り**（理由と選択肢は `docs/monitoring.md`） | 再検討条件に該当した場合 |

### 8.7 再発リスクの評価

| リスク | 評価 |
|---|---|
| thin pool 再枯渇 | **低〜中**。discard 有効化と fstrim で pool 使用率は 44% まで下がり、75% / 90% で Slack に通知される。ただし過剰割当（仮想ディスク合計 223.5 GiB / pool 155.6 GiB）は残っている |
| 監視 VM・PVE ホスト停止の未検知 | **残存**。外部監視を見送ったため、気づくのは症状から。受容したリスク |
| バックアップ不在 | **受容**（VM は IaC で再現可能。再現不能データは VM ではなく Mac にあるため、アクション #16 で対応）。NAS 追加時に再検討 |
| Mac の故障・紛失（vault_password、tfstate 等の喪失） | **高**（今回の検討で判明）。アクション #16 の Keychain 登録で軽減する予定 |
