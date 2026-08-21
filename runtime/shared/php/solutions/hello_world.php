<?php
declare(strict_types=1);

require __DIR__ . '/../inc/submenu.php';

/*
Solution Title: Hello World
Solution Summary: Minimal deterministic runtime validation page for FrankenPHP, live mounts, and basic PHP execution.
*/

function safe_command_output(array $command): array
{
    $escaped = array_map('escapeshellarg', $command);
    $commandLine = implode(' ', $escaped) . ' 2>&1';
    $output = shell_exec($commandLine);

    return [
        'command' => implode(' ', $command),
        'output' => $output === null ? 'unavailable' : trim($output),
    ];
}

$utcNow = new DateTimeImmutable('now', new DateTimeZone('UTC'));
$pathChecks = [
    '/app/public' => '/app/public',
    '/app/public/solutions' => '/app/public/solutions',
    '/app/data' => '/app/data',
    __FILE__ => __FILE__,
];

$runtimeInfo = [
    'PHP version' => PHP_VERSION,
    'SAPI' => PHP_SAPI,
    'Current script' => __FILE__,
    'Current directory' => __DIR__,
    'Hostname env' => (string) getenv('HOSTNAME'),
    'curl extension' => extension_loaded('curl') ? 'loaded' : 'missing',
];

$commandOutputs = [
    safe_command_output(['/bin/date', '-u']),
    safe_command_output(['/bin/hostname']),
];

ob_start();
?>
<h1>Hello World</h1>
<?php render_primary_submenu('solutions'); ?>

<p>
  This is the narrow deterministic FrankenPHP validation page for the current local runtime. It reads only local runtime state and mounted paths.
</p>

<p>
  <strong>UTC time from PHP:</strong> <code><?= htmlspecialchars($utcNow->format(DateTimeInterface::ATOM)) ?></code>
</p>

<div class="card">
  <h2>Runtime Signals</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 220px;">Signal</th>
        <th>Value</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($runtimeInfo as $label => $value): ?>
        <tr>
          <td><strong><?= htmlspecialchars($label) ?></strong></td>
          <td><code><?= htmlspecialchars((string) $value) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Mounted Path Visibility</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th>Path</th>
        <th style="width: 140px;">Exists</th>
        <th style="width: 140px;">Writable</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($pathChecks as $label => $path): ?>
        <tr>
          <td><code><?= htmlspecialchars($label) ?></code></td>
          <td><span class="pill <?= file_exists($path) ? 'good' : 'bad' ?>"><?= file_exists($path) ? 'YES' : 'NO' ?></span></td>
          <td><span class="pill <?= is_writable($path) ? 'warn' : 'good' ?>"><?= is_writable($path) ? 'WRITABLE' : 'READ ONLY' ?></span></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Safe Command Output</h2>
  <p>These commands are fixed and read-only. They accept no user input.</p>
  <?php foreach ($commandOutputs as $item): ?>
    <p><strong><code><?= htmlspecialchars($item['command']) ?></code></strong></p>
    <pre><?= htmlspecialchars($item['output']) ?></pre>
  <?php endforeach; ?>
</div>
<?php
$content = ob_get_clean();
$page_title = 'Knowledge Lake Solution - Hello World';
$page_description = 'Minimal deterministic FrankenPHP runtime validation page.';
require __DIR__ . '/../inc/layout.php';
