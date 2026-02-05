FROM rclone/rclone:1.73.0

COPY rclone-image/entrypoint.sh /entrypoint.sh

RUN mkdir /git \
    && mkdir /unpacked_dags \
    && chmod 777 /git \
    && chmod -R 777 /data \
    && chmod 777 /unpacked_dags \
    && chmod 777 /entrypoint.sh

ENV USER_UID=1008 \
    USER_NAME=rclone-user

RUN adduser -S -u ${USER_UID} ${USER_NAME}

USER rclone-user

ENTRYPOINT ["/bin/sh", "/entrypoint.sh"]
