#!/usr/bin/env python3
"""homelab のロゴ（SVG）を作る。文字は、フォントの輪郭（パス）に変換して入れる（`<img>` の SVG は、フォントを読み込めないため）。

使い方（fontTools と、JetBrains Mono のフォントが要る。詳しくは README.md）:
    ~/.cache/homelab-logo-venv/bin/python docs/assets/logo/make-logo.py

出力（このスクリプトと同じフォルダ）:
    logo-stack-{light,dark}.svg    横長。積み重ね（3 枚の機器 + 屋根）+ kanare’s homelab + 10.77.0.0/16 · lab.kanare.dev。主役
    seal-{light,dark}.svg          円形のエンブレム。縁に名前・アドレス・ドメイン、中央に積み重ね
    logo-graph-{light,dark}.svg    横長。家のネットワーク図 + 文字。サブ
    icon-stack.svg, icon-graph.svg 正方形のアイコン（暗い地 + 縁取り）。favicon、Homepage のタイル用
    gallery.html                   上の一覧（ライトとダークの背景に並べる）。ブラウザで開いて見る
    social-preview.html            GitHub のソーシャルプレビュー（1280 x 640）の元。PNG は README.md の手順で撮る
light は、明るい背景用（濃い文字）。dark は、暗い背景用（明るい文字）。背景は透明。
マークは静止。点滅するのは、横長のロゴの文字の横のカーソルだけ（CSS。`prefers-reduced-motion` のときは止まる）。

色は THEMES の 1 か所で決める（アクセント色は "accent"、屋根は "froof"・"fgable"）。面の濃淡は、透明度でなく、不透明の色（暗い背景で透けないため）。
フォント: JetBrains Mono（SIL Open Font License 1.1）。文字の輪郭を図形にして、ロゴに入れている。
"""
import math
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
# JetBrains Mono（Medium と Bold）を探す。Nerd Font 版（文字の形は同じ）でもよい
FONT_DIRS = [Path.home() / "Library/Fonts", Path("/Library/Fonts"), Path.home() / ".local/share/fonts", Path("/usr/share/fonts/truetype/jetbrains-mono")]
FONT_NAMES = {"medium": ("JetBrainsMono-Medium.ttf", "JetBrainsMonoNerdFont-Medium.ttf"), "bold": ("JetBrainsMono-Bold.ttf", "JetBrainsMonoNerdFont-Bold.ttf")}
_fonts = {}


def font(weight):
    if weight not in _fonts:
        for d in FONT_DIRS:
            for name in FONT_NAMES[weight]:
                if (d / name).exists():
                    f = TTFont(str(d / name))
                    _fonts[weight] = (f, f.getBestCmap(), f.getGlyphSet(), f["hmtx"], f["head"].unitsPerEm)
                    return _fonts[weight]
        raise SystemExit(f"JetBrains Mono の {weight} が見つからない（探した場所: {', '.join(str(d) for d in FONT_DIRS)}）")
    return _fonts[weight]


# 色。light: 明るい背景用、dark: 暗い背景用
THEMES = {
    # ftop / fleft / fright: 積み重ねの機器の、上面・左面・右面（不透明）。froof / fgable: 屋根の斜面・側面
    "light": {"text": "#1c2430", "muted": "#6a7485", "accent": "#3b6fb6",
              "ftop": "#c9ced6", "fleft": "#7d8796", "fright": "#2a3341", "froof": "#3b6fb6", "fgable": "#2b5591", "frback": "#30609f"},
    "dark": {"text": "#e8edf3", "muted": "#98a3b3", "accent": "#7fa8e0",
             "ftop": "#f1f4f8", "fleft": "#b4bdca", "fright": "#748093", "froof": "#7fa8e0", "fgable": "#5a84bf", "frback": "#6b93cc"},
}
TILE_BG = "#0f141a"  # 正方形のアイコンの地の色（暗い。どの背景でも使える）
TILE_RING = "#3a4555"

CSS_COMMON = """
@keyframes blink{50%{opacity:0}}
.cur{animation:blink 1.06s steps(1) infinite}
@media (prefers-reduced-motion:reduce){.cur{animation:none!important}}
"""


def glyph(ch, x, baseline, size, weight):
    """1 文字の輪郭を、パスの d にする。(d, 送り幅) を返す。"""
    f, cmap, gs, hmtx, upem = font(weight)
    name = cmap.get(ord(ch))
    if name is None:
        raise SystemExit(f"フォントに無い文字: {ch!r}")
    scale = size / upem
    pen = SVGPathPen(gs)
    gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))
    return pen.getCommands(), hmtx[name][0] * scale


def text(runs, x, baseline, size):
    """runs: [(文字列, クラス, 太さ)]。(SVG の断片, 終わりの x) を返す。"""
    out = []
    for s, cls, weight in runs:
        for ch in s:
            d, adv = glyph(ch, x, baseline, size, weight)
            x += adv
            if ch != " " and d:
                out.append(f'<path class="{cls}" d="{d}"/>')
    return "".join(out), x


def theme_css(t, uid):
    """色の指定は、この SVG（uid のクラス）だけに効かせる。ページに直接埋め込んでも、他の SVG の色と混ざらない。"""
    return (f".{uid}{{--text:{t['text']};--muted:{t['muted']};--accent:{t['accent']}}}"
            f".{uid} .tx{{fill:var(--text)}}.{uid} .mu{{fill:var(--muted)}}.{uid} .ac{{fill:var(--accent)}}"
            f".{uid} .stx{{stroke:var(--text)}}"
            f".{uid} .f-top{{fill:{t['ftop']}}}.{uid} .f-left{{fill:{t['fleft']}}}.{uid} .f-right{{fill:{t['fright']}}}"
            f".{uid} .f-roof{{fill:{t['froof']}}}.{uid} .f-gable{{fill:{t['fgable']}}}.{uid} .f-back{{fill:{t['frback']}}}")


def svg(w, h, body, css, title, uid):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="{uid}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">'
            f"<title>{title}</title><style>{css}{CSS_COMMON}</style>{body}</svg>\n")


# ---- マーク（128 x 128 の枠。静止）----
def mark_graph():
    """家のネットワーク図。五角形（家）の頂点がノード。中央のハブから、各ノードに線が伸びる。"""
    pts = [(64, 12), (112, 52), (112, 114), (16, 114), (16, 52)]
    hub = (64, 82)
    poly = " ".join(f"{x},{y}" for x, y in pts)
    spokes = "".join(f'<line x1="{hub[0]}" y1="{hub[1]}" x2="{x}" y2="{y}"/>' for x, y in pts)
    nodes = "".join(f'<circle class="tx" cx="{x}" cy="{y}" r="7.5"/>' for x, y in pts)
    return (f'<g fill="none" stroke-linejoin="round" stroke-linecap="round">'
            f'<polygon class="stx" stroke-width="5" points="{poly}"/>'
            f'<g class="stx" stroke-width="2.6" opacity="0.55">{spokes}</g></g>'
            f'{nodes}<circle class="ac" cx="{hub[0]}" cy="{hub[1]}" r="11"/>')


def _iso(a, b, h, p0):
    """アイソメトリックの直方体。p0 は、手前の下の頂点。(上面, 左面, 右面) の点列を返す。"""
    e1, e2 = (0.866, -0.5), (-0.866, -0.5)
    A = p0
    B = (A[0] + e1[0] * a, A[1] + e1[1] * a)
    D = (A[0] + e2[0] * b, A[1] + e2[1] * b)
    C = (B[0] + e2[0] * b, B[1] + e2[1] * b)
    U = lambda q: (q[0], q[1] - h)
    poly = lambda *qs: " ".join(f"{x:.1f},{y:.1f}" for x, y in qs)
    return poly(U(A), U(B), U(C), U(D)), poly(A, D, U(D), U(A)), poly(A, B, U(B), U(A)), (A, B, D, C)


def mark_stack():
    """積み重ね: 3 枚の機器（ルーター、スイッチ、ミニ PC）を斜めから見て積み、上に屋根を載せる。前面に LED。"""
    a = b = 46
    h, gap = 12, 5
    out = []
    base_y = 118
    for k in range(3):
        top, left, right, (A, B, D, C) = _iso(a, b, h, (64, base_y - k * (h + gap)))
        out.append(f'<polygon class="f-left" points="{left}"/><polygon class="f-right" points="{right}"/><polygon class="f-top" points="{top}"/>')
        for f in (0.74, 0.86):  # 右面の LED
            x = A[0] + 0.866 * a * f
            y = A[1] - 0.5 * a * f - h / 2
            out.append(f'<circle class="ac" cx="{x:.1f}" cy="{y:.1f}" r="1.9"/>')
    # 屋根（切妻）。いちばん上の面に載せる
    A = (64, base_y - 2 * (h + gap) - h)
    B = (A[0] + 0.866 * a, A[1] - 0.5 * a)
    D = (A[0] - 0.866 * b, A[1] - 0.5 * b)
    C = (B[0] - 0.866 * b, B[1] - 0.5 * b)
    r = 18
    mid = lambda p, q: ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 - r)
    M1, M2 = mid(A, D), mid(B, C)
    poly = lambda *qs: " ".join(f"{x:.1f},{y:.1f}" for x, y in qs)
    # 後ろの斜面は、棟（M1–M2）より、画面の上に、細い帯として見える。先に描く（手前の斜面と側面が、その上に重なる）
    out.append(f'<polygon class="f-back" points="{poly(D, C, M2, M1)}"/>')
    out.append(f'<polygon class="f-gable" points="{poly(A, D, M1)}"/><polygon class="f-roof" points="{poly(A, B, M2, M1)}"/>')
    return f'<g transform="translate(0 -4)">{"".join(out)}</g>'


MARKS = {"stack": mark_stack, "graph": mark_graph}


def logo(kind, theme):
    """横長。マーク（静止）+ kanare’s / homelab（カーソルだけが点滅）+ 10.77.0.0/16 · lab.kanare.dev。README の見出し用。"""
    t = THEMES[theme]
    uid = f"hl-logo-{kind}-{theme}"
    mark = f'<g transform="translate(8 8) scale(0.8)">{MARKS[kind]()}</g>'
    x0 = 8 + 102 + 22
    l1, _ = text([("kanare’s", "ac", "medium")], x0, 38, 28)
    l2, x_end = text([("homelab", "tx", "bold")], x0, 84, 52)
    sub, x_sub = text([("10.77.0.0/16 · lab.kanare.dev", "mu", "medium")], x0 + 1, 110, 16)
    adv = glyph("a", 0, 0, 52, "medium")[1]
    cur = f'<rect class="cur ac" x="{x_end + 4:.1f}" y="{84 - 52 * 0.78:.1f}" width="{adv * 0.8:.1f}" height="{52 * 0.78:.1f}"/>'
    w = int(max(x_end + 4 + adv * 0.8, x_sub) + 10)
    return svg(w, 124, mark + l1 + l2 + cur + sub, theme_css(t, uid), "kanare’s homelab", uid)


def icon(kind):
    """正方形のアイコン（暗い地 + 縁取り）。favicon、Homepage のタイル用。"""
    uid = f"hl-icon-{kind}"
    body = (f'<rect x="1" y="1" width="126" height="126" rx="27" fill="{TILE_BG}" stroke="{TILE_RING}" stroke-width="2"/>'
            f'<g transform="translate(18 18) scale(0.72)">{MARKS[kind]()}</g>')
    return svg(128, 128, body, theme_css(THEMES["dark"], uid), "kanare’s homelab", uid)


def arc_text(cx, cy, mid_r, s, size, side, center_deg, weight="medium", cls="tx"):
    """円の帯の中心線（半径 mid_r）に、文字の高さの真ん中を合わせて、文字を置く。
    side="top": 上の弧（文字は外向きに立つ）、"bottom": 下の弧（読める向き）。center_deg: 弧の真ん中の角度（SVG の座標。上 = -90、下 = 90）。
    文字の間隔は、中心線の上で、一定にする。(SVG の断片, 弧の角度（度）) を返す。"""
    f, cmap, gs, hmtx, upem = font(weight)
    adv = hmtx[cmap[ord("a")]][0] * size / upem
    half = 0.34 * size  # 文字の見かけの高さの真ん中（ベースラインから）。小文字と大文字の中間
    base_r = mid_r - half if side == "top" else mid_r + half
    total = len(s) * adv / mid_r
    out = []
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        off = (i + 0.5) * adv / mid_r - total / 2
        if side == "top":
            phi = math.radians(center_deg) + off
            alpha = math.degrees(phi) + 90
        else:
            phi = math.radians(center_deg) - off
            alpha = math.degrees(phi) - 90
        x, y = cx + base_r * math.cos(phi), cy + base_r * math.sin(phi)
        d, _ = glyph(ch, -adv / 2, 0, size, weight)
        out.append(f'<path class="{cls}" transform="translate({x:.2f} {y:.2f}) rotate({alpha:.2f})" d="{d}"/>')
    return "".join(out), math.degrees(total)


def seal(theme, kind="stack"):
    """円形のエンブレム。縁に、名前とアドレス・ドメイン。中央に、マーク。
    文字は、大円と小円の中心線の間（帯の真ん中）に揃える。"""
    t = THEMES[theme]
    uid = f"hl-seal-{kind}-{theme}"
    c = 80
    r_out, r_in = 76, 49
    mid = (r_out + r_in) / 2  # 帯の中心線（2 つの円の中心線の、ちょうど真ん中）
    top_s, bot_s = 15, 11
    top, top_span = arc_text(c, c, mid, "kanare’s homelab", top_s, "top", -90, "bold")
    bot_text = "10.77.0.0/16 · lab.kanare.dev"
    adv_b = glyph("a", 0, 0, bot_s, "medium")[1]
    bot_span = math.degrees(len(bot_text) * adv_b / mid)
    bot, _ = arc_text(c, c, mid, bot_text, bot_s, "bottom", 90, "medium", "mu")
    # 上の文字と下の文字のすき間の真ん中に、点を置く
    top_end = -90 + top_span / 2          # 右側の、上の文字の終わり
    bot_end = 90 - bot_span / 2           # 右側の、下の文字の終わり
    dots = ""
    for ang in ((top_end + bot_end) / 2, 180 - (top_end + bot_end) / 2):
        x, y = c + mid * math.cos(math.radians(ang)), c + mid * math.sin(math.radians(ang))
        dots += f'<circle class="ac" cx="{x:.2f}" cy="{y:.2f}" r="2.6"/>'
    scale = 0.58
    body = (f'<g fill="none" class="stx"><circle cx="{c}" cy="{c}" r="{r_out}" stroke-width="3"/><circle cx="{c}" cy="{c}" r="{r_in}" stroke-width="2"/></g>'
            + top + bot + dots
            + f'<g transform="translate({c - 64 * scale:.2f} {c - 64 * scale:.2f}) scale({scale})">{MARKS[kind]()}</g>')
    return svg(160, 160, body, theme_css(t, uid), "kanare’s homelab", uid)


def gallery():
    """ロゴの一覧（gallery.html）。ライトとダークの背景に並べる。<img> で読み込むので、カーソルの点滅も見える。"""
    def panel(cls, th):
        return (f'<div class="p {cls}">'
                f'<h3>横長（主役）　<code>logo-stack-{th}.svg</code></h3><div class="row"><img src="logo-stack-{th}.svg"></div>'
                f'<h3>円形のエンブレム　<code>seal-{th}.svg</code></h3><div class="row"><img src="seal-{th}.svg" width="240"></div>'
                f'<h3>横長（サブ）　<code>logo-graph-{th}.svg</code></h3><div class="row"><img src="logo-graph-{th}.svg"></div></div>')
    tiles = "".join(
        '<div class="icons">' + "".join(f'<img src="icon-{k}.svg" width="{w}">' for w in (96, 48, 32, 16)) + "</div>"
        for k in ("stack", "graph"))
    return f"""<!doctype html>
<meta charset="utf-8">
<title>kanare’s homelab — ロゴ一覧</title>
<style>
body{{margin:0;font:14px system-ui}}.g{{display:grid;grid-template-columns:1fr 1fr}}
.p{{padding:22px 34px 8px}}.l{{background:#fff;color:#222}}.d{{background:#0d1117;color:#ddd}}
h3{{margin:0 0 8px;font-size:12px;font-weight:600;opacity:.55}}h3 code{{font-weight:400}}
.row{{margin:0 0 22px}}.row img{{display:block}}.icons{{display:flex;gap:16px;align-items:flex-end;margin:0 0 14px}}.icons img{{display:block}}
</style>
<body><div class="g">{panel("l", "light")}{panel("d", "dark")}
<div class="p l"><h3>正方形のアイコン　<code>icon-stack.svg</code>、<code>icon-graph.svg</code>（96 / 48 / 32 / 16）</h3>{tiles}</div>
<div class="p d"><h3>正方形のアイコン</h3>{tiles}</div></div></body>
"""


def social_preview():
    """GitHub のソーシャルプレビュー用（1280 x 640）の HTML。ダークの地に、ダーク版のロゴを中央に置く。
    PNG にするには、ブラウザで開いて撮る（README.md の「ソーシャルプレビュー」）。"""
    return f"""<!doctype html>
<meta charset="utf-8">
<title>social preview</title>
<style>
html,body{{margin:0;width:1280px;height:640px;background:{TILE_BG}}}
body{{display:flex;align-items:center;justify-content:center}}
img{{width:820px;height:auto}}
</style>
<body><img alt="kanare’s homelab" src="logo-stack-dark.svg"></body>
"""


def main():
    for theme in ("light", "dark"):
        (HERE / f"logo-stack-{theme}.svg").write_text(logo("stack", theme), encoding="utf-8")
        (HERE / f"logo-graph-{theme}.svg").write_text(logo("graph", theme), encoding="utf-8")
        (HERE / f"seal-{theme}.svg").write_text(seal(theme), encoding="utf-8")
    for kind in ("stack", "graph"):
        (HERE / f"icon-{kind}.svg").write_text(icon(kind), encoding="utf-8")
    (HERE / "gallery.html").write_text(gallery(), encoding="utf-8")
    (HERE / "social-preview.html").write_text(social_preview(), encoding="utf-8")
    for p in sorted(HERE.glob("*.svg")):
        print(p.name, p.stat().st_size, "bytes")


if __name__ == "__main__":
    sys.exit(main())
