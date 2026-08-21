FROM dbeaver/cloudbeaver:latest

USER root
ADD https://repo1.maven.org/maven2/org/duckdb/duckdb_jdbc/1.4.3.0/duckdb_jdbc-1.4.3.0.jar /opt/cloudbeaver/drivers/duckdb_jdbc.jar
RUN chmod 644 /opt/cloudbeaver/drivers/duckdb_jdbc.jar
RUN mkdir -p /opt/cloudbeaver/workspace && chown -R 1000:1000 /opt/cloudbeaver/workspace
USER 1000
