import os
from dotenv import load_dotenv
import openai

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave_secreta")
    UPLOAD_FOLDER = 'static/uploads'
    TEXT_FOLDER = 'extracted_texts'
    LOG_FOLDER = 'logs'
    ALLOWED_EXTENSIONS = {'pdf'}
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")