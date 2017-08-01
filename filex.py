# -*- coding: utf-8 -*-

from flask import Flask, request
import os
from re import escape
import psycopg2
import psycopg2.extras
import telebot
import threading

class DbHandler(object):
    def __init__(self, db_name):
        super(DbHandler, self).__init__()
        self.db_name = db_name
        self.db = psycopg2.connect(self.db_name)

    def __db_connect__(self):
        self.cursor = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def __db_disconnect__(self):
        pass

    def insert(self, table, values, updater=None):
        try:
            self.__db_connect__()
            if (not updater):
                updater = values

            updater_str = ', '.join([(k + (" is " if updater[k] == "NULL" else "=") + ("NULL" if updater[k] == "NULL" else ("'" + str(updater[k]) + "'"))) for k in updater.keys()])
            values_str = ', '.join([("NULL" if updater[k] == "NULL" else ("'" + str(updater[k]) + "'")) for k in values.keys()])
            columns_str = ', '.join([str(k) for k in values.keys()])
            where_str = ' AND '.join([(k + (" is " if updater[k] == "NULL" else "=") + ("NULL" if updater[k] == "NULL" else ("'" + str(updater[k]) + "'"))) for k in updater.keys()])
            exists = len(self.select(table, where_str))

            if (exists):
                values_str = ', '.join([(k + "=" + ("NULL" if updater[k] == "NULL" else ("'" + str(updater[k]) + "'"))) for k in values.keys()])
                self.cursor.execute("UPDATE " + table + " SET " + values_str + " WHERE " + where_str)
                self.db.commit()
                self.__db_disconnect__()
                return True

            self.cursor.execute("INSERT INTO " + table + "(" + columns_str + ") VALUES (" + values_str + ")")
            self.db.commit()
            self.__db_disconnect__()
            return True
        except Exception as e:
            print(e)
            self.__db_disconnect__()
            return False

    def select(self, table, where=None):
        try:
            self.__db_connect__()
            if (where):
                self.cursor.execute("SELECT '" + table + "' as type, * FROM " + table + " WHERE (" + where + ")")
            else:
                self.cursor.execute("SELECT '" + table + "' as type, * FROM " + table)
            data = self.cursor.fetchall()
            self.__db_disconnect__()
            return data
        except Exception as e:
            print(e)
            self.__db_disconnect__()
            return False

    def delete(self, table, where=None):
        try:
            self.__db_connect__()
            if (where):
                self.cursor.execute("DELETE FROM " + table + " WHERE (" + where + ")")
            else:
                self.cursor.execute("DELETE FROM " + table)
            self.db.commit()
            self.__db_disconnect__()
            return True
        except Exception as e:
            print(e)
            self.__db_disconnect__()
            return False
class Explorer(object):
    def __init__(self, telegram_id):
        super(Explorer, self).__init__()
        self.user = db.select('users', "telegram_id = " + str(telegram_id))[0]
        self.path = [db.select('directories', "name = '/' AND parent_directory_id is NULL AND user_id = " + str(self.user['id']))[0]['id']]
        self.last_action_message_ids = []
        self.explorer_list_position = 0
        self.explorer_list_size = 0

    def get_path_string(self):
        if (len(self.path) == 1):
            return '/'
        try:
            directory_ids_string = ', '.join([(str(int(each))) for each in self.path])
        except Exception as e:
            return False
        directories = db.select('directories', "id in (" + directory_ids_string + ")")
        directories[:] = [d for d in directories if d.get('name') != '/']
        return '/' + ('/'.join([(directory['name']) for directory in directories]))


    def get_directory_content(self, directory_id=None):
        if (len(self.path) == 0):
            self.__init__(self.user['telegram_id'])
        if (not directory_id):
            directory_id = self.path[-1:][0]
        try:
            str(int(directory_id))
        except Exception as e:
            return False

        directories = db.select('directories', "parent_directory_id = " + str(directory_id) + " AND user_id = " + str(self.user['id']))
        directories = sorted(directories, key=lambda x: x['name'].lower())

        files = db.select('files', "directory_id = " + str(directory_id) + " AND user_id = " + str(self.user['id']))
        files = sorted(files, key=lambda x: x['name'].lower())

        elements = directories + files
        self.explorer_list_size = len(elements)
        elements = elements[self.explorer_list_position * MAX_FILES_PER_PAGE   :   (self.explorer_list_position+1) * MAX_FILES_PER_PAGE]

        return elements

    def go_to_directory(self, directory_id):
        try:
            str(int(directory_id))
        except Exception as e:
            return False
        directory_id = db.select('directories', "id = " + directory_id)[0]['id']
        self.path.append(directory_id)
        self.explorer_list_position = 0

    def go_to_parent_directory(self):
        if (len(self.path) == 0):
            self.__init__(self.user['telegram_id'])
        self.path = self.path[:-1]
        self.explorer_list_position = 0

    def new_directory(self, directory_name, parent_directory_id=None):
        if (not parent_directory_id):
            parent_directory_id = self.path[-1:][0]
        return db.insert('directories', {'name': directory_name.replace("'", "").replace('"', ""), 'parent_directory_id': parent_directory_id, 'user_id': self.user['id']})

    def new_file(self, telegram_id, name, mime, size, directory_id=None):
        if (not directory_id):
            directory_id = self.path[-1:][0]
        return db.insert('files', {'name': name.replace("'", "").replace('"', ""), 'mime': mime, 'size': size, 'telegram_id': telegram_id, 'directory_id': directory_id, 'user_id': self.user['id']})

    def remove_files(self, file_ids):
        try:
            file_ids_string = ', '.join([(str(int(each))) for each in file_ids])
        except Exception as e:
            return False
        db.delete('files', "id in (" + file_ids_string + ")")

    def remove_directories(self, directory_ids):
        try:
            directory_ids_string = ', '.join([(str(int(each))) for each in directory_ids])
        except Exception as e:
            return False

        for directory_id in directory_ids:
            content = self.get_directory_content(directory_id)
            self.remove_files([each['id'] for each in content])
        db.delete('directories', "id in (" + directory_ids_string + ")")



API_TOKEN = ''
WEBHOOK_URL = ""
DB_URL = ''
POLLING = False
MAX_FILES_PER_PAGE = 10

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()
cur.execute('CREATE TABLE IF NOT EXISTS "users" (id SERIAL PRIMARY KEY, name VARCHAR(100), telegram_id INTEGER);')
cur.execute('CREATE TABLE IF NOT EXISTS "files" (id SERIAL PRIMARY KEY, name VARCHAR(300), mime VARCHAR(100), size REAL, telegram_id INTEGER, directory_id INTEGER, user_id INTEGER);')
cur.execute('CREATE TABLE IF NOT EXISTS "directories" (id SERIAL PRIMARY KEY, name VARCHAR(300), parent_directory_id INTEGER, user_id INTEGER);')
conn.close()


db = DbHandler(DB_URL)
server = Flask(__name__)
explorers = {}
bot = telebot.TeleBot(API_TOKEN)
mime_conv = {'application/epub+zip' : 'D', 'application/java-archive' : 'D', 'application/javascript' : 'D', 'application/json' : 'D', 'application/msword' : 'D', 'application/octet-stream' : 'D', 'application/octet-stream' : 'D', 'application/ogg' : 'A', 'application/pdf' : 'D', 'application/rtf' : 'D', 'application/vnd.amazon.ebook' : 'D', 'application/vnd.apple.installer+xml' : 'D', 'application/vnd.mozilla.xul+xml' : 'D', 'application/vnd.ms-excel' : 'D', 'application/vnd.ms-powerpoint' : 'D', 'application/vnd.oasis.opendocument.presentation' : 'D', 'application/vnd.oasis.opendocument.spreadsheet' : 'D', 'application/vnd.oasis.opendocument.text' : 'D', 'application/vnd.visio' : 'D', 'application/x-abiword' : 'D', 'application/x-bzip' : 'D', 'application/x-bzip2' : 'D', 'application/x-csh' : 'D', 'application/x-rar-compressed' : 'D', 'application/x-sh' : 'D', 'application/x-shockwave-flash' : 'D', 'application/x-tar' : 'D', 'application/xhtml+xml' : 'D', 'application/xml' : 'D', 'application/zip' : 'D', 'audio/aac' : 'A', 'audio/midi' : 'A', 'audio/ogg' : 'A', 'audio/webm' : 'A', 'audio/x-wav' : 'A', 'font/ttf' : 'D', 'font/woff' : 'D', 'font/woff2' : 'D', 'image/gif' : 'P', 'image/jpeg' : 'P', 'image/svg+xml' : 'P', 'image/tiff' : 'P', 'image/webp' : 'P', 'image/x-icon' : 'P', 'text/calendar' : 'D', 'text/css' : 'D', 'text/csv' : 'D', 'text/html' : 'D', 'video/3gpp' : 'V', 'video/3gpp2' : 'V', 'video/mpeg' : 'V', 'video/ogg' : 'V', 'video/webm' : 'V', 'video/x-msvideo' : 'V'}
icon_mime = {'A' : '🎵', 'D' : '📄', 'P' : '🏞', 'U' : '❔', 'V' : '📹 '}
help_message = "- Write /start to begin\n- You can send files, images, videos, etc. and they will be stored in your current path\n- If you write a message to the bot, it will make a directory with that name in the current path\n- You can forward text messages from other chats and they will be stored as notes\n- You can delete files or directories using the red cross next to them\n- I have tried to make this bot as similar as possible to a basic file explorer\n- You can donate using /donate\n- Ideas and suggestions to @victor141516"


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, help_message)

@bot.message_handler(commands=['donate'])
def help(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('PayPal', url='https://www.paypal.me/victor141516'))
    bot.send_message(message.from_user.id, "Thank you!", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    telegram_id = message.from_user.id

    bot.send_message(telegram_id, help_message)
    db.insert('users', {'name': message.from_user.username, 'telegram_id': telegram_id}, {'telegram_id' : telegram_id})
    user_id = db.select('users', "telegram_id = " + str(telegram_id))[0]['id']

    db.insert('directories', {'name': '/', 'parent_directory_id': "NULL", 'user_id': user_id})

    get_or_create_explorer(telegram_id)
    send_replacing_message(telegram_id, bot)

@bot.message_handler(content_types=['document', 'audio', 'document', 'photo', 'video', 'video_note', 'voice', 'contact'])
def handle_docs(message):
    telegram_id = message.from_user.id
    explorer = get_or_create_explorer(telegram_id)

    if (message.document != None):
        if (message.document.mime_type in mime_conv):
            mime = mime_conv[message.document.mime_type]
        else:
            mime = 'U'
        explorer.new_file(message.message_id, message.document.file_name, mime, message.document.file_size)
    elif (message.audio != None):
        explorer.new_file(message.message_id, "audio" + str(message.date), 'A', message.audio.file_size)
    elif (message.document != None):
        explorer.new_file(message.message_id, "document" + str(message.date), 'D', message.document.file_size)
    elif (message.photo != None):
        explorer.new_file(message.message_id, "photo" + str(message.date), 'P', message.photo[0].file_size)
    elif (message.video != None):
        explorer.new_file(message.message_id, "video" + str(message.date), 'V', message.video.file_size)
    elif (message.video_note != None):
        explorer.new_file(message.message_id, "video_note" + str(message.date), 'V', message.video_note.file_size)
    elif (message.voice != None):
        explorer.new_file(message.message_id, "voice" + str(message.date), 'A', message.voice.file_size)
    elif (message.contact != None):
        explorer.new_file(message.message_id, "contact" + str(message.date), 'D', message.contact.file_size)
    elif (message.text != None):
        explorer.new_file(message.message_id, message.text.split('\n', 1)[0], 'D', len(message.text))


    send_replacing_message(telegram_id, bot)

@bot.message_handler(func=lambda m: True)
def text_message(message):
    if (message.forward_from):
        return handle_docs(message)

    new_directory_name = message.text
    telegram_id = message.from_user.id
    explorer = get_or_create_explorer(telegram_id)
    explorer.new_directory(new_directory_name)
    content = explorer.get_directory_content()
    keyboard = content_builder(content, len(explorer.path) > 1)
    remove_messages(telegram_id, bot)
    message_sent = bot.send_message(telegram_id, explorer.get_path_string(), reply_markup=keyboard)
    explorer.last_action_message_ids.append(message_sent.message_id)


@bot.message_handler(func=lambda m: True)
def new_directory(message):
    new_directory_name = message.text
    telegram_id = message.from_user.id
    explorer = get_or_create_explorer(telegram_id)
    explorer.new_directory(new_directory_name)
    content = explorer.get_directory_content()
    keyboard = content_builder(content, len(explorer.path) > 1)
    remove_messages(telegram_id, bot)
    message_sent = bot.send_message(telegram_id, explorer.get_path_string(), reply_markup=keyboard)
    explorer.last_action_message_ids.append(message_sent.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    telegram_id = call.from_user.id
    explorer = get_or_create_explorer(telegram_id)
    action = call.data[:1]
    content_id = call.data[1:]

    if (call.data == ".."):
        explorer.go_to_parent_directory()

    if (call.data == "."):
        pass

    elif (action == "d"):
        explorer.go_to_directory(content_id)

    elif (action == "f"):
        content_id = db.select('files', "id = " + content_id)[0]['telegram_id']
        bot.forward_message(telegram_id, telegram_id, content_id)

    elif (action == "r"):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton('✅', callback_data='c' + call.data),
            telebot.types.InlineKeyboardButton('❌', callback_data='.')
        )
        message_sent = bot.send_message(telegram_id, "Are you sure?", reply_markup=markup)
        explorer.last_action_message_ids.append(message_sent.message_id)
        return

    elif (action == "c"):
        action = content_id[:1]
        content_id = content_id[1:]
        if (action == "r"):
            is_directory = content_id[:1] == "d"
            content_id = content_id[1:]
            if (is_directory):
                explorer.remove_directories([content_id])
            else:
                explorer.remove_files([content_id])

    elif (action == "p"):
        explorer.explorer_list_position = explorer.explorer_list_position -1
    elif (action == "n"):
        explorer.explorer_list_position = explorer.explorer_list_position+1

    send_replacing_message(telegram_id, bot)
def remove_messages(telegram_id, bot):
    explorer = get_or_create_explorer(telegram_id)
    result = []
    if (explorer.last_action_message_ids):
        for message_id in explorer.last_action_message_ids:
            try:
                result.append(bot.delete_message(telegram_id, message_id))
                explorer.last_action_message_ids.remove(message_id)
            except Exception as e:
                print(e)
    return result

def get_or_create_explorer(id):
    if (id not in explorers):
        explorers[id] = Explorer(id)
    return explorers[id]

def content_builder(content, up = True, previous_p = False, next_p = False):
    markup = telebot.types.InlineKeyboardMarkup()

    if (up):
        markup.add(telebot.types.InlineKeyboardButton('⤴️ Go up', callback_data='..'))

    if (previous_p):
        markup.add(telebot.types.InlineKeyboardButton('⏮ Previous', callback_data='p'))

    for each in content:
        if (each["type"] == "directories"):
            icon = "📁"
        elif (each['mime'] in icon_mime):
            icon = icon_mime[each['mime']]
        else:
            icon = icon_mime['U']
        markup.add(
                telebot.types.InlineKeyboardButton(icon + " " + each['name'], callback_data=("f" if each["type"] == "files" else "d") + str(each['id'])),
                telebot.types.InlineKeyboardButton("❌", callback_data="rd" + str(each['id'])),
            )

    if (next_p):
        markup.add(telebot.types.InlineKeyboardButton('Next ⏭', callback_data='n'))

    return markup

def send_replacing_message(telegram_id, bot):
    explorer = get_or_create_explorer(telegram_id)
    content = explorer.get_directory_content()
    previous_p = explorer.explorer_list_position > 0
    next_p = explorer.explorer_list_size - (explorer.explorer_list_position * MAX_FILES_PER_PAGE) > MAX_FILES_PER_PAGE
    keyboard = content_builder(content, len(explorer.path) > 1, previous_p, next_p)
    remove_messages(telegram_id, bot)
    message_sent = bot.send_message(telegram_id, "**Path:** " + explorer.get_path_string(), reply_markup=keyboard, parse_mode="Markdown")
    explorer.last_action_message_ids.append(message_sent.message_id)





@server.route("/bot", methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + "/bot")
    return "!", 200


bot.remove_webhook()

if (POLLING):
    bot.polling()
else:
    server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))


