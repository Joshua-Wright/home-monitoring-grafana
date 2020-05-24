FROM python:3.7-alpine

LABEL maintainer="Josh Wright" \
      description="temptop M10i (elitech cloud) to InfluxDB bridge"

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY . /app
WORKDIR /app

CMD ["python3", "-u", "main.py"]
