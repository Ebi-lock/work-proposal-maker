#!/usr/bin/env python3
"""商品企画書 PPTX ビルダー

使い方:
    python3 build_deck.py content.json -o 企画書.pptx

content.json の形式は references/schema.md を参照。
デザインルール（このスクリプトが強制する）:
  - フォントは theme.font の1種類のみ（既定: Meiryo）
  - 色は theme.base / theme.sub / theme.accent の3色＋白・本文用ニュートラル（濃灰）
    背景の淡色はベース/サブ/ポイントの「同色相の薄め（tint）」のみで作る
  - 文字が枠に収まらない場合は自動で縮小し、それでも溢れる場合は警告を出す
"""
import argparse
import json
import math
import sys
import unicodedata

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

SLIDE_W, SLIDE_H = 13.333, 7.5
NEUTRAL = "333333"  # 本文テキスト（色数に数えないニュートラル）
MUTED = "767676"    # 出典・フッター
LINE_GRAY = "D9D9D9"
WHITE = "FFFFFF"

BX, BW = 0.5, 12.33          # 本文エリア 左端・幅
BY, BOTTOM = 1.85, 6.8       # 本文エリア 上端・下端

WARNINGS = []
TODO = []  # 【要確認】の残り

DEFAULT_SECTIONS = {
    "summary": "エグゼクティブサマリー",
    "background": "背景・現状分析",
    "three_c": "3C分析",
    "swot": "SWOT分析",
    "asis_tobe": "As-Is / To-Be",
    "goals": "課題とゴール",
    "target_concept": "ターゲット・コンセプト",
    "plan_6w2h": "企画内容（6W2H）",
    "product_4p": "商品戦略（4P）",
    "schedule": "スケジュール・体制",
    "budget": "予算・収支計画",
    "effect_risk": "期待効果とリスク・対策",
    "next_action": "ネクストアクション",
    # 提案書向け
    "current_issues": "背景・現状の課題",
    "solution": "提案内容",
    "process": "導入ステップ",
    "benefits": "期待される効果",
    "options": "プラン・費用",
    "company": "会社概要・実績",
    "bullets": "",
}


# ---------------------------------------------------------------- color utils
def norm_hex(h, field):
    s = str(h).strip().lstrip("#").upper()
    if len(s) != 6 or any(c not in "0123456789ABCDEF" for c in s):
        sys.exit(f"[エラー] theme.{field} の色指定が不正です: {h!r}（例: \"#1F3A5F\"）")
    return s


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """a を b に向けて t (0-1) だけ混ぜる"""
    ra, rb = _rgb(a), _rgb(b)
    return "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ra, rb))


def tint(h, t):
    return mix(h, WHITE, t)


def luminance(h):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def on_color(fill):
    """塗りの上に載せる文字色（白 or ニュートラル）"""
    return WHITE if contrast(fill, WHITE) >= contrast(fill, NEUTRAL) else NEUTRAL


def readable(color, bg=WHITE, ratio=3.0):
    """bg 上で読めるよう、必要なら同色相のまま暗くする"""
    c = color
    for _ in range(20):
        if contrast(c, bg) >= ratio:
            return c
        c = mix(c, "000000", 0.08)
    return c


# ----------------------------------------------------------------- text utils
def char_w(c):
    return 1.0 if unicodedata.east_asian_width(c) in "WFA" else 0.62


def est_lines(text, size_pt, width_in):
    width_pt = max(width_in * 72, 1)
    n = 0
    for para in str(text).split("\n"):
        w = sum(char_w(c) for c in para) * size_pt
        n += max(1, math.ceil(w / width_pt))
    return n


def _norm_paras(paras, bullet):
    out = []
    if isinstance(paras, (str, int, float)):
        paras = [paras]
    for p in paras or []:
        if isinstance(p, dict):
            d = {"text": str(p.get("text", "")), "bold": p.get("bold", False),
                 "bullet": p.get("bullet", bullet), "scale": p.get("scale", 1.0),
                 "color": p.get("color")}
        else:
            d = {"text": str(p), "bold": False, "bullet": bullet, "scale": 1.0, "color": None}
        out.append(d)
    return out


class Deck:
    def __init__(self, data):
        self.data = data
        t = data.get("theme") or {}
        for k in ("base", "sub", "accent"):
            if k not in t:
                sys.exit(f"[エラー] theme.{k} がありません。ベース・サブ・ポイントの3色が必要です。")
        self.base = norm_hex(t["base"], "base")
        self.sub = norm_hex(t["sub"], "sub")
        self.accent = norm_hex(t["accent"], "accent")
        self.font = t.get("font", "Meiryo")
        self.meta = data.get("meta") or {}
        self.prs = Presentation()
        self.prs.slide_width = Inches(SLIDE_W)
        self.prs.slide_height = Inches(SLIDE_H)
        self.page = 0
        self.section_no = 0
        self.cur_label = ""
        self._check_palette()

    # ---- palette sanity
    def _check_palette(self):
        if contrast(self.base, WHITE) < 3.0:
            WARNINGS.append(f"ベース色 #{self.base} は白背景に対して薄く、見出し文字が読みにくい可能性があります"
                            f"（コントラスト比 {contrast(self.base, WHITE):.1f}。3.0以上推奨）。")
        if contrast(self.base, self.sub) < 1.3:
            WARNINGS.append("ベース色とサブ色が近すぎて区別しにくい可能性があります。")

    # ---- primitives
    def box(self, s, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, line_w=1.0):
        shp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        if fill:
            shp.fill.solid()
            shp.fill.fore_color.rgb = RGBColor.from_string(fill)
        else:
            shp.fill.background()
        if line:
            shp.line.color.rgb = RGBColor.from_string(line)
            shp.line.width = Pt(line_w)
        else:
            shp.line.fill.background()
        shp.shadow.inherit = False
        return shp

    def _style_run(self, run, size, color, bold):
        f = run.font
        f.size = Pt(size)
        f.bold = bold
        f.name = self.font
        f.color.rgb = RGBColor.from_string(color)
        rPr = run._r.get_or_add_rPr()
        rPr.set("lang", "ja-JP")
        rPr.set("altLang", "en-US")
        for tag in ("a:ea", "a:cs"):
            el = rPr.find(qn(tag))
            if el is None:
                el = etree.SubElement(rPr, qn(tag))
            el.set("typeface", self.font)

    def text(self, s, x, y, w, h, paras, size=14, color=NEUTRAL, bold=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, bullet=False, min_size=10,
             spacing=0.35, what="", one_line=False):
        items = _norm_paras(paras, bullet)
        if not items:
            return None
        pad_x, pad_y = 0.06, 0.04
        avail_h = (h - pad_y * 2) * 72

        def need(sz):
            total = 0
            for it in items:
                ps = sz * it["scale"]
                wa = w - pad_x * 2 - (0.22 if it["bullet"] else 0)
                total += est_lines(it["text"], ps, wa) * ps * 1.45 + ps * spacing
            return total - items[-1]["scale"] * sz * spacing

        def wraps(sz):
            return one_line and any(
                est_lines(it["text"], sz * it["scale"], w - pad_x * 2 - 0.15) > len(it["text"].split("\n"))
                for it in items)

        sz = size
        while sz > min_size and (need(sz) > avail_h or wraps(sz)):
            sz -= 0.5
        if need(sz) > avail_h:
            preview = items[0]["text"][:20].replace("\n", " ")
            WARNINGS.append(f"p.{self.page}「{self.cur_label}」{what or ''}: 文字量が多く枠からはみ出す可能性があります"
                            f"（{min_size}ptまで縮小済み）。先頭: 「{preview}…」→ 文章を短くするか項目を減らしてください。")

        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Inches(pad_x)
        tf.margin_top = tf.margin_bottom = Inches(pad_y)
        for i, it in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            ps = sz * it["scale"]
            if i < len(items) - 1:
                p.space_after = Pt(ps * spacing)
            run = p.add_run()
            run.text = it["text"]
            self._style_run(run, ps, it["color"] or color, it["bold"] or bold)
            if it["bullet"]:
                pPr = p._p.get_or_add_pPr()
                pPr.set("marL", str(int(Inches(0.22))))
                pPr.set("indent", str(int(-Inches(0.22))))
                buClr = etree.SubElement(pPr, qn("a:buClr"))
                clr = etree.SubElement(buClr, qn("a:srgbClr"))
                clr.set("val", self.base if contrast(self.base, WHITE) >= 3 else readable(self.base))
                buFont = etree.SubElement(pPr, qn("a:buFont"))
                buFont.set("typeface", self.font)
                buChar = etree.SubElement(pPr, qn("a:buChar"))
                buChar.set("char", "•")
        return tb

    # ---- composite parts
    def card(self, s, x, y, w, h, header, body, header_fill=None, bullet=True, size=14, body_fill=None):
        header_fill = header_fill or self.base
        hh = 0.45
        self.box(s, x, y, w, hh, fill=header_fill)
        self.text(s, x + 0.1, y, w - 0.2, hh, [header], size=14, bold=True,
                  color=on_color(header_fill), anchor=MSO_ANCHOR.MIDDLE, min_size=11, what=f"見出し「{header}」")
        bf = body_fill or tint(self.sub, 0.88)
        self.box(s, x, y + hh, w, h - hh, fill=bf)
        if isinstance(body, str):
            body, bullet = [body], False
        self.text(s, x + 0.15, y + hh + 0.12, w - 0.3, h - hh - 0.22, body, size=size,
                  bullet=bullet, color=on_color(bf), what=f"「{header}」本文")

    def insight_height(self, insight, w=BW):
        lines = insight if isinstance(insight, list) else [insight]
        n = sum(est_lines(l, 14, w - 0.6) for l in lines)
        return max(0.85, 0.5 + 0.34 * n)

    def insight(self, s, x, y, w, h, insight, label="示唆"):
        lines = insight if isinstance(insight, list) else [insight]
        bg = tint(self.accent, 0.9)
        self.box(s, x, y, w, h, fill=bg)
        self.box(s, x, y, 0.08, h, fill=self.accent)
        lab = readable(self.accent, bg, 3.0)
        paras = [{"text": label, "bold": True, "scale": 0.85, "color": lab}]
        paras += [{"text": l, "bold": True} for l in lines]
        self.text(s, x + 0.25, y + 0.06, w - 0.4, h - 0.12, paras, size=14, spacing=0.2,
                  anchor=MSO_ANCHOR.MIDDLE, color=NEUTRAL, what="示唆ボックス")

    def kpi(self, s, x, y, w, h, value, label, highlight=False):
        bg = tint(self.sub, 0.88)
        self.box(s, x, y, w, h, fill=bg)
        col = readable(self.accent if highlight else self.base, bg, 3.0)
        vh = h * 0.58
        self.text(s, x + 0.1, y + 0.08, w - 0.2, vh, [value], size=30, bold=True, color=col,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM, min_size=14, what="数値", one_line=True)
        self.text(s, x + 0.1, y + 0.08 + vh, w - 0.2, h - vh - 0.16, [label], size=12, color=NEUTRAL,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP, min_size=9, what="数値ラベル")

    def table(self, s, x, y, w, h, headers, rows, ratios=None, total=None, size=12, num_cols=()):
        ncol = len(headers)
        ratios = ratios or [1] * ncol
        tot = sum(ratios)
        widths = [w * r / tot for r in ratios]
        hh = 0.45
        nrows = len(rows) + (1 if total else 0)
        rh = min(0.7, (h - hh) / max(nrows, 1))
        cx = x
        for i, head in enumerate(headers):
            self.box(s, cx, y, widths[i], hh, fill=self.base)
            self.text(s, cx + 0.08, y, widths[i] - 0.16, hh, [head], size=12, bold=True,
                      color=on_color(self.base), anchor=MSO_ANCHOR.MIDDLE, min_size=9, what="表見出し")
            cx += widths[i]
        cy = y + hh
        for ri, row in enumerate(rows):
            fill = WHITE if ri % 2 == 0 else tint(self.sub, 0.88)
            self.box(s, x, cy, w, rh, fill=fill)
            cx = x
            for ci in range(ncol):
                val = row[ci] if ci < len(row) else ""
                self.text(s, cx + 0.08, cy, widths[ci] - 0.16, rh, [val], size=size,
                          anchor=MSO_ANCHOR.MIDDLE, min_size=9, what="表セル",
                          align=PP_ALIGN.RIGHT if (ci in num_cols and _looks_numeric(val)) else PP_ALIGN.LEFT)
                cx += widths[ci]
            cy += rh
        self.box(s, x, cy, w, 0.015, fill=LINE_GRAY)
        if total:
            fill = tint(self.base, 0.82)
            self.box(s, x, cy, w, rh, fill=fill)
            cx = x
            for ci in range(ncol):
                val = total[ci] if ci < len(total) else ""
                self.text(s, cx + 0.08, cy, widths[ci] - 0.16, rh, [val], size=size, bold=True,
                          anchor=MSO_ANCHOR.MIDDLE, min_size=9, color=on_color(fill), what="合計行",
                          align=PP_ALIGN.RIGHT if (ci in num_cols and _looks_numeric(val)) else PP_ALIGN.LEFT)
                cx += widths[ci]
            cy += rh
        return cy

    # ---- slide chrome
    def new_slide(self):
        s = self.prs.slides.add_slide(self.prs.slide_layouts[6])
        self.page += 1
        return s

    def content_slide(self, sd):
        stype = sd["type"]
        label = sd.get("section") or DEFAULT_SECTIONS.get(stype, "")
        self.cur_label = label
        s = self.new_slide()
        self.section_no += 1
        message = sd.get("message", "")
        if not message:
            WARNINGS.append(f"p.{self.page}「{label}」: message（このスライドで言いたい一文）が空です。")
        self.text(s, 0.5, 0.3, 12.3, 0.35, [f"{self.section_no:02d}　{label}"], size=12, bold=True,
                  color=readable(self.base), min_size=10, what="セクション名")
        msz = 24
        while msz > 19 and est_lines(message, msz, 12.3 - 0.2) > 1:
            msz -= 0.5
        if est_lines(message, msz, 12.3 - 0.2) > 1:
            msz = 22  # 2行になる場合は少し小さくして2行に収める
            WARNINGS.append(f"p.{self.page}「{label}」: メッセージが1行に収まらず2行になります（{len(message)}字）。"
                            "40字前後に短くすると読みやすくなります。")
        self.text(s, 0.5, 0.62, 12.3, 0.95, [message], size=msz, bold=True, color=NEUTRAL,
                  min_size=18, anchor=MSO_ANCHOR.MIDDLE, spacing=0.1, what="メッセージ")
        self.box(s, 0.5, 1.6, 12.33, 0.04, fill=self.base)
        self.text(s, 0.5, 7.0, 9.0, 0.3, [self.meta.get("title", "")], size=9, color=MUTED, min_size=8, what="フッター")
        self.text(s, 11.83, 7.0, 1.0, 0.3, [str(self.page)], size=9, color=MUTED, align=PP_ALIGN.RIGHT)
        return s

    def bottom_parts(self, s, sd, label="示唆"):
        """sources / insight を下から配置し、本文に使える下端を返す"""
        bottom = BOTTOM
        src = sd.get("sources")
        if src:
            src_txt = "出典：" + " ／ ".join(src if isinstance(src, list) else [src])
            self.text(s, BX, bottom - 0.32, BW, 0.32, [src_txt], size=9, color=MUTED, min_size=8, what="出典")
            bottom -= 0.4
        ins = sd.get("insight")
        if ins:
            ih = self.insight_height(ins)
            self.insight(s, BX, bottom - ih, BW, ih, ins, label=sd.get("insight_label", label))
            bottom -= ih + 0.18
        return bottom

    # ---------------------------------------------------------- slide types
    def s_cover(self, sd):
        s = self.new_slide()
        self.cur_label = "表紙"
        m = {**self.meta, **{k: v for k, v in sd.items() if k != "type"}}
        self.box(s, 0, 0, 0.45, SLIDE_H, fill=self.base)
        if m.get("confidential"):
            self.text(s, 10.3, 0.35, 2.5, 0.35, [m.get("confidential") if isinstance(m.get("confidential"), str) else "社外秘"],
                      size=11, color=MUTED, align=PP_ALIGN.RIGHT)
        if m.get("to"):
            self.text(s, 1.2, 0.9, 9.0, 0.6, [m["to"]], size=20, bold=True, color=NEUTRAL, min_size=14, what="宛先")
        if m.get("category"):
            self.text(s, 1.2, 1.7, 11, 0.45, [m["category"]], size=16, bold=True, color=readable(self.base))
        self.text(s, 1.2, 2.2, 11.3, 1.7, [m.get("title", "（タイトル）")], size=38, bold=True, color=NEUTRAL,
                  min_size=26, anchor=MSO_ANCHOR.BOTTOM, spacing=0.1, what="タイトル")
        self.box(s, 1.26, 4.05, 1.3, 0.07, fill=self.accent)
        if m.get("subtitle"):
            self.text(s, 1.2, 4.25, 11.3, 0.9, [m["subtitle"]], size=18, color=NEUTRAL, min_size=14, what="サブタイトル")
        org = "　".join(x for x in (m.get("company"), m.get("department")) if x)
        info = [x for x in (org, m.get("author"), m.get("date")) if x]
        if info:
            self.text(s, 1.2, 5.7, 11.3, 1.0, ["　".join(info[:2])] + info[2:], size=14, color=NEUTRAL, spacing=0.2)

    def s_summary(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        items = sd.get("items") or []
        kpis = sd.get("kpis") or []
        kh = 1.7 if kpis else 0
        top_h = bottom - BY - (kh + 0.2 if kpis else 0)
        n = max(len(items), 1)
        gap = 0.25
        cw = (BW - gap * (n - 1)) / n
        for i, it in enumerate(items):
            self.card(s, BX + i * (cw + gap), BY, cw, top_h, it.get("label", ""), it.get("text", ""), size=15)
        if kpis:
            m = len(kpis)
            kw = (BW - gap * (m - 1)) / m
            for i, k in enumerate(kpis):
                self.kpi(s, BX + i * (kw + gap), bottom - kh, kw, kh, k.get("value", ""), k.get("label", ""), k.get("highlight", False))

    def s_background(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        data = sd.get("data") or []
        lw = 7.2 if data else BW
        self.text(s, BX, BY, lw, bottom - BY, sd.get("points") or [], size=16, bullet=True, spacing=0.6, what="本文")
        if data:
            gap = 0.2
            n = len(data)
            dh = (bottom - BY - gap * (n - 1)) / n
            dx = BX + lw + 0.3
            dw = BW - lw - 0.3
            for i, d in enumerate(data):
                self.kpi(s, dx, BY + i * (dh + gap), dw, dh, d.get("value", ""), d.get("label", ""), d.get("highlight", False))

    def _columns(self, s, sd, cols, bottom, fills=None):
        gap = 0.25
        n = len(cols)
        cw = (BW - gap * (n - 1)) / n
        for i, (head, body) in enumerate(cols):
            fill = fills[i] if fills else None
            self.card(s, BX + i * (cw + gap), BY, cw, bottom - BY, head, body or ["（未記入）"], header_fill=fill)

    def s_three_c(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd, label="成功のカギ（KSF）")
        self._columns(s, sd, [("Customer｜顧客・市場", sd.get("customer")),
                              ("Competitor｜競合", sd.get("competitor")),
                              ("Company｜自社", sd.get("company"))], bottom)

    def _grid(self, s, cells, bottom, fills):
        gap = 0.2
        cw = (BW - gap) / 2
        ch = (bottom - BY - gap) / 2
        for i, (head, body) in enumerate(cells):
            r, c = divmod(i, 2)
            self.card(s, BX + c * (cw + gap), BY + r * (ch + gap), cw, ch, head, body or ["（未記入）"],
                      header_fill=fills[r], size=13)

    def s_swot(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd, label="クロスSWOT／戦略の方向性")
        self._grid(s, [("S｜強み（内部）", sd.get("strengths")), ("W｜弱み（内部）", sd.get("weaknesses")),
                       ("O｜機会（外部）", sd.get("opportunities")), ("T｜脅威（外部）", sd.get("threats"))],
                   bottom, [self.base, self.sub])

    def s_product_4p(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        self._grid(s, [("Product｜商品", sd.get("product")), ("Price｜価格", sd.get("price")),
                       ("Place｜流通・チャネル", sd.get("place")), ("Promotion｜販促", sd.get("promotion"))],
                   bottom, [self.base, self.sub])

    def s_asis_tobe(self, sd):
        s = self.content_slide(sd)
        gaps = sd.get("gaps")
        if gaps and not sd.get("insight"):
            sd = {**sd, "insight": [f"{i + 1}. {g}" for i, g in enumerate(gaps)], "insight_label": "ギャップ＝解決すべき課題"}
        bottom = self.bottom_parts(s, sd)
        aw = 0.8
        cw = (BW - aw - 0.4) / 2
        h = bottom - BY
        self.card(s, BX, BY, cw, h, "As-Is｜現状", sd.get("asis") or [], header_fill=self.sub)
        arrow = self.box(s, BX + cw + 0.2, BY + h / 2 - 0.45, aw, 0.9, fill=self.base, shape=MSO_SHAPE.RIGHT_ARROW)
        self.card(s, BX + cw + aw + 0.4, BY, cw, h, "To-Be｜目指す姿", sd.get("tobe") or [], header_fill=self.base)

    def s_goals(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        issues = sd.get("issues") or []
        lw = 5.0
        nums = "①②③④⑤⑥⑦⑧⑨"
        self.card(s, BX, BY, lw, bottom - BY, "解決すべき課題",
                  [f"{nums[i] if i < 9 else i + 1} {t}" for i, t in enumerate(issues)], bullet=False, size=15)
        rx, rw = BX + lw + 0.3, BW - lw - 0.3
        q = sd.get("quantitative") or []
        ql = sd.get("qualitative") or []
        y = BY
        self.text(s, rx, y, rw, 0.35, ["定量目標（KPI）"], size=13, bold=True, color=readable(self.base))
        y += 0.4
        kh = 1.75 if ql else bottom - y
        if q:
            gap = 0.2
            kw = (rw - gap * (len(q) - 1)) / len(q)
            for i, k in enumerate(q):
                lab = k.get("metric", "")
                if k.get("deadline"):
                    lab += f"\n（{k['deadline']}）"
                self.kpi(s, rx + i * (kw + gap), y, kw, kh, k.get("target", ""), lab, k.get("highlight", False))
        y += kh + 0.25
        if ql:
            self.card(s, rx, y, rw, bottom - y, "定性目標", ql, header_fill=self.sub)

    def s_target_concept(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        p = sd.get("persona") or {}
        lw = 5.3
        hh = 0.45
        self.box(s, BX, BY, lw, hh, fill=self.sub)
        self.text(s, BX + 0.1, BY, lw - 0.2, hh, ["ターゲット（ペルソナ）"], size=14, bold=True,
                  color=on_color(self.sub), anchor=MSO_ANCHOR.MIDDLE)
        bf = tint(self.sub, 0.88)
        self.box(s, BX, BY + hh, lw, bottom - BY - hh, fill=bf)
        paras = []
        if p.get("profile"):
            paras.append({"text": p["profile"], "bold": True, "scale": 1.15, "bullet": False})
        paras += [{"text": a, "bullet": True} for a in p.get("attributes", [])]
        if p.get("needs"):
            paras.append({"text": "課題・ニーズ", "bold": True, "bullet": False, "color": readable(self.base, bf)})
            paras += [{"text": a, "bullet": True} for a in p["needs"]]
        self.text(s, BX + 0.15, BY + hh + 0.12, lw - 0.3, bottom - BY - hh - 0.22, paras, size=14, what="ペルソナ")

        c = sd.get("concept") or {}
        rx, rw = BX + lw + 0.3, BW - lw - 0.3
        y = BY
        self.text(s, rx, y, rw, 0.35, ["コンセプト"], size=13, bold=True, color=readable(self.base))
        y += 0.4
        cb = tint(self.base, 0.9)
        self.box(s, rx, y, rw, 1.35, fill=cb)
        self.box(s, rx, y, 0.08, 1.35, fill=self.base)
        self.text(s, rx + 0.25, y + 0.05, rw - 0.4, 1.25, [c.get("catch", "（コンセプト一文）")], size=24, bold=True,
                  color=readable(self.base, cb, 4.5), anchor=MSO_ANCHOR.MIDDLE, min_size=16, spacing=0.1, what="キャッチ")
        y += 1.5
        if c.get("description"):
            dh = min(1.1, 0.3 + 0.32 * est_lines(c["description"], 14, rw - 0.12))
            self.text(s, rx, y, rw, dh, [c["description"]], size=14, what="コンセプト説明")
            y += dh + 0.1
        if c.get("values"):
            self.card(s, rx, y, rw, bottom - y, "提供価値", c["values"], header_fill=self.base)

    def s_plan_6w2h(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        r = sd.get("rows") or {}
        left = [("why", "Why\n目的"), ("whom", "Whom\n誰に"), ("what", "What\n何を"), ("how", "How\nどうやって")]
        right = [("how_much", "How much\nいくらで"), ("when", "When\nいつ"), ("where", "Where\nどこで"), ("who", "Who\n誰が")]
        gapx, gapy = 0.3, 0.12
        cw = (BW - gapx) / 2
        rh = (bottom - BY - gapy * 3) / 4
        lab_w = 1.75
        for col, items in enumerate((left, right)):
            x = BX + col * (cw + gapx)
            for i, (key, lab) in enumerate(items):
                y = BY + i * (rh + gapy)
                self.box(s, x, y, lab_w, rh, fill=self.base)
                self.text(s, x + 0.05, y, lab_w - 0.1, rh, lab.split("\n"), size=12, bold=True, spacing=0.05, color=on_color(self.base),
                          align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, min_size=9)
                bf = tint(self.sub, 0.88)
                self.box(s, x + lab_w, y, cw - lab_w, rh, fill=bf)
                val = r.get(key) or "【要確認】"
                if not r.get(key):
                    TODO.append(f"p.{self.page}「{self.cur_label}」{lab.replace(chr(10), '｜')} が未記入")
                self.text(s, x + lab_w + 0.12, y + 0.04, cw - lab_w - 0.24, rh - 0.08,
                          val if isinstance(val, list) else [val], size=13, min_size=9,
                          bullet=isinstance(val, list), anchor=MSO_ANCHOR.MIDDLE, spacing=0.15, what=lab.replace("\n", "｜"))

    def s_schedule(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        periods = sd.get("periods") or []
        phases = sd.get("phases") or []
        team = sd.get("team") or []
        team_h = 1.15 if team else 0
        gantt_bottom = bottom - (team_h + 0.65 if team else 0)
        lab_w = 3.3
        tl_x, tl_w = BX + lab_w, BW - lab_w
        n = max(len(periods), 1)
        pw = tl_w / n
        hh = 0.45
        self.box(s, BX, BY, BW, hh, fill=self.base)
        self.text(s, BX + 0.1, BY, lab_w - 0.2, hh, ["フェーズ／担当"], size=12, bold=True,
                  color=on_color(self.base), anchor=MSO_ANCHOR.MIDDLE)
        for i, p in enumerate(periods):
            self.text(s, tl_x + i * pw, BY, pw, hh, [p], size=12, bold=True, color=on_color(self.base),
                      align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, min_size=8)
        rh = min(0.65, (gantt_bottom - BY - hh) / max(len(phases), 1))
        top = BY + hh
        for i in range(1, n):
            self.box(s, tl_x + i * pw, top, 0.01, rh * len(phases), fill=LINE_GRAY)

        def idx(v):
            if isinstance(v, int):
                return max(0, min(v, n - 1))
            if v in periods:
                return periods.index(v)
            WARNINGS.append(f"p.{self.page} スケジュール: 期間 {v!r} が periods に見つかりません。")
            return 0

        for ri, ph in enumerate(phases):
            y = top + ri * rh
            if ri % 2 == 1:
                self.box(s, BX, y, lab_w, rh, fill=tint(self.sub, 0.9))
            paras = [{"text": ph.get("name", ""), "bold": True}]
            if ph.get("owner"):
                paras.append({"text": ph["owner"], "scale": 0.8, "color": MUTED})
            self.text(s, BX + 0.1, y, lab_w - 0.2, rh, paras, size=13, anchor=MSO_ANCHOR.MIDDLE,
                      spacing=0.05, min_size=9, what="フェーズ名")
            a, b = idx(ph.get("start", 0)), idx(ph.get("end", ph.get("start", 0)))
            if b < a:
                a, b = b, a
            fill = self.accent if ph.get("highlight") else self.sub
            bar = self.box(s, tl_x + a * pw + 0.06, y + rh * 0.22, (b - a + 1) * pw - 0.12, rh * 0.56,
                           fill=fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            if ph.get("label"):
                self.text(s, tl_x + a * pw + 0.1, y + rh * 0.22, (b - a + 1) * pw - 0.2, rh * 0.56, [ph["label"]],
                          size=11, color=on_color(fill), anchor=MSO_ANCHOR.MIDDLE, min_size=8, what="バー注記")
        self.box(s, BX, top + rh * len(phases), BW, 0.015, fill=LINE_GRAY)
        if team:
            ty = bottom - team_h
            self.text(s, BX, ty - 0.4, 3, 0.35, ["実施体制"], size=13, bold=True, color=readable(self.base))
            gap = 0.2
            m = len(team)
            tw = (BW - gap * (m - 1)) / m
            for i, t in enumerate(team):
                x = BX + i * (tw + gap)
                bf = tint(self.sub, 0.88)
                self.box(s, x, ty, tw, team_h, fill=bf)
                self.box(s, x, ty, tw, 0.06, fill=self.base)
                self.text(s, x + 0.12, ty + 0.12, tw - 0.24, team_h - 0.2,
                          [{"text": t.get("role", ""), "scale": 0.85, "color": MUTED},
                           {"text": t.get("name", ""), "bold": True}], size=14, spacing=0.1, what="体制")

    def s_budget(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        costs = sd.get("costs") or []
        plan = sd.get("plan")
        metrics = sd.get("metrics") or []
        lw = 6.5
        rows = [[c.get("item", ""), c.get("amount", ""), c.get("note", "")] for c in costs]
        total = ["合計", sd["total"], ""] if sd.get("total") else None
        self.text(s, BX, BY, lw, 0.35, ["費用内訳"], size=13, bold=True, color=readable(self.base))
        self.table(s, BX, BY + 0.4, lw, bottom - BY - 0.4, ["費目", "金額", "備考"], rows, [2.2, 1.4, 2.6], total, num_cols={1})
        rx, rw = BX + lw + 0.3, BW - lw - 0.3
        y = BY
        if plan:
            ph = min(2.8, 0.85 + 0.5 * len(plan.get("rows", [])))
            self.text(s, rx, y, rw, 0.35, [plan.get("title", "収支計画")], size=13, bold=True, color=readable(self.base))
            heads = plan.get("headers") or []
            self.table(s, rx, y + 0.4, rw, ph, heads, plan.get("rows", []), [1.4] + [1] * (len(heads) - 1),
                       num_cols=set(range(1, len(heads))))
            y += ph + 0.6
        if metrics:
            gap = 0.2
            if plan:
                m = len(metrics)
                kw = (rw - gap * (m - 1)) / m
                for i, k in enumerate(metrics):
                    self.kpi(s, rx + i * (kw + gap), y, kw, bottom - y, k.get("value", ""), k.get("label", ""), k.get("highlight", False))
            else:
                m = len(metrics)
                kh = (bottom - y - gap * (m - 1)) / m
                for i, k in enumerate(metrics):
                    self.kpi(s, rx, y + i * (kh + gap), rw, kh, k.get("value", ""), k.get("label", ""), k.get("highlight", False))

    def s_effect_risk(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        lw = 4.6
        self.card(s, BX, BY, lw, bottom - BY, sd.get("effects_label", "期待効果"), sd.get("effects") or [], size=14)
        risks = sd.get("risks") or []
        has_imp = any(r.get("impact") for r in risks)
        heads = ["想定リスク", "影響度", "対策・代替案"] if has_imp else ["想定リスク", "対策・代替案"]
        ratios = [2.2, 0.8, 3.2] if has_imp else [2.4, 3.4]
        rows = [[r.get("risk", ""), r.get("impact", ""), r.get("countermeasure", "")] if has_imp
                else [r.get("risk", ""), r.get("countermeasure", "")] for r in risks]
        rx, rw = BX + lw + 0.3, BW - lw - 0.3
        self.table(s, rx, BY, rw, bottom - BY, heads, rows, ratios, size=12)

    def s_next_action(self, sd):
        s = self.content_slide(sd)
        bottom = BOTTOM
        if sd.get("contact"):
            self.text(s, BX, bottom - 0.4, BW, 0.4, [sd["contact"]], size=12, color=MUTED)
            bottom -= 0.5
        bottom = min(bottom, self.bottom_parts(s, {k: v for k, v in sd.items() if k != "contact"}))
        top = BY
        if sd.get("conclusion"):
            cb = tint(self.base, 0.9)
            ch = max(0.9, 0.35 + 0.42 * est_lines(sd["conclusion"], 18, BW - 0.5))
            self.box(s, BX, top, BW, ch, fill=cb)
            self.box(s, BX, top, 0.08, ch, fill=self.base)
            self.text(s, BX + 0.3, top + 0.05, BW - 0.45, ch - 0.1, [sd["conclusion"]], size=18, bold=True,
                      color=readable(self.base, cb, 4.5), anchor=MSO_ANCHOR.MIDDLE, min_size=13, what="結論")
            top += ch + 0.3
        asks = sd.get("asks") or []
        n = max(len(asks), 1)
        rh = min(1.1, (bottom - top) / n)
        for i, a in enumerate(asks):
            a = a if isinstance(a, dict) else {"text": a}
            y = top + i * rh
            d = min(0.7, rh - 0.25)
            self.box(s, BX, y + (rh - d) / 2 - 0.05, d, d, fill=self.base, shape=MSO_SHAPE.OVAL)
            self.text(s, BX, y + (rh - d) / 2 - 0.05, d, d, [str(i + 1)], size=20, bold=True,
                      color=on_color(self.base), align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            tw = BW - d - 0.3 - (2.6 if a.get("deadline") else 0)
            self.text(s, BX + d + 0.3, y, tw, rh - 0.1, [a.get("text", "")], size=18, bold=True,
                      anchor=MSO_ANCHOR.MIDDLE, min_size=12, what="依頼事項")
            if a.get("deadline"):
                self.text(s, BX + BW - 2.5, y, 2.5, rh - 0.1, [a["deadline"]], size=16, bold=True,
                          color=readable(self.accent), align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, min_size=11)
            self.box(s, BX + d + 0.3, y + rh - 0.06, BW - d - 0.3, 0.012, fill=LINE_GRAY)

    # ------------------------------------------------ 提案書向けスライド
    def _row_cols(self, n, max_cols=4):
        cols = n if n <= max_cols else math.ceil(n / 2)
        rows = math.ceil(n / cols) if n else 1
        return cols, rows

    def s_current_issues(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd, label="このままにした場合")
        issues = sd.get("issues") or []
        data = sd.get("data") or []
        kh = 1.6 if data else 0
        area_b = bottom - (kh + 0.2 if data else 0)
        cols, rows = self._row_cols(len(issues))
        gap = 0.25
        cw = (BW - gap * (cols - 1)) / cols
        ch = (area_b - BY - gap * (rows - 1)) / rows
        for i, it in enumerate(issues):
            it = it if isinstance(it, dict) else {"title": it}
            r, c = divmod(i, cols)
            x, y = BX + c * (cw + gap), BY + r * (ch + gap)
            bf = tint(self.sub, 0.88)
            self.box(s, x, y, cw, 0.45, fill=self.base)
            self.text(s, x + 0.1, y, cw - 0.2, 0.45, [f"課題{i + 1}｜{it.get('title', '')}"], size=14, bold=True,
                      color=on_color(self.base), anchor=MSO_ANCHOR.MIDDLE, min_size=10, what="課題見出し")
            self.box(s, x, y + 0.45, cw, ch - 0.45, fill=bf)
            detail = it.get("detail") or []
            paras = [{"text": d, "bullet": True} for d in (detail if isinstance(detail, list) else [detail])]
            if it.get("impact"):
                paras.append({"text": "影響：" + it["impact"], "bold": True, "color": readable(self.base, bf, 4.5)})
            self.text(s, x + 0.15, y + 0.57, cw - 0.3, ch - 0.67, paras, size=14, what=f"課題{i + 1}")
        if data:
            m = len(data)
            kw = (BW - gap * (m - 1)) / m
            for i, k in enumerate(data):
                self.kpi(s, BX + i * (kw + gap), area_b + 0.2, kw, kh, k.get("value", ""), k.get("label", ""), k.get("highlight", False))

    def s_solution(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        y = BY
        if sd.get("overview"):
            cb = tint(self.base, 0.9)
            oh = max(0.85, 0.3 + 0.42 * est_lines(sd["overview"], 18, BW - 0.5))
            self.box(s, BX, y, BW, oh, fill=cb)
            self.box(s, BX, y, 0.08, oh, fill=self.base)
            self.text(s, BX + 0.3, y + 0.05, BW - 0.45, oh - 0.1, [sd["overview"]], size=18, bold=True,
                      color=readable(self.base, cb, 4.5), anchor=MSO_ANCHOR.MIDDLE, min_size=13, what="提案の要点")
            y += oh + 0.25
        items = sd.get("items") or []
        cols, rows = self._row_cols(len(items))
        gap = 0.25
        cw = (BW - gap * (cols - 1)) / cols
        ch = (bottom - y - gap * (rows - 1)) / rows
        for i, it in enumerate(items):
            r, c = divmod(i, cols)
            x, yy = BX + c * (cw + gap), y + r * (ch + gap)
            body = []
            if it.get("issue"):
                body.append({"text": "対応する課題：" + it["issue"], "scale": 0.85, "color": MUTED})
            t = it.get("text") or []
            body += [{"text": v, "bullet": isinstance(t, list)} for v in (t if isinstance(t, list) else [t])]
            self.card(s, x, yy, cw, ch, it.get("title", ""), body, bullet=False, size=14)

    def s_process(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        steps = sd.get("steps") or []
        n = max(len(steps), 1)
        gap = 0.06
        sw = (BW - gap * (n - 1)) / n
        hh = 1.0
        for i, st in enumerate(steps):
            x = BX + i * (sw + gap)
            fill = self.accent if st.get("highlight") else self.base
            shape = MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON
            self.box(s, x, BY, sw + (0.25 if i < n - 1 else 0), hh, fill=fill, shape=shape)
            self.text(s, x + 0.3, BY, sw - 0.5, hh,
                      [{"text": f"STEP {i + 1}", "scale": 0.75}, {"text": st.get("title", ""), "bold": True}],
                      size=15, color=on_color(fill), align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                      spacing=0.05, min_size=10, what=f"STEP{i + 1}")
            y = BY + hh + 0.2
            if st.get("period"):
                self.text(s, x + 0.05, y, sw - 0.1, 0.4, [st["period"]], size=13, bold=True,
                          color=readable(self.base), min_size=10)
                y += 0.45
            t = st.get("text") or []
            self.box(s, x, y, sw, bottom - y, fill=tint(self.sub, 0.88))
            self.text(s, x + 0.12, y + 0.1, sw - 0.24, bottom - y - 0.2, t if isinstance(t, list) else [t],
                      size=13, bullet=isinstance(t, list), min_size=9, what=f"STEP{i + 1} 説明")

    def kpi_change(self, s, x, y, w, h, m):
        bg = tint(self.sub, 0.88)
        self.box(s, x, y, w, h, fill=bg)
        self.text(s, x + 0.1, y + 0.1, w - 0.2, 0.4, [m.get("label", "")], size=13, bold=True,
                  color=NEUTRAL, align=PP_ALIGN.CENTER, min_size=10, what="効果ラベル")
        col = readable(self.accent if m.get("highlight") else self.base, bg, 3.0)
        has_ba = m.get("before") or m.get("after")
        vh = h - 0.6 - (0.5 if has_ba else 0)
        self.text(s, x + 0.1, y + 0.5, w - 0.2, vh, [m.get("value", "")], size=34, bold=True, color=col,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, min_size=16, what="効果の数値", one_line=True)
        if has_ba:
            ba = f"{m.get('before')}　→　{m.get('after', '')}" if (m.get("before") and m.get("after")) else (m.get("before") or m.get("after"))
            self.text(s, x + 0.1, y + h - 0.55, w - 0.2, 0.45, [ba],
                      size=13, color=NEUTRAL, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, min_size=9, what="変化")

    def s_benefits(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        metrics = sd.get("metrics") or []
        points = sd.get("points") or []
        gap = 0.25
        mh = min(2.4, bottom - BY) if points else bottom - BY
        if metrics:
            m = len(metrics)
            kw = (BW - gap * (m - 1)) / m
            for i, k in enumerate(metrics):
                self.kpi_change(s, BX + i * (kw + gap), BY, kw, mh, k)
        if points:
            y = BY + (mh + gap if metrics else 0)
            self.card(s, BX, y, BW, bottom - y, sd.get("points_label", "その他の効果"), points, header_fill=self.sub)

    def s_options(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        plans = sd.get("plans") or []
        n = max(len(plans), 1)
        gap = 0.3
        cw = (BW - gap * (n - 1)) / n
        top = BY + 0.25  # 推奨タグ分
        for i, p in enumerate(plans):
            x = BX + i * (cw + gap)
            rec = p.get("recommended")
            head = self.base if rec else self.sub
            bf = tint(self.sub, 0.88)
            self.box(s, x, top, cw, bottom - top, fill=bf, line=self.accent if rec else None, line_w=2.5)
            self.box(s, x, top, cw, 0.55, fill=head)
            self.text(s, x + 0.1, top, cw - 0.2, 0.55, [p.get("name", "")], size=16, bold=True,
                      color=on_color(head), align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, min_size=11)
            if rec:
                self.box(s, x + cw / 2 - 0.6, top - 0.25, 1.2, 0.36, fill=self.accent, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
                self.text(s, x + cw / 2 - 0.6, top - 0.25, 1.2, 0.36, [p.get("tag", "推奨")], size=12, bold=True,
                          color=on_color(self.accent), align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, min_size=9)
            y = top + 0.65
            self.text(s, x + 0.1, y, cw - 0.2, 0.8, [p.get("price", "")], size=26, bold=True,
                      color=readable(self.base, bf, 4.5), align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
                      min_size=14, what="価格", one_line=True)
            y += 0.85
            if p.get("note"):
                self.text(s, x + 0.1, y, cw - 0.2, 0.4, [p["note"]], size=11, color=MUTED, align=PP_ALIGN.CENTER, min_size=9)
                y += 0.45
            self.box(s, x + 0.2, y, cw - 0.4, 0.015, fill=LINE_GRAY)
            self.text(s, x + 0.2, y + 0.1, cw - 0.4, bottom - y - 0.2, p.get("features") or [], size=13,
                      bullet=True, min_size=9, what=f"{p.get('name', '')} 内容")

    def s_company(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        profile = sd.get("profile") or []
        ach = sd.get("achievements") or []
        cases = sd.get("cases") or []
        lw = 6.0 if (ach or cases) else BW
        rows = [[p.get("label", ""), p.get("value", "")] for p in profile]
        self.text(s, BX, BY, lw, 0.35, ["会社概要"], size=13, bold=True, color=readable(self.base))
        self.table(s, BX, BY + 0.4, lw, bottom - BY - 0.4, ["項目", "内容"], rows, [1, 2.6])
        if ach or cases:
            rx, rw = BX + lw + 0.3, BW - lw - 0.3
            y = BY
            self.text(s, rx, y, rw, 0.35, ["実績"], size=13, bold=True, color=readable(self.base))
            y += 0.4
            gap = 0.2
            if ach:
                kh = 1.6 if cases else bottom - y
                m = len(ach)
                kw = (rw - gap * (m - 1)) / m
                for i, k in enumerate(ach):
                    self.kpi(s, rx + i * (kw + gap), y, kw, kh, k.get("value", ""), k.get("label", ""), k.get("highlight", False))
                y += kh + 0.25
            if cases:
                self.card(s, rx, y, rw, bottom - y, sd.get("cases_label", "主な導入事例"), cases, header_fill=self.sub)

    def s_bullets(self, sd):
        s = self.content_slide(sd)
        bottom = self.bottom_parts(s, sd)
        self.text(s, BX, BY, BW, bottom - BY, sd.get("bullets") or [], size=16, bullet=True, spacing=0.6, what="本文")

    # ---------------------------------------------------------------- build
    def build(self):
        slides = self.data.get("slides") or []
        offset = 0 if (slides and slides[0].get("type") == "cover") else 1
        for i, sd in enumerate(slides):
            for path, v in _walk(sd):
                if "【要確認】" in v:
                    TODO.append(f"p.{i + 1 + offset}「{sd.get('section') or DEFAULT_SECTIONS.get(sd.get('type'), sd.get('type'))}」{path}: {v[:40]}")
        if not slides or slides[0].get("type") != "cover":
            self.s_cover({"type": "cover"})
        for sd in slides:
            t = sd.get("type")
            fn = getattr(self, f"s_{t}", None)
            if fn is None:
                sys.exit(f"[エラー] 未対応のスライド type です: {t!r}。使えるのは cover, " + ", ".join(DEFAULT_SECTIONS))
            fn(sd)
        return self.prs


def _walk(o, path=""):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk(v, f"{path}[{i}]")


def _looks_numeric(v):
    s = str(v).strip()
    return bool(s) and (s[0].isdigit() or s[0] in "¥￥$+-△▲") and len(s) <= 16


def main():
    ap = argparse.ArgumentParser(description="商品企画書 PPTX ビルダー")
    ap.add_argument("content", help="content.json のパス")
    ap.add_argument("-o", "--output", required=True, help="出力する .pptx のパス")
    args = ap.parse_args()
    with open(args.content, encoding="utf-8") as f:
        data = json.load(f)
    deck = Deck(data)
    prs = deck.build()
    prs.save(args.output)
    print(f"[OK] {args.output} を作成しました（{deck.page} 枚）")
    print(f"     フォント: {deck.font} / ベース #{deck.base} / サブ #{deck.sub} / ポイント #{deck.accent}")
    if TODO:
        print(f"\n[要確認] {len(TODO)} 件 — ユーザーに確認が必要な箇所:")
        for t in TODO:
            print("  - " + t)
    if WARNINGS:
        print(f"\n[警告] {len(WARNINGS)} 件 — 内容を見直してから再生成してください:")
        for w in WARNINGS:
            print("  - " + w)


if __name__ == "__main__":
    main()
