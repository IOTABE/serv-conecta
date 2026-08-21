"""
Configuracao ASGI para o projeto ServConecta.

Expoe o callable ASGI como uma variavel de modulo chamada ``application``.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
