# 認証（Omada のパラメーターシート）

画面の場所は、サイト > 構成 > ネットワーク設定 > 認証（ポータル、802.1X、MAC ベース認証）である。実機の値は [`snapshot/authentication.json`](snapshot/authentication.json) にある。表の読み方は [README](README.md#表の読み方) にある。

どれも使っていない。ゲスト向けの Wi-Fi（Guests）を Omada の AP で出すとき（段階 4）に、ポータルを使うかを決める。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `portals` | なし | キャプティブポータル | 使わない |
| `dot1x.enable` | `false` | スイッチの 802.1X 認証 | 使わない |
| `dot1x.authMode` / `dot1x.authType` | `1` / `1` | 認証の方式（1 は EAP）と単位（1 は MAC ごと） | 既定。無効なので効いていない |
| `dot1x.vlanAssign` | `false` | 認証の結果で VLAN を割り当てる | 既定 |
| `mac-auth.enable` | `false` | MAC ベース認証 | 使わない |
