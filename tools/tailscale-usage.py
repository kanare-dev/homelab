#!/usr/bin/env python3
"""Tailscale 経由の通信の使い方を、端末 × 宛先 × ポートの表にする。

vm-infra の nftables（table inet ts_audit。ansible/roles/tailscale_usage_audit）が数えた、
tailscale0 から入る新しい接続の回数を集める。再起動で消えた分は、1 時間ごとに書き出した
ファイル（起動ごとに 1 つ）から足す。Tailscale の ACL を決めるための一時的な記録である。

  python3 tools/tailscale-usage.py

出力には端末の名前と Tailscale の IP が出る。リポジトリに保存しない（公開のため）。
"""
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

HOST = "vm-infra"
AUDIT_DIR = "/var/lib/tailscale-usage-audit"
REPO = Path(__file__).resolve().parent.parent
VARS = REPO / "ansible/inventory/group_vars/infra/vars.yml"
PROTO = {6: "tcp", 17: "udp", "tcp": "tcp", "udp": "udp"}


def ssh(cmd):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", HOST, cmd], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"{HOST}: {cmd}: {r.stderr.strip()}")
    return r.stdout


def host_labels():
    """dns_records（CoreDNS）から、IP → 名前の表を作る。Caddy 経由の名前は除く。"""
    labels = {}
    for name, ip, comment in re.findall(r'name: "([^"]+)",\s*ip: "([^"]+)" }\s*(#.*)?', VARS.read_text()):
        if "Caddy 経由" in (comment or "") or name == "infra":
            continue
        labels.setdefault(ip, name)
    labels["10.77.20.10"] = "vm-infra"
    return labels


def label_dest(ip, labels, self_ips):
    if ip in self_ips:
        return "vm-infra (Tailscale IP)"
    if ip.startswith("172.") and 16 <= int(ip.split(".")[1]) <= 31:
        return f"vm-infra のコンテナ ({ip})"
    return labels.get(ip, ip)


def elements(table_json):
    """nft -j list table の出力から、(送信元, 宛先, プロトコル, ポート, パケット数) を取り出す。"""
    out = []
    for item in json.loads(table_json).get("nftables", []):
        s = item.get("set")
        if not s or s.get("name") not in ("seen4", "seen6"):
            continue
        for e in s.get("elem", []):
            e = e.get("elem", e)
            key = e["val"]["concat"]
            packets = e.get("counter", {}).get("packets", 0)
            out.append((key[0], key[1], PROTO.get(key[2], str(key[2])), key[3], packets))
    return out


def main():
    boot_id = ssh("cat /proc/sys/kernel/random/boot_id").strip()
    # 今の起動の分はテーブルから直接、過去の起動の分は書き出したファイルから読む
    current = ssh("sudo nft -j list table inet ts_audit")
    files = ssh(f"sudo sh -c 'for f in {AUDIT_DIR}/*.json; do [ -e \"$f\" ] && echo \"=== $f\" && cat \"$f\" && echo; done'")
    tables = [current]
    for block in files.split("=== ")[1:]:
        name, _, body = block.partition("\n")
        if boot_id not in name and body.strip():
            tables.append(body)

    status = json.loads(ssh("tailscale status --json"))
    peers = {}
    self_ips = set(status["Self"].get("TailscaleIPs", []))
    for p in [status["Self"], *status.get("Peer", {}).values()]:
        for ip in p.get("TailscaleIPs", []):
            peers[ip] = p.get("HostName") or p.get("DNSName", ip)

    labels = host_labels()
    totals = defaultdict(int)
    for t in tables:
        for src, dst, proto, port, packets in elements(t):
            key = (peers.get(src, src), label_dest(dst, labels, self_ips), f"{proto}/{port}")
            totals[key] += max(packets, 1)

    if not totals:
        print("まだ記録が無い")
        return
    rows = sorted(totals.items(), key=lambda kv: (kv[0][0], -kv[1]))
    w0 = max(len(k[0]) for k, _ in rows)
    w1 = max(len(k[1]) for k, _ in rows)
    print(f"{'端末':<{w0}}  {'宛先':<{w1}}  {'ポート':<10}  新規接続の回数")
    for (dev, dst, port), n in rows:
        print(f"{dev:<{w0}}  {dst:<{w1}}  {port:<10}  {n}")
    print(f"\n起動の数: {len(tables)}（今の起動を含む）")


if __name__ == "__main__":
    main()
