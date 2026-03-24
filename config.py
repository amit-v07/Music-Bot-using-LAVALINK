import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    google_api_key = os.getenv('GOOGLE_API_KEY')
    error_log_file = 'bot_errors.log'

config = Config()
