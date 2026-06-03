<?php
declare(strict_types=1);

require '/app/public/onlyoffice/onlyoffice.php';

$pageTitle = 'ONLYOFFICE Documents';
$pageDescription = 'MinIO-backed ONLYOFFICE document catalogue.';
$catalogue = null;
$errorMessage = null;

try {
  $catalogue = onlyoffice_minio_document_catalogue();
} catch (Throwable $exception) {
  $errorMessage = $exception->getMessage();
}
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title><?= htmlspecialchars($pageTitle) ?></title>
  <meta name="description" content="<?= htmlspecialchars($pageDescription) ?>">
  <style>
    body {
      margin: 0;
      background: #0b0f14;
      color: #e6edf3;
      font: 16px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", Arial, sans-serif;
    }

    a {
      color: #58a6ff;
    }

    .shell {
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }

    .topbar {
      display: flex;
      flex-wrap: wrap;
      gap: 12px 20px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 24px;
    }

    .topbar-links {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
    }

    .card {
      background: #141b23;
      border: 1px solid #1f2937;
      border-radius: 12px;
      padding: 18px 20px;
      margin-bottom: 20px;
    }

    .meta-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px 20px;
    }

    .meta-grid code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th,
    td {
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid #1f2937;
      vertical-align: top;
    }

    th {
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #9fb0c3;
    }

    td code {
      word-break: break-word;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }

    .empty {
      color: #c5d1de;
    }

    .status-note {
      margin: 0;
      color: #c5d1de;
    }

    @media (max-width: 720px) {
      table,
      thead,
      tbody,
      th,
      td,
      tr {
        display: block;
      }

      thead {
        display: none;
      }

      tr {
        border-bottom: 1px solid #1f2937;
        padding: 10px 0;
      }

      td {
        border: 0;
        padding: 6px 0;
      }

      td::before {
        content: attr(data-label) ": ";
        display: inline-block;
        min-width: 112px;
        color: #9fb0c3;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <div class="topbar">
      <div>
        <h1 style="margin:0 0 6px">ONLYOFFICE Documents</h1>
        <p class="status-note">Phase 2A MinIO-backed document catalogue for the existing ONLYOFFICE prototype workflow.</p>
      </div>
      <div class="topbar-links">
        <a href="/solutions/onlyoffice_prototype.php">Prototype page</a>
        <a href="/onlyoffice/editor.php">Standalone editor</a>
      </div>
    </div>

<?php if ($errorMessage !== null): ?>
    <div class="card">
      <h2 style="margin-top:0">Connection Error</h2>
      <p><strong>MinIO catalogue lookup failed:</strong> <?= htmlspecialchars($errorMessage) ?></p>
      <p class="status-note">Endpoint: <code><?= htmlspecialchars(onlyoffice_minio_endpoint()) ?></code></p>
    </div>
<?php else: ?>
    <div class="card">
      <h2 style="margin-top:0">Catalogue Summary</h2>
      <div class="meta-grid">
        <div><strong>MinIO Endpoint</strong><br><code><?= htmlspecialchars(onlyoffice_minio_endpoint()) ?></code></div>
        <div><strong>Available Buckets</strong><br><code><?= htmlspecialchars(implode(', ', $catalogue['available_buckets'])) ?></code></div>
        <div><strong>Preferred Bucket</strong><br><code><?= htmlspecialchars($catalogue['preferred_bucket']) ?></code></div>
        <div><strong>Listing Scope</strong><br><code><?= htmlspecialchars(implode(', ', $catalogue['source_buckets'])) ?></code></div>
      </div>
    </div>

    <div class="card">
      <h2 style="margin-top:0">Documents</h2>
<?php if ($catalogue['documents'] === []): ?>
      <p class="empty">No Office-compatible objects were found in the selected MinIO scope.</p>
<?php else: ?>
      <table>
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
            <td data-label="Filename"><?= htmlspecialchars(basename($document['key'])) ?></td>
            <td data-label="Bucket"><code><?= htmlspecialchars($document['bucket']) ?></code></td>
            <td data-label="Object Key"><code><?= htmlspecialchars($document['key']) ?></code></td>
            <td data-label="Size"><?= htmlspecialchars(onlyoffice_format_bytes($document['size'])) ?></td>
            <td data-label="Last Modified"><?= htmlspecialchars(onlyoffice_format_timestamp($document['last_modified'])) ?></td>
            <td data-label="Action"><a href="<?= htmlspecialchars(onlyoffice_documents_open_url($document)) ?>">Open</a></td>
          </tr>
<?php endforeach; ?>
        </tbody>
      </table>
      <p class="status-note">
        The Open action passes the selected MinIO bucket, object key, and revision metadata directly to the editor route.
      </p>
<?php endif; ?>
    </div>
<?php endif; ?>
  </div>
</body>
</html>
