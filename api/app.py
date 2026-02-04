from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import pytesseract
import io
import os
from datetime import datetime
import logging

from utils import preprocess_image, resize_image
from receipt_parser import ReceiptParser

# ログ設定
LOG_FILE = "logs/ocr.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FastAPIアプリ初期化
app = FastAPI(title="Receipt OCR API", version="1.0.0")

# CORS設定（infinityfreeからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のドメインに制限
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# レシートパーサー初期化
parser = ReceiptParser()


@app.get("/")
async def root():
    """ヘルスチェック"""
    return {"status": "ok", "service": "Receipt OCR API"}


@app.post("/scan")
async def scan_receipt(file: UploadFile = File(...)):
    """
    レシート画像をOCR処理して商品情報を抽出
    
    Returns:
        {
            "items": [{"name": "商品名", "price": 123}, ...],
            "total": 355,
            "formatted": "商品名 ¥123, ...",
            "raw_text": "OCR生テキスト"
        }
    """
    try:
        # 画像読み込み
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        logger.info(f"画像受信: {file.filename}, サイズ: {image.size}")
        
        # 画像前処理
        image = resize_image(image)
        processed_image = preprocess_image(image)
        
        # OCR実行（日本語 + 縦書き対応 + 高精度設定）
        # PSM 6: 単一ブロックのテキストとみなす（レシートに最適）
        # OEM 3: LSTM + Legacy（最高精度）
        custom_config = r'--oem 3 --psm 6 -l jpn'
        ocr_text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        logger.info(f"OCR完了: {len(ocr_text)} 文字")
        logger.info(f"OCR結果:\n{ocr_text}")
        
        # レシート解析
        result = parser.parse(ocr_text)
        formatted = parser.format_output(result)
        
        logger.info(f"解析結果: {formatted}")
        
        # ログに記録
        log_entry = f"\n{'='*50}\n"
        log_entry += f"ファイル名: {file.filename}\n"
        log_entry += f"処理時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_entry += f"抽出結果: {formatted}\n"
        log_entry += f"{'='*50}\n"
        
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        return JSONResponse(content={
            "success": True,
            "items": result['items'],
            "total": result['total'],
            "formatted": formatted,
            "raw_text": ocr_text
        })
        
    except Exception as e:
        logger.error(f"エラー発生: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCR処理エラー: {str(e)}")


@app.get("/logs/ocr")
async def get_ocr_logs():
    """
    OCRログをテキストで取得（デバッグ用）
    """
    try:
        if not os.path.exists(LOG_FILE):
            return PlainTextResponse("ログファイルが存在しません")
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            logs = f.read()
        
        return PlainTextResponse(logs)
    
    except Exception as e:
        logger.error(f"ログ取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs/ocr/download")
async def download_ocr_logs():
    """
    OCRログファイルをダウンロード
    """
    try:
        if not os.path.exists(LOG_FILE):
            raise HTTPException(status_code=404, detail="ログファイルが存在しません")
        
        return FileResponse(
            LOG_FILE,
            media_type='text/plain',
            filename='ocr.log'
        )
    
    except Exception as e:
        logger.error(f"ログダウンロードエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/logs/ocr")
async def clear_ocr_logs():
    """
    OCRログをクリア
    """
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(f"ログクリア: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logger.info("ログファイルをクリアしました")
        return {"success": True, "message": "ログをクリアしました"}
    
    except Exception as e:
        logger.error(f"ログクリアエラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
