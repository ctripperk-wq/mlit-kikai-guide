"""標準仕様書テキスト(pdftotext -layout)から条項を機械抽出する。"""
import re, html

HEADER_PAT = re.compile(r"公共建築工事標準仕様書（機械設備工事編）令和|^\s*\d+\s+国土交通省大臣官房官庁営繕部\s*$")
HEAD_RE = re.compile(r"^ {0,3}(\d+(?:\.\d+){2,3}) +(\S.*)$")
BAD_TITLE_START = tuple("の「を にはと及ま、。（(以を超")
SECTION_RE = re.compile(r"^ *第[０-９0-9 ]+(編|章|節) ")

# PDFページ範囲 → 編
HEN_PAGES = [(2, 16, 91), (3, 92, 177), (4, 178, 203), (5, 204, 250), (6, 251, 261)]


def hen_of(page):
    for h, a, b in HEN_PAGES:
        if a <= page <= b:
            return h
    return None


def load(path):
    """[(page, raw_line)] ヘッダ・フッタ除去済み"""
    out = []
    page = 1
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            n = line.count("\f")
            line = line.replace("\f", "")
            if not HEADER_PAT.search(line):
                out.append((page, line))
            page += n
    return out


def index(lines):
    """見出し位置を列挙: (i, kind, hen, num, title, page)"""
    heads = []
    for i, (p, raw) in enumerate(lines):
        if SECTION_RE.match(raw):
            heads.append((i, "sec", hen_of(p), None, raw.strip(), p))
            continue
        m = HEAD_RE.match(raw)
        if m and not m.group(2).startswith(BAD_TITLE_START) and not re.match(r"^[0-9０-９]", m.group(2)):
            heads.append((i, "cl", hen_of(p), m.group(1), re.sub(r"\s+", " ", m.group(2)).strip(), p))
    return heads


def extract(lines, heads, hen, num):
    """hen編の条項num(子項目含む)の (title, pages, [raw lines])"""
    for k, (i, kind, h, n, title, p) in enumerate(heads):
        if kind == "cl" and h == hen and n == num:
            end = len(lines)
            for (j, kind2, h2, n2, _, _) in heads[k + 1:]:
                if kind2 == "sec" or n2 is None or not n2.startswith(num + "."):
                    end = j
                    break
            body = lines[i + 1:end]
            pages = sorted({p} | {bp for bp, l in body if l.strip()})
            return title, pages, [l for _, l in body]
    raise KeyError(f"{hen}編 {num} が見つかりません")


MARK_RE = re.compile(r"^(\(\d+\)|（\d+）|\([ｱ-ﾝ]\)|\([a-z]\)|（[a-z]）|[①-⑳]|[㋐-㋾]|注\s|なお、|ただし、)")
SUB_RE = re.compile(r"^(\d+(?:\.\d+){3,4}) +(\S.*)$")


def level(mark):
    if re.match(r"^(\(\d+\)|（\d+）)", mark):
        return 1
    if re.match(r"^\([ｱ-ﾝ]\)", mark):
        return 2
    if re.match(r"^(\([a-z]\)|（[a-z]）)", mark):
        return 3
    if re.match(r"^[①-⑳㋐-㋾]", mark):
        return 4
    return None


def render_body(raw_lines):
    """行を段落・表に整形してHTML文字列を返す"""
    blocks = []  # (type, level, text) type: p / tbl / sub
    cur_level = 1
    for raw in raw_lines:
        if not raw.strip():
            continue
        s = raw.strip()
        lead = len(raw) - len(raw.lstrip(" "))
        sm = SUB_RE.match(s)
        if sm and lead <= 3 and not sm.group(2)[0].isdigit():
            blocks.append(["sub", 0, f"{sm.group(1)} {re.sub(r'\s+', ' ', sm.group(2))}"])
            continue
        m = MARK_RE.match(s)
        if m:
            mk = m.group(1)
            rest = s[len(mk):]
            lv = level(mk)
            if lv:
                cur_level = lv
                text = mk + " " + re.sub(r"^\s+", "", rest)
                blocks.append(["p", lv, re.sub(r" {2,}", " ", text)])
            else:  # なお・ただし・注
                txt = re.sub(r" {2,}", " ", s)
                blocks.append(["p", cur_level if not mk.startswith("注") else 1, txt])
            continue
        is_tbl_line = bool(re.search(r"\S {3,}\S", s)) or bool(re.match(r"^表\s?\d", s))
        prev = blocks[-1] if blocks else None
        if is_tbl_line or (prev and prev[0] == "tbl" and (lead >= 6 or len(s) <= 14)):
            if prev and prev[0] == "tbl":
                prev[2] += "\n" + raw.rstrip()
            else:
                blocks.append(["tbl", 0, raw.rstrip()])
            continue
        # 継続行
        if prev and prev[0] == "p":
            prev[2] += s
        else:
            blocks.append(["p", cur_level, s])

    out = []
    for t, lv, txt in blocks:
        if t == "sub":
            out.append(f'<h4 class="sub">{html.escape(txt)}</h4>')
        elif t == "tbl":
            lines = txt.split("\n")
            ind = min(len(l) - len(l.lstrip(" ")) for l in lines if l.strip())
            body = "\n".join(l[ind:] for l in lines)
            out.append(f'<pre class="tbl">{html.escape(body)}</pre>')
        else:
            out.append(f'<p class="l{lv}">{html.escape(txt)}</p>')
    return "\n".join(out)


def zu_titles(path):
    """標準図: page -> 図名(先頭の意味ある行)"""
    titles = {}
    page = 1
    with open(path, encoding="utf-8") as f:
        for line in f:
            n = line.count("\f")
            l = line.replace("\f", "").strip()
            if l and page not in titles and not re.search(r"公共建築設備工事標準図|国土交通省大臣官房", l):
                titles[page] = re.sub(r"\s{2,}", " ", l)
            page += n
    return titles
