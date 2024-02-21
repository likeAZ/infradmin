FROM python:3.11
ENV APP_DIR=/usr/src/app/infradmin/
WORKDIR ${APP_DIR}
RUN mkdir "conf"
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY bin/* ./
CMD [ "python", "./main.py" ]
