<?php
declare(strict_types=1);

require '/app/public/onlyoffice/onlyoffice.php';

$errorMessage = null;
$config = null;
$version = null;
$documentKey = null;
$selectedMinioDocument = onlyoffice_selected_minio_document_uri();

try {
  $version = onlyoffice_read_document_version();
  $documentKey = onlyoffice_document_key($version);
  $config = onlyoffice_editor_config();
} catch (Throwable $exception) {
  $errorMessage = $exception->getMessage();
}
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>ONLYOFFICE Standalone Editor</title>
  <style>
    html,
    body {
      width: 100%;
      height: 100%;
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: #0b0f14;
      color: #e6edf3;
      font: 16px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", Arial, sans-serif;
    }

    body {
      display: flex;
      flex-direction: column;
    }

    .onlyoffice-standalone-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 12px 16px;
      background: #141b23;
      border-bottom: 1px solid #1f2937;
      flex: 0 0 auto;
    }

    .onlyoffice-standalone-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px 16px;
      font-size: 14px;
    }

    .onlyoffice-standalone-bar a {
      color: #3fa9f5;
      text-decoration: none;
    }

    .onlyoffice-standalone-bar a:hover {
      text-decoration: underline;
    }

    .onlyoffice-standalone-note {
      padding: 10px 16px;
      background: #102235;
      border-bottom: 1px solid #1f2937;
      font-size: 14px;
    }

    .onlyoffice-standalone-note code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }

    .onlyoffice-standalone-editor-wrap {
      position: relative;
      flex: 1 1 auto;
      min-height: 0;
      background: #ffffff;
    }

    #onlyoffice-editor {
      width: 100%;
      height: 100%;
    }

    #onlyoffice-editor > div,
    #onlyoffice-editor iframe {
      width: 100% !important;
      height: 100% !important;
    }

    .onlyoffice-standalone-error {
      padding: 24px;
    }

    .onlyoffice-standalone-error code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
    }
  </style>
</head>
<body>
<?php if ($errorMessage !== null): ?>
  <div class="onlyoffice-standalone-error">
    <h1>ONLYOFFICE Standalone Editor</h1>
    <p><a href="/solutions/onlyoffice_prototype.php">Back to prototype page</a></p>
    <p><strong>Configuration error:</strong> <?= htmlspecialchars($errorMessage) ?></p>
  </div>
<?php else: ?>
  <div class="onlyoffice-standalone-bar">
    <div class="onlyoffice-standalone-meta">
      <span><strong>Local File:</strong> <code><?= htmlspecialchars(onlyoffice_document_relative_path()) ?></code></span>
      <span><strong>Version:</strong> <code><?= htmlspecialchars((string) $version) ?></code></span>
      <span><strong>Key:</strong> <code><?= htmlspecialchars((string) $documentKey) ?></code></span>
    </div>
    <div>
      <a href="/onlyoffice/documents.php">Document catalogue</a>
      &nbsp;|&nbsp;
      <a href="/solutions/onlyoffice_prototype.php">Prototype page</a>
    </div>
  </div>

<?php if ($selectedMinioDocument !== null): ?>
  <div class="onlyoffice-standalone-note">
    Selected MinIO object: <code><?= htmlspecialchars($selectedMinioDocument) ?></code>. The editor still uses the validated local Phase 1 document path until Phase 2B implements MinIO-backed open.
  </div>
<?php endif; ?>

  <div class="onlyoffice-standalone-editor-wrap">
    <div id="onlyoffice-editor"></div>
  </div>

  <script src="<?= htmlspecialchars(onlyoffice_docs_public_url()) ?>/web-apps/apps/api/documents/api.js"></script>
  <script>
    window.addEventListener("DOMContentLoaded", function () {
      var config = <?= json_encode($config, JSON_THROW_ON_ERROR | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) ?>;
      new DocsAPI.DocEditor("onlyoffice-editor", config);
    });
  </script>
<?php endif; ?>
</body>
</html>
