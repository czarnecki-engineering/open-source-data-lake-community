# Article Outline: Building `overlay_asx_historic_csv`

This document is a detailed article brief and outline for explaining the design, implementation, testing, and packaging of `overlay_asx_historic_csv`.

It is written to support either:

- drafting a long-form article directly from this outline
- supplying structured context to ChatGPT or another writing assistant

## Recommended Location

This file lives under:

- `overlay_asx_historic_csv/docs/article_outline.md`

That is the right location because the content is about a specific distributable overlay, not about internal repo governance in general.

If a future article becomes a broader platform narrative across multiple overlays, a separate repo-level note under `docs/internal/` would make sense. For this piece, the overlay docs are the better home.

## Article Purpose

The article should explain how a reusable overlay pattern was taken from an earlier Kaggle-based ingestion overlay and applied to a second, materially different source system: historic ASX tabular files available over HTTP/HTTPS.

The article should show:

- how the overlay pattern works
- why packaging mattered
- what had to remain generic in the base platform
- what stayed overlay-specific
- what changed during real testing
- what was learned from schema drift across multiple historic files

This should not read like a marketing launch note. It should read like an engineering delivery narrative with concrete constraints, runtime proof, and design tradeoffs.

## Intended Audience

The likely readers are:

- engineers evaluating the Open Data Lake Community Edition overlay model
- maintainers who want to understand the packaging contract
- practitioners building URL-based tabular ingestion overlays
- readers interested in practical medallion-style pipelines over simple public datasets

The audience is technical. The article should not over-explain basic Git, Docker, Airflow, MinIO, pandas, or notebook concepts.

## Core Thesis

The core thesis of the article can be stated as:

> A reusable overlay packaging pattern can support multiple source systems without redesigning the platform each time, as long as the boundary between generic runtime behavior and overlay-specific behavior is kept explicit and rigorously tested.

An alternative wording:

> The second overlay validated that the Community Edition could accept a new ingestion source family by instantiating an existing overlay template rather than inventing a new architecture.

## Source Material To Supply With This Outline

If using ChatGPT to draft the article, provide:

1. `overlay_asx_historic_csv/docs/overlay_2_asx_historic_csv_prompt.md`
2. `overlay_asx_historic_csv/overlay_asx_historic_csv/README.md`
3. `overlay_asx_historic_csv/overlay_asx_historic_csv/RUNBOOK.md`
4. this file: `overlay_asx_historic_csv/docs/article_outline.md`

That set gives:

- the original contract
- the installation and packaging details
- the validated runtime path
- the delivery narrative and design decisions

## Suggested Title Options

Use one of these depending on tone.

### Direct engineering title

- `Building a Packaged ASX Historic Data Overlay for the Open Data Lake Community Edition`

### Pattern-oriented title

- `From Template to Working Overlay: Historic ASX URL Ingestion in the Open Data Lake Community Edition`

### Delivery-oriented title

- `How We Turned a Reusable Overlay Pattern into a Working ASX Historic Ingestion Stack`

### Platform-oriented title

- `Validating the Overlay Model with Historic ASX Tabular Ingestion`

## Suggested Subtitle Options

- `A practical engineering walkthrough of packaging, DAG execution, notebook validation, PHP rendering, and clean-install testing`
- `Reusing an existing overlay architecture to ingest URL-based historic ASX files into MinIO-backed medallion layers`

## Recommended Structure

The article should follow this arc:

1. establish the platform and prior overlay context
2. define the ASX overlay objective and constraints
3. explain the overlay pattern that was reused
4. walk through the runtime components
5. describe what changed during real testing
6. show how packaging and clean-install validation were proven
7. close with what this says about the platform and what remains to improve

## Detailed Section Outline

### 1. Introduction

Open with the problem:

- a first reusable overlay already existed for Kaggle ingestion
- the next test was whether the same packaging and runtime model could support a different source class
- the new source class was historic ASX tabular files published as downloadable files over HTTP/HTTPS

State the goal clearly:

- build a new overlay without redesigning the architecture
- preserve the established root-runtime plus packaged-overlay model
- prove that the overlay could be installed by unzipping an archive into the root of a clean Community Edition checkout

Important framing:

- the work was not to build “an ASX app”
- it was to validate the overlay model against a second ingestion pattern

### 2. Starting Constraints

Describe the initial delivery contract.

Key constraints:

- work on branch `feature/overlay-asx_historic_csv`
- start from the proven overlay template branch
- also follow the successful Kaggle overlay pattern
- do not invent a second overlay architecture
- keep overlay-specific logic out of `main` unless a change was truly generic

Explain why those constraints matter:

- they prevent architecture drift
- they force reuse of packaging conventions
- they make the second overlay a real test of the platform pattern rather than a one-off project

### 3. The Overlay Pattern Being Reused

Explain the model that was carried over.

The pattern had two layers:

1. root runtime files installed into the Community Edition checkout
2. packaged overlay wrappers and compose overrides under `overlay_asx_historic_csv/`

Explain the reasoning:

- root runtime paths are where Airflow, notebooks, scripts, config, and PHP already operate
- packaged overlay files are the installable distribution artifact and runtime entry point
- this allows a zip archive to be unzipped directly into a clean checkout with no manual copy phase

Use a short example of the split:

- root:
  - `config/`
  - `scripts/`
  - `dags/`
  - `notebooks/`
  - `php/solutions/`
- packaged:
  - overlay compose file
  - start/stop wrappers
  - packaged Dockerfiles
  - packaged docs

### 4. What the Overlay Needed to Do

State the required data flow.

The overlay needed to:

- load a JSON job config
- download one or more tabular files from URL sources
- store them in MinIO bucket `raw`
- transform them to Parquet in MinIO bucket `conformed`
- compute curated JSON summaries in MinIO bucket `curated`
- mirror curated JSON locally under `data/curated/...` for PHP
- provide an Airflow DAG, a notebook, and a PHP page

Call out the initial source assumption:

- the starting contract assumed CSV

Then explain the important real-world change:

- actual testing immediately showed that the provided source was `.xlsx`, not `.csv`
- later test files included `.xls` as well

This is one of the article’s most useful examples of why real source testing matters.

### 5. Runtime Components

Walk through the implemented components one by one.

#### 5.1 Config

Files:

- `config/asx_historic_jobs.example.json`
- `config/asx_historic_jobs.test.json`
- `config/asx_historic_jobs.marketindex_2016_2024.test.json`

Explain the config model:

- `name`
- `enabled`
- `source_urls`
- `raw_target`
- `conformed_target`
- `curated_target`
- optional `source_options`

Explain why `source_options` remained optional:

- simple one-sheet workbooks should just work
- sheet names or header offsets are only needed for more complex cases

#### 5.2 Shared Helper

File:

- `scripts/asx_overlay_common.py`

Responsibilities:

- config loading
- environment loading
- job normalization
- MinIO client setup
- object-key helpers
- curated mirror path resolution
- source type detection

Call out one important widening:

- source detection expanded from `.csv` to `.xlsx`, then to `.xls`

#### 5.3 Ingestion

File:

- `scripts/asx_urls_to_raw.py`

Explain what it does:

- reads enabled jobs
- downloads configured URLs
- validates non-empty content
- validates supported tabular types
- uploads objects into `raw`
- emits JSON summaries

Key design point:

- ASX-specific in naming and config contract
- otherwise simple URL-based tabular ingestion logic

#### 5.4 Conformed Transform

File:

- `scripts/raw_to_conformed.py`

Explain the logic:

- read raw objects from MinIO
- detect source type from object key
- load with pandas
- standardize column names to lowercase snake_case
- add lineage fields
- write Parquet to `conformed`

Explain the format handling:

- `.csv` via `pandas.read_csv`
- `.xlsx` via `pandas.read_excel(..., engine="openpyxl")`
- `.xls` via `pandas.read_excel(..., engine="xlrd")`

Explain the typing choice carefully:

- useful numeric and datetime types should be preserved where possible
- mixed identifier-like columns should be normalized to string before Parquet write
- this prevented pyarrow-style failures on mixed-type identifier columns such as `asx_code`

Also explain the current limitation:

- cross-year files do not share a fully stable schema
- some years still land with string-heavy conformed data because header names and data formats differ across source vintages

#### 5.5 Curated Summary

File:

- `scripts/conformed_to_curated.py`

Explain what the curated step computes:

- row count
- column list
- dtypes
- null counts
- numeric stats

Explain the output contract:

- source of truth written to MinIO bucket `curated`
- deterministic local mirror under `data/curated/...` for PHP

#### 5.6 DAG

File:

- `dags/dag_asx_historic_csv.py`

Explain that the DAG is intentionally simple:

1. `asx_urls_to_raw`
2. `raw_to_conformed`
3. `conformed_to_curated`

Why that matters:

- it proves the scripts run correctly inside the stack
- it keeps orchestration complexity low while validating the runtime contract

#### 5.7 Notebook

File:

- `notebooks/asx_historic_connectivity_and_eda.ipynb`

Explain the notebook purpose:

- validate connectivity
- inspect objects in MinIO
- load raw, conformed, and curated artifacts
- perform lightweight EDA

Mention the EDA content explicitly:

- shape
- head
- null counts
- univariate distributions
- bivariate views
- date spread
- missing-date investigation
- row frequency by `asx_code`

#### 5.8 PHP Page

File:

- `php/solutions/asx_historic_summary.php`

Explain what the page does:

- reads curated JSON only
- does not perform analytics
- renders discovered summary files from deterministic mirrored paths

Call out the solution-tag discovery contract:

- direct page URL works when the file exists
- `solutions.php` only lists the page when `ENABLED_SOLUTION_TAGS=asx-historic-csv`

This became an important runtime debugging moment.

### 6. The First Real Source Test Changed the Contract

This is a strong article section because it shows real engineering adaptation.

Explain the sequence:

- the first provided real source URL was expected to behave like a CSV source
- the actual file was an Excel workbook
- the ingestion script correctly rejected it under the original contract
- the contract was then widened to accept simple tabular sources rather than CSV only

Key point:

- the overlay architecture did not change
- only the source-type contract widened within the existing ingestion and conformed stages

Then explain the second widening:

- later real historic files included legacy `.xls`
- support was added with `xlrd`
- Dockerfiles were updated so stack execution matched host-side expectations

This is a good place to emphasize:

- this was still the same overlay
- it did not become a generic “any file ingestion” subsystem

### 7. Validation with Real Market Index Files

Describe the real dataset family used for testing.

Files tested:

- `2025`: `.xlsx`
- `2024`: `.xlsx`
- `2023`: `.xlsx`
- `2022`: `.xlsx`
- `2021`: `.xlsx`
- `2020`: `.csv`
- `2019`: `.xls`
- `2018`: `.xls`
- `2017`: `.xls`
- `2016`: `.xls`

Explain why this batch was valuable:

- it covered three file families
- it exposed schema variation across years
- it proved the overlay on more than a single happy-path file

Include the row counts from validated curated outputs:

- `2016`: `6035`
- `2017`: `5535`
- `2018`: `5700`
- `2019`: `5912`
- `2020`: `2271`
- `2021`: `5481`
- `2022`: `5265`
- `2023`: `5005`
- `2024`: `4712`
- `2025`: `4709`

Then explain the schema drift findings:

- `2024` and `2025` were closest to the current canonical expectations
- `2023` and `2016` were similar but not identical
- `2021`, `2022`, `2017`, `2018`, and `2019` used alternate header names
- `2020` was materially different and only exposed a small set of columns

This is one of the article’s strongest lessons:

- a pipeline can be operational across many files without yet being semantically canonical across all vintages

### 8. The Missing-Date Investigation

This deserves a dedicated section because it is both analytically interesting and a good example of how the notebook adds value beyond “pipeline passed”.

Describe the original question:

- why are there so many rows with no `business_date`?

Summarize the validated 2025 findings:

- `1092` rows had missing `business_date`
- all `1092` also had missing `last_price`
- `0` rows had missing `business_date` with present `last_price`

Interpretation:

- this looked like source semantics rather than a transform bug
- those rows appeared to represent listings or instruments without an active dated market value in that snapshot

Also note the concentration:

- missingness clustered heavily in certain groups, especially warrants and related instruments

This section is useful because it shows:

- the notebook was not decorative
- it surfaced an interpretable data quality pattern

### 9. Generic Platform Changes vs Overlay-Specific Changes

This is a key architectural section.

Explain the principle:

- generic improvements may be promoted into `main`
- overlay-specific behavior must remain in overlay files

Generic changes promoted to the base platform:

- `docker-compose.yaml` generic mounts for `scripts/`, `config/`, and `data`
- base Airflow Dockerfile support for tabular Excel dependencies
- base Jupyter Dockerfile support for the same

Overlay-specific behavior kept out of base:

- overlay compose files
- overlay wrapper scripts
- `ENABLED_SOLUTION_TAGS=asx-historic-csv`
- packaged overlay docs and Dockerfiles
- ASX-specific scripts and config

This section should make the architecture boundary explicit. That is one of the central lessons of the work.

### 10. Packaging and Install Validation

This section should explain why packaging was treated as a first-class engineering requirement, not an afterthought.

Describe the packaging contract:

- archive built from the contents of `overlay_asx_historic_csv/`
- unzip directly into the root of a clean Community Edition checkout
- no post-unzip copy step

Explain how it was validated:

- stop running services
- build `overlay_asx_historic_csv_v1.0.zip`
- create a clean `main`-based checkout
- unzip archive into that checkout root
- create real config
- run packaged start wrapper
- validate DAG, notebook, PHP, and MinIO objects

Call out the important implementation detail:

- documentation files were moved so they install under `overlay_asx_historic_csv/` after unzip rather than landing at repo root

Explain why that matters:

- packaged documentation should travel with the overlay
- it should not overwrite or masquerade as top-level repository docs

### 11. Development Wrappers vs Packaged Wrappers

This is worth a short dedicated explanation because it is easy for readers to miss.

Development used:

- `bash overlay_asx_historic_csv/dev-start-compose.sh`
- `bash overlay_asx_historic_csv/dev-stop-compose.sh`

Packaged installs use:

- `bash overlay_asx_historic_csv/start-compose.sh`
- `bash overlay_asx_historic_csv/stop-compose.sh`

Explain why both exist:

- source-tree development paths are not identical to installed packaged paths
- dev wrappers let the branch work naturally before packaging
- packaged wrappers are the runtime contract after unzip into a clean checkout

### 12. What Was Proven

This section should be explicit and concrete.

The work proved:

- the reusable overlay pattern can support a second source class without redesign
- URL-based tabular ingestion works against MinIO-backed medallion layers
- the stack can run the overlay end to end through Airflow
- notebook validation and lightweight EDA fit naturally into the same model
- PHP presentation can remain curated-only and still integrate into the platform
- packaging into a distributable overlay zip is viable and testable

Also state what was not yet fully solved:

- historical schema canonicalization across all years is still incomplete
- older files still land with string-heavy conformed output in several cases
- a stronger canonical mapping layer would improve cross-year comparability

That balance matters. The article should not claim more than the implementation actually achieved.

### 13. Future Improvements

End with practical next steps rather than vague aspirations.

Reasonable future work:

- add canonical header mapping across historic vintages
- normalize known aliases such as `security_group` vs `security_group_code`
- improve date and numeric coercion for older years
- expand notebook comparisons across years
- build a richer PHP cross-file summary if curated outputs become more canonical
- generalize only the platform improvements that have clearly proven reusable value

## Key Facts To Preserve Accurately

These are facts that should remain precise in the article.

### Branches

- working branch: `feature/overlay-asx_historic_csv`
- template reference: `feature/overlay-template`
- prior proven source example: `origin/feature/overlay-kaggle_ingestion`

### Overlay Name

- `overlay_asx_historic_csv`

### Runtime Stages

- `asx_urls_to_raw.py`
- `raw_to_conformed.py`
- `conformed_to_curated.py`

### DAG

- `dag_asx_historic_csv`

### Buckets

- `raw`
- `conformed`
- `curated`

### PHP Tag

- `asx-historic-csv`

### Packaged Archive

- `overlay_asx_historic_csv_v1.0.zip`

## Recommended Screenshots

If the article includes visuals, these are the best candidates.

1. Airflow DAG graph or task success view
2. MinIO bucket view showing `raw`, `conformed`, `curated`
3. notebook screenshot showing EDA outputs
4. PHP `solutions.php` showing the ASX page listed
5. PHP `asx_historic_summary.php` page rendering a curated artifact

Avoid screenshots that are too generic, such as a bare container list or an empty homepage.

## Recommended Tone

The tone should be:

- technical
- direct
- evidence-based
- reflective without being self-congratulatory

Avoid:

- launch language
- exaggerated claims about generality
- vague references to “AI-powered” or “modern data platform” themes

## Suggested Article Length

Target:

- 1,500 to 2,500 words for a blog article
- 2,500 to 4,000 words for a more detailed engineering write-up

The shorter version should compress the section-level detail but preserve:

- the overlay pattern
- the real testing changes
- the packaging proof
- the schema drift lesson

## Example Opening Paragraph

You may use or adapt this.

> After validating a first installable ingestion overlay for Kaggle datasets, the next question was whether the same packaging and runtime pattern could support a different source family without drifting into a second architecture. The test case was historic ASX tabular data published as downloadable files over HTTP. The goal was not just to ingest the files, but to prove that the Open Data Lake Community Edition could accept a second overlay, run it end to end through MinIO-backed medallion layers, expose it in Airflow, inspect it in Jupyter, render it in PHP, and package the whole result as a clean unzip-into-root installation.

## Example Closing Paragraph

You may use or adapt this.

> The value of the ASX overlay is not just that it ingests another dataset. Its real value is that it validates the overlay model under a second source pattern, with real packaging, real runtime execution, and real source variation across multiple years. The remaining work is mostly semantic rather than architectural: the platform pattern held, the packaging contract held, and the next improvements are about better canonicalization of historical schema drift rather than inventing a new deployment model.

## Short Prompt To Pair With This Outline

If you want to feed this into ChatGPT, use something like:

> Write a technical engineering article based on the attached outline, prompt, README, and RUNBOOK. Focus on how `overlay_asx_historic_csv` reused the established overlay pattern from the earlier Kaggle overlay, how the source contract widened during real testing from CSV to XLSX and XLS, how the pipeline was validated end to end through Airflow, MinIO, Jupyter, and PHP, and what was learned from schema drift across multiple historic ASX files. Keep the tone practical and evidence-based, not promotional.
