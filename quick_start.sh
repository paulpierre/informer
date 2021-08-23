#!/bin/bash


# change to app directory
cd ./app

# create virtual env
python3 -m venv 

# load venv
source venv/bin/activate

# install requirements in this env
pip install -r requirements.txt

#run the bot
python3 bot.py
