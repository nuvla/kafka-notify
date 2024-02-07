FROM python:3.8-alpine as base

FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip3 install --prefix=/install -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local
COPY src/notify* /app/
COPY src/metrics.py /app/
COPY src/run.sh /app/
COPY src/templates /app/templates
RUN mkdir /app/prom_data
ENV PROMETHEUS_MULTIPROC_DIR /app/prom_data

WORKDIR /app
EXPOSE 9140
ENTRYPOINT [ "./run.sh" ]
