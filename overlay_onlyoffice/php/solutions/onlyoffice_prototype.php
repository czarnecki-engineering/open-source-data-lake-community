<?php
declare(strict_types=1);

/*
Solution Title: ONLYOFFICE Prototype
Solution Summary: Static local-file ONLYOFFICE editor proof of concept for a single tracked DOCX document.
Solution Tag: onlyoffice
*/

require '/app/public/inc/onlyoffice.php';

$page_title = 'ONLYOFFICE Prototype';
$page_description = 'Static local-file ONLYOFFICE editor proof of concept.';

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

  <div class="card">
    <h2>Editor</h2>
    <div id="onlyoffice-editor" style="height: 720px;"></div>
  </div>

  <script src="<?= htmlspecialchars(onlyoffice_docs_public_url()) ?>/web-apps/apps/api/documents/api.js"></script>
  <script>
    window.addEventListener("DOMContentLoaded", function () {
      var config = <?= json_encode($config, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) ?>;
      new DocsAPI.DocEditor("onlyoffice-editor", config);
    });
  </script>
<?php endif; ?>
<?php
$content = ob_get_clean();
require '/app/public/inc/layout.php';
