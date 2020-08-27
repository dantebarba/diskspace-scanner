FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ARG BUILD_VERSION=''

ENV BUILD_VERSION ${BUILD_VERSION}
ENV SCAN_DIRS "['/scan']"
ENV FREE "10G"
ENV THRESHOLD "15G"
ENV LOG_LEVEL "INFO"
ENV DRY_RUN True
ENV AUTH_PASSWORD ''
ENV AUTH_USER ''
ENV RCLONE_URL http://localhost:5572
ENV SOURCE_REMOTE '/'
ENV DEST_REMOTE '/'
ENV REMOTE_PATH_MAPPING "{}"
ENV SCHEDULED ''
ENV TZ 'America/Argentina/Buenos_Aires'

ADD . .

CMD python3 src/main.py --directories "$SCAN_DIRS" --free $FREE --threshold $THRESHOLD --log_level $LOG_LEVEL --rclone_url $RCLONE_URL --auth_user $AUTH_USER --auth_password $AUTH_PASSWORD --dry_run $DRY_RUN --source_remote $SOURCE_REMOTE --dest_remote $DEST_REMOTE --remote_path_mapping "$REMOTE_PATH_MAPPING" --scheduled "$SCHEDULED"