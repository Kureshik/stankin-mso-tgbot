import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_BOT_TOKEN")
ADMINS = os.getenv("ADMINS", "")

def is_admin(user_id) -> bool:
    return str(user_id) in ADMINS
