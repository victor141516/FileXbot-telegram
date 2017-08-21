FROM alpine:latest

RUN apk --no-cache add \
      bash \
      build-base \
      git \
      libpq \
      openssh-client \
      postgresql-dev \
      python3 \
      py3-pip \
      python3-dev \
      uwsgi-python3

WORKDIR /app

RUN alias python=python3
RUN alias pip=pip3

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
COPY uwsgi.ini /etc/uwsgi.ini


CMD ["uwsgi", "--ini=/etc/uwsgi.ini", "--http-socket=:5000", "--module=filex:app"]