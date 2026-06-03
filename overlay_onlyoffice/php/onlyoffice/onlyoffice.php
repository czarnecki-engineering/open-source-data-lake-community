<?php
declare(strict_types=1);

const ONLYOFFICE_DOCUMENT_RELATIVE_PATH = 'onlyoffice/community-prototype.docx';
const ONLYOFFICE_RUNTIME_RELATIVE_PATH = 'onlyoffice/runtime';

function onlyoffice_env(string $name): string
{
  $value = getenv($name);
  if (!is_string($value) || trim($value) === '') {
    throw new RuntimeException("Missing required environment variable: {$name}");
  }

  return trim($value);
}

function onlyoffice_log(string $message): void
{
  error_log('[onlyoffice] ' . $message);
}

function onlyoffice_storage_root(): string
{
  return '/app/data';
}

function onlyoffice_fallback_document_relative_path(): string
{
  return ONLYOFFICE_DOCUMENT_RELATIVE_PATH;
}

function onlyoffice_document_relative_path(): string
{
  return onlyoffice_fallback_document_relative_path();
}

function onlyoffice_document_absolute_path(): string
{
  return onlyoffice_storage_root() . '/' . onlyoffice_document_relative_path();
}

function onlyoffice_document_version_path(): string
{
  return onlyoffice_document_absolute_path() . '.version';
}

function onlyoffice_document_title(): string
{
  return basename(onlyoffice_document_relative_path());
}

function onlyoffice_runtime_absolute_path(): string
{
  return onlyoffice_storage_root() . '/' . ONLYOFFICE_RUNTIME_RELATIVE_PATH;
}

function onlyoffice_ensure_directory_exists(string $path): void
{
  if (is_dir($path)) {
    return;
  }

  if (!@mkdir($path, 0775, true) && !is_dir($path)) {
    throw new RuntimeException('Failed to create directory: ' . $path);
  }
}

function onlyoffice_read_document_version(): int
{
  $raw = @file_get_contents(onlyoffice_document_version_path());
  if ($raw === false) {
    throw new RuntimeException('Document version metadata not found.');
  }

  $version = filter_var(trim($raw), FILTER_VALIDATE_INT);
  if ($version === false || $version < 1) {
    throw new RuntimeException('Document version metadata is invalid.');
  }

  return $version;
}

function onlyoffice_write_document_version(int $version): void
{
  if ($version < 1) {
    throw new RuntimeException('Document version must be a positive integer.');
  }

  $bytes = @file_put_contents(onlyoffice_document_version_path(), (string) $version . PHP_EOL, LOCK_EX);
  if ($bytes === false) {
    throw new RuntimeException('Failed to write document version metadata.');
  }
}

function onlyoffice_document_source_uri(?array $document = null): string
{
  if ($document === null) {
    return 'file://' . onlyoffice_document_relative_path();
  }

  return 's3://' . $document['bucket'] . '/' . $document['key'];
}

function onlyoffice_document_revision_value(array $document): string
{
  $etag = isset($document['etag']) && is_string($document['etag']) ? trim($document['etag']) : '';
  if ($etag !== '') {
    return 'etag:' . $etag;
  }

  $lastModified = isset($document['last_modified']) && is_string($document['last_modified'])
    ? trim($document['last_modified'])
    : '';
  if ($lastModified !== '') {
    return 'last_modified:' . $lastModified;
  }

  if (isset($document['size']) && is_int($document['size']) && $document['size'] >= 0) {
    return 'size:' . (string) $document['size'];
  }

  return 'source:' . onlyoffice_document_source_uri($document);
}

function onlyoffice_document_key(int $version, ?array $document = null): string
{
  if ($document !== null) {
    return hash(
      'sha256',
      implode("\n", [
        'bucket:' . $document['bucket'],
        'key:' . $document['key'],
        onlyoffice_document_revision_value($document),
      ])
    );
  }

  return hash('sha256', onlyoffice_document_relative_path() . ':' . $version);
}

function onlyoffice_docs_public_url(): string
{
  return rtrim(onlyoffice_env('ONLYOFFICE_DOCS_PUBLIC_URL'), '/');
}

function onlyoffice_docs_internal_url(): string
{
  $value = getenv('ONLYOFFICE_DOCS_INTERNAL_URL');
  if (is_string($value) && trim($value) !== '') {
    return rtrim(trim($value), '/');
  }

  return 'http://onlyoffice-docs';
}

function onlyoffice_storage_internal_url(): string
{
  return rtrim(onlyoffice_env('ONLYOFFICE_STORAGE_INTERNAL_URL'), '/');
}

function onlyoffice_document_query_string(?array $document = null): string
{
  if ($document === null) {
    return '';
  }

  return http_build_query([
    'bucket' => $document['bucket'],
    'key' => $document['key'],
  ]);
}

function onlyoffice_download_url(?array $document = null): string
{
  $url = onlyoffice_storage_internal_url() . '/onlyoffice/download.php';
  $query = onlyoffice_document_query_string($document);

  return $query === '' ? $url : $url . '?' . $query;
}

function onlyoffice_callback_url(?array $document = null): string
{
  $url = onlyoffice_storage_internal_url() . '/onlyoffice/callback.php';
  if ($document === null) {
    return $url;
  }

  $query = http_build_query([
    'state' => onlyoffice_callback_state_token($document, onlyoffice_document_key(1, $document)),
  ]);

  return $query === '' ? $url : $url . '?' . $query;
}

function onlyoffice_jwt_secret(): string
{
  return onlyoffice_env('ONLYOFFICE_JWT_SECRET');
}

function onlyoffice_callback_state_secret(): string
{
  $value = getenv('ONLYOFFICE_CALLBACK_STATE_SECRET');
  if (is_string($value) && trim($value) !== '') {
    return trim($value);
  }

  return onlyoffice_jwt_secret();
}

function onlyoffice_base64url_encode(string $data): string
{
  return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
}

function onlyoffice_base64url_decode(string $data): string
{
  $padded = strtr($data, '-_', '+/');
  $padding = strlen($padded) % 4;
  if ($padding > 0) {
    $padded .= str_repeat('=', 4 - $padding);
  }

  $decoded = base64_decode($padded, true);
  if ($decoded === false) {
    throw new RuntimeException('Invalid base64url payload.');
  }

  return $decoded;
}

function onlyoffice_jwt_encode(array $payload, string $secret): string
{
  $header = ['alg' => 'HS256', 'typ' => 'JWT'];
  $encodedHeader = onlyoffice_base64url_encode(json_encode($header, JSON_THROW_ON_ERROR));
  $encodedPayload = onlyoffice_base64url_encode(json_encode($payload, JSON_THROW_ON_ERROR));
  $signature = hash_hmac('sha256', $encodedHeader . '.' . $encodedPayload, $secret, true);

  return $encodedHeader . '.' . $encodedPayload . '.' . onlyoffice_base64url_encode($signature);
}

function onlyoffice_jwt_decode(string $token, string $secret): array
{
  $parts = explode('.', $token);
  if (count($parts) !== 3) {
    throw new RuntimeException('JWT must contain exactly three segments.');
  }

  [$encodedHeader, $encodedPayload, $encodedSignature] = $parts;

  $header = json_decode(onlyoffice_base64url_decode($encodedHeader), true, 512, JSON_THROW_ON_ERROR);
  if (!is_array($header) || ($header['alg'] ?? null) !== 'HS256') {
    throw new RuntimeException('Unsupported JWT algorithm.');
  }

  $expectedSignature = onlyoffice_base64url_encode(
    hash_hmac('sha256', $encodedHeader . '.' . $encodedPayload, $secret, true)
  );

  if (!hash_equals($expectedSignature, $encodedSignature)) {
    throw new RuntimeException('JWT signature verification failed.');
  }

  $payload = json_decode(onlyoffice_base64url_decode($encodedPayload), true, 512, JSON_THROW_ON_ERROR);
  if (!is_array($payload)) {
    throw new RuntimeException('JWT payload must decode to an object.');
  }

  return $payload;
}

function onlyoffice_extract_bearer_token(): ?string
{
  $header = $_SERVER['HTTP_AUTHORIZATION'] ?? $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ?? null;
  if (!is_string($header)) {
    return null;
  }

  if (preg_match('/^\s*Bearer\s+(.+)\s*$/i', $header, $matches) !== 1) {
    return null;
  }

  return trim($matches[1]);
}

function onlyoffice_callback_state_token(array $document, string $expectedDocumentKey): string
{
  $payload = [
    'scope' => 'onlyoffice-callback-state',
    'bucket' => $document['bucket'],
    'key' => $document['key'],
    'expected_document_key' => $expectedDocumentKey,
    'iat' => time(),
  ];

  if (isset($document['etag']) && is_string($document['etag']) && trim($document['etag']) !== '') {
    $payload['source_etag'] = trim($document['etag']);
  }

  if (isset($document['last_modified']) && is_string($document['last_modified']) && trim($document['last_modified']) !== '') {
    $payload['source_last_modified'] = trim($document['last_modified']);
  }

  if (isset($document['size']) && is_int($document['size']) && $document['size'] >= 0) {
    $payload['source_size'] = $document['size'];
  }

  return onlyoffice_jwt_encode($payload, onlyoffice_callback_state_secret());
}

function onlyoffice_validate_callback_state_token(string $token): array
{
  $payload = onlyoffice_jwt_decode($token, onlyoffice_callback_state_secret());
  if (($payload['scope'] ?? null) !== 'onlyoffice-callback-state') {
    throw new RuntimeException('Callback state token scope is invalid.');
  }

  $bucket = isset($payload['bucket']) && is_string($payload['bucket']) ? trim($payload['bucket']) : '';
  $key = isset($payload['key']) && is_string($payload['key']) ? ltrim(trim($payload['key']), '/') : '';
  $expectedDocumentKey = isset($payload['expected_document_key']) && is_string($payload['expected_document_key'])
    ? trim($payload['expected_document_key'])
    : '';

  if ($bucket === '' || $key === '' || $expectedDocumentKey === '') {
    throw new RuntimeException('Callback state token is missing required object identity fields.');
  }

  $state = [
    'bucket' => $bucket,
    'key' => $key,
    'expected_document_key' => $expectedDocumentKey,
  ];

  if (isset($payload['source_etag']) && is_string($payload['source_etag']) && trim($payload['source_etag']) !== '') {
    $state['source_etag'] = trim($payload['source_etag']);
  }

  if (
    isset($payload['source_last_modified'])
    && is_string($payload['source_last_modified'])
    && trim($payload['source_last_modified']) !== ''
  ) {
    $state['source_last_modified'] = trim($payload['source_last_modified']);
  }

  if (isset($payload['source_size'])) {
    $sourceSize = filter_var($payload['source_size'], FILTER_VALIDATE_INT);
    if ($sourceSize === false || $sourceSize < 0) {
      throw new RuntimeException('Callback state token source size is invalid.');
    }

    $state['source_size'] = $sourceSize;
  }

  if (isset($payload['iat'])) {
    $issuedAt = filter_var($payload['iat'], FILTER_VALIDATE_INT);
    if ($issuedAt === false || $issuedAt < 0) {
      throw new RuntimeException('Callback state token issued-at timestamp is invalid.');
    }

    $state['iat'] = $issuedAt;
  }

  return $state;
}

function onlyoffice_read_callback_request(): array
{
  $rawBody = file_get_contents('php://input');
  if (!is_string($rawBody) || trim($rawBody) === '') {
    return [
      'payload' => [],
      'jwt_present' => false,
      'jwt_source' => null,
      'jwt_validated' => false,
      'jwt_error' => null,
    ];
  }

  $decodedBody = json_decode($rawBody, true);
  if (!is_array($decodedBody)) {
    throw new RuntimeException('Callback body is not valid JSON.');
  }

  $secret = onlyoffice_jwt_secret();
  $token = null;
  $tokenSource = null;

  if (isset($decodedBody['token']) && is_string($decodedBody['token']) && $decodedBody['token'] !== '') {
    $token = $decodedBody['token'];
    $tokenSource = 'body';
  } else {
    $token = onlyoffice_extract_bearer_token();
    $tokenSource = $token === null ? null : 'header';
  }

  if ($token === null) {
    return [
      'payload' => $decodedBody,
      'jwt_present' => false,
      'jwt_source' => null,
      'jwt_validated' => false,
      'jwt_error' => null,
    ];
  }

  try {
    $verifiedPayload = onlyoffice_jwt_decode($token, $secret);
  } catch (Throwable $exception) {
    return [
      'payload' => $decodedBody,
      'jwt_present' => true,
      'jwt_source' => $tokenSource,
      'jwt_validated' => false,
      'jwt_error' => $exception->getMessage(),
    ];
  }
  $payload = $verifiedPayload;

  if (isset($verifiedPayload['payload']) && is_array($verifiedPayload['payload'])) {
    $payload = $verifiedPayload['payload'];
  } elseif ($tokenSource === 'header' && !isset($verifiedPayload['status']) && !isset($verifiedPayload['url'])) {
    $payload = $decodedBody;
  } elseif ($verifiedPayload === []) {
    $payload = $decodedBody;
  }

  return [
    'payload' => $payload,
    'jwt_present' => true,
    'jwt_source' => $tokenSource,
    'jwt_validated' => true,
    'jwt_error' => null,
  ];
}

function onlyoffice_document_extension(?array $document = null): string
{
  $path = $document === null ? onlyoffice_document_relative_path() : $document['key'];
  $extension = strtolower(pathinfo($path, PATHINFO_EXTENSION));

  return $extension !== '' ? $extension : 'docx';
}

function onlyoffice_document_type_from_extension(string $extension): string
{
  if (in_array($extension, ['xls', 'xlsx', 'ods'], true)) {
    return 'cell';
  }

  if (in_array($extension, ['ppt', 'pptx', 'odp'], true)) {
    return 'slide';
  }

  return 'word';
}

function onlyoffice_document_display_title(?array $document = null): string
{
  return $document === null ? onlyoffice_document_title() : basename($document['key']);
}

function onlyoffice_document_download_filename(?array $document = null): string
{
  return onlyoffice_document_display_title($document);
}

function onlyoffice_document_mime_type(?array $document = null): string
{
  return match (onlyoffice_document_extension($document)) {
    'doc' => 'application/msword',
    'docx' => 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'odt' => 'application/vnd.oasis.opendocument.text',
    'ods' => 'application/vnd.oasis.opendocument.spreadsheet',
    'odp' => 'application/vnd.oasis.opendocument.presentation',
    'xls' => 'application/vnd.ms-excel',
    'xlsx' => 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'ppt' => 'application/vnd.ms-powerpoint',
    'pptx' => 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    default => 'application/octet-stream',
  };
}

function onlyoffice_callback_spool_path(array $document): string
{
  $extension = onlyoffice_document_extension($document);
  $hash = hash('sha256', onlyoffice_document_source_uri($document));

  return onlyoffice_runtime_absolute_path() . '/callback-' . $hash . '.' . $extension;
}

function onlyoffice_callback_payload_document_key(array $payload): ?string
{
  if (isset($payload['key']) && is_string($payload['key']) && trim($payload['key']) !== '') {
    return trim($payload['key']);
  }

  if (
    isset($payload['document'])
    && is_array($payload['document'])
    && isset($payload['document']['key'])
    && is_string($payload['document']['key'])
    && trim($payload['document']['key']) !== ''
  ) {
    return trim($payload['document']['key']);
  }

  return null;
}

function onlyoffice_rewrite_docs_url_for_internal_access(string $sourceUrl): string
{
  $publicUrl = parse_url(onlyoffice_docs_public_url());
  $source = parse_url($sourceUrl);

  if (!is_array($publicUrl) || !is_array($source)) {
    return $sourceUrl;
  }

  $publicHost = $publicUrl['host'] ?? null;
  $sourceHost = $source['host'] ?? null;
  $publicPort = $publicUrl['port'] ?? null;
  $sourcePort = $source['port'] ?? null;

  if (!is_string($publicHost) || !is_string($sourceHost)) {
    return $sourceUrl;
  }

  if ($publicHost !== $sourceHost || $publicPort !== $sourcePort) {
    return $sourceUrl;
  }

  $internal = parse_url(onlyoffice_docs_internal_url());
  if (!is_array($internal) || !isset($internal['scheme'], $internal['host'])) {
    return $sourceUrl;
  }

  $rebuilt = $internal['scheme'] . '://' . $internal['host'];
  if (isset($internal['port'])) {
    $rebuilt .= ':' . $internal['port'];
  }

  $rebuilt .= $source['path'] ?? '';

  if (isset($source['query']) && $source['query'] !== '') {
    $rebuilt .= '?' . $source['query'];
  }

  if (isset($source['fragment']) && $source['fragment'] !== '') {
    $rebuilt .= '#' . $source['fragment'];
  }

  return $rebuilt;
}

function onlyoffice_download_callback_file_to_temporary_path(string $sourceUrl, string $targetDirectory): string
{
  onlyoffice_ensure_directory_exists($targetDirectory);
  $downloadUrl = onlyoffice_rewrite_docs_url_for_internal_access($sourceUrl);
  onlyoffice_log('Callback download URL rewritten to ' . $downloadUrl);

  $tmpPath = tempnam($targetDirectory, 'onlyoffice-save-');
  if ($tmpPath === false) {
    throw new RuntimeException('Failed to allocate a temporary file for the callback download.');
  }
  onlyoffice_log('Temporary callback file created at ' . $tmpPath);

  $tmpHandle = fopen($tmpPath, 'wb');
  if ($tmpHandle === false) {
    @unlink($tmpPath);
    throw new RuntimeException('Failed to open a temporary file for the callback download.');
  }

  $ch = curl_init($downloadUrl);
  curl_setopt_array($ch, [
    CURLOPT_FILE => $tmpHandle,
    CURLOPT_FOLLOWLOCATION => true,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT => 120,
    CURLOPT_FAILONERROR => true,
  ]);

  $ok = curl_exec($ch);
  $error = curl_error($ch);
  $statusCode = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
  fclose($tmpHandle);

  if ($ok === false) {
    @unlink($tmpPath);
    throw new RuntimeException('Failed to download the callback file: ' . ($error !== '' ? $error : "HTTP {$statusCode}"));
  }

  return $tmpPath;
}

function onlyoffice_download_callback_file(string $sourceUrl, string $targetPath): void
{
  onlyoffice_ensure_directory_exists(dirname($targetPath));
  $tmpPath = onlyoffice_download_callback_file_to_temporary_path($sourceUrl, dirname($targetPath));

  if (!@rename($tmpPath, $targetPath)) {
    @unlink($tmpPath);
    throw new RuntimeException('Failed to replace the local document with the callback file.');
  }
}

function onlyoffice_s3_object_canonical_uri(string $bucket, string $key): string
{
  $segments = array_values(
    array_filter(explode('/', ltrim($key, '/')), static fn(string $segment): bool => $segment !== '')
  );
  $encodedSegments = array_map(static fn(string $segment): string => rawurlencode($segment), $segments);

  $uri = '/' . rawurlencode($bucket);
  if ($encodedSegments !== []) {
    $uri .= '/' . implode('/', $encodedSegments);
  }

  return $uri;
}

function onlyoffice_minio_get_object(string $bucket, string $key): string
{
  $endpoint = parse_url(onlyoffice_minio_endpoint());
  if (!is_array($endpoint) || !isset($endpoint['scheme'], $endpoint['host'])) {
    throw new RuntimeException('ONLYOFFICE MinIO endpoint is invalid.');
  }

  $canonicalUri = onlyoffice_s3_object_canonical_uri($bucket, $key);
  $url = $endpoint['scheme'] . '://' . $endpoint['host'];
  if (isset($endpoint['port'])) {
    $url .= ':' . $endpoint['port'];
  }
  $url .= $canonicalUri;

  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_HTTPGET => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT => 120,
    CURLOPT_FAILONERROR => false,
    CURLOPT_HTTPHEADER => onlyoffice_s3_authorized_headers('GET', $canonicalUri),
  ]);

  $response = curl_exec($ch);
  $error = curl_error($ch);
  $statusCode = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);

  if (!is_string($response)) {
    throw new RuntimeException('Failed to download the selected MinIO object: ' . ($error !== '' ? $error : 'no body'));
  }

  if ($statusCode < 200 || $statusCode >= 300) {
    throw new RuntimeException("Failed to download the selected MinIO object: HTTP {$statusCode}.");
  }

  return $response;
}

function onlyoffice_minio_put_object(string $bucket, string $key, string $sourcePath, string $contentType): void
{
  if (!is_file($sourcePath) || !is_readable($sourcePath)) {
    throw new RuntimeException('Callback upload source file is not readable.');
  }

  $endpoint = parse_url(onlyoffice_minio_endpoint());
  if (!is_array($endpoint) || !isset($endpoint['scheme'], $endpoint['host'])) {
    throw new RuntimeException('ONLYOFFICE MinIO endpoint is invalid.');
  }

  $canonicalUri = onlyoffice_s3_object_canonical_uri($bucket, $key);
  $url = $endpoint['scheme'] . '://' . $endpoint['host'];
  if (isset($endpoint['port'])) {
    $url .= ':' . $endpoint['port'];
  }
  $url .= $canonicalUri;

  $payloadHash = hash_file('sha256', $sourcePath);
  if (!is_string($payloadHash)) {
    throw new RuntimeException('Failed to hash the callback upload file.');
  }

  $contentLength = filesize($sourcePath);
  if ($contentLength === false) {
    throw new RuntimeException('Failed to determine the callback upload file size.');
  }

  $handle = fopen($sourcePath, 'rb');
  if ($handle === false) {
    throw new RuntimeException('Failed to open the callback upload file.');
  }

  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_CUSTOMREQUEST => 'PUT',
    CURLOPT_UPLOAD => true,
    CURLOPT_INFILE => $handle,
    CURLOPT_INFILESIZE => $contentLength,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT => 120,
    CURLOPT_FAILONERROR => false,
    CURLOPT_HTTPHEADER => onlyoffice_s3_authorized_headers(
      'PUT',
      $canonicalUri,
      '',
      $payloadHash,
      ['content-type' => $contentType]
    ),
  ]);

  $response = curl_exec($ch);
  $error = curl_error($ch);
  $statusCode = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
  fclose($handle);

  if ($response === false) {
    throw new RuntimeException('Failed to upload the callback file to MinIO: ' . ($error !== '' ? $error : 'no response body'));
  }

  if ($statusCode < 200 || $statusCode >= 300) {
    throw new RuntimeException("Failed to upload the callback file to MinIO: HTTP {$statusCode}.");
  }
}

function onlyoffice_editor_config(): array
{
  $selectedDocument = onlyoffice_selected_minio_document();
  $version = $selectedDocument === null ? onlyoffice_read_document_version() : 1;
  $extension = onlyoffice_document_extension($selectedDocument);
  $documentKey = onlyoffice_document_key($version, $selectedDocument);

  $config = [
    'document' => [
      'fileType' => $extension,
      'key' => $documentKey,
      'title' => onlyoffice_document_display_title($selectedDocument),
      'url' => onlyoffice_download_url($selectedDocument),
    ],
    'documentType' => onlyoffice_document_type_from_extension($extension),
    'editorConfig' => [
      'callbackUrl' => onlyoffice_callback_url($selectedDocument),
      'mode' => 'edit',
      'user' => [
        'id' => 'community-onlyoffice-poc',
        'name' => 'Community Prototype User',
      ],
      'customization' => [
        'autosave' => true,
        'forcesave' => true,
      ],
    ],
  ];

  $config['token'] = onlyoffice_jwt_encode($config, onlyoffice_jwt_secret());

  return $config;
}

require_once __DIR__ . '/catalogue_helpers.php';
