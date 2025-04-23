The topics covered in this section are as follows:

* [Airflow DAG has Failed State](#airflow-dag-has-failed-state)
* [Tasks are Stuck in Queued State](#tasks-are-stuck-in-queued-state)
* [DAGs are Stuck in Running State](#dags-are-stuck-in-running-state)
* [Webserver Pod Restarts Multiple Times](#webserver-pod-restarts-multiple-times)
* [Airflow Pods Restart Multiple Times](#airflow-pods-restart-multiple-times)
* [Task does not Execute and Worker Logs are Stuck in Celery Executor](#task-does-not-execute-and-worker-logs-are-stuck-in-celery-executor)
* [Task does not Execute and Worker Logs Contain Redis Connection Error](#task-does-not-execute-and-worker-logs-contain-redis-connection-error)
* [Task Fails with Error and no Logs Available While the Logs for Other Successful Tasks are Visible](#task-fails-with-error-and-no-logs-available-while-the-logs-for-other-successful-tasks-are-visible)
* [Wrong Protocol Resolution in redirect_uri in IDP Integration](#wrong-protocol-resolution-in-redirect_uri-in-idp-integration)
* [Airflow Logs are not Available for Some Attempts in Tasks with Multpile Tries](#airflow-logs-are-not-available-for-some-attempts-in-tasks-with-multpile-tries)
* [Error Codes](#error-codes)

# Airflow DAG has Failed State

If DAG has failed state, check the logs for issues.

To retry a failed DAG:

* Use the `Clear` option on failed task details. This option clears the current state and re-runs the DAG.
* Use the `retry` policy on DAG's configuration. This policy allows to automate retries if something is wrong.

# Tasks are Stuck in Queued State

**Solution**:

* Check if there are active workers.
* Check if Redis is alive.
* Check if workers and scheduler are using the same queue.
* If current DAG has specific queue to execute then check if there is any active worker to match this.

# DAGs are Stuck in Running State

If all new DAGs are stuck in running state, it could indicate a problem with the scheduler.

**Solution**:

Check if the scheduler instance is alive. This problem could also be seen in the webserver. It displays `The scheduler does not appear to be running.` alarm on the top of the page.

If the scheduler is alive, and tasks are stuck in the queued state, see [Tasks are Stuck in Queued State](#tasks-are-stuck-in-queued-state).

# Webserver Pod Restarts Multiple Times

If webserver pod keeps restarting, it indicates a problem with the database and caused by unavailability of database.

**Solution**:

* Check if the database is alive.
* Check if the database is available from webserver.
* Check if the database has no data loss. If Airflow table is lost, you can use backup/restore to resolve this issue.
* Check the [Airflow Pods Restart Multiple Times](#airflow-pods-restart-multiple-times).

# Airflow Pods Restart Multiple Times

If any of Airflow's services restart frequently after some time of work, or if it does not start, check if there are enough resources for Airflow pods. For more information on the minimal amount of resources, refer to the **Hardware Requirements** section in the _Airflow Service Installation_.

# Task does not Execute and Worker Logs are Stuck in Celery Executor

If the Airflow tasks do not execute with `airflow.exceptions.AirflowTaskTimeout: Timeout, PID: 5620` scheduler error in the logs, and worker logs stop as shown below, check if your Redis has SSL enabled and if it has, configure the Redis SSL connection in `data.brokerUrl` installation parameter.

```

/home/airflow/.local/lib/python3.9/site-packages/airflow/configuration.py:436: FutureWarning: The 'hostname_callable' setting in [core] has the old default value of 'airflow.utils.net:get_host_ip_address'. This value has been changed to 'airflow.utils.net.get_host_ip_address' in the running config, but please update your config before Apache Airflow 2.1.
  warnings.warn(
[2023-04-05 08:27:19 +0000] [20] [INFO] Starting gunicorn 20.1.0
[2023-04-05 08:27:19 +0000] [20] [INFO] Listening at: http://[::]:8793 (20)
[2023-04-05 08:27:19 +0000] [20] [INFO] Using worker: sync
[2023-04-05 08:27:19 +0000] [21] [INFO] Booting worker with pid: 21
[2023-04-05 08:27:19 +0000] [22] [INFO] Booting worker with pid: 22
 
 -------------- celery@airflow-worker-5b8c4749c5-6p2w1 v5.2.7 (dawn-chorus)
--- ***** ----- 
-- ******* ---- Linux-5.4.219-126.411.amzn2.x86_64-x86_64-with-glibc2.31 2023-04-05 08:27:20
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         airflow.executors.celery_executor:0x7f148c834ee0
- ** ---------- .> transport:   redis://:**@your.redis.address:6379//
- ** ---------- .> results:     postgresql://root:**@your.pg.address:5432/pg_db
- *** --- * --- .> concurrency: 16 (prefork)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** ----- 
 -------------- [queues]
                .> default          exchange=default(direct) key=default
                

[tasks]
  . airflow.executors.celery_executor.execute_command
2023-04-05T08:27:20.251325968Z
```

# Task does not Execute and Worker Logs Contain Redis Connection Error

If a task does not execute and worker logs contain Redis connection error, check the Redis connection parameters. For example, consider the following error:

```
[2023-05-16 14:31:01,556: ERROR/MainProcess] consumer: Cannot connect to redis://default:**@airflow.redis-app.svc:6379/2: Error while reading from socket: (104, 'Connection reset by peer').
Trying again in 2.00 seconds... (1/100)
```

This issue is similar to the previous one in which a non-SSL Redis connection string with SSL enabled Redis is used.

# Task Fails with Error and no Logs Available While the Logs for Other Successful Tasks are Visible

When a task fails with an error and instead of the logs, the message `*** Could not read served logs: Request URL is missing an 'http://' or 'https://' protocol.` is present, it means that the Airflow executor for some reason can't start executing the task. In this case, check the following:

* Airflow pod logs
* Postgres status, postgres connections, and postgres resources
* Redis status
* Airflow pods resources
* When using remote DAG storage, DAG availability on all Airflow pods

# Wrong Protocol Resolution in redirect_uri in IDP Integration

This section briefly describes possible solutions to the problem when you get `Invalid parameter: redirect_uri` error with configured IDP integration, and the only difference is in redirect_uri HTTP/HTTPS protocol, for example:

```
https://your.idp.keycloak.address/auth/realms/realmname/protocol/openid-connect/auth...&redirect_uri=http%3A%2F%2Fyour.airflow.address...
```
instead of 
```
https://your.idp.keycloak.address/auth/realms/realmname/protocol/openid-connect/auth...&redirect_uri=https%3A%2F%2Fyour.airflow.address...
```
in your address bar.

The possible solutions to this problem are described below:

* If it is openshift that uses HA-proxy, you can try adding airflow route address to `/etc/haproxy/ocp_sni_passthrough.map` file on the balancer nodes.
* Try setting `proxy_fix_x_proto` parameter from `webserver` section. It should be set to the number of proxies in front of airflow pod, starting with the proxy where TLS termination happens. For example, in case of only openshift route and balancer with TLS termination happening on balancer, it should be set to `2`. For more information, refer to https://werkzeug.palletsprojects.com/en/3.0.x/middleware/proxy_fix/.
* It is possible to overwrite `login` method of `flask_appbuilder.security.views.AuthOAuthView` and set https manually. For example, if you are using webserver config (can be passed using `webserver.webserverConfig` parameter) similar to [webserver_config.py](/chart/helm/airflow/qs_files/webserver_config_keycloak.py), it is possible to overwrite the method like below:

```python
...
from typing import Optional
from werkzeug.wrappers import Response as WerkzeugResponse
from flask import flash, g, redirect, request, session, url_for
from flask_appbuilder.security.utils import generate_random_string
from flask_appbuilder._compat import as_unicode
...
class CustomAuthRemoteUserView(AuthOAuthView):

    @expose("/login/")
    @expose("/login/<provider>")
    @expose("/login/<provider>/<register>")
    def login(self, provider: Optional[str] = None) -> WerkzeugResponse:
        log.debug("Provider: %s", provider)
        if g.user is not None and g.user.is_authenticated:
            log.debug("Already authenticated %s", g.user)
            return redirect(self.appbuilder.get_url_for_index)

        if provider is None:
            return self.render_template(
                self.login_template,
                providers=self.appbuilder.sm.oauth_providers,
                title=self.title,
                appbuilder=self.appbuilder,
            )

        log.debug("Going to call authorize for: %s", provider)
        random_state = generate_random_string()
        state = jwt.encode(
            request.args.to_dict(flat=False), random_state, algorithm="HS256"
        )
        session["oauth_state"] = random_state
        try:
            if provider == "twitter":
                return self.appbuilder.sm.oauth_remotes[provider].authorize_redirect(
                    redirect_uri=url_for(
                        ".oauth_authorized",
                        provider=provider,
                        _external=True,
                        state=state,
                    )
                )
            else:
                return self.appbuilder.sm.oauth_remotes[provider].authorize_redirect(
                    redirect_uri=url_for(
                        ".oauth_authorized", provider=provider, _external=True, _scheme="https" #setting https manually
                    ),
                    state=state.decode("ascii") if isinstance(state, bytes) else state,
                )
        except Exception as e:
            log.error("Error on OAuth authorize: %s", e)
            flash(as_unicode(self.invalid_login_message), "warning")
            return redirect(self.appbuilder.get_url_for_index)
...

```

# Airflow Logs are not Available for Some Attempts in Tasks with Multiple Tries 

This issue can be observed in airflow setups with multiple workers and with log stored on workers. In this case, airflow logs are present in the airflow user interface for the latest try of a task with multpile tries but are missing for some of other tries. The issue happens because airflow task log reader tries to find the logs only on the worker, where the latest attempt was executed. So if previous tries were executed on different workers, the logs will not be visible in airflow user interface. The logs for the previous attemts can be found on other workers in the **/opt/airflow/logs** folder. To check on what worker previous attempts were executed, it is possible to check `Details` tab of a task and pick required Task Try on this tab. If it is critical to view the task logs in the user interface, it is recommended to configure the remote logging storage. It can be done similarly to [logging configuration for kubernetes executor workers](/docs/public/installation.md#using-s3-remote-storage-for-storing-task-logs-with-kubernetes-executor).

# Error Codes

The error codes information is given in the table below.

| Error Code   | Message Text (English)                                                      | Scenario                                                                                                                                                         | Reason                                           | Solution                                                                                            |
|--------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| AIRFLOW-8300 | "Could not get DBaaS Redis database. Response code: &s"                     | During the Airflow deployment, the DB creation script tries to configure the Redis database in DBaaS to construct a connection string for the Kubernetes secret. | The configuration issue or DBaaS is unavailable. | Check the DBaaS and Redis configuration. Check that DBaaS works properly.                           |
| AIRFLOW-8301 | "Could not get DBAAS PG database. Response code: &s"                        | During the Airflow deployment, the DB creation script tries to configure the PG database in DBaaS to construct a connection string for the Kubernetes secret.    | The configuration issue or DBaaS is unavailable. | Check the DBaaS and PG configuration. Check that DBaaS works properly.                              |
| AIRFLOW-8302 | "Could not get DBAAS airflow connection database. Response code: %s"        | Airflow could not get one of the Airflow connections of Postgres type.                                                                                           | The configuration issue or DBaaS is unavailable. | Check the DBaaS and the `config.secrets.backend` configuration. Check that DBaaS and PG work properly.  |
| AIRFLOW-8303 | "DBAAS returned connection string for PG does not contain database name"    | For some reason, DBaaS returned connection string for PG did not contain the database name.                                                                      | The configuration issue or DBaaS is unavailable. | Check that DBaaS and PG work properly.                                                              |
| AIRFLOW-8304 | "Could not get MAAS Kafka database.  Response code: %s"                     | Airflow could not get one of the Airflow connections of Kafka type.                                                                                              | The configuration issue or MaaS is unavailable.  | Check MaaS and Kafka logs. Check `config.secrets.backend_kwargs` values for Kafka connections.      |
| AIRFLOW-8305 | "Unsupported authentication mechanism for kafka addresses"                  | MaaS returned Kafka addresses with unsupported authentication mechanisms.                                                                                        | Unsupported Kafka authentication mechanism.      | Check that Kafka/DBaaS are configured with `SASL_PLAINTEXT`, `PLAINTEXT`, `SSL` or `SASL_SSL` authentication.          |
| AIRFLOW-8306 | "Client credentials not found for Kafka!"                                   | MaaS returned Kafka connection without client credentials.                                                                                                       | MaaS did not provide Kafka client credentials.   | Check Kafka/MaaS integration configuration.                                                         |
| AIRFLOW-8307 | "Not supported sasl mechanism or password format!"                          | MaaS returned Kafka connection requires a not supported sasl mechanism or password format.                                                                       | MaaS did not provide the supported Kafka connection.  | Check whether the Kafka credential type is set to `PLAIN` or `SCRAM`.                                           |
| AIRFLOW-8308 | "Incorrect parameter for SSL certificate verification"                      | The `DBAAS_SSL_VERIFICATION_MAIN` environment variable was set incorrectly.                                                                                      | Incorrect DBaaS integration configuration.            | Check that `DBAAS_SSL_VERIFICATION_MAIN` is set to `DISABLED`,`ENABLED`, or starts with `CERT_PATH:`.|
| AIRFLOW-1930 | "Error occurred while creating PG secret."                                  | The Airflow deployment script, which is responsible for the DBaaS database's creation, creates the Kubernetes secret containing the Redis connection string.     | The configuration issue or Kubernetes API issue. | Check the DBaaS and Redis configuration. Check that the Kubernetes API works properly.              |
| AIRFLOW-1931 | "Error occurred while creating Redis secret."                               | The Airflow deployment script, which is responsible for the DBaaS database's creation, creates the Kubernetes secret containing the PG connection string.        | The configuration issue or Kubernetes API issue. | Check the DBaaS and PG configuration. Check that the Kubernetes API works properly.                 |
