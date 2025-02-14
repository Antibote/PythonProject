import telebot
from config import TOKEN
from database import db_setup
from handlers import *
from scheduler import scheduler

bot = telebot.TeleBot(TOKEN)
db_setup()

@bot.message_handler(commands=['start'])
def handle_start(message):
    start(message, bot)

@bot.message_handler(commands=['main_menu'])
def handle_main_menu(message):
    main_menu(message, bot)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == 'main_menu':
        call_main_menu(call, bot)
    elif call.data == 'add':
        call_add(call, bot)
    elif call.data == 'del':
        call_del(call, bot)
    elif call.data == 'show':
        call_show(call, bot)
    elif call.data.startswith('set_reminder_'):
        call_set_reminder(call, bot)
    elif call.data.startswith('reminder_'):
        call_reminder_template(call, bot)
    elif call.data.startswith('delete_task_'):
        call_delete_task(call, bot)

bot.polling(none_stop=True)