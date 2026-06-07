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

  .onlyoffice-kv-table th,
  .onlyoffice-kv-table td,
  .onlyoffice-documents-table th,
  .onlyoffice-documents-table td {
    vertical-align: top;
  }

  .onlyoffice-kv-table th {
    width: 220px;
  }

  .onlyoffice-kv-table code,
  .onlyoffice-documents-table code {
    word-break: break-word;
  }
</style>

<h1>ONLYOFFICE Documents</h1>
<h3><a href="/index.php">Services</a> &nbsp; <a href="/health.php">Health</a> &nbsp; <a href="/solutions.php">Solutions</a></h3>

<p>
  This page lists Office-compatible objects found in MinIO and opens the selected document in the existing ONLYOFFICE editor route.
</p>

<p class="onlyoffice-links">
  <a href="/solutions/onlyoffice_prototype.php">Prototype page</a>
  <a href="/onlyoffice/editor.php">Standalone editor</a>
</p>

<?php if ($errorMessage !== null): ?>
  <div class="card">
    <h2>Connection Error</h2>
    <p><?= htmlspecialchars($errorMessage) ?></p>
    <p><strong>MinIO endpoint:</strong> <code><?= htmlspecialchars(onlyoffice_minio_endpoint()) ?></code></p>
    <p class="onlyoffice-links">
      <a href="/solutions/onlyoffice_prototype.php">Back to prototype</a>
      <a href="/index.php">Services</a>
      <a href="/solutions.php">Solutions</a>
    </p>
  </div>
<?php else: ?>
  <div class="card">
    <h2>Catalogue Summary</h2>
    <table class="tiers-compare onlyoffice-kv-table">
      <tbody>
        <tr>
          <th>MinIO Endpoint</th>
          <td><code><?= htmlspecialchars(onlyoffice_minio_endpoint()) ?></code></td>
        </tr>
        <tr>
          <th>Available Buckets</th>
          <td><code><?= htmlspecialchars($catalogue['available_buckets'] === [] ? 'none detected' : implode(', ', $catalogue['available_buckets'])) ?></code></td>
        </tr>
        <tr>
          <th>Preferred Bucket</th>
          <td><code><?= htmlspecialchars($catalogue['preferred_bucket']) ?></code></td>
        </tr>
        <tr>
          <th>Listing Scope</th>
          <td><code><?= htmlspecialchars($catalogue['source_buckets'] === [] ? 'none selected' : implode(', ', $catalogue['source_buckets'])) ?></code></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Documents</h2>
<?php if ($catalogue['documents'] === []): ?>
    <p>No supported Office documents were found in the selected MinIO scope.</p>
    <p>
      Supported document types: <code><?= htmlspecialchars(implode(', ', onlyoffice_supported_document_extensions())) ?></code>
    </p>
<?php else: ?>
    <table class="tiers-compare onlyoffice-documents-table">
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
          <td><a href="<?= htmlspecialchars(onlyoffice_documents_open_url($document)) ?>">Open in ONLYOFFICE</a></td>
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
