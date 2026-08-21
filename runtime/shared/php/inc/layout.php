<?php
declare(strict_types=1);

$page_title = $page_title ?? ($pageTitle ?? 'Knowledge Lake Local Runtime');
$page_description = $page_description ?? ($pageDescription ?? '');
$content = $content ?? '';

$PUBLIC_BASE = 'https://czarneckii.com';
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title><?= htmlspecialchars($page_title) ?></title>

  <?php if ($page_description !== ''): ?>
    <meta name="description" content="<?= htmlspecialchars($page_description) ?>">
  <?php endif; ?>

  <link rel="stylesheet" href="<?= $PUBLIC_BASE ?>/css/site.css">
  <link rel="icon" type="image/svg+xml" href="<?= $PUBLIC_BASE ?>/favicon.svg">
  <link rel="alternate icon" type="image/png" sizes="32x32" href="<?= $PUBLIC_BASE ?>/favicon-32x32.png">
  <link rel="alternate icon" type="image/png" sizes="16x16" href="<?= $PUBLIC_BASE ?>/favicon-16x16.png">
  <link rel="apple-touch-icon" href="<?= $PUBLIC_BASE ?>/apple-touch-icon.png">
  <link rel="manifest" href="<?= $PUBLIC_BASE ?>/site.webmanifest">
  <meta name="theme-color" content="#0B1F3B">
</head>
<body>

<nav class="navbar">
  <div class="container nav-inner">
    <div class="nav-brand">
      <a href="<?= $PUBLIC_BASE ?>/">
        <img src="<?= $PUBLIC_BASE ?>/brand-logo.svg" alt="Open Data Lake" style="height:50px;width:auto">
      </a>
    </div>

    <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false" aria-controls="site-menu">
      <span class="nav-toggle-bar"></span>
      <span class="nav-toggle-bar"></span>
      <span class="nav-toggle-bar"></span>
    </button>

    <ul id="site-menu" class="nav-menu">
      <li><a href="<?= $PUBLIC_BASE ?>/">Home</a></li>
      <li><a href="<?= $PUBLIC_BASE ?>/products/">Products</a></li>
      <li><a href="<?= $PUBLIC_BASE ?>/tiers/compare/">Compare</a></li>
      <li><a href="<?= $PUBLIC_BASE ?>/local/">My Data Lake</a></li>
      <li><a href="<?= $PUBLIC_BASE ?>/services/">Services</a></li>
      <li><a href="<?= $PUBLIC_BASE ?>/insights/">Insights</a></li>
      <li><a href="<?= $PUBLIC_BASE ?>/case-studies/">Case Studies</a></li>
      <li><a href="<?= $PUBLIC_BASE ?>/contact/">Contact</a></li>
    </ul>
  </div>

  <script>
    (function () {
      var toggle = document.querySelector(".nav-toggle");
      var menu = document.getElementById("site-menu");
      if (!toggle || !menu) return;
      toggle.addEventListener("click", function () {
        var open = menu.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
    })();
  </script>
</nav>

<main>
  <div class="container">
    <?= $content ?>
  </div>
</main>

<footer class="footer">
  <div class="container">
    <p>© 2026 Marek Czarnecki.</p>
  </div>
</footer>

</body>
</html>
