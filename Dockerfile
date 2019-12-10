FROM python:3.7-alpine
RUN apk add --no-cache gcc musl-dev
RUN apk update && apk upgrade && \
    apk add git alpine-sdk bash python
RUN mkdir /usr/informer
WORKDIR /usr/informer
COPY . /usr/informer

# Lets set the environment variable in the container
ENV GAE_INSTANCE=prod

RUN pip install -I Jinja2==2.10.3
RUN pip install -I SQLAlchemy==1.3.11
RUN pip install -I Werkzeug==0.16.0
RUN pip install -I pytz==2019.3
RUN pip install -I sqlalchemy-migrate==0.13.0
RUN pip install -I requests==2.7.0
RUN pip install -I Flask==1.1.1
RUN pip install -I Telethon==1.10.8
RUN pip install -I mysql-connector-python==8.0.18
RUN pip install -I gspread==3.1.0
RUN pip install -I oauth2client==4.1.3

# Comment this out if you plan to run the script inside docker with ENTRYPOINT. Replace 1234567 with your Telegram API user ID
CMD ["python","bot.py","1234567"]
