{{/*
Find a Deployment Status Provisioner image in various places.
*/}}
{{- define "deployment-status-provisioner.image" -}}
    {{- printf "%s" .Values.statusProvisioner.dockerImage -}}
{{- end -}}
{{/*
Calculates resources that should be monitored during deployment by Deployment Status Provisioner.
*/}}
{{- define "airflow.monitoredResources" -}}
  {{- if and (ne (.Values.executor | toString) "KubernetesExecutor") (eq (.Values.config.logging.qs_logging_type | toString) "stdout") .Values.workers.replicas -}}
  {{- printf "Deployment %s-worker, " (include "airflow.fullname" .) -}}
  {{- end -}}
  {{- if and (ne (.Values.executor | toString) "KubernetesExecutor") (eq (.Values.config.logging.qs_logging_type | toString) "stdoutfilesystem") .Values.workers.replicas -}}
  {{- printf "StatefulSet %s-worker, " (include "airflow.fullname" .) -}}
  {{- end -}}
  {{- if .Values.scheduler.replicas }}
  {{- printf "Deployment %s-scheduler, " (include "airflow.fullname" .) -}}
  {{- end }}
  {{- if .Values.webserver.replicas }}
  {{- printf "Deployment %s-webserver, " (include "airflow.fullname" .) -}}
  {{- end }}
  {{- if and .Values.statsd.enabled .Values.scheduler.replicas .Values.webserver.replicas }}
  {{- printf "Deployment %s-statsd, " (include "airflow.fullname" .) -}}
  {{- end }}
  {{- if index .Values "airflow-site-manager" "enabled" }}
  {{- printf "Deployment %s-site-manager, " (include "airflow.fullname" .) -}}
  {{- end }}
  {{- if index .Values "integrationTests" "enabled" }}
  {{- printf "Deployment %s-integration-tests, " (include "airflow.fullname" .) -}}
  {{- end }}
{{- end -}}

{{/*
Additional Deployment only labels for Qubership Release
*/}}
{{- define "deployment_only_labels" -}}
name: {{ include "airflow.fullname" . }}
app.kubernetes.io/name: {{ include "airflow.fullname" . }}
app.kubernetes.io/instance: '{{ .Release.Name }}'
app.kubernetes.io/version: '{{ .Values.images.airflow.tag }}'
{{- end }}

{{- define "deployment_only_labels_worker" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-worker" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_worker_k8s" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-worker" }}
app.kubernetes.io/managed-by: 'airflow-kubernetes-executor'
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_cleanup_cronjob" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-cleanup-cronjob" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_dag_processor" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-dag-processor" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_flower" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "flower" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_create_user_job" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: '{{ .Values.componentLabel | default "airflow-create-user-job" }}'
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_migrate_database_job" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-create-user-job" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_preinstall_job" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-custom-preinstall-job" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_scheduler" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-scheduler" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_statsd" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-statsd" }}
app.kubernetes.io/technology: go
{{- end }}

{{- define "deployment_only_labels_status_provisioner" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-status-provisioner-job" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_triggerer" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-triggerer" }}
app.kubernetes.io/technology: python
{{- end }}

{{- define "deployment_only_labels_webserver" -}}
{{ include "deployment_only_labels" . }}
app.kubernetes.io/component: {{ .Values.componentLabel | default "airflow-webserver" }}
app.kubernetes.io/technology: python
{{- end }}

{{/*
Additional Service only labels for Qubership Release
*/}}
{{- define "service_only_labels" -}}
name: {{ include "airflow.fullname" . }}
app.kubernetes.io/name: {{ include "airflow.fullname" . }}
{{- end }}

{{/*
Custom Qubership Update strategy
*/}}
{{- define "qubership_update_strategy" -}}
  strategy:
    {{- if eq (default "" .Values.DEPLOYMENT_STRATEGY_TYPE) "recreate" }}
    type: Recreate
    {{- else if eq (default "" .Values.DEPLOYMENT_STRATEGY_TYPE) "best_effort_controlled_rollout" }}
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 0
      maxUnavailable: 80%
    {{- else if eq (default "" .Values.DEPLOYMENT_STRATEGY_TYPE) "ramped_slow_rollout" }}
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
    {{- else if eq (default "" .Values.DEPLOYMENT_STRATEGY_TYPE) "custom_rollout" }}
    type: RollingUpdate
    rollingUpdate:
      maxSurge: {{ .Values.DEPLOYMENT_STRATEGY_MAXSURGE | default "25%" }}
      maxUnavailable: {{ .Values.DEPLOYMENT_STRATEGY_MAXUNAVAILABLE | default "25%" }}
    {{- else }}
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%
      maxUnavailable: 25%
    {{- end }}
{{- end }}
