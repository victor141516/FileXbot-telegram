import os

API_TOKEN = os.getenv('API_TOKEN', None)

DB_USER = os.getenv('DB_USER', None)
DB_PASSWORD = os.getenv('DB_PASSWORD', None)
DB_HOST = os.getenv('DB_HOST', None)
DB_NAME = os.getenv('DB_NAME', None)
DB_URL = "postgres://" + DB_USER + ":" + DB_PASSWORD + "@" + DB_HOST + "/" + DB_NAME

POLLING = os.getenv('POLLING', "1") == "1"
BOT_NAME = os.getenv('BOT_NAME', None)
DEBUG_MODE = os.getenv('DEBUG_MODE', "0") == "1"
WEBHOOK_URL = os.getenv('WEBHOOK_URL', None)
MAX_FILES_PER_PAGE = int(os.getenv('MAX_FILES_PER_PAGE', None))
