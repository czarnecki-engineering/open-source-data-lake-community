<?php
declare(strict_types=1);

require '/app/public/onlyoffice/onlyoffice.php';

try {
  $selectedDocument = onlyoffice_selected_minio_document();

  if ($selectedDocument !== null) {
    $content = onlyoffice_minio_get_object($selectedDocument['bucket'], $selectedDocument['key']);
    header('Content-Type: ' . onlyoffice_document_mime_type($selectedDocument));
    header('Content-Disposition: inline; filename="' . rawurlencode(onlyoffice_document_download_filename($selectedDocument)) . '"');
    header('Content-Length: ' . (string) strlen($content));
    echo $content;
    exit;
  }
} catch (Throwable $exception) {
  http_response_code(502);
  header('Content-Type: application/json');
  echo json_encode(['error' => $exception->getMessage()], JSON_THROW_ON_ERROR);
  exit;
}

$path = onlyoffice_document_absolute_path();

if (!is_file($path) || !is_readable($path)) {
  http_response_code(404);
  header('Content-Type: application/json');
  echo json_encode(['error' => 'Document not found.'], JSON_THROW_ON_ERROR);
  exit;
}

header('Content-Type: ' . onlyoffice_document_mime_type());
header('Content-Disposition: inline; filename="' . rawurlencode(onlyoffice_document_download_filename()) . '"');
header('Content-Length: ' . (string) filesize($path));

$handle = fopen($path, 'rb');
if ($handle === false) {
  http_response_code(500);
  header('Content-Type: application/json');
  echo json_encode(['error' => 'Failed to open document.'], JSON_THROW_ON_ERROR);
  exit;
}

fpassthru($handle);
fclose($handle);
