# ASX Historic Overlay Explanation

`overlay_asx_historic_csv` installs a simple tabular ingestion overlay for historic ASX source files available by URL.

The overlay keeps the established Community Edition pattern intact:

- the base stack remains generic
- overlay-specific runtime behavior is activated through overlay compose files and wrappers
- the PHP solution page is controlled through a solution tag

## Runtime Shape

The runtime flow is:

1. `asx_urls_to_raw.py`
2. `raw_to_conformed.py`
3. `conformed_to_curated.py`

The Airflow DAG `dag_asx_historic_csv` runs the same sequence.

## Source Model

This overlay is intentionally narrow:

- source type: `http` or `https`
- file types: `.csv`, `.xlsx`, and `.xls`
- job config may include multiple `source_urls`

The conformed step is generic for simple tabular inputs:

- `read_csv` for CSV
- `read_excel` with `openpyxl` for `.xlsx`
- `read_excel` with `xlrd` for legacy `.xls`
- single-sheet workbooks are auto-detected
- multi-sheet workbooks require `source_options.sheet_name`

## Output Model

- raw files are stored in MinIO bucket `raw`
- conformed Parquet is stored in MinIO bucket `conformed`
- curated JSON summaries are stored in MinIO bucket `curated`
- curated JSON is mirrored locally under `data/curated/asx/historic/...`

The PHP solution page reads only the mirrored curated JSON.

## PHP UI Contract

The page `php/solutions/asx_historic_summary.php` uses:

```text
Solution Tag: asx-historic-csv
```

That means:

- direct URL access works when the file exists
- listing through `php/solutions.php` only works when the PHP container has:

```text
ENABLED_SOLUTION_TAGS=asx-historic-csv
```

This variable is injected by the overlay compose files, which is why overlay startup must go through the overlay wrapper.
