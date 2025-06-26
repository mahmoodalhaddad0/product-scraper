"""
سكربت مستقل لموقع coachoutlet.com:
  • يلتقط أوضح الصور (≥10 KB).
  • يرسل 3 – 10 صور إلى تليجرام.
شغّله بــ:  python coach_scraper.py
وأرسل طلب POST إلى /scrape كما تفعل في السكربت العام.
"""

from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)
TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

# ---------- فلترة الصور ----------
def get_size(url):
    try:
        r = requests.head(url, timeout=5)
        return int(r.headers.get("Content-Length", 0))
    except:
        return 0

def filter_images(urls, min_size=10_000, min_count=3, max_count=10):
    pairs = [(u, get_size(u)) for u in urls]
    pairs = [p for p in pairs if p[1] >= min_size]
    pairs.sort(key=lambda x: x[1], reverse=True)
    sel = [u for u, _ in pairs[:max_count]]
    print(f"✅ After filter: {len(sel)} images")
    return sel if len(sel) >= min_count else []

# ---------- استخراج صور Coach ----------
def extract_coach(url):
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).content
    soup = BeautifulSoup(html, "html.parser")
    raw = []
    for img in soup.find_all("img"):
        srcset = img.get("srcset") or img.get("src")
        if not srcset:
            continue
        # إذا srcset موجود نأخذ كل روابط .jpg فيه
        if "srcset" in img.attrs:
            parts = [s.strip().split(" ")[0] for s in srcset.split(",") if ".jpg" in s]
            raw.extend([p for p in parts if p.startswith("http")])
        elif srcset.startswith("http") and ".jpg" in srcset:
            raw.append(srcset)
    print("🔍 Raw Coach images:", len(raw))
    return filter_images(raw)

# ---------- إرسال الصور لتليجرام ----------
def send_to_telegram(chat_id, urls):
    if len(urls) < 3:
        print("⚠️ أقل من 3 صور مناسبة – لم يرسل شيء.")
        return
    media = [{"type": "photo", "media": u, "caption": ""} for u in urls]
    media[0]["caption"] = "🖼️ Coach Product"
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup",
                  json={"chat_id": chat_id, "media": media})

# ---------- مسار الـ API ----------
@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.json or {}
    url, chat = data.get("url"), data.get("chat_id")
    if not url or not chat:
        return jsonify({"error": "url or chat_id missing"}), 400
    if "coachoutlet.com" not in url:
        return jsonify({"error": "only coachoutlet.com supported"}), 400

    imgs = extract_coach(url)
    send_to_telegram(chat, imgs)
    return jsonify({"sent": len(imgs)})

# ---------- تشغيل خادم Flask ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10010))  # منفذ مختلف عن السكربت العام
    print(f"Running Coach scraper on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)
