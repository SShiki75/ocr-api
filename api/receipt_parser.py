import re
from typing import List, Dict, Optional

class ReceiptParser:
    """
    ファミリーマートのレシートを解析するクラス（改良版）
    """
    
    # 解析をスキップするヘッダーキーワード
    START_KEYWORDS = ['領収証', 'FamilyMart', 'ファミリーマート']
    
    # 除外キーワード（行内に含まれる場合にスキップ）
    EXCLUDE_KEYWORDS = [
        '対象', '消費税', '税等', '内', '非課税',
        '交通系', 'マネー', '支払', 'カード', '番号', '残高',
        'レジ', '登録番号', '電話', '店', '年', '月', '日', '時', '分',
        'クーポン', 'QR', 'ギフト', 'アプリ', '発行', '受取', 'キャンペーン'
    ]
    
    def __init__(self):
        # 価格パターン: ¥ または ￥ の後の数字
        self.price_pattern = re.compile(r'[¥￥]\s*(\d{1,6})')
        
        # 合計金額キーワード
        self.total_keywords = ['合計', '小計', '計', 'TOTAL']
    
    def parse(self, ocr_text: str) -> Dict:
        """
        OCRテキストから商品名・価格・合計を抽出
        """
        lines = ocr_text.split('\n')
        items = []
        total_amount = None
        
        # 解析開始フラグ（「領収証」などを見つけるまではスキップ）
        start_parsing = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 解析開始位置の特定
            if not start_parsing:
                if any(k in line for k in self.START_KEYWORDS):
                    start_parsing = True
                continue
            
            # 合計金額の検出（「合計」キーワードがある行、またはその付近）
            if any(k in line for k in self.total_keywords):
                # 行内に ￥ があればそれを合計とする
                total_match = self.price_pattern.search(line)
                if total_match:
                    total_amount = int(total_match.group(1))
                    continue # 合計行は商品として処理しない
            
            # 除外キーワードを含む行はスキップ
            if any(keyword in line for keyword in self.EXCLUDE_KEYWORDS):
                continue
            
            # ￥ 記号を基準に商品名と価格を抽出
            price_match = self.price_pattern.search(line)
            if price_match:
                price = int(price_match.group(1))
                
                # ￥記号より前を商品名とする
                raw_name = line[:price_match.start()].strip()
                
                # 商品名のクリーニング
                product_name = self._clean_product_name(raw_name)
                
                # 有効な商品名（2文字以上）のみ追加
                if product_name and len(product_name) >= 2:
                    # 重複チェック（OCRの重複読み対策）
                    if not any(item['name'] == product_name and item['price'] == price for item in items):
                        items.append({
                            "name": product_name,
                            "price": price
                        })
        
        # もし合計が取れなかった場合、商品の合算を暫定合計とする（予備ロジック）
        if total_amount is None and items:
             # ただしレシートの性質上、合算は不正確になりやすいため、基本はOCR結果を優先
             pass

        return {
            "items": items,
            "total": total_amount,
            "success": len(items) > 0 # 商品が1つでも取れれば成功とみなす
        }
    
    def _clean_product_name(self, name: str) -> str:
        """
        商品名からノイズを除去
        """
        # レシートによく現れるノイズ文字・記号を除去
        name = re.sub(r'[\|｜\-ｰ_＿\.．:：;；!！\(\)（）\+＋\*＊\?？]', '', name)
        
        # 行頭・行末の空白とゴミを除去
        name = name.strip()
        
        # 数字のみの行は除外
        if name.isdigit():
            return ""
        
        # 1文字の記号は除外
        if len(name) <= 1 and not name.isalnum():
            return ""
            
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
        
        return ", ".join(parts) if parts else "情報を抽出できませんでした"
