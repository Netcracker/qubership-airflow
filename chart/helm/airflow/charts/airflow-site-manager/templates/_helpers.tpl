{{/*
Expand the name of the chart.
*/}}
{{- define "airflow-site-manager.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "airflow-site-manager.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "airflow-site-manager.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "airflow-site-manager.labels" -}}
{{- with .Values.labels }}
{{- toYaml . }}
{{- end }}
helm.sh/chart: {{ include "airflow-site-manager.chart" . }}
app.kubernetes.io/component: airflow-site-manager
name: {{ include "airflow-site-manager.name" . }}
{{ include "airflow-site-manager.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "airflow-site-manager.selectorLabels" -}}
app.kubernetes.io/name: {{ include "airflow-site-manager.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "airflow-site-manager.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "airflow-site-manager.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{ define "airflow_site_manager_image" -}}
{{ printf "%s:%s" (.Values.image.repository) (.Values.image.tag) }}
{{- end }}


{{/*
Service Account for Site Manager depending on smSecureAuth
*/}}
{{- define "disasterRecovery.siteManagerServiceAccount" -}}
  {{- if .Values.SITE_MANAGER_SERVICE_ACCOUNT_NAME -}}
    {{- .Values.SITE_MANAGER_SERVICE_ACCOUNT_NAME -}}
  {{- else -}}
    {{- if .Values.SM_SECURE_AUTH -}}
      {{- "site-manager-sa" -}}
    {{- else -}}
      {{- "sm-auth-sa" -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
