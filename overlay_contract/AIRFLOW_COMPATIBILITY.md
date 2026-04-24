# Airflow Compatibility

The supported stack exposes Airflow compatibility for overlays through a logical `airflow` service contract.

Allowed logical `airflow` keys in v1:

- `build`
- `image`
- `environment`
- `env_file`
- `volumes`
- `labels`
- `pull_policy`

Unsupported logical `airflow` keys in v1 include:

- `command`
- `ports`
- `depends_on`

Rules:

- target logical service `airflow` only
- do not reference `airflow-webserver`
- do not reference `airflow-scheduler`
- do not reference `airflow-user-init`

Reason:

The root wrapper compatibility layer copies only the supported keys from logical `airflow` onto the supported stack's internal Airflow services.
