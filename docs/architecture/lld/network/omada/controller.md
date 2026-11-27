# コントローラー（Omada のパラメーターシート）

コントローラー全体の設定（グローバルの設定、アカウント、Open API）である。サイトの設定は、ほかの文書にある。実機の値は [`snapshot/controller.json`](snapshot/controller.json) にある。表の読み方は [README](README.md#表の読み方) にある。コントローラーの VM、コンテナ、メモリの上限は、[Omada コントローラーと管理対象機器](../omada-controller.md#構成)にある。

## アカウント

API では読んでいない（書き出していない）。画面で見た値を、手で書いている。パスワードは Keychain（名前は台帳）にあり、ここには書かない。

| 項目 | 値 | 理由・備考 |
| --- | --- | --- |
| ローカルユーザー | `homelab-owner`（Owner。日常に使う）、`homelab-admin`（Super Admin。予備） | 名前をメールアドレスの形にしない（下の注） |
| 監視用のユーザー | `exporter`（Viewer。サイト `kanare-homelab`） | 2026-11-27 に作成。パスワードは SOPS の `omada_exporter_password`（[ADR-0039](../../../../adr/0039-omada-metrics-via-omada-exporter.md)） |
| Cloud User | TP-Link ID 名義の Owner | Omada Cloud 用。名前は変更できない仕様。TP-Link ID は台帳 |
| Open API のアプリ | `exporter`（Client Credentials モード、Viewer ロール） | 2026-11-27 に作成。omada-exporter と `tools/omada-export.py` が使う。Client ID とシークレットは SOPS（`omada_exporter_client_id`、`omada_exporter_client_secret`）。最初は Authorization Code モードで作ってしまい、トークンの取得が `-44106` で失敗したので、Client モードに直した。画面の場所は、Settings > Platform Integration > Open API |

> [!NOTE]
> Cloud Access が有効だと、ログイン画面に **TP-Link ID と同じ名前**（メール形式）を入力すると、ローカルユーザーではなくクラウド側で認証され、Cloud User のセッションになる（ログは `cloud tenant login strategy`）。このセッションは、ユーザーごとの設定（言語・テーマ・24 時間表記）を保存できず、`Account unauthorized`（`-90021`）になる。ローカルユーザーの名前を別の名前（`@` を含まない）にすると、`local tenant login strategy` で入れて保存できる。2026-11-09 に、ローカルの Owner を `homelab-owner` に改名して確認した。

## 全体の設定

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `general.name` | `kanare-homelab` | コントローラーの名前 | |
| `general.region` / `general.timeZone` | `Japan` / `Asia/Tokyo` | 国・地域、タイムゾーン | |
| `general.dst.enable` | `false` | 夏時間 | 日本に夏時間は無い |
| `syslog.enable` / `syslog.port` | `false` / `514` | コントローラー自身のログを syslog で送る | 受け手がまだ無い（[ロードマップ 14](../../../../operations/roadmap/14-syslog-collection.md)） |
| `webhook` | なし | Webhook の送り先 | 使わない。通知は Prometheus と Alertmanager で行う |

## データの保持（retention）

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `fiveMin` | `2` | 5 分ごとの時系列を残す日数（2 日で固定） | 変えられない |
| `hourly` | `7` | 1 時間ごとの時系列を残す日数 | 既定。選べるのは 7 日だけ |
| `daily` | `90` | 1 日ごとの時系列を残す日数（90、180、365 から選ぶ） | 既定。長い期間は Prometheus（omada-exporter）で見る |
| `weekly` | `180` | 1 週ごとの時系列を残す日数 | 既定 |
| `clientHistory` | `31` | クライアントの履歴を残す日数 | 既定 |
| `knownClient` | `1` | 既知のクライアントのデータを残す日数 | 既定 |
| `log` | `31` | ログを残す日数 | 既定 |
| `clientsDataEnable` / `clientDataTrendEnable` | `false` / `false` | クライアントの履歴データ・傾向を記録する | 既定 |
| `portalAuth`、`rogueAp`、`widsData` | `31` | ポータルの認証、不正な AP、無線の IDS のデータを残す日数 | 既定。使う機能は無い |

コントローラーは、2026-11-09 にメモリが尽きて固まったことがある（[INC-2026-11-09](../../../../operations/incidents/2026-11-09-omada-memory-exhaustion.md)）。保持の日数を延ばすと、MongoDB の量とメモリが増えるので、延ばすときは容量を見る。

## 機器へのアクセス（device-mgmt）

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `webControlHttp` | `true` | 機器の Web 画面（HTTP）に入れる | 既定。採用中の機器の画面は、開けても設定を変えられない |
| `webControlHttps` | `true` | 機器の Web 画面（HTTPS）に入れる | 既定 |
| `appDiscovery` | `true` | アプリから機器を見つけられる（HTTPS の画面とセット） | 既定 |

## 書き出しに無い設定

| 項目 | 値 |
| --- | --- |
| デバイス管理アクセス（システム設定） | 有効。ホスト名/IP は `10.77.10.3`（2026-11-19 から）。機器がコントローラーにつなぐ住所である |
| Omada Cloud（クラウドアクセス） | **有効**（試用中。最終的に無効にするかもしれない。[外部サービスの表](../../../hld/05-network.md#外部サービスへの依存)） |
| コントローラー本体の NTP | 指定する欄が無い（6.3.0.111。2026-11-06 に確認）。時刻は、`vm-omada` の OS に従う見込み（未確認） |
| 機器のファームウェアの自動更新 | 未確認。有効だと、機器が自動で更新・再起動する。更新の時機を自分で決めたいので、無効にしたい |
| バックアップのスケジュール | 毎週日曜 03:00（`vm-omada` の `/opt/omada/data/autobackup`）。Viewer の権限では API で読めない |
