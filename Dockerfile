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

COPY . /app/
WORKDIR /app

RUN alias python=python3
RUN alias pip=pip3
RUN mv uwsgi.ini /etc/
RUN pip3 install -r requirements.txt


CMD ["uwsgi", "--ini=/etc/uwsgi.ini", "--http-socket=:5000", "--module=filex:app"]