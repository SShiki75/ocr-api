FROM python:3.11-slim

# Tesseract OCRと日本語言語パックをインストール
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-jpn \
    tesseract-ocr-jpn-vert \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# ログディレクトリを作成
RUN mkdir -p /app/logs

# Renderの$PORTを使用
CMD uvicorn app:app --host 0.0.0.0 --port $PORT
