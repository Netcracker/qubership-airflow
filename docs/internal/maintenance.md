This section describes the backup, restore and DR deployment procedures for the Airflow Service.

All the important information about Airflow state, such as Airflow users, DAGs/Tasks and their states, connections, and so on, is stored in the database. A new Airflow instance can work with an already existing Airflow database that includes the continuing in-progress DAGs. This adds possibilities for Airflow back up and restore procedures and Airflow DR deployments.

# Backup and Restore

To create Airflow backup, it is necessary to back up the Airflow Postgres database specified in the `.Values.data.metadataConnection` parameter. 
To restore from backup, it is necessary to restore the database and then install Airflow service using this database. It is also possible to perform restore with an already existing Airflow instance, however in this case, before you start restore you must downscale Airflow service to zero replicas.

# DR Deployments

It is possible to use Airflow in DR deployments assuming that the same database is available on both the DR sites. You can have the same database available on both sites using postgres DB synchronization, PG working in HA mode, the same kubernetes service that is available on both sites, and so on. It is also necessary to ensure that at the same time there are not more than one Airflow deployments working with the same database.

When you use the same Kubernetes deployment for both sites, no additional actions are required during failover/switchover. Kubernetes automatically restarts Airflow pods on another site.

When you use different Kubernetes clusters for different sites, you can use any of the following options to perform failover/switchover:

* Manual switchover/failover - Deploy one Airflow instance on DR site and downscale it. The downscale operation is necessary since currently the charts do not support deployments with 0 replicas. Deploy another Airflow instance on the main site. Then manually upscale/downscale Airflow pods including web, scheduler and flower deployments and workers statefulset during failover/switchover.
* Perform a clean delpoy of Airflow with the same parameters to another site during failover/switchover.
  
  **Note**: Deploying Airflow in clean mode does not affect the database and the data is not lost.

**Note**: Airflow needs Redis to be available to process the tasks, so the DR solution must ensure Redis availability for Airflow on both sites.