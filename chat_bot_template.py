#!/usr/local/bin/python3
# -*- coding: utf-8 -*-

import logging
import time
import json
import os
import requests
from setup import PROXY, TOKEN
from telegram import Bot, Update
from telegram.ext import CallbackContext, CommandHandler, Filters, MessageHandler, Updater

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.

users_action = []
USER_ACTIONS_FILE = "user_actions.json"


def handle_command(func):
    def inner(*args, **kwargs):
        update = args[0]
        if update:
            users_action.append({
                'user_name': update.effective_user.first_name,
                'function': func.__name__,
                'text': update.message.text,
                'time': time.strftime("%H:%M:%S", time.localtime())
            })
        save_history()
        return func(*args, **kwargs)
    return inner


@handle_command
def handle_start(update: Update, context: CallbackContext):
    """Send a message when the command /start is issued."""
    update.message.reply_text(f'Привет, {update.effective_user.first_name}!')


@handle_command
def handle_help(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Введи команду /start для начала. ')


def handle_get_history(update: Update, context: CallbackContext):
    count = 0
    for action in users_action[::-1]:
        if action["user_name"] == update.effective_user.first_name and count != 5:
            update.message.reply_text(f"Function: {action['function']},"
                                      f" text: \"{action['text']}\", time: {action['time']}")
            count += 1
    if count == 0:
        update.message.reply_text("You haven't done anything yet")


@handle_command
def handle_echo(update: Update, context: CallbackContext):
    """Echo the user message."""
    update.message.reply_text(update.message.text)

@handle_command
def handle_fact(update: Update, context: CallbackContext):
    """third homework"""
    max_entry = -1
    json_response = requests.get('https://cat-fact.herokuapp.com/facts').json()

    for entry in json_response['all']:
        if max_entry < int(entry['upvotes']):
            max_entry = int(entry['upvotes'])
    update.message.reply_text(f"Max upvote is {max_entry}.")


def save_history():
    with open(USER_ACTIONS_FILE, mode="w", encoding="utf-8") as file:
        json.dump(users_action, file, ensure_ascii=False, indent=2)


def load_history():
    global users_action
    if os.stat(USER_ACTIONS_FILE).st_size == 0:
        return
    with open(USER_ACTIONS_FILE, mode="r", encoding="utf-8") as file:
        users_action = json.load(file)


def error(update: Update, context: CallbackContext):
    """Log Errors caused by Updates."""
    logger.warning(f'Update {update} caused error {context.error}')


def main():
    bot = Bot(
        token=TOKEN,
        base_url=PROXY,  # delete it if connection via VPN
    )
    load_history()
    updater = Updater(bot=bot, use_context=True)
    # on different commands - answer in Telegram
    updater.dispatcher.add_handler(CommandHandler('start', handle_start))
    updater.dispatcher.add_handler(CommandHandler('help', handle_help))
    updater.dispatcher.add_handler(CommandHandler('history', handle_get_history))
    updater.dispatcher.add_handler(CommandHandler('fact', handle_fact))

    # on noncommand i.e message - echo the message on Telegram
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_echo))

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
