DR sync DAG can be used to replicate Hive/HDFS data between to hadoop clusters managed by ambari. This section describes how to use DR sync DAG.

# Architecture

DR DAG consists of three parts: The HDFS part, responsible for copying HDFS files, the Hive PG part, responsible for copying HIVE PG DATABASE, and the Airflow PG part, responsible for copying AIRFLOW PG DATABASE.

## HDFS Part

![HDFS sync scheme for a folder](/docs/public/images/DRscheme.drawio.png)

DR synchronization works based on HDFS snapshots and is performed by Airflow DAG tasks. 

1. For the first initial copy, the first snapshot is created on main site. For more information, see [https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsSnapshots.html](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsSnapshots.html). 
2. The content of this snapshot is copied on the DR site to a folder using distcp.
3. For the folder on the DR site, a snapshot is created. Note that since no one is writing to the DR site apart from the distcp process, the contents of the snapshot on the main site is the same as on the DR site.

The following steps are executed in the cycle:

4. A new snapshot is created on the main site.
5. The difference between the snapshots is copied from the main site to the DR site.
6. A new snapshot is created on the DR site.
7. The previous snapshots are deleted.

## HIVE PG Part

The HIVE PG synchronization part is based on pg_dump/pg_restore and is performed by Airflow DAG tasks. It copies the PG database from one address to another address using pg_dump/pg_restore.

1. Hive on DR site is stopped through the Ambari API.
2. Database is downloaded from one address and then uploaded to another using pg_dump/pg_restore. Note that the database is dropped before it is uploaded to the target address.
3. Hive on DR site is started through the Ambari API.

## AIRFLOW PG Part

The AIRFLOW PG synchronization part is based on pg_dump/pg_restore and is performed by the Airflow DAG task. It copies the PG database from one address to another address using pg_dump/pg_restore. Currently, it is required to have the same user for both Airflow PG databases.

**Note**: If a DR failover happens during the DR DAG execution, it is necessary to manually recreate the database or manually restore it from backup.

## Tasks

The DAG consists of the following tasks:

* `find_correct_ssh_host` - This task is used to find the correct host for the SSH connection. An active namenode from the DR site is chosen.
* `stop_hive` - This task stops the hive service on the DR site through the Ambari API.
* `do_kinit` - This task performs kinit on the SSH host.
* `verify_foldername_state` - This task checks the state of the folder `foldername` and determines if an update or a full copy is needed. If the folders on the DR or Main sites are in an incorrect state, an error is displayed. Also, this task creates a snapshot on the main site that is later used to update to on the DR site. Note that there can be multiple such tasks (for each folder).
* `copy_pg_hive_database` - This copies the Hive PG database from RO copy of the main Hive database on the DR site to the PG database of Hive installed on the DR site. 
* `initialize_folder_foldername`/`update_folder_foldername` - These tasks perform an initial copy or update of the folder on the DR site, respectively. For this, the snapshot created during the previous task is used.
* `post_update_foldername` - This task checks whether the copy was successful. Also, this task removes previous snapshots in case they were present.
* `start_hive` - This task starts the Hive service on the DR site through the Ambari API.
* `copy_pg_airflow_database` - This task copies the Airflow PG database.

# Prerequisites

The prerequisites are specified below.

## HDFS Tasks

* Ensure that Airflow installation has [ssh](https://airflow.apache.org/docs/apache-airflow-providers-ssh/stable/index.html) and [hdfs](https://airflow.apache.org/docs/apache-airflow-providers-apache-hdfs/stable/index.html) providers installed.
* Ensure that both Hadoop installations (main/DR) use the same LDAP/Kerberos.
* Add nodes for both Hadoop sites to all Hadoop nodes in /etc/hosts.
* Enable the SSH login for the Airflow user (preferably Airflow HDFS user created with inv_airflow_user, but also can be some other user with necessary permissions) on the DR site, where namenodes are installed. Note that the SSH connection configuration must be the same for the nodes. For more information, refer to this [example](#example-of-enabling-ssh-login-for-airflow-user-on-hadoop-vm). 
* On the same nodes, in the home directory of the SSH user, add keytab for the HDFS user (`AIRFLOW_SSH_USER_FOR_KINIT` environment variable) with the airflow.keytab name and with necessary permissions. For more information, refer to this [example](#adding-keytab-for-airflow-hdfs-user).
* Add the SSH connection with the ssh_dr name in Airflow. For more information, see [https://airflow.apache.org/docs/apache-airflow-providers-ssh/stable/connections/ssh.html](https://airflow.apache.org/docs/apache-airflow-providers-ssh/stable/connections/ssh.html). Note that for connecting, one of the namenode hosts is used.
* On the main site, make folders to backup snapshottable. For more information, refer to this [example](#making-a-folder-snapshottable).
* On the DR site, create folders with the same addresses and make them snapshottable.
* Give the Airflow HDFS user full permissions for the folders to backup on both sites. This can be done using ranger, for example, add the Airflow user to all-path HDFS policy.
* Add the Airflow DAG to the Airflow image.
* Add webhdfs connections for both `webhdfs_default` and `webhdfs_dr` clusters.
* Specify the following environment variables for Airflow: `DR_FOLDER_LIST` (a comma separated list of folders to backup), `AIRFLOW_SSH_USER_FOR_KINIT` (Kerberos user for kinit on VMs). `AIRFLOW_SSH_USER_FOR_KINIT` here is the LDAP HDFS user for backup. 
**Note**: Since for syncing snapshot mechanism is used (that only works for folders, not files), it is not possible to specify files in the `DR_FOLDER_LIST` variable.
* If required, also specify `DR_DAG_TIMEDELTA` to set the DR DAG time interval. By default, it is set to 2.

## Hive Tasks

For Hive tasks to work, it is necessary to specify the following environment variables:

* `DRHIVEPGHOSTTOBACKUPPASSWORD` - The password of the PG instance containing the main site Hive DATA.
* `DRHIVEPGHOSTTOBACKUPUSER` - The user of the PG instance containing the main site Hive DATA.
* `DRHIVEPGHOSTTOBACKUPDB` - The database name of the PG instance containing the main site Hive DATA.
* `DRHIVEPGHOSTTOBACKUPPORT` - The port of the PG instance containing the main site Hive DATA.
* `DRHIVEPGHOSTTOBACKUP` - The address of the PG instance containing the main site Hive DATA.
* `DRHIVEPGHOSTRESTOREPASSWORD` - The password of the PG instance containing the standby site Hive DATA.
* `DRHIVEPGHOSTRESTOREUSER` - The user of the PG instance containing the standby site Hive DATA.
* `DRHIVEPGHOSTRESTOREDB` - The database name of the PG instance containing the standby site Hive DATA.
* `DRHIVEPGHOSTRESTOREPORT` - The port of the PG instance containing the standby site Hive DATA.
* `DRHIVEPGHOSTRESTORE` - The address of the PG instance containing the standby site Hive DATA.
* `AMBARI_DR_URL` - The address of the standby site Ambari API.
* `AMBARI_DR_USER` - The user of standby site Ambari API.
* `AMBARI_DR_PASSWORD` - The password of the standby site Ambari API.
* `AMBARI_DR_CLUSTER_NAME`- The cluster name of standby site Hadoop.

## Airflow Task

* `DRAIRFLOWPGHOSTTOBACKUPPASSWORD` - The password of the PG instance containing the main site Airflow DATA.
* `DRAIRFLOWPGHOSTTOBACKUPUSER` - The user of the PG instance containing the main site Airflow DATA.
* `DRAIRFLOWPGHOSTTOBACKUPDB` - The Airflow database name on the main site.
* `DRAIRFLOWPGHOSTTOBACKUPPORT` - The port of the PG instance containing the main site Airflow DATA.
* `DRAIRFLOWPGHOSTTOBACKUP` - The address of the PG instance containing the main site Airflow DATA.
* `DRAIRFLOWPGHOSTRESTOREPASSWORD` - The admin password of the PG instance containing the standby site Airflow DATA.
* `DRAIRFLOWPGHOSTRESTOREUSER` - The admin user of the PG instance containing the standby site Airflow DATA.
* `DRAIRFLOWPGHOSTRESTOREDB` - The database name of the PG instance containing the standby site Airflow DATA.
* `DRAIRFLOWPGHOSTRESTOREPORT` - The port of the PG instance containing the DR site Airflow DATA.
* `DRAIRFLOWPGHOSTRESTORE` - The address of the PG instance containing the DR site Airflow DATA.
* `DRAIRFLOWPGHOSTRESTOREOWNER` - The owner user of the DR site Airflow DB. It is recommended for this user to be the same as on the main site.

## Installation Parts

Following is an example of Airflow installation parameters example, including parameters required for the DR configuration.

```yaml
...
extraSecrets:
  sshkey:
    data: |
      sshkey: SSH_KEY_CONTENT_GOES_HERE
  '{{ .Release.Name }}-webhdfs-conn-1':
    stringData: |
      AIRFLOW_CONN_WEBHDFS_DEFAULT: 'hdfs://hdm-0.dr-main.hdfs.addr.qubership.com,hdm-1.dr-main.hdfs.addr.qubership.com:50070'
  '{{ .Release.Name }}-webhdfs-conn-2':
    stringData: |
      AIRFLOW_CONN_WEBHDFS_DR: 'hdfs://hdm-1.dr.hdfs.addr.qubership.com,hdm-2.hdfs.addr.qubership.com:50070'
  '{{ .Release.Name }}-ssh-connection':
    stringData: |
      AIRFLOW_CONN_SSH_DR: 'ssh://airflowdrdaguser@testhost?key_file=%2Fopt%2Fairflow%2Fssh%2Fsshkey'
  'hive-pg-sensitive-envs':
    stringData: |
      DRHIVEPGHOSTTOBACKUPPASSWORD: hivepgpassword_0
      DRHIVEPGHOSTRESTOREPASSWORD: hivepgpassword_1
      AMBARI_DR_PASSWORD: ambari_admin_password
extraEnvFrom: |
  - secretRef:
      name: '{{ .Release.Name }}-webhdfs-conn-1'
  - secretRef:
      name: '{{ .Release.Name }}-webhdfs-conn-2'
  - secretRef:
      name: '{{ .Release.Name }}-ssh-connection'
  - secretRef:
      name: 'hive-pg-sensitive-envs'
...
env:
  - name: DR_FOLDER_LIST
    value: /folder1,folder2
  - name: AIRFLOW_SSH_USER_FOR_KINIT
    value: airflowdrdaguser
  - name: DRHIVEPGHOSTTOBACKUPUSER
    value: postgres
  - name: DRHIVEPGHOSTTOBACKUPDB
    value: maindatabase
  - name: DRHIVEPGHOSTTOBACKUPPORT
    value: 5432
  - name: DRHIVEPGHOSTTOBACKUP
    value: pg-patroni-ro.postgres.svc
  - name: DRHIVEPGHOSTRESTOREUSER
    value: postgres
  - name: DRHIVEPGHOSTRESTOREDB
    value: drsitedatabase
  - name: DRHIVEPGHOSTRESTOREPORT
    value: 5432
  - name: DRHIVEPGHOSTRESTORE
    value: pg-patroni-direct.postgres.svc
  - name: AMBARI_DR_URL
    value: http://hdu-0.dr.hdfs.addr.qubership.com:8080
  - name: AMBARI_DR_USER
    value: admin
  - name: AMBARI_DR_CLUSTER_NAME
    value: drcluster
...
workers:
...
  extraVolumeMounts:
    - name: sshkey
      mountPath: /opt/airflow/ssh/
      readOnly: true
  extraVolumes:
    - name: sshkey
      secret:
        secretName: sshkey
...
```

**Note**: If your LDAP HDFS user (the user specified in the AIRFLOW_SSH_USER_FOR_KINIT environment) does not have permissions to do the distcp operation, for example, when a user does not have permissions to do a chown operation in HDFS, it is possible to use the HDFS system user. To do so, execute the following commands on HDFS namenodes:

```bash
cp /etc/security/keytabs/hdfs.headless.keytab /home/ssh_login_user/
chmod 600 hdfs.headless.keytab
chown ssh_login_user:ssh_login_user hdfs.headless.keytab
```

Here, `ssh_login_user` is the user of your SSH connection to the namenodes. After this, specify the following parameters in the deployer job:

```yaml
...
env:
  - name: KEYTAB_FILE_PATH_FOR_DR_SYNC
    value: hdfs.headless.keytab
  - name: AIRFLOW_SSH_USER_FOR_KINIT
    value: hdfs-dr-cluster-name
...
```

where, `dr-cluster-name` is the name of your DR HDP cluster.

# Adding DR DAG to Image

DR DAG is located at https://github.com/Netcracker/qubership-airflow/blob/main/tests_dags_image/dags/dr_sync_folderv2.py . It is possible to download DR DAG from remote server if it is stored in a ZIP archive. You can download the zip archive with the file using the command, `curl -k  https://remote.server.address.dr_dag.zip -o drdag.zip` . It is possible to put the DAG to your image during the dockerfile build.

# Possible DAG Errors and Fixes

This section provides information on the possible DAG errors and fixes.

**find_correct_ssh_host**:

If an error occurs during this task, check the HDFS connection parameters for both sites (`webhdfs_default` and `webhdfs_dr` connections and Kerberos/hostaliases configuration).

**do_kinit**:

If an error occurs during this task, check the SSH connection parameters. Also, check whether keytab is present on the node.

**verify_folder_state**:

* `Folder not found on main site!` - Check that all folders specified in `DR_FOLDER_LIST` exist on the main site.
* `Folder not found on DR site!` - Check that all folders specified in `DR_FOLDER_LIST` exist on the DR site.
* `Snapshots not found on main site, but DR folder is not empty!` - Check that `webhdfs_dr` actually points to the DR site and not the main site. Also, check that the switchover/failover process is not in progress, otherwise you might want to [restore](#restoring-from-snapshot) one of the latest snapshots on the DR site. If you are sure that the first sync iteration should be in progress, delete everything on the DR site in the backup folder (including snapshots).
* `Snapshots found on main site, not on DR and DR folder is not empty!` - This error specifies that someone has manually deleted snapshots on the DR site. If you are sure that the sync should be in progress, you can delete the contents of the backup folder on the DR site.
* `Latest snapshot numbers are different, manual resolution required!` - This specifies that the latest snapshot numbers are different on the main and DR site. It can happen in case of a switchover/failover. In this case, you can check whether there are snapshots with the same number on the DR and main sites. If so, then restore to this snapshot on the DR site and remove snapshots on the DR/main site with different numbers. However, if needed, it is possible to start the sync process a new by deleting everything in the backup folder on the DR site.

**initialize_folder/update_folder**

If an error occurs during these tasks, roll back to the latest snapshot or clear the state for `initialize` tasks. 
**Note**: Airflow pod restart might leave distcp command running on the node. To avoid any interfering with subsequent DAG runs, kill this process before restoring the latest snapshot. 
To find on which node distcp is running, it is possible to go to the failed task log and check the latest address in the distcp command, for example, it would be addr2 for the command, ```INFO - Running command: hadoop distcp -pugpax -update hdfs://addr1/dr2/.snapshot/snapshot_70 hdfs://addr2/dr2```. You can find running distcp processes with the following command: `ps aux | grep distcp`.

The following error indicates that some other process is being written to the DR site:

```
[2022-03-28 09:06:34,206] {ssh.py:477} WARNING - 22/03/28 09:06:34 WARN tools.DistCp: The target has been modified since snapshot snapshot_3
[2022-03-28 09:06:34,213] {ssh.py:477} WARNING - 22/03/28 09:06:34 ERROR tools.DistCp: Exception encountered 
java.lang.Exception: DistCp sync failed, input options: DistCpOptions{atomicCommit=false, syncFolder=true, deleteMissing=false, ignoreFailures=false, overwrite=false, append=false, useDiff=true, useRdiff=false, fromSnapshot=snapshot_3, toSnapshot=snapshot_4, skipCRC=false, blocking=true, numListstatusThreads=0, maxMaps=20, mapBandwidth=0.0, copyStrategy='uniformsize', preserveStatus=[USER, GROUP, PERMISSION, ACL, XATTR], atomicWorkPath=null, logPath=null, sourceFileListing=null, sourcePaths=[hdfs://hdm-0.dr-main.hdfs.addr.qubership.com/hadoopuser], targetPath=hdfs://hdm-2.dr.hdfs.addr.qubership.com/hadoopuser, filtersFile='null', blocksPerChunk=0, copyBufferSize=8192, verboseLog=false, directWrite=false}, sourcePaths=[hdfs://hdm-0.dr-main.hdfs.addr.qubership.com/hadoopuser/.snapshot/snapshot_4], targetPathExists=true, preserveRawXattrsfalse
	at org.apache.hadoop.tools.DistCp.prepareFileListing(DistCp.java:91)
	at org.apache.hadoop.tools.DistCp.createAndSubmitJob(DistCp.java:205)
	at org.apache.hadoop.tools.DistCp.execute(DistCp.java:182)
	at org.apache.hadoop.tools.DistCp.run(DistCp.java:153)
	at org.apache.hadoop.util.ToolRunner.run(ToolRunner.java:76)
	at org.apache.hadoop.tools.DistCp.main(DistCp.java:432)
```

In this case, also ensure that no processes is being written to the DR folders.

The following error indicates that a HDFS user does not have enough permissions to do the distcp operation with ownership rights:

```
 [2022-06-02, 10:33:19 UTC] {ssh.py:477} WARNING - 22/06/02 10:33:19 INFO mapreduce.Job: Task Id : attempt_1653656082303_0024_m_000001_0, Status : FAILED
[2022-06-02, 10:33:19 UTC] {ssh.py:477} WARNING - Error: org.apache.hadoop.security.AccessControlException: User airflowdrdaguser is not a super user (non-super user cannot change owner).
```

To fix it, it is possible to use the HDFS system user. For more information, see [Prerequisites](#prerequisites).

**post_update_folder**:

`Content is different after the copy!` - For some reason, the content is different after the copy. In this case, it is possible to roll back to the latest snapshot on the DR site.

In case of SSH copy fail, restore the backup folder to the latest snapshot and try again.

**stop_hive**

If an error occurs during this task, verify the following:

* DR site Ambari connection parameters are specified correctly.
* Hive is running on the DR site.

**copy_pg_database**

If an error occurs during this task, verify the following:

* Check connection parameters to Hive DBs.
* Ensure that the database is present on the DR site PG and create it if it is not present.

**start_hive**

If an error occurs during this task, verify the following:

* Check if Hive is stopped on the DR site.
* Check errors in the latest Ambari requests.

# Useful Commands and Examples

Some useful commands and examples are specified below.

## Example of Enabling SSH Login for Airflow User on Hadoop VM

1. Login to the VM using SSH.
2. Switch to the Airflow user (`airflowdrdaguser` in this example).

    ```bash
    sudo su
    su airflowdrdaguser
    ```

3. Generate ssh-key to login.

   ```bash
   cd /home/airflowdrdaguser
   mkdir .ssh
   cd .ssh
   ssh-keygen -b 2048 -t rsa
   {{
       ./key
       <enter>
       <enter>
   }}

   ls -la
   total 8
   drwxr-xr-x. 2 airflowdrdaguser airflowdrdaguser   32 Feb 14 07:34 .
   drwx------. 3 airflowdrdaguser airflowdrdaguser   74 Feb 14 07:33 ..
   -rw-------. 1 airflowdrdaguser airflowdrdaguser 1675 Feb 14 07:34 key
   -rw-r--r--. 1 airflowdrdaguser airflowdrdaguser  444 Feb 14 07:34 key.pub
   ```

4. Move the public key (`key.pub`) to `authorized_keys` : `mv key.pub authorized_keys`.
5. Copy the private key (`key`) to local machine and check the login, `sudo ssh -i ssh_airflow_key airflowdrdaguser@10.118.28.122`.
6. Copy `authorized_keys` to the secondary VM to the `/home/airflowdrdaguser/.ssh` path and check SSH login to the second VM from the Airflow user and the same key.

## Adding Keytab for Airflow HDFS User

It is recommended to use the same user for SSH login and for HDFS (in this example - airflowdrdaguser).

Login to the VM using SSH and use ktutil to create keytab.

   ```bash
   ktutil
   ktutil:  add_entry -password -p airflowdrdaguser -k 1 -e aes256-cts-hmac-sha1-96
   Password for airflowdrdaguser@TEST.DOMAIN:
   ktutil:  wkt airflow.keytab
   ktutil:  exit
   ```

Keytab must be located in the home directory (/home/airflowdrdaguser) and must have permissions only for airflowdrdaguser user: `-rw-------.  1 airflowdrdaguser airflowdrdaguser  174 Feb 14 08:16 airflow.keytab`.

## Restoring from Snapshot

Login to the Hadoop VM. You can get the list of available snapshots with the following command:

```yaml
sudo -u hdfs kinit -kt  /etc/security/keytabs/hdfs.headless.keytab hdfs-your-dr-cluster-name@ldap.realm
sudo -u hdfs hdfs dfs -ls /path/to/backup/folder/.snapshot/
```

To restore, you should pick the snapshot with the latest number. Note that if you are planning on running the DAG again (not Switchover/Failover case), check that the main site has snapshot with the same number (and also delete snapshots with larger numbers if they are present).

There are two possible ways of restoring a snapshot:

* Copy distcp. For more information, see [https://hadoop.apache.org/docs/stable/hadoop-distcp/DistCp.html](https://hadoop.apache.org/docs/stable/hadoop-distcp/DistCp.html). Note that you should use -p option, for example `hadoop distcp -update -p -delete /backupfolder/.snapshot/snapshot_16 /backupfolder`.
* Hadoop cp after deleting the folder content, for example: `sudo -u hdfs hdfs dfs -cp -p -f /path/to/backup/folder/.snapshot/snapshot_18/* /path/to/backup/folder/`

If you want to continue executing the DAG from this step, you should also recreate the snapshot, for example:

```bash
hdfs dfs -deleteSnapshot /backupfolder snapshot_16
hdfs dfs -createSnapshot /backupdolder snapshot_16
```

## Making a Folder Snapshottable

A HDFS folder can be made snapshottable with the following commands:

```bash
sudo -u hdfs kinit -kt /etc/security/keytabs/hdfs.headless.keytab hdfs-clustername@ldap.realm
sudo -u hdfs hdfs dfsadmin -allowSnapshot hdfs://hdfs.namenode.host:8020/folderpath
```
