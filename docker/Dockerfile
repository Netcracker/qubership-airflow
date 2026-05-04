FROM apache/airflow:slim-3.2.1-python3.11

# Arguments
ARG AIRFLOW_USER_HOME=/opt/airflow

USER root

COPY docker/dbaasintegrationpackage /dbaasintegrationpackage
COPY docker/keycloakrbacintegrationpackage /keycloakrbacintegrationpackage

RUN rm -rf /etc/apt/sources.list.d/mysql.list \
    && rm -rf /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get -y dist-upgrade \
    && apt-get --no-install-recommends install -y comerr-dev \
                       unzip \
                       build-essential \
                       manpages-dev \
                       libkrb5-dev \
                       libsasl2-dev libldap2-dev libssl-dev libnss-wrapper \
    && apt-get clean \
    && chmod 777 -R /dbaasintegrationpackage \
    && chmod 777 -R /keycloakrbacintegrationpackage


#Copy requirements folder
COPY docker/requirements.txt ${AIRFLOW_USER_HOME}/requirements.txt

COPY docker/createdb.py docker/create_dbs_dbaas.py /bin/

COPY docker/create_system_user_if_missing_nss_wrapper create_system_user_if_missing_nss_wrapper

RUN sed -i '/function create_system_user_if_missing() {/c\function create_system_user_if_missing_old() {' /entrypoint \
    && sed -e '/function create_system_user_if_missing_old/{r create_system_user_if_missing_nss_wrapper' -e 'N}' /entrypoint >> /tmp/entrypoint \
    && cp /tmp/entrypoint /entrypoint \
    && rm /tmp/entrypoint create_system_user_if_missing_nss_wrapper


USER airflow
# Grant permissions and install python packages
RUN python3 -m pip install -r ${AIRFLOW_USER_HOME}/requirements.txt \
    && cd /dbaasintegrationpackage \
    && python3 -m pip install . \
    && rm -r /dbaasintegrationpackage/* \
    && cd /keycloakrbacintegrationpackage \
    && python3 -m pip install . \
    && rm -r /keycloakrbacintegrationpackage/*


