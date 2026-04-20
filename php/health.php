<?php
declare(strict_types=1);

$checks = [
  ['name' => 'Airflow',          'host' => 'airflow',     'port' => 8080,  'path' => '/'],
  ['name' => 'Jupyter',          'host' => 'jupyter',     'port' => 8888,  'path' => '/'],
  ['name' => 'MinIO S3 API',     'host' => 'minio',       'port' => 9000,  'path' => '/minio/health/ready'],
  ['name' => 'MinIO Console',    'host' => 'minio',       'port' => 9001,  'path' => '/'],
];

function tcp_check(string $host, int $port, float $timeoutSec = 0.7): array {
  $errno = 0; $errstr = '';
  $start = microtime(true);
  $fp = @fsockopen($host, $port, $errno, $errstr, $timeoutSec);
  $ms = (int) round((microtime(true) - $start) * 1000);
  if ($fp) { fclose($fp); return ['ok' => true, 'ms' => $ms, 'err' => null]; }
  return ['ok' => false, 'ms' => $ms, 'err' => trim($errstr ?: ("errno={$errno}"))];
}

function http_head(string $url, float $timeoutSec = 1.4): array {
  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_NOBODY => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_FOLLOWLOCATION => false,
    CURLOPT_CONNECTTIMEOUT_MS => (int)($timeoutSec * 1000),
    CURLOPT_TIMEOUT_MS => (int)($timeoutSec * 1000),
  ]);

  $ok = curl_exec($ch);
  $err = curl_error($ch);
  $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);

  // curl_close() deprecated in PHP 8.5; omit it.

  if ($ok === false) {
    return ['ok' => false, 'code' => null, 'err' => $err ?: 'curl failed'];
  }
  return ['ok' => ($code > 0), 'code' => $code, 'err' => null];
}

$rows = [];
foreach ($checks as $c) {
  $path = $c['path'] ?? '';
  $url = "http://{$c['host']}:{$c['port']}{$path}";
  $tcp = tcp_check($c['host'], $c['port']);
  $http = ($tcp['ok'] && $c['path'] !== null) ? http_head($url) : ['ok' => false, 'code' => null, 'err' => ($tcp['ok'] ? 'HTTP n/a' : 'TCP failed')];
  $rows[] = ['c' => $c, 'url' => $url, 'tcp' => $tcp, 'http' => $http];
}

$now = (new DateTimeImmutable('now'))->format(DateTimeInterface::ATOM);

ob_start();
?>
<h1>My Data Lake</h1>
<h3><a href="/index.php">Services</a>  &nbsp; Health &nbsp; <a href="/solutions.php">Solutions</a></h3>

<p>
  <strong>Time:</strong> <code><?= htmlspecialchars($now) ?></code><br>
</p>

<div class="card">
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 220px;">Service</th>
        <th style="width: 140px;">TCP</th>
        <th style="width: 170px;">HTTP</th>
        <th>Internal URL</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($rows as $r): ?>
        <?php
          $tcpOk = $r['tcp']['ok'];
          $httpOk = $r['http']['ok'];
          $tcpLabel = $tcpOk ? 'OK' : 'FAIL';
          $httpLabel = $httpOk ? 'OK' : 'WARN';
        ?>
        <tr>
          <td>
            <strong><?= htmlspecialchars($r['c']['name']) ?></strong><br>
            <?= htmlspecialchars($r['c']['host'] . ':' . $r['c']['port']) ?>
          </td>

          <td>
            <span class="pill <?= $tcpOk ? 'good' : 'bad' ?>">
              <?= $tcpLabel ?>
            </span><br>
            <?= (int)$r['tcp']['ms'] ?> ms<?= $tcpOk ? '' : (' — ' . htmlspecialchars((string)$r['tcp']['err'])) ?>
          </td>

          <td>
            <span class="pill <?= $httpOk ? 'good' : 'warn' ?>">
              <?= $httpLabel ?>
            </span><br>
            <?= $r['http']['code'] ? ('HTTP ' . (int)$r['http']['code']) : htmlspecialchars((string)$r['http']['err']) ?>
          </td>

          <td><code><?= htmlspecialchars($r['url']) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>
<?php
$content = ob_get_clean();
$page_title = 'My Data Lake - Health';
$page_description = 'Local health checks for My Data Lake services.';
require __DIR__ . '/inc/layout.php';
