# Hortonworks Data Platform(HDP)  DAGs

This section covers the details about how to run the DAGs that connect to remote HDP with enabled Kerberos for HDFS,YARN and hive and enabled SSL for YARN and hive. This includes the following DAGs:
* hdfs_conn_test
* example_spark_operator
* hive_conn_test

## Common configuration

Firstly, it is necessary to configure kerberos on airflow side with airflow user. Airflow user on HDP side in Ranger must be added to HDFS `all - path` policy. It also necessary to specify hostAliases for workers on airflow side for all HDP nodes.

## hdfs_conn_test configuration

It is necessary to configure `webhdfs_default` connection of HDFS type in airflow to one of HDFS HDP nodes. Parameter example:

```
host: hdm-1.main.node.qubership.com
port: 50070
```

Note that for SSL connections the following parameters are allowed in extra field:

   * `use_ssl` - If SSL should be used. By default is set to `false`.
   * `verify` - How to verify SSL. For more information refer to https://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification.
   
## example_spark_operator configuration

For this DAG to work, it is necessary to do some configuration on HDP side:

* `dfs.client.use.datanode.hostname` in `hdfs-site` HDFS config must be set to `true`.
* HDP nodes must contain external IPs in /etc/hosts, for example: 

```
# Ansible managed
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

# Hadoop members
192.168.0.32 hdu-0.ui.node.qubership.com hdu-0
192.168.0.26 hdm-1.main.node.qubership.com hdm-1
192.168.0.25 hdm-2.main.node.qubership.com hdm-2
192.168.0.34 hdm-3.main.node.qubership.com hdm-3
192.168.0.15 hdn-1.hadoop.node.qubership.com hdn-1
192.168.0.28 hdn-2.hadoop.node.qubership.com hdn-2
192.168.0.14 hdn-3.hadoop.node.qubership.com hdn-3

# Added configs
10.109.39.7 hdu-0.ui.node.qubership.com
10.109.38.245 hdm-1.main.node.qubership.com
10.109.39.19 hdm-2.main.node.qubership.com
10.109.39.13 hdm-3.main.node.qubership.com
10.109.39.15 hdn-1.hadoop.node.qubership.com
10.109.39.17 hdn-2.hadoop.node.qubership.com
10.109.39.4 hdn-3.hadoop.node.qubership.com
```
**NOTE**: In airflow test image spark DAG you need to specify ports properties for Spark if you want to use restricted ports environment. Example for our Hadoop restricted environment is provided below: 
````
DEFAULT_SPARK_CONF = {
"spark.ui.port": "4040",
    "spark.driver.port": "40000",
    "spark.port.maxRetries": "32",
    "spark.blockManager.port": "40033",
    "spark.broadcast.port": "40034",
    "spark.executor.port": "40035",
    "spark.fileserver.port": "40036",
    "spark.replClassServer.port": "40037"
}
````
In airflow test image upon start it is necessary to execute startup script to get HDP configs. This script requires the following envs:

```yaml
env:
  - name: AMBARI_USER
    value: ambari_username
  - name: AMBARI_PASSWORD
    value: ambari_password
  - name: AMBARI_URL
    value: https://hdu-0.ui.node.qubership.com:8443
  - name: AMBARI_PORT
    value: 8443
  - name: CLUSTER_NAME
    value: hadoop-qa
  - name: HADOOP_DISTRIBUTION
    value: HDP
```

To call this script as a start up command specify:

```yaml
workers:
...
  args:
    - "bash"
    - "-c"
    - |-
      ./get_hadoop_conf.sh; \
      exec \
      airflow {{ semverCompare ">=2.0.0" .Values.airflowVersion | ternary "celery worker" "worker" }}
```

When using SSL also specify SSL cert secret and mount it into the pod:

```yaml
extraSecrets:
   certificates:
     data: |
       rootca: rootcacontentgoeshere
...
workers:
  extraVolumeMounts:
    - name: certificates
      mountPath: /opt/airflow/certs/
      readOnly: true
  extraVolumes:
    - name: certificates
      secret:
        secretName: certificates
...
```

## hive_conn_test

For this DAG to work, some additional configuration is required on HDP side:
* hive user must be added to `all - queue` yarn policy in ranger
* In `Custom hive-site` `hive.security.authorization.sqlstd.confwhitelist.append` must be set to `airflow.ctx.*|mapred.job.name`

In airflow connection `hive_cli_default` must be created with the type `Hive Client Wrapper`. Following is the example of connection parameters:

```yaml
host: hdm-1.main.node.qubership.com
schema: default;ssl=true;sslTrustStore=/etc/ssl/certs/java/cacerts;trustStorePassword=changeit
port: 10000
Extra: {"use_beeline": true,"principal":"hive/hdm-1.main.node.qubership.com@LDAP.REALM"}
```

Also it is necessary to create connection `metastore_default` of type Hive metstore Thrift. Example parameters can be:
```yaml
Host: hdm-1.main.node.qubership.com
Login: admin
Password: admin
Port: 9083
```


# Non HDP DAGs

## kafka_confluent_conn_test

For this DAG to work it is necessary to enable triggerer during airflow deployment:

```yaml
triggerer:
  enabled: true
# necessary for triggerer logs
  persistence:
    storageClassName: local-path
```

Kafka connection with connection ID `kafka_test_conn` must be created with the `Config Dict` field specified, for example:
```json
{
  "bootstrap.servers": "kafka.kafka-service:9092",
  "sasl.username": "kafkausername",
  "sasl.password": "kafkapassword",
  "sasl.mechanism": "SCRAM-SHA-512",
  "security.protocol": "SASL_PLAINTEXT",
  "group.id": "testgroup",
  "session.timeout.ms": 30000,
  "allow.auto.create.topics": "true",
  "auto.offset.reset": "earliest",
  "enable.auto.offset.store": false
}
```

`airflowtestkafkatestopic` must be created in kafka.

After this the DAG should work.

For SSL kafka the configuration must be as follows:

```json
{
  "bootstrap.servers": "kafka.kafka-service:9092",
  "sasl.username": "kafkausername",
  "sasl.password": "kafkapassword",
  "sasl.mechanism": "SCRAM-SHA-512",
  "security.protocol": "SASL_SSL",
  "group.id": "testgroup",
  "session.timeout.ms": 30000,
  "allow.auto.create.topics": "true",
  "auto.offset.reset": "earliest",
  "enable.auto.offset.store": false,
  "ssl.ca.location": "/home/airflow/certs/ca.crt"
}
```

`ssl.ca.location` must point to mounted ca certificate.

## postgres_operator_test_dag

For this DAG to work, airflow version >= 2.6.0 is required.

Postgres connection with connection ID `postgres_test_conn` and Connection Type `Postgres` must be created, for example:

* `Host`: `postgres.postgres-service.svc` 
* `Schema`: `airflowtestdagdb`
* `Login`: `airflowpgtestdaguser`
* `Password`: `airflowpgtestdagpassword`
* `Port`: `5432`

In this case the database `airflowtestdagdb` must be pre-created in PG. For example, in psql in postgres pod: `postgres=# create database airflowtestdagdb;`.

After this the DAG should work.
