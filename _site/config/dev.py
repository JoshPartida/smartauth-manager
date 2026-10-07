from .base import *
from .base import INSTALLED_APPS
from .base import MIDDLEWARE

# GENERAL ---------------------------------------------------------------------
DEBUG = True
SECRET_KEY = "django-insecure-#8)mtxiio&@5@p183x@t)wuxtvm)5!z%)nzimo_0aqc2t@mi=x"
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
DEV_SERVER_IP = "172.27.176.8"

# CACHES ----------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "",
    },
}

# EMAIL -----------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  
        'NAME': APPLICATION_CODE,
        'USER': 'fsoftware',
        'PASSWORD': 'An@lisis20120203',
        'HOST': DEV_SERVER_IP,
        'PORT': '3306',
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "smartlog": {
            "format": "-------------------------------\n{asctime} - {levelname} {pathname}: {funcName} - {message}\n({exc_info})",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "kdsuportal.log",
            "level": "WARNING",
            "formatter": "smartlog",
        },
    },
    "loggers": {
        "kdsu": {
            "handlers": ["file"],
        },
    },
}

# django-debug-toolbar --------------------------------------------------------
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}

# # OIDC DEV SETTINGS ------------------------------------------------------------------------
# OIDC_RP_CLIENT_ID = 'kdsuportal'
# OIDC_RP_CLIENT_SECRET = '9290a6549cb1e036873749119c29fb947251baedb0b513d77ad32206'
# OIDC_OP_AUTHORIZATION_ENDPOINT = f'http://{DEV_SERVER_IP}:9008/smartauth/openid/authorize'
# OIDC_OP_TOKEN_ENDPOINT = f'http://{DEV_SERVER_IP}:9008/smartauth/openid/token'
# OIDC_OP_USER_ENDPOINT = f'http://{DEV_SERVER_IP}:9008/smartauth/openid/userinfo'
# OIDC_OP_LOGOUT_ENDPOINT = f'http://{DEV_SERVER_IP}:9008/smartauth/openid/end-session'
# OIDC_RP_IDP_SIGN_KEY = "-----BEGIN PUBLIC KEY-----" \
# "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkRlr3VNaopprAPw+PAip" \
# "rqGUAu85fx48pEGpKXaelqkZwytP3qqtoCnBnFaVi7CM4lfpQvLeYMuWnf280xcv" \
# "kRW79IDr0mBxfMZjWtvnz2bJx4UUOyWTQr2WLUTEIWarlX5ogwKNFKanujf2Fnn3" \
# "nynusRgKbzFaF2xMpq7BYAoz5QVOiHvs3NT0edHWiclE+CqtaoGEyrW1kvicWKCb" \
# "Xy24UPcYGD1/9sWg3wVFZ4f9jVTnS4bGsdXvqC/SG0WIOjQWHvYyhxI2Wf6HTZs9" \
# "hBkhXArYKBgz8TNxRxN5qK3M7Wmm5Zd6nVMWdvYLzI84axPRPdlCBNAhTiCEh+yk" \
# "HwIDAQAB" \
# "-----END PUBLIC KEY-----"
