import re
from typing import List, Dict, Optional

class ReceiptParser:
    """
    ファミリーマートのレシートを解析するクラス（超堅牢版）
    """
    
    # 除外キーワード（これらのみの行や、これらを含むノイズ行をスキップ）
    EXCLUDE_KEYWORDS = [
        '対象', '消費税', '税等', '内', '非課税',
        '交通系', 'マネー', '支払', 'カード', '番号', '残高',
        'レジ', '登録番号', '電話', '店', '年', '月', '日', '時', '分',
        'クーポン', 'QR', 'ギフト', 'アプリ', '発行', '受取', 'キャンペーン',
        '軽減', '税率', '記号', 'URL'
    ]
    
    def __init__(self):
        # 価格パターン: ￥/¥記号 またはその誤読(V, Y, \, |, 剖) + 数字
        # もしくは行末の 3桁以上の数値
        self.price_with_symbol = re.compile(r'[¥￥VvYy\\剖\|]\s*(\d{1,6})')
        self.price_at_end = re.compile(r'\s+(\d{2,6})$')
        
        # 合計キーワード
        self.total_keywords = ['合計', '小計', '計', 'TOTAL', '合', '計']

    def parse(self, ocr_text: str) -> Dict:
        """
        OCRテキストから商品名・価格・合計を抽出
        """
        lines = ocr_text.split('\n')
        items = []
        total_amount = None
        
        # 1. まず合計金額を優先的に探す（レシートの下の方から探すのが効率的）
        for line in reversed(lines):
            line = line.strip()
            if any(k in line for k in self.total_keywords):
                # 合計行の価格抽出
                m = self.price_with_symbol.search(line) or self.price_at_end.search(line)
                if m:
                    total_amount = int(m.group(1))
                    break

        # 2. 各行をスキャンして商品を探す
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3:
                continue
                
            # 除外キーワードが含まれる場合はスキップ
            if any(k in line for k in self.EXCLUDE_KEYWORDS):
                continue
            
            # 合計金額そのものが含まれる行はスキップ（合計の二重取り防止）
            if total_amount and str(total_amount) in line:
                if any(k in line for k in self.total_keywords):
                    continue

            # 価格の抽出を試みる
            match = self.price_with_symbol.search(line) or self.price_at_end.search(line)
            
            if match:
                price = int(match.group(1))
                # 記号の前を商品名とする
                raw_name = line[:match.start()].strip()
                
                # 商品名が空、または短すぎる場合、1つ上の行を商品名として見る（分離しているケース）
                if (not raw_name or len(raw_name) < 2) and i > 0:
                    prev_line = lines[i-1].strip()
                    if len(prev_line) >= 2 and not any(k in prev_line for k in self.EXCLUDE_KEYWORDS):
                        raw_name = prev_line

                product_name = self._clean_product_name(raw_name)
                
                # 有効な商品名（2文字以上）のみ追加
                if product_name and len(product_name) >= 2:
                    # 重複チェック
                    if not any(item['name'] == product_name for item in items):
                        items.append({"name": product_name, "price": price})

        return {
            "items": items,
            "total": total_amount,
            "success": len(items) > 0 or total_amount is not None
        }

    def _clean_product_name(self, name: str) -> str:
        """
        商品名から記号やゴミを除去
        """
        # 一般的なノイズ記号を除去
        name = re.sub(r'[\|｜\-ｰ_＿\.．:：;；!！\(\)（）\+＋\*＊\?？@＠#＃\$＄%％&\^]', '', name)
        
        # 空白除去
        name = name.replace(' ', '')
        
        # 先頭や末尾の不要な文字を削る
        name = name.strip('っ、。・-')
        
        # 数字のみ、または短すぎるものは除外
        if name.isdigit() or len(name) < 2:
            return ""
            
        return name

    def format_output(self, result: Dict) -> str:
        """結果出力フォーマット"""
        if not result['items'] and not result['total']:
            return "情報を抽出できませんでした"
            
        parts = []
        for item in result['items']:
            parts.append(f"{item['name']} ¥{item['price']}")
        
        if result['total']:
             parts.append(f"合計 ¥{result['total']}")
             
        return ", ".join(parts)
