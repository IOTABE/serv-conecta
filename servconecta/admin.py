from django.contrib import admin
from django.utils.html import format_html

from .models import Categoria, Subcategoria, Oferta, Solicitacao, Proposta, MensagemChat


class SubcategoriaInline(admin.TabularInline):
    model = Subcategoria
    extra = 1
    prepopulated_fields = {"slug": ("nome",)}


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug")
    search_fields = ("nome",)
    prepopulated_fields = {"slug": ("nome",)}
    ordering = ("nome",)
    inlines = [SubcategoriaInline]


@admin.register(Subcategoria)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome", "categoria", "slug")
    list_filter = ("categoria",)
    search_fields = ("nome", "categoria__nome")
    prepopulated_fields = {"slug": ("nome",)}
    ordering = ("categoria__nome", "nome")


@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "prestador",
        "categoria",
        "subcategoria",
        "preco_formatado",
        "cidade",
        "prestador_verificado",
        "criado_em",
    )
    list_filter = ("prestador_verificado", "categoria", "subcategoria", "cidade", "criado_em")
    list_editable = ("prestador_verificado",)
    search_fields = ("titulo", "descricao", "cidade", "prestador__username")
    autocomplete_fields = ("prestador", "categoria", "subcategoria")
    date_hierarchy = "criado_em"
    readonly_fields = ("criado_em", "atualizado_em", "imagem_preview")
    ordering = ("-criado_em",)
    fieldsets = (
        ("Informações principais", {
            "fields": ("prestador", "categoria", "subcategoria", "titulo", "descricao"),
        }),
        ("Preço e localização", {
            "fields": ("preco", "unidade", "cidade"),
        }),
        ("Mídia e verificação", {
            "fields": ("imagem", "imagem_preview", "prestador_verificado"),
        }),
        ("Metadados", {
            "classes": ("collapse",),
            "fields": ("criado_em", "atualizado_em"),
        }),
    )

    @admin.display(description="Preço", ordering="preco")
    def preco_formatado(self, obj):
        return f"R$ {obj.preco:.2f} /{obj.unidade}"

    @admin.display(description="Pré-visualização")
    def imagem_preview(self, obj):
        if obj.imagem:
            return format_html(
                '<img src="{}" style="max-height:160px;border-radius:8px;" />',
                obj.imagem.url,
            )
        return "Sem imagem"


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = (
        "titulo",
        "cliente",
        "categoria",
        "subcategoria",
        "orcamento_formatado",
        "cidade",
        "prazo",
        "status",
        "criado_em",
    )
    list_filter = ("status", "categoria", "subcategoria", "cidade", "criado_em")
    list_editable = ("status",)
    search_fields = ("titulo", "descricao", "cidade", "cliente__username")
    autocomplete_fields = ("cliente", "categoria", "subcategoria")
    date_hierarchy = "criado_em"
    readonly_fields = ("criado_em", "atualizado_em")
    ordering = ("-criado_em",)
    actions = ("marcar_como_concluida", "marcar_como_cancelada")
    fieldsets = (
        ("Informações principais", {
            "fields": ("cliente", "categoria", "subcategoria", "titulo", "descricao", "status"),
        }),
        ("Orçamento e prazo", {
            "fields": ("orcamento", "cidade", "prazo"),
        }),
        ("Metadados", {
            "classes": ("collapse",),
            "fields": ("criado_em", "atualizado_em"),
        }),
    )

    @admin.display(description="Orçamento", ordering="orcamento")
    def orcamento_formatado(self, obj):
        if obj.orcamento is None:
            return "A combinar"
        return f"R$ {obj.orcamento:.2f}"

    @admin.action(description="Marcar selecionadas como concluídas")
    def marcar_como_concluida(self, request, queryset):
        atualizadas = queryset.update(status=Solicitacao.Status.CONCLUIDA)
        self.message_user(request, f"{atualizadas} solicitação(ões) concluída(s).")

    @admin.action(description="Marcar selecionadas como canceladas")
    def marcar_como_cancelada(self, request, queryset):
        atualizadas = queryset.update(status=Solicitacao.Status.CANCELADA)
        self.message_user(request, f"{atualizadas} solicitação(ões) cancelada(s).")


@admin.register(Proposta)
class PropostaAdmin(admin.ModelAdmin):
    list_display = ("solicitacao", "profissional", "valor", "criado_em")
    list_filter = ("criado_em",)
    search_fields = ("solicitacao__titulo", "profissional__username", "descricao")
    autocomplete_fields = ("solicitacao", "profissional")
    ordering = ("-criado_em",)


@admin.register(MensagemChat)
class MensagemChatAdmin(admin.ModelAdmin):
    list_display = ("solicitacao", "remetente", "destinatario", "criado_em")
    list_filter = ("criado_em",)
    search_fields = ("mensagem", "remetente__username", "destinatario__username", "solicitacao__titulo")
    autocomplete_fields = ("solicitacao", "remetente", "destinatario")
    ordering = ("criado_em",)
