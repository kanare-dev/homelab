#!/usr/bin/env python3
"""VLAN 間の通信マトリクス（ゲートウェイの ACL の目標）を、単体の HTML と PNG（ライト・ダーク）で作る。

内容の正は、第5章 ネットワークの「通信ポリシー」の許可表（docs/architecture/hld/05-network.md）と、
ADR-0034（ACL は VLAN の境界、ポートは UFW）。許可表を変えたら、同じ変更で下の MATRIX を直して書き出す。

  python3 docs/diagrams/acl-matrix/make-acl-matrix.py --png   # HTML と PNG（Google Chrome が要る）

- 縦が送信元、横が宛先。新規の接続の可否だけを示す（戻りの通信は常に許可）。
- 記号: allow（許可）、limit（必要な通信だけ。セルに短い説明）、deny（拒否）、same（同じ VLAN。ACL を通らない）。
- 図の文字は英語。見た目（フォント、ライト・ダーク、OKLCH の色）は構成図に揃える。
"""
import base64
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE.parent / "fonts"
OUT = HERE / "acl-matrix.html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 980, 900

COLS = ["Mgmt", "Servers", "Trusted", "Lab", "IoT", "Guests", "DMZ", "Internet"]
ROWS = ["Mgmt", "Servers", "Trusted", "Lab", "IoT", "Guests", "DMZ"]
VLAN = {"Mgmt": 10, "Servers": 20, "Trusted": 30, "Lab": 40, "IoT": 50, "Guests": 60, "DMZ": 70}
HUE = {10: 300, 20: 250, 30: 195, 40: 145, 50: 95, 60: 55, 70: 25}  # 構成図の VLAN の色相（ADR は無し。PR #47）

A, L, D, S = "allow", "limit", "deny", "same"
# 送信元 → 宛先。limit の 2 つ目は、セルに出す短い説明（第5章の「個別の許可」の要約）
MATRIX = {
    "Mgmt":    [S, D, D, D, D, D, (L, "admin"), (A, "")],
    "Servers": [(L, "proxy,<br>metrics"), S, D, (L, "ssh, web,<br>metrics"), D, D, (L, "logs"), (A, "")],
    "Trusted": [(L, "admin,<br>ping"), (A, "UFW"), S, (A, "UFW"), A, D, (L, "web, ssh"), (A, "")],
    "Lab":     [D, (L, "DNS"), D, S, D, D, D, (A, "")],
    "IoT":     [D, (L, "DNS"), D, D, S, D, D, (A, "")],
    "Guests":  [D, (L, "DNS"), D, D, D, S, D, (A, "")],
    "DMZ":     [D, D, D, D, D, D, S, (L, "web only")],
}

ICON = {
    A: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="7.5" fill="none" stroke="currentColor" stroke-width="2.6"/></svg>',
    L: '<svg viewBox="0 0 24 24"><path d="M12 4.5 20 18.5H4Z" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linejoin="round"/></svg>',
    D: '<svg viewBox="0 0 24 24"><path d="M7 7l10 10M17 7 7 17" stroke="currentColor" stroke-width="2.8" stroke-linecap="round"/></svg>',
    S: '<svg viewBox="0 0 24 24"><path d="M6 12h12" stroke="currentColor" stroke-width="2.8" stroke-linecap="round"/></svg>',
}


def cell(v):
    kind, note = (v, "") if isinstance(v, str) else v
    return f'<div class="c {kind}">{ICON[kind]}<span>{note}</span></div>'


def css():
    fonts = "".join(
        f'@font-face{{font-family:"{fam}";font-style:normal;font-weight:{wt};font-display:swap;'
        f'src:url(data:font/woff2;base64,{base64.b64encode((FONTS / fn).read_bytes()).decode()}) format("woff2")}}\n'
        for fam, fn, wt in (("Geist", "Geist.woff2", "100 900"), ("JetBrains Mono", "JetBrainsMono.woff2", "100 800")))
    vl = "".join(f"--h{v}:{h};" for v, h in HUE.items())
    light = """
  --paper:oklch(98.5% 0.004 250);--card:oklch(100% 0 0);--rule:oklch(90% 0.008 255);
  --ink:oklch(24% 0.020 258);--ink2:oklch(40% 0.016 257);--muted:oklch(56% 0.013 255);
  --allow:oklch(55% 0.15 150);--limit:oklch(64% 0.15 70);--deny:oklch(57% 0.19 25);--same:oklch(62% 0.01 255);
  --tint:13%;--dot:62%"""
    dark = """
  --paper:oklch(18% 0.012 255);--card:oklch(22% 0.014 255);--rule:oklch(32% 0.016 255);
  --ink:oklch(94% 0.008 255);--ink2:oklch(80% 0.010 255);--muted:oklch(65% 0.014 255);
  --allow:oklch(72% 0.16 150);--limit:oklch(78% 0.15 75);--deny:oklch(68% 0.19 25);--same:oklch(62% 0.01 255);
  --tint:20%;--dot:70%"""
    return fonts + f"""
:root{{color-scheme:light;{light};{vl}
  --display:"Geist","Hiragino Sans","Noto Sans JP",ui-sans-serif,system-ui,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,Menlo,monospace}}
:root[data-theme=dark]{{color-scheme:dark;{dark}}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{color-scheme:dark;{dark}}}}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--paper);color:var(--ink);font-family:var(--display)}}
.canvas{{width:{W}px;height:{H}px;padding:28px;background:var(--paper)}}
.card{{height:100%;border:1px solid var(--rule);border-radius:16px;background:var(--card);padding:28px 32px}}
h1{{font-size:21px;font-weight:600;letter-spacing:-.01em}}
.sub{{margin-top:6px;font-size:13px;color:var(--muted)}}
.grid{{margin-top:22px;display:grid;grid-template-columns:118px repeat({len(COLS)},84px);gap:6px;align-items:center}}
.col{{height:92px;position:relative}}
.col b{{position:absolute;left:30px;bottom:6px;transform:rotate(-45deg);transform-origin:left bottom;white-space:nowrap;
  font-size:15px;font-weight:600}}
.row{{text-align:right;padding-right:14px;font-size:15px;font-weight:600;line-height:1.15}}
.vl{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:8px;vertical-align:1px;
  background:oklch(var(--dot) 0.13 var(--h))}}
.id{{display:block;font-family:var(--mono);font-size:11px;font-weight:400;color:var(--muted)}}
.c{{height:66px;border-radius:9px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px}}
.c svg{{width:24px;height:24px}}
.c span{{font-family:var(--mono);font-size:10.5px;line-height:1.2;text-align:center;color:var(--ink2);min-height:0}}
.c span:empty{{display:none}}
.allow{{color:var(--allow);background:color-mix(in srgb,var(--allow) var(--tint),transparent)}}
.limit{{color:var(--limit);background:color-mix(in srgb,var(--limit) var(--tint),transparent)}}
.deny{{color:var(--deny);background:color-mix(in srgb,var(--deny) var(--tint),transparent)}}
.same{{color:var(--same);background:color-mix(in srgb,var(--same) var(--tint),transparent)}}
.inet{{border-left:1px dashed var(--rule);padding-left:6px}}
.legend{{margin-top:26px;display:flex;gap:22px;font-size:13px;color:var(--ink2);align-items:center}}
.legend i{{display:inline-flex;width:18px;height:18px;vertical-align:-4px;margin-right:6px}}
.legend i svg{{width:18px;height:18px}}
.notes{{margin-top:16px;font-size:12.5px;line-height:1.6;color:var(--muted)}}
.notes code{{font-family:var(--mono);font-size:11.5px}}
"""


def build():
    head = '<div></div>' + "".join(f'<div class="col"><b>{c}</b></div>' for c in COLS)
    rows = ""
    for r in ROWS:
        v = VLAN[r]
        rows += (f'<div class="row" style="--h:var(--h{v})"><span class="vl"></span>{r}<span class="id">VLAN{v}</span></div>'
                 + "".join(cell(x) for x in MATRIX[r]))
    legend = "".join(f'<span><i style="color:var(--{k})">{ICON[k]}</i>{t}</span>' for k, t in (
        (A, "Allow"), (L, "Only what is needed"), (D, "Deny"), (S, "Same VLAN (not via the ACL)")))
    notes = ("Rows are the source, columns the destination. Only new connections are shown; return traffic is always allowed.<br>"
             "This is the target policy for the gateway ACL. Ports on each host are restricted by its own UFW, "
             "so Trusted &rarr; Servers / Lab is allowed per VLAN.<br>"
             "Traffic inside a VLAN and traffic through the Tailscale subnet router does not pass the ACL.")
    body = (f'<div class="canvas"><div class="card"><h1>Inter-VLAN traffic matrix</h1>'
            f'<p class="sub">Gateway ACL (rtr01) &middot; source &darr; / destination &rarr;</p>'
            f'<div class="grid">{head}{rows}</div><div class="legend">{legend}</div><p class="notes">{notes}</p></div></div>')
    html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>Inter-VLAN traffic matrix</title>\n<style>' + css() + '</style>\n'
            '<script>if(location.hash==="#dark")document.documentElement.dataset.theme="dark";'
            'if(location.hash==="#light")document.documentElement.dataset.theme="light"</script>\n</head>\n<body>\n'
            + body + "\n</body>\n</html>\n")
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT} ({OUT.stat().st_size // 1024} KB)")


def render():
    for suffix, frag in (("", "#light"), ("-dark", "#dark")):
        png = HERE / f"acl-matrix{suffix}.png"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
                        f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--screenshot={png}", OUT.as_uri() + frag],
                       check=True, capture_output=True)
        print(png)


if __name__ == "__main__":
    build()
    if "--png" in sys.argv:
        render()
