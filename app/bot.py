import sys
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

# Lets set the logging level
logging.getLogger().setLevel(logging.INFO)

# -----------------
# Load the ENV file
# -----------------
env_file = 'informer.env' if os.path.isfile('informer.env') else '../informer.env'
logging.info(f'env_file: {env_file}')
dotenv_path = Path(env_file)
load_dotenv(dotenv_path=dotenv_path)

from informer import TGInformer


# ===========
# Quick setup
# ===========

#   virtualenv venv
#   source venv/bin/activate
#   pip install -r requirements.txt
#   python3 informer.py <account_id>

# Read more: https://github.com/paulpierre/informer/

try:
    account_id = sys.argv[1]
except:
    raise Exception('informer.py <account_id> - account_id is a required param')

if not account_id:
    raise Exception('Account ID required')

if __name__ == '__main__':

    informer = TGInformer(
        db_database = os.environ['MYSQL_DATABASE'],
        db_user = os.environ['MYSQL_USER'],
        db_password = os.environ['MYSQL_PASSWORD'],
        db_ip_address = os.environ['MYSQL_IP_ADDRESS'],
        db_port = os.environ['MYSQL_PORT'],
        tg_account_id = os.environ['TELEGRAM_ACCOUNT_ID'],
        tg_notifications_channel_id = os.environ['TELEGRAM_NOTIFICATIONS_CHANNEL_ID'],
        google_credentials_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
        google_sheet_name = os.environ['GOOGLE_SHEET_NAME']
    )
    informer.init()
