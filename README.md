![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/informer-logo.gif)
# Informer - Telegram Mass Surveillance

## Update 08-23-2021
* Updated to latest Telethon 1.23.0
* Fixed database issues by migrating to docker-compose
* Made Google Spreadsheets optional in setup
* Secure ENV files for setup
* Easier setup

## About
**Informer (TGInformer) is a bot library that allows you to masquerade as multiple REAL users on telegram** and spy on 500+ Telegram channels **per account**. Details are logged to a MySQL database, a private Google Sheet and your own private channel for analysis.

This is a functioning proof-of-concept project with known bugs. Feel free to fork, share and drop me a line.

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/13.png)


## Potential Business Applications
* Sock puppeteering to overthrow a despotic regime
* Brand monitoring and sentiment analysis
* Shilling cryptocurrency at a moments notice for financial gain
* Influencing sentiment on topical issues
* Getting in on price action early
* Running analysis of a telegram channel


## Features
* Run all your bots in the cloud while you sleep. Support for Google App Engine Flexible Environment and Docker

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/14.png)

* Write all notifications to private Google Sheet

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/9.png)

* Supports regular expressions for keyword filtering

* SQLAlchemy for agnostic data persistence

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/8.png)

* Logging contextual message and channel data to a private channel and database

* Stores meta information about sender of message, channel, number of participants in the channel

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/7.png)

* Auto-joins channels from CSV list containing Telegram channel URLs

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/10.png)

* Persists session of channels joined

* Login once, bot stays logged in forever without needing 2FA re-authentication

* Join up to 500 channels per account

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/4.png)

* Uses REAL accounts avoiding bot detection, **THIS IS NOT A TELEGRAM BOT** but a real automated user account. This is an important distinction because the official bot API is limited and bots are often restricted in public channels.


## Requirements
### OS / Infrastructure
* Python 3+
* Docker (optional)
* Telegram (Desktop, Web or Mobile download: https://www.telegram.org/)
* Burner app

### Python packages
* SQLAlchemy (1.3.11)
* sqlalchemy-migrate (0.13.0)
* Telethon (1.10.8)
* mysql-connector-python (8.0.18)
* gspread (3.1.0)
* oauth2client (4.1.3)

## Quick Start

### Setup your ENV vars
Edit the file informer.env which contains all the required environmental variables for informer

You can retrieve the necessary Telegram-related information here:

### Setup Your Telegram App

1. Head over to `http://my.telegram.com/auth` to authenticate your account by providing a phone number and the confirmation code sent to your phone number (or Telegram)
![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1-2.png)

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1-5.png)


2. Once you are authenticated, click on "API Development Tools"
![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1-3.png)

3. Go ahead and create a New Application by filling out the form shown below
![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1-4.png)

4. You should now have the necessary parameter values for the `informer.env` file fields `TELEGRAM_API_HASH` and `TELEGRAM_API_APP_ID`

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1-6.png)

5. Go ahead and replace the values, including `TELEGRAM_ACCOUNT_PHONE_NUMBER` and move on to the next section

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1-7.png)

### Getting your Telegram ID

So far we have what we need for Telethon and Informer to access the Telegram APIs, next we need to acquire the indentifiers for your bot's account.

1. Open Telegram and search for the user `userinfobot`.

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/2-1.png)

2. You will see multiple, make sure you select the correctly spelled account.

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/2-2.png)

3. Click on the user and you should see a dialog option at the bottom that says "Start". Click on this.

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/2-3.png)

4. The bot has a single purpose, to reflect back to you your current Telegram account's information.

You should receive your Telegram username and your Telegram account ID. This is important

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1-8.png)

5. Go ahead and edit the `informer.env` file and fill in the values for `TELEGRAM_ACCOUNT_ID` which
should be your Telegram account ID from the previous step and `TELEGRAM_ACCOUNT_USER_NAME`.

You can optionally fill in `TELEGRAM_NOTIFICATIONS_CHANNEL_ID` with your user name or a channel ID.

6. Make sure you have `TELEGRAM_ACCOUNT_PHONE_NUMBER` filled out as this is key to generating the session. For creating multiple accounts, please check out the Burner App below.

### Initialize and authenticate session

Make sure you are running python 3 and simply run `./quick_start.sh` in the directory.

You must run this first so that you can authenticate with Telegram on the first run and generate a local session file

You can later copy the files for the different accounts in app/session and mount them via Docker should you choose to do so.

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/15.png)

You will be prompted to enter in the authentication code you received either via Telegram if you have logged in before, or via SMS

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1-5.png)

Hit enter and your session should be generated in the folder `app/session` with the file name as the international phone number you provided with a `.session` extension.

Continue to the next section where we use Docker Compose to setup a database.


### Setup a Notification Channel

This step is optional, but if you would like to create a private group channel and would like to acquire the group ID do the following:

* Create a group (or channel) and set it as private or public
* Be sure to get the Telegram URL
![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/3-1.png)

Set the URL in the `informer.env` file under the parameter `TELEGRAM_NOTIFICATIONS_CHANNEL_URL`

To get the channel ID simply run `python3 bot.py <TELEGRAM_ACCOUNT_ID>` in the `app` directory where `<TELEGRAM_ACCOUNT_ID>` is the account ID you previously generated.

When the script loads, it will display all the channels you are in, simply copy this value and put it in the `TELEGRAM_NOTIFICATIONS_CHANNEL_ID` parameter of the `informer.env` file and kill the script. You're now ready to run Informer.


### Running Docker Compose
After running `quick_start.sh` you can run docker compose by:

* running `./start.sh` to build the Docker containers which include the MySQL database

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/16.png)


* Run `./stop.sh` to stop the containers

* Run `./clean.sh` to remove an dangling containers and volumes. ** NOTE ** this will RESET the database and you will lose all your data.

A few things to note:

Before you were required to run your own MySQL instance and this created some issues with connection string compatability and versioning. In this update, it is just created for you and persisted on disk.

Additionally Dozzle is provided so that you may view logs in your browser, simply go to http://localhost:9999 and click on the `app_informer` container.


### Create a telegram account with Burner App

If you do not want to use your own phone number and want to run the Informer bot with some degree of anonymity you can use the Burner App available on iOS and Android.

1. Install the app Burner

	* Android - https://play.google.com/store/apps/details?id=org.thunderdog.challegram&hl=en_US
	* iOS - https://apps.apple.com/us/app/telegram-x/id898228810

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/3.png)

2. Follow the same steps as above by providing the new phone number here:
 https://my.telegram.org/auth

3. Validate with Burner. You will be sent an authcode via SMS, you will need to provide

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/1.png)

5. Log into Telegram

6.  Attempt to login with the app by running

`python3 bot.py <api_user_id>` in the `app` directory.

7. Since you are logging in with Telethon it will ask you for your authcode in the terminal like earlier.

This was  sent via Telegram message or SMS.

Provide this and it will save your session credentials in the session file mentioned below. You will no longer need to authenticate so long as you have the session file saved.

Sessions are saved in the `app/session/` folder as `<telegram_phone_number>.session`

Rinse and repeat until you have all the necessary session files and simply mount them in Docker.


## Scaling Telegram accounts
Figuring out how to scale accounts was a bit of a nightmare as I needed an automated process. Telegram requires you use a real phone number that can recieve texts from a shortcode.

Unfortunately services with APIs like Twilio are prohibited from receiving SMS from shortcodes in the US, Canada and UK https://support.twilio.com/hc/en-us/articles/223181668-Can-Twilio-numbers-receive-SMS-from-a-short-code- for fraud purposes. This would’ve been ideal, bahumbug.

A whole evening was wasted on this endeavor until I remembered a great app I used in the past: Burner (https://www.burnerapp.com/)  — which coincidentally does have an API (https://developer.burnerapp.com/api-documentation/incoming-webhooks/).  Meaning you can dynamically generate numbers, instantiate a new account and authenticate it all via Telegram’s client SDK in Python (Telethon: https://docs.telethon.dev/en/latest/)

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

## Managing Multiple Bot Accounts

As the bot runs and joins channel, you will see your client update in real time and display the new channels you have joined.

![image](https://raw.githubusercontent.com/paulpierre/informer/master/github/screenshots/4.png)

TIP: TelegramX is by far the better client to use for these purposes as it supports multiple login. Download here:

* Android - https://play.google.com/store/apps/details?id=org.thunderdog.challegram&hl=en_US
* iOS - https://apps.apple.com/us/app/telegram-x/id898228810


## Google Sheets Integration
The python library gspread is used for managing io with Google Sheets. You will need to have a Google Cloud Platform account and enable Google Drive APIs. Afterwards you must generate server credentials with a json api key.

Instructions are here: https://www.twilio.com/blog/2017/02/an-easy-way-to-read-and-write-to-a-google-spreadsheet-in-python.html

This is optional.


## Known Bugs
* Currently a channel must have already been joined in order to begin monitoring of keywords. It is likely you will need to run the `bot.py` twice, once to let it join channels and another time to monitor them. I’m aware of this glaring bug and will fix it in the next revision.


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
