#!/usr/bin/env python3
"""
API動作確認テストスクリプト

使い方:
python test_api.py <レシート画像パス>
"""

import sys
import requests
import json

def test_ocr_api(image_path: str, api_url: str = "http://localhost:8000"):
    """
    OCR APIをテスト
    """
    print(f"🔍 テスト開始: {image_path}")
    print(f"📡 API URL: {api_url}")
    print("-" * 50)
    
    try:
        # 画像をアップロード
        with open(image_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{api_url}/scan",
                files=files,
                timeout=30
            )
        
        # レスポンス確認
        print(f"📊 HTTPステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n✅ 成功！\n")
            print("=" * 50)
            print("📝 抽出結果:")
            print("=" * 50)
            print(data.get('formatted', ''))
            print()
            
            print("=" * 50)
            print("📋 商品詳細:")
            print("=" * 50)
            for i, item in enumerate(data.get('items', []), 1):
                print(f"{i}. {item['name']}: ¥{item['price']}")
            
            if data.get('total'):
                print(f"\n💰 合計: ¥{data['total']}")
            
            print("\n" + "=" * 50)
            print("🔤 OCR生テキスト（最初の200文字）:")
            print("=" * 50)
            raw_text = data.get('raw_text', '')
            print(raw_text[:200] + "..." if len(raw_text) > 200 else raw_text)
            
        else:
            print(f"\n❌ エラー: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("\n❌ API接続エラー")
        print("💡 解決策:")
        print("  1. APIサーバーが起動しているか確認")
        print("  2. docker-compose up -d を実行")
        print("  3. URL が正しいか確認")
    
    except FileNotFoundError:
        print(f"\n❌ ファイルが見つかりません: {image_path}")
    
    except Exception as e:
        print(f"\n❌ エラー: {e}")


def test_logs_api(api_url: str = "http://localhost:8000"):
    """
    ログAPI をテスト
    """
    print("\n" + "=" * 50)
    print("📝 ログ取得テスト")
    print("=" * 50)
    
    try:
        response = requests.get(f"{api_url}/logs/ocr", timeout=10)
        
        if response.status_code == 200:
            logs = response.text
            print("\n✅ ログ取得成功\n")
            print(logs[:500] + "..." if len(logs) > 500 else logs)
        else:
            print(f"❌ エラー: {response.text}")
    
    except Exception as e:
        print(f"❌ エラー: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python test_api.py <レシート画像パス> [API_URL]")
        print("例: python test_api.py receipt.jpg")
        print("例: python test_api.py receipt.jpg https://your-app.onrender.com")
        sys.exit(1)
    
    image_path = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    # OCRテスト
    test_ocr_api(image_path, api_url)
    
    # ログテスト
    test_logs_api(api_url)
