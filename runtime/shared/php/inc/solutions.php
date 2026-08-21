<?php
declare(strict_types=1);

function solution_metadata(string $path): array
{
    $source = file_get_contents($path);
    if ($source === false) {
        return [];
    }

    $title = null;
    $summary = null;
    $tag = null;

    if (preg_match('/Solution Title:\s*(.+)/', $source, $matches) === 1) {
        $title = trim($matches[1]);
    }

    if (preg_match('/Solution Summary:\s*(.+)/', $source, $matches) === 1) {
        $summary = trim($matches[1]);
    }

    if (preg_match('/Solution Tag:\s*(.+)/', $source, $matches) === 1) {
        $tag = trim($matches[1]);
    }

    return [
        'title' => $title,
        'summary' => $summary,
        'tag' => $tag,
    ];
}

function enabled_solution_tags(): array
{
    $raw = trim((string) getenv('ENABLED_SOLUTION_TAGS'));
    if ($raw === '') {
        return [];
    }

    return array_values(array_filter(array_map('trim', explode(',', $raw))));
}

function discovered_solutions_report(string $solutionsDir): array
{
    $report = [
        'entries' => [],
        'warnings' => [],
    ];

    if (!is_dir($solutionsDir)) {
        $report['warnings'][] = 'Solutions directory is missing.';
        return $report;
    }

    $enabledTags = enabled_solution_tags();
    $enabledTagLookup = array_fill_keys($enabledTags, true);
    $files = glob($solutionsDir . '/*.php') ?: [];
    sort($files);

    foreach ($files as $path) {
        $basename = basename($path);
        $metadata = solution_metadata($path);
        $title = trim((string) ($metadata['title'] ?? ''));
        $summary = trim((string) ($metadata['summary'] ?? ''));
        $tag = trim((string) ($metadata['tag'] ?? ''));

        $issues = [];
        if ($title === '') {
            $issues[] = 'missing Solution Title';
        }
        if ($summary === '') {
            $issues[] = 'missing Solution Summary';
        }

        if ($issues !== []) {
            $report['warnings'][] = sprintf(
                '%s ignored: %s.',
                $basename,
                implode(', ', $issues)
            );
            continue;
        }

        if ($tag !== '') {
            if ($enabledTags === []) {
                $report['warnings'][] = sprintf(
                    '%s ignored: tagged "%s" but ENABLED_SOLUTION_TAGS is unset.',
                    $basename,
                    $tag
                );
                continue;
            }

            if (!isset($enabledTagLookup[$tag])) {
                $report['warnings'][] = sprintf(
                    '%s ignored: tag "%s" is not enabled.',
                    $basename,
                    $tag
                );
                continue;
            }
        }

        $report['entries'][] = [
            'file' => $basename,
            'url' => '/solutions/' . $basename,
            'title' => $title,
            'summary' => $summary,
            'tag' => $tag === '' ? null : $tag,
        ];
    }

    return $report;
}

