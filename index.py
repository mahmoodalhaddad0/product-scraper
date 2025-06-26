from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

# ─────────── أدوات مساعدة ───────────
def get_image_size(url, timeout=5):
    """يرجع حجم الصورة بالبايت (Content-Length) أو 0 عند الفشل."""
    try:
        r = requests.head(url, timeout=timeout)
        return int(r.headers.get("Content-Length", 0))
    except Exception:
        return 0

def filter_images_by_size(image_urls, min_kb=20, min_count=3, max_count=10):
    """
    تُرجع قائمة مرتّبة (أكبر↠أصغر) للصور التي حجمها >= min_kb،
    وتقصّرها إلى max_count. إذا العدد النهائي < min_count ➜ تُرجع قائمة فارغة.
    """
    imgs_with_size = [(url, get_image_size(url)) for url in image_urls]
    # الإبقاء على الصور التي تعدّت الحجم المطلوب
    large_imgs = [(u, s) for u, s in imgs_with_size if s >= min_kb * 1024]
    large_imgs.sort(key=lambda x: x[1], reverse=True)
    selected = [u for u, _ in large_imgs[:max_count]]
    return selected if len(selected) >= min_count else []

# ─────────── استخراج الصور من صفحة المنتج ───────────
def extract_images(url):
    """يجلب الصفحة، يعثر على <img> التي تحتوي على 'product' في الرابط، ثم يُرجع أفضل الصور."""
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")

    raw_urls = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and src.startswith("http") and "product" in src:
            raw_urls.append(src)

    print("🔍 وُجدت صور مبدئية:", len(raw_urls))
    filtered = filter_images_by_size(raw_urls, min_kb=20, min_count=3, max_count=10)
    print("✅ صور بعد التصفية:", len(filtered))
    return filtered

# ─────────── إرسال الصور إلى تيليجرام ───────────
def send_images_to_telegram(chat_id, image_urls):
    if not image_urls:
        print("⚠️ أقل من 3 صور واضحة – لن يتم الإرسال.")
        return
    media = [{"type": "photo", "media": url, "caption": ""} for url in image_urls]
    media[0]["caption"] = "🖼️ Product Images"
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup",
        json={"chat_id": chat_id, "media": media}
    )
    print("📤 Telegram status:", r.status_code)

# ─────────── نقطة الـ API ───────────
@app.route("/scrape", methods=["POST"])
def scrape():
    url     = request.json.get("url")
    chat_id = request.json.get("chat_id")
    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    image_urls = extract_images(url)
    send_images_to_telegram(chat_id, image_urls)
    return jsonify({"status": "done", "image_count": len(image_urls)})

# ─────────── تشغيل فلاسـك ───────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
