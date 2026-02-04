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
        '軽', '合計', '小計', '対象', '消費税', '税等', '内', '税込',
        '交通系', 'マネー', '支払', 'カード', '番号', '残高', 'レジ',
        '領収', '登録番号', '電話', 'FamilyMart', '店', '東京', '年',
        '月', '日', '時', '分', '秒', 'クーポン', 'QR', 'ギフト',
        'アプリ', '発行', '受取', '確認', 'コード', 'タップ', 'ポイント',
        'お預り', 'おつり', 'お釣', 'お買上', 'ありがとう', 'またのご',
        'レシート', 'ファミマ', '以上', '未満', '点数', '割引'
    ]
    
    def __init__(self):
        # 価格パターン: ¥123 or ¥123軽 or 123円
        self.price_pattern = re.compile(r'[¥￥]\s*(\d{1,5})\s*[軽円]?')
        
        # 合計金額パターン
        self.total_pattern = re.compile(r'(合計|小計|計|お買上)\s*[¥￥]?\s*(\d{1,5})')
    
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
                try:
                    total_amount = int(total_match.group(2))
                    continue
                except:
                    pass
            
            # 除外キーワードを含む行はスキップ
            if any(keyword in line for keyword in self.EXCLUDE_KEYWORDS):
                continue
            
            # 価格パターンを検出
            price_matches = list(self.price_pattern.finditer(line))
            
            if price_matches:
                # 最後の価格を商品価格とみなす
                price_match = price_matches[-1]
                price = int(price_match.group(1))
                
                # 商品名を抽出（価格の前の部分）
                product_name = line[:price_match.start()].strip()
                
                # 商品名のクリーニング
                product_name = self._clean_product_name(product_name)
                
                # 有効な商品名のみ追加
                if product_name and len(product_name) >= 2:
                    # 価格が妥当か確認（10円〜10000円）
                    if 10 <= price <= 10000:
                        items.append({
                            "name": product_name,
                            "price": price
                        })
        
        # 重複除去（同じ商品名・価格の組み合わせ）
        seen = set()
        unique_items = []
        for item in items:
            key = (item['name'], item['price'])
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        return {
            "items": unique_items,
            "total": total_amount
        }
    
    def _clean_product_name(self, name: str) -> str:
        """
        商品名をクリーニング
        
        - 記号や空白を正規化
        - 数字のみの行は除外
        - 意味のない文字列を除外
        """
        # 前後の空白と記号を削除
        name = name.strip(' \t\n\r\f\v。、，．,.')
        
        # 連続する空白を単一スペースに
        name = re.sub(r'\s+', '', name)
        
        # 数字のみの場合は除外
        if name.isdigit():
            return ""
        
        # 1文字の場合は除外（記号など）
        if len(name) == 1:
            return ""
        
        # 記号だけの場合は除外
        if re.match(r'^[◎○●△▲◇◆□■@＠\-ー\|｜]+$', name):
            return ""
        
        # 先頭の記号は残す（◎天然水など）
        # 末尾の余計な記号は削除
        name = re.sub(r'[。、，．,.]+$', '', name)
        
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
