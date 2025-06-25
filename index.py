import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

app = Flask(__name__)

GOOGLE_SHEET_WEBHOOK = "https://script.google.com/macros/s/AKfycbxKSbpFDXQAcXbVMV35oJwP6H04L67Nn_mZkKJJnSlr5Bw5OzCQH11wP6RcBuvP-WJtLQ/exec"
TELEGRAM_TOKEN = "7680689964:AAGSBbuksqOvd7Zvh_8JZhpVNMyuTFLwEMA"

def extract_data(url):
    headers = { "User-Agent": "Mozilla/5.0" }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("meta", property="og:title")
    image = soup.find("meta", property="og:image")
    price_tag = soup.find(string=lambda text: text and "$" in text)

    name = title["content"] if title else "N/A"
    price = price_tag.strip() if price_tag else "N/A"
    image_url = image["content"] if image else ""
    description = ""

    desc_meta = soup.find("meta", {"name": "description"})
    if desc_meta:
        description = desc_meta.get("content", "")

    return {
        "name": name,
        "price": price,
        "description": description,
        "image_url": image_url,
        "url": url
    }

def send_to_telegram(data, chat_id):
    caption = f"👜 *{data['name']}*\n💵 {data['price']}\n🔗 [رابط المنتج]({data['url']})\n📝 {data['description'][:100]}..."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    payload = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "Markdown",
        "document": data['image_url']
    }
    requests.post(url, data=payload)

def send_to_google_sheet(data):
    requests.post(GOOGLE_SHEET_WEBHOOK, json=data)

@app.route("/scrape", methods=["POST"])
def scrape():
    json_data = request.get_json()
    url = json_data.get("url")
    chat_id = json_data.get("chat_id")

    if not url or not chat_id:
        return jsonify({"error": "Missing url or chat_id"}), 400

    data = extract_data(url)
    send_to_google_sheet(data)
    send_to_telegram(data, chat_id)

    return jsonify({"status": "success", "data": data})
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
