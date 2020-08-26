FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ENV SCAN_DIRS "['/scan']"
ENV FREE "10G"
ENV THRESHOLD "15G"
ENV LOG_LEVEL "INFO"

ADD . .

CMD python3 src/main.py --directories $SCAN_DIRS --free $FREE --threshold $THRESHOLD --log_level $LOG_LEVEL