# 送信（Omada のパラメーターシート）

画面の場所は、サイト > 構成 > ネットワーク設定 > 送信（ルーティング、NAT、DHCP の予約、帯域制御、セッション制限、ゲートウェイ QoS、スイッチ QoS、OUI ベースの VLAN）である。実機の値は [`snapshot/transmission.json`](snapshot/transmission.json) にある。表の読み方は [README](README.md#表の読み方) にある。

ほとんど使っていない。家の中の経路は、ER605 が各 VLAN のゲートウェイとして直接つなぐので、静的な経路は要らない。外に何も公開しないので、ポート転送も無い。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `static-routings` | なし | 静的な経路 | 使わない |
| `policy-routings` | なし | ポリシーによる経路 | 使わない |
| `port-forwardings` | なし | ポート転送（NAT） | 外に何も公開しない（Tailscale で入る。[ADR-0005](../../../../adr/0005-tailscale-only-remote-access.md)） |
| `one-to-one-nat` | なし | 1 対 1 の NAT | 使わない |
| `nat-alg.ftp` / `h323` / `pptp` / `ipSec` | `true` | 各プロトコルの ALG（NAT を越えるための書き換え） | 既定 |
| `nat-alg.sip` | `false` | SIP の ALG | 既定 |
| `dhcp-reservations` | なし | DHCP の予約（固定の割り当て） | 使わない。住所を固定したいホストは、ホスト側で固定する（Buffalo の固定リース 1 件は、移さなかった。[移行計画](../../../../operations/roadmap/10-er605-sg2210p-migration-plan.md)） |
| `bandwidth-control.enable` | `false` | 帯域制御 | 使わない |
| `bandwidth-control.thresholdControlEnable` / `thresholdValue` | `false` / `80` | 帯域制御を始めるしきい値（%） | 既定。無効なので効いていない |
| `session-limit.enable` | `false` | セッション数の制限 | 使わない |
| `gateway-qos-class-rules` | なし | ゲートウェイ QoS のクラスのルール | 使わない |
| `switch-oui-rules` | なし | OUI ベースの VLAN（MAC の製造元で VLAN を決める） | 使わない |
