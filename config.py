import os

from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
TG_API_URL = 'https://api.telegram.org'
DB_PATH = 'db/users.db'
