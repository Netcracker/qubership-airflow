The following topics are described in this section.

* [Overview](#overview)
* [Design](#design)
  * [Switch from Active to Standby Mode](#switch-from-active-to-standby-mode)
  * [Switch from Standby to Active Mode](#switch-from-standby-to-active-mode)
  * [Switch to Disable Mode](#switch-to-disable-mode)
* [Integration With Disaster Recovery Daemon](#integration-with-disaster-recovery-daemon)
* [DAGs DR](#dags-dr)
* [REST API](#rest-api)
  * [Contract](#contract)
  * [Security](#security)
* [Airflow Service Installation Procedure](/docs/public/installation.md#airflow-site-manager-and-dr-deployment)
* [Handling Split-Brain](#handling-split-brain)
* [Alerts Suppression on 'standby' Site](#alerts-suppression-on-standby-site)

## Overview

The Airflow site manager is responsible for the disaster recovery management.  
It handles REST requests from the Platform site manager.
For more details, refer to [site manager](https://github.com/Netcracker/DRNavigator).


## Design

![alt text](/docs/public/images/airflow_switchover.png "Scale up/down scheme")

In the active mode, Airflow is scaled up.  
In the standby mode, Airflow is scaled down to 0 replicas.

Airflow depends on PostgreSQL and Redis. DR scheme including RabbitMQ is not supported. Redis does not support the DR scheme deployment, and independent instances are deployed on each site.  
Airflows on both sites use the same database in PostgreSQL. It is replicated by Postgres.  
When site-manager switches an active site to standby, PostgreSQL is moved before Airflow. As a result, an active Airflow refers to PostgreSQL in the standby mode. 
It makes the Airflow status `down`. Site-manager (SM) does not move services with the `down` status. A special parameter `allowedStandbyStateList` has been added to the SM CR file to handle such cases. 
A service is moved from `active` to `standby` if its status, before the move process, is included in the `allowedStandbyStateList`.
The `down` and  `degraded` statuses are included in `allowedStandbyStateList` for Airflow. 

### Switch from Active to Standby Mode

1. First, the site-manager switches an active PostgreSQL to the standby mode, as Airflow depends on PostgreSQL. 
   Note that Airflow when an active site becomes `down`, it cannot work with a standby PostgreSQL.
2. Site-manager switches a standby PostgreSQL on a standby site to the active mode. 
3. Site-manager forces switch of active Airflow in the down state to the standby mode. 
4. Airflow components like Web Server, Scheduler, Workers, Flower (if deployed), and StatsD (if deployed) are scaled to 0 replicas.
5. If KubernetesExecutor is used, its worker pods are deleted after all Airflow components are scaled to 0.
6. Airflow DAGs stop. The tasks' queue in Redis is removed.

### Switch from Standby to Active Mode

1. By the time site-manager gets to Airflow on a standby site, PostgreSQL is already in the active mode on that site.
2. Site-manager switches standby Airflow on a standby site to the active mode.
3. Airflow components like Web Server, Scheduler, Workers, Flower (if deployed), and StatsD (if deployed) are scaled to replicas set in the `WEB_SERVER_REPLICAS`, `SCHEDULER_REPLICAS`, `WORKER_REPLICAS`, `FLOWER_REPLICAS`, and `STATSD_REPLICAS` parameters accordingly.    
4. DAGs run according to the schedule.

### Switch to Disable Mode

Disable and Standby modes are the same for Airflow.

## DAGs DR

DAGs run only on an active site. When the Airflow mode changes to standby, the DAGs stop. The tasks' queue gets cleaned up as well.
On a new active site, the DAGs run according to the schedule.   
If retry arguments are set for the DAG, the tasks are run on a new active site later. For more information about the retry parameters, refer to the Airflow documentation at [https://airflow.apache.org/docs/apache-airflow/2.10.5/_api/airflow/models/baseoperator/index.html](https://airflow.apache.org/docs/apache-airflow/2.10.5/_api/airflow/models/baseoperator/index.html).

```python
... 
args = {
    'owner': 'Airflow',
    'retries': 3,
    'retry_delay': timedelta(minutes=5)
}
...
```

## Integration With Disaster Recovery Daemon

Airflow Site Manager implementation is based on [Disaster Recovery Daemon](https://github.com/Netcracker/qubership-disaster-recovery-daemon).

Airflow SM uses the Disaster Recovery Daemon's server and extends controller to add switchover and health calculation Airflow specific functionality.  
Instead of a Custom Resource, Airflow SM uses the `airflow-dr-state` ConfigMap to manage DR mode switches. DRD controller watches the `airflow-dr-state` ConfigMap and proceeds the mode change if it gets updated.  

```yaml
kind: ConfigMap
apiVersion: v1
metadata:
 name: airflow-dr-state
data:
 mode: 'standby'
 noWait: false
 status_comment: 'Switchover successfully done'
 status_mode: 'standby'
 status_status: 'done'
```

## REST API 

### Security

If `SITE_MANAGER_SERVICE_ACCOUNT_NAME` and `SITE_MANAGER_NAMESPACE` are enabled, the Airflow Site-Manager endpoints are secured using Kubernetes JWT Service Account Tokens.
Airflow Site-Manager requires a "Authorization": "Bearer <TOKEN>" Header to be set for the requests.
For the configuration details, refer to the [Configuring Airflow Service](/docs/public/installation.md#airflow-site-manager-and-dr-deployment) section.

### Contract

Airflow Site Manager supports the following REST API:

* Check the service mode and status of the DR procedure.
  **URL**: <service>.<namespace>.svc.cluster.local/sitemanager  
  **Method**: /GET  
  **Content**: {"mode": "active|standby|disable", "status": "running|done|failed"}
  
  Currently, Airflow Site Manager supports active and standby modes.


* Set a new mode for the service.  
  **URL**: <service>.<namespace>.svc.cluster.local/sitemanager  
  **Method**: /POST  
  **Data Params**: {"mode": "active|standby|disable"}

  Currently, Airflow Site Manager supports active and standby modes.


* Get Airflow health.   
  **URL**: <service>.<namespace>.svc.cluster.local/healthz   
  **Method**: /GET  
  **Content**: {"status": "up|down|degraded"}  
  
  Health is calculated based on the actual deployment replicas and replica parameters specified in the Airflow Site Manager parameters.  
  In the `standby` mode, the health should be `down`. 
  In the `active` mode, the health is calculated as follows:

  - Flower component can only change the status to `degraded` if it is installed and unhealthy.
  - StatsD component can only change the status to `degraded` if it is installed and unhealthy.
  - Airflow is considered `down` if at least one of the components (Scheduler, Web Server, Worker) is unhealthy.
  - Airflow is considered `degraded` if at least one of the components (Scheduler, Web Server, Worker, Flower) has fewer replicas than specified in the Airflow Site Manager's deployment parameters - `SCHEDULER_REPLICAS`, `WEB_SERVER_REPLICAS`, `WORKER_REPLICAS`, and `FLOWER_REPLICAS`.
  - In other cases, Airflow is `up`
  - KubernetesExecutor pods do not impact health of Airflow.   
  - CeleryExecutor impacts the health only if it is installed.

## Handling Split-Brain

Currently, split-brain cases are not handled automatically. This means that it is possible to get active Airflow on both sides.  
In order to handle the split-brain manually, the Airflow on site that is intended to be standby should be switched to standby:

* Switch one active Airflow to the standby mode.
   This can be done using the site-manager `sm-client` script or sending a REST request to the Airflow Site Manager.

   ```
   # Using sm-client script
   python sm-client --run-services <airflow_sm_service_name> standby <standby_site>

   # Example
   python sm-client --run-services airflow-site-manager standby k8s-2
   
   # Using REST request
   curl -X POST -H "Content-Type: application/json" \
     -d '{"mode":"standby"}' \
     http://<airflow-site-manager-ingress>/sitemanager
   
   # Example
   curl -X POST -H "Content-Type: application/json" \
     -d '{"mode":"standby"}' \
     http://airflow-site-manager.k8s-cluster.qubership.com/sitemanager

   ```

## Alerts Suppression on 'standby' Site

Airflow in the `standby` mode is scaled to 0. It triggers alerts responsible for the Airflow component's health. To avoid alerts' notification spam, alerts are suppressed on the `standby` site.  
Alerts' suppression is done based on the `AirflowDRState` alert. If this alert fires, all others are suppressed. All alerts are available and work as usual in the Prometheus service. 
Alerts' suppression only mutes notifications. 
**Note**: Alerts on the `active` site are also suppressed if Airflow components are scaled to 0.
