Skip to content
Chat history




You said:
docker-compose.yaml
File
i have a docker compose yaml that sets up a minio object store, an airflow scheduler, and three dags for a heartbeat - created in raw/ , copied to conformed/ and copied to curated/

i want to set up a pipeline for tabular data now. so 

1. a dag will aquire or create csv data, and the csv will be written in raw/ as csv.

2. a second dag will find new csv files and they will be converted to parquet as part of the copy to conformed/ 

3. a third dag will identify new parquet files in conformed/ and copy the new files to curated/

my intention is that the parquet data will be queryable in a jupyter notebook.

do not write a solution. i want to explore options.
ChatGPT said:
Understood. Let’s treat this as an architecture/options discussion (not code).

Key design choices you need to make first
1) What “new file” means in MinIO
MinIO is S3-compatible, so “newness” is typically inferred, not inherent.

Common patterns:

Prefix + object listing + watermark: list raw/*.csv, compare to a stored watermark (last processed timestamp, or a processed-manifest table), process anything unseen.

Marker files: write raw/foo.csv then raw/foo.csv._SUCCESS (or vice versa). Downstream only acts on marker presence (avoids partial uploads).

Object tags/metadata: tag objects as status=raw|conformed|curated. Not always ideal because tagging can be an extra API step and becomes a control plane you must manage carefully.

If you want deterministic behaviour, the “marker file” approach is usually the simplest and most reliable in object storage pipelines.

2) How you want Airflow DAGs to trigger
There are 3 common options:

A. Pure schedule + scan (polling)

Each DAG runs every N seconds/minutes and scans a prefix for unprocessed objects.

Pros: simple, robust, Compose-friendly.

Cons: latency + repeated listing (can be noisy as volumes grow).

B. Dataset-driven DAG chaining (Airflow Datasets)

DAG 1 “publishes” a dataset event (conceptually: raw://bucket/prefix), DAG 2 is triggered by that dataset, etc.

Pros: clearer dependency semantics than time-based chaining.

Cons: dataset events aren’t object-level; you still need object discovery/watermark logic in the consumer DAGs.

C. Event-driven using MinIO bucket notifications

MinIO can emit events (webhook, NATS, Kafka, etc.). Airflow can react via a sensor or an external trigger.

Pros: low latency, fewer scans.

Cons: more moving parts in Docker Compose (a notifier target + Airflow trigger mechanism), plus you still need idempotency because events can be duplicated or missed.

For a local Compose “data lake from scratch” pattern, most people start with A, then evolve to C if/when event-latency or scale matters.

Pipeline-specific options (CSV → Parquet and promotion)
3) Where conversion runs
Two main patterns:

Option 1: Convert inside Airflow task containers

Airflow task uses PyArrow / Polars to read CSV and write Parquet back to MinIO.

Pros: simplest topology.

Cons: you must manage Python deps in the Airflow image; conversion can be memory/CPU heavy on the scheduler/worker.

Option 2: Convert via dedicated “conversion” container/service

Airflow triggers a separate container/job (e.g., a small conversion image).

Pros: isolates heavy deps and resources.

Cons: slightly more orchestration complexity.

In Compose, Option 1 is fine for “small-to-moderate” files; Option 2 is better once files become large or you want clean separation of concerns.

4) How you define the Parquet “shape”
Your downstream queryability in Jupyter depends heavily on this:

Single-file Parquet per CSV (1:1 conversion)

Pros: trivial; easy lineage.

Cons: many small files can become inefficient; harder to query across time/partitions.

Partitioned layout (recommended once you care about analytics patterns)

Example concept: conformed/mytable/date=YYYY-MM-DD/part-....parquet

Pros: enables predicate pushdown and selective reads in DuckDB/Polars/Spark/Trino.

Cons: you must decide partition keys and naming conventions early.

Schema management

CSVs often drift. Decide now whether you:

enforce a schema (reject/park incompatible files),

allow evolution (union columns, type promotion rules),

or version schemas (e.g., v1/, v2/ prefixes).

5) Promotion semantics: “copy” vs “logical publish”
For conformed → curated:

Physical copy (what you’re doing now): replicate objects to a new prefix/bucket.

Pros: very clear; curated is immutable.

Cons: doubles storage; increases IO.

Logical publish: curated is a “view” (prefix, manifest, or catalog) over conformed.

Pros: less duplication.

Cons: you need a catalog/manifest concept; slightly more sophistication.

Given you’re building from scratch and want clarity, physical copy is fine initially.

Jupyter query options (without adding a full query engine)
Since you explicitly want Parquet queryable in a notebook, you have several “graduation levels”:

Level 1: Direct file access in Python (fastest to adopt)
DuckDB: can query Parquet directly (including over S3-compatible endpoints) and feels like SQL.

Polars / PyArrow: great for dataframe workflows; can scan Parquet lazily and push down predicates.

Best when: you want lightweight analytics without standing up Trino/Spark.

Level 2: Add a query engine later (Trino/Spark) + optional table format
If you later want SQL endpoints, concurrency, or BI tools:

Add Trino and point it at the Parquet data (works best if partitioned well).

Consider Iceberg/Delta/Hudi if you need ACID tables, schema evolution, and incremental writes.

Best when: you’re moving from “files in a bucket” to “tables”.

Operational concerns you should decide now
6) Idempotency and “exactly-once-ish” behaviour
Airflow will retry tasks; MinIO lists can be eventually consistent in some setups; events can duplicate.

Strong options:

Maintain a processed manifest (e.g., object keys + etags + processed timestamp) somewhere durable.

Make conversions idempotent (same input key always produces same output key).

Use atomic publish patterns (write temp then move/rename if your API supports it; or write marker last).

7) File size strategy
If you expect large CSVs, consider chunking/streaming conversion (or enforce max sizes).

If you expect many small CSVs, consider batching into fewer Parquet files or partitioning strategy to avoid small-file problems.

A pragmatic way to compare options
To choose cleanly, evaluate each design (polling vs event; convert in Airflow vs separate worker; copy vs logical publish; schema strictness) against:

expected file volume and size,

how quickly you need “new data visible in Jupyter,”

tolerance for extra services in Compose,

how much you care about lineage/audit.

If you want, paste the relevant parts of your current DAG patterns (just the “list objects / copy objects” approach you used for heartbeat) and I’ll map the tabular pipeline options onto the same style—still without writing the final solution.

You said:
docker-compose.yaml
File
conformed_to_curated_copy.py
Python
raw_heartbeat_1m.py
Python
raw_to_conformed_copy.py
Python
okay. lets narrow the architecture space. 

please review the docker-compose.yaml, and the attached .py files for the three DAGs.

i want to follow this architecture.

the extensions to this pattern i want are 

1. create csv files in raw/
2. convert to parquet during copy to conformed/
3. how to handle possible duplicate rows during incremental writes into conformed/ or curated/
4. what to use as the schema and content for each new csv file created in raw/
ChatGPT said:

Thought for 30s
I reviewed your Compose and the three existing DAGs. The current pattern is:

MinIO with three buckets (raw, conformed, curated) created by minio-init. 
conformed_to_curated_copy


Airflow (SequentialExecutor, SQLite) mounting ./dags and running a 1-minute heartbeat writer into raw/heartbeat/....

Two “copy if key not present” DAGs: raw -> conformed and conformed -> curated, implemented by listing keys in each bucket and copying missing keys.

That architecture is compatible with your tabular pipeline; the main question is how far you want to go beyond “object copy semantics” into “table semantics”.

Below are the options/decisions for each of your four extensions, aligned to your current pattern (scheduled scan + list + act).

1) Create CSV files in raw/
Within your current pattern, there are two clean approaches:

Option A — “Synthetic generator” DAG (like heartbeat, but CSV)
Model it on the heartbeat writer (same boto3 client pattern, same write-to-MinIO approach). The only architectural question is keying/naming:

Put tabular drops under a dedicated prefix (e.g., raw/tabular/<dataset>/ingest_date=YYYY-MM-DD/<file>.csv) to avoid mixing with heartbeat objects (your copy DAG currently lists the entire bucket).

Ensure “file completeness”: write the CSV, then optionally write a marker ._SUCCESS object (or a manifest object). This prevents downstream picking up half-written files (object stores are atomic per object, but your producer could still upload multiple related objects).

Option B — “Acquisition” DAG (pull from somewhere, then land as CSV)
Same mechanics; difference is: you will want minimal, deterministic metadata in the filename (source, extract time, batch id) so that downstream processing can be idempotent.

2) Convert to Parquet during copy to conformed/
Your existing raw_to_conformed_copy DAG is a straight copy_object when a key is missing in conformed. 
raw_to_conformed_copy


For CSV→Parquet you have two architectural choices:

Option A — Transform-in-flight (replace “copy” with “read CSV → write Parquet”)
This stays closest to your current model: one DAG run scans raw/, finds new CSV keys, and for each:

reads the CSV object from MinIO,

converts to Parquet,

writes a Parquet object to conformed/ (with a new key).

Key design choices:

Output key mapping: decide a deterministic mapping from input CSV key → output Parquet key (e.g., same base name but .parquet, and possibly under conformed/tabular/...).

Schema enforcement: Parquet requires typing; CSV is text. Decide whether to:

infer schema each time (risk drift),

enforce a pre-declared schema per dataset,

or infer + validate + quarantine on mismatch.

Option B — Two-step inside the DAG (copy raw object, then convert separately)
This reduces blast radius if conversion fails, but it tends to create clutter (you end up with CSVs in conformed or temp artifacts). Given your goal (“convert as part of copy”), Option A is usually cleaner.

Operational note: Your Airflow container currently does not pin any parquet dependencies (PyArrow/Polars). If you choose transform-in-flight, you will need to add those to the Airflow runtime image or use a dedicated conversion container. That is an implementation detail, but it is a real architectural constraint.

3) Handling duplicate rows during incremental writes (conformed/curated)
This is the point where “file pipeline” meets “table semantics”.

First, decide where deduplication belongs
Conformed is commonly treated as:

“standardised + typed + partitioned” and often append-only (you keep all records as landed, possibly with metadata columns),
while Curated is:

“analytics-ready” and may enforce uniqueness or “latest record per key”.

That split lets you keep conformed simple and do business-rule dedupe in curated.

Deduplication strategies that fit your current architecture
Strategy 1 — “Immutable batch files” (no in-place updates; dedupe at query time or in curated)
Each run writes a new Parquet file (or partition) with a batch id / load timestamp.

Curated DAG can produce a deduped snapshot (or compacted partition) by:

grouping by a business key and keeping max(load_ts), or

using a row hash to drop exact duplicates.

Pros: fits object stores and your scheduled scan/copy model.
Cons: curated becomes a compute step, not a simple copy.

Strategy 2 — “Natural key + merge/upsert”
If you truly need incremental upserts (update existing rows), files alone are awkward. You usually introduce a table format:

Iceberg / Delta / Hudi provide transactional semantics and merges.

Pros: proper upserts, schema evolution, compaction patterns.
Cons: more moving parts; beyond your current “3 DAGs + MinIO” simplicity.

Strategy 3 — “Manifest of processed row-ids”
Maintain a small state store of seen business keys or row hashes (even a simple manifest object) and drop duplicates during conversion.

Pros: keeps curated as copy.
Cons: state management can get messy; manifests can grow; concurrency concerns.

Minimal “good enough” pattern (recommended for your current stage)
Add these columns during CSV→Parquet conversion:

ingest_ts (timestamp),

source_file (key),

row_hash (hash of the logical row, or of the business-key fields),

optional business_key (concatenated string or structured columns).

Treat conformed as append-only.

Let curated perform dedupe by business key (or row_hash) and “latest-wins” based on ingest_ts.

This keeps the pipeline conceptually consistent with your current “scan for new objects and produce derived objects” DAG pattern.

4) What schema/content should each new CSV in raw use?
You need to decide whether your raw CSVs represent:

Option A — A single evolving dataset (recommended for the first iteration)
Pick one dataset name (e.g., students, customers, sales_events) and standardise:

Stable columns (core fields)

Optional columns (nullable; can be added later)

A primary/business key (even if synthetic)

A practical “starter schema” that supports incremental loads and dedupe:

record_id (string; business key or UUID)

event_ts (timestamp or date string)

…domain columns…

ingest_batch_id (string; derived from run)

ingest_ts (timestamp)

This gives you clear incremental semantics and a dedupe handle.

Option B — Multiple datasets (harder early)
If you intend multiple independent CSV types, you should separate prefixes early:

raw/tabular/<dataset>/...

and keep schema contracts per dataset.

Important alignment issue with your existing copy DAGs
Right now your copy DAG lists all objects in raw and copies any missing keys to conformed. 
raw_to_conformed_copy


If you introduce CSV drops into raw/ without prefixes and filtering, you will also propagate heartbeat objects and any other miscellaneous raw artifacts. You can keep the architecture while narrowing scope by adopting:

strict prefixes (heartbeat/ vs tabular/)

and making each DAG operate on only its prefix.

Two quick observations from your current codebase (relevant to the extension)
Your heartbeat DAG uses env-driven credentials and endpoint defaults, while the copy DAGs hardcode the endpoint and omit explicit credentials. For consistency and fewer surprises, you will want the same boto3 client construction pattern across all DAGs.

list_objects_v2 without pagination will stop at 1000 keys. That may not matter now, but it is a known scaling ceiling of the “scan and compare keys” approach.

If you want the next step in the exploration: tell me whether you want conformed to remain append-only (and dedupe in curated), or whether you want true upserts (which usually implies a table format like Iceberg/Delta). That single choice will determine how sophisticated #3 needs to become.


Sources
You said:
okay. 

1. conformed/ bucket can be append-only. 
2. the data schema shall be for financial market data, i.e. the domain columns company_identifier, open, high, low, close, volume. plus other columns as you advise.
3. there will be more data sets, not identified as yet.
ChatGPT said:
Good. With append-only conformed, you can keep your existing “scan + act” DAG pattern and defer table-format complexity.

1) Conformed as append-only: what this implies
Every raw CSV drop becomes one or more Parquet objects in conformed/.

You do not overwrite or merge in place in conformed/.

Any deduplication, “latest value wins”, or snapshot logic happens either:

in curated (as a derived dataset), or

at query time in Jupyter (DuckDB/Polars).

This is the cleanest fit for your current MinIO + Airflow + scheduled scans architecture.

2) Recommended schema for financial market OHLCV
You proposed the core domain columns:

company_identifier

open, high, low, close

volume

To make the pipeline robust (incremental loads, duplicates, multiple datasets, auditability), add these columns now. They are “boring” but they prevent most pain later.

A. Trading-time keys (critical)
You need a proper time key; without it, dedupe and incremental logic are guesswork.

market_datetime (timestamp, preferably UTC) or trade_date (date) + bar_interval (e.g., 1d, 1h, 1m)

exchange (string) if you have multi-venue data

currency (string) optional but useful for cross-market data

Minimum viable for daily bars:

trade_date (YYYY-MM-DD)

company_identifier

B. Ingestion/audit columns (strongly recommended)
These make append-only manageable and debuggable.

dataset_id (string): identifies which dataset this record belongs to (e.g., market_ohlcv_daily, market_ohlcv_intraday_v1)

source_system (string): where it came from (even if “synthetic” at first)

ingest_ts (timestamp): when your pipeline wrote it

ingest_batch_id (string): run id / logical batch key

source_object_key (string): MinIO key of the raw CSV that produced it

row_number_in_source (int): optional; useful when tracing parsing issues

C. Dedup support columns (for curated and for notebook queries)
Because conformed is append-only, duplicates will occur (same company/date repeated across sources or re-ingests). You want a deterministic way to dedupe later.

business_key (string) OR use explicit key columns (recommended) and derive later

row_hash (string): hash of the “logical row” (e.g., company + time + OHLCV)

For OHLCV, the natural business key is typically:

(dataset_id, company_identifier, market_datetime)
or for daily:

(dataset_id, company_identifier, trade_date)

D. Optional finance-friendly columns
These are useful but not mandatory at day one:

adjusted_close (float) if you ever use adjusted series

vwap (float)

trade_count (int)

data_quality_flag (string) (e.g., missing values, out-of-range)

Recommended “raw CSV contract” (baseline)
If you want a single “standard CSV shape” for this OHLCV dataset family, I would define:

Required:

dataset_id

company_identifier

market_datetime (or trade_date)

open, high, low, close

volume

Pipeline-added (not required in raw, but must exist in conformed Parquet):

ingest_ts, ingest_batch_id, source_object_key, row_hash

This gives you enough to:

append safely,

trace lineage,

dedupe later deterministically.

3) Multiple datasets: how to keep the architecture scalable
Since you will have more datasets, the key decision is how you separate them in object storage and in DAG logic.

A. Prefix layout (recommended)
Adopt a convention now:

Raw:

raw/tabular/<dataset_id>/ingest_date=YYYY-MM-DD/<file>.csv

Conformed:

conformed/tabular/<dataset_id>/.../*.parquet

Curated:

curated/tabular/<dataset_id>/.../*.parquet

This lets each DAG:

scan only raw/tabular/ (and ignore heartbeat),

optionally filter to specific dataset_id prefixes,

avoid accidental cross-dataset processing.

B. Registry concept (lightweight, still Compose-friendly)
To avoid hardcoding every future dataset into DAG code, introduce a very small “dataset registry” notion (even if it’s just a YAML/JSON file or a simple Python dict initially) with fields like:

dataset_id

expected columns / schema version

partitioning rule (daily vs intraday)

dedupe key definition

You do not need a full catalog system to get 80% of the benefit.

4) How dedupe works with append-only conformed (practical rule-set)
Given your choice, the clean operational rule is:

Conformed: store everything, never overwrite.

Curated: produce a “latest” or “unique” view by applying:

ROW_NUMBER() over (partition by business_key order by ingest_ts desc) = 1

or drop exact duplicates via row_hash

This can be implemented later either in:

a curated DAG that writes deduped Parquet, or

your Jupyter queries (DuckDB makes this very straightforward).

If you want the next narrowing step without jumping into implementation: decide whether your first dataset is daily or intraday, because that determines the primary key (trade_date vs market_datetime + interval) and the partitioning strategy in conformed/.

You said:
this first data set will be daily
ChatGPT said:
Understood: daily OHLCV as the first dataset. That lets you standardise a clean business key and partitioning approach immediately.

Recommended daily dataset contract
Business key
Use this as the logical uniqueness constraint (for dedupe in curated / notebook queries):

(dataset_id, company_identifier, trade_date)

Raw CSV columns (what your “create CSV in raw/” DAG should emit)
Required domain columns:

dataset_id (e.g., market_ohlcv_daily)

company_identifier

trade_date (YYYY-MM-DD)

open, high, low, close

volume

Strongly recommended additional columns (still safe for “daily”):

currency (optional if you know it’s always the same)

exchange (optional unless you’ll have multi-venue)

Do not require ingestion metadata in the raw CSV unless you want human readability; it can be injected during the raw→conformed conversion step.

Conformed Parquet columns (what must exist after conversion)
All raw columns plus pipeline metadata for auditability and deterministic dedupe:

ingest_ts (timestamp)

ingest_batch_id (string)

source_object_key (string)

row_hash (string; hash of at least dataset_id|company_identifier|trade_date|open|high|low|close|volume)

This keeps conformed append-only and still supports dedupe/snapshot later.

Partitioning and object layout (daily)
To keep things scalable without adding a table format yet, I recommend partitioning by date:

Raw:

raw/tabular/market_ohlcv_daily/trade_date=YYYY-MM-DD/<source>_<batch>.csv

Conformed:

conformed/tabular/market_ohlcv_daily/trade_date=YYYY-MM-DD/<source>_<batch>.parquet

Curated:

curated/tabular/market_ohlcv_daily/trade_date=YYYY-MM-DD/<snapshot_or_compacted>.parquet

This gives you:

fast “new data” discovery by prefix,

efficient notebook reads for a date range,

straightforward future evolution to Trino/Iceberg if you choose.

Duplicate handling policy (daily)
With the business key above, duplicates are simple:

Exact duplicates (same OHLCV values): remove by row_hash in curated (or query-time).

Conflicting duplicates (same key, different OHLCV): decide a rule now. The simplest is:

“latest ingest wins” using ingest_ts (or ingest_batch_id ordering).

This is deterministic and aligns with append-only conformed.

Jupyter queryability (daily)
With Parquet partitioned by trade_date=..., the notebook experience is good even without a query engine:

DuckDB or Polars can scan only relevant partitions and apply predicate pushdown.

If you want to lock the daily contract tightly: do you intend company_identifier to be a ticker (e.g., AAPL), an ISIN, or an internal id? The answer affects whether you also need exchange as a required column from day one.

You said:
ticker
ChatGPT said:
Noted: company_identifier will be a ticker. For daily data, that creates one immediate design implication: tickers are not globally unique, so you should decide whether you will treat the dataset as “single exchange only” (and omit exchange) or “multi-exchange capable” (and include exchange).

Given you said “more datasets not identified yet”, I recommend you include exchange now as a required column for this dataset family. It costs little and prevents painful rework later.

Final recommended daily OHLCV schema (ticker-based)
Raw CSV (required columns)
dataset_id (e.g., market_ohlcv_daily)

exchange (e.g., NASDAQ, ASX, NYSE)

ticker (your company_identifier)

trade_date (YYYY-MM-DD)

open (decimal/float)

high (decimal/float)

low (decimal/float)

close (decimal/float)

volume (integer)

Optional (only if you need it soon):

currency

Conformed Parquet (add pipeline metadata)
All raw columns plus:

ingest_ts

ingest_batch_id

source_object_key

row_hash

Business key (for dedupe and curated snapshots)
(dataset_id, exchange, ticker, trade_date)

Recommended object layout
Raw:

raw/tabular/market_ohlcv_daily/trade_date=YYYY-MM-DD/<exchange>_<batch>.csv

Conformed:

conformed/tabular/market_ohlcv_daily/trade_date=YYYY-MM-DD/<exchange>_<batch>.parquet

Curated:

curated/tabular/market_ohlcv_daily/trade_date=YYYY-MM-DD/<exchange>_<snapshot>.parquet

Duplicate handling rule-set (simple and deterministic)
Exact duplicates: drop by row_hash.

Conflicts on same business key: “latest ingest wins” using ingest_ts (or ingest_batch_id).

This stays fully compatible with your existing Airflow pattern (scheduled scans, append-only conformed, derived curated).

If you want to keep the dataset “single-exchange only” for now (e.g., ASX only), you can still include exchange with a constant value; it preserves forward compatibility with almost no cost.

You said:
include the 'exchange' attribute/column
ChatGPT said:
Acknowledged. With exchange included, the daily OHLCV dataset contract is now well-defined and future-proof.

Below is the finalised architectural position, aligned with your existing MinIO + Airflow + scheduled DAG pattern, without introducing table formats or eventing.

Final daily OHLCV dataset definition (ticker-based, multi-exchange)
Raw CSV schema (authoritative contract)
These are the columns your raw CSV–creating DAG must emit.

Required

dataset_id
Example: market_ohlcv_daily

exchange
Example: ASX, NASDAQ, NYSE

ticker
Example: BHP, AAPL

trade_date
Format: YYYY-MM-DD

open

high

low

close

volume

Optional (safe to omit initially)

currency

This schema is intentionally business-focused only. No pipeline metadata belongs in raw.

Conformed Parquet schema (append-only)
During raw → conformed, the Parquet writer must add pipeline metadata.

Inherited from raw

dataset_id

exchange

ticker

trade_date

open, high, low, close, volume

optional currency

Injected by pipeline

ingest_ts

ingest_batch_id

source_object_key

row_hash

This gives you:

deterministic lineage

replay safety

dedupe capability

no mutation of existing data

Business key (canonical)
This is the uniqueness definition used for deduplication and curated views:

(dataset_id, exchange, ticker, trade_date)
Everything else (OHLCV values, volume) is measure data.

Object layout (locked in)
This layout scales cleanly and matches how your copy DAGs already work.

Raw

raw/tabular/market_ohlcv_daily/
  trade_date=YYYY-MM-DD/
    <exchange>_<batch>.csv
Conformed

conformed/tabular/market_ohlcv_daily/
  trade_date=YYYY-MM-DD/
    <exchange>_<batch>.parquet
Curated

curated/tabular/market_ohlcv_daily/
  trade_date=YYYY-MM-DD/
    <exchange>_<snapshot>.parquet
This enables:

prefix-scoped DAG scans

partition pruning in notebooks

painless later migration to Trino / Iceberg if desired

Duplicate handling (final rule set)
Given append-only conformed:

Exact duplicates
→ identified via row_hash, removable in curated or query-time

Conflicting rows with same business key
→ “latest ingest wins”, ordered by ingest_ts (or ingest_batch_id)

No stateful merge is required in conformed.

Why this choice is correct for your architecture
Matches your current scan + compare + act DAG model

Avoids premature table formats

Keeps MinIO as dumb object storage

Keeps Airflow logic simple and deterministic

Supports multiple future datasets without DAG rewrites

Fully queryable from Jupyter via DuckDB / Polars immediately

The only remaining architectural decisions (when you’re ready)
CSV producer semantics
– one file per exchange per day, or many?

Curated strategy
– snapshot per day vs rolling “latest” dataset

Schema governance
– how strictly future datasets must declare schemas

When you want, we can lock each of those down in the same disciplined way—still without writing code unless you explicitly ask for it.

You said:
Answers:

Q1: I intend to get daily data from Yahoo Finance. I think this implies multiple calls to the RESTful web service - one for each 'ticker'

Q2: daily snapshot

Q3: tabular data sets should have well defined schemas at architecture time. does that count as 'strict' ?
ChatGPT said:

Thought for 7s
Great — those three answers let us lock the remaining architectural decisions without changing your overall pattern (scheduled scans, append-only conformed, daily curated snapshots).

Q1 — Yahoo Finance daily data, one call per ticker
Yes: at the “conceptual API” level, you should assume one request per ticker per run (unless you introduce batching via a paid provider). That drives three practical architecture considerations:

Rate limiting / blocking risk (realistic)
Yahoo does not provide a stable, officially supported market-data API for this use case, and common approaches (including popular libraries) rely on web endpoints that can be throttled or blocked when you request too frequently. 
Medium
+2
algotrading101.com
+2

Implication: design the raw-ingestion DAG as “polite”: throttling, caching, and retries that do not amplify request bursts.

Redistribution/licensing constraints
Yahoo’s own help content indicates restrictions on redistribution of data displayed/provided via Yahoo Finance. 
help.yahoo.com
+1

Implication: if your OSS Data Lake content is public-facing, treat this as “for personal/internal use” unless you have a licensed data source.

Idempotent object naming
Because you may re-run, partially fail, or be throttled, design your raw object keys so a re-run does not create ambiguity. You can keep your current scan pattern, but ensure keys encode:

dataset_id, exchange, ticker, trade_date, and a batch_id (run id).

That prevents accidental overwrites and makes downstream conversion deterministic.

Q2 — Daily snapshot in curated
This is a good fit with append-only conformed.

Recommended meaning of “daily snapshot” (precise):

For each trade_date, curated contains one authoritative record per (dataset_id, exchange, ticker, trade_date).

How to derive it (conceptually):

Choose the “winning” record for each business key using ingest_ts (latest wins), and optionally prefer a particular source_system if you later add multiple providers.

Operational implication:

Curated becomes a derive/compact step, not a simple object copy. It can still be implemented in the same scheduled-scan pattern, but it will produce new curated snapshot objects for each date.

Q3 — “Well defined schemas at architecture time” and whether that is “strict”
Yes — in data engineering terms, that is strict schema (or “schema-on-write”) in the sense that:

You define the dataset contract up front.

The pipeline either:

accepts a raw CSV only if it conforms (columns, types, required fields), or

quarantines it (lands it but does not convert/promote it), with an error artefact.

Important nuance:

“Strict” does not mean “never changing.” It means controlled evolution:

schema versions (e.g., market_ohlcv_daily_v1, ..._v2), or

additive-only evolution with explicit versioning rules.

Given you expect “more datasets”, I recommend this governance rule:

Every dataset must have a dataset_id and a declared schema (columns + types + business key) before ingestion is enabled.

Finalised daily OHLCV contract (with exchange)
Given your prior decisions, the dataset contract becomes:

Raw required columns

dataset_id

exchange

ticker

trade_date (YYYY-MM-DD)

open, high, low, close (numeric)

volume (integer)

Conformed adds

ingest_ts, ingest_batch_id, source_object_key, row_hash

Business key

(dataset_id, exchange, ticker, trade_date)

If you want to narrow one last thing before implementation: for Yahoo Finance, are you planning one exchange only initially (e.g., ASX) or multiple exchanges from day one? This affects how you model ticker formatting and whether you need a yahoo_symbol field separate from your canonical (exchange, ticker) pair.

You said:
initial companies / tickers will be selected from the ASX 
ChatGPT said:

Thought for 4 seconds
Understood: initial universe = ASX.

That gives you a clean, low-entropy “Phase 1” design, but there are two important nuances you should bake into the schema and naming so you do not paint yourself into a corner later.

1) Yahoo Finance identifier strategy for ASX
For Yahoo Finance, ASX-listed equities are typically referenced using the .AX suffix (e.g., BHP.AX, ASX.AX). 
help.yahoo.com
+3
Yahoo Finance
+3
Yahoo Finance
+3

Recommendation
Keep your canonical business columns as:

exchange = "ASX"

ticker = "BHP" (no suffix)

Add one extra column for acquisition convenience:

vendor_symbol = "BHP.AX" (or call it yahoo_symbol)

This avoids mixing vendor conventions into your business keys and makes later multi-vendor ingestion straightforward.

2) Final daily OHLCV schema for Phase 1 (ASX)
Raw CSV contract (daily)
Required:

dataset_id (e.g., market_ohlcv_daily)

exchange (constant "ASX" for now)

ticker (e.g., BHP)

vendor_symbol (e.g., BHP.AX)

trade_date (YYYY-MM-DD)

open, high, low, close

volume

Optional (but useful even in Phase 1):

currency (likely AUD for ASX; keep optional unless you will ingest dual-currency instruments)

Conformed Parquet (append-only + metadata)
All raw columns plus:

ingest_ts

ingest_batch_id

source_object_key

row_hash

Canonical business key
(dataset_id, exchange, ticker, trade_date)

This remains stable even if later you change providers or symbol formatting.

3) Daily snapshot meaning in curated (ASX)
Since you want daily snapshot, define it precisely as:

For each trade_date, curated contains exactly one row per (dataset_id, exchange, ticker, trade_date).

Conflict resolution rule (when duplicates occur in conformed):

“latest ingest wins” ordered by ingest_ts (or ingest_batch_id).

4) Practical warning about Yahoo Finance usage
Yahoo does not offer a formally documented public Finance API in the way many developers expect; common approaches rely on reverse-engineered endpoints, and there are Terms/redistribution constraints you should treat carefully for anything beyond personal/internal learning. 
Stack Overflow
+2
guce.yahoo.com
+2

This does not block your architecture, but it reinforces why you want:

strong ingestion metadata,

idempotent keys,

and the ability to swap data sources later without changing your canonical schema.

5) Object naming/layout for Phase 1 (ASX daily)
To keep your scan-based DAGs clean and dataset-extensible:

Raw:

raw/tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/<batch>.csv

Conformed:

conformed/tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/<batch>.parquet

Curated:

curated/tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/<snapshot>.parquet

This layout will also let Jupyter queries prune partitions by trade_date and exchange immediately.

If you want to lock the acquisition semantics before we touch implementation: for Phase 1, will each daily run fetch (a) “yesterday only” for all tickers, or (b) “a rolling window” (e.g., last 7 days) to tolerate missed runs and late corrections?

You said:
option (b) is preferred.
ChatGPT said:

Thought for 5s
Option (b) — rolling window — is the correct choice for reliability with a scan-based pipeline, especially when the upstream source can be flaky or you may miss runs.

Here is how to formalise it within the architecture you have now (append-only conformed, daily curated snapshot), and what decisions it forces.

Rolling-window ingestion semantics (daily, ASX)
Recommended contract
Each run fetches N most recent trading days for each (exchange=ASX, ticker) and lands them to raw/ as CSV. Typical N values are 7–30 depending on how tolerant you want to be of missed runs and restatements.

Why this works:

If a run fails today, tomorrow’s run still captures the missing day(s).

If the provider “revises” recent bars, you capture the revision without requiring in-place updates (because conformed is append-only).

Raw file strategy under rolling-window
You have two viable patterns; both work with your “list objects and process unseen keys” approach.

Pattern A — One raw CSV per ticker per run (simplest ingestion)
Pros: straightforward API loop (one call per ticker), easy debugging.

Cons: more files.

Suggested key shape:

raw/tabular/market_ohlcv_daily/exchange=ASX/ticker=BHP/run_ts=.../window.csv

Pattern B — One raw CSV per ticker per day (simplest downstream processing)
Pros: downstream conversion and curated snapshot become very clean: “process this trade_date partition”.

Cons: ingestion has to split the downloaded window into day-sliced objects.

Suggested key shape:

raw/tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/ticker=BHP.csv

If your end-state is “daily snapshot curated”, Pattern B reduces complexity later (fewer “grouping” steps).

Conformed behaviour under rolling-window (append-only)
No change to your “append-only” decision — but rolling-window means you will intentionally re-land overlapping days, so duplicates are guaranteed.

To handle this correctly, conformed should store:

the canonical OHLCV columns,

plus ingestion metadata,

plus a deterministic row_hash.

That gives you lossless history and deterministic dedupe.

Curated snapshot behaviour under rolling-window
Because curated is “daily snapshot”, you should define the output as:

For each trade_date, curated contains exactly one winning row per:

(dataset_id, exchange, ticker, trade_date)

Winning rule:

“latest ingest wins” using ingest_ts (or ingest_batch_id).

This is where your duplicates are resolved.

Schema decision points (now locked in by your answers)
You have already made a strict-schema call (“defined at architecture time”), which is absolutely compatible with rolling windows.

For the first dataset, with ASX tickers via Yahoo Finance identifiers:

Yahoo commonly uses .AX symbols (e.g., BHP.AX). 
Yahoo Finance
+2
Yahoo Finance
+2

So your raw schema should include both:

exchange (required; "ASX" for Phase 1)

ticker (required; BHP)

vendor_symbol (required; BHP.AX) — keeps vendor conventions out of your business key

And your canonical business key becomes:

(dataset_id, exchange, ticker, trade_date)

One compliance / robustness note (relevant to architecture)
Yahoo does not provide a formal public market-data API for high-volume programmatic use, and their help content explicitly warns against redistribution of Yahoo Finance data. 
help.yahoo.com
+2
ranaroussi.github.io
+2

Architecture implication: build this so you can later swap the source (paid API, ASX vendor feed, etc.) without changing your downstream schema.

Recommended next narrowing decision (no code yet)
Pick the raw file pattern:

A) one CSV per ticker per run (simpler ingestion)

B) one CSV per ticker per day (simpler conformed/curated and partitioning)

Given you want daily snapshots and multiple datasets later, I recommend B unless you have a strong reason to keep ingestion minimal.

You said:
okay. go with (b)
ChatGPT said:
Agreed. With (b) one CSV per ticker per day, your pipeline becomes cleanly date-partitioned end-to-end and aligns with “daily snapshot” curated.

1) Raw ingestion semantics (rolling window, but day-sliced objects)
Each ingestion run fetches the last N trading days per ticker, then splits the response into one CSV object per trade_date per ticker.

This gives you:

deterministic object keys (idempotent ingestion),

easy incremental discovery (partition/prefix driven),

minimal downstream grouping logic.

2) Canonical schema for this dataset (ASX daily OHLCV)
Raw CSV columns (required)
dataset_id (e.g., market_ohlcv_daily)

exchange (constant "ASX" for Phase 1)

ticker (e.g., BHP)

vendor_symbol (e.g., BHP.AX)

trade_date (YYYY-MM-DD)

open, high, low, close

volume

Optional (only if you need it early):

currency

Conformed Parquet columns (raw + pipeline metadata)
All raw columns plus:

ingest_ts

ingest_batch_id

source_object_key

row_hash

3) Business key and dedupe policy
Canonical business key
(dataset_id, exchange, ticker, trade_date)

What happens with duplicates (expected under rolling windows)
Conformed: append-only, keep everything.

Curated (daily snapshot): exactly one row per business key using:

“latest ingest wins” (ingest_ts / ingest_batch_id)

optionally drop exact duplicates using row_hash first.

This gives you a stable snapshot even if you re-fetch overlapping days.

4) Object layout (prefixes and partitions)
Raw (one CSV per ticker per day)
raw/tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/ticker=<TICKER>.csv

Conformed (Parquet, same partitioning)
conformed/tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/ticker=<TICKER>.parquet

Curated (daily snapshot partition)
curated/tabular/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/snapshot.parquet

(or multiple files per day if you later need sharding)

5) Strict schema interpretation (your Q3)
Yes—“well defined schemas at architecture time” is strict schema-on-write:

raw objects must match the declared column set (and expected types once converted),

anything that doesn’t conform is quarantined (kept in raw, not promoted).

6) Jupyter queryability
With Parquet partitioned by trade_date (and exchange), notebooks can efficiently query date ranges using DuckDB/Polars with predicate pushdown—no additional query engine required initially.

If you want the next (still non-code) decision: choose the rolling window size N (e.g., 7 vs 30) and decide whether you want a “quarantine prefix” for schema violations (recommended).

You said:
i think we are ready for code, aren't we? 

1. rolling window = 30

2. let's leave the schema violation logic for now.

3. please include a currency column
ChatGPT said:

Thought for 1m 43s
Yes — with your decisions locked in, you are ready for code.

Below are three DAG files that follow your existing pattern (scheduled scan + MinIO buckets), with these choices baked in:

Rolling window: 30 trading days (implemented as “fetch ~45 calendar days, then take last 30 rows” to cover weekends/holidays)

Daily objects: one CSV per ticker per trade_date in raw/

Conformed: append-only Parquet objects (one Parquet per ticker per trade_date), with ingestion metadata + row_hash

Curated: daily snapshot per trade_date (one Parquet snapshot.parquet per date), “latest ingest wins”

Currency: included; for ASX Phase 1 set to constant AUD

Dependencies (Airflow image)
These DAGs assume the Airflow container has:

yfinance (for Yahoo Finance access) 
GitHub
+1

pandas

pyarrow (for Parquet) 
Apache Arrow
+1

1) raw_market_ohlcv_daily_asx.py
Creates raw CSV objects in MinIO (one per ticker per day) using a rolling window.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
import os

import boto3
import pandas as pd
import pendulum
import yfinance as yf

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable


DATASET_ID = "market_ohlcv_daily"
EXCHANGE = "ASX"
CURRENCY = "AUD"

RAW_BUCKET = "raw"
MINIO_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def _asx_tickers() -> list[str]:
    # Set Airflow Variable ASX_TICKERS = "BHP,CBA,RIO,CSL" etc.
    raw = Variable.get("ASX_TICKERS", default_var="BHP,CBA")
    return [t.strip().upper() for t in raw.split(",") if t.strip()]


def _vendor_symbol(ticker: str) -> str:
    # Yahoo Finance convention for ASX listings: <TICKER>.AX
    return f"{ticker}.AX"


def _raw_key(trade_date: str, ticker: str) -> str:
    return (
        f"tabular/{DATASET_ID}/exchange={EXCHANGE}/trade_date={trade_date}/"
        f"ticker={ticker}.csv"
    )


def fetch_and_write_raw_csvs(rolling_trading_days: int = 30) -> None:
    """
    For each ASX ticker:
      - download daily OHLCV for ~45 calendar days
      - take last N rows (N=rolling_trading_days)
      - write one CSV object per (ticker, trade_date) into raw/
    """
    s3 = _s3_client()

    # Fetch enough calendar days to usually cover 30 trading days
    end = datetime.now(timezone.utc).date()
    start = (end - timedelta(days=45))

    for ticker in _asx_tickers():
        symbol = _vendor_symbol(ticker)

        df = yf.download(
            tickers=symbol,
            start=str(start),
            end=str(end + timedelta(days=1)),
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            continue

        # Standardise columns
        df = df.reset_index()
        # yfinance uses "Date" column for daily
        df.rename(
            columns={
                "Date": "trade_date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            },
            inplace=True,
        )

        # Ensure date string format
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date.astype(str)

        # Take last N trading days
        df = df.tail(rolling_trading_days)

        # Emit one CSV per day
        for _, row in df.iterrows():
            trade_date = row["trade_date"]

            out = pd.DataFrame(
                [
                    {
                        "dataset_id": DATASET_ID,
                        "exchange": EXCHANGE,
                        "ticker": ticker,
                        "vendor_symbol": symbol,
                        "currency": CURRENCY,
                        "trade_date": trade_date,
                        "open": float(row["open"]) if pd.notna(row["open"]) else None,
                        "high": float(row["high"]) if pd.notna(row["high"]) else None,
                        "low": float(row["low"]) if pd.notna(row["low"]) else None,
                        "close": float(row["close"]) if pd.notna(row["close"]) else None,
                        "volume": int(row["volume"]) if pd.notna(row["volume"]) else None,
                    }
                ]
            )

            csv_buf = io.StringIO()
            out.to_csv(csv_buf, index=False)

            key = _raw_key(trade_date=trade_date, ticker=ticker)
            s3.put_object(
                Bucket=RAW_BUCKET,
                Key=key,
                Body=csv_buf.getvalue().encode("utf-8"),
                ContentType="text/csv",
            )


with DAG(
    dag_id="raw_market_ohlcv_daily_asx",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule="*/5 * * * *",  # adjust as desired; 5-min is safer than 1-min for Yahoo
    catchup=False,
    max_active_runs=1,
    tags=["minio", "raw", "ohlcv", "asx"],
) as dag:
    PythonOperator(
        task_id="fetch_and_write_raw_csvs",
        python_callable=fetch_and_write_raw_csvs,
        op_kwargs={"rolling_trading_days": 30},
    )
2) raw_to_conformed_ohlcv_csv_to_parquet.py
Finds new raw CSV objects and writes conformed Parquet objects (append-only), injecting metadata + row_hash.

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import os

import boto3
import pandas as pd
import pendulum
import pyarrow as pa
import pyarrow.parquet as pq

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.context import Context


DATASET_ID = "market_ohlcv_daily"
EXCHANGE = "ASX"

RAW_BUCKET = "raw"
CONFORMED_BUCKET = "conformed"
MINIO_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def _raw_prefix() -> str:
    return f"tabular/{DATASET_ID}/exchange={EXCHANGE}/"


def _to_conformed_key(raw_key: str) -> str:
    # raw: .../ticker=ABC.csv -> conformed: same path, .parquet
    if raw_key.endswith(".csv"):
        return raw_key[:-4] + ".parquet"
    return raw_key + ".parquet"


def _row_hash(rec: dict) -> str:
    # Hash the logical row (business key + measures + currency)
    payload = "|".join(
        [
            str(rec.get("dataset_id", "")),
            str(rec.get("exchange", "")),
            str(rec.get("ticker", "")),
            str(rec.get("trade_date", "")),
            str(rec.get("open", "")),
            str(rec.get("high", "")),
            str(rec.get("low", "")),
            str(rec.get("close", "")),
            str(rec.get("volume", "")),
            str(rec.get("currency", "")),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _list_all_keys(s3, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            keys.append(obj["Key"])
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return keys


def convert_new_raw_csvs_to_parquet(**context: Context) -> None:
    s3 = _s3_client()

    raw_keys = [
        k for k in _list_all_keys(s3, RAW_BUCKET, _raw_prefix())
        if k.endswith(".csv")
    ]

    conformed_keys = set(_list_all_keys(s3, CONFORMED_BUCKET, _raw_prefix()))

    ingest_ts = datetime.now(timezone.utc).isoformat()
    ingest_batch_id = context.get("run_id") or ingest_ts

    for raw_key in raw_keys:
        out_key = _to_conformed_key(raw_key)
        if out_key in conformed_keys:
            continue  # append-only: do not overwrite

        obj = s3.get_object(Bucket=RAW_BUCKET, Key=raw_key)
        body = obj["Body"].read()

        df = pd.read_csv(io.BytesIO(body))

        # Expect exactly one row per raw CSV (by design), but handle >1 safely.
        df["ingest_ts"] = ingest_ts
        df["ingest_batch_id"] = ingest_batch_id
        df["source_object_key"] = raw_key

        # Compute row_hash per row
        df["row_hash"] = [
            _row_hash(rec) for rec in df.to_dict(orient="records")
        ]

        table = pa.Table.from_pandas(df, preserve_index=False)

        buf = io.BytesIO()
        pq.write_table(table, buf, compression="snappy")
        buf.seek(0)

        s3.put_object(
            Bucket=CONFORMED_BUCKET,
            Key=out_key,
            Body=buf.getvalue(),
            ContentType="application/octet-stream",
        )


with DAG(
    dag_id="raw_to_conformed_ohlcv_csv_to_parquet",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule="*/5 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["minio", "raw", "conformed", "ohlcv"],
) as dag:
    PythonOperator(
        task_id="convert_new_raw_csvs_to_parquet",
        python_callable=convert_new_raw_csvs_to_parquet,
    )
3) conformed_to_curated_ohlcv_daily_snapshot.py
Builds daily snapshot Parquet in curated, per trade_date, “latest ingest wins”.

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import io
import os

import boto3
import pandas as pd
import pendulum
import pyarrow as pa
import pyarrow.parquet as pq

from airflow import DAG
from airflow.operators.python import PythonOperator


DATASET_ID = "market_ohlcv_daily"
EXCHANGE = "ASX"

CONFORMED_BUCKET = "conformed"
CURATED_BUCKET = "curated"
MINIO_ENDPOINT = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    )


def _conformed_prefix() -> str:
    return f"tabular/{DATASET_ID}/exchange={EXCHANGE}/"


def _curated_snapshot_key(trade_date: str) -> str:
    return (
        f"tabular/{DATASET_ID}/exchange={EXCHANGE}/trade_date={trade_date}/snapshot.parquet"
    )


def _list_all_objects(s3, bucket: str, prefix: str) -> list[dict]:
    objs: list[dict] = []
    token = None
    while True:
        kwargs = {"Bucket": bucket, "Prefix": prefix}
        if token:
            kwargs["ContinuationToken"] = token
        resp = s3.list_objects_v2(**kwargs)
        objs.extend(resp.get("Contents", []))
        if resp.get("IsTruncated"):
            token = resp.get("NextContinuationToken")
        else:
            break
    return objs


def _recent_trade_dates(days_back: int = 45) -> list[str]:
    # Use calendar days; conformed only has trading dates anyway.
    today = datetime.now(timezone.utc).date()
    return [(today - timedelta(days=i)).isoformat() for i in range(days_back)]


def build_daily_snapshots(days_back: int = 45) -> None:
    """
    For each recent trade_date, if there is conformed data:
      - read all parquet files for that trade_date
      - dedupe by (dataset_id, exchange, ticker, trade_date)
      - pick latest ingest_ts
      - write curated snapshot.parquet (overwrite is allowed for snapshots)
    """
    s3 = _s3_client()

    for trade_date in _recent_trade_dates(days_back=days_back):
        date_prefix = f"{_conformed_prefix()}trade_date={trade_date}/"
        conformed_objs = [o for o in _list_all_objects(s3, CONFORMED_BUCKET, date_prefix) if o["Key"].endswith(".parquet")]

        if not conformed_objs:
            continue

        # Optional optimisation: only rebuild snapshot if conformed newer than snapshot
        snapshot_key = _curated_snapshot_key(trade_date)
        snapshot_last_modified = None
        try:
            head = s3.head_object(Bucket=CURATED_BUCKET, Key=snapshot_key)
            snapshot_last_modified = head["LastModified"]
        except Exception:
            snapshot_last_modified = None

        latest_conformed = max(o["LastModified"] for o in conformed_objs)
        if snapshot_last_modified and snapshot_last_modified >= latest_conformed:
            continue

        frames: list[pd.DataFrame] = []
        for o in conformed_objs:
            obj = s3.get_object(Bucket=CONFORMED_BUCKET, Key=o["Key"])
            buf = io.BytesIO(obj["Body"].read())
            table = pq.read_table(buf)
            frames.append(table.to_pandas())

        df = pd.concat(frames, ignore_index=True)

        # Ensure ingest_ts sortable
        df["ingest_ts"] = pd.to_datetime(df["ingest_ts"], utc=True, errors="coerce")

        # Latest ingest wins per business key
        df = df.sort_values("ingest_ts", ascending=True)
        df = df.drop_duplicates(
            subset=["dataset_id", "exchange", "ticker", "trade_date"],
            keep="last",
        )

        # Write snapshot
        table = pa.Table.from_pandas(df, preserve_index=False)
        out = io.BytesIO()
        pq.write_table(table, out, compression="snappy")
        out.seek(0)

        s3.put_object(
            Bucket=CURATED_BUCKET,
            Key=snapshot_key,
            Body=out.getvalue(),
            ContentType="application/octet-stream",
        )


with DAG(
    dag_id="conformed_to_curated_ohlcv_daily_snapshot",
    start_date=pendulum.datetime(2024, 1, 1, tz="Australia/Melbourne"),
    schedule="*/10 * * * *",
    catchup=False,
    max_active_runs=1,
    tags=["minio", "conformed", "curated", "ohlcv", "snapshot"],
) as dag:
    PythonOperator(
        task_id="build_daily_snapshots",
        python_callable=build_daily_snapshots,
        op_kwargs={"days_back": 45},
    )
What you need to do in your environment
Drop these three files into your ./dags/ folder.

In Airflow UI, set Variable:

ASX_TICKERS = BHP,CBA,CSL,RIO,WES (whatever you want)

Ensure the Airflow image has the Python deps noted above.

If you paste your current Dockerfile (or how you build the Airflow container), I will give you the minimal change to install yfinance + pyarrow in a way consistent with your Compose setup.

You said:
okay. i have created the three DAG files for the new airflow jobs.

1. i do not have a Dockerfile for the airflow job.

2. can ASX_TICKERS be set as an env override instead of in the UI

seeking a discussion first. no thousand lines of code and dozens of options. 
ChatGPT said:
Understood. Two concise points.

1) No Dockerfile for Airflow: how to handle yfinance + pyarrow
Because your new DAGs import yfinance and pyarrow, they must exist inside the Airflow container. Without a Dockerfile, you still have a practical “minimal-change” path:

Recommended (minimal, standard for Airflow images)
Use the Airflow image’s support for installing extra Python packages at container start via an environment variable (commonly PIP_ADDITIONAL_REQUIREMENTS in the official Apache Airflow Docker Compose patterns).

What this means in practice:

You add one env var to the airflow service in docker-compose.yaml, e.g. yfinance==... pyarrow==... pandas==...

On container start, it pip installs those packages.

Trade-offs (so you can decide deliberately):

Pros: no Dockerfile, very small change, easy to iterate.

Cons: container startup is slower; dependency installs can occasionally fail due to transient network/PyPI issues; not ideal for “production-like” reproducibility.

More robust (but does require a Dockerfile)
Build a small derived Airflow image with the dependencies baked in.

Pros: reproducible, faster startup, less brittle.

Cons: you do need a Dockerfile (but it can be ~5–10 lines).

Given you explicitly don’t have a Dockerfile and want minimal changes, the env-var install is the right first step.

2) Set ASX_TICKERS via env override (not UI)
Yes. You have two clean approaches:

Option A (recommended): keep using Airflow Variable, set it via env
Airflow supports setting Variables from environment variables using the pattern:

AIRFLOW_VAR_ASX_TICKERS="BHP,CBA,CSL,RIO"

So you can set this in docker-compose.yaml under the Airflow service environment: block, and your DAG can keep doing Variable.get("ASX_TICKERS", ...) without any UI interaction.

Pros:

no UI clicks

still uses Airflow’s variable system (consistent with future expansion)

Option B: bypass Airflow Variables entirely
Change the DAG to read directly from os.environ["ASX_TICKERS"].

Pros:

simplest mental model
Cons:

you lose the benefits of Airflow Variables (centralised config, later overrides, etc.)

Given your preference for clean architecture and future multiple datasets, I recommend Option A.

If you paste just the Airflow service section of your docker-compose.yaml, I’ll point to the exact minimal lines to add for:

pip-installed deps, and

AIRFLOW_VAR_ASX_TICKERS env override,

without introducing a large set of alternative options.

You said:
  airflow:
    image: apache/airflow:2.10.3
    container_name: airflow
    depends_on:
      minio:
        condition: service_healthy
      minio-init:
        condition: service_completed_successfully
    environment:
      # Airflow core (simplified single-container)
      AIRFLOW__CORE__EXECUTOR: SequentialExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: sqlite:////opt/airflow/airflow.db
      AIRFLOW__CORE__LOAD_EXAMPLES: "False"
      AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "False"
      AIRFLOW__WEBSERVER__EXPOSE_CONFIG: "True"

      # MinIO / S3-compatible defaults for DAG code
      S3_ENDPOINT_URL: "http://minio:9000"
      AWS_ACCESS_KEY_ID: "minioadmin"
      AWS_SECRET_ACCESS_KEY: "minioadmin"
      AWS_DEFAULT_REGION: "us-east-1"

      # Optional permissions helper (Linux/WSL; harmless elsewhere)
      AIRFLOW_UID: "${AIRFLOW_UID:-50000}"

    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
      - airflow-db:/opt/airflow

    command: >
      bash -lc "
      airflow db migrate &&
      airflow users create \
        --username minioadmin \
        --password minioadmin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com
      airflow webserver & airflow scheduler
      "
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8080/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 30
ChatGPT said:
Below are the minimal, targeted changes to your existing airflow: service to address both items:

install yfinance + pyarrow without a Dockerfile

set ASX_TICKERS via env (no UI)

1) Install Python deps without a Dockerfile
Add one environment variable:

PIP_ADDITIONAL_REQUIREMENTS: "yfinance pyarrow pandas"

This is the conventional mechanism used with the Apache Airflow Docker Compose patterns to pip-install extras at container start. It keeps your Compose-based workflow and avoids introducing a build step.

Operational note: first startup after adding this will be slower because it installs packages.

2) Set ASX_TICKERS via env override (recommended pattern)
Add this environment variable:

AIRFLOW_VAR_ASX_TICKERS: "BHP,CBA,CSL,RIO,WES"

Your DAG can keep using Variable.get("ASX_TICKERS", ...) and it will resolve from env without needing to set anything in the UI.

Minimal patch (only the added lines)
Insert these under environment: in your airflow: service:

      # Install DAG dependencies at container start (no Dockerfile)
      PIP_ADDITIONAL_REQUIREMENTS: "yfinance pyarrow pandas"

      # Airflow Variable override via env (no UI)
      AIRFLOW_VAR_ASX_TICKERS: "BHP,CBA,CSL,RIO,WES"
One important correction in your command
Right now you are missing a command separator before starting the webserver/scheduler. After the airflow users create ... block, you should add && (or a ;) so the shell does not treat airflow webserver as another argument to the users create command.

Minimal fix (add && on the line before airflow webserver):

      airflow users create \
        --username minioadmin \
        --password minioadmin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com &&
      airflow webserver & airflow scheduler
That’s it: no Dockerfile, no UI config, and you keep the same single-container Airflow pattern.

If you want one quick verification step after restart: run docker exec -it airflow python -c "import yfinance, pyarrow; print('ok')" to confirm the packages are available inside the container.

You said:
airflow container status still 'starting' -- can i see the progress somehow? 
ChatGPT said:
Yes. What you are seeing is expected given the change you just made, and there are reliable ways to see progress.

Why it’s still “starting”
Because you added:

PIP_ADDITIONAL_REQUIREMENTS: "yfinance pyarrow pandas"
the Airflow container now does this on every startup:

Start container

pip install yfinance pyarrow pandas

Run airflow db migrate

Create user

Start webserver + scheduler

Healthcheck passes → status becomes healthy

Steps 2 and 3 can easily take 1–3 minutes, especially pyarrow, which downloads large wheels. During this time Docker reports the container as starting.

Nothing is hung unless it stays there for a long time (≈10+ minutes).

How to see exactly what it is doing (recommended)
1. Stream the Airflow container logs
This is the single best signal.

docker logs -f airflow
What you should expect to see, in order:

Collecting yfinance

Collecting pyarrow

Installing collected packages

Running airflow db migrate

Creating admin user

Starting gunicorn

Scheduler starting

If you see pip output progressing, it is working.

2. Check container health explicitly
In another terminal:

docker ps --format '{{.Names}}: {{.Status}}' | sort
You should see something like:

airflow: Up X minutes (health: starting)
This confirms Docker is waiting for the healthcheck, not that the container failed.

3. Confirm it’s not stuck on the healthcheck
Your healthcheck is:

curl -fsS http://localhost:8080/health || exit 1
This will fail until the webserver is up, which only happens after pip installs + DB migrate.

So starting ≠ broken.

If you want even more visibility (optional)
You can exec into the container while it’s starting:

docker exec -it airflow bash
Then run:

ps aux | grep -E 'pip|airflow'
You’ll usually see pip install or airflow db migrate running.

When should you worry?
Only if one of these happens:

docker logs airflow shows no output for several minutes

You see a pip error (SSL, wheel build failure)

Status flips to unhealthy or container restarts

If that happens, paste the last ~30 lines of docker logs airflow and we’ll diagnose precisely.

One pragmatic note (for later)
This behaviour is why teams eventually switch to a tiny Dockerfile:

pip installs once at build time

container starts in seconds

But for right now, your setup is correct and behaving normally.

Let the logs guide you — that’s the source of truth.

You said:
airflow: Up 8 minutes (unhealthy)

the scheduler seems to be running the hearbeat dags, but i am not sure about the yFinance DAGs
ChatGPT said:
If the scheduler is running DAGs but the container is (unhealthy), the usual situation is:

Airflow webserver is not responding on localhost:8080/health inside the container, so the Docker healthcheck keeps failing.

The scheduler can still run even if the webserver is down (or crashed).

Here is the quickest way to see exactly what is happening, in the smallest number of commands.

1) Confirm what the healthcheck is failing on
Run:

docker exec -it airflow bash -lc "curl -v http://localhost:8080/health || true"
Interpretation:

If you see “Connection refused” → webserver is not running or not bound.

If you see HTTP 5xx → webserver is up but unhealthy (often DB/initialisation issues).

2) Check whether the webserver process is running
Run:

docker exec -it airflow bash -lc "ps aux | egrep 'airflow webserver|gunicorn' | grep -v grep || true"
docker exec -it airflow bash -lc "ps aux | egrep 'airflow scheduler' | grep -v grep || true"
You’ll typically find scheduler is present but webserver/gunicorn is missing (explains unhealthy).

3) Inspect the Airflow logs for the webserver start failure
The most direct signal is container logs:

docker logs --tail 200 airflow
Look for:

pip install failures (yfinance/pyarrow)

“command not found”

a syntax error in the bash -lc " ... " command

airflow users create errors (user already exists) causing the command chain to stop before starting the webserver

Very common culprit in your compose command
Your command sequence must have proper separators. If the airflow users create ... line fails (for example “user already exists”) and you used &&, the webserver never starts. If you used no separator at all, the shell can also mis-parse the command.

If the logs show an error like “already exists”, the minimal fix is to make the user-create step non-fatal, e.g. append || true to that command.

4) Verify the yFinance DAGs are actually loaded
Even if the scheduler is running, it may have skipped those DAGs due to import errors (missing packages).

Run:

docker exec -it airflow bash -lc "airflow dags list | egrep 'raw_market_ohlcv_daily_asx|raw_to_conformed_ohlcv_csv_to_parquet|conformed_to_curated_ohlcv_daily_snapshot' || true"
If they don’t appear, check import errors:

docker exec -it airflow bash -lc "python -c 'import yfinance, pyarrow; print(\"imports_ok\")' || true"
If that fails, then PIP_ADDITIONAL_REQUIREMENTS did not install correctly; the failure will be visible in docker logs airflow.

What I need from you to diagnose precisely
Paste the output of:

docker exec -it airflow bash -lc "curl -v http://localhost:8080/health || true"

docker logs --tail 80 airflow

With those two snippets, I can tell you exactly why the container is unhealthy and whether the yFinance DAGs are failing to import or just not scheduled.

You said:
minio-test> docker exec -it airflow bash -lc "curl -v http://localhost:8080/health || true"
*   Trying 127.0.0.1:8080...
* connect to 127.0.0.1 port 8080 failed: Connection refused
*   Trying [::1]:8080...
* connect to ::1 port 8080 failed: Connection refused
* Failed to connect to localhost port 8080 after 0 ms: Couldn't connect to server
* Closing connection 0
curl: (7) Failed to connect to localhost port 8080 after 0 ms: Couldn't connect to server
ChatGPT said:
That result is definitive: the Airflow webserver is not running inside the container (hence connection refused), so the Docker healthcheck can never pass and the container remains unhealthy. The scheduler can still run, which matches what you’re observing.

There are only a few likely causes in your setup, and you can confirm which one in 1–2 commands.

1) Confirm whether the webserver process exists
Run:

docker exec -it airflow bash -lc "ps aux | egrep 'airflow webserver|gunicorn' | grep -v grep || true"
docker exec -it airflow bash -lc "ps aux | egrep 'airflow scheduler' | grep -v grep || true"
You will almost certainly see the scheduler, but not webserver/gunicorn.

2) The most common root cause in your command: block
Your compose command runs:

airflow db migrate &&

airflow users create ...

airflow webserver & airflow scheduler

If airflow users create fails (very commonly because the user already exists), and you have && chaining, then the webserver never starts. Even without &&, quoting/line breaks can still cause subtle shell parsing failures.

Minimal, robust fix (single-container, still simple)
Update your command: to:

always run migrations

try to create the user but do not fail the whole container if the user already exists

start webserver and scheduler

Use this exact structure:

command: >
  bash -lc "
  set -e;
  airflow db migrate;
  airflow users create \
    --username minioadmin \
    --password minioadmin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com || true;
  airflow webserver &
  exec airflow scheduler
  "
Why this works:

|| true prevents “user already exists” from blocking startup.

exec airflow scheduler ensures the container’s main process is the scheduler (clean lifecycle).

Webserver is started reliably every time.

3) Verify whether your yFinance DAGs are loading
Once the webserver is up (curl works), confirm DAG registration:

docker exec -it airflow bash -lc "airflow dags list | egrep 'raw_market_ohlcv_daily_asx|raw_to_conformed_ohlcv_csv_to_parquet|conformed_to_curated_ohlcv_daily_snapshot' || true"
And confirm dependencies installed:

docker exec -it airflow bash -lc "python -c 'import yfinance, pyarrow; print(\"imports_ok\")'"
4) If the webserver still doesn’t start after the command fix
Then it is almost certainly crashing at boot due to a Python dependency install issue. The fastest proof is:

docker logs --tail 120 airflow
If you paste that output, I can point to the exact failing line (it is usually a pip install error or a DB init error).

At this point, apply the command fix first; it addresses the most frequent reason for “scheduler runs but /health refused.”

You said:
docker exec -it airflow bash -lc "ps aux | egrep 'airflow webserver|gunicorn' | grep -v grep || true"
bash: line 1: ps: command not found
ChatGPT said:
Good catch — this is expected and it tells us something important.

Why ps is missing
The official apache/airflow:2.10.3 image is very slim. It does not include procps, so ps is not available by default.

This is not an error and does not indicate container corruption.

How to check webserver status without ps
1) Check whether anything is listening on port 8080 (best signal)
Run:

docker exec -it airflow bash -lc "ss -ltn || true"
If you see no listener on :8080, the webserver is not running.

If ss is also missing (possible), try:

docker exec -it airflow bash -lc "netstat -ltn || true"
(One of these is usually present.)

2) Ask Airflow directly whether the webserver thinks it’s running
Run:

docker exec -it airflow bash -lc "airflow info | sed -n '/Webserver/,/Scheduler/p'"
This does not require ps and often shows whether Airflow considers the webserver active.

3) Most reliable: inspect container logs
At this point, logs are the authoritative source:

docker logs --tail 150 airflow
You are specifically looking for one of these patterns:

❌ airflow users create ... already exists (and then no webserver start)

❌ pip install failure (pyarrow, SSL, wheel build)

❌ gunicorn crash

✅ Starting gunicorn / Listening at: http://0.0.0.0:8080

Root cause (almost certainly)
Given scheduler runs, /health is refused, and no webserver, the cause is almost always:

airflow users create failed and prevented airflow webserver from starting

This happens on every restart unless guarded.

Action you should take now (minimal, deterministic)
Update your command: block exactly as below (this does not add tools, images, or complexity):

command: >
  bash -lc "
  set -e;
  airflow db migrate;
  airflow users create \
    --username minioadmin \
    --password minioadmin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com || true;
  airflow webserver &
  exec airflow scheduler
  "
Then:

docker compose down
docker compose up -d
Wait ~30–60 seconds, then test:

docker exec -it airflow bash -lc "curl -fsS http://localhost:8080/health"
You should get JSON back and the container status will flip to healthy.

Why I’m confident this is the fix
Scheduler running ⇒ DB + core Airflow OK

/health refused ⇒ webserver never started

Missing ps is normal

This exact failure mode is extremely common with single-container Airflow setups

Apply the command fix first.
If /health is still refused after that, paste the last 80 lines of docker logs airflow and we will resolve it in one more step.

You said:
previously you have used apt with the alpine image to run a test command. would this help here?
ChatGPT said:
It can help, but only in a very specific way.

What would help
Your problem is: webserver not running (health endpoint refused). To debug that, you want either:

container logs (best), or

basic process/network tools (ps, ss, etc.).

Because the apache/airflow:2.10.3 image is slim, installing tools inside it can be useful.

What won’t help
Running an Alpine sidecar container and using apk add there will not let you inspect processes inside the airflow container. Different containers have different PID namespaces. You can still test network reachability, but you already know localhost:8080 inside the container is refused.

So: Alpine is great for MinIO connectivity tests; it won’t tell you why Airflow webserver didn’t start.

The right way to add ps/diagnostic tools to the Airflow container
The Airflow image is Debian-based, so the equivalent of apk is apt-get, not apk.

You can install tools temporarily (for debugging) with:

docker exec -it airflow bash -lc "apt-get update && apt-get install -y procps iproute2 curl"
Then you can run:

docker exec -it airflow bash -lc "ps aux | head"
docker exec -it airflow bash -lc "ss -ltnp | head"
This is useful for diagnosis, but I would not rely on it as a permanent solution because:

it changes the running container state,

it will be lost on rebuild,

it adds time and network dependency.

The most efficient next step (still)
Before installing anything, the fastest, most deterministic signal is:

docker logs --tail 150 airflow
That will usually show the exact reason the webserver didn’t start (most commonly: airflow users create failed and stopped the command chain, or a pip install failure from PIP_ADDITIONAL_REQUIREMENTS).

Recommendation
Use logs first.

If logs are unclear, then install procps via apt-get inside the Airflow container for a one-off diagnosis.

Independently, apply the robust command: change I gave earlier (|| true on user create + exec airflow scheduler), because it prevents the most common failure mode.

If you paste the last ~80 lines of docker logs airflow, I can tell you whether installing tools is even necessary.

You said:
[2025-12-14T06:59:01.556+0000] {scheduler_job_runner.py:634} INFO - Setting the following tasks to queued state:
        <TaskInstance: conformed_to_curated_copy.copy_new_conformed_objects scheduled__2025-12-14T06:58:00+00:00 [scheduled]>
        <TaskInstance: raw_heartbeat_1m.write_time_to_raw scheduled__2025-12-14T06:58:00+00:00 [scheduled]>
        <TaskInstance: raw_to_conformed_copy.copy_new_raw_objects scheduled__2025-12-14T06:58:00+00:00 [scheduled]>
[2025-12-14T06:59:01.558+0000] {scheduler_job_runner.py:736} INFO - Trying to enqueue tasks: [<TaskInstance: conformed_to_curated_copy.copy_new_conformed_objects scheduled__2025-12-14T06:58:00+00:00 [scheduled]>, <TaskInstance: raw_heartbeat_1m.write_time_to_raw scheduled__2025-12-14T06:58:00+00:00 [scheduled]>, <TaskInstance: raw_to_conformed_copy.copy_new_raw_objects scheduled__2025-12-14T06:58:00+00:00 [scheduled]>] for executor: SequentialExecutor(parallelism=32)
[2025-12-14T06:59:01.558+0000] {scheduler_job_runner.py:680} INFO - Sending TaskInstanceKey(dag_id='conformed_to_curated_copy', task_id='copy_new_conformed_objects', run_id='scheduled__2025-12-14T06:58:00+00:00', try_number=1, map_index=-1) to SequentialExecutor with priority 1 and queue default
[2025-12-14T06:59:01.559+0000] {base_executor.py:168} INFO - Adding to queue: ['airflow', 'tasks', 'run', 'conformed_to_curated_copy', 'copy_new_conformed_objects', 'scheduled__2025-12-14T06:58:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/conformed_to_curated_copy.py']
[2025-12-14T06:59:01.559+0000] {scheduler_job_runner.py:680} INFO - Sending TaskInstanceKey(dag_id='raw_heartbeat_1m', task_id='write_time_to_raw', run_id='scheduled__2025-12-14T06:58:00+00:00', try_number=1, map_index=-1) to SequentialExecutor with priority 1 and queue default
[2025-12-14T06:59:01.559+0000] {base_executor.py:168} INFO - Adding to queue: ['airflow', 'tasks', 'run', 'raw_heartbeat_1m', 'write_time_to_raw', 'scheduled__2025-12-14T06:58:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/raw_heartbeat_1m.py']
[2025-12-14T06:59:01.560+0000] {scheduler_job_runner.py:680} INFO - Sending TaskInstanceKey(dag_id='raw_to_conformed_copy', task_id='copy_new_raw_objects', run_id='scheduled__2025-12-14T06:58:00+00:00', try_number=1, map_index=-1) to SequentialExecutor with priority 1 and queue default
[2025-12-14T06:59:01.560+0000] {base_executor.py:168} INFO - Adding to queue: ['airflow', 'tasks', 'run', 'raw_to_conformed_copy', 'copy_new_raw_objects', 'scheduled__2025-12-14T06:58:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/raw_to_conformed_copy.py']
[2025-12-14T06:59:01.569+0000] {sequential_executor.py:84} INFO - Executing command: ['airflow', 'tasks', 'run', 'conformed_to_curated_copy', 'copy_new_conformed_objects', 'scheduled__2025-12-14T06:58:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/conformed_to_curated_copy.py']
/home/airflow/.local/lib/python3.12/site-packages/airflow/configuration.py:859 FutureWarning: section/key [core/sql_alchemy_conn] has been deprecated, you should use[database/sql_alchemy_conn] instead. Please update your conf.get* call to use the new name
[2025-12-14T06:59:05.116+0000] {dagbag.py:588} INFO - Filling up the DagBag from /opt/airflow/dags/conformed_to_curated_copy.py
[2025-12-14T06:59:05.572+0000] {task_command.py:467} INFO - Running <TaskInstance: conformed_to_curated_copy.copy_new_conformed_objects scheduled__2025-12-14T06:58:00+00:00 [queued]> on host 41d6495e6efb
[2025-12-14T06:59:07.028+0000] {sequential_executor.py:84} INFO - Executing command: ['airflow', 'tasks', 'run', 'raw_heartbeat_1m', 'write_time_to_raw', 'scheduled__2025-12-14T06:58:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/raw_heartbeat_1m.py']
/home/airflow/.local/lib/python3.12/site-packages/airflow/configuration.py:859 FutureWarning: section/key [core/sql_alchemy_conn] has been deprecated, you should use[database/sql_alchemy_conn] instead. Please update your conf.get* call to use the new name
[2025-12-14T06:59:10.955+0000] {dagbag.py:588} INFO - Filling up the DagBag from /opt/airflow/dags/raw_heartbeat_1m.py
[2025-12-14T06:59:11.319+0000] {task_command.py:467} INFO - Running <TaskInstance: raw_heartbeat_1m.write_time_to_raw scheduled__2025-12-14T06:58:00+00:00 [queued]> on host 41d6495e6efb
[2025-12-14T06:59:12.610+0000] {sequential_executor.py:84} INFO - Executing command: ['airflow', 'tasks', 'run', 'raw_to_conformed_copy', 'copy_new_raw_objects', 'scheduled__2025-12-14T06:58:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/raw_to_conformed_copy.py']
/home/airflow/.local/lib/python3.12/site-packages/airflow/configuration.py:859 FutureWarning: section/key [core/sql_alchemy_conn] has been deprecated, you should use[database/sql_alchemy_conn] instead. Please update your conf.get* call to use the new name
[2025-12-14T06:59:16.077+0000] {dagbag.py:588} INFO - Filling up the DagBag from /opt/airflow/dags/raw_to_conformed_copy.py
[2025-12-14T06:59:16.432+0000] {task_command.py:467} INFO - Running <TaskInstance: raw_to_conformed_copy.copy_new_raw_objects scheduled__2025-12-14T06:58:00+00:00 [queued]> on host 41d6495e6efb
[2025-12-14T06:59:17.636+0000] {scheduler_job_runner.py:764} INFO - Received executor event with state success for task instance TaskInstanceKey(dag_id='conformed_to_curated_copy', task_id='copy_new_conformed_objects', run_id='scheduled__2025-12-14T06:58:00+00:00', try_number=1, map_index=-1)
[2025-12-14T06:59:17.637+0000] {scheduler_job_runner.py:764} INFO - Received executor event with state success for task instance TaskInstanceKey(dag_id='raw_heartbeat_1m', task_id='write_time_to_raw', run_id='scheduled__2025-12-14T06:58:00+00:00', try_number=1, map_index=-1)
[2025-12-14T06:59:17.638+0000] {scheduler_job_runner.py:764} INFO - Received executor event with state success for task instance TaskInstanceKey(dag_id='raw_to_conformed_copy', task_id='copy_new_raw_objects', run_id='scheduled__2025-12-14T06:58:00+00:00', try_number=1, map_index=-1)
[2025-12-14T06:59:17.645+0000] {scheduler_job_runner.py:801} INFO - TaskInstance Finished: dag_id=raw_to_conformed_copy, task_id=copy_new_raw_objects, run_id=scheduled__2025-12-14T06:58:00+00:00, map_index=-1, run_start_date=2025-12-14 06:59:16.549435+00:00, run_end_date=2025-12-14 06:59:16.995449+00:00, run_duration=0.446014, state=success, executor=SequentialExecutor(parallelism=32), executor_state=success, try_number=1, max_tries=0, job_id=51, pool=default_pool, queue=default, priority_weight=1, operator=PythonOperator, queued_dttm=2025-12-14 06:59:01.557118+00:00, queued_by_job_id=1, pid=1420
[2025-12-14T06:59:17.647+0000] {scheduler_job_runner.py:801} INFO - TaskInstance Finished: dag_id=raw_heartbeat_1m, task_id=write_time_to_raw, run_id=scheduled__2025-12-14T06:58:00+00:00, map_index=-1, run_start_date=2025-12-14 06:59:11.481113+00:00, run_end_date=2025-12-14 06:59:12.017781+00:00, run_duration=0.536668, state=success, executor=SequentialExecutor(parallelism=32), executor_state=success, try_number=1, max_tries=0, job_id=50, pool=default_pool, queue=default, priority_weight=1, operator=PythonOperator, queued_dttm=2025-12-14 06:59:01.557118+00:00, queued_by_job_id=1, pid=1402
[2025-12-14T06:59:17.648+0000] {scheduler_job_runner.py:801} INFO - TaskInstance Finished: dag_id=conformed_to_curated_copy, task_id=copy_new_conformed_objects, run_id=scheduled__2025-12-14T06:58:00+00:00, map_index=-1, run_start_date=2025-12-14 06:59:05.649077+00:00, run_end_date=2025-12-14 06:59:06.201886+00:00, run_duration=0.552809, state=success, executor=SequentialExecutor(parallelism=32), executor_state=success, try_number=1, max_tries=0, job_id=49, pool=default_pool, queue=default, priority_weight=1, operator=PythonOperator, queued_dttm=2025-12-14 06:59:01.557118+00:00, queued_by_job_id=1, pid=1391
[2025-12-14T06:59:18.293+0000] {dagrun.py:854} INFO - Marking run <DagRun conformed_to_curated_copy @ 2025-12-14 06:58:00+00:00: scheduled__2025-12-14T06:58:00+00:00, state:running, queued_at: 2025-12-14 06:59:01.464676+00:00. externally triggered: False> successful
[2025-12-14T06:59:18.294+0000] {dagrun.py:905} INFO - DagRun Finished: dag_id=conformed_to_curated_copy, execution_date=2025-12-14 06:58:00+00:00, run_id=scheduled__2025-12-14T06:58:00+00:00, run_start_date=2025-12-14 06:59:01.510626+00:00, run_end_date=2025-12-14 06:59:18.294707+00:00, run_duration=16.784081, state=success, external_trigger=False, run_type=scheduled, data_interval_start=2025-12-14 06:58:00+00:00, data_interval_end=2025-12-14 06:59:00+00:00, dag_hash=ffaeb091ac52d4d08833021793f446c2
[2025-12-14T06:59:18.310+0000] {dag.py:4180} INFO - Setting next_dagrun for conformed_to_curated_copy to 2025-12-14 06:59:00+00:00, run_after=2025-12-14 07:00:00+00:00
[2025-12-14T06:59:18.316+0000] {dagrun.py:854} INFO - Marking run <DagRun raw_heartbeat_1m @ 2025-12-14 06:58:00+00:00: scheduled__2025-12-14T06:58:00+00:00, state:running, queued_at: 2025-12-14 06:59:01.478028+00:00. externally triggered: False> successful
[2025-12-14T06:59:18.316+0000] {dagrun.py:905} INFO - DagRun Finished: dag_id=raw_heartbeat_1m, execution_date=2025-12-14 06:58:00+00:00, run_id=scheduled__2025-12-14T06:58:00+00:00, run_start_date=2025-12-14 06:59:01.511332+00:00, run_end_date=2025-12-14 06:59:18.316629+00:00, run_duration=16.805297, state=success, external_trigger=False, run_type=scheduled, data_interval_start=2025-12-14 06:58:00+00:00, data_interval_end=2025-12-14 06:59:00+00:00, dag_hash=3cce28d9499e08cc286e82938b63a944
[2025-12-14T06:59:18.324+0000] {dag.py:4180} INFO - Setting next_dagrun for raw_heartbeat_1m to 2025-12-14 06:59:00+00:00, run_after=2025-12-14 07:00:00+00:00
[2025-12-14T06:59:18.329+0000] {dagrun.py:854} INFO - Marking run <DagRun raw_to_conformed_copy @ 2025-12-14 06:58:00+00:00: scheduled__2025-12-14T06:58:00+00:00, state:running, queued_at: 2025-12-14 06:59:01.483085+00:00. externally triggered: False> successful
[2025-12-14T06:59:18.330+0000] {dagrun.py:905} INFO - DagRun Finished: dag_id=raw_to_conformed_copy, execution_date=2025-12-14 06:58:00+00:00, run_id=scheduled__2025-12-14T06:58:00+00:00, run_start_date=2025-12-14 06:59:01.511960+00:00, run_end_date=2025-12-14 06:59:18.330214+00:00, run_duration=16.818254, state=success, external_trigger=False, run_type=scheduled, data_interval_start=2025-12-14 06:58:00+00:00, data_interval_end=2025-12-14 06:59:00+00:00, dag_hash=575c783bd41bb04215e8792d3d0ff4fb
[2025-12-14T06:59:18.339+0000] {dag.py:4180} INFO - Setting next_dagrun for raw_to_conformed_copy to 2025-12-14 06:59:00+00:00, run_after=2025-12-14 07:00:00+00:00
[2025-12-14T07:00:02.202+0000] {scheduler_job_runner.py:1513} INFO - DAG raw_to_conformed_ohlcv_csv_to_parquet is at (or above) max_active_runs (1 of 1), not creating any more runs
[2025-12-14T07:00:02.213+0000] {dag.py:4180} INFO - Setting next_dagrun for conformed_to_curated_copy to 2025-12-14 07:00:00+00:00, run_after=2025-12-14 07:01:00+00:00
[2025-12-14T07:00:02.216+0000] {scheduler_job_runner.py:1513} INFO - DAG raw_heartbeat_1m is at (or above) max_active_runs (1 of 1), not creating any more runs
[2025-12-14T07:00:02.224+0000] {dag.py:4180} INFO - Setting next_dagrun for raw_to_conformed_copy to 2025-12-14 07:00:00+00:00, run_after=2025-12-14 07:01:00+00:00
[2025-12-14T07:00:02.227+0000] {scheduler_job_runner.py:1513} INFO - DAG conformed_to_curated_ohlcv_daily_snapshot is at (or above) max_active_runs (1 of 1), not creating any more runs
[2025-12-14T07:00:02.298+0000] {scheduler_job_runner.py:423} INFO - 5 tasks up for execution:
        <TaskInstance: conformed_to_curated_ohlcv_daily_snapshot.build_daily_snapshots scheduled__2025-12-14T06:50:00+00:00 [scheduled]>
        <TaskInstance: raw_to_conformed_ohlcv_csv_to_parquet.convert_new_raw_csvs_to_parquet scheduled__2025-12-14T06:55:00+00:00 [scheduled]>
        <TaskInstance: conformed_to_curated_copy.copy_new_conformed_objects scheduled__2025-12-14T06:59:00+00:00 [scheduled]>
        <TaskInstance: raw_heartbeat_1m.write_time_to_raw scheduled__2025-12-14T06:59:00+00:00 [scheduled]>
        <TaskInstance: raw_to_conformed_copy.copy_new_raw_objects scheduled__2025-12-14T06:59:00+00:00 [scheduled]>
[2025-12-14T07:00:02.299+0000] {scheduler_job_runner.py:495} INFO - DAG conformed_to_curated_ohlcv_daily_snapshot has 0/16 running and queued tasks
[2025-12-14T07:00:02.299+0000] {scheduler_job_runner.py:495} INFO - DAG raw_to_conformed_ohlcv_csv_to_parquet has 0/16 running and queued tasks
[2025-12-14T07:00:02.300+0000] {scheduler_job_runner.py:495} INFO - DAG conformed_to_curated_copy has 0/16 running and queued tasks
[2025-12-14T07:00:02.300+0000] {scheduler_job_runner.py:495} INFO - DAG raw_heartbeat_1m has 0/16 running and queued tasks
[2025-12-14T07:00:02.300+0000] {scheduler_job_runner.py:495} INFO - DAG raw_to_conformed_copy has 0/16 running and queued tasks
[2025-12-14T07:00:02.301+0000] {scheduler_job_runner.py:634} INFO - Setting the following tasks to queued state:
        <TaskInstance: conformed_to_curated_ohlcv_daily_snapshot.build_daily_snapshots scheduled__2025-12-14T06:50:00+00:00 [scheduled]>
        <TaskInstance: raw_to_conformed_ohlcv_csv_to_parquet.convert_new_raw_csvs_to_parquet scheduled__2025-12-14T06:55:00+00:00 [scheduled]>
        <TaskInstance: conformed_to_curated_copy.copy_new_conformed_objects scheduled__2025-12-14T06:59:00+00:00 [scheduled]>
        <TaskInstance: raw_heartbeat_1m.write_time_to_raw scheduled__2025-12-14T06:59:00+00:00 [scheduled]>
        <TaskInstance: raw_to_conformed_copy.copy_new_raw_objects scheduled__2025-12-14T06:59:00+00:00 [scheduled]>
[2025-12-14T07:00:02.303+0000] {scheduler_job_runner.py:736} INFO - Trying to enqueue tasks: [<TaskInstance: conformed_to_curated_ohlcv_daily_snapshot.build_daily_snapshots scheduled__2025-12-14T06:50:00+00:00 [scheduled]>, <TaskInstance: raw_to_conformed_ohlcv_csv_to_parquet.convert_new_raw_csvs_to_parquet scheduled__2025-12-14T06:55:00+00:00 [scheduled]>, <TaskInstance: conformed_to_curated_copy.copy_new_conformed_objects scheduled__2025-12-14T06:59:00+00:00 [scheduled]>, <TaskInstance: raw_heartbeat_1m.write_time_to_raw scheduled__2025-12-14T06:59:00+00:00 [scheduled]>, <TaskInstance: raw_to_conformed_copy.copy_new_raw_objects scheduled__2025-12-14T06:59:00+00:00 [scheduled]>] for executor: SequentialExecutor(parallelism=32)
[2025-12-14T07:00:02.304+0000] {scheduler_job_runner.py:680} INFO - Sending TaskInstanceKey(dag_id='conformed_to_curated_ohlcv_daily_snapshot', task_id='build_daily_snapshots', run_id='scheduled__2025-12-14T06:50:00+00:00', try_number=1, map_index=-1) to SequentialExecutor with priority 1 and queue default
[2025-12-14T07:00:02.304+0000] {base_executor.py:168} INFO - Adding to queue: ['airflow', 'tasks', 'run', 'conformed_to_curated_ohlcv_daily_snapshot', 'build_daily_snapshots', 'scheduled__2025-12-14T06:50:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/conformed_to_curated_ohlcv_daily_snapshot.py']
[2025-12-14T07:00:02.305+0000] {scheduler_job_runner.py:680} INFO - Sending TaskInstanceKey(dag_id='raw_to_conformed_ohlcv_csv_to_parquet', task_id='convert_new_raw_csvs_to_parquet', run_id='scheduled__2025-12-14T06:55:00+00:00', try_number=1, map_index=-1) to SequentialExecutor with priority 1 and queue default
[2025-12-14T07:00:02.305+0000] {base_executor.py:168} INFO - Adding to queue: ['airflow', 'tasks', 'run', 'raw_to_conformed_ohlcv_csv_to_parquet', 'convert_new_raw_csvs_to_parquet', 'scheduled__2025-12-14T06:55:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/raw_to_conformed_ohlcv_csv_to_parquet.py']
[2025-12-14T07:00:02.305+0000] {scheduler_job_runner.py:680} INFO - Sending TaskInstanceKey(dag_id='conformed_to_curated_copy', task_id='copy_new_conformed_objects', run_id='scheduled__2025-12-14T06:59:00+00:00', try_number=1, map_index=-1) to SequentialExecutor with priority 1 and queue default
[2025-12-14T07:00:02.306+0000] {base_executor.py:168} INFO - Adding to queue: ['airflow', 'tasks', 'run', 'conformed_to_curated_copy', 'copy_new_conformed_objects', 'scheduled__2025-12-14T06:59:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/conformed_to_curated_copy.py']
[2025-12-14T07:00:02.306+0000] {scheduler_job_runner.py:680} INFO - Sending TaskInstanceKey(dag_id='raw_heartbeat_1m', task_id='write_time_to_raw', run_id='scheduled__2025-12-14T06:59:00+00:00', try_number=1, map_index=-1) to SequentialExecutor with priority 1 and queue default
[2025-12-14T07:00:02.307+0000] {base_executor.py:168} INFO - Adding to queue: ['airflow', 'tasks', 'run', 'raw_heartbeat_1m', 'write_time_to_raw', 'scheduled__2025-12-14T06:59:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/raw_heartbeat_1m.py']
[2025-12-14T07:00:02.307+0000] {scheduler_job_runner.py:680} INFO - Sending TaskInstanceKey(dag_id='raw_to_conformed_copy', task_id='copy_new_raw_objects', run_id='scheduled__2025-12-14T06:59:00+00:00', try_number=1, map_index=-1) to SequentialExecutor with priority 1 and queue default
[2025-12-14T07:00:02.307+0000] {base_executor.py:168} INFO - Adding to queue: ['airflow', 'tasks', 'run', 'raw_to_conformed_copy', 'copy_new_raw_objects', 'scheduled__2025-12-14T06:59:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/raw_to_conformed_copy.py']
[2025-12-14T07:00:02.319+0000] {sequential_executor.py:84} INFO - Executing command: ['airflow', 'tasks', 'run', 'conformed_to_curated_ohlcv_daily_snapshot', 'build_daily_snapshots', 'scheduled__2025-12-14T06:50:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/conformed_to_curated_ohlcv_daily_snapshot.py']
/home/airflow/.local/lib/python3.12/site-packages/airflow/configuration.py:859 FutureWarning: section/key [core/sql_alchemy_conn] has been deprecated, you should use[database/sql_alchemy_conn] instead. Please update your conf.get* call to use the new name
[2025-12-14T07:00:06.225+0000] {dagbag.py:588} INFO - Filling up the DagBag from /opt/airflow/dags/conformed_to_curated_ohlcv_daily_snapshot.py
[2025-12-14T07:00:06.986+0000] {task_command.py:467} INFO - Running <TaskInstance: conformed_to_curated_ohlcv_daily_snapshot.build_daily_snapshots scheduled__2025-12-14T06:50:00+00:00 [queued]> on host 41d6495e6efb
[2025-12-14T07:00:08.793+0000] {sequential_executor.py:84} INFO - Executing command: ['airflow', 'tasks', 'run', 'raw_to_conformed_ohlcv_csv_to_parquet', 'convert_new_raw_csvs_to_parquet', 'scheduled__2025-12-14T06:55:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/raw_to_conformed_ohlcv_csv_to_parquet.py']
/home/airflow/.local/lib/python3.12/site-packages/airflow/configuration.py:859 FutureWarning: section/key [core/sql_alchemy_conn] has been deprecated, you should use[database/sql_alchemy_conn] instead. Please update your conf.get* call to use the new name
[2025-12-14T07:00:12.395+0000] {dagbag.py:588} INFO - Filling up the DagBag from /opt/airflow/dags/raw_to_conformed_ohlcv_csv_to_parquet.py
[2025-12-14T07:00:13.040+0000] {task_command.py:467} INFO - Running <TaskInstance: raw_to_conformed_ohlcv_csv_to_parquet.convert_new_raw_csvs_to_parquet scheduled__2025-12-14T06:55:00+00:00 [queued]> on host 41d6495e6efb
[2025-12-14T07:00:14.675+0000] {sequential_executor.py:84} INFO - Executing command: ['airflow', 'tasks', 'run', 'conformed_to_curated_copy', 'copy_new_conformed_objects', 'scheduled__2025-12-14T06:59:00+00:00', '--local', '--subdir', 'DAGS_FOLDER/conformed_to_curated_copy.py']
ChatGPT said:
This log excerpt is very helpful. It confirms:

The scheduler is running and executing tasks (including your two new DAGs).

There is no evidence in this excerpt that the webserver ever started.

The container is unhealthy because the healthcheck hits localhost:8080/health and gets “connection refused” (you already proved that).

So we are not dealing with “Airflow is down”; we are dealing with “webserver process never started (or started and immediately exited).”

What I infer from your logs
Your container logs show only scheduler activity (task execution) and none of the typical webserver startup lines (gunicorn/listening). That usually means the command: sequence is starting the scheduler, but not starting the webserver successfully.

Given your current command::

airflow users create ... 
airflow webserver & airflow scheduler
There are two common failure modes:

The airflow users create command fails (e.g., “user already exists”) and the webserver line never runs (depending on separators / shell parsing).

The webserver starts but exits immediately (most often due to a config/runtime error), while the scheduler continues.

Either way, the fix is the same: make the command block robust and ensure both processes start reliably.

The minimal fix you should apply
Replace your command: with this (exactly):

command: >
  bash -lc "
  set -e;
  airflow db migrate;
  airflow users create \
    --username minioadmin \
    --password minioadmin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com || true;
  airflow webserver &
  exec airflow scheduler
  "
Why this is the right minimal change:

|| true prevents “user already exists” from killing startup.

exec airflow scheduler keeps the container lifecycle correct.

Webserver is explicitly started every time.

Then restart:

docker compose down
docker compose up -d
And validate:

docker exec -it airflow bash -lc "curl -fsS http://localhost:8080/health"
If that returns JSON, the container will switch to healthy.

Confirm whether the yFinance ingestion DAG is actually running
Your excerpt shows raw_to_conformed_ohlcv_csv_to_parquet and conformed_to_curated_ohlcv_daily_snapshot being executed. It does not show raw_market_ohlcv_daily_asx (the Yahoo ingestion DAG). That could be because:

it is paused, or

it is scheduled later (every 5 minutes), or

it failed to parse and was not loaded.

Since your web UI is down, check via CLI:

docker exec -it airflow bash -lc "airflow dags list | egrep 'raw_market_ohlcv_daily_asx|raw_to_conformed_ohlcv_csv_to_parquet|conformed_to_curated_ohlcv_daily_snapshot'"
If raw_market_ohlcv_daily_asx is missing, the next check is imports:

docker exec -it airflow bash -lc "python -c 'import yfinance, pyarrow; print(\"imports_ok\")'"
Why I am not suggesting Alpine/apt here
You already have the critical evidence (connection refused on localhost:8080). Tools like ps would just confirm “webserver not running,” which we know. The correct next action is to fix the startup command so the webserver reliably launches.

Apply the command change and then re-test /health. If it still refuses, paste the first ~80 lines of docker logs airflow from immediately after restart (that is where gunicorn/webserver startup errors usually appear).




No file chosenNo file chosen
ChatGPT can make mistakes. Check important info.
