import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///confidence_detector.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    
    # IMAP Email Settings
    IMAP_SERVER = os.environ.get('IMAP_SERVER', 'imap.gmail.com')
    TEACHER_EMAIL = os.environ.get('TEACHER_EMAIL', '')
    TEACHER_EMAIL_PASSWORD = os.environ.get('TEACHER_EMAIL_PASSWORD', '')
