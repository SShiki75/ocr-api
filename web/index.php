<?php
/**
 * ファミリーマート レシートOCRシステム
 * 
 * 機能:
 * - 画像アップロード → Render APIでOCR処理
 * - 商品名・価格・合計を画面表示
 * - CSV出力・ダウンロード
 * - OCRログ表示・ダウンロード
 */

// エラー表示設定（デバッグ用）
error_reporting(E_ALL);
ini_set('display_errors', 1);

// API設定
define('API_URL', 'https://ocr-api-wh2v.onrender.com');

// CSV保存先
define('CSV_FILE', 'result.csv');

// 変数初期化
$result = null;
$error = null;
$csv_download_url = null;

// POSTリクエスト処理
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    // 画像アップロード処理
    if (isset($_FILES['receipt_image']) && $_FILES['receipt_image']['error'] === UPLOAD_ERR_OK) {

        $tmp_name = $_FILES['receipt_image']['tmp_name'];
        $file_name = $_FILES['receipt_image']['name'];

        // APIにファイルを送信
        $ch = curl_init();
        $cfile = new CURLFile($tmp_name, $_FILES['receipt_image']['type'], $file_name);

        curl_setopt_array($ch, [
            CURLOPT_URL => API_URL . '/scan',
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => ['file' => $cfile],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 90, // Renderの100秒制限に合わせ、90秒に調整
        ]);

        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $info = curl_getinfo($ch);

        if (curl_errno($ch)) {
            $error = 'API接続エラー: ' . curl_error($ch) . ' (Time: ' . $info['total_time'] . 's)';
        } elseif ($http_code !== 200) {
            $error = "APIエラー (HTTP $http_code): " . $response;
        } else {
            $result = json_decode($response, true);

            // CSV生成
            if ($result && isset($result['items'])) {
                generate_csv($result);
                $csv_download_url = CSV_FILE;
            }
        }

        curl_close($ch);
    } else {
        $error = '画像ファイルを選択してください';
    }
}

/**
 * CSV生成
 */
function generate_csv($data)
{
    $fp = fopen(CSV_FILE, 'w');

    // BOM追加（Excel対応）
    fprintf($fp, chr(0xEF) . chr(0xBB) . chr(0xBF));

    // ヘッダー
    fputcsv($fp, ['商品名', '価格']);

    // 商品データ
    foreach ($data['items'] as $item) {
        fputcsv($fp, [$item['name'], $item['price']]);
    }

    // 合計
    if (isset($data['total']) && $data['total']) {
        fputcsv($fp, ['合計', $data['total']]);
    }

    fclose($fp);
}

/**
 * OCRログ取得
 */
function get_ocr_logs()
{
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => API_URL . '/logs/ocr',
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
    ]);

    $response = curl_exec($ch);
    curl_close($ch);

    return $response ?: 'ログが取得できませんでした';
}

// ログ表示リクエスト
$show_logs = isset($_GET['show_logs']);
$logs = $show_logs ? get_ocr_logs() : null;

?>
<!DOCTYPE html>
<html lang="ja">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ファミマレシートOCR</title>
    <link rel="stylesheet" href="style.css">
</head>

<body>
    <div class="container">
        <header>
            <h1>🧾 ファミリーマート レシートOCR</h1>
            <p>レシート画像をアップロードして商品情報を抽出</p>
        </header>

        <!-- 画像アップロードフォーム -->
        <section class="upload-section">
            <form method="POST" enctype="multipart/form-data" id="uploadForm">
                <div class="file-input-wrapper">
                    <label for="receipt_image" class="file-label">
                        📷 レシート画像を選択
                    </label>
                    <input type="file" name="receipt_image" id="receipt_image" accept="image/*" required>
                    <span id="fileName" class="file-name">ファイル未選択</span>
                </div>
                <button type="submit" class="btn btn-primary">🔍 OCR実行</button>
            </form>
        </section>

        <!-- エラー表示 -->
        <?php if ($error): ?>
            <div class="alert alert-error">
                ❌ <?= htmlspecialchars($error) ?>
            </div>
        <?php endif; ?>

        <!-- OCR結果表示 -->
        <?php if ($result && isset($result['success']) && $result['success']): ?>
            <section class="result-section">
                <h2>📊 抽出結果</h2>

                <!-- フォーマット済み出力 -->
                <div class="formatted-output">
                    <strong>抽出データ:</strong>
                    <p class="result-text"><?= htmlspecialchars($result['formatted']) ?></p>
                </div>

                <!-- 商品リスト -->
                <div class="items-table">
                    <table>
                        <thead>
                            <tr>
                                <th>商品名</th>
                                <th>価格</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($result['items'] as $item): ?>
                                <tr>
                                    <td><?= htmlspecialchars($item['name']) ?></td>
                                    <td class="price">¥<?= number_format($item['price']) ?></td>
                                </tr>
                            <?php endforeach; ?>
                            <?php if (isset($result['total']) && $result['total']): ?>
                                <tr class="total-row">
                                    <td><strong>合計</strong></td>
                                    <td class="price"><strong>¥<?= number_format($result['total']) ?></strong></td>
                                </tr>
                            <?php endif; ?>
                        </tbody>
                    </table>
                </div>

                <!-- ダウンロードボタン -->
                <div class="download-buttons">
                    <?php if ($csv_download_url): ?>
                        <a href="<?= $csv_download_url ?>" download class="btn btn-success">
                            📥 CSV ダウンロード
                        </a>
                    <?php endif; ?>
                </div>

                <!-- OCR生テキスト（折りたたみ） -->
                <details class="raw-text-section">
                    <summary>🔍 OCR生テキストを表示</summary>
                    <pre><?= htmlspecialchars($result['raw_text']) ?></pre>
                </details>
            </section>
        <?php endif; ?>

        <!-- ログ管理セクション -->
        <section class="log-section">
            <h2>📝 デバッグログ</h2>
            <div class="log-buttons">
                <a href="?show_logs=1" class="btn btn-secondary">
                    👁️ ログ表示
                </a>
                <a href="<?= API_URL ?>/logs/ocr/download" download class="btn btn-secondary">
                    💾 ログダウンロード
                </a>
            </div>

            <?php if ($show_logs): ?>
                <div class="log-viewer">
                    <h3>OCR処理ログ</h3>
                    <pre><?= htmlspecialchars($logs) ?></pre>
                    <a href="?" class="btn btn-secondary">✖️ 閉じる</a>
                </div>
            <?php endif; ?>
        </section>

        <footer>
            <p>Powered by Tesseract OCR + FastAPI + PHP</p>
        </footer>
    </div>

    <script>
        // ファイル名表示
        document.getElementById('receipt_image').addEventListener('change', function (e) {
            const fileName = e.target.files[0]?.name || 'ファイル未選択';
            document.getElementById('fileName').textContent = fileName;
        });

        // フォーム送信時のローディング表示
        document.getElementById('uploadForm').addEventListener('submit', function () {
            const btn = this.querySelector('button[type="submit"]');
            btn.textContent = '⏳ 処理中...';
            btn.disabled = true;
        });
    </script>
</body>

</html>