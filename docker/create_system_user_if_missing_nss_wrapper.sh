

function create_system_user_if_missing() {
    if ! whoami &> /dev/null; then
        NSS_WRAPPER_PASSWD="$(mktemp)"
        export LD_PRELOAD='/usr/lib/libnss_wrapper.so'
        echo "${USER_NAME:-default}:x:$(id -u):0:${USER_NAME:-default} user:${AIRFLOW_USER_HOME_DIR}:/sbin/nologin" \
            >> "$NSS_WRAPPER_PASSWD"
      export HOME="${AIRFLOW_USER_HOME_DIR}"
    fi
}

