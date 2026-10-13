# -*- coding: utf-8 -*-
"""生成外观设计示例稿件所需的七幅视图。

示例稿件的定位是「可直接跑」：`examples/design-example.md` 在 frontmatter
里引用了 ``images/主视图.png`` 等路径，若这些文件不存在，生成申请文件时
只会在图位留一行「（图1缺失：…）」。缺的不是排版，是外观设计的保护范围
本身——外观设计以图片为准。

视图按常规外观设计制图习惯绘制：白底黑线、无彩色、正投影轮廓。
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parent / "images"
W = H = 1400
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LW = 4


def _canvas():
    img = Image.new("RGB", (W, H), WHITE)
    return img, ImageDraw.Draw(img)


def _body(d, left=400, right=1000, top=200, bottom=1150, taper=60):
    """杯身正投影轮廓：上宽下略窄，杯口为扁椭圆。"""
    d.polygon(
        [(left, top), (right, top), (right - taper, bottom), (left + taper, bottom)],
        outline=BLACK,
        fill=WHITE,
        width=LW,
    )
    d.arc((left, top - 44, right, top + 44), start=180, end=360, fill=BLACK, width=LW)
    d.line((left, top, right - taper, bottom), fill=WHITE, width=0)


def _handle(d, x=980, y0=330, y1=900, reach=270):
    """右侧 C 形把手。"""
    d.arc((x - 40, y0, x - 40 + reach, y1), start=-85, end=85, fill=BLACK, width=LW)


def front():
    img, d = _canvas()
    _body(d)
    _handle(d)
    return img


def back():
    img, d = _canvas()
    _body(d)
    return img


def side(flip=False):
    """侧视图：杯身收窄为长方形，把手在投影上偏向一侧。"""
    img, d = _canvas()
    left, right = (560, 880)
    d.polygon(
        [(left, 200), (right, 200), (right - 20, 1150), (left + 20, 1150)],
        outline=BLACK,
        fill=WHITE,
        width=LW,
    )
    d.arc((left, 156, right, 244), start=180, end=360, fill=BLACK, width=LW)
    x = right if not flip else left
    span = 250 if not flip else -250
    d.arc(
        (min(x, x + span), 340, max(x, x + span), 900),
        start=-85 if not flip else 95,
        end=85 if not flip else 265,
        fill=BLACK,
        width=LW,
    )
    return img


def top():
    """俯视图：外圆为杯口，内圆为杯底。"""
    img, d = _canvas()
    d.ellipse((380, 380, 1020, 1020), outline=BLACK, fill=WHITE, width=LW)
    d.ellipse((470, 470, 930, 930), outline=BLACK, fill=WHITE, width=LW)
    return img


def bottom():
    img, d = _canvas()
    d.ellipse((470, 470, 930, 930), outline=BLACK, fill=WHITE, width=LW)
    return img


def isometric():
    """立体图：顶面椭圆 + 侧壁 + 把手，作为最能表明设计要点的视图。"""
    img, d = _canvas()
    left, right, top_y = 400, 1000, 330
    d.arc((left, top_y - 90, right, top_y + 90), start=180, end=360, fill=BLACK, width=LW)
    d.line((left, top_y, left, 1100), fill=BLACK, width=LW)
    d.line((right, top_y, right, 1100), fill=BLACK, width=LW)
    d.arc((left, 1010, right, 1190), start=0, end=180, fill=BLACK, width=LW)
    d.line((right, top_y, right, 1100), fill=BLACK, width=LW)
    cx = (left + right) / 2
    d.arc((left, top_y - 90, right, top_y + 90), start=0, end=180, fill=BLACK, width=2)
    d.line((cx, top_y - 90, cx, top_y - 88), fill=BLACK, width=1)
    _ = math
    _handle(d, x=1000, y0=460, y1=980, reach=230)
    return img


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jobs = {
        "主视图.png": front,
        "后视图.png": back,
        "左视图.png": lambda: side(False),
        "右视图.png": lambda: side(True),
        "俯视图.png": top,
        "仰视图.png": bottom,
        "立体图.png": isometric,
    }
    for name, fn in jobs.items():
        p = OUT_DIR / name
        fn().save(p, dpi=(300, 300))
        print(f"{p.name}")


if __name__ == "__main__":
    main()
