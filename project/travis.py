from .base_settings import *  # noqa

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '294xJnzB5UkIJksvV8vU0D4n16MfEw46mJCKn6l7'  # noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_jutil',
        'USER': 'postgres',
        'PASSWORD': '',  # noqa
        'HOST': 'localhost',
        'PORT': 5432,
        'CONN_MAX_AGE': 180,
    }
}

# IP stack (IP country code)
IPSTACK_TOKEN = ''
