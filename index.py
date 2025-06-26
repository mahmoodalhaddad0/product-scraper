from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)
TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

# ---------- أدوات فحص حجم الصورة ----------
def get_image_size(url):
    try:
        r = requests.head(url, timeout=5)
        return int(r.headers.get("Content-Length", 0))
    except:
        return 0

def filter_images_by_size(image_urls, min_size_kb=20, min_count=3, max_count=10):
    images_with_sizes = [(url, get_image_size(url)) for url in image_urls]
    filtered = [(url, size) for url, size in images_with_sizes if size > min_size_kb * 1024]
    filtered.sort(key=lambda x: x[1], reverse=True)
    final = [url for url, _ in filtered[:max_count]]
    return final if len(final) >= min_count else []

# ---------- سحب الصور من Charles & Keith و Wardow ----------
def extract_html_images(url, keyword):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")
    image_urls = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("srcset", "").split()[0]
        if src and src.startswith("http") and keyword in src:
            image_urls.append(src)
    return image_urls

# ---------- فلترة حسب الموقع ----------
def extract_images(url):
    if "charleskeith.com" in url:
        return filter_images_by_size(extract_html_images(url, "product"))
    elif "wardow.com" in url:
        return filter_images_by_size(extract_html_images(url, "media/image"))
    elif "6pm.com" in url:
        return filter_images_by_size(extract_html_images(url, "amazon.com"))
    else:
        return []

# ---------- إرسال الصور إلى تيليجرام ----------
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

# ---------- نقطة تشغيل API ----------
@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.json.get("url")
    chat_id = request.json.get("chat_id")
    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    image_urls = extract_images(url)
    send_images_to_telegram(chat_id, image_urls)
    return jsonify({"status": "done", "image_count": len(image_urls)})

# ---------- تشغيل الخادم ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
