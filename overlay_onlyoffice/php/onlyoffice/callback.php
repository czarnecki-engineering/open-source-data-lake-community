<?php
declare(strict_types=1);

require '/app/public/onlyoffice/onlyoffice.php';

header('Content-Type: application/json');

try {
  $payload = onlyoffice_read_callback_request();
  $status = isset($payload['status']) ? (int) $payload['status'] : 0;

  if (($status === 2 || $status === 6) && isset($payload['url']) && is_string($payload['url']) && $payload['url'] !== '') {
    onlyoffice_download_callback_file($payload['url'], onlyoffice_document_absolute_path());

    if ($status === 2) {
      onlyoffice_write_document_version(onlyoffice_read_document_version() + 1);
    }
  }

  echo json_encode(['error' => 0], JSON_THROW_ON_ERROR);
} catch (Throwable $exception) {
  http_response_code(403);
  echo json_encode([
    'error' => 1,
    'message' => $exception->getMessage(),
  ], JSON_THROW_ON_ERROR);
}
