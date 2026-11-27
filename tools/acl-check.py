#!/usr/bin/env python3
"""ゲートウェイ ACL（ER605、LAN → LAN）の許可と拒否を、実際の通信で確かめる。

Mac（Trusted）と各ホスト（SSH）から、許可表のとおりに届くか・止まるかを試す。
各ケースの期待値は、許可のルール（1xx）に当たるかと、送信元の VLAN の末尾の拒否（9xx）が
有効かで決まる。既定は、すべての 9xx が有効な今の本番の状態。

  make acl-check                         # 今の本番の状態を確かめる
  python3 tools/acl-check.py --deny none # 全許可（9xx をすべて無効）のときの期待値で確かめる
  python3 tools/acl-check.py --deny dmz,guests,iot,lab  # 9xx を 1 件ずつ足すとき

前提: Mac が Trusted に有線か Wi-Fi で繋がり、Tailscale をオフにしている（Tailscale の経路は
ACL を通らない）。~/.ssh/config に pve01、vm-infra、vm-monitoring、vm-dev、vm-omada がある。
vm-dev（任意起動）が動いている。

ルールの正は docs/architecture/lld/network/omada-controller.md、手順は
docs/operations/runbooks/27-network-acl-tighten.md。ルールを変えたら、ここのケースも直す。
"""
import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

VLANS = ["mgmt", "servers", "trusted", "lab", "iot", "guests", "dmz"]
MAC = "{mac}"  # 実行時に、Mac の Trusted の住所に置き換える

# (送信元ホスト, 送信元 VLAN, 種類, 宛先, ポート, 期待, 根拠)
#   種類: tcp / ping / dns-udp / dns-tcp / https
#   期待: allow  = 許可のルールに当たる。常に届く
#         deny   = 送信元の VLAN の 9xx が有効なら止まる
#         always = ACL の対象外（インターネット、ゲートウェイ自身、WAN 側）。常に届く
# deny のケースは、全許可（--deny none）のときに届く宛先を選ぶ。届かない宛先だと、
# UFW が止めたのか ACL が止めたのか区別できない。
CASES = [
    # Trusted（Mac。ローカルで実行）
    ("local", "trusted", "tcp", "10.77.20.10", 443, "allow", "150 trusted→servers"),
    ("local", "trusted", "tcp", "10.77.20.30", 8080, "allow", "150 code-server"),
    ("local", "trusted", "tcp", "10.77.40.10", 22, "allow", "151 trusted→lab"),
    ("local", "trusted", "tcp", "10.77.10.10", 8006, "allow", "153 pve ui"),
    ("local", "trusted", "tcp", "10.77.10.10", 22, "allow", "153 pve ssh"),
    ("local", "trusted", "tcp", "10.77.10.3", 22, "allow", "153 omada ssh"),
    ("local", "trusted", "tcp", "10.77.10.2", 443, "allow", "154 switch ui"),
    ("local", "trusted", "ping", "10.77.10.10", None, "allow", "156 icmp→mgmt"),
    ("local", "trusted", "tcp", "10.77.10.10", 9100, "deny", "930 (mgmt は 153/154/156 のみ)"),
    # Servers
    ("vm-infra", "servers", "tcp", "10.77.10.3", 8043, "allow", "130 caddy→omada"),
    ("vm-infra", "servers", "tcp", "10.77.10.10", 8006, "allow", "130 caddy→pve"),
    ("vm-infra", "servers", "tcp", "10.77.40.10", 22, "allow", "140 infra→lab ssh"),
    ("vm-infra", "servers", "tcp", "10.77.10.10", 22, "deny", "920 (130 は 8006 のみ)"),
    ("vm-infra", "servers", "ping", MAC, None, "deny", "920 servers→trusted"),
    ("vm-monitoring", "servers", "tcp", "10.77.10.10", 9100, "allow", "131 metrics pve"),
    ("vm-monitoring", "servers", "tcp", "10.77.10.3", 9100, "allow", "131 metrics omada"),
    ("vm-monitoring", "servers", "tcp", "10.77.40.10", 9100, "allow", "141 metrics lab"),
    ("vm-monitoring", "servers", "tcp", "10.77.10.10", 8006, "deny", "920 (130 は vm-infra のみ)"),
    ("vm-monitoring", "servers", "ping", "172.22.0.1", None, "always", "WAN 側（!ネットワークは止めない）"),
    ("vm-monitoring", "servers", "ping", "1.1.1.1", None, "always", "インターネット"),
    # Lab
    ("vm-dev", "lab", "dns-udp", "10.77.20.10", 53, "allow", "170 dns udp"),
    ("vm-dev", "lab", "dns-tcp", "10.77.20.10", 53, "allow", "170 dns tcp"),
    ("vm-dev", "lab", "tcp", "10.77.20.10", 443, "deny", "940 lab→servers"),
    ("vm-dev", "lab", "ping", "10.77.10.10", None, "deny", "940 lab→mgmt"),
    ("vm-dev", "lab", "tcp", "10.77.10.10", 22, "deny", "940 lab→mgmt"),
    ("vm-dev", "lab", "ping", MAC, None, "deny", "940 lab→trusted"),
    ("vm-dev", "lab", "ping", "10.77.30.1", None, "always", "ゲートウェイ自身"),
    ("vm-dev", "lab", "ping", "1.1.1.1", None, "always", "インターネット"),
    ("vm-dev", "lab", "https", "deb.debian.org", 443, "always", "インターネット"),
    # Management
    ("pve01", "mgmt", "ping", "10.77.20.10", None, "deny", "910 mgmt→servers"),
    ("pve01", "mgmt", "tcp", "10.77.20.10", 443, "deny", "910 mgmt→servers"),
    ("pve01", "mgmt", "dns-udp", "10.77.10.1", 53, "always", "ルーターの DNS"),
    ("pve01", "mgmt", "ping", "1.1.1.1", None, "always", "インターネット"),
    ("vm-omada", "mgmt", "ping", "10.77.20.10", None, "deny", "910 mgmt→servers"),
    ("vm-omada", "mgmt", "dns-udp", "10.77.10.1", 53, "always", "ルーターの DNS"),
]


def command(kind, dest, port, local):
    if kind == "tcp":
        # macOS の nc は、接続の待ち時間を -G で指定する
        return f"nc -z {'-G 3 ' if local else ''}-w 3 {dest} {port}"
    if kind == "ping":
        # macOS の ping は -t、Linux は -W で待ち時間を指定する
        return f"ping -c 2 {'-t 3' if local else '-W 2'} {dest} >/dev/null"
    if kind == "dns-udp":
        return f"dig +time=2 +tries=1 @{dest} home.lab.kanare.dev >/dev/null"
    if kind == "dns-tcp":
        return f"dig +tcp +time=2 +tries=1 @{dest} home.lab.kanare.dev >/dev/null"
    if kind == "https":
        return f"curl -s -o /dev/null --max-time 5 https://{dest}"
    raise ValueError(kind)


def run(case):
    host, _, kind, dest, port, _, _ = case
    cmd = command(kind, dest, port, host == "local")
    if host == "local":
        argv = ["sh", "-c", cmd]
    else:
        argv = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", host, cmd]
    try:
        return subprocess.run(argv, capture_output=True, timeout=20).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def route_interface(dest):
    out = subprocess.run(["route", "-n", "get", dest], capture_output=True, text=True).stdout
    m = re.search(r"interface:\s*(\S+)", out)
    return m.group(1) if m else None


def trusted_address(iface):
    out = subprocess.run(["ipconfig", "getifaddr", iface], capture_output=True, text=True).stdout.strip()
    return out if out.startswith("10.77.30.") else None


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--deny", default="all",
                   help="有効にした 9xx の送信元 VLAN（カンマ区切り。all か none も可。既定は all）")
    deny = p.parse_args().deny
    denied = set(VLANS) if deny == "all" else set() if deny == "none" else set(deny.split(","))
    if denied - set(VLANS):
        sys.exit(f"--deny に知らない VLAN がある: {','.join(sorted(denied - set(VLANS)))}")

    # Tailscale の経路（utun）を通ると、ACL を通らずに届いてしまう
    for dest in ("10.77.20.10", "10.77.40.10"):
        iface = route_interface(dest)
        if not iface or iface.startswith("utun"):
            sys.exit(f"{dest} への経路が {iface} を通る。Tailscale をオフにしてから実行する（tailscale down）")
    mac = trusted_address(route_interface("10.77.30.1"))
    if not mac:
        sys.exit("Mac が Trusted（10.77.30.0/24）に繋がっていない")

    cases = [tuple(mac if x == MAC else x for x in c) for c in CASES]
    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(run, cases))

    fails = 0
    for case, reached in zip(cases, results):
        host, vlan, kind, dest, port, rule, why = case
        expect = rule in ("allow", "always") or vlan not in denied
        mark = "PASS" if reached == expect else "FAIL"
        fails += mark == "FAIL"
        target = f"{dest}:{port}" if port else dest
        got, want = ("reach" if reached else "BLOCK"), ("reach" if expect else "BLOCK")
        print(f"{mark}  {host:13} {kind:7} {target:22} got={got:5} want={want:5}  {why}")
    label = "all" if denied == set(VLANS) else ",".join(v for v in VLANS if v in denied) or "none"
    print(f"\n{len(cases)} cases, {fails} fail (9xx enabled: {label})")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
