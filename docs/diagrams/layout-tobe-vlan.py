#!/usr/bin/env python3
"""ER605・SG2210P を導入して VLAN に分けた後（段階 3 の完了時点）の構成図 tobe-vlan.drawio.svg を作る。

下の「配置」の座標と文字から draw.io の XML を組み、draw.io CLI で SVG に書き出す（XML を埋め込むので、
draw.io で開いて編集もできる）。何度実行しても結果は同じ。計画が変わったら、下の「配置」を直して実行する。

    python3 docs/diagrams/layout-tobe-vlan.py

必要なもの: draw.io デスクトップ版（`brew install --cask drawio`）、macOS の `sips`（アイコンの縮小）。
アイコン素材 `docs/diagrams/assets/icons/` は Git 管理外。無ければ取得する（layout-architecture.py と同じ）。

内容は docs/operations/roadmap/10-er605-sg2210p-migration-plan.md の「段階 3 の後」と
docs/architecture/08-vlan-design.md の VLAN 一覧に合わせる。食い違ったら、文書のほうが正。

規格は layout-architecture.py（現行の構成図）と同じ（10px グリッド）:
  - 文字は 14px のみ。ポート・IP は橙、VM 名は斜体。
  - VM 枠は幅 300、内側の余白 20。見出しアイコン 40、サービス行は高さ 30（アイコン 30）。
  - VM 直下のサービスと Docker アイコンは VM 枠の左端から 40。Docker 枠の中のサービスは、さらに 20 内側。
  - 行の送りは 40。Docker 枠の高さは「行数 × 40 + 10」。枠どうしの間隔は 20。
現行の図は枠が全部橙。この図は VLAN ごとに枠の色を変える（右上の凡例）。VLAN 枠・VM 枠・Docker 枠は、その VLAN の色を Opacity 40% で重ねる。
"""
import base64
import html
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "tobe-vlan.drawio.svg"
ICONS = HERE / "assets/icons"
ORANGE = '<font color="#ff8000">%s</font>'

# VLAN ごとの色（塗り, 線）と名前
COLOR = {
    10: ("#dae8fc", "#6c8ebf"),
    20: ("#ffe6cc", "#d79b00"),
    30: ("#d5e8d4", "#82b366"),
    40: ("#e1d5e7", "#9673a6"),
    50: ("#fff2cc", "#d6b656"),
    60: ("#eeeeee", "#666666"),
    70: ("#f8cecc", "#b85450"),
}
NAME = {10: "Management", 20: "Servers", 30: "Trusted", 40: "Lab", 50: "IoT", 60: "Guests", 70: "DMZ"}

cells = []  # 前面（VM、文字、線）
back = []   # 背面（背景、LAN の枠、VLAN の枠）。cells より先に描く
_tmp = tempfile.TemporaryDirectory()
_n = [0]
OFF = [0]  # 凡例より下の内容を下げる量（add と edge が足す）


def nid(prefix):
    _n[0] += 1
    return f"{prefix}{_n[0]}"


def esc(v):
    return html.escape(v, quote=True)


def ip(v):
    return ORANGE % v


def name_ip(name, addr):
    return f"<i>{name}</i> {ip(addr)}"


def add(value, style, x, y, w, h, to=None):
    cid = None
    (cells if to is None else to).append(
        f'<mxCell id="{cid or nid("c")}" value="{esc(value)}" style="{style}" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y + OFF[0]}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def text(value, x, y, w, h, align="left"):
    add(value, f"text;html=1;strokeColor=none;fillColor=none;align={align};verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=14;",
        x, y, w, h)


def frame(x, y, w, h, fill, stroke, dashed=True, opacity=40, to=None, arc=16, group=True):
    """枠。opacity（%）は draw.io の Opacity（既定 40%、group=True で Group opacity も付ける）。VLAN 枠・VM 枠・Docker 枠は同じ色を 40% で重ねるので、重なるほど濃くなる。
    枠には文字を入れない（文字は別のセル）。角丸の半径は 16px で統一。"""
    style = (f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=2;opacity={opacity};"
             f"absoluteArcSize=1;arcSize={arc};" + ("dashed=1;dashPattern=8 8;" if dashed else "") + ("opacityGroup=1;" if group else ""))
    add("", style, x, y, w, h, to=to)


def zone(vlan, x, y, w, h, dashed=True):
    fill, line = COLOR[vlan]
    frame(x, y, w, h, fill, line, dashed, to=back)


def icon(path, x, y, w, h, max_px=None, svg=None, rotation=0):
    """アイコンを縮小して埋め込む（SVG が大きくなりすぎないように）。svg を渡すと、その文字列を使う。"""
    if path and path.lstrip().startswith("<svg"):  # パスの代わりに SVG の文字列が渡された
        svg, path = path, None
    if svg:
        mime, raw = "svg+xml", svg.encode()
    else:
        src = ICONS / path
        if max_px and src.suffix == ".png":
            small = Path(_tmp.name) / src.name
            try:
                subprocess.run(["sips", "-Z", str(max_px), str(src), "--out", str(small)], check=True, capture_output=True)
                src = small
            except subprocess.CalledProcessError:  # 拡張子は png でも中身が WebP のもの（switchbot.png）は縮小できない。小さいのでそのまま使う
                pass
        mime = "svg+xml" if src.suffix == ".svg" else "png"
        raw = src.read_bytes()
    add("", f"shape=image;verticalLabelPosition=bottom;labelBackgroundColor=default;verticalAlign=top;aspect=fixed;imageAspect=1;"
            f"image=data:image/{mime},{base64.b64encode(raw).decode()};" + (f"rotation={rotation};" if rotation else ""), x, y, w, h)


def wifi_svg():
    """Wi-Fi の電波アイコン。ダークテーマ（prefers-color-scheme: dark）では白くなる SVG。"""
    cx, cy, k = 200, 340, 0.70710678
    arcs = "".join(
        f'<path d="M{cx - r * k:.1f} {cy - r * k:.1f} A{r} {r} 0 0 1 {cx + r * k:.1f} {cy - r * k:.1f}" fill="none" stroke-width="32"/>'
        for r in (95, 150, 205))
    dot = f'<path d="M{cx} {cy} L{cx - 52 * k:.1f} {cy - 52 * k:.1f} A52 52 0 0 1 {cx + 52 * k:.1f} {cy - 52 * k:.1f} Z" stroke="none"/>'
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><style>g{fill:#000;stroke:#000}'
            '@media (prefers-color-scheme:dark){g{fill:#fff;stroke:#fff}}</style><g>' + arcs + dot + '</g></svg>')


def ethernet_svg():
    """Ethernet ポートのアイコン。ダークテーマ（prefers-color-scheme: dark）では白くなる SVG。"""
    body = ('<rect x="15" y="45" width="482" height="420" rx="45"/>'
            '<path d="M77 105H435V285H405V345H345V405H167V345H107V285H77Z"/>'
            '<path d="M135 165V245M195 165V245M255 165V245M315 165V245M375 165V245M77 405H105M407 405H435"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><style>g{fill:none;stroke:#000;stroke-width:30;stroke-linecap:round;stroke-linejoin:round}'
            '@media (prefers-color-scheme:dark){g{stroke:#fff}}</style><g>' + body + '</g></svg>')


def dark_svg(path, dark="#ffffff"):
    """素材の SVG を、ダークテーマ（prefers-color-scheme: dark）では塗りを白（dark）にした SVG にする。
    公式のダークテーマ用ロゴ（GitHub Mark White、Tailscale の白いロゴ）と同じ見た目。明るいテーマでは、素材のまま。"""
    raw = (ICONS / path).read_text()
    css = f"<style>@media (prefers-color-scheme:dark){{path{{fill:{dark}!important}}}}</style>"
    i = raw.index(">", raw.index("<svg")) + 1
    return raw[:i] + css + raw[i:]


def stencil(shape, x, y, w, h):
    add("", f"verticalLabelPosition=bottom;html=1;verticalAlign=top;align=center;strokeColor=none;fillColor=#00BEF2;"
            f"shape=mxgraph.azure.{shape};pointerEvents=1;strokeWidth=2;opacity=70;", x, y, w, h)


def edge(points, arrow=None, width=3, color=None):
    """arrow は None（矢印なし）、"end"（終点側）、"start"（始点側）。
    width は線の太さ（trunk は 5、それ以外は 3）。color は線の色（access の線は、その VLAN の色）。"""
    points = [(x, y + OFF[0]) for x, y in points]
    (sx, sy), (tx, ty) = points[0], points[-1]
    mid = "".join(f'<mxPoint x="{x}" y="{y}"/>' for x, y in points[1:-1])
    arr = f'<Array as="points">{mid}</Array>' if mid else ""
    end = {"end": "endArrow=block;endFill=1;", "start": "endArrow=none;endFill=0;startArrow=classic;startFill=1;"}.get(arrow, "endArrow=none;")
    col = f"strokeColor={color};" if color else ""
    cells.append(
        f'<mxCell id="{nid("e")}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;{end}strokeWidth={width};{col}" '
        f'edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{sx}" y="{sy}" as="sourcePoint"/>'
        f'<mxPoint x="{tx}" y="{ty}" as="targetPoint"/>{arr}</mxGeometry></mxCell>')


# 部品（layout-architecture.py と同じ寸法） -----------------------------------
def row(ic, label, x, y, w):
    """サービス行。アイコン 30、文字は 10 右。"""
    icon(ic, x, y, 30, 30, max_px=120)
    text(label, x + 40, y, w - 40, 30)


def svc(name, port=None):
    return name + (f" {ip(port)}" if port else "")


def vm(vlan, x, y, name, addr, os_text, items, head_icon="platform/ubuntu.png"):
    """VM 枠（幅 300）。items は ("row", アイコン, 文字) か ("docker", [(アイコン, 文字), ...])。高さを返す。"""
    cur = y + 70
    parts = []
    for kind, *rest in items:
        if kind == "row":
            parts.append(("row", rest[0], rest[1], cur))
            cur += 40
        else:
            rows = [("platform/docker.png", "Docker containers")] + rest[0]
            parts.append(("docker", rows, None, cur))
            cur += 40 * len(rows) + 10 + 20
    h = (cur - y) if items else 80
    frame(x, y, 300, h, COLOR[vlan][0], COLOR[vlan][1])
    icon(head_icon, x + 20, y + 20, 40, 40, max_px=160)
    text(f"{name_ip(name, addr)}<br>{os_text}", x + 70, y + 20, 210, 40)
    for kind, a, b, cy in parts:
        if kind == "row":
            row(a, b, x + 40, cy, 220)
        else:
            frame(x + 20, cy, 260, 40 * len(a) + 10, COLOR[vlan][0], COLOR[vlan][1])
            for k, (ic, label) in enumerate(a):
                indent = 0 if k == 0 else 20  # 中のサービスは Docker アイコンより内側
                row(ic, label, x + 40 + indent, cy + 10 + 40 * k, 220 - indent)
    return h


def device(ic, label, x, y, w, stencil_shape=None, size=(40, 30), svg=None):
    """端末の行（高さ 60）。アイコンの中心とテキストの中心を同じ高さに置く。"""
    iw, ih = size
    if stencil_shape:
        stencil(stencil_shape, x + 10 + (40 - iw) / 2, y + (60 - ih) / 2, iw, ih)
    else:
        icon(ic, x + 10 + (40 - iw) / 2, y + (60 - ih) / 2, iw, ih, max_px=160, svg=svg)
    text(label, x + 60, y, w - 60, 60)


NODE = ("monitoring/prometheus.png", svc("node_exporter", ":9100"))


def layout():
    # 背景 ---------------------------------------------------------------
    add("", "rounded=0;whiteSpace=wrap;html=1;strokeColor=none;fillColor=#FFFFFF80;", 0, 0, 1720, 1670, to=back)

    # 凡例（右上。縦一列。上ほど信頼度が高い） ----------------------------------------
    lx, ly = 1050, 20
    frame(1040, ly, 660, 222, "#ffffff", "#999999", dashed=False, opacity=100, group=False)  # 凡例は 1 つの四角（左: VLAN 一覧、右: 線と文字）
    text(f"<b>VLAN 一覧</b>（{ip('10.77.&lt;VLAN&gt;.0/24')}）", lx - 3, ly + 6, 380, 26)
    text("信頼度", lx - 3, ly + 39, 54, 22, align="center")
    edge([(lx + 24, ly + 66), (lx + 24, ly + 200)], arrow="start")  # 矢じりが上。上ほど信頼度が高い
    for k, v in enumerate((10, 20, 30, 40, 50, 60, 70)):
        y = ly + 56 + 22 * k
        frame(lx + 50, y + 2, 30, 18, COLOR[v][0], COLOR[v][1], dashed=False, arc=4, opacity=60, group=False)
        text(f"VLAN{v} {NAME[v]}", lx + 90, y, 290, 22)

    # 外部サービス（左上。現行の図と同じ 6 つに Omada Cloud を足す） ----------------------------
    frame(20, 20, 500, 210, "#dae8fc", "#6c8ebf", dashed=False, opacity=70, group=False)
    text("External Services", 40, 30, 300, 30)
    services = [
        ("external/healthchecks.svg", "Healthchecks.io"), ("external/slack.svg", "Slack"), ("external/cloudflare.svg", "Cloudflare"),
        ("external/letsencrypt.svg", "Let's Encrypt"), (dark_svg("external/tailscale.svg"), "Tailscale"), (dark_svg("external/github.svg"), "GitHub"),
        ("network/omada.svg", "Omada Cloud"),
    ]
    for k, (ic, label) in enumerate(services):
        col, rowi = divmod(k, 4)
        row(ic, label, 40 + 240 * col, 70 + 40 * rowi, 200)
    edge([(520, 126), (850, 126)])

    # 凡例の右半分: 線と文字の意味（色つきの線は、VLAN の色の意味が左の一覧にあるので、書かない。PoE と VPN の線は、図に現れたら足す）
    edge([(1440, 30), (1440, 232)], width=1, color="#cccccc")
    text("<b>線と文字</b>", 1450, 24, 240, 26)
    for k, (w, label) in enumerate([(3, "Ethernet（上流の WAN）"), (5, "Ethernet（trunk）")]):
        cy = 63 + 22 * k
        edge([(1450, cy), (1490, cy)], width=w)
        text(label, 1500, cy - 11, 190, 22)
    text("<i>斜体</i>: ホスト名（VM、端末）", 1450, 52 + 22 * 2, 240, 22)
    text(f"{ip('橙')}: IP アドレス、ポート", 1450, 52 + 22 * 3, 240, 22)

    OFF[0] = 80  # ここから下は 80 下げる（凡例と LAN の枠が重ならないように）

    # インターネット・ルーター・スイッチ ------------------------------------------
    add("", "sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#232F3D;strokeColor=none;dashed=0;"
            "verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;"
            "pointerEvents=1;shape=mxgraph.aws4.internet;labelPerimeter=1;", 846, 21, 78, 48)  # 現行の図と同じアイコン
    text("Internet", 938, 34, 100, 30)
    edge([(880, 76), (880, 200)])  # 地球儀の下から ER605 の上まで、1 本で繋ぐ
    text(f"建物の共用ルーター {ip('172.22.0.1')}（二重 NAT）", 520, 94, 350, 24, align="right")
    text("WAN（DHCP）", 750, 128, 120, 24, align="right")

    # LAN 全体の枠 ---------------------------------------------------------
    frame(20, 170, 1680, 1400, "#ffffff", "#666666", dashed=True, opacity=70, to=back, group=False)
    frame(40, 180, 200, 40, "#dddddd", "#666666", dashed=False, opacity=70, to=back, group=False)
    text(f"<b>LAN<br>{'10.77.0.0/16'}</b>", 40, 180, 200, 40, align="center")

    # 通信ポリシー（LAN の中、ER605 の左） -------------------------------------------
    text("<b>通信ポリシー（要約）</b><br>表にない通信は拒否。Trusted は Servers・Lab・IoT・DMZ へ必要なポートだけ許可。<br>"
         f"Lab・IoT・Guests・DMZ から内部へは拒否（DNS は <i>vm-infra</i> {ip('10.77.20.11')} だけ）。<br>"
         f"外出先: Tailscale が {ip('10.77.20.0/24')} と {ip('10.77.40.0/24')} だけを広告（Management には届かない）。",
         40, 250, 560, 140)

    icon("hardware/tplink-er605.png", 760, 200, 240, 80, max_px=700)
    text(f"<b>TP-Link ER605 V2</b><br>{ip('10.77.10.1')}（VLAN10）<br>各 VLAN の GW（.1）・DHCP・ACL", 1010, 200, 330, 80)
    edge([(880, 280), (880, 380)], width=5)  # p1: trunk（太い線）
    text("ER605 p2 ⇔ SG2210P p1: trunk（VLAN10/20/30/40/50/60/70 を tag 付き）", 890, 320, 560, 40)

    icon("hardware/tplink-sg2210p.png", 760, 380, 240, 80, max_px=700)
    text(f"<b>TP-Link SG2210P</b><br>{ip('10.77.10.2')}（VLAN10）<br>p1: ER605 / p2: pve / p3: AP1 / p4: Dell U2725QE / p5–p6: 予備 / p7–p8: 将来の AP 用（PoE）", 1010, 380, 707, 80)

    # Proxmox ------------------------------------------------------------
    gx, gy = 40, 640
    icon("hardware/thinkcentre-m70q-tiny.png", 433.03, 586, 293.94, 97, max_px=700)
    text("<b>Lenovo ThinkCentre M70q Tiny Gen1<br></b>CPU: Intel Core i5-10400T (6C/12T)<br>RAM: 1 x 8 GB + 1 x 16 GB DDR4-3200<br>"
         "Storage: 1 x 256GB NVMe SSD", 430, 519, 300, 80, align="center")
    edge([(800, 460), (800, 620)], width=5)  # p2: trunk（太い線）
    text("p2: trunk（VLAN10/20/40/50/70 を tag 付き）", 440, 468, 350, 24, align="right")

    # 右の列（Management / Lab / DMZ）と、Servers の 2 列を先に配置して高さを決める
    gi = len(back)                      # Proxmox の枠は、中の VLAN 枠より前に入れる
    sx, sy = gx + 20, gy + 100          # Servers 枠
    rx = sx + 660 + 20                  # 右の列
    hosts = {}
    A = sy + 50
    h_infra = vm(20, sx + 20, A, "vm-infra", "10.77.20.11", "Ubuntu Server 24.04", [
        ("row", "network/coredns.png", svc("CoreDNS", ":5353")),
        ("row", dark_svg("external/tailscale.svg"), svc("Tailscale", ":41641")),
        ("docker", [("network/adguard.png", svc("AdGuard", ":53, :3000")),
                    ("network/unbound.svg", svc("Unbound", ":5335")),
                    ("network/caddy.png", svc("Caddy", ":80, :443"))]),
        ("row", *NODE)])
    h_code = vm(20, sx + 20, A + h_infra + 20, "vm-code", "10.77.20.22", "Ubuntu Server 24.04", [
        ("row", "dev/claude-code.svg", "Claude Code"),
        ("row", "dev/cloudcli.svg", svc("CloudCLI", ":3001")),
        ("row", "dev/code-server.png", svc("code-server", ":8080")),
        ("row", *NODE)])
    h_mon = vm(20, sx + 340, A, "vm-monitoring", "10.77.20.13", "Ubuntu Server 24.04", [
        ("docker", [("monitoring/grafana.svg", svc("Grafana", ":3000")),
                    ("monitoring/prometheus.png", svc("Prometheus", ":9090")),
                    ("monitoring/prometheus.png", svc("blackbox-exporter", ":9115"))]),
        ("row", *NODE)])
    h_apps = vm(20, sx + 340, A + h_mon + 20, "vm-apps", "10.77.20.20", "Ubuntu Server 24.04", [
        ("docker", [("apps/homepage.png", svc("Homepage", ":3001")),
                    ("apps/home-assistant.svg", svc("Home Assistant", ":8123")),
                    ("apps/n8n.svg", svc("n8n", ":5678")),
                    ("apps/freshrss.svg", svc("FreshRSS", ":8081"))]),
        ("row", *NODE)])
    servers_h = 50 + max(h_infra + 20 + h_code, h_mon + 20 + h_apps) + 20
    zone(20, sx, sy, 660, servers_h)
    text(f"<b>VLAN20 Servers</b>", sx + 10, sy + 5, 400, 30)

    y = sy
    # Management
    h = vm(10, rx + 20, y + 50, "vm-omada", "10.77.10.3", "Ubuntu Server 24.04", [("row", "network/omada-controller.png", "Omada Controller")])
    mgmt_h = 50 + h + 20
    zone(10, rx, y, 340, mgmt_h)
    text("<b>VLAN10 Management</b>", rx + 10, y + 5, 320, 30)
    y += mgmt_h + 20
    # Lab
    h1 = vm(40, rx + 20, y + 50, "vm-dev", "10.77.40.21", "Ubuntu Server 24.04", [("row", *NODE)])
    h2 = vm(40, rx + 20, y + 50 + h1 + 20, "vm-windows", "DHCP", "Windows 11（任意起動）", [], head_icon="platform/windows-11.svg")
    lab_h = 50 + h1 + 20 + h2 + 20
    zone(40, rx, y, 340, lab_h)
    text("<b>VLAN40 Lab</b>　DHCP .100–.199", rx + 10, y + 5, 320, 30)
    y += lab_h + 20
    # DMZ
    zone(70, rx, y, 340, 110)
    text("<b>VLAN70 DMZ</b>（今は空）", rx + 10, y + 5, 320, 30)
    text("外部に触れるものを将来置く", rx + 20, y + 40, 300, 60)
    y += 110

    left_bottom = sy + servers_h
    gh = max(left_bottom, y) - gy + 20 + 60
    grp = []
    frame(gx, gy, 1060, gh, COLOR[10][0], COLOR[10][1], opacity=40, to=grp)  # Proxmox ホストは Management（VLAN10）の色
    back.insert(gi, grp[0])
    icon("platform/proxmox.png", gx + 20, gy + 20, 40, 40, max_px=120)
    text(f"{name_ip('pve', '10.77.10.10')}<br><i>vmbr0.10</i>（VLAN10、tag 付き）<br>Proxmox 9.1（Debian 13 ベース）", gx + 70, gy + 20, 303, 60)
    icon("", 780, 620, 40, 40, svg=ethernet_svg())
    text("nic0", 830, 635, 60, 20)
    row(*NODE, gx + 20, gy + gh - 50, 220)

    # Buffalo と Trusted / IoT / Guests ------------------------------------------
    edge([(960, 460), (960, 500), (1410, 500), (1410, 530)], color=COLOR[30][1])  # p3: access VLAN30（VLAN の色）
    text("p3: access VLAN30（untagged）", 1000, 470, 300, 24)
    edge([(910, 460), (910, 580), (1200, 580), (1200, 640)], color=COLOR[30][1])  # p4: access VLAN30（VLAN の色）
    text("p4: access VLAN30（untagged）", 920, 550, 260, 24)
    icon("hardware/buffalo-ap.png", 1348, 517, 126.5, 115, max_px=600)
    icon("", 1448, 494, 40, 40, svg=wifi_svg(), rotation=45)  # AP が Wi-Fi を出していることを示す
    text(f"<b>Buffalo WSR-1800AX4P</b><br>{ip('10.77.30.10')}<br>AP モード（管理画面は Trusted 上）", 1461.25, 541, 230, 60)

    tx, ty = 1140, 640
    zone(30, tx, ty, 260, 300)                        # 有線（draw.io で 2 つに分けた）
    text("<b>VLAN30 Trusted</b>　DHCP .100–.199", tx + 10, ty + 5, 240, 30)
    zone(30, tx + 280, ty, 260, 300)                  # Wi-Fi
    text("<b>VLAN30 Trusted</b> Wi-Fi接続", tx + 287, ty + 5, 240, 30)
    text("<i>有線（Dell U2725QE 経由）</i>", tx + 20, ty + 40, 250, 24)
    device(None, f"<i>canales-macbook-pro-m5</i><br>{ip('DHCP')}<br>MacBook Pro M5", tx + 10, ty + 70, 250, "laptop")
    device(None, f"<i>仕事用 Windows PC</i><br>{ip('DHCP')}<br>会社の VPN", tx + 10, ty + 130, 250, "laptop")
    device(None, f"<i>canales-iphone-14</i><br>{ip('DHCP')}<br>iPhone 14", tx + 290, ty + 64, 230, "mobile", size=(30, 40))
    device("hardware/switchbot.png", f"<i>SwitchBot Hub 2</i><br>{ip('DHCP')}<br>将来 IoT へ移す", tx + 290, ty + 124, 230, size=(40, 40))
    device(None, f"<i>テレビ（無線）</i><br>{ip('DHCP')}<br>将来 IoT へ移す", tx + 290, ty + 184, 230, "computer", size=(40, 40))

    iy = ty + 300 + 20
    zone(50, tx, iy, 260, 150)
    text("<b>VLAN50 IoT</b>（将来）", tx + 10, iy + 5, 240, 30)
    device("hardware/esp32.svg", f"<i>ESP32 + BME280</i><br>{ip('10.77.50.100')}<br>現在は未使用", tx + 10, iy + 50, 250, size=(40, 40))
    text("AP 追加後に使う。2.4GHz のみ、端末間は隔離", tx + 10, iy + 110, 240, 24)
    zone(60, tx + 280, iy, 260, 150)
    text("<b>VLAN60 Guests</b>（将来）", tx + 290, iy + 5, 240, 30)
    device("", f"来客の端末<br>{ip('DHCP')}", tx + 290, iy + 50, 250, size=(40, 40), svg=wifi_svg())
    text("AP 追加後に使う。端末間は隔離、LAN へは全遮断", tx + 290, iy + 110, 240, 24)


def main():
    layout()
    xml = ('<mxGraphModel adaptiveColors="auto" dx="1700" dy="1670" grid="1" gridSize="10" page="1" pageWidth="1720" '
           'pageHeight="1670"><root><mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(back) + "".join(cells) + "</root></mxGraphModel>")
    src = Path(_tmp.name) / "tobe-vlan.drawio"
    src.write_text(xml, encoding="utf-8")
    subprocess.run(["drawio", "-x", "-f", "svg", "-e", "-b", "10", "-o", str(OUT), str(src)], check=True)
    print(f"{OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
