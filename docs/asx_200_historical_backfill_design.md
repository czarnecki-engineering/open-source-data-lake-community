# ASX200 Historical OHLCV Backfill – Design Document

## 1. Purpose
This document defines the design for a **bulk historical data backfill pipeline** to ingest **5 years of daily OHLCV market data for current ASX 200 constituents**.

The pipeline is designed to:
- Align strictly with the **existing daily_ohlcv pipeline semantics**
- Minimise source throttling risk
- Preserve auditability and replay
- Avoid schema or operational divergence between backfill and daily ingestion

The backfill is **one-off but repeatable**, implemented as a dedicated Airflow DAG that can be disabled once completion is confirmed.

---

## 2. Scope and Constraints

### In Scope
- ASX 200 **current constituents only**
- Daily OHLCV data
- Rolling **5-year window** anchored to Airflow logical date
- Yahoo Finance as the data source

### Out of Scope
- Point-in-time ASX200 membership reconstruction
- Intraday data
- Corporate action recalculation (beyond vendor-provided adjustments)
- External redistribution or licensing compliance guarantees

---

## 3. Data Source

### Provider
- **Yahoo Finance** (unofficial, free source)

### Rationale
- Broad ASX200 coverage
- No authentication required
- Suitable for scripted bulk backfill
- Already used in the existing daily pipeline

### Data Characteristics
- OHLCV prices are **unadjusted (as traded)**
- `adj_close` is **provided by the source** and retained as a secondary field

---

## 4. Universe Definition (ASX 200)

- The ASX200 constituent list is **refreshed dynamically at runtime**
- Only **current constituents** are used for the entire 5-year backfill

### Persistence
- Each run persists a dated reference artifact:

```
raw/reference/asx200/constituents_snapshot_date=YYYY-MM-DD.csv
```

This enables audit, replay, and post-hoc inspection of universe composition.

---

## 5. Time Window Semantics

- Backfill window: **exactly 5 calendar years** prior to the Airflow logical date
- Anchor: `data_interval_end` (not wall-clock `now()`)
- Ensures deterministic behaviour across retries and re-runs

---

## 6. Pipeline Architecture

The pipeline follows the existing **three-layer lake model**:

```
Yahoo Finance
   ↓
raw/
   ↓
conformed/
   ↓
curated/
```

Only the **raw ingestion** is specialised for bulk backfill. Existing downstream DAGs are reused unchanged.

---

## 7. Raw Layer Design

### Storage Semantics
- **One object per (exchange, ticker, trade_date)**
- Format: CSV
- Partitioning: by `trade_date`

Example path:
```
raw/market_ohlcv_daily/exchange=ASX/trade_date=YYYY-MM-DD/ticker=BHP.csv
```

### Content
Each CSV contains a **single normalised row** with:
- `ticker`
- `trade_date`
- `open`, `high`, `low`, `close`
- `volume`
- `adj_close`

### Behaviour
- Objects are **overwritten** if they already exist (idempotent)
- Append-only by date (no historical rewrites once written)

---

## 8. Backfill Execution Strategy

### Call Pattern
- **One Yahoo Finance call per ticker** (entire 5-year window)
- Results are fanned out into daily raw objects

### Throttling and Stability
- **Explicit throttling enforced** (fixed pacing)
- Retries with backoff for transient failures

### Concurrency
- **Sequential execution** (one ticker at a time)
- Prioritises reliability over speed

---

## 9. Error Handling and Audit

### Failure Semantics
- Pipeline **continues on error**
- Per-ticker failures do not abort the entire run

### Audit Artifacts
Failures and warnings are persisted as structured artifacts:
```
raw/audit/errors/run_date=YYYY-MM-DD/errors.json
```

---

## 10. Conformed and Curated Layers

### Conformed
- **One Parquet file per (ticker, trade_date)**
- Schema matches existing daily pipeline exactly
- Lenient schema enforcement (coercion where possible)

### Curated
- Existing curated DAG reused unchanged
- No special backfill logic

---

## 11. Scheduling and Lifecycle

### Scheduling
- Backfill DAG is **temporarily scheduled**
- Runs repeatedly until completion criteria are met

### Completion Tracking
- **State-based tracking** persisted in object storage
- Per-ticker completion markers

Example:
```
raw/control/backfill_state.json
```

### Post-Completion
- DAG is **disabled**, not deleted
- Code retained for future re-runs or extensions

---

## 12. Design Principles

- Align with existing daily ingestion semantics
- Prefer idempotency over append-only payloads
- Optimise for reliability, not speed
- Preserve auditability at every stage
- Treat Yahoo Finance as an internal analytical source

---

## 13. Status

This design is **locked and approved** based on interactive decisioning.
No open decisions remain.

---

*Document intended for storage under `docs/` and version control alongside DAG code.*

