<?php
declare(strict_types=1);

require __DIR__ . '/inc/submenu.php';

$host = '127.0.0.1';
$services = [
    ['name' => 'FrankenPHP homepage', 'url' => "http://{$host}:8088/index.php", 'notes' => 'Required public-local entry point'],
    ['name' => 'Jupyter', 'url' => "http://{$host}:8888/", 'notes' => 'Notebook UI with live repo-backed workspace'],
    ['name' => 'Airflow Web', 'url' => "http://{$host}:8080/", 'notes' => 'Workflow UI'],
    ['name' => 'MinIO Console', 'url' => "http://{$host}:9001/", 'notes' => 'Object storage admin UI'],
    ['name' => 'MinIO API', 'url' => "http://{$host}:9000/", 'notes' => 'S3-compatible endpoint'],
    ['name' => 'Metabase', 'url' => "http://{$host}:3000/", 'notes' => 'Query and exploration UI'],
    ['name' => 'Trino', 'url' => "http://{$host}:8085/ui/", 'notes' => 'Query engine web UI'],
    ['name' => 'Lakekeeper', 'url' => "http://{$host}:8181/", 'notes' => 'Catalog API root'],
    ['name' => 'Elasticsearch API', 'url' => "http://{$host}:9200/", 'notes' => 'Internal local search API endpoint'],
    ['name' => 'Kibana', 'url' => "http://{$host}:5601/", 'notes' => 'Internal local search inspection UI'],
    ['name' => 'CloudBeaver', 'url' => "http://{$host}:8978/", 'notes' => 'Browser SQL utility surface'],
    ['name' => 'AI Access API', 'url' => "http://{$host}:8000/health", 'notes' => 'Deterministic NL-to-SQL over demo.asx_ohlcv_summary'],
    ['name' => 'Open WebUI', 'url' => "http://{$host}:8090/", 'notes' => 'ASX OHLCV Assistant — subordinate browser chat surface'],
];

$mountedPath = '/app/public';
$now = (new DateTimeImmutable('now'))->format(DateTimeInterface::ATOM);

ob_start();
?>
<h1>Knowledge Lake Local Runtime</h1>
<?php render_primary_submenu('services'); ?>

<p>
  <strong>Time:</strong> <code><?= htmlspecialchars($now) ?></code><br>
  FrankenPHP is serving this page from the live repo-backed content path at <code><?= htmlspecialchars($mountedPath) ?></code>.
</p>

<p>
  Edit files under <code>runtime/shared/php/</code>, refresh the browser, and the change should appear immediately while the Minikube mount remains healthy.
</p>

<div class="card">
  <h2>Local Services</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 220px;">Service</th>
        <th>URL</th>
        <th style="width: 260px;">Notes</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($services as $service): ?>
        <tr>
          <td><strong><?= htmlspecialchars($service['name']) ?></strong></td>
          <td><a href="<?= htmlspecialchars($service['url']) ?>" target="_blank" rel="noopener"><?= htmlspecialchars($service['url']) ?></a></td>
          <td><?= htmlspecialchars($service['notes']) ?></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
 </div>

<div class="card">
  <h2>Runtime Notes</h2>
  <p>
    This runtime preserves the existing Knowledge Lake service set while keeping FrankenPHP as a narrow Foundation-compatible local entry surface.
  </p>
  <p>
    The local-development path remains intentionally simple: FrankenPHP content under <code>runtime/shared/php/</code> is repo-backed and live-mounted, the Jupyter notebook workspace under <code>runtime/shared/notebooks/</code> remains writable, and local working files under <code>runtime/shared/data/</code> stay visible to the running stack.
  </p>
  <p>
    Use <a href="/health.php">/health.php</a> to check in-cluster service reachability from the FrankenPHP pod, confirm that the content mount is present, and confirm that the local data mount is writable.
  </p>
  <p>
    Use <a href="/solutions.php">/solutions.php</a> to browse dynamically discovered runtime solution pages from the live-mounted <code>runtime/shared/php/solutions/</code> directory.
  </p>
  <p>
    The local launcher now guarantees only that this FrankenPHP entry point and Jupyter are reachable. Other linked services may still be starting when the launcher returns, so use the health page and local <code>kubectl</code> status checks while they warm.
  </p>
</div>
<?php
$content = ob_get_clean();
$page_title = 'Knowledge Lake Local Runtime';
$page_description = 'FrankenPHP landing page for the local Knowledge Lake Kubernetes scaffold.';
require __DIR__ . '/inc/layout.php';
