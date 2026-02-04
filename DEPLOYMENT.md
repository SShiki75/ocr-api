# 🚀 デプロイ手順（5分で完了）

## ✅ 事前準備
- [ ] Renderアカウント作成 → https://render.com
- [ ] infinityfreeアカウント作成 → https://infinityfree.net
- [ ] GitHubリポジトリ作成

---

## 📋 ステップ1: Render（API側）

### 1-1. コードをGitHubにプッシュ

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 1-2. Renderでデプロイ

1. Renderダッシュボード → **New** → **Web Service**
2. リポジトリを接続
3. 以下を設定:

```
Name: famima-receipt-ocr
Region: Singapore
Branch: main
Root Directory: api
Runtime: Docker
Instance Type: Free
```

4. **Create Web Service** をクリック
5. デプロイ完了まで待つ（3〜5分）

### 1-3. API URLを確認

```
https://famima-receipt-ocr.onrender.com
```

この URL をメモ ✏️

---

## 📂 ステップ2: infinityfree（フロント側）

### 2-1. API URL を設定

`frontend/index.php` の11行目を編集:

```php
define('API_URL', 'https://famima-receipt-ocr.onrender.com');
                  ↑ あなたのRender URLに変更
```

### 2-2. ファイルをアップロード

1. infinityfreeコントロールパネル → **File Manager**
2. `htdocs/` に移動
3. 以下をアップロード:
   - `index.php`
   - `style.css`

### 2-3. 完了！

ブラウザで以下にアクセス:
```
https://YOUR_DOMAIN.infinityfreeapp.com
```

---

## 🧪 動作確認

### テスト1: API確認
```bash
curl https://famima-receipt-ocr.onrender.com/
```

期待される結果:
```json
{"status":"ok","service":"Receipt OCR API"}
```

### テスト2: フロント確認
1. ブラウザでサイトを開く
2. アップロードされたレシート画像（ファミリーマートレシート2.jpg）を選択
3. 「🔍 OCR実行」をクリック
4. 以下が表示されればOK:
   ```
   ザバスプロテインフルー ¥247, ◎天然水新潟県津南６０ ¥108, 合計 ¥355
   ```

---

## ⚠️ トラブルシューティング

### 問題: 「API接続エラー」

**原因:** RenderのFreeプランは15分後にスリープ

**解決策:**
1. もう一度「OCR実行」をクリック（起動に30秒〜1分）
2. Renderダッシュボードで **Manual Deploy** を実行

---

### 問題: OCR結果が空

**原因:** 画像が不鮮明 / 対応外レシート

**解決策:**
1. 高解像度で再撮影（1000px以上推奨）
2. デバッグログを確認:「👁️ ログ表示」
3. OCR生テキストで元画像の内容が認識されているか確認

---

### 問題: CSV文字化け

**原因:** Excelが UTF-8 with BOM を期待

**確認:** `index.php` 80行目に以下があるか:
```php
fprintf($fp, chr(0xEF).chr(0xBB).chr(0xBF));
```

---

## 🎉 完了！

これで完全に動作するシステムが完成しました！

### 次のステップ
- [ ] 独自ドメインを設定（infinityfree Pro）
- [ ] Renderを有料プランにしてスリープ解除
- [ ] 他のコンビニレシートにも対応

---

## 📞 サポート

問題が解決しない場合:
1. **ログ確認**: フロントの「👁️ ログ表示」
2. **Renderログ**: Renderダッシュボード → Logs
3. **GitHub Issues**: バグ報告・質問

---

**Enjoy! 🚀**
