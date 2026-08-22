from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    # Ofertas
    path("ofertas/", views.ofertas, name="ofertas"),
    path("ofertas/nova/", views.oferta_criar, name="oferta_criar"),
    path("ofertas/<int:pk>/editar/", views.oferta_editar, name="oferta_editar"),
    path("ofertas/<int:pk>/", views.oferta_detalhe, name="oferta_detalhe"),
    path("ofertas/<int:pk>/contratar/", views.contratar_oferta, name="contratar"),
    path("ofertas/<int:pk>/chat/", views.chat_oferta, name="chat_oferta"),
    # Solicitações
    path("solicitacoes/", views.solicitacoes, name="solicitacoes"),
    path("solicitacoes/nova/", views.solicitacao_criar, name="solicitacao_criar"),
    path("solicitacoes/<int:pk>/editar/", views.solicitacao_editar, name="solicitacao_editar"),
    path("solicitacoes/<int:pk>/", views.solicitacao_detalhe, name="solicitacao_detalhe"),
    path("solicitacoes/<int:pk>/concluir/", views.solicitacao_concluir, name="solicitacao_concluir"),
    path("solicitacoes/<int:pk>/avaliar/", views.solicitacao_avaliar, name="solicitacao_avaliar"),
    path("encerramentos/<int:pk>/aprovar/", views.encerramento_aprovar, name="encerramento_aprovar"),
    path("encerramentos/<int:pk>/disputa/", views.encerramento_disputar, name="encerramento_disputar"),
    path("encerramentos/<int:pk>/cancelar/", views.encerramento_cancelar, name="encerramento_cancelar"),
    path("solicitacoes/<int:pk>/proposta/", views.proposta_criar, name="proposta_criar"),
    path("solicitacoes/<int:pk>/chat/", views.chat_view, name="chat"),
    path("solicitacoes/<int:pk>/chat/<int:outro_id>/", views.chat_view, name="chat_com"),
    path(
        "solicitacoes/<int:pk>/chat/<int:outro_id>/novas/",
        views.chat_mensagens_novas,
        name="chat_mensagens_novas",
    ),
    # Autenticação
    path(
        "entrar/",
        auth_views.LoginView.as_view(template_name="servconecta/login.html"),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("cadastro/", views.cadastro, name="cadastro"),
    # Perfil
    path("perfil/", views.perfil, name="perfil"),
    # Notificações
    path("notificacoes/", views.notificacoes, name="notificacoes"),
    # API
    path("api/subcategorias/", views.api_subcategorias, name="api_subcategorias"),
]

