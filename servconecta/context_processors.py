from .models import Notificacao


def notificacoes_nao_lidas(request):
    """Contador para o sino da navbar."""
    total = 0
    if getattr(request.user, "is_authenticated", False):
        total = Notificacao.objects.filter(destinatario=request.user, lida=False).count()
    return {"notificacoes_nao_lidas": total}
