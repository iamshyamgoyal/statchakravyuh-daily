import os, json, urllib.parse, requests
 
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
 
with open("solution.json", encoding="utf-8") as f:
    s = json.load(f)
 
latex = r"\dpi{200}\bg{white}\large " + s["key_result_latex"]
img_url = "https://latex.codecogs.com/png.image?" + urllib.parse.quote(latex)
img = requests.get(img_url, timeout=40)
img.raise_for_status()
with open("result.png", "wb") as out:
    out.write(img.content)
 
caption = (
    "\u2705 <b>StatChakravyuh Solution</b>\n"
    "<i>Practice . Improve . Repeat</i>\n\n"
    f"\U0001F4DA Topic: {s['topic']}\n\n"
    f"<b>Correct answer: {s['correct_option']}</b>\n\n"
    f"<b>Explanation</b>\n{s['explanation']}\n\n"
    "<b>Key result to remember</b> (shown above)\n\n"
    f"\U0001F4A1 {s['exam_tip']}\n\n"
    "\U0001F310 statchakravyuh.com\n"
    "#StatChakravyuh #Solution #Statistics"
)
 
url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
with open("result.png", "rb") as photo:
    r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption,
                                 "parse_mode": "HTML"},
                      files={"photo": photo}, timeout=40)
print("Telegram response:", r.status_code, r.text)
r.raise_for_status()
