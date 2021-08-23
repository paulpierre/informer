import sys
import os
import json
import re
import asyncio
import gspread
import logging
import build_database
import sqlalchemy as db
from datetime import datetime, timedelta
from random import randrange
from telethon import utils
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InterfaceError, ProgrammingError
from telethon.tl.functions.users import GetFullUserRequest
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
from telethon.errors.rpcerrorlist import FloodWaitError, ChannelPrivateError, UserAlreadyParticipantError
from telethon.tl.functions.channels import  JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from oauth2client.service_account import ServiceAccountCredentials
from models import Account, Channel, ChatUser, Keyword, Message, Monitor, Notification


banner = """
    --------------------------------------------------
        ____      ____                              
       /  _/___  / __/___  _________ ___  ___  _____
       / // __ \/ /_/ __ \/ ___/ __ `__ \/ _ \/ ___/
     _/ // / / / __/ /_/ / /  / / / / / /  __/ /    
    /___/_/ /_/_/  \____/_/  /_/ /_/ /_/\___/_/
    
    --------------------------------------------------
    by @paulpierre updated 2021-08-16 (2019-11-26)
    https://github.com/paulpierre/informer
"""


# Lets set the logging level
logging.getLogger().setLevel(logging.INFO)

class TGInformer:

    def __init__(self,
        db_database = os.environ['MYSQL_DATABASE'],
        db_user = os.environ['MYSQL_USER'],
        db_password = os.environ['MYSQL_PASSWORD'],
        db_ip_address = os.environ['MYSQL_IP_ADDRESS'],
        db_port = os.environ['MYSQL_PORT'],
        tg_account_id = os.environ['TELEGRAM_ACCOUNT_ID'],
        tg_notifications_channel_id = os.environ['TELEGRAM_NOTIFICATIONS_CHANNEL_ID'],
        google_credentials_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS'],
        google_sheet_name = os.environ['GOOGLE_SHEET_NAME'],
        tg_phone_number = os.environ['TELEGRAM_ACCOUNT_PHONE_NUMBER']
    ):

        # ------------------
        # Instance variables
        # ------------------
        self.keyword_list = []
        self.channel_list = []
        self.channel_meta = {}
        self.bot_task = None
        self.KEYWORD_REFRESH_WAIT = 15 * 60 # Every 15 minutes
        self.MIN_CHANNEL_JOIN_WAIT = 30
        self.MAX_CHANNEL_JOIN_WAIT = 120
        self.bot_uptime = 0
        self.client = None
        self.loop = asyncio.get_event_loop()
       

        # --------------
        # Display banner
        # --------------
        print(banner)

        # ------------------------------------------------
        # Check if we're in app engine and set environment
        # ------------------------------------------------

        self.SERVER_MODE = os.environ['ENV']
        self.MYSQL_CONNECTOR_STRING = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_ip_address}:{db_port}/{db_database}?charset=utf8mb4&collation=utf8mb4_general_ci'
        
        logging.info(f'Starting Informer SERVER_MODE: {self.SERVER_MODE}\n')

        # -----------------------------------------
        # Set the channel we want to send alerts to
        # -----------------------------------------
        self.monitor_channel = tg_notifications_channel_id

        if not tg_account_id:
            raise Exception('Must specify "tg_account_id" in informer.env file for bot instance')

        # -----------------------
        # Initialize Google Sheet
        # -----------------------

        logging.info(f'Attempting to access Google Sheet {google_sheet_name}.sheet1 ...\n')

        # Lets check if the file exists

        try:
            if os.path.isfile(google_credentials_path):  

                scope = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive']
                creds = ServiceAccountCredentials.from_json_keyfile_name(google_credentials_path, scope)

                self.gsheet = gspread.authorize(creds)
                self.sheet = self.gsheet.open(google_sheet_name).sheet1
            else:
                self.gsheet = False
        except gspread.exceptions.APIError:
            self.gsheet = False

        # -------------------
        # Initialize database
        # -------------------

        logging.info(f'Setting up MySQL connector with connector string: {self.MYSQL_CONNECTOR_STRING} ... \n')     
        self.engine = db.create_engine(self.MYSQL_CONNECTOR_STRING)  # , echo=True
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # --------------------
        # Load account from DB
        # --------------------
        logging.info(f'Attempting to load user session from database with account_id {tg_account_id} ...\n')

        self.tg_user = None
        try:
            self.account = self.session.query(Account).filter_by(account_id=tg_account_id).first()
        except ProgrammingError as e:
            logging.error(f'Received error {e} \n Database is not set up, setting it up')
            build_database.initialize_db()
            self.account = self.session.query(Account).filter_by(account_id=tg_account_id).first()

        if not self.account:
            raise Exception(f'Invalid account_id {tg_account_id} for bot instance')

        # =======================
        # Initiate bot async loop
        # ========================
        self.loop.run_until_complete(self.bot_interval())

    # =============
    # Get all users
    # =============
    def get_channel_all_users(self, channel_id):
        # TODO: this function is not complete
        channel = self.client.get_entity(PeerChat(channel_id))
        users = self.client.get_participants(channel)
        print(f'total users: {users.total}')
        for user in users:
            if user.username is not None and not user.is_self:
                print(utils.get_display_name(user), user.username, user.id, user.bot, user.verified, user.restricted, user.first_name, user.last_name, user.phone, user.is_self)

    # =====================
    # Get # of participants
    # =====================
    async def get_channel_user_count(self, channel):
        data = await self.client.get_entity(PeerChannel(-channel))
        users = await self.client.get_participants(data)
        return users.total

    # =======================
    # Get channel by group ID
    # =======================
    def get_channel_info_by_group_id(self, id):
        channel = self.client.get_entity(PeerChat(id))

        return {
            'channel_id': channel.id,
            'channel_title': channel.title,
            'is_broadcast': False,
            'is_mega_group': False,
            'channel_access_hash': None,
        }

    # ==========================
    # Get channel by channel URL
    # ==========================
    async def get_channel_info_by_url(self, url):
        logging.info(f'{sys._getframe().f_code.co_name}: Getting channel info with url: {url}')
        channel_hash = utils.parse_username(url)[0]

        # -----------------------------------------
        # Test if we can get entity by channel hash
        # -----------------------------------------
        try:
            channel = await self.client.get_entity(channel_hash)
        except ValueError:
            logging.info(f'{sys._getframe().f_code.co_name}: Not a valid telegram URL: {url}')
            return False
        except FloodWaitError as e:
            logging.info(f'{sys._getframe().f_code.co_name}: Got a flood wait error for: {url}')
            await asyncio.sleep(e.seconds * 2)

        return {
            'channel_id': channel.id,
            'channel_title': channel.title,
            'is_broadcast': channel.broadcast,
            'is_mega_group': channel.megagroup,
            'channel_access_hash': channel.access_hash,
        }

    # ===================
    # Get user info by ID
    # ===================
    async def get_user_by_id(self, user_id=None):
        u = await self.client.get_input_entity(PeerUser(user_id=user_id))
        user = await self.client(GetFullUserRequest(u))

        logging.info(f'{sys._getframe().f_code.co_name}: User ID {user_id} has data:\n {user}\n\n')

        return {
            'username': user.user.username,
            'first_name': user.user.first_name,
            'last_name': user.user.last_name,
            'is_verified': user.user.verified,
            'is_bot': user.user.bot,
            'is_restricted': user.user.restricted,
            'phone': user.user.phone,
        }

    # ==============================
    # Initialize keywords to monitor
    # ==============================
    async def init_keywords(self):
        self.keyword_list = []
        keywords = self.session.query(Keyword).filter_by(keyword_is_enabled=True).all()

        for keyword in keywords:
            self.keyword_list.append({
                'id': keyword.keyword_id,
                'name': keyword.keyword_description,
                'regex': keyword.keyword_regex
            })
            logging.info(f'{sys._getframe().f_code.co_name}: Monitoring keywords: {json.dumps(self.keyword_list, indent=4)}')

    # ===========================
    # Initialize channels to join
    # ===========================
    async def init_monitor_channels(self):

        # ---------------------
        # Let's start listening
        # ---------------------
        @self.client.on(events.NewMessage)
        async def message_event_handler(event):
            await self.filter_message(event)

        # -----------------------------
        # Update the channel data in DB
        # -----------------------------
        current_channels = []
        # Lets iterate through all the open chat channels we have
        async for dialog in self.client.iter_dialogs():
            channel_id = dialog.id

            # As long as it is not a chat with ourselves
            if not dialog.is_user:

                # Certain channels have a prefix of 100, lets remove that
                if str(abs(channel_id))[:3] == '100':
                    channel_id = int(str(abs(channel_id))[3:])

                # Lets add it to the current list of channels we're in
                current_channels.append(channel_id)
                logging.info(f'id: {dialog.id} name: {dialog.name}')

        logging.info(f'{sys._getframe().f_code.co_name}: ### Current channels {json.dumps(current_channels, indent=4)}')

        # -----------------------------------
        # Get the list of channels to monitor
        # -----------------------------------
        self.session = self.Session()
        account = self.session.query(Account).first()
        monitors = self.session.query(Monitor).filter_by(account_id=account.account_id).all()

        channels_to_monitor = []
        for monitor in monitors:
            channel_data = {
                'channel_id': monitor.channel.channel_id,
                'channel_name': monitor.channel.channel_name,
                'channel_title': monitor.channel.channel_title,
                'channel_url': monitor.channel.channel_url,
                'account_id': monitor.channel.account_id,
                'channel_is_megagroup': monitor.channel.channel_is_mega_group,
                'channel_is_group': monitor.channel.channel_is_group,
                'channel_is_private': monitor.channel.channel_is_private,
                'channel_is_broadcast': monitor.channel.channel_is_broadcast,
                'channel_access_hash': monitor.channel.channel_access_hash,
                'channel_size': monitor.channel.channel_size,
                'channel_is_enabled': monitor.channel.channel_is_enabled,
                'channel_tcreate': monitor.channel.channel_tcreate
            }

            if monitor.channel.channel_is_enabled is True:
                channels_to_monitor.append(channel_data)
        self.session.close()

        # -------------------------------
        # Iterate through channel objects
        # -------------------------------
        for channel in channels_to_monitor:
            self.session = self.Session()
            channel_obj = self.session.query(Channel).filter_by(channel_id=channel['channel_id']).first()

            # -------------------------------
            # We have sufficient channel data
            # -------------------------------
            if channel['channel_id']:
                self.channel_list.append(channel['channel_id'])
                logging.info(f"Adding channel {channel['channel_name']} to monitoring w/ ID: {channel['channel_id']} hash: {channel['channel_access_hash']}")

                self.channel_meta[channel['channel_id']] = {
                    'channel_id': channel['channel_id'],
                    'channel_title': channel['channel_title'],
                    'channel_url': channel['channel_url'],
                    'channel_size': 0,
                    'channel_texpire': datetime.now() + timedelta(hours=3)
                }

            else:
                # ------------------------
                # If not grab channel data
                # ------------------------
                if channel['channel_url'] and '/joinchat/' not in channel['channel_url']:
                    o = await self.get_channel_info_by_url(channel['channel_url'])

                    # -----------------------------
                    # If channel is invalid, ignore
                    # -----------------------------
                    if o is False:
                        logging.error(f"Invalid channel URL: {channel['channel_url']}")
                        continue

                    logging.info(f"{sys._getframe().f_code.co_name}: ### Successfully identified {channel['channel_name']}")

                # -------------------------
                # If the channel is a group
                # -------------------------
                elif channel['channel_is_group']:
                    o = await self.get_channel_info_by_group_id(channel['channel_id'])

                    logging.info(f"{sys._getframe().f_code.co_name}: ### Successfully identified {channel['channel_name']}")
                
                else:
                    logging.info(f"{sys._getframe().f_code.co_name}: Unable to indentify channel {channel['channel_name']}")
                    continue

                channel_obj.channel_id = o['channel_id']
                channel_obj.channel_title = o['channel_title']
                channel_obj.channel_is_broadcast = o['is_broadcast']
                channel_obj.channel_is_mega_group = o['is_mega_group']
                channel_obj.channel_access_hash = o['channel_access_hash']


                self.channel_meta[o['channel_id']] = {
                    'channel_id': o['channel_id'],
                    'channel_title': o['channel_title'],
                    'channel_url': channel['channel_url'],
                    'channel_size': 0,
                    'channel_texpire':datetime.now() + timedelta(hours=3)
                }


            # -------------------------------
            # Determine is channel is private
            # -------------------------------
            channel_is_private = True if (channel['channel_is_private'] or '/joinchat/' in channel['channel_url']) else False
            if channel_is_private:
                logging.info(f'channel_is_private: {channel_is_private}')

            # ------------------------------------------
            # Join if public channel and we're not in it
            # ------------------------------------------
            if channel['channel_is_group'] is False and channel_is_private is False and channel['channel_id'] not in current_channels:
                logging.info(f"{sys._getframe().f_code.co_name}: Joining channel: {channel['channel_id']} => {channel['channel_name']}")
                try:
                    await self.client(JoinChannelRequest(channel=await self.client.get_entity(channel['channel_url'])))
                    sec = randrange(self.MIN_CHANNEL_JOIN_WAIT, self.MAX_CHANNEL_JOIN_WAIT)
                    logging.info(f'sleeping for {sec} seconds')
                    await asyncio.sleep(sec)
                except FloodWaitError as e:
                    logging.info(f'Received FloodWaitError, waiting for {e.seconds} seconds..')
                    # Lets wait twice as long as the API tells us for posterity
                    await asyncio.sleep(e.seconds * 2)

                except ChannelPrivateError as e:
                    logging.info('Channel is private or we were banned bc we didnt respond to bot')
                    channel['channel_is_enabled'] = False

            # ------------------------------------------
            # Join if private channel and we're not in it
            # ------------------------------------------
            elif channel_is_private and channel['channel_id'] not in current_channels:
                channel_obj.channel_is_private = True
                logging.info(f"{sys._getframe().f_code.co_name}: Joining private channel: {channel['channel_id']} => {channel['channel_name']}")

                # -------------------------------------
                # Join private channel with secret hash
                # -------------------------------------
                channel_hash = channel['channel_url'].replace('https://t.me/joinchat/', '')

                try:
                    await self.client(ImportChatInviteRequest(hash=channel_hash))

                    # ----------------------
                    # Counter FloodWaitError
                    # ----------------------
                    sec = randrange(self.MIN_CHANNEL_JOIN_WAIT, self.MAX_CHANNEL_JOIN_WAIT)
                    logging.info(f'sleeping for {sec} seconds')
                    await asyncio.sleep(sec)
                except FloodWaitError as e:
                    logging.info(f'Received FloodWaitError, waiting for {e.seconds} seconds..')
                    await asyncio.sleep(e.seconds * 2)
                except ChannelPrivateError as e:
                    logging.info('Channel is private or we were banned bc we didnt respond to bot')
                    channel['channel_is_enabled'] = False
                except UserAlreadyParticipantError as e:
                    logging.info('Already in channel, skipping')
                    self.session.close()
                    continue

            # ---------------------------------
            # Rollback session if we get a dupe
            # ---------------------------------
            try:
                self.session.commit()
            except IntegrityError:
                self.session.rollback()
            except InterfaceError:
                pass
            self.session.close()

        logging.info(f"{sys._getframe().f_code.co_name}: Monitoring channels: {json.dumps(self.channel_list, indent=4)}")
        logging.info(f'Channel METADATA: {self.channel_meta}')


    # ===========================
    # Filter the incoming message
    # ===========================
    async def filter_message(self, event):
        # If this is a channel, grab the channel ID
        if isinstance(event.message.to_id, PeerChannel):
            channel_id = event.message.to_id.channel_id
        # If this is a group chat, grab the chat ID
        elif isinstance(event.message.to_id, PeerChat):
            channel_id = event.message.chat_id
        else:
            # Message comes neither from a channel or chat, lets skip
            return

        # Channel values from the API are signed ints, lets get ABS for consistency
        channel_id = abs(channel_id)

        message = event.raw_text

        # Lets check to see if the message comes from our channel list
        if channel_id in self.channel_list:

            # Lets iterate through our keywords to monitor list
            for keyword in self.keyword_list:

                # If it matches the regex then voila!
                if re.search(keyword['regex'], message, re.IGNORECASE):
                    logging.info(
                        f'Filtering: {channel_id}\n\nEvent raw text: {event.raw_text} \n\n Data: {event}')

                    # Lets send the notification with all the pertinent information in the params
                    await self.send_notification(
                        message_obj=event.message,
                        event=event, sender_id=event.sender_id,
                        channel_id=channel_id,
                        keyword=keyword['name'],
                        keyword_id=keyword['id']
                    )

    # ====================
    # Handle notifications
    # ====================
    async def send_notification(self, sender_id=None, event=None, channel_id=None, keyword=None, keyword_id=None, message_obj=None):
        message_text = message_obj.message

        # Lets set the meta data
        is_mention = message_obj.mentioned
        is_scheduled = message_obj.from_scheduled
        is_fwd = False if message_obj.fwd_from is None else True
        is_reply = False if message_obj.reply_to_msg_id is None else True
        is_bot = False if message_obj.via_bot_id is None else True

        if isinstance(message_obj.to_id, PeerChannel):
            is_channel = True
            is_group = False
            is_private = False
        elif isinstance(message_obj.to_id, PeerChat):
            is_channel = False
            is_group = True
            is_private = False
        else:
            is_channel = False
            is_group = False
            is_private = False

        # We track the channel size and set it to expire after sometime, if it does we update the participant size
        if channel_id in self.channel_meta and self.channel_meta[channel_id]['channel_size'] == 0 or datetime.now() > self.channel_meta[channel_id]['channel_texpire']:
            logging.info('refreshing the channel information')
            channel_size = await self.get_channel_user_count(channel_id)
        else:
            channel_size = self.channel_meta[channel_id]['channel_size']

        # Lets get who sent the message
        sender = await event.get_sender()
        sender_username = sender.username

        channel_id = abs(channel_id)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Set the message for the notification we're about to send in our monitor channel
        message = f'⚠️ "{keyword}" mentioned by {sender_username} in => "{self.channel_meta[channel_id]["channel_title"]}" url: {self.channel_meta[channel_id]["channel_url"]}\n\n Message:\n"{message_text}\ntimestamp: {timestamp}'
        logging.info(f'{sys._getframe().f_code.co_name} Sending notification {message}')

        # ----------------
        # Send the message
        # ----------------
        await self.client.send_message(self.monitor_channel, message)

        # -------------------------
        # Write to the Google Sheet
        # -------------------------
        if self.gsheet is True:
            self.sheet.append_row([
                sender_id,
                sender_username,
                channel_id,
                self.channel_meta[channel_id]['channel_title'],
                self.channel_meta[channel_id]['channel_url'],
                keyword,
                message_text,
                is_mention,
                is_scheduled,
                is_fwd,
                is_reply,
                is_bot,
                is_channel,
                is_group,
                is_private,
                channel_size,
                timestamp
            ])

        # --------------
        # Add user to DB
        # --------------
        o = await self.get_user_by_id(sender_id)

        self.session = self.Session()
        if not bool(self.session.query(ChatUser).filter_by(chat_user_id=sender_id).all()):

            self.session.add(ChatUser(
                chat_user_id=sender_id,
                chat_user_is_bot=o['is_bot'],
                chat_user_is_verified=o['is_verified'],
                chat_user_is_restricted=o['is_restricted'],
                chat_user_first_name=o['first_name'],
                chat_user_last_name=o['last_name'],
                chat_user_name=o['username'],
                chat_user_phone=o['phone'],
                chat_user_tlogin=datetime.now(),
                chat_user_tmodified=datetime.now()
            ))

        # -----------
        # Add message
        # -----------
        msg = Message(
            chat_user_id=sender_id,
            account_id=self.account.account_id,
            channel_id=channel_id,
            keyword_id=keyword_id,
            message_text=message_text,
            message_is_mention=is_mention,
            message_is_scheduled=is_scheduled,
            message_is_fwd=is_fwd,
            message_is_reply=is_reply,
            message_is_bot=is_bot,
            message_is_group=is_group,
            message_is_private=is_private,
            message_is_channel=is_channel,
            message_channel_size=channel_size,
            message_tcreate=datetime.now()
        )
        self.session.add(msg)

        self.session.flush()

        message_id = msg.message_id

        self.session.add(Notification(
            keyword_id=keyword_id,
            message_id=message_id,
            channel_id=channel_id,
            account_id=self.account.account_id,
            chat_user_id=sender_id
        ))

        # -----------
        # Write to DB
        # -----------
        try:
            self.session.commit()
        except IntegrityError:
            pass
        self.session.close()


    async def update_keyword_list(self):
        # ------------------------------
        # Lets update keywords in memory
        # ------------------------------
        # TODO: functionality to poll the DB for new keywords and refresh in memory
        logging.info('### updating keyword_list')
        pass

    def stop_bot_interval(self):
        self.bot_task.cancel()

   
    # ==============
    # Main coroutine
    # ==============           
    async def bot_interval(self): 

        # ----------------------
        # Telegram service login
        # ----------------------
        logging.info(f'Logging in with account # {self.account.account_phone} ... \n')
        session_file = 'session/' + self.account.account_phone.replace('+', '')
        self.client = TelegramClient(session_file, self.account.account_api_id, self.account.account_api_hash)
    
        # -----------------------
        # Authorize from terminal
        # -----------------------
        # TODO: automate authcode with the Burner API
        await self.client.start(phone=f'{self.account.account_phone}')
        
        if not await self.client.is_user_authorized():
            logging.info(f'Client is currently not logged in, please sign in! Sending request code to {self.account.account_phone}, please confirm on your mobile device')
            await self.client.send_code_request(self.account.account_phone)
            self.tg_user = await self.client.sign_in(self.account.account_phone, input('Enter code: '))
        
        self.tg_user = await self.client.get_me()
      
        await self.init_keywords()
        await self.init_monitor_channels()
        count = 0
        while True:
            count +=1
            logging.info('### {count} Running bot interval')
            await self.init_keywords()
            await asyncio.sleep(self.KEYWORD_REFRESH_WAIT)

    