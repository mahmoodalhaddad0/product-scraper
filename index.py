from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

# استخراج روابط الصور من الصفحة
def extract_images(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")

    image_urls = []
    for img in soup.find_all("img"):
        # نختار srcset إن وُجد لأنه غالبًا أوضح
        src = img.get("srcset")
        if src:
            src = src.split()[0]
        else:
            src = img.get("data-src") or img.get("src")

        if src and src.startswith("//"):
            src = "https:" + src
        if src and src.startswith("http") and "product" in src:
            image_urls.append(src)

    return filter_largest_images(image_urls)

# تحديد حجم الصورة
def get_image_size(url):
    try:
        r = requests.head(url, timeout=5)
        return int(r.headers.get("Content-Length", 0))
    except:
        return 0

# اختيار أفضل الصور بالحجم بين 3 إلى 10 صور فقط
def filter_largest_images(image_urls):
    images_with_sizes = [(url, get_image_size(url)) for url in image_urls]
    images_with_sizes = [pair for pair in images_with_sizes if pair[1] >= 20 * 1024]  # فقط الصور فوق 20KB
    images_with_sizes.sort(key=lambda x: x[1], reverse=True)

    selected = images_with_sizes[:10]
    if len(selected) < 3:
        return []  # إذا أقل من 3 صور واضحة، ما نرسل شي

    return [url for url, _ in selected]

# إرسال الصور إلى تيليجرام
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

# نقطة تشغيل API
@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.json.get("url")
    chat_id = request.json.get("chat_id")
    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    image_urls = extract_images(url)
    send_images_to_telegram(chat_id, image_urls)
    return jsonify({"status": "done", "image_count": len(image_urls)})

# تشغيل الخادم
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
