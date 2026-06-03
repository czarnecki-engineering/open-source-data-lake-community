<?php
declare(strict_types=1);

const ONLYOFFICE_DOCUMENTS_BUCKET = 'onlyoffice';
const ONLYOFFICE_SUPPORTED_DOCUMENT_EXTENSIONS = [
  'doc',
  'docx',
  'odt',
  'odp',
  'ods',
  'ppt',
  'pptx',
  'xls',
  'xlsx',
];

function onlyoffice_env_or_default(array $names, string $default): string
{
  foreach ($names as $name) {
    $value = getenv($name);
    if (is_string($value) && trim($value) !== '') {
      return trim($value);
    }
  }

  return $default;
}

function onlyoffice_documents_bucket(): string
{
  return onlyoffice_env_or_default(['ONLYOFFICE_DOCUMENTS_BUCKET'], ONLYOFFICE_DOCUMENTS_BUCKET);
}

function onlyoffice_selected_minio_document(): ?array
{
  $bucket = $_GET['bucket'] ?? null;
  $key = $_GET['key'] ?? null;
  $etag = $_GET['etag'] ?? null;
  $lastModified = $_GET['last_modified'] ?? null;
  $size = $_GET['size'] ?? null;

  if (!is_string($bucket) || trim($bucket) === '' || !is_string($key) || trim($key) === '') {
    return null;
  }

  $document = [
    'bucket' => trim($bucket),
    'key' => ltrim(trim($key), '/'),
  ];

  if (is_string($etag) && trim($etag) !== '') {
    $document['etag'] = trim($etag, " \t\n\r\0\x0B\"");
  }

  if (is_string($lastModified) && trim($lastModified) !== '') {
    $document['last_modified'] = trim($lastModified);
  }

  if (is_string($size) && trim($size) !== '') {
    $parsedSize = filter_var(trim($size), FILTER_VALIDATE_INT);
    if ($parsedSize !== false && $parsedSize >= 0) {
      $document['size'] = $parsedSize;
    }
  }

  return $document;
}

function onlyoffice_selected_minio_document_uri(): ?string
{
  $document = onlyoffice_selected_minio_document();
  if ($document === null) {
    return null;
  }

  return 's3://' . $document['bucket'] . '/' . $document['key'];
}

function onlyoffice_minio_endpoint(): string
{
  return rtrim(
    onlyoffice_env_or_default(['ONLYOFFICE_MINIO_ENDPOINT', 'S3_ENDPOINT_URL'], 'http://minio:9000'),
    '/'
  );
}

function onlyoffice_minio_region(): string
{
  return onlyoffice_env_or_default(['AWS_DEFAULT_REGION'], 'us-east-1');
}

function onlyoffice_minio_access_key(): string
{
  return onlyoffice_env_or_default(['AWS_ACCESS_KEY_ID', 'MINIO_ROOT_USER'], 'minioadmin');
}

function onlyoffice_minio_secret_key(): string
{
  return onlyoffice_env_or_default(['AWS_SECRET_ACCESS_KEY', 'MINIO_ROOT_PASSWORD'], 'minioadmin');
}

function onlyoffice_supported_document_extensions(): array
{
  return ONLYOFFICE_SUPPORTED_DOCUMENT_EXTENSIONS;
}

function onlyoffice_is_supported_document_key(string $key): bool
{
  $extension = strtolower(pathinfo($key, PATHINFO_EXTENSION));

  return $extension !== '' && in_array($extension, onlyoffice_supported_document_extensions(), true);
}

function onlyoffice_s3_signing_key(string $dateStamp, string $region, string $secretKey): string
{
  $dateKey = hash_hmac('sha256', $dateStamp, 'AWS4' . $secretKey, true);
  $regionKey = hash_hmac('sha256', $region, $dateKey, true);
  $serviceKey = hash_hmac('sha256', 's3', $regionKey, true);

  return hash_hmac('sha256', 'aws4_request', $serviceKey, true);
}

function onlyoffice_s3_canonical_uri(string $bucket = ''): string
{
  if ($bucket === '') {
    return '/';
  }

  return '/' . rawurlencode($bucket);
}

function onlyoffice_s3_canonical_query(array $query): string
{
  ksort($query);
  $parts = [];

  foreach ($query as $key => $value) {
    $parts[] = rawurlencode((string) $key) . '=' . rawurlencode((string) $value);
  }

  return implode('&', $parts);
}

function onlyoffice_s3_parse_xml(string $xml): SimpleXMLElement
{
  $strippedXml = preg_replace('/\sxmlns="[^"]+"/', '', $xml, 1);
  if (!is_string($strippedXml)) {
    throw new RuntimeException('Failed to normalise the MinIO XML response.');
  }

  $parsed = simplexml_load_string($strippedXml);
  if ($parsed === false) {
    throw new RuntimeException('Failed to parse the MinIO XML response.');
  }

  return $parsed;
}

function onlyoffice_s3_request(string $method, string $bucket = '', array $query = []): string
{
  $endpoint = parse_url(onlyoffice_minio_endpoint());
  if (!is_array($endpoint) || !isset($endpoint['scheme'], $endpoint['host'])) {
    throw new RuntimeException('ONLYOFFICE MinIO endpoint is invalid.');
  }

  $canonicalUri = onlyoffice_s3_canonical_uri($bucket);
  $canonicalQuery = onlyoffice_s3_canonical_query($query);
  $payloadHash = hash('sha256', '');
  $amzDate = gmdate('Ymd\THis\Z');
  $dateStamp = gmdate('Ymd');
  $hostHeader = $endpoint['host'] . (isset($endpoint['port']) ? ':' . $endpoint['port'] : '');

  $canonicalHeaders = implode("\n", [
    'host:' . $hostHeader,
    'x-amz-content-sha256:' . $payloadHash,
    'x-amz-date:' . $amzDate,
  ]) . "\n";
  $signedHeaders = 'host;x-amz-content-sha256;x-amz-date';
  $canonicalRequest = implode("\n", [
    $method,
    $canonicalUri,
    $canonicalQuery,
    $canonicalHeaders,
    $signedHeaders,
    $payloadHash,
  ]);

  $credentialScope = $dateStamp . '/' . onlyoffice_minio_region() . '/s3/aws4_request';
  $stringToSign = implode("\n", [
    'AWS4-HMAC-SHA256',
    $amzDate,
    $credentialScope,
    hash('sha256', $canonicalRequest),
  ]);
  $signature = hash_hmac(
    'sha256',
    $stringToSign,
    onlyoffice_s3_signing_key($dateStamp, onlyoffice_minio_region(), onlyoffice_minio_secret_key())
  );
  $authorization = 'AWS4-HMAC-SHA256 Credential=' . onlyoffice_minio_access_key() . '/' . $credentialScope
    . ', SignedHeaders=' . $signedHeaders
    . ', Signature=' . $signature;

  $url = $endpoint['scheme'] . '://' . $hostHeader . $canonicalUri;
  if ($canonicalQuery !== '') {
    $url .= '?' . $canonicalQuery;
  }

  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_HTTPGET => $method === 'GET',
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_CONNECTTIMEOUT => 10,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_FAILONERROR => false,
    CURLOPT_HTTPHEADER => [
      'Authorization: ' . $authorization,
      'x-amz-content-sha256: ' . $payloadHash,
      'x-amz-date: ' . $amzDate,
    ],
  ]);

  $response = curl_exec($ch);
  $error = curl_error($ch);
  $statusCode = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);

  if (!is_string($response)) {
    throw new RuntimeException('MinIO request failed: ' . ($error !== '' ? $error : 'no response body received'));
  }

  if ($statusCode < 200 || $statusCode >= 300) {
    throw new RuntimeException("MinIO request failed with HTTP {$statusCode}.");
  }

  return $response;
}

function onlyoffice_s3_authorized_headers(string $method, string $canonicalUri, string $canonicalQuery = ''): array
{
  $endpoint = parse_url(onlyoffice_minio_endpoint());
  if (!is_array($endpoint) || !isset($endpoint['host'])) {
    throw new RuntimeException('ONLYOFFICE MinIO endpoint is invalid.');
  }

  $payloadHash = hash('sha256', '');
  $amzDate = gmdate('Ymd\THis\Z');
  $dateStamp = gmdate('Ymd');
  $hostHeader = $endpoint['host'] . (isset($endpoint['port']) ? ':' . $endpoint['port'] : '');
  $canonicalHeaders = implode("\n", [
    'host:' . $hostHeader,
    'x-amz-content-sha256:' . $payloadHash,
    'x-amz-date:' . $amzDate,
  ]) . "\n";
  $signedHeaders = 'host;x-amz-content-sha256;x-amz-date';
  $canonicalRequest = implode("\n", [
    $method,
    $canonicalUri,
    $canonicalQuery,
    $canonicalHeaders,
    $signedHeaders,
    $payloadHash,
  ]);
  $credentialScope = $dateStamp . '/' . onlyoffice_minio_region() . '/s3/aws4_request';
  $stringToSign = implode("\n", [
    'AWS4-HMAC-SHA256',
    $amzDate,
    $credentialScope,
    hash('sha256', $canonicalRequest),
  ]);
  $signature = hash_hmac(
    'sha256',
    $stringToSign,
    onlyoffice_s3_signing_key($dateStamp, onlyoffice_minio_region(), onlyoffice_minio_secret_key())
  );
  $authorization = 'AWS4-HMAC-SHA256 Credential=' . onlyoffice_minio_access_key() . '/' . $credentialScope
    . ', SignedHeaders=' . $signedHeaders
    . ', Signature=' . $signature;

  return [
    'Authorization: ' . $authorization,
    'x-amz-content-sha256: ' . $payloadHash,
    'x-amz-date: ' . $amzDate,
  ];
}

function onlyoffice_minio_list_buckets(): array
{
  $root = onlyoffice_s3_parse_xml(onlyoffice_s3_request('GET'));
  $buckets = [];

  foreach ($root->Buckets->Bucket ?? [] as $bucket) {
    $name = isset($bucket->Name) ? trim((string) $bucket->Name) : '';
    if ($name === '') {
      continue;
    }

    $buckets[] = $name;
  }

  sort($buckets);

  return $buckets;
}

function onlyoffice_minio_list_objects(string $bucket): array
{
  $objects = [];
  $continuationToken = null;

  do {
    $query = ['list-type' => '2'];
    if ($continuationToken !== null) {
      $query['continuation-token'] = $continuationToken;
    }

    $root = onlyoffice_s3_parse_xml(onlyoffice_s3_request('GET', $bucket, $query));

    foreach ($root->Contents ?? [] as $content) {
      $key = isset($content->Key) ? trim((string) $content->Key) : '';
      if ($key === '' || !onlyoffice_is_supported_document_key($key)) {
        continue;
      }

      $objects[] = [
        'bucket' => $bucket,
        'key' => $key,
        'etag' => isset($content->ETag) ? trim((string) $content->ETag, "\"") : '',
        'size' => isset($content->Size) ? (int) $content->Size : 0,
        'last_modified' => isset($content->LastModified) ? (string) $content->LastModified : '',
      ];
    }

    $isTruncated = strtolower((string) ($root->IsTruncated ?? 'false')) === 'true';
    $continuationToken = $isTruncated && isset($root->NextContinuationToken)
      ? trim((string) $root->NextContinuationToken)
      : null;
  } while ($continuationToken !== null);

  usort(
    $objects,
    static fn(array $left, array $right): int => strcmp($left['key'], $right['key'])
  );

  return $objects;
}

function onlyoffice_minio_document_catalogue(): array
{
  $availableBuckets = onlyoffice_minio_list_buckets();
  $preferredBucket = onlyoffice_documents_bucket();
  $sourceBuckets = in_array($preferredBucket, $availableBuckets, true) ? [$preferredBucket] : $availableBuckets;
  $documents = [];

  foreach ($sourceBuckets as $bucket) {
    $documents = array_merge($documents, onlyoffice_minio_list_objects($bucket));
  }

  return [
    'available_buckets' => $availableBuckets,
    'documents' => $documents,
    'preferred_bucket' => $preferredBucket,
    'source_buckets' => $sourceBuckets,
  ];
}

function onlyoffice_documents_open_url(array $document): string
{
  return '/onlyoffice/editor.php?' . http_build_query([
    'bucket' => $document['bucket'],
    'key' => $document['key'],
    'etag' => $document['etag'] ?? '',
    'last_modified' => $document['last_modified'] ?? '',
    'size' => isset($document['size']) ? (string) $document['size'] : '',
  ]);
}

function onlyoffice_format_bytes(int $bytes): string
{
  if ($bytes < 1024) {
    return $bytes . ' B';
  }

  $units = ['KB', 'MB', 'GB', 'TB'];
  $size = (float) $bytes;
  $unitCount = count($units);

  foreach ($units as $index => $unit) {
    $size /= 1024;
    if ($size < 1024 || $index === $unitCount - 1) {
      return number_format($size, 1) . ' ' . $unit;
    }
  }

  return (string) $bytes . ' B';
}

function onlyoffice_format_timestamp(string $timestamp): string
{
  if ($timestamp === '') {
    return 'n/a';
  }

  try {
    $date = new DateTimeImmutable($timestamp);
  } catch (Throwable) {
    return $timestamp;
  }

  return $date->format('Y-m-d H:i:s T');
}
