#!/usr/bin/env python3
"""現状（as-is）の構成図を、単体の HTML で作る。段階 3 の後（2026-11-17〜）の、実機のとおりの構成。`vm-omada`（`10.77.10.3`）と SG2210P（`10.77.10.2`）は、2026-11-19 に Management（VLAN10）へ移った（ADR-0031）。Proxmox ホスト（`10.77.10.10`）も、2026-11-19 に VLAN10 へ移った。ER605 の既定のネットワークも、2026-11-20 に Management（VLAN10、`10.77.10.1/24`）に統合した（ADR-0032）。VLAN1 は使わない。p2・空きポートの native は `Blackhole`（VLAN 999）。

最終形（to-be）は ../to-be-diagram/。この図は、to-be-diagram のスクリプトを写して、配置と文字を現状に合わせたもの。見た目の決まりと部品は同じ。
実機を変えたら（IP、VLAN、ポート）、この図を直す。この図は、削除せず、常に実機の状態を表す。to-be-diagram（目指す姿。随時更新する）を追いかけ、実機が追いつくと、ほぼ同じ形になる。

この図の本体はこのスクリプト。下の「配置」の座標と文字から HTML（as-is-diagram.html。ロゴとフォントを埋め込む）を組み、
Markdown から参照する PNG（as-is-diagram.png、ダーク版は as-is-diagram-dark.png）も書き出す。何度実行しても結果は同じ。
計画が変わったら、下の「配置」を直して実行する。

    python3 docs/diagrams/as-is-diagram/make-as-is-diagram.py          # as-is-diagram.html を書き出す
    python3 docs/diagrams/as-is-diagram/make-as-is-diagram.py --png    # さらに Chrome で as-is-diagram.png / as-is-diagram-dark.png を書き出す

必要なもの: macOS の `sips`（アイコンの縮小）、--png には Google Chrome（ヘッドレスで撮る。Playwright は要らない）。
フォントは ../fonts/（Geist と JetBrains Mono。OFL。物理構成図と共通）を HTML に埋め込む。
アイコン素材 `docs/diagrams/assets/icons/` は Git 管理外。無ければ取得する。
内容は docs/architecture/lld/network/ip-addresses.md（IP の正）と docs/architecture/lld/network/omada-controller.md・wsr-1800ax4p.md、platform/proxmox-host.md（機器の設定の正）に合わせる。食い違ったら、文書のほうが正。

見た目の決まり（座標は 10px グリッド。背景の方眼は 20px）:
  - 背景は方眼。文字は Geist（日本語は Hiragino / Noto Sans JP）、IP・ポート・線のラベルは JetBrains Mono。ライト・ダーク両対応。
  - 文字は 14px。ポート・IP は橙、ホスト名（VM、端末）は斜体、見出しは太字。
  - VLAN ごとに枠の色を変える（右上の凡例）。VLAN 枠・VM 枠・Docker 枠は、その VLAN の色を 40% で重ねる（入れ子ほど濃い）。
  - VM 枠は幅 300、内側の余白 20。見出しアイコン 40（枠なし）。サービスの行は高さ 30、アイコン 28 を白いタイル 36 に入れる。
  - VM 直下のサービスと Docker アイコンは VM 枠の左端から 40。Docker 枠の中のサービスは、さらに 20 内側。
  - 行の送りは 40。Docker 枠の高さは「行数 × 40 + 10」。枠どうしの間隔は 20。
  - ポートの VLAN の書き方は `tagged: VLAN…` / `untagged: VLAN…` に統一する。
"""
import base64
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "as-is-diagram.html"
ICONS = HERE.parent / "assets/icons"
LOGO = HERE.parents[2] / "assets/logo"  # リポジトリのロゴ（Git 管理）
FONTS = HERE.parent / "fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1720, 1690

# VLAN ごとの色（塗り, 線）。信頼度の高い VLAN10 から低い VLAN70 へ、色相環を紫→赤と一方向にたどる
# （寒色は信頼できる側、暖色は信頼できない側）。明るさと彩度はそろえる。
COLOR = {
    10: ("oklch(95% 0.035 300)", "oklch(60% 0.13 300)"),  # 紫
    20: ("oklch(95% 0.035 250)", "oklch(60% 0.13 250)"),  # 青
    30: ("oklch(95% 0.035 195)", "oklch(60% 0.13 195)"),  # ティール
    40: ("oklch(95% 0.035 145)", "oklch(60% 0.13 145)"),  # 緑
    50: ("oklch(95% 0.035 95)", "oklch(60% 0.13 95)"),  # 黄
    60: ("oklch(95% 0.035 55)", "oklch(60% 0.13 55)"),  # 橙
    70: ("oklch(95% 0.035 25)", "oklch(60% 0.13 25)"),  # 赤
}
NAME = {10: "Management", 20: "Servers", 30: "Trusted", 40: "Lab", 50: "IoT", 60: "Guests", 70: "DMZ"}

back = []  # 背面（枠）。out より先に描く
out = []   # 前面（アイコン、文字、線）
_tmp = tempfile.TemporaryDirectory()
OFF = [0]  # 凡例より下の内容を下げる量


def ip(v):
    return f'<span class="ip">{v}</span>'


def name_ip(name, addr):
    return f"<i>{name}</i> {ip(addr)}"


def svc(name, port=None):
    return name + (f" {ip(port)}" if port else "")


def pos(x, y, w, h):
    return f"left:{x:g}px;top:{y + OFF[0]:g}px;width:{w:g}px;height:{h:g}px"


def text(value, x, y, w, h, align="left", cls=""):
    out.append(f'<div class="t {cls}" style="{pos(x, y, w, h)};text-align:{align}"><div>{value}</div></div>')


def frame(x, y, w, h, cls, to=None):
    (out if to is None else to).append(f'<div class="f {cls}" style="{pos(x, y, w, h)}"></div>')


def zone(vlan, x, y, w, h):
    frame(x, y, w, h, f"z z{vlan}", to=back)


def _data(path, svg=None, max_px=None):
    """アイコンの data URI。PNG は sips で縮小（HTML が大きくなりすぎないように）。"""
    if svg is not None:
        return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    src = ICONS / path
    if max_px and src.suffix == ".png":
        small = Path(_tmp.name) / src.name
        try:
            subprocess.run(["sips", "-Z", str(max_px), str(src), "--out", str(small)], check=True, capture_output=True)
            src = small
        except subprocess.CalledProcessError:  # 拡張子は png でも中身が WebP のもの（switchbot.png）。小さいのでそのまま使う
            pass
    mime = "svg+xml" if src.suffix == ".svg" else "png"
    return f"data:image/{mime};base64," + base64.b64encode(src.read_bytes()).decode()


def icon(path, x, y, w, h, max_px=None, svg=None, rotation=0):
    """svg は文字列、または (ライト用, ダーク用) の組。path も (ライト用, ダーク用) のファイルの組にできる。
    組のときは、テーマに合わせて切り替える。"""
    st = pos(x, y, w, h) + (f";transform:rotate({rotation}deg)" if rotation else "")
    if isinstance(path, tuple):
        out.append(f'<img class="i lt" style="{st}" src="{_data(path[0], None, max_px)}" alt="">')
        out.append(f'<img class="i dk" style="{st}" src="{_data(path[1], None, max_px)}" alt="">')
    elif isinstance(svg, tuple):
        out.append(f'<img class="i lt" style="{st}" src="{_data(None, svg[0])}" alt="">')
        out.append(f'<img class="i dk" style="{st}" src="{_data(None, svg[1])}" alt="">')
    else:
        out.append(f'<img class="i" style="{st}" src="{_data(path, svg, max_px)}" alt="">')


def wifi_svg(color):
    cx, cy, k = 200, 340, 0.70710678
    arcs = "".join(
        f'<path d="M{cx - r * k:.1f} {cy - r * k:.1f} A{r} {r} 0 0 1 {cx + r * k:.1f} {cy - r * k:.1f}" fill="none" stroke-width="32"/>'
        for r in (95, 150, 205))
    dot = f'<path d="M{cx} {cy} L{cx - 52 * k:.1f} {cy - 52 * k:.1f} A52 52 0 0 1 {cx + 52 * k:.1f} {cy - 52 * k:.1f} Z" stroke="none"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><g fill="{color}" stroke="{color}">{arcs}{dot}</g></svg>')


def ethernet_svg(color):
    body = ('<rect x="15" y="45" width="482" height="420" rx="45"/>'
            '<path d="M77 105H435V285H405V345H345V405H167V345H107V285H77Z"/>'
            '<path d="M135 165V245M195 165V245M255 165V245M315 165V245M375 165V245M77 405H105M407 405H435"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><g fill="none" stroke="{color}" stroke-width="30" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>')


def mono_pair(make):
    """ライト（墨色）とダーク（明るい灰）の両方を作る。"""
    return (make("#2b3140"), make("#e4e7ee"))


def dark_pair(path):
    """素材の SVG を、ダークテーマでは塗りを白にした組にする（公式のダーク用ロゴ GitHub Mark White、Tailscale の白いロゴと同じ見た目）。"""
    raw = (ICONS / path).read_text()
    i = raw.index(">", raw.index("<svg")) + 1
    return (raw, raw[:i] + "<style>path{fill:#fff!important}</style>" + raw[i:])


def edge(points, arrow=None, width=3, color=None, dash=False):
    """arrow は None（矢印なし）、"end"（終点側）、"start"（始点側）。color は CSS の色（既定は墨色）。dash は破線（Wi-Fi）。"""
    pts = [(x, y + OFF[0]) for x, y in points]
    d = "M" + " L".join(f"{x:g} {y:g}" for x, y in pts)
    mk = {"end": ' marker-end="url(#ar)"', "start": ' marker-start="url(#ar)"'}.get(arrow, "")
    col = color or "var(--neutral)"
    out.append(f'<svg class="e" width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true">'
               f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{width}"{' stroke-dasharray="6 5"' if dash else ''}{mk}/></svg>')


# 部品 -------------------------------------------------
def row(ic, label, x, y, w):
    """サービス行。アイコン 30、文字は 10 右。"""
    out.append(f'<div class="tile" style="{pos(x - 3, y - 3, 36, 36)}"></div>')  # 白いタイル（ロゴは白地用なので、ダークでも白）
    if isinstance(ic, tuple):
        icon(None, x + 1, y + 1, 28, 28, svg=ic[0])  # ライト用の版
    else:
        icon(ic, x + 1, y + 1, 28, 28, max_px=120)
    text(label, x + 40, y, w - 40, 30, cls="nw")


def vm(vlan, x, y, name, addr, os_text, items):
    """VM 枠（幅 300）。items は ("row", アイコン, 文字) か ("docker", [(アイコン, 文字), ...])。高さを返す。"""
    cur = y + 70
    parts = []
    for kind, *rest in items:
        if kind == "row":
            parts.append(("row", rest[0], rest[1], cur))
            cur += 40
        else:
            rows = [(("platform/docker-mark-black.svg", "platform/docker-mark-white.svg"), "Docker containers")] + rest[0]
            parts.append(("docker", rows, None, cur))
            cur += 40 * len(rows) + 10 + 20
    h = (cur - y) if items else 80
    frame(x, y, 300, h, f"z z{vlan}")
    icon("platform/ubuntu.png", x + 20, y + 20, 40, 40, max_px=160)
    text(f"{name_ip(name, addr)}<br>{os_text}", x + 70, y + 20, 210, 40)
    for kind, a, b, cy in parts:
        if kind == "row":
            row(a, b, x + 40, cy, 220)
        else:
            frame(x + 20, cy, 260, 40 * len(a) + 10, f"z z{vlan}")
            for k, (ic, label) in enumerate(a):
                if k == 0:  # 見出し（Docker アイコンはタイルに入れない。2026-11-19 からのロゴ。ライトは黒、ダークは白。公式の色をそのまま使う）
                    icon(ic, x + 40, cy + 10, 30, 30, max_px=120)
                    text(label, x + 80, cy + 10, 180, 30)
                else:  # 中のサービスは Docker アイコンより内側
                    row(ic, label, x + 60, cy + 10 + 40 * k, 200)
    return h


def device(ic, label, x, y, w, size=(40, 30), svg=None, tile=False):
    """端末の行（高さ 60）。アイコンの中心とテキストの中心を同じ高さに置く。
    tile=True は、サービスのロゴ（SwitchBot）。サービスの行と同じ、白いタイル 36 にアイコン 28。"""
    cx, cy = x + 30, y + 30  # アイコンの中心
    if tile:
        out.append(f'<div class="tile" style="{pos(cx - 18, cy - 18, 36, 36)}"></div>')
        icon(ic, cx - 14, cy - 14, 28, 28, max_px=160, svg=svg)
    else:
        iw, ih = size
        icon(ic, cx - iw / 2, cy - ih / 2, iw, ih, max_px=160, svg=svg)
    text(label, x + 60, y, w - 60, 60)


NODE = ("monitoring/prometheus.png", svc("node_exporter", ":9100"))


def layout():
    # 凡例（右上。縦一列。上ほど信頼度が高い） ------------------------------------------
    lx, ly = 1050, 20
    frame(1040, ly, 660, 222, "legend")  # 凡例は 1 つの四角（左: VLAN 一覧、右: 線と文字）
    text(f"<b>VLANs</b> ({ip('10.77.&lt;VLAN&gt;.0/24')})", lx - 3, ly + 6, 380, 26)
    text("Trust", lx - 3, ly + 39, 54, 22, align="center", cls="el")
    edge([(lx + 24, ly + 66), (lx + 24, ly + 200)], arrow="start")  # 矢じりが上。上ほど信頼度が高い
    for k, v in enumerate((10, 20, 30, 40, 50, 60, 70)):
        y = ly + 56 + 22 * k
        frame(lx + 50, y + 2, 30, 18, f"sw z{v}")
        text(f"VLAN{v} {NAME[v]}", lx + 90, y, 290, 22)

    # 外部サービス（左上） --------------------------------------------------------------
    frame(20, 20, 500, 210, "ext")
    text("<b>External Services</b>", 40, 30, 300, 30)
    services = [
        ("external/healthchecks.svg", "Healthchecks.io"), ("external/slack.svg", "Slack"), ("external/cloudflare.svg", "Cloudflare"),
        ("external/letsencrypt.svg", "Let's Encrypt"), (mono_pair_dark("external/tailscale.svg"), "Tailscale"),
        (mono_pair_dark("external/github.svg"), "GitHub"), ("network/omada.svg", "Omada Cloud"),
    ]
    for k, (ic, label) in enumerate(services):
        col, rowi = divmod(k, 4)
        row(ic, label, 40 + 240 * col, 70 + 40 * rowi, 200)
    edge([(520, 125), (852, 125)])

    # 凡例の右半分: 線と文字の意味
    edge([(1440, 30), (1440, 232)], width=1, color="var(--rule2)")
    text("<b>Lines and text</b>", 1450, 24, 240, 26)
    for k, (w, label) in enumerate([(3, "Ethernet (upstream WAN)"), (5, "Ethernet (trunk)")]):
        cy = 63 + 22 * k
        edge([(1450, cy), (1490, cy)], width=w)
        text(label, 1500, cy - 11, 190, 22)
    edge([(1450, 63 + 22 * 2), (1490, 63 + 22 * 2)], width=2, dash=True)
    text("Wi-Fi", 1500, 52 + 22 * 2, 190, 22)
    text("<i>Italic</i>: hostname (VM, device)", 1450, 52 + 22 * 3, 240, 22)
    text(f"{ip('Orange')}: IP address, port", 1450, 52 + 22 * 4, 240, 22)

    OFF[0] = 80  # ここから下は 80 下げる（凡例と LAN の枠が重ならないように）

    # インターネット・ルーター・スイッチ ------------------------------------------------
    out.append(f'<div class="tile" style="{pos(852, 17, 56, 56)}"></div>')
    icon(None, 860, 25, 40, 40, svg=INTERNET[0])
    text("Internet", 920, 30, 100, 30)
    edge([(880, 73), (880, 219)])  # タイルの下から ER605 の上まで、1 本で繋ぐ
    text(f"Building router {ip('172.22.0.1')} (double NAT)", 520, 94, 350, 24, align="right", cls="el")
    text("WAN (DHCP)", 750, 128, 120, 24, align="right", cls="el")

    # LAN 全体の枠 ---------------------------------------------------------------------
    frame(20, 170, 1680, 1400, "lan", to=back)
    frame(40, 180, 200, 40, "lanlabel", to=back)
    text("<b>LAN</b><br>10.77.0.0/16", 40, 180, 200, 40, align="center")

    icon("hardware/tplink-er605.png", 789, 219, 182, 61, max_px=700)  # 実寸の幅の比（ER605 158mm : SG2210P 209mm ≒ 0.76）。下端は 280 のまま
    text(f"<b>TP-Link ER605 V2</b><br>{ip('10.77.10.1')} (VLAN10)<br>Gateway for each VLAN ({ip('10.77.&lt;VLAN&gt;.1')}), DHCP, ACL (allow all)", 1010, 200, 420, 80)
    edge([(880, 280), (880, 380)], width=5)  # p1: trunk（太い線）
    text("ER605 p2 ⇔ SG2210P p1: trunk (untagged: VLAN10 / tagged: VLAN20,30,40,50,60,70)", 890, 320, 700, 40, cls="el")

    icon("hardware/tplink-sg2210p.png", 760, 380, 240, 80, max_px=700)
    text(f"<b>TP-Link SG2210P</b><br>{ip('10.77.10.2')} (VLAN10)<br>p1: ER605 / p2: pve01 / p3: Buffalo / p4: Dell U2725QE<br>p5–p7: unused (native Blackhole) / p8: recovery port (native VLAN10)", 1010, 380, 690, 80)

    # Proxmox ---------------------------------------------------------------------------
    gx, gy = 40, 640
    icon("hardware/thinkcentre-m70q-tiny.png", 433.03, 586, 293.94, 97, max_px=700)
    text("<b>Lenovo ThinkCentre M70q Tiny Gen1</b><br>CPU: Intel Core i5-10400T (6C/12T)<br>RAM: 1 x 8 GB + 1 x 16 GB DDR4-3200<br>"
         "Storage: 1 x 256GB NVMe SSD", 430, 519, 300, 80, align="center")
    edge([(800, 460), (800, 620)], width=5)  # p2: trunk（太い線）
    text("p2: trunk (native: Blackhole / tagged: VLAN10,20,30,40,50,60,70)", 220, 468, 570, 24, align="right", cls="el")

    # 右の列（Management / Lab / DMZ）と、Servers の 2 列を先に配置して高さを決める
    gi = len(back)                      # Proxmox の枠は、中の VLAN 枠より前に入れる
    sx, sy = gx + 20, gy + 100          # Servers 枠
    rx = sx + 660 + 20                  # 右の列
    A = sy + 50
    h_infra = vm(20, sx + 20, A, "vm-infra", "10.77.20.10", "Ubuntu Server 24.04", [
        ("row", "network/coredns.png", svc("CoreDNS", ":5353")),
        ("row", mono_pair_dark("external/tailscale.svg"), svc("Tailscale", ":41641")),
        ("docker", [("network/adguard.png", svc("AdGuard", ":53, :3000")),
                    ("network/unbound.svg", svc("Unbound", ":5335")),
                    ("network/caddy.png", svc("Caddy", ":80, :443"))]),
        ("row", *NODE)])
    h_code = vm(20, sx + 20, A + h_infra + 20, "vm-code", "10.77.20.30", "Ubuntu Server 24.04", [
        ("row", "dev/claude-code.svg", "Claude Code"),
        ("row", "dev/cloudcli.svg", svc("CloudCLI", ":3001")),
        ("row", "dev/code-server.png", svc("code-server", ":8080")),
        ("row", *NODE)])
    h_mon = vm(20, sx + 340, A, "vm-monitoring", "10.77.20.11", "Ubuntu Server 24.04", [
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
    text("<b>VLAN20 Servers</b>", sx + 10, sy + 5, 400, 30)

    y = sy
    # Management（VLAN10）: vm-omada（2026-11-19〜。NIC 1 枚。ER605・SG2210P もここにつなぐ）
    h = vm(10, rx + 20, y + 50, "vm-omada", "10.77.10.3", "Ubuntu Server 24.04", [("row", "network/omada-controller.png", "Omada Controller")])
    mgmt_h = 50 + h + 20
    zone(10, rx, y, 340, mgmt_h)
    text("<b>VLAN10 Management</b>", rx + 10, y + 5, 320, 30)
    y += mgmt_h + 20
    # Lab
    h1 = vm(40, rx + 20, y + 50, "vm-dev", "10.77.40.10", "Ubuntu Server 24.04", [("row", *NODE)])
    lab_h = 50 + h1 + 20
    zone(40, rx, y, 340, lab_h)
    text("<b>VLAN40 Lab</b>", rx + 10, y + 5, 320, 30)
    y += lab_h + 20
    # DMZ
    zone(70, rx, y, 340, 110)
    text("<b>VLAN70 DMZ</b> (unused)", rx + 10, y + 5, 320, 30)
    text("For services exposed to the internet", rx + 20, y + 40, 300, 60)
    y += 110

    left_bottom = sy + servers_h
    gh = max(left_bottom, y) - gy + 20 + 60
    grp = []
    frame(gx, gy, 1060, gh, "z z10", to=grp)  # Proxmox ホストは Management（VLAN10）の色
    back.insert(gi, grp[0])
    icon(("platform/proxmox.svg", "platform/proxmox-dark.svg"), gx + 20, gy + 20, 40, 40)  # ダークは黒い部分が白い版
    text(f"{name_ip('pve01', '10.77.10.10')}<br><i>vmbr0.10</i> (tagged: VLAN10)<br>Proxmox 9.1 (based on Debian 13)", gx + 70, gy + 20, 303, 60)
    icon(None, 780, 620, 40, 40, svg=mono_pair(ethernet_svg))
    text("nic0", 830, 635, 60, 20)
    row(*NODE, gx + 20, gy + gh - 50, 220)

    # Trusted / IoT / Guests ----------------------------------------------------------
    # VLAN30 は 1 つの枠。Dell のディスプレイ（有線。ノート PC は USB-C でディスプレイの NIC を使う）と
    # Buffalo（AP）を枠の中に置き、端末はつながっている機器の下にぶら下げる（有線は実線、Wi-Fi は破線）。
    tx, ty = 1120, 640
    zone(30, tx, ty, 570, 320)
    dx, ax = tx + 40, tx + 340                         # ディスプレイと AP のアイコンの中心（x）
    edge([(910, 460), (910, 580), (dx, 580), (dx, ty + 57)], color="var(--l30)")  # p4: access VLAN30（VLAN の色）
    text("p4: access (untagged: VLAN30)", 920, 550, 260, 24, cls="el")
    edge([(960, 460), (960, 500), (ax, 500), (ax, ty + 45)], color="var(--l30)")  # p3: access VLAN30（VLAN の色）
    text("p3: access (untagged: VLAN30)", 1000, 470, 300, 24, cls="el")
    text("<b>VLAN30 Trusted</b>", dx + 16, ty + 5, 200, 30)  # 見出しは p4 の線の右

    # 有線: ディスプレイ（DHCP）に、ノート PC をぶら下げる
    device("hardware/clients/display.png", f"<b>Dell U2725QE</b><br>{ip('DHCP')}<br>Display with USB-C dock", tx + 10, ty + 57, 240, size=(54, 36))
    edge([(dx, ty + 105), (dx, ty + 245)], width=2)
    for k, label in enumerate(["<i>canales-macbook-pro-m5</i><br>MacBook Pro M5", "<i>Work Windows Laptop</i><br>Corporate VPN"]):
        cy = ty + 185 + 60 * k
        edge([(dx, cy), (dx + 16, cy)], width=2)
        device(f"hardware/clients/{'macbook' if k == 0 else 'windows-laptop'}.png", label, dx + 12, cy - 30, 268, size=(52, 52))
    text("USB-C", dx + 6, ty + 118, 60, 20, cls="el")

    # Wi-Fi: AP に、無線の端末をぶら下げる
    icon("hardware/buffalo-ap.png", ax - 33, ty + 45, 66, 60, max_px=300)
    icon(None, ax + 12, ty + 22, 24, 24, svg=mono_pair(wifi_svg), rotation=45)  # AP が Wi-Fi を出していることを示す
    text(f"<b>Buffalo WSR-1800AX4P</b><br>{ip('10.77.30.50')}<br>AP mode", ax + 40, ty + 45, 190, 60)
    edge([(ax, ty + 105), (ax, ty + 275)], width=2, dash=True)
    clients = [("iphone.png", f"<i>canales-iphone-14</i><br>{ip('DHCP')}<br>iPhone 14", False),
               ("switchbot.png", f"<i>SwitchBot Hub 2</i><br>{ip('DHCP')}<br>To be moved to IoT", True),
               ("tv.png", f"<i>TV (Wi-Fi)</i><br>{ip('DHCP')}<br>To be moved to IoT", False)]
    for k, (ic, label, tile) in enumerate(clients):
        cy = ty + 155 + 60 * k
        edge([(ax, cy), (ax + 22, cy)], width=2, dash=True)
        device(f"hardware/clients/{ic}", label, ax + 20, cy - 30, 210, size=(52, 52), tile=tile)

    iy = ty + 320 + 20
    zone(50, tx, iy, 275, 170)
    text("<b>VLAN50 IoT</b> (unused)", tx + 10, iy + 5, 240, 30)
    text("Used once an AP is added.<br>2.4 GHz only, client isolation", tx + 10, iy + 50, 240, 40)
    zone(60, tx + 295, iy, 275, 170)
    text("<b>VLAN60 Guests</b> (unused)", tx + 305, iy + 5, 240, 30)
    device("", f"Guest devices<br>{ip('DHCP')}", tx + 305, iy + 50, 250, size=(40, 40), svg=mono_pair(wifi_svg))
    text("Used once an AP is added.<br>Client isolation, no access to the LAN", tx + 305, iy + 120, 255, 40)

    # 右下: homelab の横長のロゴ（LAN の枠の中の空き。421 × 124）
    icon((str(LOGO / "logo-stack-light.svg"), str(LOGO / "logo-stack-dark.svg")), 1380, 1462, 300, 88)


mono_pair_dark = dark_pair
INTERNET = None
# Internet の地球儀（Lucide の globe。線画）
GLOBE = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="COLOR" stroke-width="1.6" '
         'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/>'
         '<path d="M3 12h18M12 3c2.8 2.6 4.2 5.6 4.2 9S14.8 18.4 12 21c-2.8-2.6-4.2-5.6-4.2-9S9.2 5.6 12 3z"/></svg>')


def css():
    vl = "".join(f"--f{v}:{f};--l{v}:{l};" for v, (f, l) in COLOR.items())
    zc = "".join(f".z{v}{{--f:var(--f{v});--l:var(--l{v})}}" for v in COLOR)
    light = f"""
  --paper:oklch(98.5% 0.004 250);--paper2:oklch(96.5% 0.005 252);--card:oklch(100% 0 0 / .85);
  --rule:oklch(93% 0.007 255);--rule2:oklch(83% 0.011 255);--muted:oklch(56% 0.013 255);
  --neutral:oklch(46% 0.015 255);--ink:oklch(24% 0.020 258);--ink2:oklch(34% 0.018 257);
  --orange:oklch(60% 0.17 52);--veil:oklch(98.5% 0.004 250 / .85);--zfill:40%;--zline:40%;{vl}"""
    dark = f"""
  --paper:oklch(18% 0.012 255);--paper2:oklch(22% 0.014 255);--card:oklch(22% 0.014 255 / .85);
  --rule:oklch(24% 0.013 255);--rule2:oklch(38% 0.018 255);--muted:oklch(65% 0.014 255);
  --neutral:oklch(72% 0.012 255);--ink:oklch(94% 0.008 255);--ink2:oklch(85% 0.010 255);
  --orange:oklch(76% 0.14 60);--veil:oklch(18% 0.012 255 / .85);--zfill:16%;--zline:60%;"""
    fonts = "".join(
        f'@font-face{{font-family:"{fam}";font-style:normal;font-weight:{wt};font-display:swap;'
        f'src:url(data:font/woff2;base64,{base64.b64encode((FONTS / fn).read_bytes()).decode()}) format("woff2")}}\n'
        for fam, fn, wt in (("Geist", "Geist.woff2", "100 900"), ("JetBrains Mono", "JetBrainsMono.woff2", "100 800")))
    return fonts + f"""
:root{{color-scheme:light;{light}
  --display:"Geist","Hiragino Sans","Yu Gothic UI","Noto Sans CJK JP","Noto Sans JP",ui-sans-serif,system-ui,sans-serif;
  --mono:"JetBrains Mono","Hiragino Sans","Yu Gothic UI","Noto Sans CJK JP","Noto Sans JP",ui-monospace,Menlo,monospace}}
:root[data-theme=dark]{{color-scheme:dark;{dark}}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{color-scheme:dark;{dark}}}}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--paper);color:var(--ink);font-family:var(--display)}}
.canvas{{position:relative;width:{W}px;height:{H}px;overflow:hidden;background-color:var(--paper);
  background-image:linear-gradient(var(--rule) 1px,transparent 1px),linear-gradient(90deg,var(--rule) 1px,transparent 1px);
  background-size:20px 20px;background-position:-1px -1px}}
.f,.t,.i,.e{{position:absolute}}
.e{{left:0;top:0;pointer-events:none}}
.t{{display:flex;align-items:center;font-size:14px;line-height:1.3;font-weight:400}}
.t>div{{width:100%}}
b{{font-weight:600}}
i{{font-style:italic}}
.ip{{font-family:var(--mono);font-size:12px;letter-spacing:0;color:var(--orange);margin-left:.2em}}
.nw{{white-space:nowrap}}
/* 線のラベル: 等幅、線が下を通っても読めるように地の色で縁取る */
.el{{font-family:var(--mono);font-size:12px;letter-spacing:.04em;color:var(--ink2);
  text-shadow:0 0 2px var(--paper),0 0 2px var(--paper),0 0 4px var(--paper),0 0 6px var(--paper)}}
.el .ip{{font-size:12px}}
.i{{object-fit:contain}}
.tile{{position:absolute;background:#fff;border:1px solid var(--rule2);border-radius:8px;box-shadow:0 1px 2px oklch(24% .02 258 / .08)}}
.dk{{display:none}}
:root[data-theme=dark] .lt{{display:none}}:root[data-theme=dark] .dk{{display:block}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]) .lt{{display:none}}:root:not([data-theme=light]) .dk{{display:block}}}}
/* VLAN の枠。VLAN 枠・VM 枠・Docker 枠は同じ色を重ねるので、入れ子ほど濃くなる */
{zc}
.z{{border-radius:16px;border:2px dashed color-mix(in srgb,var(--l) var(--zline),transparent);
  background:color-mix(in srgb,var(--f) var(--zfill),transparent)}}
:root[data-theme=dark] .z{{background:color-mix(in srgb,var(--l) var(--zfill),transparent)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]) .z{{background:color-mix(in srgb,var(--l) var(--zfill),transparent)}}}}
.sw{{border-style:solid;border-radius:4px;border-width:1.5px;background:color-mix(in srgb,var(--f) 85%,transparent)}}
:root[data-theme=dark] .sw{{background:color-mix(in srgb,var(--l) 35%,transparent)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]) .sw{{background:color-mix(in srgb,var(--l) 35%,transparent)}}}}
.ext{{border-radius:16px;border:2px solid color-mix(in srgb,oklch(62% 0.02 255) 70%,transparent);background:color-mix(in srgb,oklch(94% 0.01 255) 70%,transparent)}}
:root[data-theme=dark] .ext{{background:color-mix(in srgb,oklch(62% 0.02 255) 22%,transparent)}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]) .ext{{background:color-mix(in srgb,oklch(62% 0.02 255) 22%,transparent)}}}}
.lan{{border-radius:16px;border:2px dashed color-mix(in srgb,var(--muted) 70%,transparent);background:color-mix(in srgb,var(--paper) 70%,transparent)}}
.lanlabel{{border-radius:16px;border:2px solid color-mix(in srgb,var(--muted) 70%,transparent);background:var(--paper2)}}
.legend{{border-radius:10px;border:1px solid var(--rule2);background:var(--card)}}
"""


def build():
    global INTERNET
    INTERNET = tuple(GLOBE.replace("COLOR", c) for c in ("#2b3140", "#e4e7ee"))  # 線の色をテーマに合わせる
    layout()
    marker = ('<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>'
              '<marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" '
              'orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/></marker></defs></svg>')
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>Homelab diagram (as-is)</title>\n<style>' + css() + '</style>\n'
            '<script>if(location.hash==="#dark")document.documentElement.dataset.theme="dark";'
            'if(location.hash==="#light")document.documentElement.dataset.theme="light"</script>\n</head>\n<body>\n'
            + marker + '\n<div class="canvas">\n' + "\n".join(back) + "\n" + "\n".join(out) + "\n</div>\n</body>\n</html>\n")
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT} ({OUT.stat().st_size // 1024} KB)")


def render():
    for suffix, frag in (("", "#light"), ("-dark", "#dark")):
        png = HERE / f"as-is-diagram{suffix}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--screenshot={png}", OUT.as_uri() + frag],
                       check=True, capture_output=True)
        print(png)


if __name__ == "__main__":
    build()
    if "--png" in sys.argv:
        render()
