FROM python:3.11
WORKDIR /usr/src/app/infradmin
RUN mkdir "conf"
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY bin/* ./
CMD [ "python", "./main.py" ]
