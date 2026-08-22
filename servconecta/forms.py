from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Oferta, Solicitacao, Proposta, Subcategoria

User = get_user_model()

TAMANHO_MAXIMO_IMAGEM_MB = 5


def validar_tamanho_imagem(imagem):
    """Impede uploads de imagem acima do limite definido."""
    limite = TAMANHO_MAXIMO_IMAGEM_MB * 1024 * 1024
    if imagem.size > limite:
        raise ValidationError(
            f"A imagem deve ter no máximo {TAMANHO_MAXIMO_IMAGEM_MB} MB."
        )


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
