<?php
declare(strict_types=1);

const ONLYOFFICE_DOCUMENT_RELATIVE_PATH = 'onlyoffice/community-prototype.docx';

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

function onlyoffice_document_relative_path(): string
{
  return ONLYOFFICE_DOCUMENT_RELATIVE_PATH;
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

function onlyoffice_document_key(int $version): string
{
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

function onlyoffice_download_url(): string
{
  return onlyoffice_storage_internal_url() . '/onlyoffice/download.php';
}

function onlyoffice_callback_url(): string
{
  return onlyoffice_storage_internal_url() . '/onlyoffice/callback.php';
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

function onlyoffice_editor_config(): array
{
  $version = onlyoffice_read_document_version();

  $config = [
    'document' => [
      'fileType' => 'docx',
      'key' => onlyoffice_document_key($version),
      'title' => onlyoffice_document_title(),
      'url' => onlyoffice_download_url(),
    ],
    'documentType' => 'word',
    'editorConfig' => [
      'callbackUrl' => onlyoffice_callback_url(),
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
