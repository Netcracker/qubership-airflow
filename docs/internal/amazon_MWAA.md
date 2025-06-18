This documents provides the details relating to Amazon MWAA. For more information, refer to [https://aws.amazon.com/managed-workflows-for-apache-airflow/](https://aws.amazon.com/managed-workflows-for-apache-airflow/).

**Note**: In Amazon MWAA, a set of possible Airflow versions is predefined, for example, by the time Airflow 2.6.1 was released, Amazon MWAA's latest possible version was only 2.5.1.

# Deploying Amazon MWAA

## Creating S3 Bucket for MWAA

Firstly, it is necessary to create an S3 bucket (additional permissions are required). For more information, refer to [https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-s3-bucket.html](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-s3-bucket.html). 

Important takeaways:

* Bucket name must be DNS-compliant.
* Public access must be blocked.
* Bucket versioning must be enabled.

## Populating the Bucket for MWAA

It is possible to add your DAGs in the bucket and the **requirements.txt** file with Python libraries to install. The **requirements.txt** file example for 2.5.1 version can be found at [https://github.com/aws/aws-mwaa-local-runner/blob/v2.5.1/requirements/requirements.txt](https://github.com/aws/aws-mwaa-local-runner/blob/v2.5.1/requirements/requirements.txt); the file can be found in the repository for other Airflow versions too. Note that internet access might be required for installing custom python libraries with the **requirements.txt** file.

## Creating VPC

If you do not have enough permission to create VPC automatically, it is necessary to pre-create one or configure an existing one to have the same parameters as described in the Amazon documentation at [https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html](https://docs.aws.amazon.com/mwaa/latest/userguide/vpc-create.html).

## Creating a Role

If you do not have enough permissions to create a role for MWAA automatically, it must be pre-created. For more information about Airflow execution role, refer to [https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html](https://docs.aws.amazon.com/mwaa/latest/userguide/mwaa-create-role.html).

## MWAA Configuration and Creation

During the configuration, it is necessary to specify the S3 bucket with DAGs location, **requirements.txt** location, and other files. 

![mwaabucketconfig.png](/docs/dev/mwaabucketconfig.png)


It is also possible to specify a pre-created execution role/security group/VPC along with other parameters.

If the creation is not successful, try automatic creation of execution role/security group/VPC. Also try creating MWAA with a user having more permissions.

If no internet access is selected, the UI will be available with the same authentication as to AWS itself.
