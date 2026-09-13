FROM jupyter/minimal-notebook:latest

USER root
RUN pip install --no-cache-dir \
    boto3==1.37.38 \
    duckdb \
    matplotlib \
    minio \
    pandas \
    pyarrow \
    scipy \
    yfinance
USER jovyan
