<?php
/**
 * infinityfree cURL制限テストページ
 * 
 * このページでAPIへの接続をテストして、
 * infinityfreeの制限を診断します
 */

header('Content-Type: text/html; charset=utf-8');

$api_url = 'https://ocr-api-wh2v.onrender.com';
$results = [];

// テスト1: ヘルスチェック
$results['health_check'] = test_health_check($api_url);

// テスト2: cURL設定確認
$results['curl_info'] = get_curl_info();

// テスト3: PHPinfo確認
$results['php_info'] = get_php_restrictions();

function test_health_check($url) {
    $ch = curl_init();
    
    curl_setopt_array($ch, [
        CURLOPT_URL => $url . '/',
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_SSL_VERIFYPEER => true,
    ]);
    
    $start = microtime(true);
    $response = curl_exec($ch);
    $elapsed = microtime(true) - $start;
    
    $info = curl_getinfo($ch);
    $error = curl_error($ch);
    $errno = curl_errno($ch);
    
    curl_close($ch);
    
    return [
        'success' => !$errno && $info['http_code'] == 200,
        'http_code' => $info['http_code'],
        'response' => $response,
        'error' => $error,
        'errno' => $errno,
        'connect_time' => $info['connect_time'],
        'total_time' => $elapsed,
        'url' => $url . '/',
    ];
}

function get_curl_info() {
    return [
        'curl_version' => function_exists('curl_version') ? curl_version() : 'Not available',
        'curl_enabled' => function_exists('curl_init'),
        'openssl_enabled' => extension_loaded('openssl'),
    ];
}

function get_php_restrictions() {
    return [
        'max_execution_time' => ini_get('max_execution_time'),
        'max_input_time' => ini_get('max_input_time'),
        'upload_max_filesize' => ini_get('upload_max_filesize'),
        'post_max_size' => ini_get('post_max_size'),
        'memory_limit' => ini_get('memory_limit'),
        'allow_url_fopen' => ini_get('allow_url_fopen'),
        'disable_functions' => ini_get('disable_functions'),
    ];
}

?>
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>infinityfree cURL テスト</title>
    <style>
        body {
            font-family: monospace;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
        }
        h1 { color: #4ec9b0; }
        h2 { 
            color: #569cd6; 
            margin-top: 30px;
            border-bottom: 2px solid #569cd6;
            padding-bottom: 5px;
        }
        .success { color: #4ec9b0; }
        .error { color: #f48771; }
        .warning { color: #dcdcaa; }
        pre {
            background: #2d2d2d;
            padding: 15px;
            border-left: 3px solid #007acc;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #404040;
        }
        th {
            background: #2d2d2d;
            color: #4ec9b0;
        }
    </style>
</head>
<body>
    <h1>🔍 infinityfree cURL 接続テスト</h1>
    <p>Render APIへの接続をテストします</p>

    <!-- テスト1: ヘルスチェック -->
    <h2>テスト1: API ヘルスチェック</h2>
    <table>
        <tr>
            <th>項目</th>
            <th>結果</th>
        </tr>
        <tr>
            <td>URL</td>
            <td><?= htmlspecialchars($results['health_check']['url']) ?></td>
        </tr>
        <tr>
            <td>ステータス</td>
            <td class="<?= $results['health_check']['success'] ? 'success' : 'error' ?>">
                <?= $results['health_check']['success'] ? '✅ 成功' : '❌ 失敗' ?>
            </td>
        </tr>
        <tr>
            <td>HTTPコード</td>
            <td><?= $results['health_check']['http_code'] ?></td>
        </tr>
        <tr>
            <td>接続時間</td>
            <td><?= number_format($results['health_check']['connect_time'], 3) ?>秒</td>
        </tr>
        <tr>
            <td>合計時間</td>
            <td><?= number_format($results['health_check']['total_time'], 3) ?>秒</td>
        </tr>
        <?php if ($results['health_check']['error']): ?>
        <tr>
            <td>エラー</td>
            <td class="error">
                <?= htmlspecialchars($results['health_check']['error']) ?>
                (Error #<?= $results['health_check']['errno'] ?>)
            </td>
        </tr>
        <?php endif; ?>
    </table>

    <?php if ($results['health_check']['success']): ?>
    <div class="success">
        <h3>✅ API接続成功！</h3>
        <pre><?= htmlspecialchars($results['health_check']['response']) ?></pre>
    </div>
    <?php else: ?>
    <div class="error">
        <h3>❌ API接続失敗</h3>
        <p>考えられる原因:</p>
        <ul>
            <li>infinityfreeが外部URLへのcURLをブロックしている</li>
            <li>タイムアウト設定が短すぎる</li>
            <li>Renderのサービスがダウンしている</li>
        </ul>
    </div>
    <?php endif; ?>

    <!-- テスト2: cURL情報 -->
    <h2>テスト2: cURL設定</h2>
    <table>
        <tr>
            <th>項目</th>
            <th>値</th>
        </tr>
        <tr>
            <td>cURL有効</td>
            <td class="<?= $results['curl_info']['curl_enabled'] ? 'success' : 'error' ?>">
                <?= $results['curl_info']['curl_enabled'] ? '✅ 有効' : '❌ 無効' ?>
            </td>
        </tr>
        <tr>
            <td>OpenSSL有効</td>
            <td class="<?= $results['curl_info']['openssl_enabled'] ? 'success' : 'error' ?>">
                <?= $results['curl_info']['openssl_enabled'] ? '✅ 有効' : '❌ 無効' ?>
            </td>
        </tr>
        <?php if (isset($results['curl_info']['curl_version']['version'])): ?>
        <tr>
            <td>cURLバージョン</td>
            <td><?= htmlspecialchars($results['curl_info']['curl_version']['version']) ?></td>
        </tr>
        <?php endif; ?>
    </table>

    <!-- テスト3: PHP設定 -->
    <h2>テスト3: PHP設定</h2>
    <table>
        <tr>
            <th>設定項目</th>
            <th>値</th>
        </tr>
        <?php foreach ($results['php_info'] as $key => $value): ?>
        <tr>
            <td><?= htmlspecialchars($key) ?></td>
            <td><?= htmlspecialchars($value ?: '(未設定)') ?></td>
        </tr>
        <?php endforeach; ?>
    </table>

    <!-- 推奨事項 -->
    <h2>📋 推奨事項</h2>
    <?php if ($results['health_check']['success']): ?>
    <div class="success">
        <p>✅ API接続は正常です。</p>
        <p>もしOCR実行時にタイムアウトする場合:</p>
        <ul>
            <li><strong>index_direct.html</strong> を使用（ブラウザから直接API接続）</li>
            <li>UptimeRobotでAPIを定期的に起動（PREVENT_SLEEP.md参照）</li>
        </ul>
    </div>
    <?php else: ?>
    <div class="error">
        <p>❌ infinityfreeからRender APIへの接続に失敗しています。</p>
        <p><strong>解決策:</strong></p>
        <ol>
            <li><strong>index_direct.html</strong> を使用してください
                <ul>
                    <li>ブラウザから直接Render APIに接続</li>
                    <li>infinityfreeのサーバー経由ではないため制限なし</li>
                </ul>
            </li>
            <li>別のホスティングサービスを検討
                <ul>
                    <li>Netlify（無料）</li>
                    <li>Vercel（無料）</li>
                    <li>GitHub Pages（無料）</li>
                </ul>
            </li>
        </ol>
    </div>
    <?php endif; ?>

    <hr style="margin: 40px 0; border-color: #404040;">
    <p style="text-align: center; color: #666;">
        テスト完了 | 
        <a href="index.php" style="color: #569cd6;">メインページに戻る</a> |
        <a href="index_direct.html" style="color: #4ec9b0;">直接API版を試す</a>
    </p>
</body>
</html>
