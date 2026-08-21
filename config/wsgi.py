"""
Configuracao WSGI para o projeto ServConecta.

Expoe o callable WSGI como uma variavel de modulo chamada ``application``.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
