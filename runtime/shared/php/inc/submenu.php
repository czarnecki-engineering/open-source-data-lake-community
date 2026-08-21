<?php
declare(strict_types=1);

function render_primary_submenu(string $current): void
{
    $items = [
        'services' => ['label' => 'Services', 'url' => '/index.php'],
        'health' => ['label' => 'Health', 'url' => '/health.php'],
        'solutions' => ['label' => 'Solutions', 'url' => '/solutions.php'],
    ];

    $parts = [];
    foreach ($items as $key => $item) {
        if ($key === $current) {
            $parts[] = htmlspecialchars($item['label']);
            continue;
        }

        $parts[] = sprintf(
            '<a href="%s">%s</a>',
            htmlspecialchars($item['url']),
            htmlspecialchars($item['label'])
        );
    }

    echo '<h3>' . implode(' &nbsp; ', $parts) . '</h3>';
}
