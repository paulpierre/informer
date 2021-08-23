FROM python:3.7-alpine
RUN apk add --no-cache gcc musl-dev
RUN apk update && apk upgrade && \
    apk add git alpine-sdk bash python3
COPY app /usr/local/app
WORKDIR /usr/local/app
RUN pip3 install -r requirements.txt

