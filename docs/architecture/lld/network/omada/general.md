# 一般設定（Omada のパラメーターシート）

画面の場所は、サイト > 構成 > ネットワーク設定 > 一般設定（サイト設定、SSH、スケジュール、mDNS、VoIP、CLI 設定、SNMP）である。実機の値は [`snapshot/general.json`](snapshot/general.json) にある。表の読み方は [README](README.md#表の読み方) にある。

| 画面 | 使っているか |
| --- | --- |
| サイト設定 | 使う（[下の節](#サイト設定)） |
| SSH | 使わない（[下の節](#ssh)） |
| スケジュール | 使わない（再起動・更新のスケジュールは無い） |
| mDNS | ルールを作ってあるが、無効（[下の節](#mdns-の中継)） |
| VoIP、CLI 設定 | 使わない（書き出していない） |
| SNMP | 使わない（[下の節](#snmp)） |

## サイト設定

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `site.name` | `kanare-homelab` | サイトの名前 | 2026-11-06 に決めた |
| `site.region` | `Japan` | 国・地域 | |
| `site.timeZone` | `Asia/Tokyo` | タイムゾーン（画面の表記は「(UTC+09:00) 大阪、札幌、東京」） | 2026-11-06 に確認 |
| `site.scenario` | `General` | 用途（シナリオ） | 既定 |
| `site.dst.enable` | `false` | 夏時間 | 日本に夏時間は無い |
| `site.ntpEnable` / `ntp.ntpEnable` | `true` | 機器に NTP の時刻を配る | 2026-11-06 に設定 |
| `site.ntpServers` | `ntp.nict.jp` | NTP のサーバー | ER605・SG2210P に配る時刻 |
| `led.enable` | `true` | 機器の LED（サイト全体） | 既定。機器ごとの設定は「サイトの設定に従う」 |
| `lldp.lldp.enable` | `true` | LLDP（隣の機器の情報を交換する） | 既定 |

## デバイスアカウント

ER605・SG2210P に共通の管理者のアカウントである（サイト設定 > デバイスアカウント）。機器に直接入るとき（Omada Discovery Utility、SSH、単体の動作に戻したときの本体の画面）に使う。パスワードを変えると、全機器に反映される。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `device-account.username` | `admin` | 管理者の名前 | 既定 |
| パスワード | （書かない） | | Keychain（台帳）。書き出しでは落としている |

> [!WARNING]
> Open API の Viewer の権限でも、このパスワードが平文で読める（2026-11-28 に確認）。危険と対策は [Omada コントローラーと管理対象機器](../omada-controller.md#viewer-の権限で機器のパスワードが読める危険)にある。

## SSH

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `ssh.sshEnable` | `false` | 機器の SSH を有効にする | 使わない。設定はコントローラーから行う |
| `ssh.sshServerPort` | `22` | SSH のポート | 既定 |
| `ssh.layer3Access` | `false` | ほかのサブネットから SSH で入れる | 既定 |

## SNMP

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `snmp.snmpV1V2CEnable` | `false` | SNMP v1・v2c | 使わない。機器の状態は omada-exporter が Omada の API から読む（[ADR-0039](../../../../adr/0039-omada-metrics-via-omada-exporter.md)） |
| `snmp.snmpV3Enable` | `false` | SNMP v3 | 使わない |
| `snmp.contact` / `snmp.location` | 空 | 連絡先・場所 | |

## リモートログ

画面の場所は、ネットワーク設定ではなく、ログ > 設定 > アドバンス > リモートログである。API では、サイトの設定として読める。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `remote-logging.remoteLog.enable` | `false` | 機器のログを syslog で送る | 受け手がまだ無い。syslog の収集は[ロードマップ 14](../../../../operations/roadmap/14-syslog-collection.md) で検討中。ゲートウェイ ACL のログを使うにも、これが要る |
| `remote-logging.remoteLog.port` | `514` | syslog のポート | 既定 |
| `remote-logging.remoteLog.moreClientLog` | `false` | クライアントのログも送る | 既定 |

## mDNS の中継

API の呼び方を確かめていないので、書き出していない。値は、画面で見たものを手で書いている（2026-11-11 に作成。運用者の報告）。

| 項目 | 値 | 理由・備考 |
| --- | --- | --- |
| ルール | `mdns-trusted-iot`（**無効**） | テレビを IoT に移すときに有効にして、実機で確かめる |
| Bonjour サービス | AirPlay と Google Cast | Google Cast は一覧に無いので、`Google Cast` / `_googlecast._tcp.local` を追加した（サービス ID は `_A._B.local` の形）。`_googlezone._tcp` などの追加が要るかは、有効にするときに確かめる |
| バンド VLAN | VLAN ID 別 | |
| サービスネットワーク VLAN | 50（IoT） | 機器（テレビなど）を置く側 |
| クライアントネットワーク VLAN | 30（Trusted） | 操作する端末の側 |
