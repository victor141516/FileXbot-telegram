FROM python:2-alpine

RUN apk --no-cache add \
      build-base \
      git \
      libpq \
      postgresql-dev 

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["gunicorn", "-w4", "-b :5000", "filex:bot"]
