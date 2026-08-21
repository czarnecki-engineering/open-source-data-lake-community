<?php
declare(strict_types=1);

require __DIR__ . '/../inc/submenu.php';

/*
Solution Title: Runtime Diagnostics
Solution Summary: Read-only display of local Kubernetes resource usage — pods, PVCs, node memory, and Docker container stats — collected by collect-runtime-diagnostics.sh.
*/

// Data comes from a pre-generated JSON file. PHP does not execute kubectl, docker, or minikube.
$dataPath = '/app/data/runtime_diagnostics.json';

function rd_read_diagnostics(string $path): ?array
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

function rd_age_label(string $iso8601): string
{
    $collected = DateTimeImmutable::createFromFormat(DateTimeInterface::ATOM, $iso8601, new DateTimeZone('UTC'));
    if ($collected === false) {
        return 'unknown age';
    }

    $now = new DateTimeImmutable('now', new DateTimeZone('UTC'));
    $diff = $now->getTimestamp() - $collected->getTimestamp();

    if ($diff < 60) {
        return "{$diff}s ago";
    }
    if ($diff < 3600) {
        return floor($diff / 60) . 'm ago';
    }
    if ($diff < 86400) {
        return floor($diff / 3600) . 'h ago';
    }

    return floor($diff / 86400) . 'd ago';
}

function rd_pill_class(bool $ok): string
{
    return $ok ? 'good' : 'bad';
}

function rd_phase_pill(string $phase): string
{
    $class = match (strtolower($phase)) {
        'running', 'bound' => 'good',
        'pending'          => 'warn',
        default            => 'bad',
    };
    return '<span class="pill ' . $class . '">' . htmlspecialchars($phase) . '</span>';
}

function rd_state_pill(string $state): string
{
    $class = str_starts_with($state, 'running') ? 'good' : (str_starts_with($state, 'waiting') ? 'warn' : 'bad');
    return '<span class="pill ' . $class . '">' . htmlspecialchars($state) . '</span>';
}

$diag = rd_read_diagnostics($dataPath);

ob_start();
?>
<h1>Runtime Diagnostics</h1>
<?php render_primary_submenu('solutions'); ?>

<p>
  Read-only display of local Kubernetes resource state. Data is collected externally by
  <code>runtime/knowledge-lake/collect-runtime-diagnostics.sh</code> and written to
  <code>runtime/shared/data/runtime_diagnostics.json</code>.
  PHP does not execute cluster commands.
</p>

<?php if ($diag === null): ?>
  <div class="card">
    <h2>No Diagnostics Data Available</h2>
    <p>The diagnostics file was not found at <code><?= htmlspecialchars($dataPath) ?></code>.</p>
    <p>Run the collector from the repository root, then refresh this page:</p>
    <pre>bash runtime/knowledge-lake/collect-runtime-diagnostics.sh</pre>
    <p>The file will be written to <code>runtime/shared/data/runtime_diagnostics.json</code> and picked up from <code>/app/data/runtime_diagnostics.json</code> inside the FrankenPHP container via the live data mount.</p>
  </div>
<?php else: ?>

<?php
$collectedAt = $diag['collected_at'] ?? 'unknown';
$namespace   = $diag['namespace']    ?? 'unknown';
$pods        = $diag['pods']         ?? [];
$pvcs        = $diag['pvcs']         ?? [];
$nodeInfo    = $diag['node']         ?? [];
$dockerStats = $diag['docker_stats'] ?? [];
$diagErrors  = $diag['errors']       ?? [];

$totalPods    = count($pods);
$readyPods    = count(array_filter($pods, fn($p) => $p['ready'] ?? false));
$totalRestarts = array_sum(array_map(
    fn($p) => array_sum(array_column($p['containers'] ?? [], 'restart_count')),
    $pods
));
$boundPvcs = count(array_filter($pvcs, fn($v) => ($v['phase'] ?? '') === 'Bound'));
?>

<div class="card">
  <h2>Collection Summary</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th>Field</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Collected at</strong></td>
        <td>
          <code><?= htmlspecialchars($collectedAt) ?></code>
          (<?= htmlspecialchars(rd_age_label($collectedAt)) ?>)
        </td>
      </tr>
      <tr>
        <td><strong>Namespace</strong></td>
        <td><code><?= htmlspecialchars($namespace) ?></code></td>
      </tr>
      <tr>
        <td><strong>Pods ready</strong></td>
        <td>
          <span class="pill <?= rd_pill_class($readyPods === $totalPods && $totalPods > 0) ?>">
            <?= (int) $readyPods ?> / <?= (int) $totalPods ?>
          </span>
        </td>
      </tr>
      <tr>
        <td><strong>Total restart count</strong></td>
        <td>
          <span class="pill <?= rd_pill_class($totalRestarts === 0) ?>">
            <?= (int) $totalRestarts ?>
          </span>
        </td>
      </tr>
      <tr>
        <td><strong>PVCs bound</strong></td>
        <td>
          <span class="pill <?= rd_pill_class($boundPvcs === count($pvcs) && count($pvcs) > 0) ?>">
            <?= (int) $boundPvcs ?> / <?= count($pvcs) ?>
          </span>
        </td>
      </tr>
      <?php if ($diagErrors !== []): ?>
      <tr>
        <td><strong>Collector warnings</strong></td>
        <td><span class="pill warn"><?= count($diagErrors) ?></span></td>
      </tr>
      <?php endif; ?>
    </tbody>
  </table>
</div>

<?php if ($nodeInfo !== []): ?>
<div class="card">
  <h2>Node Memory</h2>
  <?php
  $capacity    = $nodeInfo['capacity']    ?? [];
  $allocatable = $nodeInfo['allocatable'] ?? [];
  $freeOutput  = $nodeInfo['memory_free_output'] ?? null;
  $descAlloc   = $nodeInfo['describe_allocated'] ?? null;
  ?>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th>Metric</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Node name</strong></td>
        <td><code><?= htmlspecialchars($nodeInfo['name'] ?? 'unknown') ?></code></td>
      </tr>
      <tr>
        <td><strong>CPU capacity</strong></td>
        <td><code><?= htmlspecialchars($capacity['cpu'] ?? 'unknown') ?></code></td>
      </tr>
      <tr>
        <td><strong>CPU allocatable</strong></td>
        <td><code><?= htmlspecialchars($allocatable['cpu'] ?? 'unknown') ?></code></td>
      </tr>
      <tr>
        <td><strong>Memory capacity</strong></td>
        <td><code><?= htmlspecialchars($capacity['memory'] ?? 'unknown') ?></code></td>
      </tr>
      <tr>
        <td><strong>Memory allocatable</strong></td>
        <td><code><?= htmlspecialchars($allocatable['memory'] ?? 'unknown') ?></code></td>
      </tr>
    </tbody>
  </table>

  <?php if ($freeOutput !== null): ?>
    <p style="margin-top:1em"><strong>Node free -h (minikube ssh)</strong></p>
    <pre><?= htmlspecialchars($freeOutput) ?></pre>
  <?php endif; ?>

  <?php if ($descAlloc !== null): ?>
    <p style="margin-top:1em"><strong>Allocated resources (kubectl describe node)</strong></p>
    <pre><?= htmlspecialchars($descAlloc) ?></pre>
  <?php endif; ?>
</div>
<?php endif; ?>

<?php if ($pods !== []): ?>
<div class="card">
  <h2>Pod Health</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th>Pod</th>
        <th style="width: 100px;">Phase</th>
        <th style="width: 80px;">Ready</th>
        <th>Containers</th>
        <th style="width: 100px;">Restarts</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($pods as $pod): ?>
        <?php
        $podRestarts = array_sum(array_column($pod['containers'] ?? [], 'restart_count'));
        $podName     = $pod['name']  ?? '';
        $podPhase    = $pod['phase'] ?? 'Unknown';
        $podReady    = $pod['ready'] ?? false;
        $podContainers = $pod['containers'] ?? [];
        ?>
        <tr>
          <td>
            <code style="font-size: 0.85em;"><?= htmlspecialchars($podName) ?></code>
          </td>
          <td><?= rd_phase_pill($podPhase) ?></td>
          <td>
            <span class="pill <?= rd_pill_class($podReady) ?>"><?= $podReady ? 'YES' : 'NO' ?></span>
          </td>
          <td>
            <?php foreach ($podContainers as $c): ?>
              <div style="margin-bottom: 2px;">
                <code><?= htmlspecialchars($c['name'] ?? '') ?></code>
                <?= rd_state_pill($c['state'] ?? 'unknown') ?>
              </div>
            <?php endforeach; ?>
          </td>
          <td>
            <span class="pill <?= rd_pill_class($podRestarts === 0) ?>">
              <?= (int) $podRestarts ?>
            </span>
          </td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>
<?php elseif ($diag !== null): ?>
<div class="card">
  <h2>Pod Health</h2>
  <p>No pods found in namespace <code><?= htmlspecialchars($namespace) ?></code> at collection time.</p>
</div>
<?php endif; ?>

<?php if ($pvcs !== []): ?>
<div class="card">
  <h2>Persistent Volume Claims</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th>PVC Name</th>
        <th style="width: 100px;">Status</th>
        <th style="width: 100px;">Capacity</th>
        <th style="width: 100px;">Requested</th>
        <th>Access Modes</th>
        <th>Storage Class</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($pvcs as $pvc): ?>
        <tr>
          <td><code><?= htmlspecialchars($pvc['name'] ?? '') ?></code></td>
          <td><?= rd_phase_pill($pvc['phase'] ?? 'Unknown') ?></td>
          <td><code><?= htmlspecialchars($pvc['capacity'] ?? 'unknown') ?></code></td>
          <td><code><?= htmlspecialchars($pvc['requested'] ?? 'unknown') ?></code></td>
          <td><code><?= htmlspecialchars(implode(', ', $pvc['access_modes'] ?? [])) ?></code></td>
          <td><code><?= htmlspecialchars($pvc['storage_class'] ?? 'unknown') ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>
<?php endif; ?>

<?php if ($dockerStats !== []): ?>
<div class="card">
  <h2>Docker Container Stats</h2>
  <p>Resource usage at collection time. <code>minikube</code> is the cluster VM container; all Kubernetes workloads run inside it.</p>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th>Container</th>
        <th style="width: 110px;">CPU %</th>
        <th style="width: 180px;">Memory</th>
        <th style="width: 160px;">Net I/O</th>
        <th style="width: 160px;">Block I/O</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($dockerStats as $stat): ?>
        <tr>
          <td>
            <strong><?= htmlspecialchars($stat['name'] ?? '') ?></strong><br>
            <code style="font-size:0.8em;"><?= htmlspecialchars(substr((string) ($stat['id'] ?? ''), 0, 12)) ?></code>
          </td>
          <td><code><?= htmlspecialchars($stat['cpu_perc']  ?? '') ?></code></td>
          <td><code><?= htmlspecialchars($stat['mem_usage'] ?? '') ?></code></td>
          <td><code><?= htmlspecialchars($stat['net_io']    ?? '') ?></code></td>
          <td><code><?= htmlspecialchars($stat['block_io']  ?? '') ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>
<?php endif; ?>

<?php if ($diagErrors !== []): ?>
<div class="card">
  <h2>Collector Warnings</h2>
  <p>These are non-fatal errors recorded by <code>collect-runtime-diagnostics.sh</code> during the last collection run. Sections with missing data will show as empty above.</p>
  <ul>
    <?php foreach ($diagErrors as $err): ?>
      <li><code><?= htmlspecialchars((string) $err) ?></code></li>
    <?php endforeach; ?>
  </ul>
</div>
<?php endif; ?>

<?php endif; // $diag !== null ?>
<?php
$content = ob_get_clean();
$page_title = 'Knowledge Lake Solution - Runtime Diagnostics';
$page_description = 'Read-only display of local Kubernetes resource usage — pods, PVCs, node memory, and Docker container stats.';
require __DIR__ . '/../inc/layout.php';
