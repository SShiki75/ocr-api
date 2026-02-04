import re
from typing import List, Dict, Optional

class ReceiptParser:
    """
    ファミリーマートのレシートを解析するクラス（究極堅牢版）
    """
    
    # 完全に除外するキーワード（これらのみの行や、これらを含むノイズ行をスキップ）
    EXCLUDE_KEYWORDS = [
        '対象', '消費税', '税等', '内', '非課税',
        '交通系', 'マネー', '支払', 'カード', '番号', '残高',
        'レジ', '登録番号', '電話', '店', '年', '月', '日', '時', '分',
        'クーポン', 'QR', 'ギフト', 'アプリ', '発行', '受取', 'キャンペーン',
        '軽減', '税率', '記号', 'URL', 'サイト'
    ]
    
    # 合計に関連するキーワード
    TOTAL_KEYWORDS = ['合計', '小計', '計', 'TOTAL', '合', '計']

    def __init__(self):
        # ￥記号および誤読されやすい文字のパターン
        self.symbol_pattern = r'[¥￥VvYy\\剖\|]'
        
    def parse(self, ocr_text: str) -> Dict:
        """OCRテキストを解析して商品情報を抽出"""
        lines = ocr_text.split('\n')
        items = []
        total_amount = None
        
        # 1. 合計金額の特定（逆順に走査）
        for i, line in enumerate(reversed(lines)):
            line = line.strip()
            if any(k in line for k in self.TOTAL_KEYWORDS):
                # 記号付きまたは行末の数値を合計として探す
                price = self._find_price_in_text(line)
                if price:
                    total_amount = price
                    break
                # 次の行（逆順なので上の行）もチェック
                if i < len(lines) - 1:
                    price = self._find_price_in_text(lines[-(i+2)])
                    if price:
                        total_amount = price
                        break

        # 2. 商品アイテムの特定
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3: continue
            
            # 除外キーワードチェック
            if any(k in line for k in self.EXCLUDE_KEYWORDS):
                continue
            
            # 価格を探す
            price = self._find_price_in_text(line)
            if price:
                # 合計金額そのものと一致する場合はスキップ（重複防止）
                if total_amount and price == total_amount:
                    if any(k in line for k in self.TOTAL_KEYWORDS):
                        continue
                
                # 商品名（価格より前の文字列）を特定
                price_index = line.rfind(str(price))
                raw_name = line[:price_index].strip()
                
                # 記号（￥など）を除去
                raw_name = re.sub(self.symbol_pattern, '', raw_name).strip()
                
                # 商品名が短すぎる場合、1行上のテキストを確認（商品名と価格が分かれているケース）
                if len(self._clean_name(raw_name)) < 2 and i > 0:
                    prev_line = lines[i-1].strip()
                    if len(prev_line) >= 2 and not any(k in prev_line for k in self.EXCLUDE_KEYWORDS):
                        raw_name = prev_line
                
                clean_name = self._clean_name(raw_name)
                if len(clean_name) >= 2:
                    # 重複登録を避ける
                    if not any(item['name'] == clean_name for item in items):
                        items.append({"name": clean_name, "price": price})

        return {
            "items": items,
            "total": total_amount,
            "success": len(items) > 0 or total_amount is not None
        }

    def _find_price_in_text(self, text: str) -> Optional[int]:
        """テキスト内から「価格」と思われる最適な数値を1つ抽出"""
        # A. 記号 + 数値 のパターン (例: ￥150, 剖150, V150)
        symbol_match = re.search(self.symbol_pattern + r'\s*([\d,]{1,8})', text)
        if symbol_match:
            return self._to_int(symbol_match.group(1))
            
        # B. 行末近くの 2-6 桁の数値
        end_match = re.search(r'(\d[, \d]{2,7})$', text)
        if end_match:
            return self._to_int(end_match.group(1))
            
        return None

    def _to_int(self, s: str) -> Optional[int]:
        """文字列を数値に変換（カンマやスペースを除去）"""
        s = re.sub(r'[^\d]', '', s)
        try:
            val = int(s)
            # 現実的な価格帯（1円〜100万円）を対象
            if 1 <= val <= 1000000:
                return val
        except:
            pass
        return None

    def _clean_name(self, name: str) -> str:
        """商品名からゴミ記号を徹底除去"""
        # レシートによく出る記号・誤読ノイズを除去
        name = re.sub(r'[\|｜\-ｰ_＿\.．:：;；!！\(\)（）\+＋\*＊\?？@＠#＃\$＄%％&\^=＝/／\\剖]', '', name)
        # 空白と全角空白を除去
        name = name.replace(' ', '').replace('　', '')
        # 先頭・末尾の特定の文字（。、など）を削る
        name = name.strip('っ、。・-「」')
        return name

    def format_output(self, result: Dict) -> str:
        """表示用文字列の生成"""
        if not result['items'] and not result['total']:
            return "情報を抽出できませんでした"
            
        parts = []
        for item in result['items']:
            parts.append(f"{item['name']} ¥{item['price']}")
        
        if result['total']:
             parts.append(f"合計 ¥{result['total']}")
             
        return ", ".join(parts)
