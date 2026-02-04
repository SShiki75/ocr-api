import os
from flask import Flask, request, jsonify
from PIL import Image
import pytesseract
import psutil

from receipt_parser import parse_receipt
from utils import resize_image, preprocess_for_ocr, save_log

app = Flask(__name__)

@app.get("/")
def index():
    return "OCR API running"

@app.get("/memory")
def memory():
    mem = psutil.Process().memory_info().rss / (1024 * 1024)
    return {"memory_mb": mem}

@app.post("/ocr")
def ocr():
    if "image" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["image"]
    img = Image.open(file.stream)

    # 画像リサイズ
    img = resize_image(img)
    
    # 画像前処理（コントラスト強調、二値化など）
    img = preprocess_for_ocr(img)

    # OCR設定
    # PSM 6: 単一の均一なテキストブロックを想定
    # OEM 3: デフォルトのLSTMエンジン
    custom_config = r'--psm 6 --oem 3'
    
    # OCR実行
    text = pytesseract.image_to_string(img, lang="jpn+eng", config=custom_config)

    # パース
    parsed = parse_receipt(text)

    # ログ保存（直近2件）
    save_log(text)

    return jsonify({
        "raw_text": text,
        "parsed_data": parsed
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
