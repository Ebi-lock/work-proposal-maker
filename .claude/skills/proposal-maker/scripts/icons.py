"""シンプルなアイコン（PowerPoint の図形で描くベクターアイコン）

外部の画像ファイルを使わず、円・四角・多角形の組み合わせで描く。
- 単色なので、資料の3色ルールを崩さない（色は呼び出し側が渡す）
- 図形なので拡大しても粗くならず、PowerPoint 上で色や大きさを変えられる
- 1つのアイコンは1つのグループにまとめる（名前は "icon:<名前>"）

座標は 100×100 のマス目で定義する。
  ("o",  x, y, w, h)          円（楕円）
  ("r",  x, y, w, h)          四角
  ("rr", x, y, w, h)          角丸四角
  ("s",  MSO_SHAPE, x, y, w, h) PowerPoint の既定図形
  ("p",  [(x, y), ...])       多角形
  ("l",  [(x, y), ...], 太さ) 太い折れ線（端と角は丸）
  ("ring", x, y, w, h, 太さ)  輪（塗りなしの円）
要素名の末尾に "-" を付けると「くり抜き」（背景色で塗る）になる。例: "o-", "l-"
"""
import math

from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu, Inches, Pt

S = MSO_SHAPE

ICONS = {
    # 人・組織
    "user": [("o", 34, 8, 32, 32), ("s", S.ROUND_2_SAME_RECTANGLE, 18, 46, 64, 44)],
    "users": [("o", 56, 12, 24, 24), ("s", S.ROUND_2_SAME_RECTANGLE, 50, 40, 42, 36),
              ("o+", 20, 18, 30, 30), ("s+", S.ROUND_2_SAME_RECTANGLE, 8, 52, 54, 38)],
    "building": [("r", 18, 10, 42, 82), ("r", 60, 40, 24, 52),
                 ("r-", 26, 20, 9, 9), ("r-", 43, 20, 9, 9), ("r-", 26, 36, 9, 9), ("r-", 43, 36, 9, 9),
                 ("r-", 26, 52, 9, 9), ("r-", 43, 52, 9, 9), ("r-", 66, 50, 12, 8), ("r-", 66, 64, 12, 8),
                 ("r-", 33, 74, 12, 18)],
    "store": [("p", [(8, 32), (18, 10), (82, 10), (92, 32)]), ("r", 16, 38, 68, 52),
              ("r-", 24, 46, 24, 20), ("r-", 56, 52, 18, 38)],
    "award": [("p", [(30, 6), (46, 6), (54, 46), (38, 46)]), ("p", [(54, 6), (70, 6), (62, 46), (46, 46)]),
              ("o+", 24, 38, 52, 52), ("ring-", 34, 48, 32, 32, 5)],
    # 分析・目標
    "chart": [("r", 14, 54, 18, 34), ("r", 41, 36, 18, 52), ("r", 68, 16, 18, 72), ("r", 8, 88, 84, 6)],
    "trend": [("l", [(10, 78), (36, 50), (54, 64), (84, 32)], 9), ("p", [(66, 26), (92, 22), (88, 48)])],
    "target": [("ring", 10, 10, 80, 80, 9), ("ring", 28, 28, 44, 44, 9), ("o", 42, 42, 16, 16)],
    "search": [("ring", 10, 10, 58, 58, 10), ("l", [(62, 62), (88, 88)], 13)],
    "checklist": [("r", 10, 14, 16, 16), ("rr", 34, 18, 56, 8), ("r", 10, 42, 16, 16), ("rr", 34, 46, 56, 8),
                  ("r", 10, 70, 16, 16), ("rr", 34, 74, 40, 8)],
    "check": [("o", 8, 8, 84, 84), ("l-", [(30, 52), (44, 66), (70, 38)], 10)],
    "idea": [("o", 22, 6, 56, 56), ("r", 36, 52, 28, 18), ("rr", 36, 74, 28, 7), ("rr", 40, 85, 20, 7)],
    "flag": [("r", 16, 6, 8, 88), ("p", [(24, 10), (84, 10), (70, 31), (84, 52), (24, 52)])],
    # お金・時間・計画
    "yen": [("o", 8, 8, 84, 84), ("l-", [(34, 26), (50, 48), (66, 26)], 8), ("r-", 46, 46, 8, 32),
            ("r-", 32, 52, 36, 6), ("r-", 32, 63, 36, 6)],
    "clock": [("ring", 10, 10, 80, 80, 9), ("rr", 46, 24, 8, 30), ("rr", 46, 46, 24, 8)],
    "calendar": [("rr", 10, 16, 80, 74), ("r-", 18, 38, 64, 44), ("rr", 26, 6, 9, 20), ("rr", 65, 6, 9, 20),
                 ("r", 26, 46, 12, 10), ("r", 44, 46, 12, 10), ("r", 62, 46, 12, 10),
                 ("r", 26, 63, 12, 10), ("r", 44, 63, 12, 10)],
    "document": [("p", [(18, 6), (60, 6), (82, 28), (82, 94), (18, 94)]), ("p-", [(60, 6), (60, 28), (82, 28)]),
                 ("r-", 30, 42, 40, 6), ("r-", 30, 56, 40, 6), ("r-", 30, 70, 26, 6)],
    "package": [("r", 10, 16, 80, 18), ("r", 16, 38, 68, 52), ("r-", 42, 16, 16, 30), ("rr-", 36, 50, 28, 7)],
    # 状態・注意
    "warning": [("s", S.ISOSCELES_TRIANGLE, 6, 10, 88, 80), ("rr-", 45, 36, 10, 28), ("o-", 44.5, 70, 11, 11)],
    "shield": [("p", [(50, 6), (86, 18), (84, 50), (50, 94), (16, 50), (14, 18)]),
               ("l-", [(34, 50), (46, 62), (66, 40)], 8)],
    "lock": [("ring", 28, 8, 44, 56, 9), ("rr", 16, 42, 68, 50), ("o-", 43, 56, 14, 14), ("r-", 47, 64, 6, 16)],
    "up": [("s", S.UP_ARROW, 22, 6, 56, 88)],
    "down": [("s", S.DOWN_ARROW, 22, 6, 56, 88)],
    "star": [("s", S.STAR_5_POINT, 6, 8, 88, 84)],
    "heart": [("s", S.HEART, 8, 12, 84, 78)],
    "bolt": [("s", S.LIGHTNING_BOLT, 16, 4, 68, 92)],
    # 仕組み・手段
    "gear": [("s", S.GEAR_6, 8, 8, 84, 84), ("o-", 36, 36, 28, 28)],
    "cloud": [("s", S.CLOUD, 4, 18, 92, 64)],
    "globe": [("ring", 10, 10, 80, 80, 7), ("ring", 33, 10, 34, 80, 6), ("r", 10, 47, 80, 6), ("r", 47, 10, 6, 80)],
    "phone": [("rr", 26, 4, 48, 92), ("r-", 33, 14, 34, 64), ("o-", 44, 82, 12, 9)],
    "mail": [("rr", 6, 20, 88, 60), ("l-", [(14, 30), (50, 56), (86, 30)], 6)],
    "chat": [("rr", 6, 10, 80, 56), ("p", [(18, 60), (40, 60), (16, 86)]),
             ("o-", 22, 32, 11, 11), ("o-", 41, 32, 11, 11), ("o-", 60, 32, 11, 11)],
    "cart": [("l", [(6, 16), (20, 16), (30, 62)], 7), ("p", [(24, 28), (92, 28), (84, 62), (30, 62)]),
             ("o", 28, 72, 16, 16), ("o", 66, 72, 16, 16)],
    "truck": [("r", 4, 22, 56, 48), ("p", [(62, 36), (82, 36), (96, 54), (96, 70), (62, 70)]),
              ("p-", [(68, 43), (79, 43), (88, 54), (68, 54)]), ("o+", 12, 60, 22, 22), ("o+", 66, 60, 22, 22)],
    "leaf": [("p", [(14, 86), (12, 52), (24, 28), (50, 14), (88, 10), (84, 48), (70, 72), (46, 86)]),
             ("l-", [(24, 76), (66, 34)], 5)],
    "picture": [("rr", 6, 14, 88, 72), ("r-", 14, 22, 72, 56), ("p", [(18, 74), (40, 44), (54, 62), (66, 50), (82, 74)]),
                ("o", 62, 28, 12, 12)],
}

ALIASES = {
    "person": "user", "customer": "user", "persona": "user", "team": "users", "people": "users",
    "company": "building", "office": "building", "shop": "store", "medal": "award", "achievement": "award",
    "graph": "chart", "data": "chart", "growth": "trend", "goal": "target", "analysis": "search",
    "list": "checklist", "task": "checklist", "ok": "check", "bulb": "idea", "money": "yen", "cost": "yen",
    "price": "yen", "time": "clock", "schedule": "calendar", "plan": "document", "doc": "document",
    "product": "package", "box": "package", "risk": "warning", "alert": "warning", "security": "shield",
    "safe": "shield", "setting": "gear", "system": "gear", "global": "globe", "mobile": "phone",
    "smartphone": "phone", "email": "mail", "message": "chat", "voice": "chat", "delivery": "truck",
    "logistics": "truck", "eco": "leaf", "image": "picture", "photo": "picture", "speed": "bolt",
    "competitor": "flag",
}


def resolve(name):
    """アイコン名を正規化する。見つからなければ None"""
    if not name:
        return None
    n = str(name).strip().lower()
    n = ALIASES.get(n, n)
    return n if n in ICONS else None


def names():
    return sorted(ICONS)


def _rgb(h):
    return RGBColor.from_string(h)


def _plain(shp, fill, line=None, line_pt=0.0):
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = _rgb(fill)
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = _rgb(line)
        shp.line.width = Pt(line_pt)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    return shp


def _poly(shapes, pts, fill):
    fb = shapes.build_freeform(pts[0][0], pts[0][1], scale=1.0)
    fb.add_line_segments(pts[1:], close=True)
    shp = fb.convert_to_shape()
    return _plain(shp, fill)


def draw(shapes, name, x, y, d, color, hole, badge=None):
    """(x, y) を左上とする一辺 d インチの正方形にアイコンを描く。

    color: 絵の色 / hole: くり抜き部分の色（＝下地の色） / badge: 円形の下地の色（None なら下地なし）
    戻り値: グループ図形。名前が不明なら None
    """
    key = resolve(name)
    if key is None:
        return None
    grp = shapes.add_group_shape()
    grp.name = f"icon:{key}"
    gs = grp.shapes
    if badge:
        _plain(gs.add_shape(S.OVAL, Inches(x), Inches(y), Inches(d), Inches(d)), badge)
        hole = badge
        inset = d * 0.22
        x, y, d = x + inset, y + inset, d - inset * 2
    u = d / 100.0  # 1マスあたりのインチ

    def X(v):
        return Inches(x + v * u)

    def Y(v):
        return Inches(y + v * u)

    def L(v):
        return Inches(v * u)

    sep_pt = d * 72 * 0.045  # 重なる図形の境目に入れるすき間

    for el in ICONS[key]:
        kind = el[0]
        cut = kind.endswith("-")
        sep = kind.endswith("+")
        kind = kind.rstrip("-+")
        fill = hole if cut else color
        if kind in ("o", "r", "rr", "s"):
            if kind == "s":
                shape_type, (ex, ey, ew, eh) = el[1], el[2:6]
            else:
                shape_type = {"o": S.OVAL, "r": S.RECTANGLE, "rr": S.ROUNDED_RECTANGLE}[kind]
                ex, ey, ew, eh = el[1:5]
            shp = gs.add_shape(shape_type, X(ex), Y(ey), L(ew), L(eh))
            if shape_type == S.ROUNDED_RECTANGLE:
                shp.adjustments[0] = 0.25
            if shape_type == S.ROUND_2_SAME_RECTANGLE:
                shp.adjustments[0] = 0.5
            _plain(shp, fill, line=hole if sep else None, line_pt=sep_pt)
        elif kind == "ring":
            ex, ey, ew, eh, wt = el[1:6]
            shp = gs.add_shape(S.OVAL, X(ex + wt / 2), Y(ey + wt / 2), L(ew - wt), L(eh - wt))
            _plain(shp, None, line=fill, line_pt=wt * u * 72)
        elif kind == "p":
            _poly(gs, [(X(px), Y(py)) for px, py in el[1]], fill)
        elif kind == "l":
            pts, wt = el[1], el[2]
            r = wt / 2
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                dx, dy = x2 - x1, y2 - y1
                ln = math.hypot(dx, dy) or 1
                nx, ny = -dy / ln * r, dx / ln * r
                quad = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
                _poly(gs, [(X(px), Y(py)) for px, py in quad], fill)
            for px, py in pts:
                _plain(gs.add_shape(S.OVAL, X(px - r), Y(py - r), L(wt), L(wt)), fill)
    return grp
