"""
URLs raiz do projeto ServConecta.

Inclui o admin do Django e as rotas do app `servconecta`.
Em modo DEBUG, serve tambem os arquivos de midia (uploads de imagens das ofertas).
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("servconecta.urls")),
]

# Servir arquivos de midia durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
