This section provides information about changing passwords for the Airflow service.

# Change Airflow Web User Interface Password

This sub-section provides information about how to change the Airflow Web user interface passwords.

## Without LDAP

When LDAP is not used, it is possible to change the default user password with recreation of the user using command line in the web UI pod. For more information, refer to the _Official Airflow Documentation_ at [https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/auth-manager/index.html](https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/auth-manager/index.html).

## With LDAP

When LDAP is used, you must change the password via LDAP. You can update the bind user credentials in Airflow configuration via deployer job after the credentials are changed on the LDAP server. The relevant parameter is `apiServer.apiServerConfig`.

# Update PostgreSQL, Redis Passwords, and Kerberos Keytab

You can update the PostgreSQL password via deploy job. However, Airflow does not update the password in the database itself. You must first change the password on the database side. The relevant parameters are as follows:

```
data.metadataConnection.*
```

To update the Redis password, it is necessary to redeploy Airflow. You can use the deploy job in `clean` mode. First, you need to change the password on the Redis side. The following parameter is responsible for it:
 
```
data.brokerUrl
```

Kerberos keytab can be updated via deploy job too using the `kerberos.keytabBase64Content` parameter.

# Upgrade Connections and Variables

The connections and variables created by the chart and stored as environment variables can be updated via chart by setting new values for the respective environments in the chart.

The connections and variables created through the UI (User Interface) or pod terminals must be updated through the UI or pod terminals. For more information, refer to [https://airflow.apache.org/docs/apache-airflow/3.1.1/howto/connection.html](https://airflow.apache.org/docs/apache-airflow/3.1.1/howto/connection.html).

# Web User Interface Role Management

When RBAC is enabled, Airflow provides the following default roles for web UI users: `Admin`, `User`, `Op`, `Viewer`, and `Public`.

It is also possible to create custom roles if required. For more information about roles and permissions, refer to [https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/auth-manager/index.html#](https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/auth-manager/index.html#) and [https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/auth-manager/index.html](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/auth-manager/index.html).

## Add Roles for Users

To add roles for a user via UI, you must login to Airflow as an admin user.
Navigate to **Security > Users > Edit Record**. Enter the role in **Role** text box.

**Note**: It is possible to add a role during user creation. For more information, refer to [https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/cli-ref.html](https://airflow.apache.org/docs/apache-airflow-providers-fab/stable/cli-ref.html].

## Roles with LDAP

When `AUTH_ROLES_MAPPING` is not specified in the `apiServer.apiServerConfig` parameter, there is no synchronization between LDAP roles and web UI Airflow roles since the web UI Airflow roles are configured separately. In this case, the role assigned to the user existing on the LDAP server on the first login in Airflow web UI is specified in the `apiServer.apiServerConfig` parameter in the `AUTH_USER_REGISTRATION_ROLE` variable. You can change this role later via web UI if required. It is also possible to pre-create users with required role using the `airflow users` command. Then, the user is able to login to Airflow with this role provided the user with the same username exists on the LDAP server.

When `AUTH_ROLES_MAPPING` is specified in `apiServer.apiServerConfig` a group mapping is enabled between LDAP and Airflow web UI. Assuming `AUTH_USER_REGISTRATION` is set to `True`, the roles for the users in this case are assigned as per the `AUTH_ROLES_MAPPING` parameter.
