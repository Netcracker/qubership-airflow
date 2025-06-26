This guide provides information about the main security parameters and its configuration in Qubership Platform Airflow service.

## Direct Access to KubeAPI from Pods with Justification and Goal of this Connection

When deployed with kubernetes executor, airflow can access KubeAPI to create worker pods to execute DAG tasks.

Airflow platform custom preinstall job can use KubeAPI to remove some deprecated secrets from older airflow versions.

Additionally, when writing DAGs, users can access KubeAPI in order to execute custom DAG logic.

## Exposed Ports

* Airflow User Interface port - Only on API server pods, by default 8080. Airflow user interface, API and metrics plugin use this port.
* workerLogs port - Only on worker pods, by default 8793. Used by webserver to retrieve task logs from workers.
* Statsd exporter ports - Only on statsd exporter pod, by default 9125 (ingest) and 9102 (scrape). Used for airflow prometheus metrics.

**Note**: Ports can be changed in the installation parameters. Additional ports will be present, if not tested by Qubership Platform airflow components are deployed, for example, triggerer or rpcServer.

## Secure Protocols

Airflow supports secure connection to various services:
* For configuration of secure connection to DBaaS/MaaS API, refer to the [DBaaS Integration](/docs/public/installation.md#dbaas-integration) section in the _Airflow Service Installation Procedure_.
* For configuration of secure connections recieved from DBaaS/MaaS, refer to the [Using SSL with Connections Received from DBaaS](/docs/public/installation.md#using-ssl-with-connections-received-from-dbaas) section in the _Airflow Service Installation Procedure_.
* For configuration TLS for providers
When configuring TLS for manually created connections, refer to the _Official Airflow Provider Documentation_ at https://airflow.apache.org/docs/#providers-packages-docs-apache-airflow-providers-index-html.
* For configuring TLS for airflow logs in S3, refer to the [Using S3 Remote Storage for Storing Task Logs with Kubernetes Executor](/docs/public/installation.md#using-s3-remote-storage-for-storing-task-logs-with-kubernetes-executor) section in the _Airflow Service Installation Procedure_.
* For enabling TLS on airflow user interface, refer to the [Using S3 Remote Storage for Storing Task Logs with Kubernetes Executor](/docs/public/installation.md#using-s3-remote-storage-for-storing-task-logs-with-kubernetes-executor) section in the _Airflow Service Installation Procedure_.
* For enabling TLS on airflow ingresses, refer to the [Enabling HTTPS for Airflow Ingresses](/docs/public/installation.md#enabling-https-for-airflow-ingresses) section in the _Airflow Service Installation Procedure_.
* For enabling TLS on airflow user interface inside Kubernetes, refer to the [Enabling TLS on airflow UI inside kubernetes](/docs/public/installation.md#enabling-tls-on-airflow-ui-inside-kubernetes) section in the _Airflow Service Installation Procedure_.
* For configuring airflow with TLS IDP, refer to the [Keycloak With TLS](/docs/public/installation.md#keycloak-with-tls) section in the _Airflow Service Installation Procedure_.
* For configuring Rclone TLS, refer to the [Using TLS for Rclone Endpoint](/docs/public/installation.md#using-tls-for-rclone-endpoint) section in the _Airflow Service Installation Procedure_.

## Local Accounts

By default, Airflow deploys without IDP and creates the Admin user (using [Airflow FAB provider](https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/index.html)). It is configured by `webserver.defaultUser` parameter. The user creation can be disabled or it is possible to assign another role to this user. When using IDP, the creation of this user should be disabled.

### Changing Credentials

**Note**: Changing credentials is only possible when using Airflow local management and not remote IDP/Keycloak (or LDAP).

Credentials can be changed in the Airflow Web user interface on the `Your Profile` page.

### List of Airflow Roles

For the list of airflow roles and information about configuring Airflow roles, refer to the _Official Airflow Documentation_ at [https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/auth-manager/access-control.html](https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/auth-manager/access-control.html).

## List of Security Events

**Note**: This list includes a list of webserver security events for IDP and database web users authentication.

| event                                                  | example |
|--------------------------------------------------------|---|
| access to API UI address                               |`10.236.211.162 - - [19/Dec/2024:05:33:33 +0000] "GET / HTTP/1.1" 302 197 "https://dashboard.custom.cloud.qubership.com/" "Mozilla/5.0...`|
| failed login attempt with database authentication      |`[2024-12-19T05:34:28.225+0000] {override.py:2214} INFO - [AUDIT] Login Failed for user: ...`|
| User info when received from IDP                       |[`2024-12-20T11:19:45.068+0000] {webserver_config.py:112} INFO - user info: {'username': 'airflow_test_user_1703', 'email': 'airflow_test_user_1703@qubership.com', 'first_name': 'airflow_test_user_1703', 'last_name': 'airflow_test_user_1703', 'role_keys': ['airflow_admin']`}|
| User add events after receiving user from IDP          |`[2024-12-20T11:19:46.100+0000] {override.py:1596} INFO - [AUDIT] Added user airflow_test_user_1703`|
| User modification events after receiving user from IDP |`[2024-12-20T11:19:46.124+0000] {override.py:1678} INFO - [AUDIT] Updated user airflow_test_user_1703 airflow_test_user_1703`|

**Note**: For Airflow audit logs that are accessible in the Airflow API user interface, refer to [https://airflow.apache.org/docs/apache-airflow/stable/security/audit_logs.html](https://airflow.apache.org/docs/apache-airflow/stable/security/audit_logs.html).

## Session Management

By default, (Or using default Keycloak/IDP integration) the session timeout can not be customized and uses airflow/Flask_appbuilder default value. However, airflow (and airflow helm chart) allows to pass the custom python configuration file as an installation parameter (`apiServer.apiServerConfig`). Hence, it is possible to write the custom config and add session management if needed. For more information, refer to the _Airflow Documentation_ at [https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/auth-manager/webserver-authentication.html](https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/auth-manager/webserver-authentication.html) and _Flask-Appbuilder Docnumentation_ at [https://flask-appbuilder.readthedocs.io/en/latest/security.html](https://flask-appbuilder.readthedocs.io/en/latest/security.html).

## Password Requirements and Restrictions

When using IDP/LDAP, password policy is configured on the IDP/LDAP side. Without LDAP/IDP, airflow does not enforce any password policy. Hence, please use your own good password policy, or even better, use IDP.

## Blocking Account

When using LDAP/IDP, account should be blocked on the IDP side (AUTH_ROLES_SYNC_AT_LOGIN should be set to true in this case, it is set to true in default IDP integration configuration). For more information, refer to https://flask-appbuilder.readthedocs.io/en/latest/security.html. When not using LDAP/IDP, it is possible to delete the user using pod CLI, refer to https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/cli-ref.html. Alternatively, it is possible to delete users in the Airflow UI on the **Security**-> **List Users** tab.

## Security Related Events Logs

It is possible too see some security related events in Web user interface on the **Browse** -> **Audit Logs** tab. In pod logs, it is possible to use [Audit logging](/docs/public/installation.md#audit-logs). When using IDP(Keycloak), user management operations are executed on IDP side. Without IDP user management operations performed in the user interface are not logged itself per second, but it is possible to find them in the logs by request address, for example, for adding user `10.227.209.117 - - [18/Dec/2024:13:37:39 +0000] "GET /users/add` . The same goes for login/logout events: `10.227.209.117 - - [18/Dec/2024:13:55:09 +0000] "POST /logout/` or `10.227.209.117 - - [18/Dec/2024:13:55:26 +0000] "GET /login/` . For failed login event, it is possible to audit log, for example: `[2024-12-18T13:58:57.716+0000] {override.py:2214} INFO - [AUDIT] Login Failed for user: wsdf`.
