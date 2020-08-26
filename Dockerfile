FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

ENV SCAN_DIRS "['/scan']"
ENV FREE "10 GB"
ENV THRESHOLD "15 GB"
ENV LOG_LEVEL "INFO"

ADD . .

ENTRYPOINT [ "python3", "src/main.py" ]

CMD ["--directory ${SCAN_DIRS}", "--free ${FREE}", "--threshold ${THRESHOLD}", "--log_level ${LOG_LEVEL}"]