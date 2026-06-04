<?php
declare(strict_types=1);

/*
Solution Title: ONLYOFFICE Prototype
Solution Summary: Static local-file ONLYOFFICE editor proof of concept for a single tracked DOCX document.
Solution Tag: onlyoffice
*/

require '/app/public/onlyoffice/onlyoffice.php';

$page_title = 'ONLYOFFICE Prototype';
$page_description = 'Static local-file ONLYOFFICE editor proof of concept.';

$browserHost = 'http://127.0.0.1';
$entryPoints = [
  [
    'name' => 'PHP Document Catalogue',
    'url' => $browserHost . ':8088/onlyoffice/documents.php',
    'purpose' => 'Browse MinIO-backed documents through the existing PHP catalogue.',
    'group' => 'Document Browsing And Editing',
  ],
  [
    'name' => 'Nextcloud Files',
    'url' => $browserHost . ':8091/',
    'purpose' => 'Browse and edit the same MinIO-backed documents through Nextcloud Files.',
    'group' => 'Document Browsing And Editing',
  ],
  [
    'name' => 'ONLYOFFICE Docs',
    'url' => $browserHost . ':8090/',
    'purpose' => 'Document server welcome and service endpoint. This is not a document library.',
    'group' => 'Operator And Service Entry Points',
  ],
  [
    'name' => 'MinIO Console',
    'url' => $browserHost . ':9001/',
    'purpose' => 'Operator view of the authoritative MinIO buckets and objects.',
    'group' => 'Operator And Service Entry Points',
  ],
];

$errorMessage = null;
$config = null;
$version = null;
$documentKey = null;

try {
  $version = onlyoffice_read_document_version();
  $documentKey = onlyoffice_document_key($version);
  $config = onlyoffice_editor_config();
} catch (Throwable $exception) {
  $errorMessage = $exception->getMessage();
}

ob_start();
?>
<h1>ONLYOFFICE Prototype</h1>
<h3><a href="/index.php">Services</a> &nbsp; <a href="/health.php">Health</a> &nbsp; <a href="/solutions.php">Solutions</a></h3>

<p>
  This Phase 1 prototype opens a single static local document from <code>./data/onlyoffice/</code> and saves edits back to the same path through the ONLYOFFICE callback handler.
</p>

<p>
  Phase 2A adds a MinIO-backed document catalogue at <a href="/onlyoffice/documents.php"><code>/onlyoffice/documents.php</code></a>. Opening from the catalogue now identifies documents by <code>s3://bucket/key</code>, while save-back to MinIO/S3 remains Phase 2C.
</p>

<div class="card">
  <h2>Document Browsing And Editing</h2>
  <p>
    Use these entry points to browse the same MinIO-backed documents through either the PHP catalogue or Nextcloud Files.
  </p>
  <table class="tiers-compare">
    <thead>
      <tr><th style="width: 220px;">Entry Point</th><th>URL</th><th>Purpose</th></tr>
    </thead>
    <tbody>
      <?php foreach ($entryPoints as $entryPoint): ?>
        <?php if ($entryPoint['group'] !== 'Document Browsing And Editing') { continue; } ?>
        <tr>
          <td><strong><?= htmlspecialchars($entryPoint['name']) ?></strong></td>
          <td><a href="<?= htmlspecialchars($entryPoint['url']) ?>" target="_blank" rel="noopener"><?= htmlspecialchars($entryPoint['url']) ?></a></td>
          <td><?= htmlspecialchars($entryPoint['purpose']) ?></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
  <p>
    Development Nextcloud login defaults: <strong>Username:</strong> <code>admin</code>, <strong>Password:</strong> <code>admin123</code>
  </p>
</div>

<div class="card">
  <h2>Operator And Service Entry Points</h2>
  <p>
    Use these links for service visibility and storage inspection rather than document browsing.
  </p>
  <table class="tiers-compare">
    <thead>
      <tr><th style="width: 220px;">Entry Point</th><th>URL</th><th>Purpose</th></tr>
    </thead>
    <tbody>
      <?php foreach ($entryPoints as $entryPoint): ?>
        <?php if ($entryPoint['group'] !== 'Operator And Service Entry Points') { continue; } ?>
        <tr>
          <td><strong><?= htmlspecialchars($entryPoint['name']) ?></strong></td>
          <td><a href="<?= htmlspecialchars($entryPoint['url']) ?>" target="_blank" rel="noopener"><?= htmlspecialchars($entryPoint['url']) ?></a></td>
          <td><?= htmlspecialchars($entryPoint['purpose']) ?></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<?php if ($errorMessage !== null): ?>
  <div class="card">
    <h2>Configuration Error</h2>
    <p><?= htmlspecialchars($errorMessage) ?></p>
  </div>
<?php else: ?>
  <div class="card">
    <h2>Document</h2>
    <p><strong>File:</strong> <code><?= htmlspecialchars(onlyoffice_document_relative_path()) ?></code></p>
    <p><strong>Version:</strong> <code><?= htmlspecialchars((string) $version) ?></code></p>
    <p><strong>Document Key:</strong> <code><?= htmlspecialchars((string) $documentKey) ?></code></p>
  </div>

  <div class="onlyoffice-prototype-editor-shell">
    <h2>Standalone Editor</h2>
    <p>
      Open the standalone validation route to bypass the Community page container and render ONLYOFFICE directly in a full-browser editor surface.
    </p>
    <p>
      <a href="/onlyoffice/editor.php"><strong>Open standalone editor</strong></a>
    </p>
    <p>
      <a href="/onlyoffice/documents.php"><strong>Open MinIO document catalogue</strong></a>
    </p>
  </div>
<?php endif; ?>
<?php
$content = ob_get_clean();
require '/app/public/inc/layout.php';
