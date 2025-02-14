import datetime
from telebot import types
from database import db_execute, db_fetchall
import scheduler  # Теперь импортируем ТОЛЬКО scheduler, а не send_reminder
from apscheduler.jobstores.base import JobLookupError


def send_reminder(chat_id, task_id, bot):
    task = db_fetchall("SELECT Task FROM Adds WHERE Id = ?", (task_id,))
    if task:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Удалить запись", callback_data=f'delete_task_{task_id}'),
            types.InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')
        )
        bot.send_message(chat_id, f'⏰ Напоминание: {task[0][0]}!', reply_markup=markup)

def start(message, bot):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Главное меню", callback_data='main_menu'))
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}! Я бот-ежедневник!', reply_markup=markup)


def main_menu(message, bot):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Добавить запись", callback_data='add'),
        types.InlineKeyboardButton("Удалить запись", callback_data='del')
    )
    markup.add(types.InlineKeyboardButton("Посмотреть записи", callback_data='show'))
    bot.send_message(message.chat.id, 'Выберите действие:', reply_markup=markup)

def add_task(message, bot):
    task_text = message.text.strip()
    if not task_text:
        bot.send_message(message.chat.id, '❌ Текст задачи не может быть пустым!')
        return

    # Пробуем добавить запись
    task_id = db_execute("INSERT INTO Adds (ChatID, Task) VALUES (?, ?)", (message.chat.id, task_text))
    
    if task_id is None:  # Если произошла ошибка
        bot.send_message(message.chat.id, '❌ Ошибка при создании задачи! Попробуйте ещё раз.')
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Да", callback_data=f'set_reminder_{task_id}'),
        types.InlineKeyboardButton("Нет", callback_data='main_menu')
    )
    bot.send_message(message.chat.id, '✅ Запись добавлена! Создать напоминание?', reply_markup=markup)



def set_reminder_template(call, task_id, bot):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("5 минут", callback_data=f'reminder_5_{task_id}'),
        types.InlineKeyboardButton("30 минут", callback_data=f'reminder_30_{task_id}')
    )
    markup.add(
        types.InlineKeyboardButton("1 час", callback_data=f'reminder_60_{task_id}'),
        types.InlineKeyboardButton("24 часа", callback_data=f'reminder_1440_{task_id}')
    )
    markup.add(types.InlineKeyboardButton("Своё время", callback_data=f'reminder_custom_{task_id}'))
    bot.send_message(call.message.chat.id, '⏳ Выберите время напоминания:', reply_markup=markup)

def set_reminder(message, task_id, bot):
    """Функция установки напоминания с вводом времени."""
    try:
        reminder_time = datetime.datetime.strptime(message.text, '%d-%m-%Y %H:%M:%S')
        current_time = datetime.datetime.now()

        if reminder_time <= current_time:
            bot.send_message(message.chat.id, '❌ Дата должна быть в будущем!')
            return

        task_exists = db_fetchall("SELECT Id FROM Adds WHERE Id = ?", (task_id,))
        # if not task_exists:
        #     bot.send_message(message.chat.id, '❌ Задача не найдена!')
        #     return

        db_execute("INSERT INTO Reminders (TaskID, ReminderTime) VALUES (?, ?)", 
                   (task_id, reminder_time.strftime("%Y-%m-%d %H:%M:%S")))

        scheduler.schedule_reminder(message.chat.id, task_id, reminder_time, bot)  # ✅ Новый вызов

        bot.send_message(message.chat.id, f'✅ Напоминание установлено на {reminder_time.strftime("%Y-%m-%d %H:%M:%S")}!')

    except ValueError:
        bot.send_message(message.chat.id, '❌ Неверный формат! Используйте DD-MM-YYYY HH:MM:SS.')
        bot.register_next_step_handler(message, set_reminder, task_id, bot)

def call_main_menu(call, bot):
    main_menu(call.message, bot)

def call_add(call, bot):
    bot.send_message(call.message.chat.id, '📝 Введите текст задачи:')
    bot.register_next_step_handler(call.message, add_task, bot)

def call_del(call, bot):
    tasks = db_fetchall("SELECT Id, Task FROM Adds WHERE ChatID = ?", (call.message.chat.id,))
    if tasks:
        markup = types.InlineKeyboardMarkup()
        for task in tasks:
            markup.add(types.InlineKeyboardButton(task[1], callback_data=f'delete_task_{task[0]}'))
        bot.send_message(call.message.chat.id, '❌ Выберите запись для удаления:', reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, '📭 Записей нет.')

def call_show(call, bot):
    tasks = db_fetchall("SELECT Task FROM Adds WHERE ChatID = ?", (call.message.chat.id,))
    text = '\n'.join([f"{i+1}. {task[0]}" for i, task in enumerate(tasks)]) if tasks else '📭 Записей нет.'
    bot.send_message(call.message.chat.id, f'📋 Ваши записи:\n{text}')

def call_set_reminder(call, bot):
    task_id = int(call.data.replace('set_reminder_', ''))
    set_reminder_template(call, task_id, bot)



def call_reminder_template(call, bot):
    """Функция для установки напоминания через кнопки."""
    data = call.data.split('_')
    minutes = data[1]
    
    try:
        task_id = int(data[2])
    except (IndexError, ValueError):
        bot.send_message(call.message.chat.id, '❌ Ошибка! Неверный ID задачи.')
        return


    if minutes == 'custom':
        bot.send_message(call.message.chat.id, '⏳ Введите дату и время в формате DD-MM-YYYY HH:MM:SS:')
        bot.register_next_step_handler(call.message, set_reminder, task_id, bot)
    else:
        try:
            minutes = int(minutes)
        except ValueError:
            bot.send_message(call.message.chat.id, '❌ Неверное время.')
            return

        current_time = datetime.datetime.now()
        reminder_time = current_time + datetime.timedelta(minutes=minutes)
        
        db_execute(
            "INSERT INTO Reminders (TaskID, ReminderTime) VALUES (?, ?)",
            (task_id, reminder_time.strftime("%Y-%m-%d %H:%M:%S"))
        )

        scheduler.schedule_reminder(call.message.chat.id, task_id, reminder_time, bot)  # ✅ Новый вызов

        bot.send_message(
            call.message.chat.id,
            f'✅ Напоминание установлено на {reminder_time.strftime("%d-%m-%Y %H:%M:%S")}!'
        )
def call_delete_task(call, bot):
    task_id = int(call.data.replace('delete_task_', ''))
    
    # 1. Удаляем напоминания из планировщика и таблицы Reminders
    reminders = db_fetchall("SELECT Id FROM Reminders WHERE TaskID = ?", (task_id,))
    for reminder in reminders:
        reminder_id = reminder[0]
        job_id = f'reminder_{reminder_id}'
        try:
            scheduler.remove_job(job_id)  # Удаляем задачу из планировщика
        except JobLookupError:
            pass
        db_execute("DELETE FROM Reminders WHERE Id = ?", (reminder_id,))  # Удаляем запись из Reminders
    
    # 2. Теперь удаляем саму задачу из Adds
    success = db_execute("DELETE FROM Adds WHERE Id = ?", (task_id,))
    
    if success:
        bot.send_message(call.message.chat.id, '🗑️ Запись удалена!')
    else:
        bot.send_message(call.message.chat.id, '❌ Ошибка при удалении записи!')
    
    main_menu(call.message, bot)
