FROM jupyter/minimal-notebook:latest

USER root
RUN pip install --no-cache-dir boto3 duckdb matplotlib minio pandas pyarrow
USER jovyan
