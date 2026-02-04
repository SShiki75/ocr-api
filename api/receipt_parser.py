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
        # 価格パターン: \247 or ¥247 or \24/ or \247軽 
        # Tesseractは¥を\と誤認識し、数字も誤認識することがあるため柔軟に対応
        # [¥￥\\] = 円マーク各種とバックスラッシュ
        # [/軽円]? = スラッシュ、軽、円などが続くことがある
        self.price_pattern = re.compile(r'[¥￥\\]\s*(\d{1,5})\s*[/軽円]?')
        
        # 合計金額パターン（より柔軟に）
        self.total_pattern = re.compile(r'(合計|小計|計|お買上|買上)\s*[¥￥\\]?\s*(\d{1,5})')
    
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
            
            # 合計金額を検出（複数パターン）
            total_match = self.total_pattern.search(line)
            if total_match:
                try:
                    total_str = total_match.group(2)
                    # OCR誤認識補正
                    total_str = self._correct_ocr_price(total_str, line)
                    total_amount = int(total_str)
                    continue
                except:
                    pass
            
            # 合計が漢字で誤認識されている場合も検出
            # 例: "書十" → "合計", "うロロ" → "355"
            if '書' in line or '十' in line:
                # 価格パターンで金額を探す
                price_matches_for_total = list(self.price_pattern.finditer(line))
                if price_matches_for_total:
                    try:
                        price_str = price_matches_for_total[-1].group(1)
                        price_str = self._correct_ocr_price(price_str, line)
                        total_candidate = int(price_str)
                        # 合計金額として妥当か（100円以上）
                        if total_candidate >= 100:
                            total_amount = total_candidate
                            continue
                    except:
                        pass
            
            # 価格パターンを検出
            price_matches = list(self.price_pattern.finditer(line))
            
            if not price_matches:
                continue
            
            # 最後の価格を商品価格とみなす
            price_match = price_matches[-1]
            try:
                price_str = price_match.group(1)
                
                # OCR誤認識の補正
                # 例: "24/" → "247", "10B" → "108"
                price_str = self._correct_ocr_price(price_str, line[price_match.start():price_match.end()+5])
                
                price = int(price_str)
            except:
                continue
            
            # 商品名を抽出（価格の前の部分）
            product_name = line[:price_match.start()].strip()
            
            # 除外キーワードチェック（商品名部分のみ）
            # 「軽」は価格部分にあるので、商品名には影響しない
            if any(keyword in product_name for keyword in self.EXCLUDE_KEYWORDS):
                continue
            
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
    
    def _correct_ocr_price(self, price_str: str, context: str) -> str:
        """
        OCRの価格誤認識を補正
        
        よくある誤認識:
        - 7 → / や l
        - 8 → B
        - 0 → O
        - 5 → S
        
        例:
        - "24/" → "247" (context: "\24/軽")
        - "10B" → "108" (context: "\10B軽")
        """
        # contextから手がかりを得る
        # 例: "\24/軽" なら / を 7 に変換すべき
        
        # 2桁または3桁で末尾が / → 7に変換
        if len(price_str) in [2, 3] and '/' in context:
            price_str = price_str.replace('/', '7')
        
        # 末尾が B → 8に変換
        if 'B' in context or 'b' in context:
            price_str = price_str.replace('B', '8').replace('b', '8')
        
        # O → 0 に変換（ゼロと大文字O）
        price_str = price_str.replace('O', '0').replace('o', '0')
        
        # S → 5 に変換
        price_str = price_str.replace('S', '5').replace('s', '5')
        
        # l（小文字L）→ 1 に変換
        price_str = price_str.replace('l', '1').replace('I', '1')
        
        return price_str
    
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
