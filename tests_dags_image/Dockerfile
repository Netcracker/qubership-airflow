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
# https://github.com/xmlsec/python-xmlsec/issues/336
# libxmlsec1-dev pulls libgnutls28-dev, which pulls nettle-dev. Debian orders the hardened runtime
# packages already in the base image (libnettle8t64, libhogweed6t64) 3.10.1-1+dhi1 above the
# 3.10.1-1+deb13u0+dhi1 that nettle-dev requires, so apt refuses the implied downgrade and the
# transaction fails with unmet dependencies. Allow the downgrade for this install.
RUN apt-get --no-install-recommends install -y --allow-downgrades default-jre sasl2-bin libsasl2-2 libsasl2-modules libsasl2-modules-gssapi-mit pkg-config libxml2-dev libxmlsec1-dev libxmlsec1-openssl \
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
