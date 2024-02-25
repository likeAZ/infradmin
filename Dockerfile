FROM python:3.11
ENV APP_DIR=/usr/src/app/infradmin/
WORKDIR ${APP_DIR}
RUN apt-get update && apt-get install -y \
    rsync \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir "conf" "backup"
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY bin/ .
COPY conf/ conf/
CMD [ "python", "./main.py" ]
