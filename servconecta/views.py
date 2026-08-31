import json
import os

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static as static_url
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import (
    AvaliacaoForm,
    CadastroForm,
    DisputaForm,
    EncerramentoForm,
    OfertaForm,
    PropostaForm,
    SolicitacaoForm,
)
from .models import (
    Avaliacao,
    Categoria,
    Encerramento,
    MensagemChat,
    Notificacao,
    Oferta,
    Proposta,
    Solicitacao,
    Subcategoria,
)
from .reputacao import (
    avaliacoes_visiveis,
    notificar,
    pode_criar_solicitacao,
    tem_selo_elite,
    total_servicos_finalizados,
)

User = get_user_model()


def api_subcategorias(request):
    """Retorna a lista de subcategorias de uma categoria em formato JSON."""
    categoria_id = request.GET.get("categoria_id")
    if not categoria_id:
        return JsonResponse([], safe=False)

    subcategorias = Subcategoria.objects.filter(categoria_id=categoria_id).values("id", "nome", "slug")
    return JsonResponse(list(subcategorias), safe=False)


def home(request):
    """Página inicial: hero, destaques e itens recentes."""
    ofertas = list(
        Oferta.objects.select_related("prestador", "categoria", "subcategoria")[:4]
    )
    for oferta in ofertas:
        oferta.selo_elite = tem_selo_elite(oferta.prestador)
    context = {
        "ofertas": ofertas,
        "solicitacoes": Solicitacao.objects.select_related("cliente", "categoria", "subcategoria")[:4],
        "categorias": Categoria.objects.prefetch_related("subcategorias")[:6],
    }
    return render(request, "servconecta/home.html", context)


def _paginar(request, queryset, por_pagina=9):
    from django.core.paginator import Paginator

    paginator = Paginator(queryset, por_pagina)
    page_obj = paginator.get_page(request.GET.get("page"))
    return page_obj


def ofertas(request):
    """Listagem de ofertas com busca por texto, cidade, categoria e subcategoria."""
    qs = Oferta.objects.select_related("prestador", "categoria", "subcategoria").all()

    q = request.GET.get("q", "").strip()
    cidade = request.GET.get("cidade", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    subcategoria_id = request.GET.get("subcategoria", "").strip()

    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(descricao__icontains=q))
    if cidade:
        qs = qs.filter(cidade__icontains=cidade)
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if subcategoria_id:
        qs = qs.filter(subcategoria_id=subcategoria_id)

    categorias = Categoria.objects.all()
    subcategorias = (
        Subcategoria.objects.filter(categoria_id=categoria_id)
        if categoria_id.isdigit()
        else Subcategoria.objects.none()
    )

    page_obj = _paginar(request, qs)
    for oferta in page_obj.object_list:
        oferta.selo_elite = tem_selo_elite(oferta.prestador)
    context = {
        "ofertas": page_obj.object_list,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "total": qs.count(),
        "q": q,
        "cidade": cidade,
        "categoria_id": int(categoria_id) if categoria_id.isdigit() else "",
        "subcategoria_id": int(subcategoria_id) if subcategoria_id.isdigit() else "",
        "categorias": categorias,
        "subcategorias": subcategorias,
    }
    return render(request, "servconecta/ofertas.html", context)


def solicitacoes(request):
    """Listagem de solicitações com busca por texto, cidade, categoria e subcategoria."""
    qs = Solicitacao.objects.select_related("cliente", "categoria", "subcategoria").all()

    q = request.GET.get("q", "").strip()
    cidade = request.GET.get("cidade", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    subcategoria_id = request.GET.get("subcategoria", "").strip()

    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(descricao__icontains=q))
    if cidade:
        qs = qs.filter(cidade__icontains=cidade)
    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)
    if subcategoria_id:
        qs = qs.filter(subcategoria_id=subcategoria_id)

    categorias = Categoria.objects.all()
    subcategorias = (
        Subcategoria.objects.filter(categoria_id=categoria_id)
        if categoria_id.isdigit()
        else Subcategoria.objects.none()
    )

    page_obj = _paginar(request, qs)
    context = {
        "solicitacoes": page_obj.object_list,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "total": qs.count(),
        "q": q,
        "cidade": cidade,
        "categoria_id": int(categoria_id) if categoria_id.isdigit() else "",
        "subcategoria_id": int(subcategoria_id) if subcategoria_id.isdigit() else "",
        "categorias": categorias,
        "subcategorias": subcategorias,
    }
    return render(request, "servconecta/solicitacoes.html", context)


def oferta_detalhe(request, pk):
    oferta = get_object_or_404(
        Oferta.objects.select_related("prestador", "categoria", "subcategoria"), pk=pk
    )
    return render(request, "servconecta/oferta_detalhe.html", {
        "oferta": oferta,
        "nota_prestador": Avaliacao.nota_media_de(oferta.prestador),
        "selo_prestador": tem_selo_elite(oferta.prestador),
        "servicos_finalizados": total_servicos_finalizados(oferta.prestador),
    })


def _participante(user, solicitacao):
    """Cliente ou o profissional engajado na ordem de serviço."""
    return user.is_authenticated and user in solicitacao.participantes()


def solicitacao_detalhe(request, pk):
    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related("cliente", "categoria", "subcategoria"), pk=pk
    )
    proposta_do_usuario = None
    propostas = None
    encerramento = None
    ja_avaliou = False
    avaliacoes_reveladas = []
    outra_avaliacao_pendente = False

    participante = _participante(request.user, solicitacao)
    if participante:
        encerramento = (
            Encerramento.objects.filter(solicitacao=solicitacao)
            .exclude(status=Encerramento.Status.CANCELADO)
            .select_related("solicitado_por", "respondido_por")
            .first()
        )
        ja_avaliou = solicitacao.avaliacoes.filter(avaliador=request.user).exists()
        if ja_avaliou:
            reveladas = avaliacoes_visiveis(solicitacao)
            if len(reveladas) < 2:
                outra_avaliacao_pendente = True
            else:
                for av in reveladas:
                    avaliacoes_reveladas.append({
                        "titulo": (
                            f"{av.avaliador.get_short_name() or av.avaliador.username}"
                            f" avaliou {av.avaliado.get_short_name() or av.avaliado.username}"
                        ),
                        "media": av.media,
                        "data": av.criada_em,
                        "notas": [
                            (Avaliacao.LABELS[c], getattr(av, f"nota_{c}"))
                            for c in Avaliacao.CRITERIOS[av.papel]
                        ],
                        "tags": [t for t in av.tags.split(", ") if t],
                        "comentario": av.comentario,
                    })

    if request.user.is_authenticated:
        if request.user == solicitacao.cliente:
            # Dono vê todas as propostas recebidas
            propostas = (
                Proposta.objects.filter(solicitacao=solicitacao)
                .select_related("profissional")
                .order_by("-criado_em")
            )
        else:
            # Profissional vê apenas sua proposta
            proposta_do_usuario = Proposta.objects.filter(
                solicitacao=solicitacao, profissional=request.user
            ).first()

    profissional_ativo = solicitacao.profissional_ativo
    context = {
        "solicitacao": solicitacao,
        "proposta_do_usuario": proposta_do_usuario,
        "propostas": propostas,
        "encerramento": encerramento,
        "participante": participante,
        "profissional_ativo": profissional_ativo,
        "ja_avaliou": ja_avaliou,
        "avaliacoes_reveladas": avaliacoes_reveladas,
        "outra_avaliacao_pendente": outra_avaliacao_pendente,
        "nota_profissional": Avaliacao.nota_media_de(profissional_ativo) if profissional_ativo else None,
        "selo_profissional": tem_selo_elite(profissional_ativo) if profissional_ativo else False,
    }
    return render(request, "servconecta/solicitacao_detalhe.html", context)


@login_required
def solicitacao_concluir(request, pk):
    """Etapa 1: cliente ou prestador marca a ordem como concluída."""
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if not _participante(request.user, solicitacao):
        messages.error(request, "Apenas quem participa da ordem pode concluí-la.")
        return redirect("solicitacao_detalhe", pk=pk)

    if solicitacao.status == Solicitacao.Status.CONCLUIDA:
        messages.info(request, "Esta ordem já foi concluída.")
        return redirect("solicitacao_detalhe", pk=pk)

    pendente = Encerramento.objects.filter(
        solicitacao=solicitacao,
        status__in=[Encerramento.Status.PENDENTE, Encerramento.Status.DISPUTADO],
    ).first()
    if pendente:
        messages.info(
            request, "Já existe um pedido de encerramento em andamento para esta ordem."
        )
        return redirect("solicitacao_detalhe", pk=pk)

    if request.method == "POST":
        form = EncerramentoForm(request.POST)
        if form.is_valid():
            encerramento = form.save(commit=False)
            encerramento.solicitacao = solicitacao
            encerramento.solicitado_por = request.user
            encerramento.save()
            if solicitacao.status == Solicitacao.Status.ABERTA:
                solicitacao.status = Solicitacao.Status.EM_ANDAMENTO
                solicitacao.save(update_fields=["status"])

            outro = encerramento.outra_parte
            papel = "cliente" if request.user == solicitacao.cliente else "profissional"
            notificar(
                outro,
                "Confirma o término do serviço?",
                f"O {papel} marcou o serviço “{solicitacao.titulo}” como concluído. "
                "Confirme o término ou abra uma disputa.",
                url=reverse("solicitacao_detalhe", args=[pk]),
            )
            messages.success(
                request,
                f"Conclusão enviada! {outro.get_short_name() or outro.username} "
                "foi notificado para confirmar.",
            )
            return redirect("solicitacao_detalhe", pk=pk)
    else:
        form = EncerramentoForm(initial={"valor_final": solicitacao.orcamento})

    return render(request, "servconecta/encerramento_form.html", {
        "form": form,
        "solicitacao": solicitacao,
    })


@login_required
@require_http_methods(["POST"])
def encerramento_aprovar(request, pk):
    """Etapa 2: a outra parte aprova — status vira Concluída e avaliações liberam."""
    encerramento = get_object_or_404(Encerramento.objects.select_related("solicitacao"), pk=pk)
    solicitacao = encerramento.solicitacao

    if not _participante(request.user, solicitacao) or request.user == encerramento.solicitado_por:
        messages.error(request, "Apenas a outra parte pode confirmar este encerramento.")
        return redirect("solicitacao_detalhe", pk=solicitacao.pk)

    if encerramento.status != Encerramento.Status.PENDENTE:
        messages.info(request, "Este encerramento já foi respondido.")
        return redirect("solicitacao_detalhe", pk=solicitacao.pk)

    encerramento.status = Encerramento.Status.APROVADO
    encerramento.respondido_por = request.user
    encerramento.save(update_fields=["status", "respondido_por", "atualizado_em"])

    solicitacao.status = Solicitacao.Status.CONCLUIDA
    solicitacao.save(update_fields=["status", "atualizado_em"])

    for usuario in solicitacao.participantes():
        notificar(
            usuario,
            "Serviço concluído! Avalie a experiência",
            f"A ordem “{solicitacao.titulo}” foi concluída. Sua avaliação às cegas "
            "está liberada — ela só será revelada quando ambos avaliarem.",
            url=reverse("solicitacao_avaliar", args=[solicitacao.pk]),
        )

    messages.success(request, "Serviço concluído! Agora vocês podem se avaliar.")
    return redirect("solicitacao_detalhe", pk=solicitacao.pk)


@login_required
def encerramento_disputar(request, pk):
    """Etapa 2 alternativa: abre disputa / suporte em vez de aprovar."""
    encerramento = get_object_or_404(Encerramento.objects.select_related("solicitacao"), pk=pk)
    solicitacao = encerramento.solicitacao

    if not _participante(request.user, solicitacao) or request.user == encerramento.solicitado_por:
        messages.error(request, "Apenas a outra parte pode contestar este encerramento.")
        return redirect("solicitacao_detalhe", pk=solicitacao.pk)

    if encerramento.status != Encerramento.Status.PENDENTE:
        messages.info(request, "Este encerramento já foi respondido.")
        return redirect("solicitacao_detalhe", pk=solicitacao.pk)

    if request.method == "POST":
        form = DisputaForm(request.POST)
        if form.is_valid():
            encerramento.status = Encerramento.Status.DISPUTADO
            encerramento.respondido_por = request.user
            encerramento.resposta_observacoes = form.cleaned_data["motivo"]
            encerramento.save()
            for usuario in solicitacao.participantes():
                notificar(
                    usuario,
                    "Disputa aberta na sua ordem de serviço",
                    f"A ordem “{solicitacao.titulo}” está em disputa e será analisada "
                    f"pelo suporte. Motivo: {form.cleaned_data['motivo'][:200]}",
                    url=reverse("solicitacao_detalhe", args=[solicitacao.pk]),
                    enviar_email=False,
                )
            messages.warning(
                request, "Disputa registrada. Nosso suporte entrará em contato."
            )
            return redirect("solicitacao_detalhe", pk=solicitacao.pk)
    else:
        form = DisputaForm()

    return render(request, "servconecta/encerramento_disputa.html", {
        "form": form,
        "solicitacao": solicitacao,
        "encerramento": encerramento,
    })


@login_required
@require_http_methods(["POST"])
def encerramento_cancelar(request, pk):
    """Quem pediu o encerramento pode cancelar antes da resposta."""
    encerramento = get_object_or_404(Encerramento, pk=pk)
    solicitacao = encerramento.solicitacao
    if request.user != encerramento.solicitado_por:
        messages.error(request, "Apenas quem solicitou pode cancelar.")
        return redirect("solicitacao_detalhe", pk=solicitacao.pk)
    if encerramento.status != Encerramento.Status.PENDENTE:
        messages.info(request, "Este encerramento já foi respondido.")
        return redirect("solicitacao_detalhe", pk=solicitacao.pk)
    encerramento.status = Encerramento.Status.CANCELADO
    encerramento.save(update_fields=["status", "atualizado_em"])
    messages.info(request, "Pedido de conclusão cancelado.")
    return redirect("solicitacao_detalhe", pk=solicitacao.pk)


@login_required
def solicitacao_avaliar(request, pk):
    """Etapa 3: avaliação mútua às cegas (liberada após a dupla confirmação)."""
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if solicitacao.status != Solicitacao.Status.CONCLUIDA:
        messages.error(request, "As avaliações abrem após a confirmação do término.")
        return redirect("solicitacao_detalhe", pk=pk)

    if not _participante(request.user, solicitacao):
        messages.error(request, "Apenas participantes da ordem podem avaliar.")
        return redirect("solicitacao_detalhe", pk=pk)

    profissional = solicitacao.profissional_ativo
    if profissional is None:
        messages.error(request, "Nenhum profissional vinculado a esta ordem.")
        return redirect("solicitacao_detalhe", pk=pk)

    if Avaliacao.objects.filter(solicitacao=solicitacao, avaliador=request.user).exists():
        messages.info(request, "Você já avaliou esta ordem.")
        return redirect("solicitacao_detalhe", pk=pk)

    if request.user == solicitacao.cliente:
        papel = Avaliacao.Papel.CLIENTE_AVALIA_PRESTADOR
        avaliado = profissional
    else:
        papel = Avaliacao.Papel.PRESTADOR_AVALIA_CLIENTE
        avaliado = solicitacao.cliente

    if request.method == "POST":
        form = AvaliacaoForm(papel, request.POST)
        if form.is_valid():
            avaliacao = Avaliacao(
                solicitacao=solicitacao,
                avaliador=request.user,
                avaliado=avaliado,
            )
            form.aplicar_em(avaliacao)
            avaliacao.save()
            outro = avaliado
            ambos = solicitacao.avaliacoes.count() >= 2
            if ambos:
                notificar(
                    outro,
                    "Avaliação revelada",
                    f"Avaliações da ordem “{solicitacao.titulo}” foram liberadas — "
                    "vocês dois já responderam.",
                    url=reverse("solicitacao_detalhe", args=[pk]),
                )
                messages.success(request, "Avaliação enviada! As notas dos dois lados já estão visíveis.")
            else:
                messages.success(
                    request,
                    "Avaliação registrada! Ela ficará visível quando a outra parte também avaliar.",
                )
            return redirect("solicitacao_detalhe", pk=pk)
    else:
        form = AvaliacaoForm(papel)

    return render(request, "servconecta/avaliacao_form.html", {
        "form": form,
        "solicitacao": solicitacao,
        "avaliado": avaliado,
        "papel": papel,
        "nomes_criterios": Avaliacao.CRITERIOS[papel],
    })


@login_required
def notificacoes(request):
    """Central de notificações in-app; marca tudo como lido ao abrir."""
    lista = list(Notificacao.objects.filter(destinatario=request.user)[:50])
    nao_lidas = [n for n in lista if not n.lida]
    if nao_lidas:
        Notificacao.objects.filter(
            pk__in=[n.pk for n in nao_lidas]
        ).update(lida=True)
    return render(request, "servconecta/notificacoes.html", {
        "notificacoes": lista,
        "total_nao_lidas": len(nao_lidas),
    })


@login_required
def oferta_criar(request):
    if request.method == "POST":
        form = OfertaForm(request.POST, request.FILES)
        if form.is_valid():
            oferta = form.save(commit=False)
            oferta.prestador = request.user
            oferta.save()
            return redirect(oferta)
    else:
        form = OfertaForm()
    return render(request, "servconecta/oferta_form.html", {"form": form})


@login_required
def oferta_editar(request, pk):
    """Dono da oferta edita seus dados, inclusive Categoria/Subcategoria e imagem."""
    oferta = get_object_or_404(Oferta, pk=pk)

    if request.user != oferta.prestador and not request.user.is_staff:
        messages.error(request, "Você só pode editar as suas próprias ofertas.")
        return redirect("oferta_detalhe", pk=pk)

    if request.method == "POST":
        form = OfertaForm(request.POST, request.FILES, instance=oferta)
        if form.is_valid():
            oferta = form.save(commit=False)
            if request.POST.get("remover_imagem"):
                oferta.imagem = None
            oferta.save()
            messages.success(request, "Oferta atualizada com sucesso!")
            return redirect(oferta)
    else:
        form = OfertaForm(instance=oferta)

    return render(
        request,
        "servconecta/oferta_form.html",
        {"form": form, "oferta": oferta, "editando": True},
    )


@login_required
def solicitacao_criar(request):
    permitido, motivo = pode_criar_solicitacao(request.user)
    if not permitido:
        messages.error(request, motivo)
        return redirect("perfil")

    if request.method == "POST":
        form = SolicitacaoForm(request.POST)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.cliente = request.user
            solicitacao.save()
            return redirect(solicitacao)
    else:
        form = SolicitacaoForm()
    return render(request, "servconecta/solicitacao_form.html", {"form": form})


@login_required
def solicitacao_editar(request, pk):
    """Dono da solicitação edita seus dados, inclusive Categoria/Subcategoria."""
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    if request.user != solicitacao.cliente and not request.user.is_staff:
        messages.error(request, "Você só pode editar as suas próprias solicitações.")
        return redirect("solicitacao_detalhe", pk=pk)

    if request.method == "POST":
        form = SolicitacaoForm(request.POST, instance=solicitacao)
        if form.is_valid():
            form.save()
            messages.success(request, "Solicitação atualizada com sucesso!")
            return redirect(solicitacao)
    else:
        form = SolicitacaoForm(instance=solicitacao)

    return render(
        request,
        "servconecta/solicitacao_form.html",
        {"form": form, "solicitacao": solicitacao, "editando": True},
    )


@login_required
def perfil(request):
    """Perfil do usuário: menu com Minhas ofertas e Minhas solicitações."""
    aba = request.GET.get("aba", "ofertas")
    if aba not in ("ofertas", "solicitacoes"):
        aba = "ofertas"

    minhas_ofertas = (
        Oferta.objects.filter(prestador=request.user)
        .select_related("prestador", "categoria", "subcategoria")
    )
    minhas_solicitacoes = (
        Solicitacao.objects.filter(cliente=request.user)
        .select_related("cliente", "categoria", "subcategoria")
    )

    context = {
        "aba": aba,
        "minhas_ofertas": minhas_ofertas,
        "minhas_solicitacoes": minhas_solicitacoes,
        "total_ofertas": minhas_ofertas.count(),
        "total_solicitacoes": minhas_solicitacoes.count(),
    }
    return render(request, "servconecta/perfil.html", context)


@login_required
def proposta_criar(request, pk):
    """Profissional envia proposta para uma solicitação."""
    solicitacao = get_object_or_404(Solicitacao, pk=pk)

    # Dono da solicitação não pode propor para si mesmo
    if request.user == solicitacao.cliente:
        messages.error(request, "Você não pode enviar proposta para sua própria solicitação.")
        return redirect("solicitacao_detalhe", pk=pk)

    # Evitar proposta duplicada
    if Proposta.objects.filter(solicitacao=solicitacao, profissional=request.user).exists():
        messages.info(request, "Você já enviou uma proposta para esta solicitação.")
        return redirect("solicitacao_detalhe", pk=pk)

    if request.method == "POST":
        form = PropostaForm(request.POST)
        if form.is_valid():
            proposta = form.save(commit=False)
            proposta.solicitacao = solicitacao
            proposta.profissional = request.user
            proposta.save()
            messages.success(request, "Proposta enviada com sucesso!")
            return redirect("solicitacao_detalhe", pk=pk)
    else:
        form = PropostaForm()

    return render(request, "servconecta/proposta_form.html", {
        "form": form,
        "solicitacao": solicitacao,
    })


@login_required
def contratar_oferta(request, pk):
    """Cliente contrata uma oferta criando uma solicitação vinculada."""
    oferta = get_object_or_404(Oferta.objects.select_related("prestador", "categoria", "subcategoria"), pk=pk)

    if request.user == oferta.prestador:
        messages.error(request, "Você não pode contratar sua própria oferta.")
        return redirect("oferta_detalhe", pk=pk)

    permitido, motivo = pode_criar_solicitacao(request.user)
    if not permitido:
        messages.error(request, motivo)
        return redirect("perfil")

    if request.method == "POST":
        form = SolicitacaoForm(request.POST)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.cliente = request.user
            solicitacao.save()
            # Cria proposta automática do prestador da oferta
            Proposta.objects.get_or_create(
                solicitacao=solicitacao,
                profissional=oferta.prestador,
                defaults={"valor": oferta.preco, "descricao": oferta.descricao},
            )
            nome = oferta.prestador.get_short_name() or oferta.prestador.username
            messages.success(request, f"Solicitação criada! {nome} foi notificado.")
            return redirect("solicitacao_detalhe", pk=solicitacao.pk)
    else:
        form = SolicitacaoForm(initial={
            "titulo": f"Contratar: {oferta.titulo}",
            "descricao": oferta.descricao,
            "orcamento": oferta.preco,
            "cidade": oferta.cidade,
            "categoria": oferta.categoria,
            "subcategoria": oferta.subcategoria,
        })

    return render(request, "servconecta/contratar_form.html", {
        "form": form,
        "oferta": oferta,
    })


@login_required
def chat_oferta(request, pk):
    """
    Chat a partir de uma oferta: o cliente conversa com o prestador.
    Cria uma solicitação implícita (rascunho) caso não exista nenhuma entre os dois,
    para que o chat possa ser iniciado sem passar pelo fluxo de contratação.
    """
    from django.utils import timezone

    oferta = get_object_or_404(Oferta.objects.select_related("prestador", "categoria", "subcategoria"), pk=pk)

    if request.user == oferta.prestador:
        messages.info(request, "Esta é a sua oferta.")
        return redirect("oferta_detalhe", pk=pk)

    # Busca uma solicitação existente criada por este usuário vinculada ao prestador da oferta
    solicitacao_existente = Solicitacao.objects.filter(
        cliente=request.user,
        propostas__profissional=oferta.prestador,
    ).first()

    if not solicitacao_existente:
        # Cria uma solicitação de rascunho silenciosamente para suportar o chat
        solicitacao_existente = Solicitacao.objects.create(
            cliente=request.user,
            categoria=oferta.categoria,
            subcategoria=oferta.subcategoria,
            titulo=f"Conversa sobre: {oferta.titulo}",
            descricao=oferta.descricao,
            orcamento=oferta.preco,
            cidade=oferta.cidade,
            status=Solicitacao.Status.ABERTA,
        )
        # Vincula o prestador da oferta como proponente
        Proposta.objects.create(
            solicitacao=solicitacao_existente,
            profissional=oferta.prestador,
            valor=oferta.preco,
            descricao=oferta.descricao,
        )

    return redirect("chat_com", pk=solicitacao_existente.pk, outro_id=oferta.prestador.pk)


@login_required
def chat_view(request, pk, outro_id=None):
    """
    Chat entre o cliente de uma solicitação e um profissional.
    Controle de acesso: apenas os participantes diretos podem acessar.
    """
    solicitacao = get_object_or_404(Solicitacao.objects.select_related("cliente"), pk=pk)
    usuario = request.user
    eh_cliente = usuario == solicitacao.cliente

    if outro_id:
        outro_usuario = get_object_or_404(User, pk=outro_id)
    elif eh_cliente:
        # Cliente sem outro_id → lista de conversas
        participantes_ids = set(
            MensagemChat.objects.filter(solicitacao=solicitacao)
            .values_list("remetente", flat=True)
        ) | set(
            MensagemChat.objects.filter(solicitacao=solicitacao)
            .values_list("destinatario", flat=True)
        )
        participantes_ids.discard(usuario.pk)
        participantes = User.objects.filter(pk__in=participantes_ids)
        # Inclui profissionais que já enviaram propostas
        proposta_ids = Proposta.objects.filter(
            solicitacao=solicitacao
        ).values_list("profissional", flat=True)
        todos_ids = set(participantes_ids) | set(proposta_ids)
        todos_ids.discard(usuario.pk)
        todos = User.objects.filter(pk__in=todos_ids)
        return render(request, "servconecta/chat_lista.html", {
            "solicitacao": solicitacao,
            "participantes": todos,
        })
    else:
        # Profissional sem outro_id → conversa direto com cliente
        outro_usuario = solicitacao.cliente

    # Verifica permissão: deve ser cliente ou ter proposta enviada
    tem_permissao = (
        eh_cliente or
        Proposta.objects.filter(solicitacao=solicitacao, profissional=usuario).exists() or
        usuario == outro_usuario
    )
    if not tem_permissao:
        messages.error(request, "Você não tem acesso a esta conversa.")
        return redirect("solicitacao_detalhe", pk=pk)

    # Carrega histórico entre os dois participantes
    mensagens = MensagemChat.objects.filter(
        solicitacao=solicitacao
    ).filter(
        Q(remetente=usuario, destinatario=outro_usuario) |
        Q(remetente=outro_usuario, destinatario=usuario)
    ).select_related("remetente").order_by("criado_em")

    # POST: envia nova mensagem (CSRF protegido pelo middleware do Django)
    if request.method == "POST":
        texto = request.POST.get("mensagem", "").strip()
        if texto:
            MensagemChat.objects.create(
                solicitacao=solicitacao,
                remetente=usuario,
                destinatario=outro_usuario,
                mensagem=texto,
            )
        return redirect("chat_com", pk=pk, outro_id=outro_usuario.pk)

    return render(request, "servconecta/chat.html", {
        "solicitacao": solicitacao,
        "outro_usuario": outro_usuario,
        "mensagens": mensagens,
        "usuario_id": usuario.pk,
    })


@login_required
def chat_mensagens_novas(request, pk, outro_id):
    """
    Retorna novas mensagens em JSON para polling do frontend.
    Apenas GET. Controle de acesso aplicado.
    """
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    outro_usuario = get_object_or_404(User, pk=outro_id)
    usuario = request.user

    tem_permissao = (
        usuario == solicitacao.cliente or
        Proposta.objects.filter(solicitacao=solicitacao, profissional=usuario).exists() or
        usuario == outro_usuario
    )
    if not tem_permissao:
        return JsonResponse({"error": "Acesso negado."}, status=403)

    after_id = request.GET.get("after_id", 0)
    try:
        after_id = int(after_id)
    except (ValueError, TypeError):
        after_id = 0

    qs = MensagemChat.objects.filter(
        solicitacao=solicitacao,
        pk__gt=after_id,
    ).filter(
        Q(remetente=usuario, destinatario=outro_usuario) |
        Q(remetente=outro_usuario, destinatario=usuario)
    ).select_related("remetente").order_by("criado_em")

    data = [
        {
            "id": m.pk,
            "remetente_id": m.remetente.pk,
            "remetente": m.remetente.get_short_name() or m.remetente.username,
            "mensagem": m.mensagem,
            "criado_em": m.criado_em.strftime("%d/%m/%Y %H:%M"),
        }
        for m in qs
    ]
    return JsonResponse({"mensagens": data})


@require_http_methods(["GET", "POST"])
def cadastro(request):
    if request.method == "POST":
        form = CadastroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = CadastroForm()
    return render(request, "servconecta/cadastro.html", {"form": form})


# ---------------------------------------------------------------------------
# PWA — manifest.json e service worker
# ---------------------------------------------------------------------------


def manifest_pwa(request):
    def icon(path):
        return request.build_absolute_uri(static_url(path))

    data = {
        "name": "ServConecta — Conectando Profissionais e Clientes",
        "short_name": "ServConecta",
        "description": "Encontre o serviço ideal ou ofereça seus talentos. Simples, seguro e transparente.",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#eef2f9",
        "theme_color": "#1a56db",
        "lang": "pt-BR",
        "icons": [
            {
                "src": icon("pwa/icons/icon-192x192.png"),
                "sizes": "192x192",
                "type": "image/png",
            },
            {
                "src": icon("pwa/icons/icon-512x512.png"),
                "sizes": "512x512",
                "type": "image/png",
            },
            {
                "src": icon("pwa/icons/icon-maskable-192x192.png"),
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "maskable",
            },
            {
                "src": icon("pwa/icons/icon-maskable-512x512.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ],
    }
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})


@never_cache
def service_worker(request):
    sw_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "pwa", "sw.js")
    with open(sw_path) as f:
        return HttpResponse(f.read(), content_type="application/javascript")
