from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import (
    Avaliacao,
    Encerramento,
    Oferta,
    Solicitacao,
    Proposta,
    Subcategoria,
)

User = get_user_model()

TAMANHO_MAXIMO_IMAGEM_MB = 5


def validar_tamanho_imagem(imagem):
    """Impede uploads de imagem acima do limite definido."""
    limite = TAMANHO_MAXIMO_IMAGEM_MB * 1024 * 1024
    if imagem.size > limite:
        raise ValidationError(
            f"A imagem deve ter no máximo {TAMANHO_MAXIMO_IMAGEM_MB} MB."
        )


class EncerramentoForm(forms.ModelForm):
    """Etapa 1 do fechamento: pedido de conclusão com dupla confirmação."""

    class Meta:
        model = Encerramento
        fields = ["valor_final", "observacoes"]
        labels = {
            "valor_final": "Valor final ajustado (R$)",
            "observacoes": "Observações do serviço",
        }
        widgets = {
            "observacoes": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Relate como o serviço foi executado, combinações finais, etc.",
            }),
        }
        help_texts = {
            "valor_final": "Deixe em branco se o valor acordado não mudou.",
        }


class DisputaForm(forms.Form):
    """Etapa 2 alternativa: abrir disputa / suporte."""

    motivo = forms.CharField(
        label="Motivo da disputa",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Explique o problema com o serviço para a nossa equipe analisar.",
        }),
    )


class AvaliacaoForm(forms.Form):
    """
    Etapa 3: avaliação às cegas.

    Os critérios (4 notas de 1 a 5) e as tags rápidas dependem do papel:
    cliente avalia prestador ("CP") ou prestador avalia cliente ("PC").
    """

    def __init__(self, papel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.papel = papel

        for campo in Avaliacao.CRITERIOS[papel]:
            self.fields[campo] = forms.TypedChoiceField(
                label=Avaliacao.LABELS[campo],
                choices=[(i, str(i)) for i in range(1, 6)],
                coerce=int,
                widget=forms.RadioSelect,
            )

        self.fields["tags"] = forms.MultipleChoiceField(
            label="Feedback rápido",
            required=False,
            choices=[(tag, tag) for tag in Avaliacao.TAGS_POR_PAPEL[papel]],
            widget=forms.CheckboxSelectMultiple,
        )
        self.fields["comentario"] = forms.CharField(
            label="Comentário (opcional)",
            required=False,
            max_length=500,
            widget=forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "Escreva uma experiência para ajudar a comunidade...",
            }),
        )

    def clean_tags(self):
        return ", ".join(sorted(self.cleaned_data.get("tags", [])))

    def aplicar_em(self, avaliacao):
        """Preenche a instância de Avaliacao com os critérios do papel."""
        avaliacao.papel = self.papel
        for campo in Avaliacao.CRITERIOS[self.papel]:
            setattr(avaliacao, f"nota_{campo}", self.cleaned_data[campo])
        avaliacao.tags = self.cleaned_data["tags"]
        avaliacao.comentario = self.cleaned_data["comentario"]
        return avaliacao


class CadastroForm(UserCreationForm):
    """Formulário de registro de novo usuário."""

    email = forms.EmailField(required=True, label="E-mail")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class OfertaForm(forms.ModelForm):
    imagem = forms.ImageField(
        label="Imagem",
        required=False,
        validators=[validar_tamanho_imagem],
        help_text=(
            f"JPG ou PNG, até {TAMANHO_MAXIMO_IMAGEM_MB} MB. "
            "A imagem é redimensionada automaticamente para o padrão dos cards."
        ),
        widget=forms.ClearableFileInput(attrs={"accept": "image/*"}),
    )

    class Meta:
        model = Oferta
        fields = [
            "titulo",
            "categoria",
            "subcategoria",
            "descricao",
            "preco",
            "unidade",
            "cidade",
            "imagem",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subcategoria"].queryset = Subcategoria.objects.none()

        if "categoria" in self.data:
            try:
                categoria_id = int(self.data.get("categoria"))
                self.fields["subcategoria"].queryset = Subcategoria.objects.filter(categoria_id=categoria_id).order_by("nome")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.categoria:
            self.fields["subcategoria"].queryset = self.instance.categoria.subcategorias.order_by("nome")


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = [
            "titulo",
            "categoria",
            "subcategoria",
            "descricao",
            "orcamento",
            "cidade",
            "prazo",
        ]
        widgets = {
            "prazo": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subcategoria"].queryset = Subcategoria.objects.none()

        if "categoria" in self.data:
            try:
                categoria_id = int(self.data.get("categoria"))
                self.fields["subcategoria"].queryset = Subcategoria.objects.filter(categoria_id=categoria_id).order_by("nome")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.categoria:
            self.fields["subcategoria"].queryset = self.instance.categoria.subcategorias.order_by("nome")


class PropostaForm(forms.ModelForm):
    class Meta:
        model = Proposta
        fields = ["valor", "descricao"]
        widgets = {
            "descricao": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "Descreva sua qualificação, prazo e detalhes do serviço..."
            }),
        }
