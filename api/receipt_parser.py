import re
from typing import List, Dict, Optional

class ReceiptParser:
    """
    ファミリーマートのレシートを解析するクラス
    """
    
    # 除外する部分文字列（商品名に含まれていたら除外）
    EXCLUDE_PATTERNS = [
        # 税金・支払い関連
        r'対象', r'消費税', r'税等', r'内\)', r'税込',
        # 支払い方法
        r'交通系', r'マネ', r'支払', r'カード', r'番号', r'残高',
        # システム情報
        r'レジ', r'領収', r'登録番号', r'電話', r'FamilyMart',
        # 日付・時刻
        r'\d+年', r'\d+月', r'\d+日', r'\d+:\d+',
        # その他
        r'クーポン', r'QR', r'ギフト', r'アプリ', r'ポイント',
        # OCR誤認識パターン
        r'[0-9]{4,}',  # 4桁以上の連続数字（登録番号など）
    ]
    
    def __init__(self):
        # 価格パターン: \247 or ¥247 or \24/軽 
        self.price_pattern = re.compile(r'[¥￥\\]\s*(\d{2,5})\s*[/軽円]?')
        
        # 合計金額パターン
        self.total_pattern = re.compile(r'(合計|小計|計|お買上|買上|言十|書十)')
    
    def parse(self, ocr_text: str) -> Dict:
        """
        OCRテキストから商品名・価格・合計を抽出
        """
        lines = ocr_text.split('\n')
        items = []
        total_amount = None
        all_prices = []  # 全ての価格を記録
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # 価格パターンを検出
            price_matches = list(self.price_pattern.finditer(line))
            if not price_matches:
                continue
            
            # 最後の価格を使用
            price_match = price_matches[-1]
            price_str = price_match.group(1)
            
            # 価格補正
            price_str, was_corrected = self._correct_ocr_price(price_str, line[price_match.start():])
            
            try:
                price = int(price_str)
            except:
                continue
            
            # 価格が妥当か確認
            if not (10 <= price <= 10000):
                continue
            
            # 商品名を抽出
            product_name = line[:price_match.start()].strip()
            
            # 合計金額の判定
            if self.total_pattern.search(line) or self.total_pattern.search(product_name):
                if price >= 100:  # 合計は100円以上
                    total_amount = price
                continue
            
            # 除外パターンチェック
            if self._should_exclude(product_name, line):
                continue
            
            # 商品名クリーニング
            product_name = self._clean_product_name(product_name)
            
            # 有効な商品名のみ追加
            if product_name and len(product_name) >= 2:
                # 同じ商品・価格の重複を避ける
                if not any(item['name'] == product_name and item['price'] == price for item in items):
                    items.append({
                        "name": product_name,
                        "price": price
                    })
                    all_prices.append(price)
        
        # 合計が見つからない場合、最大の価格を合計とする
        if not total_amount and all_prices:
            # 全商品の合計を計算
            calculated_total = sum(all_prices)
            # 最も大きい価格を確認
            max_price = max(all_prices) if all_prices else 0
            
            # 最大価格が他の価格の合計に近い場合、それを合計とする
            if len(all_prices) > 1 and max_price >= calculated_total * 0.8:
                total_amount = max_price
                # その価格を商品リストから削除
                items = [item for item in items if item['price'] != max_price]
            else:
                total_amount = calculated_total
        
        return {
            "items": items,
            "total": total_amount
        }
    
    def _correct_ocr_price(self, price_str: str, context: str) -> tuple:
        """
        OCRの価格誤認識を補正
        
        Returns:
            (補正後の価格文字列, 補正されたかどうか)
        """
        original = price_str
        corrected = False
        
        # 2桁価格で/が続く場合、末尾に7を追加
        if len(price_str) == 2 and re.search(r'[/\\]', context):
            price_str = price_str + '7'
            corrected = True
        
        # 一般的な文字置換
        replacements = {
            '/': '7', 'l': '1', 'I': '1',
            'B': '8', 'b': '8',
            'O': '0', 'o': '0',
            'S': '5', 's': '5',
            'Z': '2', 'z': '2',
        }
        
        for old, new in replacements.items():
            if old in price_str:
                price_str = price_str.replace(old, new)
                corrected = True
        
        return price_str, corrected
    
    def _should_exclude(self, product_name: str, full_line: str) -> bool:
        """
        この行を除外すべきかチェック
        """
        # 除外パターンに一致するか
        for pattern in self.EXCLUDE_PATTERNS:
            if re.search(pattern, product_name) or re.search(pattern, full_line):
                return True
        
        # 商品名が短すぎる
        if len(product_name) < 2:
            return True
        
        # 記号だけ
        if re.match(r'^[^a-zA-Z0-9ぁ-んァ-ヶー一-龯]+$', product_name):
            return True
        
        # 「軽」だけの行
        if product_name in ['軽', '◎', '@', '○']:
            return True
        
        return False
    
    def _clean_product_name(self, name: str) -> str:
        """
        商品名をクリーニング
        """
        # 前後の空白と記号を削除
        name = name.strip(' \t\n\r\f\v。、，．,.:：;；')
        
        # 連続する空白を削除
        name = re.sub(r'\s+', '', name)
        
        # 先頭の特定記号以外を削除
        # ◎、@は残す
        name = re.sub(r'^[^\w◎@ぁ-んァ-ヶー一-龯]+', '', name)
        
        # 末尾の記号を削除
        name = re.sub(r'[。、，．,.]+$', '', name)
        
        return name
    
    def format_output(self, result: Dict) -> str:
        """
        結果を指定フォーマットで出力
        """
        parts = []
        
        for item in result['items']:
            parts.append(f"{item['name']} ¥{item['price']}")
        
        if result['total']:
            parts.append(f"合計 ¥{result['total']}")
        
        return ", ".join(parts)
