ARG base_img=ghcr.io/netcracker/qubership-airflow:main

FROM $base_img

# Arguments
ARG AIRFLOW_USER_HOME=/opt/airflow
#
#ENV KAFKA_CONF_DIR=/etc/hadoop/conf

USER root

COPY tests_dags_image/dags/ ${AIRFLOW_USER_HOME}/dags/
COPY tests_dags_image/get_hadoop_conf.sh ${AIRFLOW_USER_HOME}/get_hadoop_conf.sh
COPY tests_dags_image/add_s3_policy.py /bin/
# default-jre and the SASL packages serve the HDFS and Kafka test DAGs. The libxmlsec1-dev packages are
# deliberately absent: xmlsec is pulled only by apache-airflow-providers-amazon[python3-saml], which is not
# installed here and is excluded on Python 3.14. Keeping it would drag in libgnutls28-dev, whose nettle-dev
# dependency cannot resolve against the hardened nettle packages already in the base image.
RUN apt-get --no-install-recommends install -y default-jre sasl2-bin libsasl2-2 libsasl2-modules libsasl2-modules-gssapi-mit \
    && apt-get clean

RUN chmod 0777 ${AIRFLOW_USER_HOME}/get_hadoop_conf.sh \
    && mkdir -p /etc/hadoop/conf \
    && chown airflow /etc/hadoop/conf

#Copy requirements folder
COPY tests_dags_image/requirements.txt ${AIRFLOW_USER_HOME}/test_requirements.txt

USER airflow
# Install apache-airflow-backport-providers-cncf-kubernetes python package
RUN python3 -m pip install -r ${AIRFLOW_USER_HOME}/test_requirements.txt

ENV SPARK_HOME=/home/airflow/.local/lib/python3.14/site-packages/pyspark
ENV HADOOP_USER_NAME=hdfs
ENV HADOOP_CONF_DIR=/etc/hadoop/conf


# COPY docker/idpapiintegrationpackage /idpapiintegrationpackage
# RUN chmod 777 -R /idpapiintegrationpackagecd /idpapiintegrationpackage \
#     && python3 -m pip install . \
#     && rm -r /idpapiintegrationpackage/*
