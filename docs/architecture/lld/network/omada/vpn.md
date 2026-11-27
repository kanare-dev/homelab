# VPN（Omada のパラメーターシート）

画面の場所は、サイト > 構成 > ネットワーク設定 > VPN である。実機の値は [`snapshot/vpn.json`](snapshot/vpn.json) にある。表の読み方は [README](README.md#表の読み方) にある。

ER605 の VPN は使わない。外から家に入るのは Tailscale だけにしている（[ADR-0005](../../../../adr/0005-tailscale-only-remote-access.md)。二重 NAT のため、ER605 で VPN を受けられない）。

| キー | 値 | 意味 | 理由・備考 |
| --- | --- | --- | --- |
| `site-to-site` | なし | 拠点間 VPN | 使わない |
| `wireguard` | なし | WireGuard VPN | 使わない（Tailscale を使う） |
