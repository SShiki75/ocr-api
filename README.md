# 🧾 ファミリーマート レシートOCRシステム

## 📋 概要

ファミリーマートのレシート画像から商品名・価格・合計金額を自動抽出するシステム

**抽出例:**
```
ザバスプロテインフルー ¥247, ◎天然水新潟県津南６０ ¥108, 合計 ¥355
```

### 主要機能
- ✅ レシート画像のOCR処理（Tesseract + 日本語対応）
- ✅ 商品名・価格の自動抽出（「軽」などのノイズ除去）
- ✅ CSV出力・ダウンロード
- ✅ OCRログの表示・ダウンロード
- ✅ デバッグ用生テキスト表示

---

## 🏗️ システム構成

### バックエンド（Render - FastAPI + Docker）
- **サービス:** Web Service
- **リージョン:** Singapore（推奨）
- **プラン:** Free（スリープあり）

### フロントエンド（infinityfree - PHP 8.2）
- **ホスティング:** infinityfree
- **PHP:** 8.2
- **必要拡張:** cURL, file操作

---

## 🚀 デプロイ手順

### 1️⃣ Render（バックエンドAPI）

#### ステップ1: リポジトリ準備
```bash
# Gitリポジトリ作成
git init
git add api/*
git commit -m "Initial commit"
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

#### ステップ2: Renderでデプロイ
1. [Render](https://render.com) にログイン
2. **New → Web Service** を選択
3. リポジトリを接続
4. 以下の設定:

| 項目 | 値 |
|------|-----|
| Name | `famima-receipt-ocr-api` |
| Region | Singapore |
| Branch | `main` |
| Root Directory | `api` |
| Runtime | Docker |
| Instance Type | Free |

5. **Create Web Service** をクリック

#### ステップ3: デプロイ確認
```bash
# ヘルスチェック
curl https://YOUR_APP_NAME.onrender.com/

# レスポンス例
{"status":"ok","service":"Receipt OCR API"}
```

---

### 2️⃣ infinityfree（フロントエンド）

#### ステップ1: ファイルアップロード
1. infinityfreeのコントロールパネルにログイン
2. **File Manager** を開く
3. `htdocs/` 直下に以下をアップロード:
   - `index.php`
   - `style.css`

#### ステップ2: API URL設定
`index.php` の11行目を修正:
```php
define('API_URL', 'https://YOUR_APP_NAME.onrender.com');
```

#### ステップ3: 動作確認
ブラウザで `https://YOUR_DOMAIN.infinityfreeapp.com/` にアクセス

---

## 📂 ファイル構成

```
receipt-ocr-system/
├── api/                        # Render用バックエンド
│   ├── Dockerfile             # Docker設定
│   ├── requirements.txt       # Python依存関係
│   ├── app.py                 # FastAPI メインアプリ
│   ├── receipt_parser.py      # レシート解析ロジック
│   └── utils.py               # 画像前処理
│
└── frontend/                   # infinityfree用フロント
    ├── index.php              # メインUI
    └── style.css              # スタイルシート
```

---

## 🎯 使い方

### 1. 画像アップロード
1. 「📷 レシート画像を選択」をクリック
2. ファミマのレシート画像を選択
3. 「🔍 OCR実行」をクリック

### 2. 結果確認
- **抽出データ**: フォーマット済みテキスト
- **商品リスト**: テーブル形式で表示
- **合計金額**: 自動計算

### 3. データ出力
- **CSV**: 「📥 CSV ダウンロード」ボタン
- **ログ**: 「👁️ ログ表示」または「💾 ログダウンロード」

---

## 🔧 トラブルシューティング

### ❌ 「API接続エラー」が表示される

**原因:**
- RenderのFreeプランはスリープする（15分間アクセスがない場合）
- 初回リクエストは起動に30秒〜1分かかる

**解決策:**
1. もう一度「OCR実行」をクリック
2. Renderダッシュボードでサービスが起動しているか確認

---

### ❌ OCR精度が低い

**原因:**
- レシート画像がぼやけている
- 照明が不均一

**解決策:**
1. **高解像度で撮影**: 1000px以上推奨
2. **正面から撮影**: 斜めからの撮影は避ける
3. **明るい場所で撮影**: 影が入らないように

---

### ❌ 「軽」などのノイズが混入

**原因:**
- `receipt_parser.py` の除外キーワードに含まれていない

**解決策:**
`receipt_parser.py` の15行目を編集:
```python
EXCLUDE_KEYWORDS = [
    '軽', '合計', '小計', '対象', '消費税',
    # 追加キーワードをここに記入
]
```

---

### ❌ CSV文字化け

**原因:**
- Excel対応のBOMが不足

**解決策:**
`index.php` の80行目を確認:
```php
fprintf($fp, chr(0xEF).chr(0xBB).chr(0xBF));  // BOM追加
```

---

## 🛠️ カスタマイズ

### OCR言語設定変更
`app.py` の76行目:
```python
custom_config = r'--oem 3 --psm 6 -l jpn+jpn_vert'
# 英語のみ: -l eng
# 中国語: -l chi_sim
```

### 除外キーワード追加
`receipt_parser.py` の15〜20行目:
```python
EXCLUDE_KEYWORDS = [
    '軽', '合計', '小計',
    # 追加したいキーワード
]
```

### CSVフォーマット変更
`index.php` の74〜88行目を編集

---

## 📊 API仕様

### POST /scan
レシート画像をOCR処理

**リクエスト:**
```bash
curl -X POST https://YOUR_APP.onrender.com/scan \
  -F "file=@receipt.jpg"
```

**レスポンス:**
```json
{
  "success": true,
  "items": [
    {"name": "ザバスプロテインフルー", "price": 247},
    {"name": "◎天然水新潟県津南６０", "price": 108}
  ],
  "total": 355,
  "formatted": "ザバスプロテインフルー ¥247, ◎天然水新潟県津南６０ ¥108, 合計 ¥355",
  "raw_text": "OCR生テキスト..."
}
```

### GET /logs/ocr
OCRログを取得

### GET /logs/ocr/download
OCRログをダウンロード

---

## 📝 ライセンス

MIT License

---

## 🙋 サポート

問題が発生した場合:
1. **ログ確認**: 「👁️ ログ表示」で詳細を確認
2. **画像確認**: OCR生テキストに元画像の内容が含まれているか確認
3. **API確認**: `https://YOUR_APP.onrender.com/` でヘルスチェック

---

## 🎉 改善予定
- [ ] 複数レシート一括処理
- [ ] 他コンビニ対応（セブン、ローソン）
- [ ] データベース連携
- [ ] スマホアプリ化
