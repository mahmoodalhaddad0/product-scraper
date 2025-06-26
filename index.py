from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)
TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

# --------- استخراج الصور من تشارلز ووردو ----------
def extract_images_standard(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).content, "html.parser")
    urls = [img.get("src") or img.get("data-src")
            for img in soup.find_all("img")
            if (img.get("src") or img.get("data-src") or "").startswith("http") and "product" in (img.get("src") or "")]
    print("🔍 [STANDARD] raw:", len(urls))
    return filter_images(urls)

# --------- استخراج الصور من 6pm ----------
def extract_images_6pm(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).content, "html.parser")
    urls = []
    for img in soup.find_all("img"):
        srcset = img.get("srcset")
        src    = img.get("src")
        if srcset:
            last = srcset.split(",")[-1].strip().split(" ")[0]
            if "amazon.com" in last:
                urls.append(last)
        elif src and "amazon.com" in src:
            urls.append(src)
    print("🔍 [6PM] raw:", len(urls))
    return filter_images(urls)

# --------- استخراج الصور من Coach Outlet ----------
def extract_images_coach(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    soup = BeautifulSoup(requests.get(url, headers=headers, timeout=10).content, "html.parser")
    urls = []
    for img in soup.find_all("img"):
        src = img.get("srcset") or img.get("src")
        if not src:
            continue
        if "srcset" in img.attrs:
            src = src.split(",")[-1].strip().split(" ")[0]
        if src.startswith("http") and ".jpg" in src:
            urls.append(src)
    print("🔍 [COACH] raw:", len(urls))
    return filter_images(urls)

# --------- فلترة الصور ----------
def get_image_size(url):
    try:
        r = requests.head(url, timeout=5)
        return int(r.headers.get("Content-Length", 10240))  # 10 KB افتراضيًا عند الفشل
    except:
        return 10240

def filter_images(image_urls, min_size=10_000, min_count=3, max_count=10):
    pairs = [(u, get_image_size(u)) for u in image_urls]
    pairs = [p for p in pairs if p[1] >= min_size]
    pairs.sort(key=lambda x: x[1], reverse=True)
    selected = [u for u, _ in pairs[:max_count]]
    print("✅ filtered:", len(selected), "—", selected[:5])
    return selected if len(selected) >= min_count else []

# --------- إرسال الصور إلى تيليجرام ----------
def send_images_to_telegram(chat_id, urls):
    if len(urls) < 3:
        print("⚠️ أقل من 3 صور؛ لم يُرسل شيء.")
        return
    media = [{"type": "photo", "media": u, "caption": ""} for u in urls]
    media[0]["caption"] = "🖼️ Product Images"
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup",
                  json={"chat_id": chat_id, "media": media})

# --------- نقطة الـ API ----------
@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.json.get("url")
    chat = request.json.get("chat_id")
    if not url or not chat:
        return jsonify({"error": "Missing url or chat_id"}), 400

    if "charleskeith.com" in url or "wardow.com" in url:
        imgs = extract_images_standard(url)
    elif "6pm.com" in url:
        imgs = extract_images_6pm(url)
    elif "coachoutlet.com" in url:
        imgs = extract_images_coach(url)
    else:
        return jsonify({"error": "Unsupported website"}), 400

    send_images_to_telegram(chat, imgs)
    return jsonify({"sent": len(imgs)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
