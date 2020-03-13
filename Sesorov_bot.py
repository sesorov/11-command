#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import logging
import json
import os
import requests
import telegram
from datetime import datetime

from setup import PROXY, TOKEN
from telegram import Bot, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

ACTION_LOG = []
ACTION_COUNT = 0

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.


def log(func):
    def inner(*args, **kwargs):
        global ACTION_COUNT
        update = args[0]
        if update and hasattr(update, "warning"):
            with open(f"{update.message.chat.id}.json", "a") as handle:
                print(func, file=handle)
        if update and hasattr(update, "message") and hasattr(update, "effective_user"):
            ACTION_COUNT += 1
            if ACTION_COUNT > 5:
                ACTION_LOG.pop(0)
                with open(f"{update.message.chat.id}.json", 'w+') as handle:
                    json.dump(ACTION_LOG, handle, indent=2)
            log = {
                "Action": f"{ACTION_COUNT}:",
                "user": update.effective_user.first_name,
                "function": func.__name__,
                "message": update.message.text,
                "time": args[0].message.date.strftime("%d-%b-%Y (%H:%M:%S.%f)")
            }
            ACTION_LOG.append(log)
            try:
                os.remove(f"{update.message.chat.id}.json")
            except FileNotFoundError:
                print("No such file; probably, first use. Creating new.")
            with open(f"{update.message.chat.id}.json", 'w+') as handle:
                json.dump(ACTION_LOG, handle, indent=2)
            handle.close()
            return func(*args, **kwargs)
    return inner

@log
def start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(f'Привет, {update.effective_user.first_name}!')
    f = open(f"{update.message.chat.id}.json", "w+")

@log
def chat_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Введи команду /start для начала. ')

@log
def echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

@log
def history(update: Update, context: CallbackContext):
    """Display 5 latest ACTION_HISTORY elements when the command /history is issued."""
    global ACTION_COUNT, ACTION_LOG
    update.message.reply_text("Last 5 actions:")
    with open(f"{update.message.chat.id}.json", "r") as handle:
        data = json.load(handle)
        output = ""
        for action in data:
            for key, value in action.items():
                output += f"{key}: {value}\n"
            output += "\n"
        update.message.reply_text(output)
    handle.close()

@log
def fact(update: Update, context: CallbackContext):
    fact = requests.get("https://cat-fact.herokuapp.com/facts").json()["all"][0]
    quote = f"<i>{fact['text']}</i>"
    author = f"<b>Author: {fact['user']['name']['first']} {fact['user']['name']['last']}</b>"
    update.message.reply_text("Well, time for a good quote...")
    update.message.reply_text(f'«{quote}»\n\t                     一 {author:}', parse_mode=telegram.ParseMode.HTML)

@log
def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')


def main():
    bot = Bot(
        token="895548858:AAHWTesxKmd6rpC3P4u6QJejsordITl3cYU",
        base_url=PROXY,  # delete it if connection via VPN
    )
    updater = Updater(bot=bot, use_context=True)

    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', chat_help))
    updater.dispatcher.add_handler(CommandHandler('history', history))
    updater.dispatcher.add_handler(CommandHandler('fact', fact))

    # on noncommand i.e message - echo the message on Telegram
    updater.dispatcher.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    logger.info('Start Bot')
    main()
