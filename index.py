from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)
TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

# --------- استخراج الصور من موقع Coach ---------
def extract_images_coach(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")

    image_urls = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and "coach.scene7.com" in src and src.endswith(".jpg"):
            image_urls.append(src)

    # إزالة التكرار
    image_urls = list(set(image_urls))
    return filter_images(image_urls)

# --------- فلترة الصور ---------
def get_image_size(url):
    try:
        r = requests.head(url, timeout=5)
        return int(r.headers.get("Content-Length", 0))
    except:
        return 0

def filter_images(image_urls):
    images_with_sizes = [(url, get_image_size(url)) for url in image_urls]
    images_with_sizes = [i for i in images_with_sizes if i[1] > 20 * 1024]
    images_with_sizes.sort(key=lambda x: x[1], reverse=True)
    selected = [url for url, _ in images_with_sizes[:10]]
    return selected if len(selected) >= 3 else []

# --------- إرسال الصور إلى تيليجرام ---------
def send_images_to_telegram(chat_id, image_urls):
    if len(image_urls) < 3:
        print("⚠️ عدد الصور غير كافي")
        return
    media = [{"type": "photo", "media": url, "caption": ""} for url in image_urls]
    media[0]["caption"] = "🖼️ Product Images"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup",
        json={"chat_id": chat_id, "media": media}
    )

# --------- نقطة الدخول ---------
@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.json.get("url")
    chat_id = request.json.get("chat_id")
    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    if "coachoutlet.com" not in url:
        return jsonify({"error": "URL not supported"}), 400

    image_urls = extract_images_coach(url)
    send_images_to_telegram(chat_id, image_urls)
    return jsonify({"status": "done", "image_count": len(image_urls)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
