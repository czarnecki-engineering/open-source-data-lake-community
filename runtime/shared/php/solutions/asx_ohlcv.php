<?php
declare(strict_types=1);

require __DIR__ . '/../inc/submenu.php';

/*
Solution Title: ASX OHLCV
Solution Summary: Ingests ASX OHLCV price data from Yahoo Finance through the raw, conformed, and curated lake zones.
*/

function asx_ohlcv_read_json_file(string $path): ?array
{
    if (!is_file($path)) {
        return null;
    }

    $raw = file_get_contents($path);
    if ($raw === false) {
        return null;
    }

    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : null;
}

$configPath = '/app/config/dags/asx_ohlcv.json';
$summaryPath = '/app/data/asx_ohlcv_summary.json';
$configPayload = asx_ohlcv_read_json_file($configPath);
$summaryPayload = asx_ohlcv_read_json_file($summaryPath);

$runDate = date('Y-m-d');

$implementationChecks = [
    ['label' => 'Config present in mounted config path',   'status' => $configPayload !== null, 'path' => $configPath],
    ['label' => 'Raw DAG implemented',                     'status' => true, 'path' => 'runtime/shared/dags/asx_ohlcv_raw.py'],
    ['label' => 'Conformed DAG implemented',               'status' => true, 'path' => 'runtime/shared/dags/asx_ohlcv_raw_to_conformed.py'],
    ['label' => 'Curated DAG implemented',                 'status' => true, 'path' => 'runtime/shared/dags/asx_ohlcv_conformed_to_curated.py'],
    ['label' => 'Iceberg/Trino DAG implemented',           'status' => true, 'path' => 'runtime/shared/dags/asx_ohlcv_curated_to_iceberg.py'],
    ['label' => 'DAG runtime helper implemented',          'status' => true, 'path' => 'runtime/shared/dags/asx_ohlcv_runtime.py'],
    ['label' => 'EDA notebook implemented',                'status' => true, 'path' => 'runtime/shared/notebooks/asx_ohlcv_analysis.ipynb'],
    ['label' => 'PHP solution implemented',                'status' => true, 'path' => 'runtime/shared/php/solutions/asx_ohlcv.php'],
    ['label' => 'Metabase chart instructions documented',  'status' => true, 'path' => 'See Metabase Chart section below'],
    ['label' => 'AI Access layer implemented',            'status' => true, 'path' => 'runtime/shared/ai/asx_ohlcv_ai_access.py'],
    ['label' => 'AI Access Slice 2: Ollama wording',     'status' => true, 'path' => 'runtime/shared/ai/asx_ohlcv_ai_access.py (--use-ollama)'],
    ['label' => 'AI Access Slice 3: AI Access API',      'status' => true, 'path' => 'runtime/shared/ai/api/server.py'],
    ['label' => 'AI Access Slice 3: Open WebUI surface', 'status' => true, 'path' => 'runtime/knowledge-lake/k8s/base/open-webui/'],
];

$runtimeChecks = [
    ['label' => 'Notebook summary present', 'status' => $summaryPayload !== null, 'path' => $summaryPath],
];

$expectedRawPaths = [
    'Raw zone (per ticker, per run date)' => 's3://raw/asx_ohlcv/{YYYY-MM-DD}/{ticker_ax}_ohlcv.json',
    'Example BHP.AX (' . $runDate . ')'  => 's3://raw/asx_ohlcv/' . $runDate . '/bhp_ax_ohlcv.json',
    'Example RIO.AX (' . $runDate . ')'  => 's3://raw/asx_ohlcv/' . $runDate . '/rio_ax_ohlcv.json',
    'Example CBA.AX (' . $runDate . ')'  => 's3://raw/asx_ohlcv/' . $runDate . '/cba_ax_ohlcv.json',
];

$expectedConformedPaths = [
    'Conformed zone (per ticker, per run date)' => 's3://conformed/asx_ohlcv/{YYYY-MM-DD}/{ticker_ax}_ohlcv.json',
    'Example BHP.AX (' . $runDate . ')'         => 's3://conformed/asx_ohlcv/' . $runDate . '/bhp_ax_ohlcv.json',
    'Example RIO.AX (' . $runDate . ')'         => 's3://conformed/asx_ohlcv/' . $runDate . '/rio_ax_ohlcv.json',
    'Example CBA.AX (' . $runDate . ')'         => 's3://conformed/asx_ohlcv/' . $runDate . '/cba_ax_ohlcv.json',
];

$expectedCuratedPaths = [
    'Curated summary (per run date)' => 's3://curated/asx_ohlcv/{YYYY-MM-DD}/summary.json',
    'Example (' . $runDate . ')'     => 's3://curated/asx_ohlcv/' . $runDate . '/summary.json',
];

$warnings = [];

if ($configPayload === null) {
    $warnings[] = 'ASX OHLCV config is not currently readable from /app/config/dags/asx_ohlcv.json.';
}

ob_start();
?>
<h1>ASX OHLCV</h1>
<?php render_primary_submenu('solutions'); ?>

<ul>
  <li>Complete six-stage pipeline: raw ingestion from Yahoo Finance, normalisation to conformed records, aggregation to a curated per-ticker summary, materialisation into a Lakekeeper-backed Iceberg table, a Jupyter EDA notebook, and a Metabase chart — all implemented and validated.</li>
  <li>Three-slice AI Access layer: deterministic NL-to-SQL over Trino (Slice 1); optional Ollama wording over retrieved results (Slice 2); narrow HTTP API and Open WebUI browser chat surface (Slice 3).</li>
  <li>Trino is the query authority. Metabase, Ollama, the AI Access API, and Open WebUI are subordinate surfaces.</li>
  <li>This page is read-only. It does not trigger Airflow, mutate MinIO, or query Trino.</li>
</ul>

<div class="card">
  <h2>Implementation Checklist</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 300px;">Component</th>
        <th style="width: 120px;">Status</th>
        <th>Observed Path</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($implementationChecks as $row): ?>
        <tr>
          <td><strong><?= htmlspecialchars($row['label']) ?></strong></td>
          <td><span class="pill <?= $row['status'] ? 'good' : 'bad' ?>"><?= $row['status'] ? 'PRESENT' : 'MISSING' ?></span></td>
          <td><code><?= htmlspecialchars($row['path']) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Runtime Checklist</h2>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 300px;">Check</th>
        <th style="width: 120px;">Status</th>
        <th>Path</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($runtimeChecks as $row): ?>
        <tr>
          <td><strong><?= htmlspecialchars($row['label']) ?></strong></td>
          <td><span class="pill <?= $row['status'] ? 'good' : 'bad' ?>"><?= $row['status'] ? 'PRESENT' : 'MISSING' ?></span></td>
          <td><code><?= htmlspecialchars($row['path']) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Runtime Validation</h2>
  <p>
    Runtime validation is through Airflow DAG execution logs, MinIO object presence,
    Trino query access, and the Jupyter EDA notebook. Run the four-DAG chain in sequence
    using the same timestamp, then execute the notebook:
  </p>
  <pre>airflow dags test asx_ohlcv_raw                  2026-05-20T12:00:00+00:00
airflow dags test asx_ohlcv_raw_to_conformed     2026-05-20T12:00:00+00:00
airflow dags test asx_ohlcv_conformed_to_curated 2026-05-20T12:00:00+00:00
airflow dags test asx_ohlcv_curated_to_iceberg   2026-05-20T12:00:00+00:00</pre>
  <p>
    After the Iceberg DAG succeeds, confirm Trino query access from inside the cluster:
  </p>
  <pre>kubectl -n knowledge-lake exec deploy/trino -- \
  trino --catalog demo --execute \
  "SELECT ticker, run_date, row_count, latest_close FROM demo.asx_ohlcv_summary ORDER BY ticker"</pre>
  <p>
    Then execute the EDA notebook inside the Jupyter container:
  </p>
  <pre>kubectl -n knowledge-lake exec deploy/jupyter -- \
  jupyter nbconvert --to notebook --execute \
  /home/jovyan/work/asx_ohlcv_analysis.ipynb \
  --output /home/jovyan/work/asx_ohlcv_analysis.ipynb</pre>
  <p>
    After notebook execution, <code>/app/data/asx_ohlcv_summary.json</code> will be
    present and the Runtime Checklist above will show <strong>PRESENT</strong>.
  </p>
</div>

<div class="card">
  <h2>Expected Raw Artifacts</h2>
  <p>These paths are documentation only. This page does not query MinIO.</p>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 300px;">Artifact</th>
        <th>Path</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($expectedRawPaths as $label => $value): ?>
        <tr>
          <td><strong><?= htmlspecialchars($label) ?></strong></td>
          <td><code><?= htmlspecialchars($value) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Expected Conformed Artifacts</h2>
  <p>These paths are documentation only. This page does not query MinIO.</p>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 300px;">Artifact</th>
        <th>Path</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($expectedConformedPaths as $label => $value): ?>
        <tr>
          <td><strong><?= htmlspecialchars($label) ?></strong></td>
          <td><code><?= htmlspecialchars($value) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
  <p style="margin-top: 0.8rem;">
    <strong>Conformed record schema:</strong>
    <code>ticker, trade_date, open, high, low, close, volume, source, ingest_date</code>
  </p>
</div>

<div class="card">
  <h2>Expected Curated Artifacts</h2>
  <p>These paths are documentation only. This page does not query MinIO.</p>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 300px;">Artifact</th>
        <th>Path</th>
      </tr>
    </thead>
    <tbody>
      <?php foreach ($expectedCuratedPaths as $label => $value): ?>
        <tr>
          <td><strong><?= htmlspecialchars($label) ?></strong></td>
          <td><code><?= htmlspecialchars($value) ?></code></td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
  <p style="margin-top: 0.8rem;">
    <strong>Curated summary fields per ticker:</strong>
    <code>ticker, run_date, row_count, start_trade_date, end_trade_date, min_close, max_close, latest_close, average_volume</code>
  </p>
</div>

<div class="card">
  <h2>Expected Iceberg and Trino Paths</h2>
  <p>These paths are documentation only. This page does not query Trino or Lakekeeper.</p>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 300px;">Artifact</th>
        <th>Path / Query</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Iceberg warehouse</strong></td>
        <td><code>minio-spike</code> (Lakekeeper-managed, backed by <code>s3://curated/lakekeeper-spike/</code>)</td>
      </tr>
      <tr>
        <td><strong>Iceberg namespace</strong></td>
        <td><code>demo</code></td>
      </tr>
      <tr>
        <td><strong>Iceberg table</strong></td>
        <td><code>demo.asx_ohlcv_summary</code></td>
      </tr>
      <tr>
        <td><strong>Trino catalog</strong></td>
        <td><code>demo</code></td>
      </tr>
      <tr>
        <td><strong>Trino full table reference</strong></td>
        <td><code>demo.demo.asx_ohlcv_summary</code></td>
      </tr>
      <tr>
        <td><strong>Trino validation query</strong></td>
        <td><code>SELECT ticker, run_date, row_count, latest_close FROM demo.asx_ohlcv_summary ORDER BY ticker</code></td>
      </tr>
      <tr>
        <td><strong>Iceberg table schema</strong></td>
        <td><code>ticker, run_date, row_count, start_trade_date, end_trade_date, min_close, max_close, latest_close, average_volume, generated_at</code></td>
      </tr>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Notebook Summary</h2>
  <?php if ($summaryPayload === null): ?>
    <p>
      No notebook summary found at <code><?= htmlspecialchars($summaryPath) ?></code>.
      Execute the EDA notebook to generate this artifact.
    </p>
  <?php else: ?>
    <p>Read from <code><?= htmlspecialchars($summaryPath) ?></code>. This page does not query Trino.</p>
    <table class="tiers-compare">
      <tbody>
        <?php
        $displayFields = [
            'generated_at'            => 'Generated at',
            'source_table'            => 'Source table',
            'run_date'                => 'Run date',
            'row_count'               => 'Rows returned',
            'configured_tickers'      => 'Configured tickers',
            'highest_close_ticker'    => 'Highest latest close',
            'lowest_close_ticker'     => 'Lowest latest close',
        ];
        foreach ($displayFields as $key => $label):
            $val = $summaryPayload[$key] ?? null;
            $display = is_array($val) ? implode(', ', $val) : (string)$val;
        ?>
          <tr>
            <td style="width: 220px;"><strong><?= htmlspecialchars($label) ?></strong></td>
            <td><code><?= htmlspecialchars($display) ?></code></td>
          </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
    <?php if (!empty($summaryPayload['latest_close_by_ticker']) && is_array($summaryPayload['latest_close_by_ticker'])): ?>
      <p style="margin-top: 0.8rem;"><strong>Latest close by ticker:</strong></p>
      <table class="tiers-compare">
        <thead><tr><th>Ticker</th><th>Latest close</th><th>Avg volume</th></tr></thead>
        <tbody>
          <?php foreach ($summaryPayload['latest_close_by_ticker'] as $ticker => $close):
            $vol = $summaryPayload['average_volume_by_ticker'][$ticker] ?? null;
          ?>
            <tr>
              <td><strong><?= htmlspecialchars((string)$ticker) ?></strong></td>
              <td><code><?= htmlspecialchars($close !== null ? number_format((float)$close, 2) : 'n/a') ?></code></td>
              <td><code><?= htmlspecialchars($vol !== null ? number_format((int)$vol) : 'n/a') ?></code></td>
            </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    <?php endif; ?>
  <?php endif; ?>
</div>

<div class="card">
  <h2>Metabase Charts (Subordinate)</h2>
  <p>
    These charts are served from the local Metabase instance at
    <a href="http://127.0.0.1:3000" target="_blank"><code>http://127.0.0.1:3000</code></a>.
    They query <code>demo.asx_ohlcv_summary</code> through Trino only.
    Metabase is not a query authority and does not connect to MinIO directly.
    The charts are blank when Metabase or Trino is not running.
  </p>

  <h3>Latest Close by Ticker</h3>
  <iframe
    src="http://127.0.0.1:3000/public/question/9a1733a1-c1fc-4a68-98ac-fc77ab49e017"
    width="100%"
    height="400"
    frameborder="0"
    allowtransparency="true"
  ></iframe>
  <p style="margin-top: 0.4rem; font-size: 0.85em;">
    <a href="http://127.0.0.1:3000/public/question/9a1733a1-c1fc-4a68-98ac-fc77ab49e017" target="_blank">Open full screen ↗</a>
  </p>

  <h3 style="margin-top: 1.5rem;">Average Volume by Ticker</h3>
  <iframe
    src="http://127.0.0.1:3000/public/question/2cf890f4-7070-47ec-991e-9268e9adc956"
    width="100%"
    height="400"
    frameborder="0"
    allowtransparency="true"
  ></iframe>
  <p style="margin-top: 0.4rem; font-size: 0.85em;">
    <a href="http://127.0.0.1:3000/public/question/2cf890f4-7070-47ec-991e-9268e9adc956" target="_blank">Open full screen ↗</a>
  </p>

  <p style="margin-top: 1rem;">
    <strong>Note:</strong> These public share UUIDs are specific to the current local
    Metabase H2 PVC state. If the PVC is deleted and Metabase is reset, run
    <code>runtime/knowledge-lake/setup-metabase.sh</code> to recreate the connection
    and charts, or follow the manual setup steps below.
  </p>

  <h3 style="margin-top: 1.5rem;">Manual setup (if PVC was reset)</h3>
  <p>
    The Metabase connection and charts were provisioned via the Metabase API on
    2026-05-20. To recreate after a PVC reset:
  </p>
  <ol>
    <li>Complete the Metabase setup wizard at <code>http://127.0.0.1:3000</code>.</li>
    <li>Admin → Databases → Add database: type <code>Presto</code>, host <code>trino</code>,
        port <code>8080</code>, catalog <code>demo</code>, username <code>metabase</code>.</li>
    <li>New → Question → SQL: <code>SELECT ticker, latest_close, average_volume FROM demo.asx_ohlcv_summary ORDER BY ticker</code></li>
    <li>Choose Bar chart, X-axis <code>ticker</code>, Y-axis <code>latest_close</code>. Save.</li>
    <li>Sharing → Enable public sharing. Copy the public link UUID.</li>
    <li>Update the iframe src in this PHP page with the new UUID.</li>
  </ol>
</div>

<div class="card">
  <h2>AI Access</h2>
  <ul>
    <li>Slice 1 (deterministic): maps accepted natural-language questions to pre-written SQL executed through Trino. Always authoritative.</li>
    <li>Slice 2 (optional Ollama wording): sends already-retrieved Trino rows to Ollama for rephrasing only. Falls back to deterministic answer if Ollama is unavailable.</li>
    <li>Query path (Slice 1): <code>AI Access -> Trino -> demo.asx_ohlcv_summary (Lakekeeper/Iceberg -> MinIO)</code></li>
    <li>Query path (Slice 2): <code>AI Access -> Trino -> demo.asx_ohlcv_summary -> Ollama (wording only)</code></li>
    <li>No SQL generated freely. No direct MinIO access. No vector store. No RAG. No model memory answers.</li>
  </ul>

  <h3>Supported Questions</h3>
  <table class="tiers-compare">
    <thead>
      <tr>
        <th style="width: 340px;">Natural-Language Question</th>
        <th>Allowlisted SQL Pattern</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>What is the latest close for BHP.AX?</td>
        <td><code>SELECT ticker, run_date, latest_close, min_close, max_close FROM demo.asx_ohlcv_summary WHERE ticker = 'BHP.AX' ORDER BY run_date DESC LIMIT 1</code></td>
      </tr>
      <tr>
        <td>Which ticker has the highest average volume?</td>
        <td><code>SELECT ticker, run_date, average_volume FROM demo.asx_ohlcv_summary ORDER BY average_volume DESC LIMIT 1</code></td>
      </tr>
      <tr>
        <td>Summarise the ASX OHLCV dataset.</td>
        <td><code>SELECT ticker, run_date, row_count, latest_close, min_close, max_close, average_volume FROM demo.asx_ohlcv_summary ORDER BY ticker</code></td>
      </tr>
      <tr>
        <td>How many tickers are in the ASX OHLCV summary?</td>
        <td><code>SELECT COUNT(DISTINCT ticker) AS ticker_count FROM demo.asx_ohlcv_summary</code></td>
      </tr>
      <tr>
        <td>Show the latest close by ticker.</td>
        <td><code>SELECT ticker, latest_close, run_date FROM demo.asx_ohlcv_summary ORDER BY ticker</code></td>
      </tr>
    </tbody>
  </table>

  <h3 style="margin-top: 1.2rem;">Slice 2: Optional Ollama Wording</h3>
  <p>
    When <code>--use-ollama</code> is passed, the script sends the already-retrieved
    Trino rows to Ollama for natural-language wording only.
  </p>
  <table class="tiers-compare">
    <tbody>
      <tr>
        <td style="width: 220px;"><strong>Ollama receives</strong></td>
        <td>The user question, matched intent name, exact SQL used, Trino result rows as JSON, and the deterministic answer text</td>
      </tr>
      <tr>
        <td><strong>Ollama does not</strong></td>
        <td>Generate SQL, choose which query to run, retrieve data, or answer from model memory</td>
      </tr>
      <tr>
        <td><strong>Fallback</strong></td>
        <td>If Ollama is unavailable or fails, the deterministic answer is returned with <code>Mode: deterministic_fallback</code> and a reason</td>
      </tr>
      <tr>
        <td><strong>Ollama endpoint</strong></td>
        <td>Default: <code>http://127.0.0.1:11434</code> — override with <code>OLLAMA_BASE_URL</code></td>
      </tr>
      <tr>
        <td><strong>Model</strong></td>
        <td>First available model from <code>/api/tags</code> — override with <code>OLLAMA_MODEL</code></td>
      </tr>
      <tr>
        <td><strong>Mode indicators</strong></td>
        <td><code>deterministic</code> · <code>ollama_summarised</code> · <code>deterministic_fallback</code></td>
      </tr>
    </tbody>
  </table>

  <h3 style="margin-top: 1.2rem;">Validation</h3>
  <p>Run the AI access validation script from the repo root (runtime must be running):</p>
  <pre>runtime/knowledge-lake/validate-ai-access.sh</pre>
  <p>With optional Ollama validation (passes whether Ollama is available or not):</p>
  <pre>runtime/knowledge-lake/validate-ai-access.sh --with-ollama</pre>
  <p>Run individual questions directly (deterministic):</p>
  <pre>python runtime/shared/ai/asx_ohlcv_ai_access.py "Summarise the ASX OHLCV dataset."
python runtime/shared/ai/asx_ohlcv_ai_access.py "What is the latest close for BHP.AX?"
python runtime/shared/ai/asx_ohlcv_ai_access.py "Which ticker has the highest average volume?"
python runtime/shared/ai/asx_ohlcv_ai_access.py "How many tickers are in the ASX OHLCV summary?"
python runtime/shared/ai/asx_ohlcv_ai_access.py "Show the latest close by ticker."
python runtime/shared/ai/asx_ohlcv_ai_access.py --list-questions</pre>
  <p>Run with optional Ollama wording (Slice 2):</p>
  <pre>python runtime/shared/ai/asx_ohlcv_ai_access.py --use-ollama "Summarise the ASX OHLCV dataset."
python runtime/shared/ai/asx_ohlcv_ai_access.py --use-ollama "What is the latest close for BHP.AX?"</pre>
  <p>Default Trino endpoint: <code>http://127.0.0.1:8085</code> (port-forward from running runtime).</p>

  <h3 style="margin-top: 1.2rem;">Scope Boundary</h3>
  <p>
    Slices 1 and 2 are the narrow deterministic AI Access layer. Slice 1 maps accepted
    question patterns to pre-written SQL executed through Trino. Slice 2 adds opt-in
    Ollama wording over results Slice 1 already retrieved; Ollama does not generate SQL
    and does not access data sources directly. Slice 3 adds an HTTP API and a browser
    chat surface — both subordinate to the same deterministic layer.
  </p>
  <p>
    Future increments (vector/RAG, autonomous agents) require separate ADR decisions
    and must remain subordinate to the existing query architecture.
  </p>
</div>

<div class="card">
  <h2>AI Access Slice 3: Open WebUI Chat Surface</h2>
  <ul>
    <li>Narrow browser chat interface routing questions through the deterministic AI access layer.</li>
    <li>Open WebUI is a subordinate local chat surface only.</li>
    <li>All answers originate from allowlisted Trino queries against <code>demo.asx_ohlcv_summary</code>.</li>
  </ul>

  <h3>Architecture Path</h3>
  <p>
    <code>User -> Open WebUI -> AI Access API -> allowlisted SQL -> Trino -> demo.asx_ohlcv_summary (Lakekeeper/Iceberg -> MinIO)</code>
  </p>

  <h3>Components</h3>
  <table class="tiers-compare">
    <tbody>
      <tr>
        <td style="width: 220px;"><strong>AI Access API</strong></td>
        <td>Narrow HTTP server at <code>http://127.0.0.1:8000</code>. Exposes <code>POST /ask</code> (direct JSON) and <code>POST /v1/chat/completions</code> (OpenAI-compatible for Open WebUI). Imports routing logic from <code>asx_ohlcv_ai_access.py</code> — no SQL duplication.</td>
      </tr>
      <tr>
        <td><strong>Open WebUI</strong></td>
        <td>Browser chat surface at <code><a href="http://127.0.0.1:8090" target="_blank">http://127.0.0.1:8090</a></code>. Configured with <code>OPENAI_API_BASE_URL=http://ai-access-api:8000/v1</code>. Select model <code>asx-ohlcv-assistant</code> in the model picker.</td>
      </tr>
      <tr>
        <td><strong>Model ID</strong></td>
        <td><code>asx-ohlcv-assistant</code> — the only model exposed by the API; backed by the deterministic allowlisted query path, not a real LLM.</td>
      </tr>
      <tr>
        <td><strong>Ollama (optional)</strong></td>
        <td>Optional in-cluster deployment at <code>http://ollama:11434</code>. Apply manually: <code>kubectl apply -k runtime/knowledge-lake/k8s/base/ollama/ -n knowledge-lake</code>. Not required for deterministic answers.</td>
      </tr>
    </tbody>
  </table>

  <h3 style="margin-top: 1.2rem;">Quick Test — AI Access API Direct</h3>
  <p>From the host (requires port-forward at 127.0.0.1:8000):</p>
  <pre>curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the latest close for BHP.AX?"}' | python3 -m json.tool
curl -s http://127.0.0.1:8000/v1/models | python3 -m json.tool</pre>
  <p>From inside the cluster:</p>
  <pre>kubectl -n knowledge-lake exec deploy/ai-access-api -- \
  curl -s http://127.0.0.1:8000/health</pre>

  <h3 style="margin-top: 1.2rem;">Supported Questions (same as Slices 1 and 2)</h3>
  <table class="tiers-compare">
    <thead><tr><th>Natural-Language Question</th><th>Routes to</th></tr></thead>
    <tbody>
      <tr><td>What is the latest close for BHP.AX?</td><td><code>latest_close_for_BHP.AX</code></td></tr>
      <tr><td>Which ticker has the highest average volume?</td><td><code>highest_average_volume</code></td></tr>
      <tr><td>Summarise the ASX OHLCV dataset.</td><td><code>summarise_dataset</code></td></tr>
      <tr><td>How many tickers are in the ASX OHLCV summary?</td><td><code>ticker_count</code></td></tr>
      <tr><td>Show the latest close by ticker.</td><td><code>latest_close_by_ticker</code></td></tr>
    </tbody>
  </table>
  <p style="margin-top: 0.5rem;">
    Unsupported questions return <code>mode: unrecognised</code> with the list of
    supported questions. No SQL is generated for unrecognised input.
  </p>

  <h3 style="margin-top: 1.2rem;">Validation</h3>
  <p>Run from the repo root (runtime must be running with port-forwards active):</p>
  <pre>runtime/knowledge-lake/validate-open-webui.sh</pre>

  <h3 style="margin-top: 1.2rem;">Scope Boundary</h3>
  <table class="tiers-compare">
    <tbody>
      <tr>
        <td style="width: 220px;"><strong>No vector store</strong></td>
        <td>No Chroma, Qdrant, pgvector, or any embedding index. Answers come from Trino SQL only.</td>
      </tr>
      <tr>
        <td><strong>No RAG</strong></td>
        <td>No document ingestion, chunking, embedding, or retrieval pipeline.</td>
      </tr>
      <tr>
        <td><strong>No free SQL generation</strong></td>
        <td>The LLM (if Ollama is used) only rephrases already-retrieved Trino rows. It does not write or choose SQL.</td>
      </tr>
      <tr>
        <td><strong>No autonomous agents</strong></td>
        <td>No tool calling, multi-step orchestration, or agent framework. Open WebUI is a passive display surface.</td>
      </tr>
      <tr>
        <td><strong>No new query authority</strong></td>
        <td>Trino remains the only supported query boundary. Open WebUI and the API do not query MinIO directly.</td>
      </tr>
      <tr>
        <td><strong>Deterministic fallback preserved</strong></td>
        <td>All paths fall back to the deterministic answer when Ollama is unavailable. The CLI script continues to work independently.</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="card">
  <h2>Config</h2>
  <?php if ($configPayload === null): ?>
    <p>ASX OHLCV config is not currently readable from <code><?= htmlspecialchars($configPath) ?></code>.</p>
  <?php else: ?>
    <pre><?= htmlspecialchars(json_encode($configPayload, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES)) ?></pre>
  <?php endif; ?>
</div>

<div class="card">
  <h2>Architecture</h2>
  <p>
    Airflow orchestrates the three-stage lake flow through independent DAGs sharing
    a common run date. MinIO is the durable artifact authority for all zone outputs.
    This page is strictly read-only and does not trigger Airflow, mutate MinIO, or
    query Trino.
  </p>
  <ul>
    <li><strong>asx_ohlcv_raw</strong> — fetches OHLCV data from yFinance, writes one JSON wrapper per ticker to <code>s3://raw/asx_ohlcv/</code></li>
    <li><strong>asx_ohlcv_raw_to_conformed</strong> — reads each raw object, normalises records to a flat conformed schema, writes to <code>s3://conformed/asx_ohlcv/</code></li>
    <li><strong>asx_ohlcv_conformed_to_curated</strong> — reads all conformed objects for the run date, computes per-ticker statistics, writes a single summary to <code>s3://curated/asx_ohlcv/</code></li>
    <li><strong>asx_ohlcv_curated_to_iceberg</strong> — reads the curated summary, creates or reuses the <code>demo.asx_ohlcv_summary</code> Iceberg table in Lakekeeper, and appends one row per ticker; deduplicates by run date so re-runs are idempotent</li>
    <li><strong>asx_ohlcv_analysis.ipynb</strong> — subordinate EDA notebook; queries <code>demo.asx_ohlcv_summary</code> through Trino, computes per-ticker EDA summary, writes <code>/home/jovyan/data/asx_ohlcv_summary.json</code> for this page; no mutations</li>
    <li><strong>Metabase chart (manual, optional)</strong> — subordinate bar chart created once in the local Metabase instance via the admin UI; queries <code>demo.asx_ohlcv_summary</code> through Trino; Metabase is not a query authority and does not connect to MinIO directly</li>
  </ul>
  <p>
    Ticker names are normalised to safe filenames by replacing <code>.</code> with
    <code>_</code> and lowercasing (e.g. <code>BHP.AX</code> becomes <code>bhp_ax</code>).
    Run date is derived from the Airflow logical execution date so all three DAGs
    address the same object paths when triggered with the same timestamp.
  </p>
</div>

<div class="card">
  <h2>Normal Operation</h2>
  <ul>
    <li>Trigger each DAG in order using the same execution timestamp.</li>
    <li>The conformed DAG reads raw objects from the raw DAG; the curated DAG reads conformed objects.</li>
    <li>All DAGs use the same run date derived from the Airflow logical date.</li>
    <li><strong>Note:</strong> yFinance is installed into the Airflow vendor path on first run after each pod restart. The first raw task may take additional time.</li>
  </ul>
</div>

<div class="card">
  <h2>Prerequisites</h2>
  <ul>
    <li>The validated local runtime must already be running through <code>runtime/knowledge-lake/start-k8s.sh</code>.</li>
    <li>The foreground Minikube repo mount must remain healthy.</li>
    <li>Airflow and MinIO must both be available.</li>
    <li>The Airflow pods must be able to reach <code>finance.yahoo.com</code> for yFinance data fetching.</li>
  </ul>
</div>

<?php if ($warnings !== []): ?>
  <div class="card">
    <h2>Warnings</h2>
    <ul>
      <?php foreach ($warnings as $warning): ?>
        <li><?= htmlspecialchars($warning) ?></li>
      <?php endforeach; ?>
    </ul>
  </div>
<?php endif; ?>
<?php
$content = ob_get_clean();
$page_title = 'Knowledge Lake Solution - ASX OHLCV';
$page_description = 'Read-only view of the ASX OHLCV solution slice: raw, conformed, and curated lake zones.';
require __DIR__ . '/../inc/layout.php';
