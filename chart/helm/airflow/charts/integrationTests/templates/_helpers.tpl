{{/*
Find a integrationTests image in various places.
*/}}
{{- define "integrationTests.image" -}}
  {{ printf "%s" (.Values.image) }}
{{- end }}

{{- define "airflow.imagesToTest" -}}
  {{- printf "No images by default" -}}
{{- end }}
