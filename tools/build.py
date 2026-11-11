# -*- coding: utf-8 -*-
"""サイト生成: python3 build.py <src_dir> <out_dir>"""
import os, sys, re, html, json, subprocess
import parse
from content import WORKS, COMMON, SPEC_URL, ZU_URL, SPEC_PAGE, ZU_PAGE

SRC, OUT = sys.argv[1], sys.argv[2]
SPEC_PDF = os.path.join(SRC, "spec.pdf")
ZU_PDF = os.path.join(SRC, "zu.pdf")
E = html.escape

lines = parse.load(os.path.join(SRC, "spec.txt"))
heads = parse.index(lines)
zu_t = parse.zu_titles(os.path.join(SRC, "zu.txt"))

HEN_NAME = {2: "第2編 共通工事", 3: "第3編 空気調和設備工事", 5: "第5編 給排水衛生設備工事"}
ALL = WORKS + [COMMON]
IDX = []          # 横断検索用
_seen_c, _seen_z = {}, {}
CHIPS = {
    "reibai": ["気密", "真空", "ろう付け", "吊り 間隔", "立て管", "保温 厚さ", "曲げ"],
    "drain": ["勾配", "トラップ", "間接排水", "通水", "保温", "材料"],
    "duct": ["板厚", "吊り", "フランジ", "補強", "シール", "防火", "保温 厚さ"],
    "eisei": ["勾配", "水圧", "満水", "通気", "埋設", "吊り 間隔", "保温 厚さ"],
    "kyotsu": ["保温", "スリーブ", "貫通", "試験", "洗浄"],
}
HOME_CHIPS = ["勾配", "吊り 間隔", "振れ止め", "試験", "保温 厚さ", "板厚", "真空", "トラップ", "防火区画", "埋設"]


def plain(raw_lines):
    return re.sub(r"\s+", " ", " ".join(l.strip() for l in raw_lines if l.strip()))


def chips_html(words):
    return '<div class="chips">' + "".join(
        f'<button type="button" class="chip" data-q="{E(x)}">{E(x.replace(" ", ""))}</button>' for x in words) + "</div>"
NAV = [(w["id"], w["short"]) for w in ALL]

spec_pages, zu_pages = set(), set()

ZU_FIX = {  # 図示記号ページの名称補足
    3: "図示記号（配管）その1", 4: "図示記号（配管）その2", 5: "図示記号（配管）その3",
    6: "図示記号（配管：空調・冷媒・ドレン等）", 7: "図示記号（配管：衛生・排水等）",
    12: "図示記号（機器及び材料：ダクト・吹出口等）", 13: "図示記号（機器及び材料：ダクト附属品等）",
    17: "図示記号（機器及び材料：衛生）その1", 18: "図示記号（機器及び材料：衛生）その2",
    19: "図示記号（機器及び材料：衛生）その3", 2: "一般仕様（図示記号・機材標準図・施工標準図の扱い）",
    26: "パッケージ形空気調和機屋内機・FCU等の形式記号",
    95: "施工標準図 一覧表（一）", 96: "施工標準図 一覧表（二）", 97: "施工標準図 一覧表（三）",
}


def spec_link(p, label=None):
    spec_pages.add(p)
    return (f'<a class="pg" href="img/spec/p{p:03d}.jpg" data-full="img/spec/p{p:03d}.jpg" '
            f'data-cap="標準仕様書 原本PDF {p}ページ">{E(label or f"原本 p.{p}")}</a>')


def ref_html(ref):
    return f'<span class="ref">{E(ref)}</span>'


def clause_html(hen, num, wid):
    title, pages, body = parse.extract(lines, heads, hen, num)
    cid = f"c{hen}-{num.replace('.', '_')}"
    pg = " ".join(spec_link(p) for p in pages)
    return (f'<details class="cl" id="{cid}">'
            f'<summary><span class="num">{E(num)}</span><span class="ttl">{E(title)}</span>'
            f'<span class="hen">第{hen}編</span></summary>'
            f'<div class="body"><div class="pgs">原本ページ：{pg} '
            f'<a class="ext" href="{SPEC_URL}#page={pages[0]}" target="_blank" rel="noopener">国交省PDF↗</a></div>'
            f'{parse.render_body(body)}'
            f'<p class="tblnote">※表の罫線はテキスト化で崩れます。数値は必ず原本ページ画像で確認してください。</p>'
            f'</div></details>'), (hen, num, title, cid, plain(body))


def zu_card(p):
    zu_pages.add(p)
    t = ZU_FIX.get(p, zu_t.get(p, ""))
    t = re.sub(r"\s*単位.*$", "", t)
    return (f'<figure class="zu" id="z{p}"><a href="img/zu/p{p:03d}.jpg" data-full="img/zu/p{p:03d}.jpg" '
            f'data-cap="標準図 原本PDF {p}ページ：{E(t)}">'
            f'<img loading="lazy" src="img/zu/t{p:03d}.jpg" alt="{E(t)}"></a>'
            f'<figcaption>{E(t)}<span>原本PDF p.{p}・<a href="{ZU_URL}#page={p}" target="_blank" rel="noopener">国交省PDF↗</a></span></figcaption></figure>')


CSS = open(os.path.join(os.path.dirname(__file__), "style.css"), encoding="utf-8").read()
JS = open(os.path.join(os.path.dirname(__file__), "app.js"), encoding="utf-8").read()


def page(fname, title, active, main, desc, extra_js=""):
    nav = "".join(
        f'<a href="{i}.html" class="{"on" if i == active else ""}">{E(s)}</a>' for i, s in NAV)
    html_doc = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}｜国交省 機械設備 標準仕様書・標準図 工事別まとめ</title>
<meta name="description" content="{E(desc)}">
<link rel="stylesheet" href="style.css">
</head><body data-work="{active}">
<header class="top"><div class="wrap">
<a class="brand" href="index.html"><b>機械設備</b> 標準仕様・標準図</a>
<nav class="tabs">{nav}</nav>
</div></header>
{main}
<footer class="foot"><div class="wrap">
<p><b>出典</b>：「公共建築工事標準仕様書（機械設備工事編）令和7年版（修補版）」（国土交通省大臣官房官庁営繕部）<a href="{SPEC_PAGE}" target="_blank" rel="noopener">{SPEC_PAGE}</a>、
「公共建築設備工事標準図（機械設備工事編）令和7年版」（同）<a href="{ZU_PAGE}" target="_blank" rel="noopener">{ZU_PAGE}</a> を加工して作成。</p>
<p>本サイトは国土交通省が作成・監修したものではありません。条文は原本PDFから機械的に抽出したもの、早見表は要約です。実際の工事では設計図書（特記仕様・図面等）が標準仕様書に優先します（標準仕様書 1.1.1）。必ず原本・設計図書で確認してください。</p>
</div></footer>
<dialog id="lb"><div class="lbbar"><span id="lbcap"></span><button id="lbzoom" type="button">拡大</button><a id="lbopen" target="_blank" rel="noopener">別タブ</a><button id="lbclose" type="button">閉じる</button></div><div class="lbimg"><img id="lbimg" alt=""></div></dialog>
{extra_js}<script src="app.js"></script>
</body></html>"""
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
        f.write(html_doc)


def work_page(w):
    parts, toc = [], []
    quick = w.get("quick")
    if quick:
        rows = ""
        for i, (a, bb, c) in enumerate(quick):
            qid = f"q-{w['id']}-{i}"
            rows += f'<tr class="q" id="{qid}"><th>{E(a)}</th><td>{E(bb)}</td><td>{ref_html(c)}</td></tr>'
            IDX.append({"k": "早見表", "w": [w["id"]], "h": f"{w['id']}.html#{qid}", "t": a, "x": f"{bb}（根拠 {c}）"})
        parts.append(f'<section id="quick"><h2>早見表</h2>'
                     f'<p class="note">主要な数値・ルールの要約です。根拠欄の「2-2.4.6(2)」は「第2編 2.4.6 (2)」を表します。</p>'
                     f'<table class="qt"><thead><tr><th>項目</th><th>規定</th><th>根拠</th></tr></thead><tbody>{rows}</tbody></table></section>')
        toc.append(("quick", "早見表"))
    # 条文
    groups, cur = [], None
    for hen, num in w["clauses"]:
        h, meta = clause_html(hen, num, w["id"])
        if cur is None or cur[0] != hen:
            cur = [hen, []]
            groups.append(cur)
        cur[1].append((h, meta))
    sec = ['<section id="spec"><h2>標準仕様書 条文</h2>'
           '<div class="tools"><button type="button" data-act="open">すべて開く</button>'
           '<button type="button" data-act="close">すべて閉じる</button></div>']
    toc.append(("spec", "標準仕様書 条文"))
    for hen, items in groups:
        sec.append(f'<h3 class="hen">{E(HEN_NAME.get(hen, f"第{hen}編"))}</h3>')
        toc.append(("", HEN_NAME.get(hen, f"第{hen}編"), "hen", 0))
        for h, (hh, num, title, cid, txt) in items:
            sec.append(h)
            if cid in _seen_c:
                IDX[_seen_c[cid]]["w"].append(w["id"])
            else:
                _seen_c[cid] = len(IDX)
                IDX.append({"k": "条文", "w": [w["id"]], "h": f"{w['id']}.html#{cid}",
                            "t": f"第{hh}編 {num} {title}", "x": txt})
            toc.append((cid, f"{num} {title}", True))
    sec.append("</section>")
    parts.append("".join(sec))
    # 標準図
    zu = "".join(zu_card(p) for p in w["zu"])
    for p in w["zu"]:
        t = re.sub(r"\s*単位.*$", "", ZU_FIX.get(p, zu_t.get(p, "")))
        if p in _seen_z:
            IDX[_seen_z[p]]["w"].append(w["id"])
        else:
            _seen_z[p] = len(IDX)
            IDX.append({"k": "標準図", "w": [w["id"]], "h": f"{w['id']}.html#z{p}", "t": t, "x": f"標準図 原本PDF p.{p}"})
    note = f'<p class="note">{E(w["zu_note"])}</p>' if w.get("zu_note") else ""
    parts.append(f'<section id="zu"><h2>標準図</h2>{note}<div class="zugrid">{zu}</div></section>')
    toc.append(("zu", "標準図"))

    toc_html = "".join(
        (f'<span class="tochen">{E(t[1])}</span>' if len(t) == 4 else
         f'<a href="#{t[0]}" class="{"sub" if len(t) > 2 else ""}">{E(t[1])}</a>') for t in toc)
    jump = "".join(f'<a href="#{t[0]}">{E(t[1])}</a>' for t in toc if len(t) == 2)
    main = f"""<main class="wrap layout">
<aside class="toc"><div class="tocin"><p class="toch">目次</p>{toc_html}</div></aside>
<div class="content">
<div class="hero h-{w['id']}"><p class="kicker">{E(w.get('icon',''))} 工事別</p><h1>{E(w['name'])}</h1><p>{E(w['lead'])}</p></div>
<div class="search"><input id="q" type="search" placeholder="このページ内を検索（スペースで複数語）" autocomplete="off"><span id="qn"></span></div>
{chips_html(CHIPS.get(w['id'], []))}
<p class="allsearch"><a href="index.html#find">全ページから探す →</a></p>
<nav class="jump">{jump}</nav>
{''.join(parts)}
</div></main>"""
    page(f"{w['id']}.html", w["name"], w["id"], main, f"{w['name']}：国交省標準仕様書・標準図（機械設備工事編 令和7年版）の該当条文・早見表・標準図")


def index_page():
    cards = "".join(
        f'<a class="card h-{w["id"]}" href="{w["id"]}.html"><span class="ci">{E(w.get("icon",""))}</span>'
        f'<b>{E(w["name"])}</b><span>{E(w["lead"])}</span></a>' for w in ALL)
    main = f"""<main class="wrap home">
<div class="hero home-hero"><p class="kicker">国土交通省 官庁営繕 令和7年版</p>
<h1>機械設備 標準仕様書・標準図<br>工事別まとめ</h1>
<p>「公共建築工事標準仕様書（機械設備工事編）」と「公共建築設備工事標準図（機械設備工事編）」から、冷媒・ドレン・ダクト・衛生配管にかかわる条文と図を工事ごとに整理しました。スマホでも現場で引けるように、早見表・原本ページ画像付きです。</p></div>
<section id="find" class="find"><h2>全ページから探す</h2>
<div class="search home-search"><input id="gq" type="search" placeholder="例：吊り 間隔／真空／ダクト 板厚" autocomplete="off"><span id="gqn"></span></div>
{chips_html(HOME_CHIPS).replace('class="chips"', 'class="chips gchips"')}
<p class="note">早見表・条文・標準図をまとめて検索します。スペースで区切ると全部を含むものに絞り込み。言い換え（ピッチ→間隔、SUS→ステンレス、断熱→保温 など）にも対応。</p>
<div id="gres"></div></section>
<h2 class="cardsh">工事から探す</h2>
<div class="cards">{cards}</div>
<section class="howto"><h2>使い方</h2>
<ul>
<li><b>早見表</b>：よく使う数値（勾配・吊り間隔・板厚・試験圧力など）を根拠条項つきで一覧化。</li>
<li><b>条文</b>：原本PDFからそのまま抽出。タップで開閉、ページ内検索で絞り込み。</li>
<li><b>原本 p.○</b>：原本ページの画像を表示。表の数値は必ずこちらで確認してください。</li>
<li><b>標準図</b>：該当する標準図を画像で表示。タップで拡大。</li>
</ul>
<p class="ver">収録版：標準仕様書 令和7年版（修補版 令和7年11月5日 国営設第110号）／標準図 令和7年版（最終改定 令和7年5月12日 国営設第33号）</p>
</section></main>"""
    page("index.html", "トップ", "", main, extra_js='<script src="search-index.js"></script>', desc="国交省 公共建築工事標準仕様書・標準図（機械設備工事編）令和7年版を冷媒・ドレン・ダクト・衛生配管の工事別に整理")


def render_images():
    for kind, pdf, pages, dpi in (("spec", SPEC_PDF, spec_pages, 130), ("zu", ZU_PDF, zu_pages, 160)):
        d = os.path.join(OUT, "img", kind)
        os.makedirs(d, exist_ok=True)
        for p in sorted(pages):
            dst = os.path.join(d, f"p{p:03d}.jpg")
            if not os.path.exists(dst):
                subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-r", str(dpi), "-gray",
                                "-jpeg", "-jpegopt", "quality=72,optimize=y", "-singlefile",
                                pdf, dst[:-4]], check=True)
            if kind == "zu":
                th = os.path.join(d, f"t{p:03d}.jpg")
                if not os.path.exists(th):
                    subprocess.run(["pdftoppm", "-f", str(p), "-l", str(p), "-scale-to", "480", "-gray",
                                    "-jpeg", "-jpegopt", "quality=70,optimize=y", "-singlefile",
                                    pdf, th[:-4]], check=True)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for w in WORKS:
        work_page(w)
    work_page(COMMON)
    index_page()
    names = {w["id"]: w["short"] for w in ALL}
    with open(os.path.join(OUT, "search-index.js"), "w", encoding="utf-8") as f:
        f.write("window.SIDX=" + json.dumps({"names": names, "items": IDX}, ensure_ascii=False, separators=(",", ":")) + ";")
    with open(os.path.join(OUT, "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    with open(os.path.join(OUT, "app.js"), "w", encoding="utf-8") as f:
        f.write(JS)
    render_images()
    print("spec pages:", len(spec_pages), "zu pages:", len(zu_pages))
