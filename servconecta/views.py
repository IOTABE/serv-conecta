import json

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import CadastroForm, OfertaForm, PropostaForm, SolicitacaoForm
from .models import Categoria, Subcategoria, MensagemChat, Oferta, Proposta, Solicitacao

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
    context = {
        "ofertas": Oferta.objects.select_related("prestador", "categoria", "subcategoria")[:4],
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
    return render(request, "servconecta/oferta_detalhe.html", {"oferta": oferta})


def solicitacao_detalhe(request, pk):
    solicitacao = get_object_or_404(
        Solicitacao.objects.select_related("cliente", "categoria", "subcategoria"), pk=pk
    )
    proposta_do_usuario = None
    propostas = None

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

    return render(
        request,
        "servconecta/solicitacao_detalhe.html",
        {
            "solicitacao": solicitacao,
            "proposta_do_usuario": proposta_do_usuario,
            "propostas": propostas,
        },
    )


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
def solicitacao_criar(request):
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
