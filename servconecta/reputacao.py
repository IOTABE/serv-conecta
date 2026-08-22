"""
Reputação e gamificação do ServConecta.

- Nota média: média simples das últimas 50 avaliações recebidas.
- Selo Elite (Prestador Destaque): nota >= 4.8 e mais de 10 serviços finalizados.
- Cliente restrito: nota < 3.0 (com no mínimo 3 avaliações) recebe alertas
  internos e fica limitado a 1 solicitação aberta por vez.

As avaliações são às cegas: uma avaliação só é revelada à outra parte quando
ambos os lados tiverem avaliado a mesma ordem de serviço.
"""

from django.core.mail import send_mail
from django.conf import settings

from .models import Avaliacao, Notificacao, Proposta, Solicitacao

NOTA_MINIMA_SELO = 4.8
SERVICOS_MINIMOS_SELO = 10
NOTA_MINIMA_CLIENTE = 3.0
AVALIACOES_MINIMAS_RESTRICAO = 3
MAX_SOLICITACOES_ABERTAS_RESTRITO = 1


def total_servicos_finalizados(prestador):
    """Órdens concluídas em que o prestador estava engajado."""
    return (
        Solicitacao.objects.filter(status=Solicitacao.Status.CONCLUIDA)
        .filter(propostas__profissional=prestador)
        .distinct()
        .count()
    )


def tem_selo_elite(prestador):
    """Selo 'Prestador Verificado / Destaque' para os melhores profissionais."""
    if not getattr(prestador, "pk", None):
        return False
    nota = Avaliacao.nota_media_de(prestador)
    if nota is None or nota < NOTA_MINIMA_SELO:
        return False
    return total_servicos_finalizados(prestador) > SERVICOS_MINIMOS_SELO


def cliente_restrito(cliente):
    """Clientes mal avaliados ganham restrições de uso."""
    if not getattr(cliente, "pk", None):
        return False
    recebidas = Avaliacao.objects.filter(
        avaliado=cliente, papel=Avaliacao.Papel.PRESTADOR_AVALIA_CLIENTE
    ).count()
    if recebidas < AVALIACOES_MINIMAS_RESTRICAO:
        return False
    nota = Avaliacao.nota_media_de(cliente)
    return nota is not None and nota < NOTA_MINIMA_CLIENTE


def solicitacoes_abertas_do(cliente):
    return Solicitacao.objects.filter(
        cliente=cliente,
        status__in=[Solicitacao.Status.ABERTA, Solicitacao.Status.EM_ANDAMENTO],
    ).count()


def pode_criar_solicitacao(cliente):
    """(permitido, motivo) — aplica a restrição de orçamentos simultâneos."""
    if not cliente_restrito(cliente):
        return True, ""
    abertas = solicitacoes_abertas_do(cliente)
    if abertas >= MAX_SOLICITACOES_ABERTAS_RESTRITO:
        return False, (
            "Sua reputação como cliente está abaixo do mínimo aceito "
            f"(nota {Avaliacao.nota_media_de(cliente)}). Enquanto isso, você pode "
            f"ter apenas {MAX_SOLICITACOES_ABERTAS_RESTRITO} solicitação ativa por vez. "
            "Conclua ou cancele suas solicitações pendentes."
        )
    return True, ""


def notificar(destinatario, titulo, texto, url="", enviar_email=True):
    """Cria a notificação in-app e tenta enviar por e-mail quando configurado."""
    Notificacao.objects.create(
        destinatario=destinatario,
        titulo=titulo,
        texto=texto,
        url=url,
    )
    email = getattr(destinatario, "email", "")
    if enviar_email and email and not settings.DEBUG:
        try:
            send_mail(titulo, texto, settings.DEFAULT_FROM_EMAIL, [email])
        except Exception:
            pass


def avaliacoes_visiveis(solicitacao):
    """Retorna as avaliações já reveladas (blind review: exige os dois lados)."""
    todas = list(solicitacao.avaliacoes.select_related("avaliador", "avaliado"))
    if len(todas) < 2:
        return []
    return todas
