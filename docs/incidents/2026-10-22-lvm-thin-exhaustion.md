# INC-2026-10-22: Proxmox LVM-thin プール枯渇による全 VM 停止

| 項目 | 内容 |
|---|---|
| 状態 | **暫定復旧済み（15:00）**・恒久対応と根本調査は継続中 |
| 発生日 | 2026-10-22（枯渇の正確な時刻は未特定） |
| 発見 | 2026-10-22 01:00 頃（iPhone から `home.lab.kanare.dev` に到達不能） |
| 調査実施 | 2026-10-22 14:54 JST 時点の PVE ホスト読み取り専用調査 |
| 影響 | VM 6 台が `io-error` で一時停止。DNS・監視・アプリ・開発環境・Windows すべて停止 |
| 直接原因 | `local-lvm`（thin pool `pve/data`）の Data% が 100% に到達 |
| 根本原因 | 後述「根本原因分析」参照（オーバープロビジョニング + discard 未設定 + 容量監視なし） |

> 本ドキュメントはポストモーテム兼用の時系列記録。**確定（観測した事実）**と**推定**と**未確認**を区別して書く。
> 復旧後に「復旧作業」「再発防止の実装結果」「ポストモーテム」を追記する。

## 1. 時系列

| 時刻 (JST) | 事象 | 区分 |
|---|---|---|
| 〜2026-10-22 | thin pool が徐々に消費され 100% に到達（時刻不明。PVE のカーネルログに該当記録なし） | 推定 |
| 10-22 01:00 頃 | iPhone から内部ドメイン・外部サイトとも名前解決できず障害に気づく | 確定 |
| 10-22 午前 | Proxmox UI で VM 6 台 `io-error`、`local-lvm` 100% を確認 | 確定 |
| 10-22 14:54 | PVE に SSH し読み取り専用で調査（本ドキュメント §2） | 確定 |
| 10-22 14:56:46 | `lvextend -L +14G pve/data` 実行。141.6 → 155.6 GiB、Data% 100 → 91.00 | 確定 |
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
| 8 | VM 稼働 約 104 日で徐々に蓄積した可能性が高い | 推定 | uptime ≈ 8,960,000 秒（約 103.7 日）で全 VM 無停止、discard なし |

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
- 結論: **discard を有効化し `fstrim` を実行すれば、pool の使用量は理論上 50 GiB 前後まで下がる見込み**（vm-windows を除く）。

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

- [ ] 枯渇した正確な時刻と、増加の速度（VM 復旧後、Prometheus の過去データがあれば `node_filesystem_*` から推定）
- [ ] 各 VM 内での実使用量と、割当 (Data%) との差（discard 未設定の影響量）
- [ ] vm-monitoring が 90% 割当の理由（TSDB / Docker ログ / イメージ）
- [ ] vm-windows の消費（Windows Update 等）
- [ ] `ubuntu-cloud`(9000) が停止している理由（テンプレートなら正常）

## 7. 教訓（暫定）

1. 利用者から見える症状（DNS 不達）と原因（基盤ストレージ枯渇）は別の階層にあった。下位から調べる。
2. thin provisioning は「ゲスト内の使用率」と「プールの使用率」が別物。プールを直接監視しなければ気づけない。
3. discard が無いと thin pool の割当は減らない。オーバープロビジョニングと組み合わさると枯渇は時間の問題になる。
4. 「アラートが機能していなかった」と思い込んでいたが、実際は**そもそも存在しなかった**。仮説を前提にせず設定を確認する。
5. 監視基盤が障害対象と同じ基盤にあると、障害時に通知も止まる。

## 8. ポストモーテム（復旧後に記入）

- 復旧時刻 / 総停止時間:
- 実施した復旧操作:
- 実際の根本原因（VM 内調査の結果）:
- うまくいったこと / いかなかったこと:
- 再発防止の実装結果とアクションの担当・期限:
