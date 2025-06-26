from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)
TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

# --- استخراج الصور العامة ---
def get_image_size(url):
    try:
        r = requests.head(url, timeout=5)
        return int(r.headers.get("Content-Length", 0))
    except:
        return 0

def filter_largest_images(image_urls, min_count=3, max_count=10, min_size_kb=20):
    images_with_sizes = [(url, get_image_size(url)) for url in image_urls]
    images_with_sizes = [item for item in images_with_sizes if item[1] >= min_size_kb * 1024]
    images_with_sizes.sort(key=lambda x: x[1], reverse=True)
    selected = [url for url, _ in images_with_sizes[:max_count]]
    return selected if len(selected) >= min_count else []

# --- تشارلز أند كيث و وردو و 6pm ---
def extract_standard_images(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")

    image_urls = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and src.startswith("http") and "product" in src:
            image_urls.append(src)
    return filter_largest_images(image_urls)

# --- Coach Outlet ---
def extract_coach_images(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")

    image_urls = []
    for img in soup.find_all("img"):
        srcset = img.get("srcset")
        if srcset:
            candidates = [s.split(" ")[0] for s in srcset.split(",") if ".jpg" in s]
            image_urls.extend([c for c in candidates if c.startswith("http")])
    return filter_largest_images(image_urls)

# --- إرسال الصور إلى تيليجرام ---
def send_images_to_telegram(chat_id, image_urls):
    if not image_urls:
        print("⚠️ لا توجد صور مناسبة")
        return
    media = [{"type": "photo", "media": url, "caption": ""} for url in image_urls]
    media[0]["caption"] = "🖼️ Product Images"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup",
        json={"chat_id": chat_id, "media": media}
    )

# --- API Endpoint ---
@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.json.get("url")
    chat_id = request.json.get("chat_id")
    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    # تحديد الموقع
    if any(site in url for site in ["charleskeith.com", "wardow.com", "6pm.com"]):
        image_urls = extract_standard_images(url)
    elif "coachoutlet.com" in url:
        image_urls = extract_coach_images(url)
    else:
        return jsonify({"error": "Unsupported website"}), 400

    send_images_to_telegram(chat_id, image_urls)
    return jsonify({"status": "done", "image_count": len(image_urls)})

# --- تشغيل الخادم ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
