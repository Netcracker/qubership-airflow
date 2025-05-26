FROM apache/airflow:slim-3.0.1-python3.11

# Arguments
ARG AIRFLOW_USER_HOME=/opt/airflow

USER root

COPY docker/dbaasintegrationpackage /dbaasintegrationpackage

RUN rm -rf /etc/apt/sources.list.d/mysql.list \
    && rm -rf /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get -y dist-upgrade \
    && apt-get --no-install-recommends install -y comerr-dev \
                       unzip \
                       build-essential \
                       manpages-dev \
                       libkrb5-dev \
                       libsasl2-dev libldap2-dev libssl-dev \
    && apt-get clean \
    && chmod 777 -R /dbaasintegrationpackage


#Copy requirements folder
COPY docker/requirements.txt ${AIRFLOW_USER_HOME}/requirements.txt

COPY docker/createdb.py docker/create_dbs_dbaas.py /bin/


USER airflow
# Grant permissions and install python packages
RUN python3 -m pip install -r ${AIRFLOW_USER_HOME}/requirements.txt \
    && cd /dbaasintegrationpackage \
    && python3 -m pip install . \
    && rm -r /dbaasintegrationpackage/*

# WA because prometheus plugin is not working
RUN curl https://raw.githubusercontent.com/drshott/airflow-exporter/refs/heads/airflow3-compat/airflow_exporter/prometheus_exporter.py -o https://raw.githubusercontent.com/drshott/airflow-exporter/refs/heads/airflow3-compat/airflow_exporter/prometheus_exporter.py





