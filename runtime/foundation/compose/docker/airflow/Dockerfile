FROM apache/airflow:2.10.5

USER airflow
# pyarrow pinned explicitly (was bare `pyarrow`, which numpy<2 forced pip to
# resolve down to 19.0.0 — the latest release still compatible with
# numpy<2). pyarrow 19.0.0 has a real read bug: OSError "Repetition level
# histogram size mismatch" when reading certain Parquet files with
# dictionary-encoded columns and page-index/SizeStatistics metadata (as
# written by newer pyarrow/pandas writers) — reproduced live 2026-08-21
# reading a public GitHub-hosted Parquet file for the asx_ohlcv community
# solution. jupyter's Dockerfile has no numpy pin and resolved pyarrow to
# 25.0.0, which reads the same file correctly — confirming this is a
# pyarrow-version bug, not a bad file. 25.0.0 has no pip-level numpy
# requirement (`pip show pyarrow` reports none) and was live-verified
# compatible with the numpy<2 already pinned here: reading the same file,
# .to_pandas()/pa.Table.from_pandas() round-tripping, and — critically —
# a read-only pyiceberg scan().to_arrow() against both existing production
# Iceberg tables (demo.heartbeat_events, demo.asx_ohlcv_summary) all
# succeeded before this was committed.
RUN pip install --no-cache-dir \
    boto3==1.37.38 \
    "numpy<2" \
    "pandas==2.1.4" \
    pyarrow==25.0.0 \
    pyiceberg==0.7.1 \
    yfinance
