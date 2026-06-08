#!/usr/bin/env python3
"""
StatChakravyuh daily practice card generator and Telegram poster.

This script reads a question definition from a JSON file, renders a branded
card image (with mathematical equations drawn cleanly using matplotlib), and
sends that image to a Telegram channel using the Telegram Bot API.

It supports two card types:
    question  -> the morning practice problem card
    solution  -> the evening solution card with explanation

Usage:
    python statchakravyuh_card.py question.json
    python statchakravyuh_card.py solution.json

Required environment variables:
    TELEGRAM_BOT_TOKEN   The token you received from BotFather
    TELEGRAM_CHAT_ID     The id of your channel or group
"""

import os
import sys
import json
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Brand configuration
# ----------------------------------------------------------------------
NAVY        = (12, 42, 94)
AMBER       = (232, 160, 32)
GREEN       = (39, 160, 74)
WHITE       = (255, 255, 255)
PALE_BLUE   = (238, 242, 255)
BORDER_BLUE = (212, 222, 239)
SOFT_BLUE   = (246, 248, 255)
TEXT_DARK   = (26, 26, 46)
TEXT_MUTE   = (92, 122, 170)
CREAM       = (254, 249, 237)
CREAM_TEXT  = (154, 107, 0)
GREEN_BG    = (234, 246, 237)
GREEN_TEXT  = (26, 122, 53)

CARD_W = 1080
SIDE   = 60

HERE     = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")


# ----------------------------------------------------------------------
# Font loading
# ----------------------------------------------------------------------
def sans(size, weight="Medium"):
    """Load the Outfit variable font at a given weight."""
    path = os.path.join(FONT_DIR, "Outfit.ttf")
    try:
        f = ImageFont.truetype(path, size)
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
        return f
    except Exception:
        return ImageFont.load_default()


def serif(size):
    """Load a serif font for the question body text."""
    for candidate in [
        os.path.join(FONT_DIR, "LibreBaskerville-Regular.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ]:
        if os.path.exists(candidate):
            try:
                return ImageFont.truetype(candidate, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ----------------------------------------------------------------------
# Equation rendering using matplotlib mathtext (no LaTeX install needed)
# ----------------------------------------------------------------------
def render_equation(latex, target_px_height, color=(26, 42, 64)):
    """Render a LaTeX-style string to a transparent PNG and return a PIL image."""
    hex_color = "#%02x%02x%02x" % color
    fig = plt.figure(figsize=(10, 2))
    fig.patch.set_alpha(0.0)
    fig.text(0.5, 0.5, f"${latex}$", fontsize=42, ha="center",
             va="center", color=hex_color)
    tmp = os.path.join(HERE, "_eq_tmp.png")
    fig.savefig(tmp, dpi=220, transparent=True, bbox_inches="tight",
                pad_inches=0.06)
    plt.close(fig)
    img = Image.open(tmp).convert("RGBA")
    ratio = target_px_height / img.height
    new_w = int(img.width * ratio)
    img = img.resize((new_w, target_px_height), Image.LANCZOS)
    os.remove(tmp)
    return img


# ----------------------------------------------------------------------
# Text helpers
# ----------------------------------------------------------------------
def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rounded(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill,
                           outline=outline, width=width)


# ----------------------------------------------------------------------
# Shared header and footer
# ----------------------------------------------------------------------
def draw_header(draw, card, y, badge_text, badge_color):
    draw.rectangle([0, y, CARD_W, y + 6], fill=AMBER)
    y += 6
    head_h = 118
    draw.rectangle([0, y, CARD_W, y + head_h], fill=NAVY)

    logo = 72
    lx, ly = SIDE, y + (head_h - logo) // 2
    rounded(draw, [lx, ly, lx + logo, ly + logo], 16, fill=AMBER)
    f_logo = sans(30, "SemiBold")
    tw = draw.textlength("SC", font=f_logo)
    draw.text((lx + (logo - tw) / 2, ly + 16), "SC", font=f_logo, fill=WHITE)

    tx = lx + logo + 22
    draw.text((tx, y + 30), "StatChakravyuh", font=sans(34, "SemiBold"), fill=WHITE)
    draw.text((tx, y + 74), "PRACTICE  .  IMPROVE  .  REPEAT",
              font=sans(17, "Regular"), fill=(150, 165, 200))

    f_badge = sans(20, "Medium")
    bw = draw.textlength(badge_text, font=f_badge)
    bx2 = CARD_W - SIDE
    bx1 = bx2 - bw - 44
    by1 = y + (head_h - 46) // 2
    rounded(draw, [bx1, by1, bx2, by1 + 46], 23, outline=badge_color, width=2)
    draw.text((bx1 + 22, by1 + 11), badge_text, font=f_badge, fill=badge_color)
    return y + head_h


def draw_meta(draw, y, topic, difficulty, date_text):
    h = 60
    draw.rectangle([0, y, CARD_W, y + h], fill=PALE_BLUE)
    draw.line([0, y + h, CARD_W, y + h], fill=BORDER_BLUE, width=1)
    f = sans(19, "Medium")

    tw = draw.textlength(topic, font=f)
    rounded(draw, [SIDE, y + 14, SIDE + tw + 36, y + 46], 16, fill=NAVY)
    draw.text((SIDE + 18, y + 20), topic, font=f, fill=WHITE)

    dx = SIDE + tw + 36 + 12
    dw = draw.textlength(difficulty, font=f)
    rounded(draw, [dx, y + 14, dx + dw + 36, y + 46], 16,
            fill=CREAM, outline=(252, 222, 160), width=1)
    draw.text((dx + 18, y + 20), difficulty, font=f, fill=CREAM_TEXT)

    f2 = sans(18, "Regular")
    dtw = draw.textlength(date_text, font=f2)
    draw.text((CARD_W - SIDE - dtw, y + 20), date_text, font=f2, fill=TEXT_MUTE)
    return y + h + 1


def draw_footer(draw, y):
    h = 64
    draw.rectangle([0, y, CARD_W, y + h], fill=NAVY)
    f = sans(17, "Regular")
    draw.text((SIDE, y + 23),
              "UPSC ISS  .  UGC NET  .  IIT JAM  .  GATE Statistics",
              font=f, fill=(150, 165, 200))
    site = "statchakravyuh.com"
    sw = draw.textlength(site, font=sans(18, "Medium"))
    draw.text((CARD_W - SIDE - sw, y + 22), site,
              font=sans(18, "Medium"), fill=AMBER)
    return y + h


# ----------------------------------------------------------------------
# Question card
# ----------------------------------------------------------------------
def build_question_card(data):
    base = Image.new("RGB", (CARD_W, 2000), WHITE)
    draw = ImageDraw.Draw(base)
    y = 0
    y = draw_header(draw, base, y, "Daily Practice", AMBER)
    y = draw_meta(draw, y, data["topic"], data.get("difficulty", "Medium"),
                  data["date"])
    y += 36

    draw.rectangle([SIDE, y + 2, SIDE + 6, y + 30], fill=AMBER)
    draw.text((SIDE + 20, y), "QUESTION", font=sans(18, "SemiBold"), fill=AMBER)
    y += 50

    f_q = serif(27)
    for line in wrap_text(draw, data["question"], f_q, CARD_W - 2 * SIDE):
        draw.text((SIDE, y), line, font=f_q, fill=TEXT_DARK)
        y += 42
    y += 14

    if data.get("equation"):
        eq = render_equation(data["equation"], 78)
        box_h = eq.height + 56
        rounded(draw, [SIDE, y, CARD_W - SIDE, y + box_h], 14,
                fill=SOFT_BLUE, outline=BORDER_BLUE, width=1)
        base.paste(eq, ((CARD_W - eq.width) // 2, y + 28), eq)
        if data.get("equation_note"):
            note = data["equation_note"]
            fn = sans(17, "Regular")
            nw = draw.textlength(note, font=fn)
            draw.text(((CARD_W - nw) / 2, y + box_h - 4), note, font=fn,
                      fill=TEXT_MUTE)
            box_h += 22
        y += box_h + 30

    labels = ["A", "B", "C", "D"]
    opts = data["options"]
    col_w = (CARD_W - 2 * SIDE - 20) // 2
    row_h = 92
    for i, opt in enumerate(opts):
        col = i % 2
        row = i // 2
        ox = SIDE + col * (col_w + 20)
        oy = y + row * (row_h + 16)
        rounded(draw, [ox, oy, ox + col_w, oy + row_h], 12,
                fill=(248, 249, 252), outline=BORDER_BLUE, width=1)
        cd = 34
        rounded(draw, [ox + 18, oy + (row_h - cd) // 2,
                       ox + 18 + cd, oy + (row_h - cd) // 2 + cd], cd // 2,
                fill=NAVY)
        lw = draw.textlength(labels[i], font=sans(19, "SemiBold"))
        draw.text((ox + 18 + (cd - lw) / 2, oy + (row_h - cd) // 2 + 6),
                  labels[i], font=sans(19, "SemiBold"), fill=WHITE)
        eq = render_equation(opt, 44)
        max_eq_w = col_w - 90
        if eq.width > max_eq_w:
            r = max_eq_w / eq.width
            eq = eq.resize((max_eq_w, int(eq.height * r)), Image.LANCZOS)
        base.paste(eq, (ox + 70, oy + (row_h - eq.height) // 2), eq)
    y += 2 * row_h + 16 + 30

    h = 56
    draw.rectangle([0, y, CARD_W, y + h], fill=CREAM)
    draw.line([0, y, CARD_W, y], fill=(252, 222, 160), width=1)
    draw.line([0, y + h, CARD_W, y + h], fill=(252, 222, 160), width=1)
    info = "Suggested time 3 min   |   Post your answer below   |   Solution at 9 PM"
    draw.text((SIDE, y + 17), info, font=sans(18, "Regular"), fill=CREAM_TEXT)
    y += h

    y = draw_footer(draw, y)
    return base.crop((0, 0, CARD_W, y))


# ----------------------------------------------------------------------
# Solution card
# ----------------------------------------------------------------------
def build_solution_card(data):
    base = Image.new("RGB", (CARD_W, 2600), WHITE)
    draw = ImageDraw.Draw(base)
    y = 0
    y = draw_header(draw, base, y, "Solution", GREEN)
    y = draw_meta(draw, y, data["topic"], data.get("difficulty", "Medium"),
                  data["date"] + "  .  9 PM")
    y += 0

    ah = 110
    draw.rectangle([0, y, CARD_W, y + ah], fill=GREEN_BG)
    draw.line([0, y + ah, CARD_W, y + ah], fill=(168, 217, 181), width=1)
    draw.rectangle([SIDE, y + 22, SIDE + 6, y + 48], fill=GREEN)
    draw.text((SIDE + 20, y + 20), "CORRECT ANSWER",
              font=sans(17, "SemiBold"), fill=GREEN_TEXT)
    cd = 44
    rounded(draw, [SIDE, y + 54, SIDE + cd, y + 54 + cd], cd // 2, fill=GREEN)
    al = data["correct_label"]
    aw = draw.textlength(al, font=sans(22, "SemiBold"))
    draw.text((SIDE + (cd - aw) / 2, y + 62), al, font=sans(22, "SemiBold"),
              fill=WHITE)
    eq = render_equation(data["correct_answer"], 50)
    base.paste(eq, (SIDE + cd + 20, y + 54 + (cd - eq.height) // 2), eq)
    y += ah + 32

    draw.rectangle([SIDE, y + 2, SIDE + 6, y + 30], fill=AMBER)
    draw.text((SIDE + 20, y), "STEP BY STEP EXPLANATION",
              font=sans(18, "SemiBold"), fill=AMBER)
    y += 54

    for idx, step in enumerate(data["steps"], start=1):
        cd = 38
        rounded(draw, [SIDE, y, SIDE + cd, y + cd], cd // 2,
                fill=PALE_BLUE, outline=BORDER_BLUE, width=1)
        nw = draw.textlength(str(idx), font=sans(19, "SemiBold"))
        draw.text((SIDE + (cd - nw) / 2, y + 8), str(idx),
                  font=sans(19, "SemiBold"), fill=NAVY)
        tx = SIDE + cd + 22
        draw.text((tx, y + 2), step["title"], font=sans(20, "SemiBold"),
                  fill=NAVY)
        yy = y + 40
        f_b = serif(23)
        for line in wrap_text(draw, step["text"], f_b, CARD_W - tx - SIDE):
            draw.text((tx, yy), line, font=f_b, fill=(42, 42, 64))
            yy += 36
        if step.get("equation"):
            eq = render_equation(step["equation"], 64)
            box_h = eq.height + 36
            rounded(draw, [tx, yy + 6, CARD_W - SIDE, yy + 6 + box_h], 10,
                    fill=SOFT_BLUE, outline=BORDER_BLUE, width=1)
            paste_x = tx + ((CARD_W - SIDE - tx) - eq.width) // 2
            base.paste(eq, (max(tx + 10, paste_x), yy + 6 + 18), eq)
            yy += box_h + 16
        y = yy + 24

    kb_pad = 28
    f_k = sans(18, "Regular")
    key_lines = wrap_text(draw, data["key_note"], f_k, CARD_W - 2 * SIDE - 2 * kb_pad)
    keq = render_equation(data["key_result"], 64)
    kb_h = 50 + keq.height + 18 + len(key_lines) * 28 + kb_pad
    rounded(draw, [SIDE, y, CARD_W - SIDE, y + kb_h], 14,
            fill=(240, 244, 255), outline=(184, 200, 240), width=1)
    draw.text((SIDE + kb_pad, y + 20), "KEY RESULT",
              font=sans(17, "SemiBold"), fill=NAVY)
    base.paste(keq, ((CARD_W - keq.width) // 2, y + 52), keq)
    ky = y + 52 + keq.height + 14
    for line in key_lines:
        draw.text((SIDE + kb_pad, ky), line, font=f_k, fill=(74, 95, 138))
        ky += 28
    y += kb_h + 28

    th = 60
    draw.rectangle([0, y, CARD_W, y + th], fill=CREAM)
    draw.line([0, y, CARD_W, y], fill=(252, 222, 160), width=1)
    draw.line([0, y + th, CARD_W, y + th], fill=(252, 222, 160), width=1)
    tip = data.get("exam_tip", "")
    for line in wrap_text(draw, "Exam tip: " + tip, sans(17, "Regular"),
                          CARD_W - 2 * SIDE)[:1]:
        draw.text((SIDE, y + 19), line, font=sans(17, "Regular"),
                  fill=CREAM_TEXT)
    y += th

    y = draw_footer(draw, y)
    return base.crop((0, 0, CARD_W, y))


# ----------------------------------------------------------------------
# Telegram sending
# ----------------------------------------------------------------------
def send_to_telegram(image_path, caption):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram credentials not set. Skipping send. Image saved at",
              image_path)
        return
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(image_path, "rb") as photo:
        r = requests.post(url, data={"chat_id": chat_id, "caption": caption,
                                     "parse_mode": "HTML"},
                          files={"photo": photo}, timeout=60)
    if r.status_code == 200:
        print("Posted to Telegram successfully.")
    else:
        print("Telegram error:", r.status_code, r.text)


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: python statchakravyuh_card.py <data.json>")
        sys.exit(1)
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)

    kind = data.get("type", "question")
    if kind == "solution":
        card = build_solution_card(data)
        out = os.path.join(HERE, "solution_card.png")
        caption = data.get("caption", "Today's solution is here. "
                                       "Practice. Improve. Repeat.")
    else:
        card = build_question_card(data)
        out = os.path.join(HERE, "question_card.png")
        caption = data.get("caption", "Today's practice problem is live. "
                                       "Post your answer below.")
    card.save(out, "PNG")
    print("Saved card:", out, card.size)
    send_to_telegram(out, caption)


if __name__ == "__main__":
    main()
