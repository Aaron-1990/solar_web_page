import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-cambiar-en-produccion'
    
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///energia_solar_360.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@energiasolar360.mx')
    
    # Analytics
    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID')
    FACEBOOK_PIXEL_ID = os.environ.get('FACEBOOK_PIXEL_ID')
    
    # Partners/Afiliados
    AMAZON_AFFILIATE_ID = os.environ.get('AMAZON_AFFILIATE_ID', 'tu-id-20')
    HOTMART_AFFILIATE_ID = os.environ.get('HOTMART_AFFILIATE_ID')
