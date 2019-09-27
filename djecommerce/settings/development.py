from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'debug_toolbar'
]

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]

# DEBUG TOOLBAR SETTINGS

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': show_toolbar
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'Ecom',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '',
    }
}

STRIPE_PUBLIC_KEY = 'pk_test_dhVvGuD9Ond4lgXl3hN4IJ8h00pofyiHp1'
STRIPE_SECRET_KEY = 'sk_test_y06mC0pt4IZiRwSgRrlIoHgG00HtlLJzlG'
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND ="django.core.mail.backends.smtp.EmailBackend"
# gmail settings
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'kevomash10@gmail.com'
EMAIL_HOST_PASSWORD = 'uvosvpqobgjbrjwl'
EMAIL_PORT = 587
EMAIL_USE_TLS = True





DEFAULT_FROM_EMAIL = 'Johnson Mwaniki <johnsonmwaniki100@email.com>'
ADMINS = (
    ('Johnson Mwaniki', 'johnsonmwaniki100@email.com'),
)