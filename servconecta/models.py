import io

from PIL import Image, ImageOps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

LADO_MAXIMO_IMAGEM = 1280


def padronizar_imagem(imagem, lado_maximo=LADO_MAXIMO_IMAGEM):
    """Redimensiona, corrige rotação e reencodea a imagem como JPEG padrão."""
    imagem.seek(0)
    img = ImageOps.exif_transpose(Image.open(imagem))
    if img.mode != "RGB":
        img = img.convert("RGB")
    if max(img.size) > lado_maximo:
        img.thumbnail((lado_maximo, lado_maximo), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    nome_arquivo = (imagem.name or "oferta").rsplit("/", 1)[-1]
    nome_base = slugify(nome_arquivo.rsplit(".", 1)[0]) or "oferta"
    imagem.save(f"{nome_base}.jpg", ContentFile(buffer.getvalue()), save=False)


class Categoria(models.Model):
    nome = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Subcategoria(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name="subcategorias",
    )
    nome = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90)

    class Meta:
        verbose_name = "Subcategoria"
        verbose_name_plural = "Subcategorias"
        ordering = ["categoria__nome", "nome"]
        unique_together = ("categoria", "slug")

    def __str__(self):
        return f"{self.categoria.nome} › {self.nome}"


class Oferta(models.Model):
    """Serviço oferecido por um profissional."""

    prestador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ofertas",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ofertas",
    )
    subcategoria = models.ForeignKey(
        Subcategoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ofertas",
    )
    titulo = models.CharField("Título", max_length=140)
    descricao = models.TextField("Descrição")
    preco = models.DecimalField("Preço", max_digits=10, decimal_places=2)
    # unidade exibida ao lado do preço (ex.: SERVIÇO, HORA, DIÁRIA)
    unidade = models.CharField(max_length=20, default="SERVIÇO")
    cidade = models.CharField(max_length=120)
    imagem = models.ImageField(upload_to="ofertas/", blank=True, null=True)
    prestador_verificado = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Oferta"
        verbose_name_plural = "Ofertas"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if self.imagem and not self.imagem._committed:
            padronizar_imagem(self.imagem)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("oferta_detalhe", args=[self.pk])


class Solicitacao(models.Model):
    class Status(models.TextChoices):
        ABERTA = "aberta", "Aberta"
        EM_ANDAMENTO = "em_andamento", "Em andamento"
        CONCLUIDA = "concluida", "Concluída"
        CANCELADA = "cancelada", "Cancelada"

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solicitacoes",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitacoes",
    )
    subcategoria = models.ForeignKey(
        Subcategoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitacoes",
    )
    titulo = models.CharField("Título", max_length=140)
    descricao = models.TextField("Descrição")
    orcamento = models.DecimalField(
        "Orçamento", max_digits=10, decimal_places=2, null=True, blank=True
    )
    cidade = models.CharField(max_length=120)
    prazo = models.DateField("Prazo", null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ABERTA
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Solicitação"
        verbose_name_plural = "Solicitações"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo

    def get_absolute_url(self):
        return reverse("solicitacao_detalhe", args=[self.pk])

    @property
    def profissional_ativo(self):
        """Profissional contratado/engajado na solicitação (última proposta)."""
        proposta = self.propostas.order_by("-criado_em").first()
        return proposta.profissional if proposta else None

    def participantes(self):
        """Usuários diretamente envolvidos: cliente + profissional ativo."""
        profissional = self.profissional_ativo
        return [u for u in (self.cliente, profissional) if u]


class Encerramento(models.Model):
    """
    Etapa do fluxo de fechamento com dupla confirmação.

    Uma parte pede o encerramento informando o valor final ajustado e
    observações; a outra parte aprova (conclui) ou abre disputa.
    """

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Aguardando confirmação"
        APROVADO = "aprovado", "Aprovado"
        DISPUTADO = "disputado", "Em disputa"
        CANCELADO = "cancelado", "Cancelado"

    solicitacao = models.ForeignKey(
        Solicitacao, on_delete=models.CASCADE, related_name="encerramentos"
    )
    solicitado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="encerramentos_solicitados",
    )
    valor_final = models.DecimalField(
        "Valor final ajustado", max_digits=10, decimal_places=2, null=True, blank=True
    )
    observacoes = models.TextField("Observações do serviço", blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDENTE
    )
    respondido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="encerramentos_respondidos",
    )
    resposta_observacoes = models.TextField("Observações da resposta", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Encerramento"
        verbose_name_plural = "Encerramentos"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"Encerramento #{self.pk} — {self.solicitacao.titulo} ({self.status})"

    @property
    def outra_parte(self):
        """Usuário que deve confirmar ou contestar o encerramento."""
        return next(
            (
                u
                for u in self.solicitacao.participantes()
                if u != self.solicitado_por
            ),
            None,
        )

    def clean(self):
        if self.solicitado_por_id and self.outra_parte is None:
            raise ValidationError("O solicitante não é participante desta ordem.")


class Avaliacao(models.Model):
    """
    Avaliação mútua às cegas entre cliente e prestador.

    papel = "CP": cliente avalia prestador (critérios de serviço).
    papel = "PC": prestador avalia cliente (critérios de contratação).
    Só fica visível para a outra parte quando ambos avaliarem.
    """

    class Papel(models.TextChoices):
        CLIENTE_AVALIA_PRESTADOR = "CP", "Cliente avalia prestador"
        PRESTADOR_AVALIA_CLIENTE = "PC", "Prestador avalia cliente"

    CRITERIOS = {
        "CP": ["qualidade_servico", "pontualidade", "limpeza_organizacao", "comunicacao"],
        "PC": ["clareza_pedido", "cumprimento_pagamento", "respeito_educacao", "facilidade_acesso"],
    }

    LABELS = {
        "qualidade_servico": "Qualidade do Serviço",
        "pontualidade": "Pontualidade",
        "limpeza_organizacao": "Limpeza e Organização",
        "comunicacao": "Comunicação",
        "clareza_pedido": "Clareza no Pedido",
        "cumprimento_pagamento": "Cumprimento do Pagamento",
        "respeito_educacao": "Respeito / Educação",
        "facilidade_acesso": "Facilidade de Acesso",
    }

    TAGS_POR_PAPEL = {
        "CP": [
            "Pontual",
            "Caprichoso",
            "Preço Justo",
            "Educado",
            "Não Cumpriu Horário",
        ],
        "PC": [
            "Bom Pagador",
            "Respeitoso",
            "Local Acessível",
            "Comunicação Difícil",
        ],
    }

    solicitacao = models.ForeignKey(
        Solicitacao, on_delete=models.CASCADE, related_name="avaliacoes"
    )
    avaliador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="avaliacoes_enviadas",
    )
    avaliado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="avaliacoes_recebidas",
    )
    papel = models.CharField(max_length=2, choices=Papel.choices)

    nota_qualidade_servico = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    nota_pontualidade = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    nota_limpeza_organizacao = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    nota_comunicacao = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    nota_clareza_pedido = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    nota_cumprimento_pagamento = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    nota_respeito_educacao = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    nota_facilidade_acesso = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    tags = models.CharField(max_length=250, blank=True)
    comentario = models.TextField(blank=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        ordering = ["-criada_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["solicitacao", "avaliador"],
                name="avaliacao_unica_por_ordem_e_avaliador",
            )
        ]

    def __str__(self):
        return f"{self.get_papel_display()} — ordem #{self.solicitacao_id}"

    def save(self, *args, **kwargs):
        self.full_clean(exclude=None)
        super().save(*args, **kwargs)

    def clean(self):
        campos = self.CRITERIOS[self.papel] if self.papel else []
        faltando = [c for c in campos if getattr(self, f"nota_{c}") is None]
        if faltando:
            raise ValidationError("Responda todas as notas de 1 a 5 estrelas.")

    @property
    def media(self):
        notas = [
            getattr(self, f"nota_{campo}")
            for campo in self.CRITERIOS.get(self.papel, [])
        ]
        notas = [n for n in notas if n is not None]
        return round(sum(notas) / len(notas), 2) if notas else None

    @classmethod
    def nota_media_de(cls, user, ultimas=50):
        """Média simples das médias das últimas `ultimas` avaliações recebidas."""
        medias = [
            a.media for a in cls.objects.filter(avaliado=user)[:ultimas] if a.media
        ]
        return round(sum(medias) / len(medias), 1) if medias else None


class Notificacao(models.Model):
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes",
    )
    titulo = models.CharField(max_length=140)
    texto = models.TextField(blank=True)
    url = models.CharField(max_length=255, blank=True)
    lida = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"
        ordering = ["-criada_em"]

    def __str__(self):
        return self.titulo


class Proposta(models.Model):
    solicitacao = models.ForeignKey(
        'Solicitacao',
        on_delete=models.CASCADE,
        related_name="propostas"
    )
    profissional = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="propostas_enviadas"
    )
    valor = models.DecimalField("Valor da Proposta", max_digits=10, decimal_places=2)
    descricao = models.TextField("Descrição da Proposta")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Proposta"
        verbose_name_plural = "Propostas"
        ordering = ["-criado_em"]
        unique_together = ("solicitacao", "profissional")

    def __str__(self):
        return f"Proposta de R$ {self.valor} para {self.solicitacao.titulo}"


class MensagemChat(models.Model):
    solicitacao = models.ForeignKey(
        'Solicitacao',
        on_delete=models.CASCADE,
        related_name="mensagens"
    )
    remetente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensagens_enviadas"
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensagens_recebidas"
    )
    mensagem = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensagem de Chat"
        verbose_name_plural = "Mensagens de Chat"
        ordering = ["criado_em"]

    def __str__(self):
        return f"De {self.remetente.username} para {self.destinatario.username} em {self.solicitacao.titulo}"
