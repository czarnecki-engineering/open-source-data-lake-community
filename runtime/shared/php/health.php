<?php
declare(strict_types=1);

require __DIR__ . '/inc/submenu.php';

$checks = [
    ['name' => 'Airflow Web', 'host' => 'airflow-web', 'port' => 8080, 'path' => '/health'],
    ['name' => 'MinIO API', 'host' => 'minio', 'port' => 9000, 'path' => '/minio/health/ready'],
    ['name' => 'MinIO Console', 'host' => 'minio', 'port' => 9001, 'path' => '/'],
    ['name' => 'Lakekeeper', 'host' => 'lakekeeper', 'port' => 8181, 'path' => '/'],
    ['name' => 'Trino', 'host' => 'trino', 'port' => 8080, 'path' => '/ui/'],
    ['name' => 'Metabase', 'host' => 'metabase', 'port' => 3000, 'path' => '/'],
    ['name' => 'Elasticsearch', 'host' => 'elasticsearch', 'port' => 9200, 'path' => '/_cluster/health'],
    ['name' => 'Kibana', 'host' => 'kibana', 'port' => 5601, 'path' => '/api/status'],
    ['name' => 'CloudBeaver', 'host' => 'cloudbeaver', 'port' => 8978, 'path' => '/'],
    ['name' => 'AI Access API', 'host' => 'ai-access-api', 'port' => 8000, 'path' => '/health'],
    ['name' => 'Open WebUI', 'host' => 'open-webui', 'port' => 8080, 'path' => '/'],
];

function tcp_check(string $host, int $port, float $timeoutSec = 0.7): array
{
    $errno = 0;
    $errstr = '';
    $start = microtime(true);
    $fp = @fsockopen($host, $port, $errno, $errstr, $timeoutSec);
    $ms = (int) round((microtime(true) - $start) * 1000);

    if ($fp) {
        fclose($fp);
        return ['ok' => true, 'ms' => $ms, 'err' => null];
    }

    return ['ok' => false, 'ms' => $ms, 'err' => trim($errstr ?: ("errno={$errno}"))];
}

function http_head(string $url, float $timeoutSec = 1.5): array
{
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_NOBODY => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_CONNECTTIMEOUT_MS => (int) ($timeoutSec * 1000),
        CURLOPT_TIMEOUT_MS => (int) ($timeoutSec * 1000),
    ]);

    $ok = curl_exec($ch);
    $err = curl_error($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);

    if ($ok === false) {
        return ['ok' => false, 'code' => null, 'err' => $err ?: 'curl failed'];
    }

    return ['ok' => $code > 0, 'code' => $code, 'err' => null];
}

$rows = [];
foreach ($checks as $check) {
    $url = "http://{$check['host']}:{$check['port']}{$check['path']}";
    $tcp = tcp_check($check['host'], $check['port']);
    $http = $tcp['ok']
        ? http_head($url)
        : ['ok' => false, 'code' => null, 'err' => 'TCP failed'];

    $rows[] = ['check' => $check, 'url' => $url, 'tcp' => $tcp, 'http' => $http];
}

$contentMountInfo = [
    'path' => __DIR__,
    'exists' => is_dir(__DIR__),
    'writable' => is_writable(__DIR__),
];

$dataMountPath = '/app/data';
$dataMountInfo = [
    'path' => $dataMountPath,
    'exists' => is_dir($dataMountPath),
    'writable' => is_writable($dataMountPath),
];

$now = (new DateTimeImmutable('now'))->format(DateTimeInterface::ATOM);

ob_start();
?>
<h1>FrankenPHP Health</h1>
<?php render_primary_submenu('health'); ?>

<p>
  <strong>Time:</strong> <code><?= htmlspecialchars($now) ?></code><br>
  Checks run from the FrankenPHP pod to in-cluster services. Some services may still be warming when <code>runtime/knowledge-lake/start-k8s.sh</code> returns.
</p>

<div class="card">
  <h2>In-Cluster Reachability</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 220px;">Service</th>
        <th style="width: 140px;">TCP</th>
        <th style="width: 160px;">HTTP</th>
        <th>Internal URL</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($rows as $row): ?>
        <?php
        $tcpOk = $row['tcp']['ok'];
        $httpOk = $row['http']['ok'];
        ?>
        <tr>
          <td><strong><?= htmlspecialchars($row['check']['name']) ?></strong><br><code><?= htmlspecialchars($row['check']['host'] . ':' . $row['check']['port']) ?></code></td>
          <td>
            <span class="pill <?= $tcpOk ? 'good' : 'bad' ?>"><?= $tcpOk ? 'OK' : 'FAIL' ?></span><br>
            <?= (int) $row['tcp']['ms'] ?> ms<?= $tcpOk ? '' : (' - ' . htmlspecialchars((string) $row['tcp']['err'])) ?>
          </td>
          <td>
            <span class="pill <?= $httpOk ? 'good' : 'warn' ?>"><?= $httpOk ? 'OK' : 'WARN' ?></span><br>
            <?= $row['http']['code'] ? ('HTTP ' . (int) $row['http']['code']) : htmlspecialchars((string) $row['http']['err']) ?>
          </td>
          <td><code><?= htmlspecialchars($row['url']) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Live Mount Status</h2>
  <p><strong>Content mount:</strong> <code><?= htmlspecialchars($contentMountInfo['path']) ?></code></p>
  <p>
    <span class="pill <?= $contentMountInfo['exists'] ? 'good' : 'bad' ?>"><?= $contentMountInfo['exists'] ? 'DIR OK' : 'DIR MISSING' ?></span>
    <span class="pill <?= $contentMountInfo['writable'] ? 'warn' : 'good' ?>"><?= $contentMountInfo['writable'] ? 'WRITABLE' : 'READ ONLY' ?></span>
  </p>
  <p>
    For the current local-development direction, the FrankenPHP content mount may be intentionally read-only from the container while still reflecting host-side edits immediately.
  </p>
  <p><strong>Data mount:</strong> <code><?= htmlspecialchars($dataMountInfo['path']) ?></code></p>
  <p>
    <span class="pill <?= $dataMountInfo['exists'] ? 'good' : 'bad' ?>"><?= $dataMountInfo['exists'] ? 'DIR OK' : 'DIR MISSING' ?></span>
    <span class="pill <?= $dataMountInfo['writable'] ? 'good' : 'bad' ?>"><?= $dataMountInfo['writable'] ? 'WRITABLE' : 'READ ONLY' ?></span>
  </p>
  <p>
    This checks the FrankenPHP content and local data mounts only. It does not claim that every runtime component is live-mounted.
  </p>
</div>
<?php
$content = ob_get_clean();
$page_title = 'Knowledge Lake Local Runtime Health';
$page_description = 'Service and live-mount checks from the FrankenPHP pod.';
require __DIR__ . '/inc/layout.php';
