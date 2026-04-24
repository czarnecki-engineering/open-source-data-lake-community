<?php
declare(strict_types=1);

require __DIR__ . '/../../php/inc/submenu.php';

/*
Solution Title: File Only Demo
Solution Summary: Minimal example overlay that proves additive PHP content works without an overlay compose file.
*/

$page_title = 'File Only Demo';
$page_description = 'Minimal file-only overlay example.';

ob_start();
?>
<h1>File Only Demo</h1>
<?php render_primary_submenu('solutions'); ?>

<p>
  This page comes from the <code>overlay_file_only_demo</code> example overlay.
</p>

<p>
  It proves the simplest overlay path: install additive files into the normal runtime folders and
  start the base stack with plain <code>./start-compose.sh</code>.
</p>

<div class="card">
  <h2>Why No Compose YAML?</h2>
  <p>
    The base PHP container already mounts <code>./php</code> into the runtime, so this overlay only needs to add
    <code>php/solutions/file_only_demo.php</code>.
  </p>
</div>
<?php
$content = ob_get_clean();
require __DIR__ . '/../../php/inc/layout.php';
