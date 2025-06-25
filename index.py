from flask import Flask, request, jsonify
import requests, os
from bs4 import BeautifulSoup

app = Flask(__name__)

TELEGRAM_BOT_TOKEN   = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbxKSbpFDXQAcXbVMV35oJwP6H04L67Nn_mZkKJJnSlr5Bw5OzCQH11wP6RcBuvP-WJtLQ/exec"

# ---------- استخراج بيانات المنتج ----------
def extract_data(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res  = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(res.content, "html.parser")

    name = soup.find("title").get_text(strip=True)

    price_tag = soup.find("span", class_="price") \
            or soup.find("span", class_="ProductPrice") \
            or soup.find("span", {"data-testid": "price"})
    price = price_tag.get_text(strip=True) if price_tag else "غير متوفر"

    desc_tag = soup.find("meta", {"name": "description"})
    description = desc_tag["content"].strip() if desc_tag else "غير متوفر"

    image_urls = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and src.startswith("http") and "product" in src:
            image_urls.append(src)

    print("🖼️ عدد الصور:", len(image_urls))
    return {
        "name":  name,
        "price": price,
        "description": description,
        "image_urls": image_urls[:10],
        "source_url": url
    }

# ---------- إرسال الصور كملفات إلى تيليجرام ----------
def send_images_to_telegram(chat_id, image_urls):
    if not image_urls:
        print("⚠️ لا توجد صور لإرسالها")
        return

    for i, url in enumerate(image_urls[:10]):
        caption = "📦 Product Image" if i == 0 else ""
        payload = {
            "chat_id": chat_id,
            "document": url,
            "caption": caption
        }
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
            json=payload
        )
        print(f"📤 أُرسلت الصورة {i+1}, Status: {r.status_code}")

# ---------- إرسال البيانات إلى Google Sheet ----------
def send_data_to_sheet(data):
    payload = {
        "name":  data["name"],
        "price": data["price"],
        "description": data["description"],
        "image_url": data["image_urls"][0] if data["image_urls"] else "",
        "url":   data["source_url"]
    }
    r = requests.post(GOOGLE_SHEET_WEBHOOK, json=payload)
    print("📋 Google Sheets Response:", r.text.strip())

# ---------- مسار الـ API ----------
@app.route("/scrape", methods=["POST"])
def scrape():
    url     = request.json.get("url")
    chat_id = request.json.get("chat_id")
    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    data = extract_data(url)
    send_images_to_telegram(chat_id, data["image_urls"])
    send_data_to_sheet(data)
    return jsonify({"status": "done"})

# ---------- تشغيل فلاســك ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
