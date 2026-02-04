import re
from typing import List, Dict, Optional

class ReceiptParser:
    """
    ファミリーマートのレシートを解析するクラス
    
    除外キーワード:
    - 「軽」（軽減税率マーク）
    - 「合計」「小計」（商品名ではない）
    - 「8%対象」「(内)消費税等」などの税金情報
    - 「交通系マネー」などの支払い方法
    """
    
    EXCLUDE_KEYWORDS = [
        '軽', '合計', '小計', '対象', '消費税', '税等', '内',
        '交通系', 'マネー', '支払', 'カード', '番号', '残高',
        'レジ', '領収証', '登録番号', '電話', 'FamilyMart',
        '店', '東京', '新宿', '年', '月', '日', '時', '分',
        'クーポン', 'QR', 'ギフト', 'アプリ', '発行', '受取'
    ]
    
    def __init__(self):
        # 価格パターン: ¥123 or 123円 or ¥123軽
        self.price_pattern = re.compile(r'[¥￥]?\s*(\d{1,5})\s*[円軽]?')
        
        # 合計金額パターン
        self.total_pattern = re.compile(r'(合計|小計|計)\s*[¥￥]?\s*(\d{1,5})')
    
    def parse(self, ocr_text: str) -> Dict:
        """
        OCRテキストから商品名・価格・合計を抽出
        
        Returns:
            {
                "items": [{"name": "商品名", "price": 123}, ...],
                "total": 355
            }
        """
        lines = ocr_text.split('\n')
        items = []
        total_amount = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # 合計金額を検出
            total_match = self.total_pattern.search(line)
            if total_match:
                total_amount = int(total_match.group(2))
                continue
            
            # 除外キーワードを含む行はスキップ
            if any(keyword in line for keyword in self.EXCLUDE_KEYWORDS):
                continue
            
            # 価格パターンを検出
            price_match = self.price_pattern.search(line)
            if price_match:
                price = int(price_match.group(1))
                
                # 商品名を抽出（価格の前の部分）
                product_name = line[:price_match.start()].strip()
                
                # 商品名のクリーニング
                product_name = self._clean_product_name(product_name)
                
                # 有効な商品名のみ追加
                if product_name and len(product_name) >= 2:
                    items.append({
                        "name": product_name,
                        "price": price
                    })
        
        return {
            "items": items,
            "total": total_amount
        }
    
    def _clean_product_name(self, name: str) -> str:
        """
        商品名をクリーニング
        
        - 先頭の記号（◎、○、など）は保持
        - 数字のみの行は除外
        - 空白を正規化
        """
        # 空白を正規化
        name = re.sub(r'\s+', '', name)
        
        # 数字のみの場合は除外
        if name.isdigit():
            return ""
        
        # 特殊記号の後に何もない場合は除外
        if len(name) == 1 and not name.isalnum():
            return ""
        
        return name
    
    def format_output(self, result: Dict) -> str:
        """
        結果を指定フォーマットで出力
        
        例: 「ザバスプロテインフルー ¥247, ◎天然水新潟県津南６０ ¥108, 合計 ¥355」
        """
        parts = []
        
        for item in result['items']:
            parts.append(f"{item['name']} ¥{item['price']}")
        
        if result['total']:
            parts.append(f"合計 ¥{result['total']}")
        
        return ", ".join(parts)
