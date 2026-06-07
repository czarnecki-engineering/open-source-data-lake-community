<?php
declare(strict_types=1);

require '/app/public/onlyoffice/onlyoffice.php';

$page_title = 'ONLYOFFICE Documents';
$page_description = 'MinIO-backed ONLYOFFICE document catalogue.';
$catalogue = null;
$errorMessage = null;

try {
  $catalogue = onlyoffice_minio_document_catalogue();
} catch (Throwable $exception) {
  $errorMessage = $exception->getMessage();
}
ob_start();
?>
<style>
  .onlyoffice-links {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin: 0 0 24px;
  }

  .onlyoffice-meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px 20px;
  }

  .onlyoffice-meta-grid code {
    word-break: break-word;
  }
</style>

<h1>ONLYOFFICE Documents</h1>
<h3><a href="/index.php">Services</a> &nbsp; <a href="/health.php">Health</a> &nbsp; <a href="/solutions.php">Solutions</a></h3>

<p>
  Phase 2A MinIO-backed document catalogue for the existing ONLYOFFICE prototype workflow.
</p>

<p class="onlyoffice-links">
  <a href="/solutions/onlyoffice_prototype.php">Prototype page</a>
  <a href="/onlyoffice/editor.php">Standalone editor</a>
</p>

<?php if ($errorMessage !== null): ?>
  <div class="card">
    <h2>Connection Error</h2>
    <p><strong>MinIO catalogue lookup failed:</strong> <?= htmlspecialchars($errorMessage) ?></p>
    <p>Endpoint: <code><?= htmlspecialchars(onlyoffice_minio_endpoint()) ?></code></p>
  </div>
<?php else: ?>
  <div class="card">
    <h2>Catalogue Summary</h2>
    <div class="onlyoffice-meta-grid">
      <div><strong>MinIO Endpoint</strong><br><code><?= htmlspecialchars(onlyoffice_minio_endpoint()) ?></code></div>
      <div><strong>Available Buckets</strong><br><code><?= htmlspecialchars(implode(', ', $catalogue['available_buckets'])) ?></code></div>
      <div><strong>Preferred Bucket</strong><br><code><?= htmlspecialchars($catalogue['preferred_bucket']) ?></code></div>
      <div><strong>Listing Scope</strong><br><code><?= htmlspecialchars(implode(', ', $catalogue['source_buckets'])) ?></code></div>
    </div>
  </div>

  <div class="card">
    <h2>Documents</h2>
<?php if ($catalogue['documents'] === []): ?>
    <p>No Office-compatible objects were found in the selected MinIO scope.</p>
<?php else: ?>
    <table class="tiers-compare">
      <thead>
        <tr>
          <th>Filename</th>
          <th>Bucket</th>
          <th>Object Key</th>
          <th>Size</th>
          <th>Last Modified</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
<?php foreach ($catalogue['documents'] as $document): ?>
        <tr>
          <td><strong><?= htmlspecialchars(basename($document['key'])) ?></strong></td>
          <td><code><?= htmlspecialchars($document['bucket']) ?></code></td>
          <td><code><?= htmlspecialchars($document['key']) ?></code></td>
          <td><?= htmlspecialchars(onlyoffice_format_bytes($document['size'])) ?></td>
          <td><?= htmlspecialchars(onlyoffice_format_timestamp($document['last_modified'])) ?></td>
          <td><a href="<?= htmlspecialchars(onlyoffice_documents_open_url($document)) ?>">Open</a></td>
        </tr>
<?php endforeach; ?>
      </tbody>
    </table>
    <p>
      The Open action passes the selected MinIO bucket, object key, and revision metadata directly to the editor route.
    </p>
<?php endif; ?>
  </div>
<?php endif; ?>
<?php
$content = ob_get_clean();
require '/app/public/inc/layout.php';
