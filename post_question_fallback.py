#!/usr/bin/env python3
"""
Fallback question poster — uses codecogs to render LaTeX and posts to Telegram
when PIL/matplotlib are not available in the execution environment.
"""

import os
import sys
import json
import urllib.parse
import requests

TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def codecogs_url(latex: str) -> str:
    encoded = urllib.parse.quote(r"\dpi{180}\bg{white}\large " + latex)
    return "https://latex.codecogs.com/png.image?" + encoded

def fetch_image(latex: str) -> bytes:
    url = codecogs_url(latex)
    r = requests.get(url, timeout=40)
    r.raise_for_status()
    return r.content

def build_caption(data: dict) -> str:
    labels = ["A", "B", "C", "D"]
    opts   = data["options"]
    opt_lines = "\n".join(
        f"({labels[i]})  {opts[i]}" for i in range(len(opts))
    )
    eq_note = f"\n<i>{data['equation_note']}</i>" if data.get("equation_note") else ""
    return (
        "\U0001F4CA <b>StatChakravyuh Daily Practice</b>\n"
        "<i>Practice • Improve • Repeat</i>\n\n"
        f"\U0001F4C5 {data['date']}\n"
        f"\U0001F4DA Topic: {data['topic']}    "
        f"\U0001F3AF Difficulty: {data['difficulty']}\n\n"
        "❓ <b>Question</b>\n"
        f"{data['question']}{eq_note}\n\n"
        f"<b>Options</b>\n{opt_lines}\n\n"
        "⏱ Suggested time: 3 min\n"
        "\U0001F4AC Post your answer below\n"
        "✅ Solution at 9 PM\n\n"
        "\U0001F310 statchakravyuh.com\n"
        "#StatChakravyuh #DailyPractice #Statistics"
    )

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "question.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # render the main equation via codecogs
    eq_image = fetch_image(data["equation"])
    img_path = "question_eq.png"
    with open(img_path, "wb") as out:
        out.write(eq_image)

    caption = build_caption(data)
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(img_path, "rb") as photo:
        r = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"},
            files={"photo": photo},
            timeout=60,
        )
    print("Telegram response:", r.status_code, r.text[:300])
    r.raise_for_status()

if __name__ == "__main__":
    main()
