<?php
declare(strict_types=1);

require __DIR__ . '/../inc/submenu.php';

/*
Solution Title: Hello World Summary
Solution Summary: Displays the deterministic curated summary produced by the hello-world reference overlay.
Solution Tag: hello-world
*/

function hello_world_summary_path(): string
{
  return '/app/data/curated/hello_world/latest/summary.json';
}

function hello_world_read_summary(string $path): ?array
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

function hello_world_value(mixed $value): string
{
  if (is_array($value)) {
    return json_encode($value, JSON_UNESCAPED_SLASHES) ?: '[]';
  }
  return (string) $value;
}

$summaryPath = hello_world_summary_path();
$summary = hello_world_read_summary($summaryPath);

$page_title = 'Hello World Summary';
$page_description = 'Deterministic summary output for the hello-world reference overlay.';

ob_start();
?>
<h1>Hello World Summary</h1>
<?php render_primary_submenu('solutions'); ?>

<p>
  Curated summary path: <code><?= htmlspecialchars($summaryPath) ?></code>
</p>

<?php if ($summary === null): ?>
  <div class="card">
    <h2>Summary Not Available</h2>
    <p>The hello-world curated summary has not been generated yet.</p>
  </div>
<?php else: ?>
  <div class="card">
    <h2>Curated Summary</h2>
    <table class="tiers-compare">
      <thead>
        <tr>
          <th style="width: 220px;">Field</th>
          <th>Value</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($summary as $key => $value): ?>
          <tr>
            <td><strong><?= htmlspecialchars((string) $key) ?></strong></td>
            <td><code><?= htmlspecialchars(hello_world_value($value)) ?></code></td>
          </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  </div>
<?php endif; ?>
<?php
$content = ob_get_clean();
require __DIR__ . '/../inc/layout.php';
