<?php
declare(strict_types=1);

function solution_metadata(string $path): array
{
  $source = file_get_contents($path);
  if ($source === false) {
    return [];
  }

  $title = null;
  $summary = null;
  $tag = null;

  if (preg_match('/Solution Title:\s*(.+)/', $source, $matches) === 1) {
    $title = trim($matches[1]);
  }

  if (preg_match('/Solution Summary:\s*(.+)/', $source, $matches) === 1) {
    $summary = trim($matches[1]);
  }

  if (preg_match('/Solution Tag:\s*(.+)/', $source, $matches) === 1) {
    $tag = trim($matches[1]);
  }

  return [
    'title' => $title,
    'summary' => $summary,
    'tag' => $tag,
  ];
}

$solutionsDir = __DIR__ . '/solutions';
$entries = [];
$enabledTags = array_filter(array_map('trim', explode(',', (string) getenv('ENABLED_SOLUTION_TAGS'))));
$enabledTagLookup = array_fill_keys($enabledTags, true);

if (is_dir($solutionsDir)) {
  $files = glob($solutionsDir . '/*.php') ?: [];
  sort($files);

  foreach ($files as $path) {
    $basename = basename($path);
    $metadata = solution_metadata($path);
    $tag = $metadata['tag'] ?? null;

    if ($tag !== null && $tag !== '' && !isset($enabledTagLookup[$tag])) {
      continue;
    }

    $entries[] = [
      'file' => $basename,
      'url' => '/solutions/' . $basename,
      'title' => $metadata['title'] ?? pathinfo($basename, PATHINFO_FILENAME),
      'summary' => $metadata['summary'] ?? 'No summary metadata provided.',
      'tag' => $tag,
    ];
  }
}

$page_title = 'Solutions';
$page_description = 'Installed solution pages for My Data Lake.';

ob_start();
?>
<h1>Solutions</h1>
<h3><a href="/index.php">Services</a> &nbsp; <a href="/health.php">Health</a> &nbsp; Solutions</h3>

<p>
  Solution pages are discovered from <code>php/solutions/</code>.
  Each page should define <code>Solution Title:</code> and <code>Solution Summary:</code> metadata near the top of the file.
  Overlay-specific pages can also define <code>Solution Tag:</code> and are shown only when that tag is enabled in the PHP container.
</p>

<div class="card">
  <h2>Available Solutions</h2>
  <?php if ($entries === []): ?>
    <p>No solution pages found.</p>
  <?php else: ?>
    <table class="tiers-compare">
      <thead>
        <tr>
          <th style="width: 260px;">Title</th>
          <th>Summary</th>
          <th style="width: 220px;">Link</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($entries as $entry): ?>
          <tr>
            <td><strong><?= htmlspecialchars($entry['title']) ?></strong></td>
            <td><?= htmlspecialchars($entry['summary']) ?></td>
            <td><a href="<?= htmlspecialchars($entry['url']) ?>"><?= htmlspecialchars($entry['url']) ?></a></td>
          </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  <?php endif; ?>
</div>
<?php
$content = ob_get_clean();
require __DIR__ . '/inc/layout.php';
