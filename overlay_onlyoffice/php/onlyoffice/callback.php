<?php
declare(strict_types=1);

require '/app/public/onlyoffice/onlyoffice.php';

header('Content-Type: application/json');

try {
  $request = onlyoffice_read_callback_request();
  $payload = $request['payload'];
  $status = isset($payload['status']) ? (int) $payload['status'] : 0;
  $jwtPresent = (bool) ($request['jwt_present'] ?? false);
  $jwtValidated = (bool) ($request['jwt_validated'] ?? false);
  $jwtSource = $request['jwt_source'] ?? null;
  $jwtError = $request['jwt_error'] ?? null;
  $saveStatus = $status === 2 || $status === 6;
  $state = null;
  $stateToken = $_GET['state'] ?? null;

  onlyoffice_log('Callback received with status ' . $status . '.');
  onlyoffice_log(
    'Callback JWT validation '
    . ($jwtValidated ? 'succeeded' : 'failed')
    . '; token '
    . ($jwtPresent ? 'present' : 'missing')
    . ($jwtSource !== null ? ' via ' . $jwtSource : '')
    . '.'
  );
  if (!$jwtValidated && is_string($jwtError) && $jwtError !== '') {
    onlyoffice_log('Callback JWT validation error: ' . $jwtError);
  }

  if (is_string($stateToken) && trim($stateToken) !== '') {
    try {
      $state = onlyoffice_validate_callback_state_token(trim($stateToken));
      onlyoffice_log(
        'Callback state token validation succeeded for target '
        . $state['bucket']
        . '/'
        . $state['key']
        . '.'
      );
    } catch (Throwable $stateException) {
      onlyoffice_log('Callback state token validation failed: ' . $stateException->getMessage());
      if ($saveStatus) {
        throw $stateException;
      }
    }
  } else {
    onlyoffice_log('Callback state token missing.');
  }

  if (!$saveStatus) {
    onlyoffice_log('Ignored callback status ' . $status . '.');
    echo json_encode(['error' => 0], JSON_THROW_ON_ERROR);
    exit;
  }

  if (!$jwtValidated) {
    throw new RuntimeException('ONLYOFFICE callback JWT validation is required for save callbacks.');
  }

  if (!isset($payload['url']) || !is_string($payload['url']) || trim($payload['url']) === '') {
    throw new RuntimeException('ONLYOFFICE callback payload did not include a save URL.');
  }

  $callbackDocumentKey = onlyoffice_callback_payload_document_key($payload);
  if ($state !== null) {
    if ($callbackDocumentKey !== null) {
      if (!hash_equals($state['expected_document_key'], $callbackDocumentKey)) {
        onlyoffice_log(
          'Callback document key comparison failed: expected '
          . $state['expected_document_key']
          . ', received '
          . $callbackDocumentKey
          . '.'
        );
        throw new RuntimeException('ONLYOFFICE callback document key did not match the signed callback state.');
      }

      onlyoffice_log('Callback document key comparison succeeded.');
    } else {
      onlyoffice_log('Callback document key not present; signed callback state remains the trusted identity.');
    }

    $tempPath = onlyoffice_download_callback_file_to_temporary_path($payload['url'], onlyoffice_runtime_absolute_path());

    try {
      onlyoffice_log('Uploading callback file to MinIO target ' . $state['bucket'] . '/' . $state['key'] . '.');
      onlyoffice_minio_put_object(
        $state['bucket'],
        $state['key'],
        $tempPath,
        onlyoffice_document_mime_type($state)
      );
      onlyoffice_log('MinIO upload succeeded for ' . $state['bucket'] . '/' . $state['key'] . '.');
    } finally {
      if (is_file($tempPath)) {
        if (@unlink($tempPath)) {
          onlyoffice_log('Temporary callback file deleted: ' . $tempPath);
        } else {
          onlyoffice_log('Failed to delete temporary callback file: ' . $tempPath);
        }
      }
    }
  } else {
    if ($callbackDocumentKey === null) {
      throw new RuntimeException('Signed callback state is required for non-prototype save callbacks.');
    }

    $localDocumentKey = onlyoffice_document_key(onlyoffice_read_document_version());
    if (!hash_equals($localDocumentKey, $callbackDocumentKey)) {
      onlyoffice_log(
        'Legacy local prototype key comparison failed: expected '
        . $localDocumentKey
        . ', received '
        . $callbackDocumentKey
        . '.'
      );
      throw new RuntimeException('Signed callback state is required for MinIO-backed save callbacks.');
    }

    onlyoffice_log('Legacy local prototype key comparison succeeded.');
    onlyoffice_log('Using legacy local prototype save path.');
    onlyoffice_download_callback_file($payload['url'], onlyoffice_document_absolute_path());
    if ($status === 2) {
      onlyoffice_write_document_version(onlyoffice_read_document_version() + 1);
    }
  }

  echo json_encode(['error' => 0], JSON_THROW_ON_ERROR);
} catch (Throwable $exception) {
  onlyoffice_log('Callback failed: ' . $exception->getMessage());
  http_response_code(403);
  echo json_encode([
    'error' => 1,
    'message' => $exception->getMessage(),
  ], JSON_THROW_ON_ERROR);
}
