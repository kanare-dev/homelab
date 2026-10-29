#!/usr/bin/env python3
"""構成図 docs/diagrams/architecture.drawio.svg の座標・文字・余白を規格どおりに組み直す。

SVG に埋め込まれた draw.io の XML を読み、全セルの位置を決め直して、draw.io CLI で SVG に書き出す。
何度実行しても結果は同じ。VM やサービスを足したら、下の「配置」を直して実行する。

    python3 docs/diagrams/layout-architecture.py

必要なもの: draw.io デスクトップ版（`brew install --cask drawio`）。

規格（10px グリッド）:
  - 文字は 14px のみ。ポート・IP は橙、VM 名は斜体。
  - VM 枠は幅 300、内側の余白 20。見出しアイコン 40、サービス行は高さ 30（アイコン 30）。
  - VM 直下のサービスと Docker アイコンは VM 枠の左端から 40（VM 見出しのアイコンより内側）。
    Docker 枠の中のサービスは、さらに 20 内側（Docker アイコンより内側）。
  - 行の送りは 40。Docker 枠の高さは「行数 × 40 + 10」。枠どうしの間隔は 20。
"""
import base64
import html
import re
import subprocess
import sys
import tempfile
import urllib.parse
import zlib
from pathlib import Path

SVG = Path(__file__).resolve().parent / "architecture.drawio.svg"
ICONS = SVG.parent / "assets/icons"  # Git 管理外。新しいアイコンを初めて取り込むときだけ読む
K = "Ka6-sXaiJ_n7gUF576qm-"  # draw.io が付けた ID の接頭辞（vm-code の枠）
ORANGE = '<font color="#ff8000">%s</font>'


def read_model(path):
    content = html.unescape(re.search(r'content="([^"]*)"', path.read_text()).group(1))
    body = re.search(r"<diagram[^>]*>(.*)</diagram>", content, re.S).group(1)
    if body.strip().startswith("<"):
        return body
    return urllib.parse.unquote(zlib.decompress(base64.b64decode(body), -15).decode())


class Model:
    def __init__(self, xml):
        self.xml = xml

    def _cell(self, cid, tail):
        m = re.search(r'(<mxCell id="%s"(?:(?!</mxCell>).)*?)%s' % (re.escape(cid), tail), self.xml, re.S)
        if not m:
            raise KeyError(cid)
        return m

    def geo(self, cid, x=None, y=None, w=None, h=None):
        m = re.search(
            r'(<mxCell id="%s"(?:(?!</mxCell>).)*?<mxGeometry )([^>]*?)( as="geometry"\s*/?>)' % re.escape(cid),
            self.xml, re.S)
        if not m:
            raise KeyError(cid)
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(2)))
        for k, v in (("x", x), ("y", y), ("width", w), ("height", h)):
            if v is not None:
                a[k] = "%g" % v
        s = " ".join(f'{k}="{v}"' for k, v in a.items())
        self.xml = self.xml[:m.start(2)] + s + self.xml[m.end(2):]

    def value(self, cid, v):
        m = self._cell(cid, r' value="[^"]*"')
        self.xml = self.xml[:m.end(1)] + ' value="%s"' % html.escape(v, quote=True) + self.xml[m.end():]

    def edge(self, cid, x1, y1, x2, y2):
        m = re.search(r'<mxCell id="%s" edge.*?</mxCell>' % cid, self.xml, re.S)
        new = (f'<mxCell id="{cid}" edge="1" parent="1" style="endArrow=none;html=1;startArrow=none;strokeWidth=3;" '
               f'value=""><mxGeometry height="50" relative="1" width="50" as="geometry">'
               f'<mxPoint x="{x1}" y="{y1}" as="sourcePoint"/><mxPoint x="{x2}" y="{y2}" as="targetPoint"/>'
               f'</mxGeometry></mxCell>')
        self.xml = self.xml[:m.start()] + new + self.xml[m.end():]

    def add_edge(self, cid, x1, y1, x2, y2):
        """既存の線と同じ見た目で、新しい線を追加する（すでにあれば何もしない）。"""
        if f'<mxCell id="{cid}"' not in self.xml:
            self.xml = self.xml.replace("</root>", '<mxCell id="%s" edge="1" parent="1" value=""></mxCell></root>' % cid)
        self.edge(cid, x1, y1, x2, y2)

    def drop(self, cid):
        m = re.search(r'<mxCell id="%s" edge.*?</mxCell>' % cid, self.xml, re.S)
        if m:
            self.xml = self.xml[:m.start()] + self.xml[m.end():]

    def clone(self, src, new_id, icon=None):
        """既存セルを複製して新しい ID で追加する（すでにあれば何もしない）。
        icon に SVG のパスを渡すと、複製したセルの画像をその SVG に差し替える（初回だけ読む）。"""
        if f'<mxCell id="{new_id}"' in self.xml:
            return
        cell = re.search(r'<mxCell id="%s"(?:(?!</mxCell>).)*?</mxCell>' % re.escape(src), self.xml, re.S).group(0)
        cell = cell.replace(f'id="{src}"', f'id="{new_id}"', 1)
        if icon:
            data = base64.b64encode((ICONS / icon).read_bytes()).decode()
            cell = re.sub(r"image=[^;\"]*", "image=data:image/svg+xml," + data, cell, count=1)
        self.xml = self.xml.replace("</root>", cell + "</root>")

    def normalize_styles(self):
        def fix(m):
            s = m.group(0)
            st = re.search(r' style="([^"]*)"', s).group(1)
            new = st
            if "shape=image" in st and "rotation" not in st:
                new = new.replace("imageAspect=0", "imageAspect=1")  # 正方形の枠に歪ませず収める
            if st.startswith("text;"):
                new = new.replace("strokeWidth=2;", "").replace("opacity=70;", "")
                if "fontSize=" not in new:
                    new += "fontSize=14;"
            return s.replace(st, new, 1)
        self.xml = re.sub(r'<mxCell id="[^"]*"(?:(?!</mxCell>).)*?</mxCell>', fix, self.xml, flags=re.S)

    # 部品 ---------------------------------------------------------------
    def row(self, icon, text, x, y, w):
        self.geo(icon, x, y, 30, 30)
        self.geo(text, x + 40, y, w - 40, 30)

    def head(self, icon, text, x, y, w):
        self.geo(icon, x, y, 40, 40)
        self.geo(text, x + 50, y, w - 50, 40)

    def vm(self, frame, icon, text, x, y, h):
        self.geo(frame, x, y, 300, h)
        self.head(icon, text, x + 20, y + 20, 260)

    def dbox(self, box, rows, x, y):
        """Docker 枠。rows の先頭は「Docker containers」の見出し行。"""
        self.geo(box, x + 20, y, 260, 40 * len(rows) + 10)
        for k, (icon, text) in enumerate(rows):
            indent = 0 if k == 0 else 20  # 中のサービスは Docker アイコンより内側
            self.row(icon, text, x + 40 + indent, y + 10 + 40 * k, 220 - indent)

    def device(self, icon, text, x, y, iw, ih, w):
        """端末の行（高さ 60）。アイコンの中心とテキストの中心を同じ高さに置く。"""
        self.geo(icon, x + 20 + (40 - iw) / 2, y + (60 - ih) / 2, iw, ih)
        self.geo(text, x + 70, y, w - 90, 60)


def vm_head(name, ip):
    return f"<i>{name}</i> {ORANGE % ip}<br>Ubuntu Server 24.04"


def svc(name, port=None):
    return name + (f" {ORANGE % port}" if port else "")


def layout(m):
    m.normalize_styles()

    # 文字 ---------------------------------------------------------------
    m.value("8", "Buffalo WSR-1800AX4P<br>" + ORANGE % "192.168.11.1")
    m.value("13", "Internet")
    m.value("15", "Lenovo ThinkCentre M70q Tiny<br>CPU: Intel Core i5-10400T (6C/12T)<br>"
                  "RAM: 1 x 8 GB + 1 x 16 GB DDR4-3200<br>Storage: 1 x 256GB NVMe SSD")
    m.value("24", "<b>LAN<br>192.168.11.0/24</b>")
    m.value("27", "<i>pve</i> " + ORANGE % "192.168.11.10" + "<br>Proxmox 9.1<br>(based on Debian 13)")
    for cid, name, ip in (("34", "vm-infra", "192.168.11.11"), ("37", "vm-monitoring", "192.168.11.13"),
                          ("47", "vm-apps", "192.168.11.20"), ("91", "vm-dev", "192.168.11.21"),
                          (K + "106", "vm-code", "192.168.11.22")):
        m.value(cid, vm_head(name, ip))
    for cid in ("62", "80", "98"):
        m.value(cid, "Docker containers")
    m.value("72", svc("CoreDNS", ":5353"))
    m.value("82", svc("Tailscale", ":41641"))
    m.value("102", svc("AdGuard", ":53, :3000"))
    m.value("101", svc("Unbound", ":5335"))
    m.value("74", svc("Caddy", ":80, :443"))
    m.value("65", svc("Grafana", ":3000"))
    m.value("66", svc("Prometheus", ":9090"))
    m.clone("64", "vmmon-blackbox-icon")
    m.clone("66", "vmmon-blackbox-text")
    m.value("vmmon-blackbox-text", svc("blackbox-exporter", ":9115"))
    m.value("93", svc("Homepage", ":3001"))
    m.clone("92", "vmapps-ha-icon", icon="apps/home-assistant.svg")
    m.clone("93", "vmapps-ha-text")
    m.value("vmapps-ha-text", svc("Home Assistant", ":8123"))
    m.clone("92", "vmapps-n8n-icon", icon="apps/n8n.svg")
    m.clone("93", "vmapps-n8n-text")
    m.value("vmapps-n8n-text", svc("n8n", ":5678"))
    for cid in ("84", "86", "88", "95"):
        m.value(cid, svc("node_exporter", ":9100"))
    m.value("vmcode-claude-text", svc("Claude Code"))
    m.value("vmcode-cloudcli-text", svc("CloudCLI", ":3001"))
    m.value("vmcode-codeserver-text", svc("code-server", ":8080"))
    m.value("vmcode-nodeexp-text", svc("node_exporter", ":9100"))
    ext = (("healthchecks", "Healthchecks.io"), ("slack", "Slack"), ("cloudflare", "Cloudflare"),
           ("letsencrypt", "Let's Encrypt"), ("tailscale", "Tailscale"), ("github", "GitHub"))
    m.clone("89", "ext-frame")
    m.clone("24", "ext-label")
    m.value("ext-label", "<b>External Services</b>")
    for n, label in ext:
        m.clone("92", f"ext-{n}-icon", icon=f"external/{n}.svg")
        m.clone("93", f"ext-{n}-text")
        m.value(f"ext-{n}-text", label)
    m.value("59", "<i>canales-macbook-pro-m5</i><br>" + ORANGE % "DHCP" + "<br>MacBook Pro M5")
    m.value("60", "<i>canales-iphone-14</i><br>" + ORANGE % "DHCP" + "<br>iPhone 14")
    m.value("57", ORANGE % "DHCP" + "<br>SwitchBot Hub 2")
    m.value("58", ORANGE % "192.168.11.100" + "<br>ESP32 + BME280")

    # 配置 ---------------------------------------------------------------
    m.clone("94", "vmdev-nodeexp-icon")
    m.clone("95", "vmdev-nodeexp-text")
    m.value("vmdev-nodeexp-text", svc("node_exporter", ":9100"))
    m.clone("89", "vmwin-frame")
    m.clone("90", "vmwin-icon", icon="platform/windows-11.svg")
    m.clone("91", "vmwin-text")
    m.value("vmwin-text", "<i>vm-windows</i> " + ORANGE % "DHCP" + "<br>Windows 11")
    m.geo("77", 0, 0, 1380, 1070)                      # 背景（キャンバス）。外周の余白は 40
    m.geo("28", 40, 40, 140, 40)
    m.geo("24", 40, 40, 140, 40)

    cx = 940                                          # Internet・ルーター・nic0 を通す縦線
    m.geo("Hu1WL4VJLdPnrhCaS11O-103", cx - 38.19, 46.5, 76.38, 47)  # インターネットのアイコン（差し替え済み）
    m.geo("13", cx + 40, 55, 80, 30)
    m.geo("103", cx - 60, 160, 120, 80)
    m.geo("8", cx + 70, 170, 220, 40)
    m.geo("38", cx - 20, 320, 40, 50)
    m.edge("11", cx, 93.5, cx, 160)
    m.edge("21", cx, 240, cx, 320)
    for cid in ("42", "68", "69"):
        m.drop(cid)

    m.geo("ext-frame", 220, 40, 640, 150)             # 外部サービス（Internet の左）。VM 枠と同じ見た目
    m.geo("ext-label", 240, 50, 200, 30)
    for k, (n, _) in enumerate(ext):
        m.row(f"ext-{n}-icon", f"ext-{n}-text", 240 + 210 * (k % 3), 100 + 40 * (k // 3), 190)
    m.add_edge("ext-edge", 860, 70, cx - 38.19, 70)

    m.geo("12", 530 - 25.05, 340 - 52)                # 90 度回転した画像。見た目の中心は (530, 340)
    m.geo("15", 380, 225, 300, 80)

    m.geo("14", 40, 340, 980, 690)                    # PVE 枠
    m.head("26", "27", 60, 360, 300)
    m.geo("27", 110, 360, 260, 60)

    c1, c2, c3, top = 60, 380, 700, 440               # VM 列の x と上端
    m.vm("32", "31", "34", c1, top, 380)              # vm-infra
    m.row("71", "72", c1 + 40, top + 70, 220)
    m.row("81", "82", c1 + 40, top + 110, 220)
    m.dbox("78", [("79", "80"), ("99", "102"), ("100", "101"), ("73", "74")], c1, top + 150)
    m.row("83", "84", c1 + 40, top + 330, 220)
    m.vm("89", "90", "91", c1, top + 400, 120)        # vm-dev
    m.row("vmdev-nodeexp-icon", "vmdev-nodeexp-text", c1 + 40, top + 470, 220)

    m.vm("35", "36", "37", c2, top, 300)              # vm-monitoring
    m.dbox("67", [("61", "62"), ("63", "65"), ("64", "66"), ("vmmon-blackbox-icon", "vmmon-blackbox-text")], c2, top + 70)
    m.row("85", "86", c2 + 40, top + 250, 220)
    m.vm(K + "104", K + "105", K + "106", c2, top + 320, 240)   # vm-code
    for k, n in enumerate(("claude", "cloudcli", "codeserver", "nodeexp")):
        m.row(f"vmcode-{n}-icon", f"vmcode-{n}-text", c2 + 40, top + 390 + 40 * k, 220)

    m.vm("45", "46", "47", c3, top, 300)              # vm-apps
    m.dbox("96", [("97", "98"), ("92", "93"), ("vmapps-ha-icon", "vmapps-ha-text"),
                    ("vmapps-n8n-icon", "vmapps-n8n-text")], c3, top + 70)
    m.row("94", "95", c3 + 40, top + 250, 220)
    m.vm("vmwin-frame", "vmwin-icon", "vmwin-text", c3, top + 320, 80)   # vm-windows（手動起動。node_exporter 未導入）
    m.geo("vmwin-icon", c3 + 25, top + 345, 30, 30)    # 余白のないロゴなので、他の見出しアイコンと大きさが合うよう小さくする

    m.row("87", "88", 80, 980, 220)                   # Proxmox ホスト自身の node_exporter（PVE 枠の左下）

    rx, rw = 1060, 280                                # LAN / IoT の枠。上端・下端は PVE 枠に合わせる
    m.head("30", "43", rx + 20, 290, rw - 20)
    m.geo("44", rx, 340, rw, 180)
    m.device("52", "59", rx, 360, 40, 30, rw)
    m.device("51", "60", rx, 440, 30, 40, rw)
    m.head("70", "53", rx + 20, 800, rw - 20)
    m.geo("54", rx, 850, rw, 180)
    m.device("55", "57", rx, 870, 40, 40, rw)
    m.device("56", "58", rx, 950, 40, 40, rw)


def main():
    model = Model(read_model(SVG))
    layout(model)
    with tempfile.TemporaryDirectory() as tmp:
        src, out = Path(tmp, "architecture.drawio"), Path(tmp, "architecture.svg")
        src.write_text('<mxfile><diagram name="Page-1">' + model.xml + "</diagram></mxfile>")
        subprocess.run(["drawio", "-x", "-f", "svg", "-e", "-b", "0", "--compress", "-o", str(out), str(src)],
                       check=True, capture_output=True)
        SVG.write_text(out.read_text().replace("color-scheme: light dark;", "color-scheme: light;"))
    print(f"更新: {SVG}")


if __name__ == "__main__":
    sys.exit(main())
