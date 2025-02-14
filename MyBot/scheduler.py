from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import datetime
from database import db_execute, db_fetchall
from telebot import types

scheduler = BackgroundScheduler()
scheduler.start()

def send_reminder(chat_id, task_id, bot):
    """Функция для отправки напоминания пользователю."""
    task = db_fetchall("SELECT Task FROM Adds WHERE Id = ?", (task_id,))
    if task:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Удалить запись", callback_data=f'delete_task_{task_id}'),
            types.InlineKeyboardButton("Вернуться в главное меню", callback_data='main_menu')
        )
        bot.send_message(chat_id, f'⏰ Напоминание: {task[0][0]}!', reply_markup=markup)

def schedule_reminder(chat_id, task_id, reminder_time, bot):
    """Добавление напоминания в планировщик."""
    try:
        # Вставляем запись в Reminders и сразу получаем её ID
        query = """
            INSERT INTO Reminders (TaskID, ReminderTime) 
            VALUES (?, ?)
        """
        params = (task_id, reminder_time.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Используем db_execute, который возвращает lastrowid
        reminder_id = db_execute(query, params)
        
        if not reminder_id:
            raise ValueError("Не удалось добавить напоминание в БД")
        
        job_id = f'reminder_{reminder_id}'  # Уникальный ID на основе reminder_id
        scheduler.add_job(
            send_reminder,
            'date',
            run_date=reminder_time,
            args=[chat_id, task_id, bot],
            id=job_id
        )
        print(f"Напоминание {job_id} добавлено!")
    except Exception as e:
        print(f"Ошибка при добавлении напоминания: {e}")

def remove_job(job_id):
    """Функция для удаления задачи из планировщика."""
    try:
        scheduler.remove_job(job_id)
        print(f"Задача {job_id} удалена из планировщика.")
    except JobLookupError as e:
        print(f"Ошибка при удалении задачи: {e}")