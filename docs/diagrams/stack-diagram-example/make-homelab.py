"""homelab の現行の構成図の下書き HTML（stack-diagram スキルのテンプレート）を作る。

座標のずれを避けるため、ノードの中心 x と上端 y から、箱・グループ・線の座標を計算する。
手順（詳しくは docs/diagrams/README.md）:

    python3 make-homelab.py draft.html
    python3 ~/.claude/skills/stack-diagram/scripts/build.py draft.html <icons-dir> homelab.html \\
        --fonts ~/.claude/skills/stack-diagram/assets/fonts
    python3 ~/.claude/skills/stack-diagram/scripts/render_png.py homelab.html homelab.png --selector .canvas --scale 2

<icons-dir> は Git 管理外（取得し直す）。必要なもの: stack-diagram スキル（~/.claude/skills/stack-diagram）、
Playwright と Chromium（PNG の書き出し）。
"""
import re, pathlib, sys
TPL = pathlib.Path.home() / ".claude/skills/stack-diagram/assets/template.html"
W, H = 1440, 1170

def node(cx, top, icon, name, role, tile=""):
    cls = f"tile {tile}".strip()
    return (f'    <div class="node" style="left:{cx-66}px;top:{top}px">\n'
            f'      <div class="{cls}"><img src="%%ICON_{icon}%%" alt=""></div>\n'
            f'      <div class="name"><span>{name}</span></div><div class="role"><span>{role}</span></div>\n'
            f'    </div>\n')

def group(kind, left, top, w, h, label, icon=None):
    img = f'<img src="%%ICON_{icon}%%" alt="">' if icon else ""
    return (f'    <div class="group {kind}" style="left:{left}px; top:{top}px; width:{w}px; height:{h}px;">\n'
            f'      <div class="g-label">{img}<span>{label}</span></div>\n    </div>\n')

groups, nodes, edges = [], [], []
G = groups.append; N = nodes.append; E = edges.append

# 外部サービス（上段。タイルの上端 100、グループは 40〜250）
ext = [("cloudflare", "Cloudflare", "DNS・DNS-01", 1012), ("tailscale", "Tailscale", "コントロールプレーン", 872),
       ("letsencrypt", "Let's Encrypt", "証明書", 732), ("omada", "Omada Cloud", "クラウドアクセス", 592),
       ("github", "GitHub", "リポジトリ・CI", 452), ("slack", "Slack", "アラート通知", 312),
       ("healthchecks", "Healthchecks.io", "外部 Heartbeat", 172)]
G(group("gb", 82, 40, 1102 - 82 + 0, 210, "外部サービス"))
for icon, name, role, cx in ext: N(node(cx, 100, icon, name, role))

# インターネットと Buffalo（右の列）
N(node(1300, 100, "internet", "Internet", "建物の共用ルーター"))
N(node(1300, 260, "router", "Buffalo", "WSR-1800AX4P · .1"))

# Proxmox（40,330 〜 1126,1130）と VM のグループ
G(group("ga", 40, 330, 1086, 800, "Proxmox VE · 192.168.11.10", "proxmoxsq"))
col = {1: 64, 2: 418, 3: 772}
def vm(c, top, h, label, w=330): G(group("ga-nested", col[c], top, w, h, label, "ubuntu"))
vm(1, 378, 210, "vm-omada · 192.168.11.12")
vm(1, 612, 350, "vm-apps · 192.168.11.20")
vm(2, 378, 350, "vm-monitoring · 192.168.11.13")
vm(2, 752, 350, "vm-code · 192.168.11.22")
vm(3, 378, 490, "vm-infra · 192.168.11.11")
vm(3, 892, 210, "vm-dev .21（手動起動）")

# col1
N(node(304, 438, "omadactl", "Omada Controller", "ネットワーク機器の管理"))
N(node(154, 672, "homepage", "Homepage", "ダッシュボード"))
N(node(304, 672, "homeassistant", "Home Assistant", "ホームオートメーション"))
N(node(154, 812, "n8n", "n8n", "ワークフロー"))
N(node(304, 812, "freshrss", "FreshRSS", "RSS リーダー"))
# col2
N(node(508, 438, "prometheus", "Prometheus", "メトリクス"))
N(node(658, 438, "prometheus", "Alertmanager", "アラート通知"))
N(node(508, 578, "grafana", "Grafana", "可視化"))
N(node(658, 578, "prometheus", "blackbox", "外形監視"))
N(node(508, 812, "claude", "Claude Code", "AI コーディング"))
N(node(658, 812, "codeserver", "code-server", "ブラウザの VS Code"))
N(node(508, 952, "cloudcli", "CloudCLI", "Web ターミナル"))
# col3
N(node(862, 438, "tailscale", "Tailscale", "subnet router"))
N(node(1012, 438, "caddy", "Caddy", "リバースプロキシ"))
N(node(862, 578, "adguard", "AdGuard Home", "DNS・広告ブロック"))
N(node(1012, 578, "unbound", "Unbound", "再帰リゾルバ"))
N(node(862, 718, "coredns", "CoreDNS", "内部ゾーン"))
N(node(862, 952, "vmdev", "vm-dev", "検証用"))

# LAN の端末（右の列）
G(group("gb", 1210, 378, 180, 630, "LAN の端末"))
N(node(1300, 438, "macbook", "MacBook Pro", "Mac（作業用）"))
N(node(1300, 578, "iphone", "iPhone", "スマホ"))
N(node(1300, 718, "switchbot", "SwitchBot Hub 2", "Wi-Fi · DHCP"))
N(node(1300, 858, "esp32", "ESP32 + BME280", "現在は停止中"))

# 線
def path(cls, d, marker=True, both=False):
    m = ' marker-end="url(#ar)"' if marker else ""
    s = ' marker-start="url(#ar)"' if both else ""
    E(f'      <path class="{cls}" d="{d}"{m}{s}/>')
def label(x, y, t, accent=False, anchor="middle"):
    E(f'      <text class="el{" a" if accent else ""}" x="{x}" y="{y}" text-anchor="{anchor}">{t}</text>')

path("n", "M1300 206 V256"); label(1310, 236, "WAN（二重 NAT）", anchor="start")
path("n", "M1266 290 H1100 V326"); label(1183, 282, "有線 LAN")
path("e", "M1266 468 H1046"); label(1156, 460, "HTTPS", True)
path("e", "M1266 608 H1180 V468", marker=False)
path("n", "M1030 434 V206"); label(1040, 300, "DNS-01", anchor="start")
path("n", "M985 434 V270 H732 V206"); label(797, 262, "ACME")
path("n", "M862 434 V420 H938 V206", both=True); label(948, 322, "VPN", anchor="start")
path("n", "M655 434 V284 H312 V206"); label(476, 276, "通知")
path("n", "M686 434 V298 H172 V206"); label(240, 290, "Watchdog")
path("n dash", "M304 434 V312 H592 V206"); label(602, 234, "試用中", anchor="start")
path("n", "M896 608 H978"); label(937, 600, "DNS")
path("n", "M862 684 V714"); label(872, 702, "lab.kanare.dev", anchor="start")

html = TPL.read_text(encoding="utf-8")
head, rest = html.split("    <!-- GROUPS =", 1)
tail = "  </div>\n  </div>\n\n  <div class=\"legend\">" + rest.split("  </div>\n  </div>\n\n  <div class=\"legend\">", 1)[1]
body = ("    <!-- GROUPS -->\n" + "".join(groups) + "\n    <!-- EDGES -->\n"
        f'    <svg class="edges" viewBox="0 0 {W} {H}" aria-hidden="true">\n'
        '      <defs>\n        <marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">\n'
        '          <path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/>\n        </marker>\n      </defs>\n'
        + "\n".join(edges) + "\n    </svg>\n\n    <!-- NODES -->\n" + "".join(nodes) + "\n")
html = head + body + tail
html = html.replace('<html lang="en">', '<html lang="ja">', 1)
html = html.replace("width: 1000px; height: 540px; background", f"width: {W}px; height: {H}px; background", 1)
html = html.replace("svg.edges { position:absolute; inset:0; width:1000px; height:540px;", f"svg.edges {{ position:absolute; inset:0; width:{W}px; height:{H}px;", 1)
# グループのラベルにも、ノードの文字と同じ半透明の下地（線が下を通るとき読めるように）
html = html.replace(".g-label img { width: 14px; height: 14px; }",
    ".g-label img { width: 14px; height: 14px; }\n.g-label span { background: var(--color-veil); padding: 0 var(--space-xs); border-radius: 3px; }", 1)
html = html.replace("<title><!-- TITLE --></title>", "<title>homelab 構成図（現行）</title>")
html = html.replace("<!-- KICKER: e.g. stack-diagram / author / 2026-08 -->", "stack-diagram / homelab / 2026-11")
html = html.replace("<h1><!-- TITLE --></h1>", "<h1>homelab 構成図（現行）</h1>")
html = html.replace("<!-- LEDE: 1-2 short sentences, or delete this <p> -->", "Buffalo の下で、Proxmox 上の VM が動く現行の構成。Caddy が <code>*.lab.kanare.dev</code> の入口で、Prometheus が全 VM を監視する。")
html = html.replace('<span class="sw"></span>request path', '<span class="sw"></span>端末からの通信')
html = html.replace('<span class="sw n"></span>internal', '<span class="sw n"></span>VM・外部サービスとの通信')
html = html.replace('<span class="sw n dash"></span>dev / deploy', '<span class="sw n dash"></span>試用中')
html = html.replace("<!-- FOOT-LEFT: author / one-liner -->", "VM 名の横の数字は IP アドレス（192.168.11.0/24）")
html = html.replace("<!-- FOOT-RIGHT: icon sources actually used, from manifest.json, e.g. \"icons: svgl / devicon / Lucide\" -->", "icons: svgl / devicon / gilbarbara / Lucide / 既存の構成図の素材")
pathlib.Path(sys.argv[1]).write_text(html, encoding="utf-8")
print("draft written", sys.argv[1], len(html)//1024, "KB")
