
import csv
import sys
import os
import logging
from dotenv import load_dotenv
from pathlib import Path
import sqlalchemy as db
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from models import Account, Channel, ChatUser, Keyword, Message, Monitor, Notification
logging.getLogger().setLevel(logging.INFO)

# -----------------
# Load the ENV file
# -----------------
dotenv_path = Path('informer.env')
load_dotenv(dotenv_path=dotenv_path)

Session = None
session = None
SERVER_MODE = None
engine = None

"""
This script will build our your database for you
"""

def init_db():
    global session, SERVER_MODE, engine
    logging.info(f'{sys._getframe().f_code.co_name}: Initializing the database')
    Account.metadata.create_all(engine)
    ChatUser.metadata.create_all(engine)
    Channel.metadata.create_all(engine)
    Message.metadata.create_all(engine)
    Keyword.metadata.create_all(engine)
    Monitor.metadata.create_all(engine)
    Notification.metadata.create_all(engine)
    session.close()


"""
    Lets setup the channels to monitor in the database
"""
def init_data():

    global session, SERVER_MODE, engine
    session = Session()
    init_add_account()
    init_add_channels()
    init_add_keywords()
    init_add_monitors()
    session.close()

def init_add_account():

    global session, SERVER_MODE, engine

    logging.info(f'{sys._getframe().f_code.co_name}: Adding bot account')

    BOT_ACCOUNTS = [
    
        Account(
            account_id=os.environ['TELEGRAM_ACCOUNT_ID'],
            account_api_id=os.environ['TELEGRAM_API_APP_ID'],
            account_api_hash=os.environ['TELEGRAM_API_HASH'],
            account_is_bot=False,
            account_is_verified=False,
            account_is_restricted=False,
            account_first_name=os.environ['TELEGRAM_ACCOUNT_FIRST_NAME'],
            account_last_name=os.environ['TELEGRAM_ACCOUNT_LAST_NAME'],
            account_user_name=os.environ['TELEGRAM_ACCOUNT_USER_NAME'],
            account_phone=os.environ['TELEGRAM_ACCOUNT_PHONE_NUMBER'],  # Enter your burner phone number here
            account_is_enabled=True,
            account_tlogin=datetime.now(),
            account_tcreate=datetime.now(),
            account_tmodified=datetime.now()),

    ]

    for account in BOT_ACCOUNTS:
        session.add(account)

    session.commit()

def init_add_channels():
    global session, SERVER_MODE, engine

    # Lets get the first account
    account = session.query(Account).first()

    CHANNELS = [
        {
            'channel_name': 'Informer monitoring',
            'channel_id': os.environ['TELEGRAM_NOTIFICATIONS_CHANNEL_ID'],  # Enter your own Telegram channel ID for monitoring here
            'channel_url': os.environ['TELEGRAM_NOTIFICATIONS_CHANNEL_URL'],
            'channel_is_private': False if os.environ['TELEGRAM_NOTIFICATIONS_CHANNEL_IS_PRIVATE']=='0' else True
        },

    ]

    # Lets import the CSV with the channel list
    with open(os.environ['TELEGRAM_CHANNEL_MONITOR_LIST']) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count != 0:
                print(f'Adding channel {row[0]} => {row[1]}')
                CHANNELS.append({
                    'channel_name': row[0],
                     'channel_url': row[1]
                                 })
            line_count += 1

    
    logging.info(f'Inserting {line_count} channels to database')

    for channel in CHANNELS:
        logging.info(f"{sys._getframe().f_code.co_name}: Adding channel {channel['channel_name']} to database")

        channel_url = channel['channel_url'] if 'channel_url' in channel else None
        channel_id = channel['channel_id'] if 'channel_id' in channel else None
        channel_is_group = channel['channel_is_group'] if 'channel_is_group' in channel else False
        channel_is_private = channel['channel_is_private'] if 'channel_is_private' in channel else False

        session.add(Channel(
            channel_name=channel['channel_name'],
            channel_url=channel_url,
            channel_id=channel_id,
            account_id=account.account_id,
            channel_tcreate=datetime.now(),
            channel_is_group=channel_is_group,
            channel_is_private=channel_is_private
        ))
    session.commit()

# ==============================
# The keywords we want to spy on
# ==============================
def init_add_keywords():
    global session, SERVER_MODE, engine
    KEYWORDS = [
        {
            'keyword_description': 'Binance',
            'keyword_regex': '(binance|bnb)'
        },
        {
            'keyword_description': 'Huobi',
            'keyword_regex': '(huobi)'
        },
        {
            'keyword_description': 'Bittrex',
            'keyword_regex': '(bittrex)'
        },
        {
            'keyword_description': 'Bitfinex',
            'keyword_regex': '(bitfinex)'
        },
        {
            'keyword_description': 'Coinbase',
            'keyword_regex': '(coinbase)'
        },
        {
            'keyword_description': 'Kraken',
            'keyword_regex': '(kraken)'
        },
        {
            'keyword_description': 'Poloniex',
            'keyword_regex': '(poloniex)'
        },

    ]

    for keyword in KEYWORDS:
        logging.info(f"{sys._getframe().f_code.co_name}: Adding keyword {keyword['keyword_description']} to the database")

        session.add(Keyword(
            keyword_description=keyword['keyword_description'],
            keyword_regex=keyword['keyword_regex'],
            keyword_tmodified=datetime.now(),
            keyword_tcreate=datetime.now()
        ))
    session.commit()


# ======================================
# Lets add the channels we want to watch
# ======================================
def init_add_monitors():
    global session, SERVER_MODE, engine
    # Lets assign them all
    accounts = session.query(Account).all()
    channels = session.query(Channel).all()
    account_index = 0
    channel_count = 0

    for channel in channels:
        if account_index in accounts:
            account = accounts[account_index]
            logging.info(f'{sys._getframe().f_code.co_name}: Adding monitoring to channel {channel.channel_name} with account_id {account.account_id} to the database')
            session.add(Monitor(
                channel_id=channel.id,
                account_id=account.account_id,
                monitor_tcreate=datetime.now(),
                monitor_tmodified=datetime.now()
            ))
            channel_count += 1
            if channel_count > 500:
                account_index += 1
                channel_count = 0
    session.commit()


def initialize_db():
    global session, SERVER_MODE, engine, Session
    DATABASE_NAME = os.environ['MYSQL_DATABASE']

    db_database = os.environ['MYSQL_DATABASE']
    db_user = os.environ['MYSQL_USER']
    db_password = os.environ['MYSQL_PASSWORD']
    db_ip_address = os.environ['MYSQL_IP_ADDRESS']
    db_port = os.environ['MYSQL_PORT']
    SERVER_MODE = os.environ['ENV']
    MYSQL_CONNECTOR_STRING = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_ip_address}:{db_port}/{db_database}?charset=utf8mb4&collation=utf8mb4_general_ci'

    engine = db.create_engine(MYSQL_CONNECTOR_STRING, echo=True)
    Session = sessionmaker(bind=engine)
    session = None
    session = Session()
    session.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME} CHARACTER SET 'utf8mb4' COLLATE 'utf8mb4_unicode_ci';")
    session.execute('commit')
    #session.close()

    # engine = db.create_engine(f'{MYSQL_CONNECTOR_STRING}?charset=utf8mb4', echo=True)
    # Session = sessionmaker(bind=engine)
    # session = None
    # session = Session()

    # A hack to support unicode for emojis
    session.execute('SET NAMES "utf8mb4" COLLATE "utf8mb4_unicode_ci"')
    session.execute(f'ALTER DATABASE {DATABASE_NAME} CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;')
    session.execute('commit')

    init_db()
    init_data()


if __name__ == '__main__':
    initialize_db()
