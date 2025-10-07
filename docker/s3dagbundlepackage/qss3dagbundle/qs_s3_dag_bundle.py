import subprocess

from airflow.providers.amazon.aws.bundles.s3 import S3DagBundle

checksum_command = 'find /tmp/airflow/dag_bundles -type f -name "*.yaml" -or -name "*.py" -or -name "*.json" -or -name "*.csv" -or -name "*.zip" -or -name "*.sql" | sort -u | xargs cat | md5sum'  # noqa: E501


class QSS3DAGBundle(S3DagBundle):
    supports_versioning = False
