# RUNBOOK (MinIO + Airflow)

Copy/pasteable PowerShell steps to bring the stack up cleanly, verify MinIO buckets, and sanity-check Airflow DAGs. Commands were derived from `RUNBOOK.history`.

## 0) Prereqs
- Docker Desktop with Compose v2.
- Ports 9000/9001/8080 free.
- Run from repo root: `C:\Users\marek\Downloads\minio-test`.

## 1) Optional clean reset
```powershell
docker compose down -v
docker image rm apache/airflow:2.10.3-custom 2>$null   # force rebuild of custom image
Remove-Item -Recurse -Force .\logs 2>$null              # clear local logs
```

## 2) Prepare local mounts
```powershell
New-Item -ItemType Directory -Force -Path dags,logs,plugins | Out-Null
```

## 3) Build the Airflow image
```powershell
docker compose build airflow
```

## 4) Bring everything up
```powershell
docker compose up -d
docker ps --format '{{.Names}}: {{.Status}}' | sort
```

## 5) Check MinIO buckets
```powershell
docker compose exec -T minio mc ls local
docker compose exec -T minio mc ls -r local/raw | head -n 10
docker compose exec -T minio mc ls -r local/conformed | head -n 10
docker compose exec -T minio mc ls -r local/curated | head -n 10
```

## 6) Airflow sanity checks
```powershell
docker exec -it airflow airflow users list
docker exec -it airflow airflow dags list
```

## 7) Trigger and inspect a DAG (example: ASX OHLCV)
```powershell
docker exec -it airflow airflow dags trigger raw_market_ohlcv_daily_asx
Start-Sleep -Seconds 30
docker compose exec -T minio mc ls -r local/raw/tabular/market_ohlcv_daily | head -n 20
docker compose exec -T minio mc ls -r local/conformed/tabular/market_ohlcv_daily | head -n 20
docker compose exec -T minio mc ls -r local/curated/tabular/market_ohlcv_daily | head -n 20
```

## 8) Shutdown
```powershell
docker compose down --remove-orphans
```

If you need a full reset including volumes, rerun the clean reset step (down -v, remove image, remove logs) before the next start.
