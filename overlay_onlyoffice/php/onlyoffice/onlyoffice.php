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
  $query = onlyoffice_document_query_string($document);

  return $query === '' ? $url : $url . '?' . $query;
}

function onlyoffice_jwt_secret(): string
{
  return onlyoffice_env('ONLYOFFICE_JWT_SECRET');
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

function onlyoffice_read_callback_request(): array
{
  $rawBody = file_get_contents('php://input');
  if (!is_string($rawBody) || trim($rawBody) === '') {
    return [];
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
    return $decodedBody;
  }

  $verifiedPayload = onlyoffice_jwt_decode($token, $secret);

  if (isset($verifiedPayload['payload']) && is_array($verifiedPayload['payload'])) {
    return $verifiedPayload['payload'];
  }

  if (isset($verifiedPayload['status']) || isset($verifiedPayload['url'])) {
    return $verifiedPayload;
  }

  if ($tokenSource === 'header') {
    return $decodedBody;
  }

  return $verifiedPayload !== [] ? $verifiedPayload : $decodedBody;
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

function onlyoffice_download_callback_file(string $sourceUrl, string $targetPath): void
{
  onlyoffice_ensure_directory_exists(dirname($targetPath));
  $downloadUrl = onlyoffice_rewrite_docs_url_for_internal_access($sourceUrl);
  $tmpPath = tempnam(dirname($targetPath), 'onlyoffice-');
  if ($tmpPath === false) {
    throw new RuntimeException('Failed to allocate a temporary file for the callback download.');
  }

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

function onlyoffice_editor_config(): array
{
  $selectedDocument = onlyoffice_selected_minio_document();
  $version = $selectedDocument === null ? onlyoffice_read_document_version() : 1;
  $extension = onlyoffice_document_extension($selectedDocument);

  $config = [
    'document' => [
      'fileType' => $extension,
      'key' => onlyoffice_document_key($version, $selectedDocument),
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
