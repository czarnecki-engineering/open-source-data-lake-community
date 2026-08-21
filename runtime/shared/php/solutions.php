<?php
declare(strict_types=1);

require __DIR__ . '/inc/solutions.php';
require __DIR__ . '/inc/submenu.php';

$solutionsDir = __DIR__ . '/solutions';
$report = discovered_solutions_report($solutionsDir);
$entries = $report['entries'];
$warnings = $report['warnings'];
$enabledTags = enabled_solution_tags();
$relativeSolutionsDir = 'runtime/shared/php/solutions/';

ob_start();
?>
<h1>Solutions</h1>
<?php render_primary_submenu('solutions'); ?>

<p>
  Solution pages are discovered from <code><?= htmlspecialchars($relativeSolutionsDir) ?></code> using metadata comments near the top of each file.
  New solution pages can be added under that directory without modifying <code>solutions.php</code>.
</p>

<p>
  Discovery stays deterministic by scanning <code>*.php</code> files in lexical order and ignoring malformed pages safely.
</p>

<div class="card">
  <h2>Available Solutions</h2>
  <?php if ($entries === []): ?>
    <p>No valid solution pages were discovered in <code><?= htmlspecialchars($relativeSolutionsDir) ?></code>.</p>
  <?php else: ?>
    <table class="tiers-compare">
      <thead>
        <tr>
          <th style="width: 240px;">Title</th>
          <th>Summary</th>
          <th style="width: 160px;">Tag</th>
          <th style="width: 220px;">Link</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($entries as $entry): ?>
          <tr>
            <td><strong><?= htmlspecialchars($entry['title']) ?></strong></td>
            <td><?= htmlspecialchars($entry['summary']) ?></td>
            <td><?= htmlspecialchars((string) ($entry['tag'] ?? 'always')) ?></td>
            <td><a href="<?= htmlspecialchars($entry['url']) ?>"><?= htmlspecialchars($entry['url']) ?></a></td>
          </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  <?php endif; ?>
</div>

<div class="card">
  <h2>Discovery Rules</h2>
  <ul>
    <li>Each solution page should live under <code><?= htmlspecialchars($relativeSolutionsDir) ?></code>.</li>
    <li>Each page should include <code>Solution Title:</code> and <code>Solution Summary:</code> comments near the top of the file.</li>
    <li><code>Solution Tag:</code> remains supported for compatibility with the reference implementation.</li>
    <li>Malformed or disabled pages are skipped and reported below instead of breaking the index.</li>
  </ul>
  <?php if ($enabledTags === []): ?>
    <p><code>ENABLED_SOLUTION_TAGS</code> is unset, so only untagged pages are currently discoverable.</p>
  <?php else: ?>
    <p>Enabled tags: <code><?= htmlspecialchars(implode(', ', $enabledTags)) ?></code></p>
  <?php endif; ?>
</div>

<?php if ($warnings !== []): ?>
  <div class="card">
    <h2>Discovery Warnings</h2>
    <ul>
      <?php foreach ($warnings as $warning): ?>
        <li><?= htmlspecialchars($warning) ?></li>
      <?php endforeach; ?>
    </ul>
  </div>
<?php endif; ?>
<?php
$content = ob_get_clean();
$page_title = 'Knowledge Lake Local Runtime Solutions';
$page_description = 'Dynamically discovered local runtime solution pages served by FrankenPHP.';
require __DIR__ . '/inc/layout.php';
