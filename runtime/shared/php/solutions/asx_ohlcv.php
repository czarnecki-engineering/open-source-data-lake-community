<?php
declare(strict_types=1);

require __DIR__ . '/../inc/submenu.php';

/*
Solution Title: ASX Publication Research
Solution Summary: Runs publication-derived ASX return-predictability research on public Yahoo/yFinance data through the Community data-lake pipeline.
*/

$airflowUrl = 'http://127.0.0.1:8080/';
$jupyterUrl = 'http://127.0.0.1:8888/';

$pipelineSteps = [
    [
        'step' => '1',
        'name' => 'Build sector map',
        'dag' => 'asx_sector_map_curated',
        'path' => 'runtime/shared/dags/asx_sector_map_curated.py',
        'purpose' => 'Build the current Yahoo-derived ASX sector reference map used by the pairs-trading research.',
        'url' => $airflowUrl,
    ],
    [
        'step' => '2a',
        'name' => 'Ingest OHLCV raw data',
        'dag' => 'asx_ohlcv_raw',
        'path' => 'runtime/shared/dags/asx_ohlcv_raw.py',
        'purpose' => 'Download configured ASX OHLCV history from Yahoo Finance into the MinIO raw zone.',
        'url' => $airflowUrl,
    ],
    [
        'step' => '2b',
        'name' => 'Transform raw to conformed',
        'dag' => 'asx_ohlcv_raw_to_conformed',
        'path' => 'runtime/shared/dags/asx_ohlcv_raw_to_conformed.py',
        'purpose' => 'Normalise raw OHLCV records into conformed Parquet objects.',
        'url' => $airflowUrl,
    ],
    [
        'step' => '2c',
        'name' => 'Build curated research panel',
        'dag' => 'asx_ohlcv_conformed_to_curated',
        'path' => 'runtime/shared/dags/asx_ohlcv_conformed_to_curated.py',
        'purpose' => 'Combine conformed ticker histories into the curated ASX research panel.',
        'url' => $airflowUrl,
    ],
    [
        'step' => '2d',
        'name' => 'Materialise Iceberg summary',
        'dag' => 'asx_ohlcv_curated_to_iceberg',
        'path' => 'runtime/shared/dags/asx_ohlcv_curated_to_iceberg.py',
        'purpose' => 'Materialise the curated ASX summary into Lakekeeper/Iceberg and validate Trino access.',
        'url' => $airflowUrl,
    ],
    [
        'step' => '3',
        'name' => 'Run publication research notebook',
        'dag' => 'asx_publication_research.ipynb',
        'path' => 'runtime/shared/notebooks/asx_publication_research.ipynb',
        'purpose' => 'Run the four strategy families, statistical inference, publication comparison, and result plots.',
        'url' => $jupyterUrl,
    ],
];

$headlineResults = [
    ['strategy' => 'Trend Following', 'public' => 'Supported after Holm', 'publication' => 'Not supported after Holm'],
    ['strategy' => 'Mean Reversion', 'public' => 'Not supported after Holm', 'publication' => 'Not supported after Holm'],
    ['strategy' => 'Pairs Trading', 'public' => 'Not supported after Holm', 'publication' => 'Not supported after Holm'],
    ['strategy' => 'Tax-Loss Selling', 'public' => 'Supported after Holm', 'publication' => 'Not supported after Holm'],
];

ob_start();
?>
<h1>ASX Publication Research</h1>
<?php render_primary_submenu('solutions'); ?>

<div class="card">
  <h2>Purpose</h2>
  <p>
    This solution applies publication-derived ASX return-predictability methodology to a publicly reproducible
    Yahoo/yFinance dataset inside the Open Data Lake Community architecture.
  </p>
  <p>
    It is <strong>not</strong> a replication of the licensed Norgate publication dataset. The objective is to show
    how the same broad research framework behaves in a weaker but reproducible public-data environment and to make
    the data-quality boundary explicit.
  </p>
</div>

<div class="card">
  <h2>Execution Sequence</h2>
  <p>
    Run the Airflow DAGs in the order shown below, then execute the Jupyter notebook.
    This page is read-only and does not trigger Airflow, mutate MinIO, or execute the notebook.
  </p>
  <div style="max-width: 100%; overflow-x: auto;">
    <table class="tiers-compare" style="width: 100%; table-layout: fixed;">
      <thead>
        <tr>
          <th style="width: 8%;">Step</th>
          <th style="width: 26%;">Action</th>
          <th style="width: 28%;">DAG / Notebook</th>
          <th style="width: 38%;">Repository Path</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($pipelineSteps as $row): ?>
          <tr>
            <td><strong><?= htmlspecialchars($row['step']) ?></strong></td>
            <td>
              <strong><?= htmlspecialchars($row['name']) ?></strong><br>
              <small><?= htmlspecialchars($row['purpose']) ?></small>
            </td>
            <td style="overflow-wrap: anywhere; word-break: break-word;">
              <a href="<?= htmlspecialchars($row['url']) ?>" target="_blank" rel="noopener">
                <code><?= htmlspecialchars($row['dag']) ?></code>
              </a>
            </td>
            <td style="overflow-wrap: anywhere; word-break: break-word;">
              <code><?= htmlspecialchars($row['path']) ?></code>
            </td>
          </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  </div>
</div>

<div class="card">
  <h2>Research Workflow</h2>
  <ul>
    <li>Build the public ASX research panel from the curated OHLCV dataset.</li>
    <li>Use STW.AX as the public benchmark proxy and the RBA cash-rate TRI as the risk-free series.</li>
    <li>Run Trend Following, Mean Reversion, Pairs Trading, and Tax-Loss Selling.</li>
    <li>Apply publication-style walk-forward evaluation where applicable.</li>
    <li>Apply ex-ante liquidity-tier transaction costs.</li>
    <li>Run deterministic bootstrap confidence intervals, sign-flip tests, and Holm correction.</li>
    <li>Compare the public Yahoo/STW findings with frozen publication/Norgate evidence.</li>
    <li>Render four plots covering fold effects, primary effects and confidence intervals, Tax-Loss annual effects, and Yahoo-versus-publication effects.</li>
  </ul>
</div>

<div class="card">
  <h2>Headline Results</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th>Strategy</th>
        <th>Public Yahoo/STW implementation</th>
        <th>Publication/Norgate evidence</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($headlineResults as $row): ?>
        <tr>
          <td><strong><?= htmlspecialchars($row['strategy']) ?></strong></td>
          <td><?= htmlspecialchars($row['public']) ?></td>
          <td><?= htmlspecialchars($row['publication']) ?></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
  <p>
    Different support decisions are treated as evidence of sensitivity to the data and design environment,
    not as a failed reproduction attempt.
  </p>
</div>

<div class="card">
  <h2>Data and Method Limitations</h2>
  <ul>
    <li>The Yahoo/yFinance security universe is retrospective, not historical point-in-time ASX 200 membership.</li>
    <li>Security identity is ticker-based rather than permanent Norgate asset identity.</li>
    <li>Yahoo delisting and historical coverage are incomplete and vendor-dependent.</li>
    <li>STW.AX is a public ETF benchmark proxy rather than the publication benchmark series.</li>
    <li>Yahoo adjusted-price conventions differ from the publication/Norgate price convention.</li>
    <li>The sector map is current Yahoo-derived classification, not historical point-in-time classification.</li>
  </ul>
</div>

<div class="card">
  <h2>Primary Runtime Artifacts</h2>
  <table class="tiers-compare">
    <tbody>
      <tr>
        <td style="width: 280px;"><strong>Curated OHLCV research panel</strong></td>
        <td><code>s3://curated/tabular/market_ohlcv_daily_v2/exchange=ASX/asx_ohlcv_panel_curated.parquet</code></td>
      </tr>
      <tr>
        <td><strong>Curated sector map</strong></td>
        <td><code>s3://curated/tabular/asx_ticker_sector_map_v1/exchange=ASX/asx_ticker_sector_map.parquet</code></td>
      </tr>
      <tr>
        <td><strong>Research notebook</strong></td>
        <td><code>runtime/shared/notebooks/asx_publication_research.ipynb</code></td>
      </tr>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Interpretation Boundary</h2>
  <p>
    The correct description of this solution is:
    <strong>publication-derived methodology demonstrated on a publicly reproducible ASX dataset, with explicit comparison to publication evidence showing data/design sensitivity.</strong>
  </p>
</div>

<?php
$content = ob_get_clean();
$page_title = 'Knowledge Lake Solution - ASX Publication Research';
$page_description = 'Read-only ASX publication research solution page for the public Yahoo/yFinance Community data-lake implementation.';
require __DIR__ . '/../inc/layout.php';
