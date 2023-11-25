from datetime import datetime, timedelta
import time
import pytz
import html
import config
import logging
import asyncio
import threading
import telebot
import sql_exec
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

bot = telebot.TeleBot(config.main_bot)

def settings(arg):
    markup = InlineKeyboardMarkup()
    arg -= 1
    arg = max(arg, 0)
    for x in range(arg * 7, arg * 7 + 7):
        if sql_exec.get_pos_line("chats", x) == 0:
            break
        line = sql_exec.get_pos_line_result("chats", x)
        name = bot.get_chat(line[0][0]).title
        markup.row(InlineKeyboardButton(f"{x + 1}. {name}", callback_data=f"{bot.get_chat(line[0][0]).id}"))
    if sql_exec.count_row("chats") > 7:
        markup.row(InlineKeyboardButton("<<", callback_data=f"prev_page_{arg}"), InlineKeyboardButton(">>", callback_data=f"next_page_{arg}"),)
    return markup

def settings_chat(id_chat):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📩 Рассылка", callback_data=f"mailing_{id_chat}"))
    markup.row(InlineKeyboardButton("🌄 Утренний опрос", callback_data=f"morning_{id_chat}"))
    markup.row(InlineKeyboardButton("🎆 Вечерний опрос", callback_data=f"evening_{id_chat}"))
    markup.row(InlineKeyboardButton("❌ Удалить из чата", callback_data=f"remove_bot_{id_chat}"))
    markup.row(InlineKeyboardButton("<< Вернуться", callback_data="show_settings"))
    return markup

def settings_mailing(id_chat):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⏳ Изменить текст", callback_data=f"text_change_{id_chat}"))
    markup.row(InlineKeyboardButton("🌄 Время начало рассылки", callback_data=f"text_time_morning_{id_chat}"))
    markup.row(InlineKeyboardButton("🎆 Время окончание рассылки", callback_data=f"text_time_evening_{id_chat}"))
    markup.row(InlineKeyboardButton("❌ Удалить рассылку", callback_data=f"remove_mailing_{id_chat}"))
    markup.row(InlineKeyboardButton("<< Вернуться", callback_data=f"{id_chat}"))
    return markup

def settings_evening(id_chat):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⏳ Изменить вопрос", callback_data=f"text_change_evening_{id_chat}"))
    markup.row(InlineKeyboardButton("⏳ Изменить ответы", callback_data=f"change_answer_evening_{id_chat}"))
    markup.row(InlineKeyboardButton("⏳ Изменить время", callback_data=f"change_time_evening_{id_chat}"))
    y = sql_exec.check("evening_poll", "chat_id", id_chat)[0][3]
    x = "Включить" if str(y) == "0" or y is None else "Выключить"
    markup.row(InlineKeyboardButton(f"🌄 {x} режим анонимности", callback_data=f"change_bool_anonim_even_{id_chat}"))
    y = sql_exec.check("evening_poll", "chat_id", id_chat)[0][4]
    x = "Включить" if str(y) == "0" or y is None else "Выключить"
    markup.row(InlineKeyboardButton(f"🎆 {x} режим нескольких ответов", callback_data=f"change_bool_multiply_even_{id_chat}"))
    markup.row(InlineKeyboardButton("❌ Удалить голосование", callback_data=f"remove_evening_{id_chat}"))
    markup.row(InlineKeyboardButton("<< Вернуться", callback_data=f"{id_chat}"))
    return markup

def settings_morning(id_chat):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⏳ Изменить вопрос", callback_data=f"text_change_morning_{id_chat}"))
    markup.row(InlineKeyboardButton("⏳ Изменить ответы", callback_data=f"change_answer_morning_{id_chat}"))
    markup.row(InlineKeyboardButton("⏳ Изменить время", callback_data=f"change_time_morning_{id_chat}"))
    y = sql_exec.check("morning_poll", "chat_id", id_chat)[0][3]
    x = "Включить" if str(y) == "0" or y is None else "Выключить"
    markup.row(InlineKeyboardButton(f"🌄 {x} режим анонимности", callback_data=f"change_bool_anonim_morning_{id_chat}"))
    y = sql_exec.check("morning_poll", "chat_id", id_chat)[0][4]
    x = "Включить" if str(y) == "0" or y is None else "Выключить"
    markup.row(InlineKeyboardButton(f"🎆 {x} режим нескольких ответов", callback_data=f"change_bool_multiply_morning_{id_chat}"))
    markup.row(InlineKeyboardButton("❌ Удалить голосование", callback_data=f"remove_morning_{id_chat}"))
    markup.row(InlineKeyboardButton("<< Вернуться", callback_data=f"{id_chat}"))
    return markup

def add_minute(time_string):
    hours, minutes = map(int, time_string.split(":"))
    minutes = int(minutes) + 1
    if minutes >= 60:
        hours = int(hours) + 1
        minutes = minutes - 60
    return f"{hours:02d}:{minutes:02d}"

@bot.message_handler(commands=['start'])
def start_message(message):
    results = sql_exec.check("users", "user_id", message.from_user.id)
    print(results)
    if len(results) == 0:
        sql_exec.insert("users", 'user_id,state,currect_bot', f'{message.from_user.id},NULL,NULL')
    bot.send_message(message.chat.id, "Добро пожаловать! 👋")

@bot.message_handler(commands=['regbot'])
def regbot_in_group(message):
    text_for_send = f"""<b>Установка "{bot.get_me().full_name}" в чат</b>

0) Используйте мобильное приложение
1) Пригласите бота <a href="http://t.me/snerov_bot?startgroup=snerov">по этой ссылке</a>
2) Нажмите на название СВОЕГО чата
3) Используйте бота!

💬 По желанию можете придумать должность и активировать дополнительные права администратора.
❗️ Не отключайте уже установленные права!"""
    sql_exec.set_state(message.chat.id, "1")
    bot.send_message(message.chat.id, text_for_send, parse_mode="HTML", disable_web_page_preview=True)

@bot.message_handler(commands=['settings'])
def settings_message(message):
    bot.send_message(message.chat.id, "<b>Панель управления ботом</b>", parse_mode="HTML", reply_markup=settings(1))

@bot.message_handler(content_types=['new_chat_members'])
def send_welcome(message):
    bot_obj = bot.get_me()
    bot_id = bot_obj.id

    for chat_member in message.new_chat_members:
        if chat_member.id == bot_id:
            invited_by = message.from_user.id
            result = sql_exec.check("users", 'user_id', invited_by)
            try:
                if result[0][1] is None:
                    bot.send_message(
                        message.chat.id,
                        '<b>Не инициализированная установка бота!</b>',
                        parse_mode="HTML",
                    )
                    bot.leave_chat(message.chat.id)
                else:
                    sql_exec.set_state(invited_by, "NULL")
                    if (
                        len(
                            sql_exec.check(
                                "chats", 'Unique_ID', message.chat.id
                            )
                        )
                        != 0
                    ):
                        sql_exec.delete_chat(message.chat.id)
                    sql_exec.insert("chats", "Unique_ID,Mailing_ID,Poll_Morning,Poll_Evening", f"{message.chat.id},NULL,NULL,NULL")
                    bot.send_message(
                        message.chat.id,
                        '<b>Установка бота завершена!</b>',
                        parse_mode="HTML",
                    )
                    bot.send_message(invited_by, f'<b>"{bot.get_me().full_name}"</b> установился в чат:\n<code>{message.chat.title}</code>', parse_mode="HTML")
            except Exception as e:
                print(e)
                bot.send_message(
                    message.chat.id,
                    '<b>Добавлять бота может пользователь без анонимности!</b>',
                    parse_mode="HTML",
                )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    print(call.data)
    
    count_chats = sql_exec.count_row("chats")
    count_page_chats = count_chats // 7

    if 'change_answer_morning' in call.data:
        id_chat = int(str(call.data).removeprefix("change_answer_morning_"))
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

<i>Введите ответы опроса...
В формате :
<b>Пример_Отправки_Ответа</b>

ВАЖНО! Не более 10 пунктов! Ограничение Telegram!</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_answer_poll, id_chat, call, False)
        return
    elif "change_answer_evening_" in call.data:
        id_chat = int(str(call.data).removeprefix("change_answer_evening_"))
        
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>

<i>Введите ответы опроса...
В формате :
<b>Пример_Отправки_Ответа</b>

ВАЖНО! Не более 10 пунктов! Ограничение Telegram!</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_answer_poll, id_chat, call, True)
        return
    if 'change_bool_multiply_morning_' in call.data:
        id_chat = int(str(call.data).removeprefix("change_bool_multiply_morning_"))
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""     
        now_state = False if str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][4]) == "0" or sql_exec.check("morning_poll", "chat_id", id_chat)[0][4] == None else True
        new_state = '0' if now_state else '1'
        sql_exec.set("morning_poll", 'chat_id', id_chat, 'multiply', new_state)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_morning(id_chat))  
        return
    elif "change_bool_multiply_even_" in call.data:
        id_chat = int(str(call.data).removeprefix("change_bool_multiply_even_"))
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""     
        now_state = False if str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][4]) == "0" or sql_exec.check("evening_poll", "chat_id", id_chat)[0][4] == None else True
        new_state = '0' if now_state else '1'
        sql_exec.set("evening_poll", 'chat_id', id_chat, 'multiply', new_state)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_evening(id_chat)) 
        return
    elif len(sql_exec.check("chats", 'Unique_ID', call.data)) != 0:
        try: sql_exec.check("mailing", "chat_id", call.data)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("mailing", "chat_id,start_time,end_time,text", f"{call.data},NULL,NULL,NULL")
        try: sql_exec.check("morning_poll", "chat_id", call.data)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{call.data},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", call.data)[0][1] if sql_exec.check("morning_poll", "chat_id", call.data)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", call.data)[0][2] if sql_exec.check("morning_poll", "chat_id", call.data)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", call.data)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        try: sql_exec.check("evening_poll", "chat_id", call.data)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{call.data},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", call.data)[0][1] if sql_exec.check("evening_poll", "chat_id", call.data)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", call.data)[0][2] if sql_exec.check("evening_poll", "chat_id", call.data)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", call.data)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        SENDER_TEXT_MAIN_CHAT = f"""⚙️ <b>{bot.get_chat(call.data).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", call.data)[0][1] if sql_exec.check("mailing", "chat_id", call.data)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", call.data)[0][2] if sql_exec.check("mailing", "chat_id", call.data)[0][2] != None else "__:__"})</i>:
• <code>{sql_exec.check("mailing", "chat_id", call.data)[0][3] if sql_exec.check("mailing", "chat_id", call.data)[0][3] != None else "____________________"}</code>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>
"""
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=SENDER_TEXT_MAIN_CHAT, parse_mode="HTML", reply_markup=settings_chat(call.data)) 
        return
    elif 'change_bool_anonim_morning_' in call.data:
        id_chat = int(str(call.data).removeprefix("change_bool_anonim_morning_"))
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""     
        now_state = False if str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][3]) == "0" or sql_exec.check("morning_poll", "chat_id", id_chat)[0][3] == None else True
        new_state = '0' if now_state else '1'
        sql_exec.set("morning_poll", 'chat_id', id_chat, 'anonim', new_state)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_morning(id_chat))  
        return
    elif 'change_bool_anonim_even_' in call.data:
        id_chat = int(str(call.data).removeprefix("change_bool_anonim_even_"))
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""     
        now_state = False if str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][3]) == "0" or sql_exec.check("evening_poll", "chat_id", id_chat)[0][3] == None else True
        new_state = '0' if now_state else '1'
        sql_exec.set("evening_poll", 'chat_id', id_chat, 'anonim', new_state)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_evening(id_chat))  
        return
    elif "remove_mailing_" in call.data:
        id_chat = str(call.data).removeprefix("remove_mailing_")
        try: sql_exec.check("mailing", "chat_id", id_chat)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("mailing", "chat_id,start_time,end_time,text", f"{id_chat},NULL,NULL,NULL")
        sql_exec.set_null("mailing", "chat_id", id_chat, "text")
        sql_exec.set_null("mailing", "chat_id", id_chat, "start_time")
        sql_exec.set_null("mailing", "chat_id", id_chat, "end_time")
        sql_exec.remove_line("mailing", 'chat_id', id_chat)
        try: sql_exec.check("mailing", "chat_id", id_chat)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("mailing", "chat_id,start_time,end_time,text", f"{id_chat},NULL,NULL,NULL")
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        SENDER_TEXT_MAIN_CHAT = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", id_chat)[0][1] if sql_exec.check("mailing", "chat_id", id_chat)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", id_chat)[0][2] if sql_exec.check("mailing", "chat_id", id_chat)[0][2] != None else "__:__"})</i>:
• <code>{sql_exec.check("mailing", "chat_id", id_chat)[0][3] if sql_exec.check("mailing", "chat_id", id_chat)[0][3] != None else "____________________"}</code>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>
"""
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=SENDER_TEXT_MAIN_CHAT, parse_mode="HTML", reply_markup=settings_chat(id_chat))
        return
    elif "remove_morning_" in call.data:
        id_chat = str(call.data).removeprefix("remove_morning_")
        try: sql_exec.check("mailing", "chat_id", id_chat)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("mailing", "chat_id,start_time,end_time,text", f"{id_chat},NULL,NULL,NULL")
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL")
        sql_exec.remove_line("morning_poll", "chat_id", id_chat)
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        SENDER_TEXT_MAIN_CHAT = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", id_chat)[0][1] if sql_exec.check("mailing", "chat_id", id_chat)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", id_chat)[0][2] if sql_exec.check("mailing", "chat_id", id_chat)[0][2] != None else "__:__"})</i>:
• <code>{sql_exec.check("mailing", "chat_id", id_chat)[0][3] if sql_exec.check("mailing", "chat_id", id_chat)[0][3] != None else "____________________"}</code>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>
"""
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=SENDER_TEXT_MAIN_CHAT, parse_mode="HTML", reply_markup=settings_chat(id_chat))
        return
    elif "remove_evening_" in call.data:
        id_chat = str(call.data).removeprefix("remove_evening_")
        try: sql_exec.check("mailing", "chat_id", id_chat)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("mailing", "chat_id,start_time,end_time,text", f"{id_chat},NULL,NULL,NULL")
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL")
        sql_exec.remove_line("evening_poll", "chat_id", id_chat)
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        SENDER_TEXT_MAIN_CHAT = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", id_chat)[0][1] if sql_exec.check("mailing", "chat_id", id_chat)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", id_chat)[0][2] if sql_exec.check("mailing", "chat_id", id_chat)[0][2] != None else "__:__"})</i>:
• <code>{sql_exec.check("mailing", "chat_id", id_chat)[0][3] if sql_exec.check("mailing", "chat_id", id_chat)[0][3] != None else "____________________"}</code>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>
"""
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=SENDER_TEXT_MAIN_CHAT, parse_mode="HTML", reply_markup=settings_chat(id_chat))
        return
    elif "remove_bot_" in call.data:
        id_chat = str(call.data).removeprefix("remove_bot_")
        bot.answer_callback_query(call.id, "Бот покинул чат!", True)
        bot.leave_chat(id_chat)
        sql_exec.remove_line("mailing", "chat_id", id_chat)
        sql_exec.remove_line("chats", "Unique_ID", id_chat)
        sql_exec.remove_line("evening_poll", "chat_id", id_chat)
        sql_exec.remove_line("morning_poll", "chat_id", id_chat)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Панель управления ботом</b>", parse_mode="HTML", reply_markup=settings(1))
        return
    elif "text_change_morning_" in call.data:
        id_chat = int(str(call.data).removeprefix("text_change_morning_"))
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

<i>Введите вопрос опроса...</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_text_poll, id_chat, call, False)
        return
    elif "text_change_evening_" in call.data:
        id_chat = int(str(call.data).removeprefix("text_change_evening_"))
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>

<i>Введите вопрос опроса...</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_text_poll, id_chat, call, True)
        return
    elif "change_time_morning_" in call.data:
        id_chat = int(str(call.data).removeprefix("change_time_morning_"))
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

<i>Введите время опроса...</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_time_poll, id_chat, call, False)
        return
    elif "change_time_evening_" in call.data:
        id_chat = int(str(call.data).removeprefix("change_time_evening_"))
        
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>

<i>Введите время опроса...</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_time_poll, id_chat, call, True)
        return
    elif "text_change_" in call.data:
        id_chat = int(str(call.data).removeprefix("text_change_"))
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", id_chat)[0][1] if sql_exec.check("mailing", "chat_id", id_chat)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", id_chat)[0][2] if sql_exec.check("mailing", "chat_id", id_chat)[0][2] != None else "__:__"})</i>:
<code>{sql_exec.check("mailing", "chat_id", id_chat)[0][3] if sql_exec.check("mailing", "chat_id", id_chat)[0][3] != None else "____________________"}</code>

<i>Введите текст рассылки...</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_text, id_chat, call)
        return
    elif "text_time_morning_" in call.data:
        id_chat = int(str(call.data).removeprefix("text_time_morning_"))
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", id_chat)[0][1] if sql_exec.check("mailing", "chat_id", id_chat)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", id_chat)[0][2] if sql_exec.check("mailing", "chat_id", id_chat)[0][2] != None else "__:__"})</i>:
<code>{sql_exec.check("mailing", "chat_id", id_chat)[0][3] if sql_exec.check("mailing", "chat_id", id_chat)[0][3] != None else "____________________"}</code>

<i>Введите время начала рассылки...</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_time, id_chat, call, False)
        return
    elif "text_time_evening_" in call.data:
        id_chat = int(str(call.data).removeprefix("text_time_evening_"))
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", id_chat)[0][1] if sql_exec.check("mailing", "chat_id", id_chat)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", id_chat)[0][2] if sql_exec.check("mailing", "chat_id", id_chat)[0][2] != None else "__:__"})</i>:
<code>{sql_exec.check("mailing", "chat_id", id_chat)[0][3] if sql_exec.check("mailing", "chat_id", id_chat)[0][3] != None else "____________________"}</code>

<i>Введите время окончания рассылки...</i>
"""
        x = bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML")
        bot.register_next_step_handler(x, change_time, id_chat, call, True)
        return
    elif "morning_" in call.data:
        id_chat = int(str(call.data).removeprefix("morning_"))
        try: sql_exec.check("morning_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] if sql_exec.check("morning_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_morning = "____________________"
        morning_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", id_chat)[0][5])
            morning_options = eval(morning_options)
        except Exception as e:
            print(e)
            morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🌄 <i>Утренний опрос ({time_morning})</i>:
<b><i>{text_morning}</i></b>
• <code>{nl.join(morning_options)}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_morning(id_chat))  
        return
    elif "evening_" in call.data:
        id_chat = int(str(call.data).removeprefix("evening_"))
        try: sql_exec.check("evening_poll", "chat_id", id_chat)[0]
        except Exception as e:
            print(e)
            sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{id_chat},NULL,NULL,1,NULL,NULL") 
        try: time_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][1] != None else "__:__"
        except Exception as e:
            print(e)
            time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] if sql_exec.check("evening_poll", "chat_id", id_chat)[0][2] != None else "____________________"
        except Exception as e:
            print(e)
            text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", id_chat)[0][5])
            evening_options = eval(evening_options)
        except Exception as e:
            print(e)
            evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']
        
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>

🎆 <i>Вечерний опрос ({time_evening})</i>:
<b><i>{text_evening}</i></b>
• <code>{nl.join(evening_options)}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_evening(id_chat))
        return
    elif "mailing_" in call.data:
        id_chat = int(str(call.data).removeprefix("mailing_"))
        try: sql_exec.check("mailing", "chat_id", id_chat)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("mailing", "chat_id,start_time,end_time,text", f"{id_chat},NULL,NULL,NULL")
        text = f"""⚙️ <b>{bot.get_chat(id_chat).title}</b>
        
📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", id_chat)[0][1] if sql_exec.check("mailing", "chat_id", id_chat)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", id_chat)[0][2] if sql_exec.check("mailing", "chat_id", id_chat)[0][2] != None else "__:__"})</i>:
<code>{sql_exec.check("mailing", "chat_id", id_chat)[0][3] if sql_exec.check("mailing", "chat_id", id_chat)[0][3] != None else "____________________"}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_mailing(id_chat))   
        return
    elif call.data == 'show_settings': 
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Панель управления ботом</b>", parse_mode="HTML", reply_markup=settings(1))
        return
    elif len(sql_exec.check("chats", 'Unique_ID', call.data)) != 0:
        try: sql_exec.check("mailing", "chat_id", call.data)[0][1]
        except Exception as e:
            print(e)
            sql_exec.insert("mailing", "chat_id,start_time,end_time,text", f"{call.data},NULL,NULL,NULL")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=SENDER_TEXT_MAIN_CHAT, parse_mode="HTML", reply_markup=settings_chat(call.data))
        return
    elif "next_page_" in call.data:
        page = int(str(call.data).removeprefix("next_page_"))
        if page == count_page_chats or (count_page_chats == 1 and count_chats % 7 == 0): bot.answer_callback_query(call.id, text="Дальше листать некуда... Больше чатов у нас нет :(", show_alert=True)
        else: bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Панель управления ботом</b>", parse_mode="HTML", reply_markup=settings(page + 2))
        return
    elif "prev_page_" in call.data:
        page = int(str(call.data).removeprefix("prev_page_"))
        if page == 0: bot.answer_callback_query(call.id, text="Дальше листать некуда... Отрицательных страниц не существует :(", show_alert=True)
        else: bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="<b>Панель управления ботом</b>", parse_mode="HTML", reply_markup=settings(page))
        return
    else: 
        bot.answer_callback_query(call.id)
        return

def change_answer_poll(message, argument, call, evening):
    list_to_sql = ""
    message.text = html.escape(message.text)
    temp_list = str(message.text).split("_")
    if 0 < len(temp_list) <= 10:
        str_list = "['"
        str_list += "', '".join(temp_list)
        str_list += "']"
        list_to_sql = str_list
        if evening:
            sql_exec.set("evening_poll", "chat_id", argument, 'options', str_list)
        else:
            sql_exec.set("morning_poll", "chat_id", argument, 'options', str_list)       
    else:
        try: time_evening = sql_exec.check("evening_poll", "chat_id", argument)[0][1] if sql_exec.check("evening_poll", "chat_id", argument)[0][1] != None else "__:__"
        except: time_evening = "__:__"
        try: text_evening = sql_exec.check("evening_poll", "chat_id", argument)[0][2] if sql_exec.check("evening_poll", "chat_id", argument)[0][2] != None else "____________________"
        except: text_evening = "____________________"
        evening_options = ['____________________']
        nl = '</code>\n• <code>'
        try:
            evening_options = str(sql_exec.check("evening_poll", "chat_id", argument)[0][5])
            evening_options = eval(evening_options)
        except: evening_options = ['____________________']
        if isinstance(evening_options, list): pass
        else: evening_options = ['____________________']

        nl = '</code>\n• <code>'
        try:
            morning_options = str(sql_exec.check("morning_poll", "chat_id", argument)[0][5])
            morning_options = eval(morning_options)
        except: morning_options = ['____________________']
        if isinstance(morning_options, list): pass
        else: morning_options = ['____________________']
        try: time_morning = sql_exec.check("morning_poll", "chat_id", argument)[0][1] if sql_exec.check("morning_poll", "chat_id", argument)[0][1] != None else "__:__"
        except: time_morning = "__:__"
        try: text_morning = sql_exec.check("morning_poll", "chat_id", argument)[0][2] if sql_exec.check("morning_poll", "chat_id", argument)[0][2] != None else "____________________"
        except: text_morning = "____________________"
        text = f"""⚙️ <b>{bot.get_chat(argument).title}</b>

{"🌄" if not evening else "🎆"} <i>{"Утренний" if not evening else "Вечерний"} опрос ({time_morning if not evening else time_evening})</i>:
<b><i>{text_evening if evening else text_morning }</i></b>
• <code>{nl.join(morning_options) if not evening else nl.join(evening_options)}</code>

<i>Используйте кнопки ниже для редактрирования...</i>

<i><b>Вы указали более 10 пунктов!</b></i>
"""
    
        if evening:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_evening(argument))
        else:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_morning(argument))
        bot.delete_message(message.chat.id, message.message_id)
        return

    try: sql_exec.check("morning_poll", "chat_id", argument)[0]
    except: sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{argument},NULL,NULL,1,NULL,NULL") 
    try: time_morning = sql_exec.check("morning_poll", "chat_id", argument)[0][1] if sql_exec.check("morning_poll", "chat_id", argument)[0][1] != None else "__:__"
    except: time_morning = "__:__"
    try: text_morning = sql_exec.check("morning_poll", "chat_id", argument)[0][2] if sql_exec.check("morning_poll", "chat_id", argument)[0][2] != None else "____________________"
    except: text_morning = "____________________"
    morning_options = ['____________________']
    nl = '</code>\n• <code>'
    try:
        morning_options = str(sql_exec.check("morning_poll", "chat_id", argument)[0][5])
        morning_options = eval(morning_options)
    except: morning_options = ['____________________']
    if isinstance(morning_options, list): pass
    else: morning_options = ['____________________']
    
    try: sql_exec.check("evening_poll", "chat_id", argument)[0]
    except: sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{argument},NULL,NULL,1,NULL,NULL") 
    try: time_evening = sql_exec.check("evening_poll", "chat_id", argument)[0][1] if sql_exec.check("evening_poll", "chat_id", argument)[0][1] != None else "__:__"
    except: time_evening = "__:__"
    try: text_evening = sql_exec.check("evening_poll", "chat_id", argument)[0][2] if sql_exec.check("evening_poll", "chat_id", argument)[0][2] != None else "____________________"
    except: text_evening = "____________________"
    evening_options = ['____________________']
    nl = '</code>\n• <code>'
    try:
        evening_options = str(sql_exec.check("evening_poll", "chat_id", argument)[0][5])
        evening_options = eval(evening_options)
    except: evening_options = ['____________________']
    if isinstance(evening_options, list): pass
    else: evening_options = ['____________________']
    
    text = f"""⚙️ <b>{bot.get_chat(argument).title}</b>

{"🌄" if not evening else "🎆"} <i>{"Утренний" if not evening else "Вечерний"} опрос ({time_morning if not evening else time_evening})</i>:
<b><i>{text_evening if evening else text_morning }</i></b>
• <code>{nl.join(morning_options) if not evening else nl.join(evening_options)}</code>
<i>Используйте кнопки ниже для редактрирования...</i>
"""
    
    if evening:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_evening(argument))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_morning(argument))
    bot.delete_message(message.chat.id, message.message_id)
    return

def change_time(message, argument, call, end_time):
    message.text = html.escape(message.text)
    if end_time: sql_exec.set("mailing", "chat_id", argument, "end_time", message.text)
    else: sql_exec.set("mailing", "chat_id", argument, "start_time", message.text)
    text = f"""⚙️ <b>{bot.get_chat(argument).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", argument)[0][1] if sql_exec.check("mailing", "chat_id", argument)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", argument)[0][2] if sql_exec.check("mailing", "chat_id", argument)[0][2] != None else "__:__"})</i>:
<code>{sql_exec.check("mailing", "chat_id", argument)[0][3] if sql_exec.check("mailing", "chat_id", argument)[0][3] != None else "____________________"}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_mailing(argument))
    bot.delete_message(message.chat.id, message.message_id)

def change_text(message, argument, call):
    message.text = html.escape(message.text)
    sql_exec.set("mailing", "chat_id", argument, "text", message.text)
    text = f"""⚙️ <b>{bot.get_chat(argument).title}</b>

📩 <i>Рассылка ({sql_exec.check("mailing", "chat_id", argument)[0][1] if sql_exec.check("mailing", "chat_id", argument)[0][1] != None else "__:__"} - {sql_exec.check("mailing", "chat_id", argument)[0][2] if sql_exec.check("mailing", "chat_id", argument)[0][2] != None else "__:__"})</i>:
<code>{sql_exec.check("mailing", "chat_id", argument)[0][3] if sql_exec.check("mailing", "chat_id", argument)[0][3] != None else "____________________"}</code>

<i>Используйте кнопки ниже для редактрирования...</i>
"""
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_mailing(argument))
    bot.delete_message(message.chat.id, message.message_id)

def change_text_poll(message, argument, call, evening):
    message.text = html.escape(message.text)
    if evening: sql_exec.set("evening_poll", "chat_id", argument, "question", message.text)
    else: sql_exec.set("morning_poll", "chat_id", argument, "question", message.text)
    try: sql_exec.check("morning_poll", "chat_id", argument)[0]
    except: sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{argument},NULL,NULL,1,NULL,NULL") 
    try: time_morning = sql_exec.check("morning_poll", "chat_id", argument)[0][1] if sql_exec.check("morning_poll", "chat_id", argument)[0][1] != None else "__:__"
    except: time_morning = "__:__"
    try: text_morning = sql_exec.check("morning_poll", "chat_id", argument)[0][2] if sql_exec.check("morning_poll", "chat_id", argument)[0][2] != None else "____________________"
    except: text_morning = "____________________"
    morning_options = ['____________________']
    nl = '</code>\n• <code>'
    try:
        morning_options = str(sql_exec.check("morning_poll", "chat_id", argument)[0][5])
        morning_options = eval(morning_options)
    except: morning_options = ['____________________']
    if isinstance(morning_options, list): pass
    else: morning_options = ['____________________']
    

    try: sql_exec.check("evening_poll", "chat_id", argument)[0]
    except: sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{argument},NULL,NULL,1,NULL,NULL") 
    try: time_evening = sql_exec.check("evening_poll", "chat_id", argument)[0][1] if sql_exec.check("evening_poll", "chat_id", argument)[0][1] != None else "__:__"
    except: time_evening = "__:__"
    try: text_evening = sql_exec.check("evening_poll", "chat_id", argument)[0][2] if sql_exec.check("evening_poll", "chat_id", argument)[0][2] != None else "____________________"
    except: text_evening = "____________________"
    evening_options = ['____________________']
    nl = '</code>\n• <code>'
    try:
        evening_options = str(sql_exec.check("evening_poll", "chat_id", argument)[0][5])
        evening_options = eval(evening_options)
    except: evening_options = ['____________________']
    if isinstance(evening_options, list): pass
    else: evening_options = ['____________________']
    
    text = f"""⚙️ <b>{bot.get_chat(argument).title}</b>

{"🌄" if not evening else "🎆"} <i>{"Утренний" if not evening else "Вечерний"} опрос ({time_morning if not evening else time_evening})</i>:
<b><i>{text_evening if evening else text_morning }</i></b>
• <code>{nl.join(morning_options) if not evening else nl.join(evening_options)}</code>
<i>Используйте кнопки ниже для редактрирования...</i>
"""
    if evening:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_evening(argument))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_morning(argument))
    bot.delete_message(message.chat.id, message.message_id)

def change_time_poll(message, argument, call, evening):
    message.text = html.escape(message.text)
    if evening: sql_exec.set("evening_poll", "chat_id", argument, "time", message.text)
    else: sql_exec.set("morning_poll", "chat_id", argument, "time", message.text)
    try: sql_exec.check("morning_poll", "chat_id", argument)[0]
    except Exception as e:
        print(e)
        sql_exec.insert("morning_poll", "chat_id,time,question,anonim,multiply,options", f"{argument},NULL,NULL,1,NULL,NULL") 
    try: time_morning = sql_exec.check("morning_poll", "chat_id", argument)[0][1] if sql_exec.check("morning_poll", "chat_id", argument)[0][1] != None else "__:__"
    except Exception as e:
        print(e)
        time_morning = "__:__"
    try: text_morning = sql_exec.check("morning_poll", "chat_id", argument)[0][2] if sql_exec.check("morning_poll", "chat_id", argument)[0][2] != None else "____________________"
    except Exception as e:
        print(e)
        text_morning = "____________________"
    morning_options = ['____________________']
    nl = '</code>\n• <code>'
    try:
        morning_options = str(sql_exec.check("morning_poll", "chat_id", argument)[0][5])
        morning_options = eval(morning_options)
    except Exception as e:
        print(e)
        morning_options = ['____________________']
    if isinstance(morning_options, list): pass
    else: morning_options = ['____________________']
    

    try: sql_exec.check("evening_poll", "chat_id", argument)[0]
    except Exception as e:
        print(e)
        sql_exec.insert("evening_poll", "chat_id,time,question,anonim,multiply,options", f"{argument},NULL,NULL,1,NULL,NULL") 
    try: time_evening = sql_exec.check("evening_poll", "chat_id", argument)[0][1] if sql_exec.check("evening_poll", "chat_id", argument)[0][1] != None else "__:__"
    except Exception as e:
        print(e)
        time_evening = "__:__"
    try: text_evening = sql_exec.check("evening_poll", "chat_id", argument)[0][2] if sql_exec.check("evening_poll", "chat_id", argument)[0][2] != None else "____________________"
    except Exception as e:
        print(e)
        text_evening = "____________________"
    evening_options = ['____________________']
    nl = '</code>\n• <code>'
    try:
        evening_options = str(sql_exec.check("evening_poll", "chat_id", argument)[0][5])
        evening_options = eval(evening_options)
    except Exception as e:
        print(e)
        evening_options = ['____________________']
    if isinstance(evening_options, list): pass
    else: evening_options = ['____________________']
    
    text = f"""⚙️ <b>{bot.get_chat(argument).title}</b>

{"🌄" if not evening else "🎆"} <i>{"Утренний" if not evening else "Вечерний"} опрос ({time_morning if not evening else time_evening})</i>:
<b><i>{text_evening if evening else text_morning }</i></b>
• <code>{nl.join(morning_options) if not evening else nl.join(evening_options)}</code>
<i>Используйте кнопки ниже для редактрирования...</i>
"""
    if evening:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_evening(argument))
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=text, parse_mode="HTML", reply_markup=settings_morning(argument))
    bot.delete_message(message.chat.id, message.message_id)

async def send_mailing():
    while True:
        for x in sql_exec.return_table("mailing"):
            try:
                if (x[0] != None and len(x[0]) != 0) and (x[1] != None and len(x[1]) != 0) and (x[2] != None and len(x[2]) != 0) and (x[3] != None and len(x[3]) != 0):
                    chat_id = x[0]
                    start_time = x[1]
                    end_time = x[2]
                    text = x[3]
                    text = html.escape(text)
                    current_time = datetime.now(pytz.timezone("Europe/Moscow"))
                    x = datetime.strptime(start_time, '%H:%M').time()
                    y = datetime.strptime(end_time, '%H:%M').time()
                    if current_time.time() >= x:
                        if current_time.time() < y:
                            await send_mail(chat_id, text) 
            except Exception as e:
                print(e)

        await asyncio.sleep(20)

async def send_poll():
    while True:
        for x in sql_exec.return_table("morning_poll"):
            try:
                if (x[0] != None and len(x[0]) != 0) and (x[1] != None and len(x[1]) != 0) and (x[2] != None and len(x[2]) != 0) and (x[3] != None and len(x[3]) != 0) and (x[5] != None and len(x[5]) != 0):
                    chat_id      = x[0]
                    time         = x[1]
                    question     = x[2]
                    if x[3] == None or len(x[3]) == 0:
                        anonim = "0"
                    else:
                        anonim = x[3]
                    if x[4] == None or len(x[4]) == 0:
                        multiply = "0"
                    else:
                        multiply = x[4]
                    options      = x[5]
                    question = html.escape(question)
                    current_time = datetime.now(pytz.timezone("Europe/Moscow"))
                    x = datetime.strptime(time, '%H:%M').time()
                    if current_time.time() > x:
                        if current_time.time() < datetime.strptime(add_minute(time), '%H:%M').time():
                            print(type(chat_id), chat_id)
                            print(type(question), question)
                            print(type(anonim), anonim)
                            print(type(multiply), multiply)
                            print(type(options), options)
                            await send_poll_chat(chat_id, question, anonim, multiply, options)
            except Exception as e:
                print(e)

        for x in sql_exec.return_table("evening_poll"):
            try:
                if (x[0] != None and len(x[0]) != 0) and (x[1] != None and len(x[1]) != 0) and (x[2] != None and len(x[2]) != 0) and (x[3] != None and len(x[3]) != 0) and (x[5] != None and len(x[5]) != 0):
                    chat_id      = x[0]
                    time         = x[1]
                    question     = x[2]
                    if x[3] == None or len(x[3]) == 0:
                        anonim = "0"
                    else:
                        anonim = x[3]
                    if x[4] == None or len(x[4]) == 0:
                        multiply = "0"
                    else:
                        multiply = x[4]
                    options      = x[5]
                    question = html.escape(question)
                    current_time = datetime.now(pytz.timezone("Europe/Moscow"))
                    x = datetime.strptime(time, '%H:%M').time()
                    if current_time.time() > x:
                        if current_time.time() < datetime.strptime(add_minute(time), '%H:%M').time():
                            print(type(chat_id), chat_id)
                            print(type(question), question)
                            print(type(anonim), anonim)
                            print(type(multiply), multiply)
                            print(type(options), options)
                            await send_poll_chat(chat_id, question, anonim, multiply, options)
            except Exception as e:
                print(e)
        await asyncio.sleep(55)

async def send_poll_chat(chat_id, question, anonim, multiply, options):
    x = [html.unescape(option) for option in eval(options)]
    bot.send_poll(chat_id, question, x, bool(int(anonim)), allows_multiple_answers=bool(int(multiply)))

async def send_mail(chat_id, text):
    print(str(html.unescape(text)))
    bot.send_message(chat_id, str(html.unescape(text)), parse_mode="Markdown")

def bot_polling():
    bot.infinity_polling(timeout=300)

def start_send_mailing():
    asyncio.run(send_mailing())

def start_send_poll_thread():
    asyncio.run(send_poll())

def main():
    send_mailing_thread = threading.Thread(target=start_send_mailing)
    send_poll_thread = threading.Thread(target=start_send_poll_thread)
    bot_polling_thread = threading.Thread(target=bot_polling)
    send_mailing_thread.start()
    bot_polling_thread.start()
    send_poll_thread.start()
    send_mailing_thread.join()
    bot_polling_thread.join()
    send_poll_thread.join()

if __name__ == "__main__":
    main()


