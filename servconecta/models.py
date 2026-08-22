from django.conf import settings
from django.db import models
from django.urls import reverse


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
