import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuración básica de Nova Solar MX
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'nova-solar-mx-dev-key-2025'
    
    # Información de la empresa
    COMPANY_NAME = 'Nova Solar MX'
    SITE_NAME = 'Nova Solar MX'
    SITE_URL = os.environ.get('SITE_URL') or 'https://novasolarmx.com'
    DOMAIN = 'novasolarmx.com'
    
    # Base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///nova_solar_mx.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuración
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp-mail.outlook.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'mxnovasun@outlook.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Nova Solar MX <mxnovasun@outlook.com>')
    
    # Contact information
    CONTACT_EMAIL = 'mxnovasun@outlook.com'
    SUPPORT_EMAIL = 'mxnovasun@outlook.com'
    BUSINESS_EMAIL = 'mxnovasun@outlook.com'
    
    # Analytics y tracking
    GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID')
    FACEBOOK_PIXEL_ID = os.environ.get('FACEBOOK_PIXEL_ID')
    GOOGLE_TAG_MANAGER_ID = os.environ.get('GOOGLE_TAG_MANAGER_ID')
    
    # Partners y afiliados
    AMAZON_AFFILIATE_ID = os.environ.get('AMAZON_AFFILIATE_ID', 'novasolarmx-20')
    HOTMART_AFFILIATE_ID = os.environ.get('HOTMART_AFFILIATE_ID')
    TEMU_AFFILIATE_ID = os.environ.get('TEMU_AFFILIATE_ID')
    ALIEXPRESS_AFFILIATE_ID = os.environ.get('ALIEXPRESS_AFFILIATE_ID')
    
    # SEO y meta tags
    DEFAULT_META_TITLE = 'Nova Solar MX - Calculadora Solar Profesional'
    DEFAULT_META_DESCRIPTION = 'La calculadora solar más avanzada de México. Calcula tu sistema solar para hogar y vehículo eléctrico. Equipos premium, incentivos gubernamentales.'
    DEFAULT_KEYWORDS = 'paneles solares, energía solar México, calculadora solar, vehículo eléctrico, Nova Solar MX'
    
    # Configuración de la aplicación
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL')
    
    # Session configuración
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SUPPRESS_SEND = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    MAIL_SUPPRESS_SEND = False
    
    # Configuración específica de producción
    PREFERRED_URL_SCHEME = 'https'
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block'
    }

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    MAIL_SUPPRESS_SEND = True

# Configuración automática basada en environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}