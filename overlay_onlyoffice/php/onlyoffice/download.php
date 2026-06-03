<?php
declare(strict_types=1);

require '/app/public/inc/onlyoffice.php';

$path = onlyoffice_document_absolute_path();

if (!is_file($path) || !is_readable($path)) {
  http_response_code(404);
  header('Content-Type: application/json');
  echo json_encode(['error' => 'Document not found.'], JSON_THROW_ON_ERROR);
  exit;
}

header('Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document');
header('Content-Disposition: inline; filename="' . rawurlencode(onlyoffice_document_title()) . '"');
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
