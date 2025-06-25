from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"
GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbxKSbpFDXQAcXbVMV35oJwP6H04L67Nn_mZkKJJnSlr5Bw5OzCQH11wP6RcBuvP-WJtLQ/exec"

def extract_data(url):
    headers = { "User-Agent": "Mozilla/5.0" }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("title").text.strip() if soup.find("title") else ""
    price = ""
    for tag in soup.find_all(["span", "div"]):
        if tag and tag.text and any(c in tag.text for c in ["$", "USD"]):
            price = tag.text.strip()
            break

    images = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if src and src.startswith("http"):
            images.append(src)

    return {
        "title": title,
        "price": price,
        "image_urls": images[:5],
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
