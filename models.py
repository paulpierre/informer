from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Account(Base):
    """
    The telegram account being used as the sock puppet
    """
    __tablename__ = 'account'
    id = Column(Integer, index=True, primary_key=True, autoincrement=True)
    account_id = Column(Integer, nullable=False, index=True)
    account_api_id = Column(Integer, default=None, nullable=False)
    account_api_hash = Column(String(50), default=None, nullable=False)
    account_is_bot = Column(Boolean(), default=None)
    account_is_verified = Column(Boolean(), default=None)
    account_is_restricted = Column(Boolean(), default=None)
    account_first_name = Column(String(50), default=None)
    account_last_name = Column(String(50), default=None)
    account_user_name = Column(String(100), default=None, nullable=False)
    account_phone = Column(String(25), unique=True, default=None, nullable=False)
    account_tlogin = Column(DateTime, default=None)
    account_is_enabled = Column(Boolean(), default=True)
    account_tcreate = Column(DateTime, default=datetime.now())
    account_tmodified = Column(DateTime, default=datetime.now())

    channels = relationship('Channel', back_populates='accounts')
    messages = relationship('Message', back_populates='account')


class Channel(Base):
    """
    The telegram channel the user is in
    """
    __tablename__ = 'channel'
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, unique=True, index=True, nullable=True) # The URL can come first but the channel ID populated later
    channel_name = Column(String(256), default=None, nullable=True)
    channel_title = Column(String(256), default=None, nullable=True)
    channel_url = Column(String(256), nullable=True)
    account_id = Column(Integer, ForeignKey('account.account_id'), nullable=False)  # The account ID (bot) that spawned the channel
    channel_is_mega_group = Column(Boolean(), nullable=True)
    channel_is_group = Column(Boolean(), nullable=True)
    channel_is_private = Column(Boolean(), nullable=True)
    channel_is_broadcast = Column(Boolean(), nullable=True)
    channel_access_hash = Column(String(50), nullable=True)
    channel_size = Column(Integer, nullable=True)
    channel_is_enabled = Column(Boolean(), nullable=True, default=True)
    channel_tcreate = Column(DateTime, default=datetime.now())

    messages = relationship('Message')

    accounts = relationship('Account', back_populates='channels')
    notifications = relationship('Notification', back_populates='channel')


class ChatUser(Base):
    """
    The participant of a chat on telegram
    """
    __tablename__ = 'chat_user'
    id = Column(Integer, primary_key=True, index=True)
    chat_user_id = Column(Integer, unique=True, index=True, nullable=False)
    chat_user_is_bot = Column(Boolean(), default=None)
    chat_user_is_verified = Column(Boolean(), default=None)
    chat_user_is_restricted = Column(Boolean(), default=None)
    chat_user_first_name = Column(String(50), default=None)
    chat_user_last_name = Column(String(50), default=None)
    chat_user_name = Column(String(100), default=None)
    chat_user_phone = Column(String(25), default=None)
    chat_user_tlogin = Column(DateTime, default=None)
    chat_user_tcreate = Column(DateTime, default=datetime.now())
    chat_user_tmodified = Column(DateTime, default=datetime.now())

    messages = relationship('Message')


class Keyword(Base):
    """
    This is the keyword to be alerted by
    """
    __tablename__ = 'keyword'
    keyword_id = Column(Integer, primary_key=True, index=True)
    keyword_description = Column(String(256), default=None, nullable=False)
    keyword_regex = Column(String(256), unique=True, nullable=False)
    keyword_is_enabled = Column(Boolean(), nullable=True, default=True)
    keyword_tmodified = Column(DateTime, default=datetime.now())
    keyword_tcreate = Column(DateTime, default=datetime.now())

    notifications = relationship('Notification')


class Message(Base):
    """
    The actual message from a channel and from a user
    """
    __tablename__ = 'message'
    message_id = Column(Integer, primary_key=True, index=True)
    chat_user_id = Column(Integer, ForeignKey('chat_user.chat_user_id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account.account_id'), nullable=False)  # The account ID (bot)
    channel_id = Column(Integer, ForeignKey('channel.channel_id'), nullable=False)
    keyword_id = Column(Integer, ForeignKey('keyword.keyword_id'), nullable=False)
    message_text = Column(String(10000), default=None)
    message_is_mention = Column(Boolean(), default=None)
    message_is_scheduled = Column(Boolean(), default=None)
    message_is_fwd = Column(Boolean(), default=None)
    message_is_reply = Column(Boolean(), default=None)
    message_is_bot = Column(Boolean(), default=None)
    message_is_group = Column(Boolean(), default=None)
    message_is_private = Column(Boolean(), default=None)
    message_is_channel = Column(Boolean(), default=None)
    message_channel_size = Column(Integer, default=None)
    message_tcreate = Column(DateTime, default=datetime.now())

    user = relationship('ChatUser', back_populates='messages')
    account = relationship('Account', back_populates='messages')
    channel = relationship('Channel', back_populates='messages')
    notifications = relationship('Notification')


class Monitor(Base):
    """
    Channels to join and monitor
    """
    __tablename__ = 'monitor'
    monitor_id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channel.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account.account_id'), nullable=False)  # The account ID (bot)
    monitor_tcreate = Column(DateTime, default=datetime.now())
    monitor_tmodified = Column(DateTime, default=datetime.now())
    channel = relationship('Channel')


class Notification(Base):
    """
    A log of notifications of keywords detected
    """
    __tablename__ = 'notification'
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey('keyword.keyword_id'), nullable=False)
    message_id = Column(Integer, ForeignKey('message.message_id'), nullable=False)
    channel_id = Column(Integer, ForeignKey('channel.channel_id'), nullable=False)
    account_id = Column(Integer, ForeignKey('account.account_id'), nullable=False)  # The account ID (bot)
    chat_user_id = Column(Integer, ForeignKey('chat_user.chat_user_id'), nullable=False)
    notification_tnotify = Column(DateTime, default=datetime.now())

    keyword = relationship('Keyword')
    message = relationship('Message')
    channel = relationship('Channel')
    user = relationship('ChatUser')
