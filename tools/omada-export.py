#!/usr/bin/env python3
"""Omada コントローラーの設定値を Open API で取り出し、JSON に書き出す（ADR-0041）。

画面にしか置けない Omada の設定（ADR-0040）を、実機から機械的に写し取る。書き出した値は
docs/architecture/lld/network/omada/snapshot/ に置き、Git で管理する。実機を変えたあとに流すと、
変わった値が git diff に出る。パラメーターシート（omada-controller.md）と食い違えば、ずれである。

  make omada-export                              # snapshot/ を書き直す
  python3 tools/omada-export.py --out <dir>      # 別の場所に書き出す（比べるだけのとき）

認証は、omada-exporter 用の Open API のクライアント（Viewer。SOPS の omada_exporter_client_id・
omada_exporter_client_secret）を使う。値は画面にもファイルにも出さない。GET だけを呼ぶ。
リポジトリは公開なので、秘密の値（パスワード、鍵）と MAC アドレスは書き出す前に落とす。MAC は、
機器の名前（rtr01、sw01）に置き換え、機器でない MAC は <mac> にする。
"""
import argparse
import json
import re
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SECRETS = REPO / "ansible/inventory/group_vars/monitoring/secrets.sops.yml"
OUT = REPO / "docs/architecture/lld/network/omada/snapshot"
BASE = "https://omada.lab.kanare.dev"
SITE_NAME = "kanare-homelab"
PAGE = "page=1&pageSize=1000"

# 書き出す前に落とすキー（大文字小文字を区別しない、部分一致）
# 機器を特定できる値（シリアル番号）も落とす
# SSID のパスフレーズは pskSetting.securityKey にある。pskSetting ごと落とすと WPA モードも消えるので、鍵だけを落とす
DROP_KEY = re.compile(r"pass(word|phrase)?$|pwd|secret|^psk$|securitykey|privatekey|private_key|token|community|presharedkey|^sn$|serialnumber", re.I)
# 実行のたびに変わる値（状態、統計、時刻）。設定ではないので落とす
VOLATILE_KEY = re.compile(
    r"^(status|statusCategory|uptime|upTime|lastSeen|lastSeenTime|cpuUtil|memUtil|clientNum|clients|"
    r"rx|tx|rxRate|txRate|download|upload|traffic.*|.*Traffic|speed|linkSpeed|duplex|linkStatus|"
    r"needUpgrade|upgradeTime|createTime|updateTime|modifyTime|timestamp|.*Timestamp|time|"
    r"temp|temperature|poePower|poeRemain.*|load|loadRate|connectedTime|ipStatus|onlineTime|"
    r"wanUpTime|internetState|online|isOnline|adoptFailType|totalRows|currentPage|currentSize|"
    r"detailStatus|portOnlineStatus|wanOnlineStatus|portStatus|connectedStatus|switchStatusCategory)$"
)
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?:[-:][0-9A-Fa-f]{2}){5}\b")


def sops_value(key):
    r = subprocess.run(["sops", "-d", "--extract", f'["{key}"]', str(SECRETS)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"sops で {key} を読めない: {r.stderr.strip()}")
    return r.stdout.strip()


class Api:
    def __init__(self):
        self.ctx = ssl.create_default_context()
        self.cid = self._get(f"{BASE}/api/info")["result"]["omadacId"]
        body = {"omadacId": self.cid, "client_id": sops_value("omada_exporter_client_id"),
                "client_secret": sops_value("omada_exporter_client_secret")}
        r = self._req(f"{BASE}/openapi/authorize/token?grant_type=client_credentials", body)
        if r.get("errorCode") != 0:
            sys.exit(f"トークンを取れない: {r.get('errorCode')} {r.get('msg')}")
        self.token = r["result"]["accessToken"]

    def _req(self, url, data=None, token=None):
        h = {"Content-Type": "application/json"}
        if token:
            h["Authorization"] = "AccessToken=" + token
        req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=h,
                                     method="POST" if data else "GET")
        with urllib.request.urlopen(req, timeout=60, context=self.ctx) as f:
            return json.load(f)

    def _get(self, url):
        return self._req(url)

    def get(self, path):
        """Open API を GET し、result を返す。失敗は {"_error": ...} にする（書き出しは止めない）。"""
        path = path.replace("{omadacId}", self.cid)
        try:
            r = self._req(BASE + path, token=self.token)
        except Exception as e:  # noqa: BLE001  HTTP の失敗も記録して続ける
            return {"_error": str(e)}
        if r.get("errorCode") != 0:
            return {"_error": f"{r.get('errorCode')} {r.get('msg')}"}
        res = r.get("result")
        if isinstance(res, dict) and "data" in res and "totalRows" in res:
            return res["data"]  # ページ付きの一覧は、中身だけにする
        return res


def clean(o, macs, names, key=""):
    """秘密の値・変わる値を落とし、MAC を機器の名前にし、ほかの設定を指す ID に名前を添える。"""
    if isinstance(o, dict):
        out = {}
        for k, v in o.items():
            if DROP_KEY.search(k) or VOLATILE_KEY.match(k):
                continue
            out[k] = clean(v, macs, names, k)
        return out
    if isinstance(o, list):
        return [clean(v, macs, names, key) for v in o]
    if isinstance(o, str):
        # その設定自身の ID（キーが id）には名前を添えない。ほかの設定を指す ID だけに添える
        if o in names and key != "id":
            return f"{o} ({names[o]})"
        return MAC_RE.sub(lambda m: macs.get(norm_mac(m.group(0)), "<mac>"), o)
    return o


def norm_mac(m):
    return m.replace(":", "-").upper()


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", type=Path, default=OUT)
    out = p.parse_args().out

    api = Api()
    sites = api.get("/openapi/v1/{omadacId}/sites?" + PAGE)
    site = next(s["siteId"] for s in sites if s["name"] == SITE_NAME)
    S = f"/openapi/v1/{{omadacId}}/sites/{site}"
    G = "/openapi/v1/{omadacId}"

    devices = api.get(f"{S}/devices?{PAGE}")
    macs = {norm_mac(d["mac"]): d["name"] for d in devices}
    # ACL などが ID で指すネットワークとグループに、名前を添えるための表
    names = {n["id"]: n["name"] for n in api.get(f"{S}/lan-networks?{PAGE}")}
    names.update({g["groupId"]: g["name"] for g in api.get(f"{S}/profiles/groups") if "groupId" in g})
    names.update({x["id"]: x["name"] for x in api.get(f"/openapi/v2/{{omadacId}}/sites/{site}/lan-profiles?{PAGE}")})

    # 画面のメニューの区分ごとに 1 ファイルにする（サイト > 構成 > ネットワーク設定）
    groups = {
        "general": {  # 一般設定
            "site": f"{S}", "ntp": f"{S}/setting/ntp", "ssh": f"{S}/ssh",
            "snmp": f"{S}/setting/service/snmp", "remote-logging": f"{S}/remote-logging",
            "led": f"{S}/led", "lldp": f"{S}/lldp", "device-account": f"{S}/device-account",
            "reboot-schedules": f"{S}/reboot-schedules?{PAGE}", "upgrade-schedules": f"{S}/upgrade-schedules?{PAGE}",
        },
        "network": {  # ネットワーク設定（インターネット、LAN、WLAN）
            "internet": f"{S}/internet", "lan-networks": f"{S}/lan-networks?{PAGE}",
            "wlans": f"{S}/wireless-network/wlans?{PAGE}", "lan-multicasts": f"{S}/lan-multicasts?{PAGE}",
            "igmp": f"{S}/setting/service/igmp", "dns-proxy": f"{S}/setting/service/dns-proxy",
            "ddns": f"{S}/setting/service/ddns?{PAGE}", "upnp": f"{S}/upnp",
        },
        "authentication": {  # 認証
            "portals": f"{S}/portals?{PAGE}", "dot1x": f"{S}/dot1x", "mac-auth": f"{S}/mac-auth",
        },
        "security": {  # セキュリティ
            "acl-config-mode": f"{S}/acls/osg-config-mode", "gateway-acls": f"{S}/acls/osg-acls?{PAGE}",
            "switch-acls": f"{S}/acls/osw-acls?{PAGE}", "eap-acls": f"{S}/acls/eap-acls?{PAGE}",
            "url-filters-gateway": f"{S}/url-filters/gateway?{PAGE}", "ips": f"{S}/network-security/ips",
            "firewall": f"{S}/firewall", "attack-defense": f"{S}/attack-defense",
            "ip-mac-binds": f"{S}/ip-mac-binds?{PAGE}",
        },
        "transmission": {  # 送信
            "static-routings": f"{S}/routing/static-routings?{PAGE}",
            "policy-routings": f"{S}/routing/policy-routings?{PAGE}",
            "port-forwardings": f"{S}/nat/port-forwardings?{PAGE}", "one-to-one-nat": f"{S}/nat/one-to-one-nat?{PAGE}",
            "nat-alg": f"{S}/nat/alg", "dhcp-reservations": f"{S}/setting/service/dhcp?{PAGE}",
            "bandwidth-control": f"{S}/bandwidth-control", "session-limit": f"{S}/session-limit",
            "gateway-qos-class-rules": f"{S}/qos/gateway/class-rules?{PAGE}",
            "switch-oui-rules": f"{S}/switch-oui-rules?{PAGE}",
        },
        "profiles": {  # プロファイル
            "groups": f"{S}/profiles/groups",
            # スイッチのポートのプロファイル（デバイス設定 > ポートプロファイル）。v2 は VLAN の設定の有無も返す
            "lan-profiles": f"/openapi/v2/{{omadacId}}/sites/{site}/lan-profiles?{PAGE}",
        },
        "vpn": {
            "site-to-site": f"{S}/vpn/site-to-site-vpns?{PAGE}", "wireguard": f"{S}/vpn/wireguards?{PAGE}",
        },
        "controller": {  # コントローラー全体の設定
            "general": f"{G}/global/controller/setting/general", "retention": f"{G}/controller/setting/retention",
            "syslog": f"{G}/global/controller/setting/syslog", "device-mgmt": f"{G}/device-mgmt",
            "webhook": f"{G}/webhook/settings",
        },
    }
    # 機器ごとの設定（ファイル名は機器の名前）
    meta = {}
    for d in devices:
        mac, name, kind = d["mac"], d["name"], d.get("type")
        if kind == "gateway":
            groups[f"device-{name}"] = {"general-config": f"{S}/gateways/{mac}/general-config",
                                        "ports": f"{S}/gateways/{mac}/ports"}
        elif kind == "switch":
            meta[f"device-{name}"] = {"switch-mac": mac}
            groups[f"device-{name}"] = {"general-config": f"{S}/switches/{mac}/general-config",
                                        "networks": f"{S}/switches/{mac}/networks?{PAGE}",
                                        "interfaces": f"{S}/switches/{mac}/interfaces?{PAGE}",
                                        "ports": f"{S}/switches/ports/overview?{PAGE}"}
        elif kind == "ap":
            groups[f"device-{name}"] = {k: f"{S}/aps/{mac}/{k}" for k in (
                "general-config", "ip-setting", "vlan", "radio-config", "trunk-setting",
                "management-wlan", "lldp", "load-balance")}
    # SSID は WLAN グループの中にある。一覧には設定の一部しか無いので、SSID ごとに詳細を読む
    wlans = api.get(f"{S}/wireless-network/wlans?{PAGE}")
    for w in wlans if isinstance(wlans, list) else []:
        ssids = api.get(f"{S}/wireless-network/wlans/{w['wlanId']}/ssids?{PAGE}")
        for x in ssids if isinstance(ssids, list) else []:
            groups["network"][f"ssid {x['name']}"] = f"{S}/wireless-network/wlans/{w['wlanId']}/ssids/{x['ssidId']}"
    groups["devices"] = {"devices": f"{S}/devices?{PAGE}"}

    out.mkdir(parents=True, exist_ok=True)
    # 書き出しは JSON だけ。README.md など、ほかのファイルには触れない
    errors = 0
    for name, paths in groups.items():
        data = {}
        for k, path in paths.items():
            r = api.get(path)
            if k == "ports" and isinstance(r, list):  # サイト全体の一覧なので、この機器のポートだけにする
                dev = name.removeprefix("device-")
                r = [x for x in r if x.get("switchName") == dev]
            data[k] = clean(r, macs, names)
        if "switch-mac" in meta.get(name, {}):
            # ネットワーク（VLAN）ごとに、どのポートをネイティブ・タグ付きで通るか。ポートの一覧にはタグの中身が無い
            mac = meta[name]["switch-mac"]
            nets = api.get(f"{S}/switches/{mac}/port-lag-networks?{PAGE}")
            data["vlan-membership"] = {
                f"{n['vlan']} {n['name']}": clean(api.get(f"{S}/switches/{mac}/port-lag-networks/{n['id']}/vlan/{n['vlan']}"), macs, names)
                for n in (nets if isinstance(nets, list) else [])
            }
        errors += sum(1 for v in data.values() if isinstance(v, dict) and "_error" in v)
        (out / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(f"{len(groups)} ファイルを {out} に書き出した（取れなかった窓口: {errors}）")


if __name__ == "__main__":
    main()
