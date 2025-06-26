from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)
TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

def get_image_size(url):
    try:
        r = requests.head(url, timeout=5)
        return int(r.headers.get("Content-Length", 0))
    except:
        return 0

def filter_largest_images(image_urls, min_size=20_000, min_count=3, max_count=10):
    images_with_sizes = [(url, get_image_size(url)) for url in image_urls]
    filtered = [url for url, size in sorted(images_with_sizes, key=lambda x: x[1], reverse=True) if size >= min_size]
    return filtered[:max_count] if len(filtered) >= min_count else []

def extract_images(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")
    image_urls = []

    if "charleskeith.com" in url or "wardow.com" in url or "6pm.com" in url:
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and src.startswith("http") and "product" in src:
                image_urls.append(src)

    elif "coachoutlet.com" in url:
        for img in soup.find_all("img"):
            src = img.get("srcset") or img.get("src")
            if src:
                if "srcset" in img.attrs:
                    src = src.split(",")[-1].strip().split(" ")[0]
                if src.startswith("http") and ".jpg" in src:
                    image_urls.append(src)

    print("🔍 Found raw images:", len(image_urls))
    print("🔗 Raw image URLs:", image_urls)

    return filter_largest_images(image_urls)

def send_images_to_telegram(chat_id, image_urls):
    if not image_urls:
        print("❌ لا توجد صور مناسبة للإرسال.")
        return
    media = [{"type": "photo", "media": url, "caption": ""} for url in image_urls]
    media[0]["caption"] = "🖼️ Product Images"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup",
        json={"chat_id": chat_id, "media": media}
    )

@app.route("/scrape", methods=["POST"])
def scrape():
    url     = request.json.get("url")
    chat_id = request.json.get("chat_id")
    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    image_urls = extract_images(url)
    print("✅ Filtered image count:", len(image_urls))
    print("✅ Filtered image URLs:", image_urls)

    send_images_to_telegram(chat_id, image_urls)
    return jsonify({"status": "done", "images_sent": len(image_urls)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
