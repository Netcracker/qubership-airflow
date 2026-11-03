{{/*
Namespace of the dbaas-operator instance that manages the resources. The value is templated.
*/}}
{{- define "airflow.dbaas.operatorNamespace" -}}
{{- tpl .Values.dbaasDeclarative.operatorNamespace . -}}
{{- end -}}
{{/*
Name of the Secret that the dbaas-operator fills with the PostgreSQL connection properties of Airflow.
*/}}
{{- define "airflow.dbaas.pgSecretName" -}}
{{- default (printf "%s-dbaas-postgresql" (include "airflow.fullname" .)) .Values.dbaasDeclarative.postgresql.secretName -}}
{{- end -}}
{{/*
Name of the Secret that the dbaas-operator fills with the Redis connection properties of Airflow.
*/}}
{{- define "airflow.dbaas.redisSecretName" -}}
{{- default (printf "%s-dbaas-redis" (include "airflow.fullname" .)) .Values.dbaasDeclarative.redis.secretName -}}
{{- end -}}
{{/*
Renders an InternalDatabase and a DatabaseSecretClaim for one database.
Expects a dict with: ctx (root context), name, type, classifier, secretName, and optionally namePrefix, settings and existing.
When existing is true, the database is owned by another service: only the DatabaseSecretClaim is rendered and its
app.kubernetes.io/name label is dbaasDeclarative.serviceName, which the owner grants access to with a DatabaseAccessPolicy.
Classifier keys other than microserviceName, scope, namespace, tenantId and customKeys become classifier.extraKeys.
*/}}
{{- define "airflow.dbaas.database" -}}
{{- $ctx := .ctx -}}
{{- $c := .classifier -}}
{{- $classifier := dict "microserviceName" $c.microserviceName "scope" ($c.scope | default "service") "namespace" ($c.namespace | default $ctx.Release.Namespace) -}}
{{- if $c.tenantId }}{{- $_ := set $classifier "tenantId" $c.tenantId -}}{{- end -}}
{{- if $c.customKeys }}{{- $_ := set $classifier "customKeys" $c.customKeys -}}{{- end -}}
{{- $extraKeys := omit $c "microserviceName" "scope" "namespace" "tenantId" "customKeys" -}}
{{- if $extraKeys }}{{- $_ := set $classifier "extraKeys" $extraKeys -}}{{- end }}
{{- if not .existing }}
---
apiVersion: dbaas.netcracker.com/v1
kind: InternalDatabase
metadata:
  name: {{ .name }}
  namespace: {{ $ctx.Release.Namespace }}
  labels:
    release: {{ $ctx.Release.Name }}
spec:
  operatorNamespace: {{ include "airflow.dbaas.operatorNamespace" $ctx | quote }}
  classifier: {{- toYaml $classifier | nindent 4 }}
  type: {{ .type }}
  {{- with .namePrefix }}
  namePrefix: {{ . | quote }}
  {{- end }}
  {{- with .settings }}
  settings: {{- toYaml . | nindent 4 }}
  {{- end }}
{{- end }}
---
apiVersion: dbaas.netcracker.com/v1
kind: DatabaseSecretClaim
metadata:
  name: {{ .name }}
  namespace: {{ $ctx.Release.Namespace }}
  labels:
    release: {{ $ctx.Release.Name }}
    app.kubernetes.io/name: {{ ternary $ctx.Values.dbaasDeclarative.serviceName $c.microserviceName (default false .existing) | quote }}
spec:
  operatorNamespace: {{ include "airflow.dbaas.operatorNamespace" $ctx | quote }}
  classifier: {{- toYaml $classifier | nindent 4 }}
  type: {{ .type }}
  secretName: {{ .secretName }}
{{- end -}}
