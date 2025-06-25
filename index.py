from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbxKSbpFDXQAcXbVMV35oJwP6H04L67Nn_mZkKJJnSlr5Bw5OzCQH11wP6RcBuvP-WJtLQ/exec"

def extract_data(url):
    print("🚀 بدء استخراج البيانات من:", url)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print("❌ فشل الوصول للرابط:", e)
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    # استخراج اسم المنتج
    name = soup.find("title").get_text(strip=True)
    print("📝 الاسم:", name)

    # استخراج السعر
    price_element = soup.find("span", class_="price") or soup.find("span", class_="ProductPrice") or soup.find("span", {"data-testid": "price"})
    price = price_element.get_text(strip=True) if price_element else "غير متوفر"
    print("💰 السعر:", price)

    # استخراج الوصف
    desc_element = soup.find("meta", {"name": "description"}) or soup.find("div", class_="description")
    description = desc_element.get("content", "").strip() if desc_element and desc_element.name == "meta" else desc_element.get_text(strip=True) if desc_element else "غير متوفر"
    print("📄 الوصف:", description)

    # استخراج كل الصور
    image_tags = soup.find_all("img")
    image_urls = []

    for img in image_tags:
        src = img.get("src") or img.get("data-src")
        if src and "product" in src and src.startswith("http"):
            image_urls.append(src)

    print("🖼️ عدد الصور:", len(image_urls))

    if not image_urls:
        print("⚠️ لم يتم العثور على صور مناسبة.")
    
    return {
        "name": name,
        "price": price,
        "description": description,
        "image_urls": image_urls,
        "source_url": url
    }


def send_images_to_telegram(chat_id, image_urls):
    media = []
    for i, url in enumerate(image_urls):
        media.append({
            "type": "photo",
            "media": url,
            "caption": "Product Images" if i == 0 else ""
        })
    payload = {
        "chat_id": chat_id,
        "media": media
    }
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"
    requests.post(telegram_url, json=payload)

def send_data_to_sheet(data):
    response = requests.post(GOOGLE_SHEET_WEBHOOK, json=data)
    print("Google Sheets Response:", response.text)

@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.json.get("url")
    chat_id = request.json.get("chat_id")

    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    data = extract_data(url)
    send_images_to_telegram(chat_id, data["image_urls"])
    send_data_to_sheet(data)

    return jsonify({"status": "done", "data": data})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
