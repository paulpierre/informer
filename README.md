![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/informer-logo.gif)
# Informer - Telegram Mass Surveillance
## About
**Informer (TGInformer) is a bot library that allows you to masquerade as multiple REAL users on telegram** and spy on 500+ Telegram channels **per account**. Details are logged to a MySQL database, a private Google Sheet and your own private channel for analysis.

This is a functioning proof-of-concept project with known bugs. Feel free to fork, share and drop me a line.


## Potential Business Applications
* Sock puppeteering to overthrow a despotic regime
* Brand monitoring and sentiment analysis
* Shilling cryptocurrency at a moments notice for financial gain
* Influencing sentiment on topical issues
* Getting in on price action early
* Running analysis of a telegram channel


## Features
* Write all notifications to private Google Sheet

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/9.png)

* Supports regular expressions for keyword filtering

* SQLAlchemy for agnostic data persistence

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/8.png)

* Logging contextual message and channel data to a private channel and database

* Stores meta information about sender of message, channel, number of participants in the channel

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/7.png)

* Auto-joins channels from CSV list containing Telegram channel URLs

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/10.png)

* Persists session of channels joined

* Login once, bot stays logged in forever without needing 2FA re-authentication

* Join up to 500 channels per account

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/4.png)

* Uses REAL accounts avoiding bot detection, **THIS IS NOT A TELEGRAM BOT** but a real automated user account. This is an important distinction because the official bot API is limited and bots are often restricted in public channels.


## Requirements
### OS / Infrastructure
* Python 3+
* Docker (optional)
* Telegram (Desktop, Web or Mobile download: https://www.telegram.org/)
* Burner app

### Python packages
* Jinja2 (2.10.3)
* SQLAlchemy (1.3.11)
* Werkzeug (0.16.0)
* pytz (2019.3)
* sqlalchemy-migrate (0.13.0)
* requests (2.7.0)
* Flask (1.1.1)
* Telethon (1.10.8)
* mysql-connector-python (8.0.18)
* gspread (3.1.0)
* oauth2client (4.1.3)


## Getting Started
### Run locally without Docker
If you’re not interested in kicking the tires and want to light some fires instead, you can run the Informer bot locally and not in a docker instance. A licky boom boom down.

1. Create a virtual environment in the local directory

`virtualenv venv`

2. Install the depencies in requirements.txt

`pip install -r requirements.txt`

3. Use the instructions below to retrieve your Telegram user API ID and API hash and supply this information in `build_database.py`

4. Create a MySQL database locally and supply the credentials in the bot.py. MySQL comes with MacOS. You can also install the latest version for your OS and follow the instructions here:

	https://dev.mysql.com/doc/mysql-getting-started/en/

5. Run `python3 build_database.py` . This will create the models in `models.py` inside your new MySQL database and ensure it is unicode safe for those fun eye-bleeding emojis on TG.

It will also setup some default values for keywords to monitor and channels to join supplied in channels.csv.

6. Create a group or channel on Telegram and retrieve its channel ID. This will be the channel where your snitching bot will drop all its notifications of keywords mentioned in other channels. Provide this value in `tg_notifications_channel_id=<your_channel_id>` inside `bot.py`

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/2.png)

7. If all is well we can go ahead and fire up Informer by running
`python3 bot.py <your_api_user_id>` which will take your configuration and spin up an instance of the `TGInformer` class and begin surveillance.
You will need to provide the API ID you generated from the instructions below as an argument so the bot knows which account to log into.

**NOTE:** If this is your first time logging in, it will send you an authorization code via SMS or via the Telegram app. You will need to enter this to authenticate the bot and log into the Telegram servers. You will only need to do this once as a session file will be generated locally to persist all sessions. This entire process is handled by the Telethon Telegram client SDK.

### Create a telegram account with Burner App

1. Install the app Burner

	* Android - https://play.google.com/store/apps/details?id=org.thunderdog.challegram&hl=en_US
	* iOS - https://apps.apple.com/us/app/telegram-x/id898228810

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/3.png)

2. You first will need to create Telegram API credentials by providing a phone number here:
 https://my.telegram.org/auth

3. Validate with Burner. You will be sent an authcode via SMS, you will need to provide

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/1.png)

5. Log into Telegram

6.  attempt to login with the app by running

`python3 bot.py <api_user_id>`

7. Since you are logging in with Telethon it will ask you for your authcode in the terminal. This was  sent via Telegram message or SMS. Provide this and it will save your session credentials in the session file mentioned below. You will no longer need to authenticate so long as you have the session file saved.

Sessions are saved in the `session/` folder as `<telegram_phone_number>.session`


## Scaling Telegram accounts
Figuring out how to scale accounts was a bit of a nightmare as I needed an automated process. Telegram requires you use a real phone number that can recieve texts from a shortcode.

Unfortunately services with APIs like Twilio are prohibited from receiving SMS from shortcodes in the US, Canada and UK https://support.twilio.com/hc/en-us/articles/223181668-Can-Twilio-numbers-receive-SMS-from-a-short-code- for fraud purposes. This would’ve been ideal, bahumbug.

A whole evening was wasted on this endeavor until I remebered a great app I used in the past: Burner (https://www.burnerapp.com/)  — which coincidentally does have an API (https://developer.burnerapp.com/api-documentation/incoming-webhooks/).  Meaning you can dynamically generate numbers, instantiate a new account and authenticate it all via Telegram’s client SDK in Python (Telethon: https://docs.telethon.dev/en/latest/)

The best part is Burner numbers are free for 14 days. Telegram accounts connected via client API need only login once and permanently persist sessions. I have not integrated with the Burner API, but the process is straight forward.


### Telethon SDK
The bot is built on top of the Telethon Python SDK (https://docs.telethon.dev/en/latest/)

A few things to note and gotchas encountered in building this proof of concept:

1. **Rate Limiting**
Telegram does intense rate limiting which will throw FloodWaitErrors. 
In my research it seems like no one knows the algorithm for this but 
you want your back off waits to scale in response because when you 
violate and exceed the unknown rate limit, the waits become 
exponential. I’ve found a happy medium with my approach to waiting.

FloodWaitErrors can occur when you are submitting too many requests 
to the API whether it is querying users information or joining  too many 
channels too fast

2. **Telethon Sessions**
Telethon will create a session file. You can set the name of the session 
file when you instantiate the Telethon client: 

`TelegramClient(<session_file_name>, <api_user_id>, <api_user_hash>)`

	This file happens to be a sqlite database which you can connect to. It 	
	acts like a cache and stores historical data as well as your session 
	authentication information so you will not have to re-authenticate with 
	Telegram’s 2FA . Note that you will need to login for a first time and 
	authenticate when you first use the API.


### Docker
If you want to run the bot as a containerized instance on a server with AWS, GCP or Digital ocean you can.

You will need to create an account with a container registry service, available on most enterprise cloud providers but Docker Hub will do (https://hub.docker.com/signup)

1. Create a Docker repository, instructions here: https://docs.docker.com/docker-hub/repos/

2. Build the Docker image. We’re running on a lean Alpine Python 3.7 image.

 `docker build -t <user_name>/<repo_name>/informer:latest .`

**NOTE:** You will want an entry point to run bot.py and provide it a Telegram API user ID. There are a few ways to approach this:

* You can comment out and include the CMD instruction and provide the API user ID via environment variable:
`CMD [“python”,”bot.py”,”${SHILLOMATIC_ACCOUNT_ID}”]`
You will need to set the environment variable 
`SHILLOMATIC_ACCOUNT_ID`  to your Telegram accounts API user ID 
inside your Cloud Provider’s console or export it in your shell 
environment with `export SHILLOMATIC_ACCOUNT_ID=“1234567”` 

* Or you can set or over-ride the entry point in your cloud provider just make sure you provide the Telegram API user ID as an argument:

`python3 bot.py 1234567`

* Or you can run the bot inside the shell environment with Docker:

	1. SSH into your remote shell environment

	2. Pull the Docker image from the remote repository:

	`docker pull <user_name>/<repo_name>/informer:latest`

	3. Get the Docker container ID with:

	`docker container ls`

	4. Run the Docker image and script in interactive mode:

	`docker run -ti <container_id> python3 bot.py 1234567`
	Where 1234567 is your Telegram API user ID.

3. Push the Docker image to your remote repository:

`docker push <user_name>/<repo_name>/informer:latest`

4. Assuming some entry point was set either in the Docker file, your cloud provider container dashboard, or manually in the shell with `docker run` you can open Telegram and login with the same account as above.

As the bot runs and joins channel, you will see your client update in real time and display the new channels you have joined.

![image](https://raw.githubusercontent.com/paulpierre/informer/master/screenshots/4.png)

TIP: TelegramX is by far the better client to use for these purposes as it supports multiple login. Download here:

* Android - https://play.google.com/store/apps/details?id=org.thunderdog.challegram&hl=en_US
* iOS - https://apps.apple.com/us/app/telegram-x/id898228810


## Google Sheets Integration
The python library gspread is used for managing io with Google Sheets. You will need to have a Google Cloud Platform account and enable Google Drive APIs. Afterwards you must generate server credentials with a json api key.

Instructions are here: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html


## Known Bugs
* Currently a channel must have already been joined in order to begin monitoring of keywords. It is likely you will need to run the `bot.py` twice, once to let it join channels and another time to monitor them. I’m aware of this glaring butg and will fix it in the next revision.


## Todo
* Create user interface dashboard for bot management
	* Create new accounts
	* Add / remove channels
	* Add / remove keywords to monitor
	* View notifications 
	* Recieve web push notifications
* Automatically poll the database to update the keywords to monitor in memory
* Automate creation of phone numbers via Burner API and authcode process


## Getting in touch
Did you find this project interesting? Please star it if so.

It was made in two days as a proof of concept for a friend in the cryptocurrency space. If you find any interesting or lucrative applications, I’m always happy to collaborate. You can reach me at:

@paulpierre on Twitter or hi (at) paulpierre (dot) com 

Most of my interesting projects are private on github, but feel free to check them out: http://www.github.com/paulpierre or past work at http://www.paulpierre.com


## Open Source License
----
Copyright (c) 2020 Paul Pierre
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in allcopies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
