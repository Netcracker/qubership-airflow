import subprocess

from airflow.providers.amazon.aws.bundles.s3 import S3DagBundle

checksum_command = 'find /tmp/airflow/dag_bundles -type f -name "*.yaml" -or -name "*.py" -or -name "*.json" -or -name "*.csv" -or -name "*.zip" -or -name "*.sql" | sort -u | xargs cat | md5sum'  # noqa: E501


class QSS3DAGBundle(S3DagBundle):
    supports_versioning = True

    def get_current_version(self) -> str | None:
        checksum = subprocess.run(
            checksum_command, shell=True, capture_output=True, text=True, check=True
        )
        return checksum.stdout

    def view_url_template(self) -> str | None:
        if hasattr(self, "_view_url_template") and self._view_url_template:
            # Because we use this method in the view_url method, we need to handle
            # backward compatibility for Airflow versions that doesn't have the
            # _view_url_template attribute. Should be removed when we drop support for Airflow 3.0
            return self._view_url_template
        # https://<bucket-name>.s3.<region>.amazonaws.com/<object-key>
        url = f"https://{self.bucket_name}.s3"
        if self.s3_hook.region_name:
            url += f".{self.s3_hook.region_name}"
        url += ".amazonaws.com"
        if self.prefix:
            url += f"/{self.prefix}"

        return url
