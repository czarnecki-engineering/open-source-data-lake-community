<?php
declare(strict_types=1);

$base = getenv('OLLAMA_BASE_URL') ?: 'http://ollama:11434';

function get_json(string $url): array {
  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT_MS => 2500,
    CURLOPT_CONNECTTIMEOUT_MS => 1200,
  ]);

  $body = curl_exec($ch);
  $err  = curl_error($ch);
  $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);

  // curl_close() deprecated in PHP 8.5; omit it.

  if ($body === false) {
    return ['ok' => false, 'code' => null, 'err' => $err ?: 'curl failed', 'raw' => null, 'json' => null];
  }

  $json = json_decode($body, true);
  return [
    'ok' => ($code >= 200 && $code < 300),
    'code' => $code,
    'err' => null,
    'raw' => $body,
    'json' => is_array($json) ? $json : null,
  ];
}

$tagsUrl = rtrim($base, '/') . '/api/tags';
$res = get_json($tagsUrl);

$now = (new DateTimeImmutable('now'))->format(DateTimeInterface::ATOM);

ob_start();
?>
<h1>Open Data Lake – Ollama</h1>

<p>
  <strong>Time:</strong> <code><?= htmlspecialchars($now) ?></code><br>
  <a href="/index.php">Back to services</a>
</p>

<div class="card">
  <h2>/api/tags</h2>

  <p>
    <strong>URL:</strong> <code><?= htmlspecialchars($tagsUrl) ?></code><br>
    <strong>Status:</strong>
    <span class="pill <?= $res['ok'] ? 'good' : 'bad' ?>"><?= $res['ok'] ? 'OK' : 'FAIL' ?></span>
    <?php if ($res['code']): ?>
      <span>HTTP <?= (int)$res['code'] ?></span>
    <?php endif; ?>
    <?php if ($res['err']): ?>
      <span>— <?= htmlspecialchars($res['err']) ?></span>
    <?php endif; ?>
  </p>

  <?php if ($res['json'] !== null): ?>
    <h3>Models</h3>
    <ul>
      <?php foreach (($res['json']['models'] ?? []) as $m): ?>
        <li>
          <strong><?= htmlspecialchars($m['name'] ?? 'unknown') ?></strong>
          <?php if (!empty($m['details']['parameter_size'])): ?>
            <span>— <?= htmlspecialchars((string)$m['details']['parameter_size']) ?></span>
          <?php endif; ?>
        </li>
      <?php endforeach; ?>
    </ul>
  <?php endif; ?>
</div>

<div class="card">
  <h3>API Response (JSON)</h3>
  <?php
    $pretty = null;
    if (!empty($res['raw'])) {
      $decoded = json_decode($res['raw'], true);
      if (json_last_error() === JSON_ERROR_NONE) {
        $pretty = json_encode($decoded, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
      }
    }
  ?>
  <pre><?= htmlspecialchars($pretty ?? $res['raw'] ?? '') ?></pre>
</div>
<?php
$content = ob_get_clean();
$page_title = 'Open Data Lake – Ollama';
$page_description = 'Local Ollama API utilities and model listing.';
require __DIR__ . '/inc/layout.php';