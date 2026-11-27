# セキュリティ（Omada のパラメーターシート）

画面の場所は、サイト > 構成 > ネットワーク設定 > セキュリティである。実機の値は [`snapshot/security.json`](snapshot/security.json) にある。表の読み方は [README](README.md#表の読み方) にある。

| 画面 | 使っているか |
| --- | --- |
| ACL（ゲートウェイ ACL） | 使う。VLAN の境界の通信を絞る（[下の節](#ゲートウェイ-acl)） |
| ACL（スイッチ ACL、EAP ACL） | 使わない（0 件）。スイッチの中の通信は絞らない。EAP（Omada の AP）は無い |
| URL フィルタリング | 使わない（0 件） |
| アプリケーションコントロール | 使わない（書き出していない。ER605 は対象外の見込み。未確認） |
| ワイヤレス IDS/IPS | 使わない（Omada の AP が無い） |
| ファイアウォール | 既定のまま（[下の節](#ファイアウォール)） |
| IDS/IPS | 無効（`ips.enable` は `false`）。ER605 は対象外の見込み（未確認） |
| 攻撃の防御 | 既定のまま（[下の節](#攻撃の防御)） |
| IP-MAC バインディング | 使わない（0 件） |

## ゲートウェイ ACL

**2026-11-27 に、この節の値で ACL を絞った**（[手順書 27](../../../../operations/runbooks/27-network-acl-tighten.md#実施の記録)。それまでは全許可だった）。方針は[通信ポリシー](../../../hld/05-network.md#通信ポリシー)と [ADR-0034](../../../../adr/0034-acl-for-vlan-boundaries-ufw-for-ports.md)、名前の付け方は [ACL の名前と説明の付け方](../acl.md)にある。画面の場所は、セキュリティ > ACL の「ゲートウェイ ACL」で、方向はすべて LAN → LAN である。リハーサルの `rh-` のルール 7 件は、同じ日に削除した。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `acl-config-mode.mode` | `0` | ゲートウェイ ACL の設定の方式。0 はプロファイル（グループ）を使う方式、1 はカスタム | 既定 |

ルールは、上から順に評価される。表の順に作る。一覧に表示されるのは「説明」の欄なので、名前（`130-servers-to-mgmt-caddy` など）を説明の欄に入れた。1 件のルールの宛先には、グループを複数選べる。プロトコルも複数選べる（「TCP & UDP」と表示される）。グループの中身は、[プロファイル](profiles.md#グループ)にある。

| 名前 | 動作 | プロトコル | 送信元 | 宛先 |
| --- | --- | --- | --- | --- |
| `130-servers-to-mgmt-caddy` | 許可 | TCP | `grp-vm-infra` | `grp-mgmt-omada-ui`、`grp-mgmt-pve-ui` |
| `131-servers-to-mgmt-metrics` | 許可 | TCP | `grp-vm-monitoring` | `grp-mgmt-metrics` |
| `140-servers-to-lab-ssh` | 許可 | TCP | `grp-vm-infra` | `grp-lab-access` |
| `141-servers-to-lab-metrics` | 許可 | TCP | `grp-vm-monitoring` | `grp-lab-metrics` |
| `142-servers-to-lab-mosh` | 許可 | UDP | `grp-vm-infra` | `grp-lab-mosh` |
| `150-trusted-to-servers` | 許可 | すべて | ネットワーク Trusted | ネットワーク Servers |
| `151-trusted-to-lab` | 許可 | すべて | ネットワーク Trusted | ネットワーク Lab |
| `153-trusted-to-mgmt` | 許可 | TCP | ネットワーク Trusted | `grp-mgmt-pve-admin`、`grp-mgmt-omada-ssh` |
| `154-trusted-to-mgmt-devices` | 許可 | TCP | ネットワーク Trusted | `grp-mgmt-devices-web` |
| `156-trusted-to-mgmt-icmp` | 許可 | ICMP | ネットワーク Trusted | ネットワーク Management |
| `160-trusted-to-iot` | 許可 | すべて | ネットワーク Trusted | ネットワーク IoT |
| `170-lab-to-servers-dns` | 許可 | TCP と UDP | ネットワーク Lab | `grp-dns` |
| `171-iot-to-servers-dns` | 許可 | TCP と UDP | ネットワーク IoT | `grp-dns` |
| `172-guests-to-servers-dns` | 許可 | TCP と UDP | ネットワーク Guests | `grp-dns` |
| `910-deny-from-mgmt` | 拒否 | すべて | ネットワーク Management | !ネットワーク Management |
| `920-deny-from-servers` | 拒否 | すべて | ネットワーク Servers | !ネットワーク Servers |
| `930-deny-from-trusted` | 拒否 | すべて | ネットワーク Trusted | !ネットワーク Trusted |
| `940-deny-from-lab` | 拒否 | すべて | ネットワーク Lab | !ネットワーク Lab |
| `950-deny-from-iot` | 拒否 | すべて | ネットワーク IoT | !ネットワーク IoT |
| `960-deny-from-guests` | 拒否 | すべて | ネットワーク Guests | !ネットワーク Guests |
| `970-deny-from-dmz` | 拒否 | すべて | ネットワーク DMZ | !ネットワーク DMZ |

- すべてのルールで、ログは無効にしている。ログを使うには、サイトのリモートログ（syslog の送り先）が要る。末尾の拒否（`9xx`）だけログを有効にする案は、[ロードマップ 14](../../../../operations/roadmap/14-syslog-collection.md) で検討中である。
- 戻りの通信（確立済み）は、ルールが無くても通る（2026-11-27 に確認。拒否を有効にした VLAN へ、許可した向きから SSH で入れた）。
- Trusted → DMZ（Web・SSH）、Servers → DMZ（ログの取得）、Management → DMZ（管理用ポート）は、DMZ に何も置いていないので、作らない（今は末尾の拒否に当たる）。DMZ に機器を置くときに足す。
- **確認済み（2026-11-27）**: プロトコルは、ICMP だけも、TCP と UDP の両方も選べる。送信元に IP グループ、宛先に IP-Port グループを選べる。
- **確認済み（2026-11-27）**: `!ネットワーク` の拒否は、WAN 側のプライベートアドレス（建物の共用ルーター `172.22.0.1`）宛の通信を止めない。`vm-monitoring` から `172.22.0.1` への ping は、`920` を有効にしたあとも通り、Prometheus の `building-router` の監視は `up` のままだった。
- 確かめ方: Mac（Tailscale をオフ）と各ホストから、許可と拒否の両方を 35 件流す `make acl-check`（`tools/acl-check.py`）で確かめた（[手順書 27](../../../../operations/runbooks/27-network-acl-tighten.md#実施の記録)）。コントローラーや機器を作り直したあとは、ACL が全許可に戻っていないかを、これで確かめる。**ルールを変えたら、スクリプトのケースも同じ変更で直す。**

## ファイアウォール

ER605 の接続の追跡（タイムアウト）と、いくつかの挙動の設定である。変えた記録は無い。タイムアウトの単位は、仕様書に記載が無い（秒と見込む。未確認）。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `broadcastPing` | `false` | ブロードキャスト宛の ping に応答する | 既定 |
| `receiveRedirects` | `false` | ICMP リダイレクトを受け入れる | 既定 |
| `sendRedirects` | `true` | ICMP リダイレクトを送る | 既定 |
| `synCookies` | `true` | SYN Cookies を使う（SYN フラッドへの備え） | 既定 |
| `tcpEstablished` | `7440` | 確立済みの TCP の接続を覚えておく時間 | 既定 |
| `tcpSynSent` | `120` | TCP の SYN_SENT の時間 | 既定 |
| `tcpSynReceive` | `60` | TCP の SYN_RECV の時間 | 既定 |
| `tcpFinWait` | `120` | TCP の FIN_WAIT の時間 | 既定 |
| `tcpTimeWait` | `120` | TCP の TIME_WAIT の時間 | 既定 |
| `tcpClose` | `10` | TCP の CLOSE の時間 | 既定 |
| `tcpCloseWait` | `60` | TCP の CLOSE_WAIT の時間 | 既定 |
| `tcpLastAck` | `30` | TCP の LAST_ACK の時間 | 既定 |
| `udpStream` | `180` | 双方向に流れている UDP の時間 | 既定 |
| `udpOther` | `60` | そのほかの UDP の時間 | 既定 |
| `icmp` | `30` | ICMP の時間 | 既定 |
| `other` | `600` | そのほかのプロトコルの時間 | 既定 |

## 攻撃の防御

ER605 が、不正なパケットや大量のパケットを落とす設定である。変えた記録は無い。フラッドの制限（`*Enable`）は、すべて無効である。制限の値（`*Limit`）の単位は、仕様書に記載が無い（未確認）。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `tcpConnEnable` / `tcpConnLimit` | `false` / `10000` | 多数の接続による TCP SYN フラッドの制限（Multi-connections） | 既定 |
| `udpConnEnable` / `udpConnLimit` | `false` / `12000` | 多数の接続による UDP フラッドの制限（Multi-connections） | 既定 |
| `icmpConnEnable` / `icmpConnLimit` | `false` / `1500` | 多数の接続による ICMP フラッドの制限（Multi-connections） | 既定 |
| `tcpSrcEnable` / `tcpSrcLimit` | `false` / `4000` | 同じ送信元からの TCP SYN フラッドの制限（Stationary source） | 既定 |
| `udpSrcEnable` / `udpSrcLimit` | `false` / `6000` | 同じ送信元からの UDP フラッドの制限（Stationary source） | 既定 |
| `icmpSrcEnable` / `icmpSrcLimit` | `false` / `600` | 同じ送信元からの ICMP フラッドの制限（Stationary source） | 既定 |
| `tcpScanEnable` | `true` | TCP のポートスキャンを落とす | 既定 |
| `tcpScanReject` | `false` | TCP のポートスキャンに、落とすのではなく拒否を返す | 既定 |
| `pingDeathEnable` | `true` | Ping of Death を落とす | 既定 |
| `largePingEnable` | `false` | 大きすぎる ping を落とす | 既定 |
| `pingWanEnable` | `true` | WAN からの ping を落とす | 既定。外からの ping に応答しない |
| `winNukeAttackEnable` | `true` | WinNuke 攻撃を落とす | 既定 |
| `tcpSynFinEnable` | `true` | SYN と FIN が両方立った TCP を落とす | 既定 |
| `tcpFinNoAckEnable` | `true` | FIN が立ち ACK が無い TCP を落とす | 既定 |
| `specifiedOptionEnable` | `true` | 指定した IP オプションを持つパケットを落とす | 既定 |
| `specifiedOption.*Enable` | すべて `true` | 落とす IP オプション（Security、Record Route、Stream、Timestamp、No Operation） | 既定 |
| `icmpTimestampRequestReject` | `true` | ICMP のタイムスタンプ要求を拒否する | 既定 |
