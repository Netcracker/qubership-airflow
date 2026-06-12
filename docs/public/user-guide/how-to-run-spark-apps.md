This section covers the details about how to run the Spark applications.

It covers the following topics:

* [Overview](#overview)
* [Prerequisites](#prerequisites)  
  * [Set Up RBAC](#set-up-rbac)
* [Submit Spark Applications Using spark_kubernetes Airflow Operator](#submit-spark-applications-using-spark_kubernetes-airflow-operator)
  * [Adding Kubernetes Connection](#adding-kubernetes-connection)

# Overview

This section provides information about how to submit Spark applications to Spark Operator GCP using the Airflow Operator. For more information, refer to [Spark_kubernetes](http://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/_api/airflow/providers/cncf/kubernetes/operators/spark_kubernetes/index.html#module-airflow.providers.cncf.kubernetes.operators.spark_kubernetes). 

# Prerequisites

Before you begin, ensure that you have the following:

* Spark Operator deployed on Kubernetes.
* Airflow service account granted with proper permissions to submit Spark applications to the dedicated namespace. For more information, see [Set Up RBAC](#set-up-rbac).
  
## Set Up RBAC

The Spark Operator works with Spark applications in a namespace specified by Spark Operator's `sparkJobNamespace` deployment parameter.  
Airflow service account should have access to be able to create SparkApplication custom resources in the Spark application namespace.  
The `attach_log` parameter of Airflow `SparkKubernetesSensor` allows appending the Spark application driver pod's logs to the sensor log.  
The application logs are rendered in the task of `SparkKubernetesSensor` when the application fails or completes successfully.
The Airflow service account should have access to the driver pod's logs as well.

The following role and role binding should be added to the Spark application's namespace specified by `sparkJobNamespace`:

Role:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: <spark_applications_namespace> #set the namespace specified by `sparkJobNamespace`
  name: airflow-spark-operator-role
rules:
  - apiGroups:
      - sparkoperator.k8s.io
    resources:
      - sparkapplications
      - sparkapplications/status
    verbs:
      - create
      - get
      - update
  - apiGroups:
      - ""
    resources:
      - pods/log
    verbs:
      - get
      - list
```

Role Binding:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: airflow-spark-operator-role-binding
  namespace: <spark_applications_namespace> #set the namespace specified by `sparkJobNamespace`
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: airflow-spark-operator-role
subjects:
- kind: ServiceAccount
  name: <airflow_service_account> #set the name of a serviceAccount used by Airflow
  namespace: <airflow-namespace> #set the namespace where Airflow has been deployed
```

# Submit Spark Applications Using spark_kubernetes Airflow Operator

To submit the Spark Applications, perform the following steps:

1. Prepare the SparkApplication yaml files. For more information, refer to the _Spark Operator Documentation_ at [[Spark Operator documentation](https://kubeflow.github.io/spark-operator/)](https://kubeflow.github.io/spark-operator/) and to _qubership-spark-on-k8s project_ at [https://github.com/Netcracker/qubership-spark-on-k8s](https://github.com/Netcracker/qubership-spark-on-k8s).  
1. Prepare a DAG to submit SparkApplication files:
   1. [airflow.providers.cncf.kubernetes.operators.spark_kubernetes](https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/_api/airflow/providers/cncf/kubernetes/operators/spark_kubernetes/index.html) can be used to create a task for Spark application submission.  
   1. [airflow.providers.cncf.kubernetes.sensors.spark_kubernetes](https://airflow.apache.org/docs/apache-airflow-providers-cncf-kubernetes/stable/_api/airflow/providers/cncf/kubernetes/sensors/spark_kubernetes/index.html) can be used to add a monitoring task to monitor the application status.  
      **Note**: It is recommended to set `reschedule` mode to a sensor that is used to monitor long-running applications, such as streaming. In this mode, the sensor instead of holding a worker slot for its whole execution time releases the worker resources and reschedules at a later time while the Spark application is running.  
      Refer to [airflow.sensors.base](https://airflow.apache.org/docs/apache-airflow/stable/_api/airflow/sensors/base/index.html) for details.  
   
   See an example of Spark DAGs at [/tests_dags_image/dags/spark-pi-dag.py](../../tests_dags_image/dags/spark-pi-dag.py), [/tests_dags_image/dags/spark-pi-dag.py](../../tests_dags_image/dags/spark-streaming-kafka-dag.py). In these DAGs the Spark applications namespace can be set by Airflow Variable with `spark_app_namespace` key. The variable can be added using Airflow UI Admin -> Variables menu.
1. Prepare a new docker image of Airflow. You can extend Qubership airflow release image for it.
1. Copy Spark application DAGs to `${AIRFLOW_USER_HOME}/dags/` in the Docker file. SparkApplication yaml files should be added to the directory as they are specified in the DAG.
1. Add Kubernetes connection to Airflow. For more information, see [Adding Kubernetes Connection](#adding-kubernetes-connection).
1. Deploy Airflow to Kubernetes and trigger the Spark DAGs.

## Adding Kubernetes Connection

Airflow _spark_kubernetes_ operator uses a connection of type Kubernetes to create Spark application's custom resources.

You can add the connection using any one of the following ways:

* Using Airflow UI 
  1. Login to the Airflow UI and navigate to the Admin > Connections menu.
    ![alt text](/docs/public/images/airflow-connections-menu.png "Airflow Connections")
  2. Add a connection of the `Kubernetes Cluster Connection` type.
    The connection name should be `kubernetes_default`.  
    The checkbox **In cluster configuration** should be checked if airflow and Spark operator are deployed on the same Kubernetes. Otherwise, the Kubernetes connection parameters should be specified.
    ![alt text](/docs/public/images/airflow-kubernetes-connection.png "Airflow Kubernetes Connection")
    
* Add the connection during the Airflow deployment or upgrade by specifying the connection in the Airflow deployment parameters:
  
  ```yaml
   scheduler:
     connections:
       - id: kubernetes_default
         type: kubernetes
         extra: '{"extra__kubernetes__namespace": "default", "extra__kubernetes__in_cluster": "true"}'
  ```
