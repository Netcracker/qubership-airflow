{{/*
Find a integrationTests image in various places.
*/}}
{{- define "integrationTests.image" -}}
  {{ printf "%s" (.Values.image) }}
{{- end }}

{{- define "airflow.imagesToTest" -}}
  {{- printf "No images by default" -}}
{{- end }}

{{/*
Additional Service only labels for Qubership Release
*/}}
{{- define "service_only_labels" -}}
name: {{ include "airflow.fullname" . }}
app.kubernetes.io/name: {{ include "airflow.fullname" . }}
{{- end }}