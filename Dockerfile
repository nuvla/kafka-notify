FROM python:3.8-alpine as base

FROM base as builder
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip3 install --prefix=/install -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local
COPY src/notify* /app/
COPY src/run.sh /app/
COPY src/templates /app/templates

WORKDIR /app
ENTRYPOINT [ "./run.sh" ]
