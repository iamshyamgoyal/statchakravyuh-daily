import os, json, urllib.parse, requests
 
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
 
with open("today.json", encoding="utf-8") as f:
    q = json.load(f)
 
# 1. Build a clean equation image from the LaTeX string
latex = r"\dpi{200}\bg{white}\large " + q["equation_latex"]
img_url = "https://latex.codecogs.com/png.image?" + urllib.parse.quote(latex)
img = requests.get(img_url, timeout=40)
img.raise_for_status()
with open("equation.png", "wb") as out:
    out.write(img.content)
 
# 2. Build the branded caption
o = q["options"]
caption = (
    "\U0001F4CA <b>StatChakravyuh Daily Practice</b>\n"
    "<i>Practice . Improve . Repeat</i>\n\n"
    f"\U0001F4C5 {q['date']}\n"
    f"\U0001F4DA Topic: {q['topic']}\n"
    f"\U0001F3AF {q['exams']}\n\n"
    f"\u2753 <b>Question</b>\n{q['question_text']}\n\n"
    "(The key statistic is shown in the image above.)\n\n"
    f"(A) {o['A']}\n(B) {o['B']}\n(C) {o['C']}\n(D) {o['D']}\n\n"
    f"\u23F1 Suggested time: {q['time']}\n"
    f"\U0001F522 Difficulty: {q['difficulty']}\n"
    "\U0001F4AC Post your answer in the comments\n"
    "\u2705 Solution will be posted in the evening\n\n"
    "\U0001F310 www.statchakravyuh.com\n"
    "#StatChakravyuh #DailyPractice #Statistics"
)
 
# 3. Send the equation image with the caption
url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
with open("equation.png", "rb") as photo:
    r = requests.post(url, data={"chat_id": CHAT_ID, "caption": caption,
                                 "parse_mode": "HTML"},
                      files={"photo": photo}, timeout=40)
print("Telegram response:", r.status_code, r.text)
r.raise_for_status()
