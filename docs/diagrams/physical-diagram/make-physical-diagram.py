#!/usr/bin/env python3
"""物理構成図（どの機器のどのポートを、どの機器のどのポートに繋ぐか）を、単体の HTML で作る。

ER605・SG2210P を導入して VLAN に分けた後（段階 3 の完了時点）の、有線の最終形。機器はアイコンではなく四角、
ポートは四角（色で用途を示す）、ケーブルは線（太さと色で種類を示す）で描く。VM・サービス・IP の一覧は、
論理側の図（../main-diagram/main-diagram.png）に任せ、ここでは配線だけを見る。

この図の本体はこのスクリプト。下の「配置」の座標と文字から HTML（physical-diagram.html）を組み、Markdown から参照する
PNG（physical-diagram.png、ダーク版は physical-diagram-dark.png）も書き出す。何度実行しても結果は同じ。

    python3 docs/diagrams/physical-diagram/make-physical-diagram.py          # physical-diagram.html を書き出す
    python3 docs/diagrams/physical-diagram/make-physical-diagram.py --png    # さらに Chrome で physical-diagram.png / physical-diagram-dark.png を書き出す

必要なもの: --png には Google Chrome（ヘッドレスで撮る。Playwright は要らない）。
フォントは ../fonts/（Geist と JetBrains Mono。OFL。VLAN 化のあとの図と共通）を HTML に埋め込む。
内容は docs/operations/roadmap/10-er605-sg2210p-migration-plan.md の「段階 3 の後」「ケーブルと電源」、
docs/hardware/er605/settings.md・docs/hardware/sg2210p/settings.md のポート表、docs/architecture/08-vlan-design.md に合わせる。
食い違ったら、docs/ の文書のほうが正。

見た目の決まり（座標は 10px グリッド。背景の方眼は 20px。スタイルは ../main-diagram/make-main-diagram.py と同じ）:
  - 機器は角丸の四角（名前は太字、IP は橙の等幅）。ポートは 48×26 の四角で、機器の枠にまたがせる。
  - ポートの色: WAN（灰の塗り）、trunk（墨の塗り）、access VLAN30（緑）、未使用（点線の枠）。
  - ケーブルの線: WAN は 3px の灰、trunk は 5px の墨、access VLAN30 は 3px の緑（to-be の図と同じ色）。
    ケーブルではないもの（無線、ディスプレイ経由）は、点線。
  - ポートの VLAN の書き方は `tagged: VLAN…` / `untagged: VLAN…` に統一する。
"""
import base64
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "physical-diagram.html"
FONTS = HERE.parent / "fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1320, 940

out = []  # 描く順（後ろほど手前）


def ip(v):
    return f'<span class="ip">{v}</span>'


def text(value, x, y, w, h, align="left", cls=""):
    out.append(f'<div class="t {cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;text-align:{align}"><div>{value}</div></div>')


def box(x, y, w, h, cls="dev"):
    out.append(f'<div class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>')


def port(cx, cy, label, kind, w=48):
    """ポート（幅 48、高さ 26）。cx, cy は中心。機器の枠の上にまたがせる。kind: wan / trunk / v30 / free"""
    out.append(f'<div class="p {kind}" style="left:{cx - w // 2}px;top:{cy - 13}px;width:{w}px">{label}</div>')


def cable(points, kind="trunk"):
    """ケーブルの線（直角に曲がる）。kind: wan / trunk / v30 / air"""
    d = "M" + " L".join(f"{x} {y}" for x, y in points)
    out.append(f'<svg class="e" width="{W}" height="{H}" viewBox="0 0 {W} {H}" aria-hidden="true"><path class="c {kind}" d="{d}" fill="none"/></svg>')


def layout():
    text("<b>物理構成図</b>（段階 3 の完了後。有線）", 40, 14, 600, 28, cls="head")

    # 建物の共用ルーター ---------------------------------------------------------------
    box(40, 60, 280, 110)
    text(f"<b>建物の共用ルーター</b><br>{ip('172.22.0.1')}<br>上流（二重 NAT）", 56, 72, 220, 90)
    port(320, 115, "LAN", "wan")
    text("壁の<br>LAN ポート", 244, 120, 70, 40, align="right", cls="sub")

    # ER605 -----------------------------------------------------------------------------
    box(480, 40, 420, 150)
    text(f"<b>TP-Link ER605 V2</b><br>{ip('10.77.10.1')}（VLAN10）<br>各 VLAN の GW（.1）・DHCP・ACL<br>1000BASE-T × 5", 540, 54, 340, 84)
    port(480, 115, "p1 WAN", "wan", w=88)
    # ポートの種類は、運用者が本体で確認した（2026-11-06）: p1 は WAN、p2・p3 は WAN/LAN、p4・p5 は LAN
    for cx, n, kind, sub in ((530, "p2", "trunk", "WAN/LAN<br>→ SG p1"), (610, "p3", "free", "WAN/LAN<br>未使用"), (690, "p4", "free", "LAN<br>未使用"), (770, "p5", "free", "LAN<br>未使用")):
        port(cx, 190, n, kind)
        text(sub, cx - 40, 148, 80, 30, align="center", cls="sub")

    # ケーブル A: 壁 → ER605 p1
    cable([(344, 115), (436, 115)], "wan")
    text("<b>ケーブル A</b><br>長尺", 338, 66, 108, 38, align="center", cls="el")

    # SG2210P ---------------------------------------------------------------------------
    box(480, 330, 760, 150)
    text(f"<b>TP-Link SG2210P</b><br>{ip('10.77.10.2')}（VLAN10）<br>1000BASE-T（PoE+）× 8 ＋ SFP × 2", 500, 350, 400, 66)
    port(530, 330, "p1", "trunk")
    text("ER605 p2 から", 562, 310, 120, 16, cls="sub")
    sg = (
        (530, "p2", "trunk", "Proxmox<br>trunk"),
        (610, "p3", "v30", "Buffalo<br>access"),
        (690, "p4", "v30", "Dell<br>access"),
        (770, "p5", "free", "予備"),
        (850, "p6", "free", "予備"),
        (930, "p7", "free", "AP 用<br>PoE（将来）"),
        (1010, "p8", "free", "AP 用<br>PoE（将来）"),
        (1090, "p9", "free", "SFP<br>未使用"),
        (1170, "p10", "free", "SFP<br>未使用"),
    )
    for cx, n, kind, sub in sg:
        port(cx, 480, n, kind)
        text(sub, cx - 38, 434, 76, 30, align="center", cls="sub")

    # ケーブル: ER605 p2 → SG2210P p1（新しく買う短いケーブル）
    cable([(530, 203), (530, 317)], "trunk")
    text("<b>短い 0.3〜0.5 m</b>（新規）<br>trunk（tagged: VLAN10/20/30/40/50/60/70）", 550, 236, 420, 40, cls="el")

    # 下流の機器 ----------------------------------------------------------------------------
    # Proxmox（ThinkCentre）
    box(100, 640, 320, 130)
    text(f"<b>Lenovo ThinkCentre M70q Tiny Gen1</b><br>Proxmox（pve）{ip('10.77.10.10')}<br>NIC は 1 つ（1000BASE-T）", 116, 664, 290, 90)
    port(260, 640, "nic0", "trunk")
    cable([(530, 493), (530, 560), (260, 560), (260, 627)], "trunk")
    text("<b>短い 0.5〜1 m</b>（新規）<br>trunk（tagged: VLAN10/20/40/50/70）", 70, 508, 440, 40, align="right", cls="el")

    # Buffalo
    box(470, 640, 280, 130)
    text(f"<b>Buffalo WSR-1800AX4P</b><br>AP モード　{ip('10.77.30.50')}<br>Wi-Fi の入口だけ（段階 4 まで）", 486, 664, 250, 90)
    port(610, 640, "INTERNET※", "v30", w=104)
    cable([(610, 493), (610, 627)], "v30")
    text("<b>ケーブル B</b>　長尺<br>access（untagged: VLAN30）", 624, 566, 230, 40, cls="el")

    # Dell U2725QE
    box(840, 640, 320, 100)
    text("<b>Dell U2725QE</b><br>メインディスプレイ", 856, 664, 290, 56)
    port(1000, 640, "LAN", "v30")
    cable([(690, 493), (690, 560), (1000, 560), (1000, 627)], "v30")
    text("<b>ケーブル C</b>　長尺<br>access（untagged: VLAN30）", 700, 506, 400, 40, cls="el")

    # ケーブルではないもの（点線）
    box(840, 810, 320, 80, "dev ghost")
    text("<b>MacBook Pro M5</b><br>仕事用 Windows PC", 856, 826, 290, 50)
    cable([(1000, 740), (1000, 810)], "air")
    text("ディスプレイ経由<br>（有線 LAN）", 1014, 756, 140, 40, cls="el")

    box(470, 810, 280, 80, "dev ghost")
    text("<b>Wi-Fi 端末</b><br>スマホ・テレビ・SwitchBot ほか", 486, 826, 250, 50)
    cable([(610, 770), (610, 810)], "air")
    text("Wi-Fi（無線）", 624, 780, 140, 20, cls="el")

    # 凡例 ---------------------------------------------------------------------------------
    box(960, 30, 320, 262, "legend")
    text("<b>凡例</b>", 976, 38, 280, 26)
    for k, (kind, label) in enumerate((("wan", "WAN（上流）"), ("trunk", "trunk（tagged）"), ("v30", "access（untagged: VLAN30）"), ("air", "点線: 無線・ディスプレイ経由"))):
        y = 78 + 26 * k
        cable([(980, y), (1030, y)], kind)
        text(label, 1042, y - 12, 230, 24)
    text("A・B・C は今ある長いケーブル（使い回す）。「新規」は買い足す短いケーブル。", 976, 176, 290, 40, cls="sub")
    for k, (kind, label, n) in enumerate((("wan", "WAN", "p1"), ("trunk", "trunk", "p2"), ("v30", "access", "p3"), ("free", "未使用", "p5"))):
        x = 1000 + 72 * k
        port(x, 246, n, kind)
        text(label, x - 34, 262, 68, 22, align="center", cls="sub")

    text("※ 取扱説明書にポートの指定はなく、公式 FAQ では AP モードで INTERNET も LAN として動く。",
         40, 900, 1240, 24, cls="note")


def css():
    fonts = "".join(
        f'@font-face{{font-family:"{fam}";font-style:normal;font-weight:{wt};font-display:swap;'
        f'src:url(data:font/woff2;base64,{base64.b64encode((FONTS / fn).read_bytes()).decode()}) format("woff2")}}\n'
        for fam, fn, wt in (("Geist", "Geist.woff2", "100 900"), ("JetBrains Mono", "JetBrainsMono.woff2", "100 800")))
    light = """
  --paper:oklch(98.5% 0.004 250);--paper2:oklch(96.5% 0.005 252);--card:oklch(100% 0 0 / .9);
  --rule:oklch(93% 0.007 255);--rule2:oklch(83% 0.011 255);--muted:oklch(56% 0.013 255);
  --neutral:oklch(46% 0.015 255);--ink:oklch(24% 0.020 258);--ink2:oklch(34% 0.018 257);
  --orange:oklch(60% 0.17 52);--l30:#82b366;"""
    dark = """
  --paper:oklch(18% 0.012 255);--paper2:oklch(22% 0.014 255);--card:oklch(22% 0.014 255 / .9);
  --rule:oklch(24% 0.013 255);--rule2:oklch(38% 0.018 255);--muted:oklch(65% 0.014 255);
  --neutral:oklch(72% 0.012 255);--ink:oklch(94% 0.008 255);--ink2:oklch(85% 0.010 255);
  --orange:oklch(76% 0.14 60);--l30:#82b366;"""
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
.dev,.legend,.t,.p,.e{{position:absolute}}
.e{{left:0;top:0;pointer-events:none}}
.dev{{border:2px solid var(--ink2);border-radius:10px;background:var(--card)}}
.dev.ghost{{border-style:dashed;border-color:var(--muted);background:color-mix(in srgb,var(--paper) 60%,transparent)}}
.legend{{border:1px solid var(--rule2);border-radius:10px;background:var(--card)}}
.t{{display:flex;align-items:center;font-size:14px;line-height:1.4}}
.t>div{{width:100%}}
.head{{font-size:16px}}
b{{font-weight:600}}
.ip{{font-family:var(--mono);font-size:13px;color:var(--orange)}}
.sub{{font-family:var(--mono);font-size:11px;line-height:1.3;color:var(--muted)}}
.el{{font-family:var(--mono);font-size:12px;letter-spacing:.03em;color:var(--ink2);
  text-shadow:0 0 2px var(--paper),0 0 2px var(--paper),0 0 4px var(--paper),0 0 6px var(--paper)}}
.el b{{font-weight:700}}
.note{{font-size:12px;color:var(--muted)}}
/* ポート */
.p{{width:48px;height:26px;display:flex;align-items:center;justify-content:center;border:2px solid var(--neutral);border-radius:6px;
  background:var(--paper);font-family:var(--mono);font-size:12px;font-weight:600;color:var(--ink)}}
.p.wan{{background:var(--neutral);border-color:var(--neutral);color:var(--paper)}}
.p.trunk{{background:var(--ink);border-color:var(--ink);color:var(--paper)}}
.p.v30{{background:color-mix(in srgb,var(--l30) 40%,var(--paper));border-color:var(--l30)}}
.p.free{{border-style:dashed;border-color:var(--rule2);color:var(--muted);font-weight:400}}
/* ケーブル */
.c{{stroke-linejoin:miter;stroke-linecap:butt}}
.c.wan{{stroke:var(--neutral);stroke-width:3}}
.c.trunk{{stroke:var(--ink);stroke-width:5}}
.c.v30{{stroke:var(--l30);stroke-width:3}}
.c.air{{stroke:var(--neutral);stroke-width:2;stroke-dasharray:6 6}}
"""


def build():
    layout()
    html = ('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>物理構成図（段階 3 の完了後）</title>\n<style>' + css() + '</style>\n'
            '<script>if(location.hash==="#dark")document.documentElement.dataset.theme="dark";'
            'if(location.hash==="#light")document.documentElement.dataset.theme="light"</script>\n</head>\n<body>\n'
            '<div class="canvas">\n' + "\n".join(out) + "\n</div>\n</body>\n</html>\n")
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT} ({OUT.stat().st_size // 1024} KB)")


def render():
    for suffix, frag in (("", "#light"), ("-dark", "#dark")):
        png = HERE / f"physical-diagram{suffix}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--screenshot={png}", OUT.as_uri() + frag],
                       check=True, capture_output=True)
        print(png)


if __name__ == "__main__":
    build()
    if "--png" in sys.argv:
        render()
