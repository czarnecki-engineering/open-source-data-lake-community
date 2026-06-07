<?php
declare(strict_types=1);

require '/app/public/onlyoffice/onlyoffice.php';

$errorMessage = null;
$config = null;
$version = null;
$documentKey = null;
$selectedMinioDocument = onlyoffice_selected_minio_document_uri();
$selectedMinioSource = onlyoffice_selected_minio_document();

try {
  $version = $selectedMinioSource === null ? onlyoffice_read_document_version() : 1;
  $documentKey = onlyoffice_document_key($version, $selectedMinioSource);
  $config = onlyoffice_editor_config();
} catch (Throwable $exception) {
  $errorMessage = $exception->getMessage();
}

$selectedDocumentDisplay = $selectedMinioDocument ?? onlyoffice_document_source_uri();
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
      background: #f5f7fa;
      color: #152033;
      font: 16px/1.5 system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, "Helvetica Neue", Arial, sans-serif;
    }

    body {
      display: flex;
      flex-direction: column;
    }

    .onlyoffice-standalone-bar {
      display: flex;
      flex-direction: column;
      align-items: stretch;
      gap: 8px;
      padding: 12px 16px;
      background: #ffffff;
      border-bottom: 1px solid #d8e0ea;
      flex: 0 0 auto;
    }

    .onlyoffice-standalone-heading {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px 16px;
    }

    .onlyoffice-standalone-heading h1 {
      margin: 0;
      font-size: 20px;
      line-height: 1.2;
    }

    .onlyoffice-standalone-nav {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 14px;
    }

    .onlyoffice-standalone-bar p {
      margin: 0;
      font-size: 14px;
    }

    .onlyoffice-standalone-bar a {
      color: #0b57a4;
      text-decoration: none;
    }

    .onlyoffice-standalone-bar a:hover {
      text-decoration: underline;
    }

    .onlyoffice-standalone-meta {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
      margin-top: 8px;
    }

    .onlyoffice-standalone-meta th,
    .onlyoffice-standalone-meta td {
      padding: 8px 10px;
      border: 1px solid #d8e0ea;
      text-align: left;
      vertical-align: top;
      background: #ffffff;
    }

    .onlyoffice-standalone-meta th {
      width: 160px;
      background: #f7f9fc;
    }

    .onlyoffice-standalone-meta code,
    .onlyoffice-standalone-error code {
      word-break: break-word;
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
      max-width: 960px;
      margin: 0 auto;
    }

    .onlyoffice-standalone-error-links {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 16px;
    }

    .onlyoffice-standalone-details {
      border: 1px solid #d8e0ea;
      background: #f7f9fc;
    }

    .onlyoffice-standalone-details summary {
      cursor: pointer;
      padding: 8px 10px;
      font-size: 14px;
      font-weight: 600;
      list-style: none;
    }

    .onlyoffice-standalone-details summary::-webkit-details-marker {
      display: none;
    }

    .onlyoffice-standalone-details summary::after {
      content: "Show";
      float: right;
      font-weight: 400;
      color: #4b5b73;
    }

    .onlyoffice-standalone-details[open] summary::after {
      content: "Hide";
    }

    @media (max-width: 720px) {
      .onlyoffice-standalone-meta th {
        width: 120px;
      }
    }
  </style>
</head>
<body>
<?php if ($errorMessage !== null): ?>
  <div class="onlyoffice-standalone-error">
    <h1>Editor Configuration Error</h1>
    <p><?= htmlspecialchars($errorMessage) ?></p>
    <p class="onlyoffice-standalone-error-links">
      <a href="/onlyoffice/documents.php">Back to document catalogue</a>
      <a href="/solutions/onlyoffice_prototype.php">Back to prototype page</a>
    </p>
  </div>
<?php else: ?>
  <div class="onlyoffice-standalone-bar">
    <div class="onlyoffice-standalone-heading">
      <h1>ONLYOFFICE Editor</h1>
      <div class="onlyoffice-standalone-nav">
        <a href="/onlyoffice/documents.php">Document catalogue</a>
        <a href="/solutions/onlyoffice_prototype.php">Prototype page</a>
      </div>
    </div>
    <p>
      The ONLYOFFICE configuration, callback URL, download URL, and document key logic remain unchanged.
    </p>
    <details class="onlyoffice-standalone-details">
      <summary>Document details: <code><?= htmlspecialchars(basename($selectedMinioSource['key'] ?? onlyoffice_document_relative_path())) ?></code></summary>
      <table class="onlyoffice-standalone-meta">
        <tbody>
          <tr>
            <th>Document</th>
            <td><code><?= htmlspecialchars(basename($selectedMinioSource['key'] ?? onlyoffice_document_relative_path())) ?></code></td>
          </tr>
          <tr>
            <th>Version</th>
            <td><code><?= htmlspecialchars((string) $version) ?></code></td>
          </tr>
          <tr>
            <th>Key</th>
            <td><code><?= htmlspecialchars((string) $documentKey) ?></code></td>
          </tr>
          <tr>
            <th>Source URI</th>
            <td><code><?= htmlspecialchars($selectedDocumentDisplay) ?></code></td>
          </tr>
<?php if ($selectedMinioSource !== null): ?>
          <tr>
            <th>Bucket</th>
            <td><code><?= htmlspecialchars($selectedMinioSource['bucket']) ?></code></td>
          </tr>
          <tr>
            <th>Object Key</th>
            <td><code><?= htmlspecialchars($selectedMinioSource['key']) ?></code></td>
          </tr>
<?php if (isset($selectedMinioSource['size']) && is_int($selectedMinioSource['size'])): ?>
          <tr>
            <th>Size</th>
            <td><?= htmlspecialchars(onlyoffice_format_bytes($selectedMinioSource['size'])) ?></td>
          </tr>
<?php endif; ?>
<?php if (isset($selectedMinioSource['last_modified']) && is_string($selectedMinioSource['last_modified']) && $selectedMinioSource['last_modified'] !== ''): ?>
          <tr>
            <th>Last Modified</th>
            <td><?= htmlspecialchars(onlyoffice_format_timestamp($selectedMinioSource['last_modified'])) ?></td>
          </tr>
<?php endif; ?>
<?php endif; ?>
        </tbody>
      </table>
    </details>
  </div>

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
