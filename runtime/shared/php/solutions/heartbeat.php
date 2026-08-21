<?php
declare(strict_types=1);

require __DIR__ . '/../inc/submenu.php';

/*
Solution Title: Heartbeat
Solution Summary: Read-only heartbeat solution page that collates the deterministic Airflow, MinIO, Iceberg, Trino, notebook, and local summary slice.
*/

function heartbeat_read_json_file(string $path): ?array
{
    if (!is_file($path)) {
        return null;
    }

    $raw = file_get_contents($path);
    if ($raw === false) {
        return null;
    }

    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : null;
}

$summaryPath = '/app/data/heartbeat_summary.json';
$configPath = '/app/config/dags/heartbeat.json';
$notebookPath = 'runtime/shared/notebooks/heartbeat_analysis.ipynb';
$expectedPaths = [
    'Raw prefix' => 's3://raw/reference/heartbeat/events/',
    'Conformed prefix' => 's3://conformed/reference/heartbeat/events/',
    'Curated summary object' => 's3://curated/reference/heartbeat/latest/heartbeat_summary.json',
    'Expected Trino table' => 'demo.heartbeat_events',
    'Expected Trino query' => 'SELECT event_id, latest_event_timestamp, latest_message FROM demo.heartbeat_events ORDER BY latest_event_timestamp DESC LIMIT 20',
];
$summaryPayload = heartbeat_read_json_file($summaryPath);
$configPayload = heartbeat_read_json_file($configPath);
$implementationChecks = [
    ['label' => 'Config present in mounted config path', 'status' => $configPayload !== null, 'path' => $configPath],
    ['label' => 'Raw DAG implemented', 'status' => true, 'path' => 'runtime/shared/dags/heartbeat_raw.py'],
    ['label' => 'Conformed DAG implemented', 'status' => true, 'path' => 'runtime/shared/dags/heartbeat_raw_to_conformed.py'],
    ['label' => 'Curated DAG implemented', 'status' => true, 'path' => 'runtime/shared/dags/heartbeat_conformed_to_curated.py'],
    ['label' => 'Iceberg/Trino DAG implemented', 'status' => true, 'path' => 'runtime/shared/dags/heartbeat_curated_to_iceberg.py'],
    ['label' => 'Notebook implemented', 'status' => true, 'path' => $notebookPath],
    ['label' => 'PHP solution implemented', 'status' => true, 'path' => 'runtime/shared/php/solutions/heartbeat.php'],
];
$runtimeChecks = [
    ['label' => 'Notebook summary present', 'status' => is_file($summaryPath), 'path' => $summaryPath],
];
$warnings = [];

if ($configPayload === null) {
    $warnings[] = 'Heartbeat config is not currently readable from /app/config/dags/heartbeat.json.';
}

if ($summaryPayload === null) {
    $warnings[] = 'Notebook summary is missing or unreadable at /app/data/heartbeat_summary.json. Run the notebook after the Airflow heartbeat DAG chain completes.';
}

ob_start();
?>
<h1>Heartbeat</h1>
<?php render_primary_submenu('solutions'); ?>

<p>
  This page is a read-only operational view of the deterministic heartbeat solution slice. It does not trigger Airflow, mutate MinIO, or query Trino directly.
</p>

<div class="card">
  <h2>Implementation Checklist</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 280px;">Stage</th>
        <th style="width: 140px;">Status</th>
        <th>Observed Path</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($implementationChecks as $row): ?>
        <tr>
          <td><strong><?= htmlspecialchars($row['label']) ?></strong></td>
          <td><span class="pill <?= $row['status'] ? 'good' : 'bad' ?>"><?= $row['status'] ? 'PRESENT' : 'MISSING' ?></span></td>
          <td><code><?= htmlspecialchars($row['path']) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Runtime Validation Checklist</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 280px;">Runtime Artifact</th>
        <th style="width: 140px;">Status</th>
        <th>Observed Path</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($runtimeChecks as $row): ?>
        <tr>
          <td><strong><?= htmlspecialchars($row['label']) ?></strong></td>
          <td><span class="pill <?= $row['status'] ? 'good' : 'bad' ?>"><?= $row['status'] ? 'PRESENT' : 'MISSING' ?></span></td>
          <td><code><?= htmlspecialchars($row['path']) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Expected Runtime Artifacts</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 220px;">Artifact</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($expectedPaths as $label => $value): ?>
        <tr>
          <td><strong><?= htmlspecialchars($label) ?></strong></td>
          <td><code><?= htmlspecialchars($value) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Heartbeat Config</h2>
  <?php if ($configPayload === null): ?>
    <p>Heartbeat config is not currently readable from <code><?= htmlspecialchars($configPath) ?></code>.</p>
  <?php else: ?>
    <pre><?= htmlspecialchars(json_encode($configPayload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></pre>
  <?php endif; ?>
</div>

<div class="card">
  <h2>Notebook Summary</h2>
  <?php if ($summaryPayload === null): ?>
    <p>The notebook summary file is not currently available at <code><?= htmlspecialchars($summaryPath) ?></code>.</p>
  <?php else: ?>
    <pre><?= htmlspecialchars(json_encode($summaryPayload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></pre>
  <?php endif; ?>
</div>

<div class="card">
  <h2>Architecture</h2>
  <ul>
    <li>Airflow orchestrates the workflow.</li>
    <li>MinIO is the object-store authority for <code>raw</code>, <code>conformed</code>, and <code>curated</code>.</li>
    <li>Lakekeeper governs the Iceberg catalog path.</li>
    <li>Trino is the accepted query boundary.</li>
    <li>This PHP page is read-only and observational.</li>
  </ul>
</div>

<div class="card">
  <h2>Normal Operation</h2>
  <ul>
    <li>Trigger the four Airflow DAGs in order.</li>
    <li>Run the notebook.</li>
    <li>Inspect this page.</li>
    <li>Expected artifacts: raw heartbeat JSON, conformed heartbeat JSON, curated summary JSON, Iceberg materialization into <code>demo.heartbeat_events</code>, notebook summary at <code>/app/data/heartbeat_summary.json</code>.</li>
  </ul>
</div>

<div class="card">
  <h2>Prerequisites</h2>
  <ul>
    <li>The validated local runtime must already be running through <code>runtime/knowledge-lake/start-k8s.sh</code>.</li>
    <li>The foreground Minikube repo mount must remain healthy.</li>
    <li>Airflow, MinIO, Lakekeeper, Trino, Jupyter, and FrankenPHP must all be available.</li>
    <li>The notebook must be run after the Airflow heartbeat chain if this page is expected to display the local summary payload.</li>
  </ul>
</div>

<div class="card">
  <h2>FAQs</h2>
  <p><strong>Why does this page read config directly but not DAG or notebook files?</strong><br>The local overlay now mounts the single repo-visible config tree into the containers that need it as the accepted config-first pattern. DAG and notebook source trees remain outside the FrankenPHP surface.</p>
  <p><strong>Why is the notebook summary the main runtime signal here?</strong><br>Because <code>/app/data</code> is the existing shared writable mount that both Jupyter and FrankenPHP can observe without widening the runtime architecture.</p>
  <p><strong>Does this page query Trino or mutate runtime state?</strong><br>No. It only renders expected paths and any summary JSON that already exists on the shared local data mount.</p>
</div>

<?php if ($warnings !== []): ?>
  <div class="card">
    <h2>Warnings</h2>
    <ul>
      <?php foreach ($warnings as $warning): ?>
        <li><?= htmlspecialchars($warning) ?></li>
      <?php endforeach; ?>
    </ul>
  </div>
<?php endif; ?>
<?php
$content = ob_get_clean();
$page_title = 'Knowledge Lake Solution - Heartbeat';
$page_description = 'Read-only heartbeat solution page for the deterministic local Knowledge Lake validation slice.';
require __DIR__ . '/../inc/layout.php';
