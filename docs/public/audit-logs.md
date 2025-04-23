Auditing helps to maintain and secure the logs of critical activities in an Airflow service environment.

Topics covered in this section:

* [Audit Logs](#audit-logs)
* [Example of Audit Logs](#example-of-audit-logs)
* [Audit Logs Formatting](#audit-logs-formatting)
* [Audit Logs Configuration](#audit-logs-configuration)
* [Audit in Airflow Web UI](#audit-in-airflow-web-ui)

# Audit Logs

Airflow logs the following audit events:
- Successful login(only Kerberos)
- Failed login
- User profiles updates such as when the user resets password or updates the first or last name

# Example of Audit Logs

When using Qubership Airflow logging configuration, audit logs contain the '[AUDIT]' string.

```
[2021-05-24 10:33:32,996] {manager.py:230} INFO - [AUDIT] Updated user admin admin
[2021-05-24 09:58:05,091] {manager.py:769} INFO - [AUDIT] Login Failed for user: admin
```

# Audit Logs Formatting

By default, Airflow logs audit events. To distinguish the logs, the following has been added to [QS_DEFAULT_LOGGING_CONFIG](../../chart/helm/airflow/qs_files/qs_platform_logging_config.py):

* Audit log formatter to add '[AUDIT]' to audit logs
* Audit log handler
* Loggers for modules that logs audit events

```
QS_DEFAULT_LOGGING_CONFIG = {
    ...
    'formatters': {
        'airflow-audit': {
            'format': LOG_FORMAT_AUDIT
        }
        ...
    },
    'handlers': {
        'audit': {
            'class': 'airflow.utils.log.logging_mixin.RedirectStdHandler',
            'formatter': 'airflow-audit',
            'stream': 'sys.stdout'
        }
        ...
    },
    'loggers': {
        ...
        'flask_appbuilder.security.sqla.manager': {
            'handlers': ['audit'],
            'level': AUDIT_LOG_LEVEL,
            'propagate': False,
        },
        'flask_appbuilder.security.manager': {
            'handlers': ['audit'],
            'level': AUDIT_LOG_LEVEL,
            'propagate': False,
        },
        'airflow.security.kerberos': {
            'handlers': ['audit'],
            'level': AUDIT_LOG_LEVEL,
            'propagate': False,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    }
}  # type: Dict[str, Any]
```

# Audit Logs Configuration

Airflow and Graylog should be configured:

* To apply audit log formatting, set the following helm chart parameters:

```yaml
...
config:
...
  logging:
...
    logging_config_class: airflow_local_settings.QS_DEFAULT_LOGGING_CONFIG
...
airflowLocalSettings:  |-
    {{ .Files.Get "qs_files/qs_platform_logging_config.py" }}
...
```

  For more information, see [Enabling Custom Logging Configurations](installation.md#enabling-custom-logging-configurations).
* Set `config.logging.audit_log_level`. It should at least be set to its default value of 'INFO', else some audit logs are lost. 
* Configure Graylog rules for Audit Logs stream to filter messages that contain '[AUDIT]'

In case of Qubership Graylog:

1. Log in to Graylog.
1. Navigate to **System > Pipelines**.
1. Click **Manage rules** on **Pipelines overview** panel.
1. Edit the 'Route Audit logs' rule to filer messages with `[AUDIT]`
    
```
rule "Route Audit logs"
when
(to_bool(regex(pattern: "PG_SERVICE|access-control|database system is|audit_log_type|logType\": \t]*audit|com.qubership.security.audit.*CEF|AUDIT", value: to_string($message.message)).matches) OR
to_bool(regex(pattern: "logType[\": \t]*audit", value: to_string($message.log)).matches) OR
to_bool(regex(pattern: "^parsed.var.log.audit.audit.log$", value: to_string($message.tag)).matches) OR
to_bool(regex(pattern: "^parsed.var.log.ocp-audit.log$", value: to_string($message.tag)).matches) OR
to_bool(regex(pattern: "^parsed.var.log.kube-apiserver.audit.log$", value: to_string($message.tag)).matches) OR
to_bool(regex(pattern: "^parsed.var.log.openshift-apiserver.audit.log.log$", value: to_string($message.tag)).matches) OR
to_bool(regex(pattern: "^parsed.var.log.kubernetes.kube-apiserver-audit.log$", value: to_string($message.tag)).matches) OR
to_bool(regex(pattern: "^parsed.var.log.kubernetes.audit.log$", value: to_string($message.tag)).matches) OR
(has_field("container_name") AND to_bool(regex(pattern: "graylog_web_1|graylog_graylog_1|graylog_mongo_1|graylog_elasticsearch_1", value: to_string($message.container_name)).matches)) OR
(has_field("kubernetes") AND to_bool(regex(pattern: "mongo-cluster", value: to_string($message.kubernetes)).matches) AND to_bool(regex(pattern: "ACCESS|CONTROL", value: to_string($message.message)).matches)) OR
(has_field("container_name") AND to_bool(regex(pattern: "grafana", value: to_string($message.container_name)).matches) AND
to_bool(regex(pattern: "Invalid username or password|Successful Login|Successful Logout|Failed to look up user based on cookie", value: to_string($message.message)).matches))
)
AND NOT
(to_bool(regex(pattern: "parsed.var.log.messages|systemd", value: to_string($message.tag)).matches))
then
route_to_stream(id: "60a7c56b425a052b6d8e67e4", remove_from_default: true);
end
```

# Audit in Airflow Web UI

Airflow Web UI provides the following pages with audit information:

## User's Statistics

Log in to Airflow Web UI and navigate to **Security** -> **User's Statistics** tab.  
This tab provides the user's login count and the failed login count.

![alt text](/docs/public/images/airflow-ui-user-stat.png "User Statistics")

## Logs

Log in to the Airflow Web UI and navigate to **Browse** -> **Logs** tab.  

This tab contains events such as:

* cli_delete_user
* cli_create_user

![alt text](/docs/public/images/airflow-ui-logs.png "Logs")
