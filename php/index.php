<?php
declare(strict_types=1);

$host = '127.0.0.1';
$services = [
  ['Service' => 'Airflow',        'URL' => "http://{$host}:8080/",  'Notes' => 'Web UI'],
  ['Service' => 'Jupyter',        'URL' => "http://{$host}:8888/",  'Notes' => 'Notebook UI'],
  ['Service' => 'MinIO Console',  'URL' => "http://{$host}:9001/",  'Notes' => 'Admin console'],
  ['Service' => 'MinIO S3 API',   'URL' => "http://{$host}:9000/",  'Notes' => 'S3 endpoint'],
  ['Service' => 'CloudBeaver',    'URL' => "http://{$host}:8978/",  'Notes' => 'DB admin UI'],
  ['Service' => 'Streamlit',      'URL' => "http://{$host}:8501/",  'Notes' => 'App UI'],
  ['Service' => 'Metabase',       'URL' => "http://{$host}:3000/",  'Notes' => 'Dashboards'],
  ['Service' => 'ClickHouse (HTTP)', 'URL' => "http://{$host}:8123/", 'Notes' => 'HTTP interface'],
  ['Service' => 'ClickHouse (native)', 'URL' => "tcp://{$host}:19000", 'Notes' => 'Native protocol (host 19000 -> container 9000)'],
  ['Service' => 'Ollama API',     'URL' => "http://{$host}:11434/", 'Notes' => 'API root'],
  ['Service' => 'PHP (this)',     'URL' => "http://{$host}:8088/",  'Notes' => 'FrankenPHP'],
];

$utilities = [
  ['Page' => 'Container health checks', 'URL' => "/health.php", 'Notes' => 'From PHP container to other containers'],
  ['Page' => 'Ollama utilities',        'URL' => "/ollama.php", 'Notes' => 'Basic API checks and model listing'],
];

$now = (new DateTimeImmutable('now'))->format(DateTimeInterface::ATOM);

ob_start();
?>
<h1>Open Data Lake – Services</h1>

<p>
  <strong>Time:</strong> <code><?= htmlspecialchars($now) ?></code>
</p>

<div class="card">
  <h2>Service home pages</h2>
  <table class="tiers-compare">
    <thead>
      <tr><th style="width: 180px;">Service</th><th>URL</th><th style="width: 260px;">Notes</th></tr>
    </thead>
    <tbody>
      <?php foreach ($services as $s): ?>
        <tr>
          <td><strong><?= htmlspecialchars($s['Service']) ?></strong></td>
          <td>
            <a href="<?= htmlspecialchars($s['URL']) ?>" target="_blank" rel="noopener">
              <?= htmlspecialchars($s['URL']) ?>
            </a>
          </td>
          <td><?= htmlspecialchars($s['Notes']) ?></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Utility pages</h2>
  <table class="tiers-compare">
    <thead>
      <tr><th style="width: 220px;">Page</th><th>Link</th><th style="width: 260px;">Notes</th></tr>
    </thead>
    <tbody>
      <?php foreach ($utilities as $u): ?>
        <tr>
          <td><strong><?= htmlspecialchars($u['Page']) ?></strong></td>
          <td><a href="<?= htmlspecialchars($u['URL']) ?>"><?= htmlspecialchars($u['URL']) ?></a></td>
          <td><?= htmlspecialchars($u['Notes']) ?></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<p>
  If your browser upgrades <code>localhost</code> to HTTPS, use <code>http://127.0.0.1:8088/</code>.
</p>
<?php
$content = ob_get_clean();
$page_title = 'Open Data Lake – Services';
$page_description = 'Local service index for the Open Data Lake Docker Compose stack.';
require __DIR__ . '/inc/layout.php';