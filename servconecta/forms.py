from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Oferta, Solicitacao, Proposta

User = get_user_model()


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
    class Meta:
        model = Oferta
        fields = [
            "titulo",
            "categoria",
            "descricao",
            "preco",
            "unidade",
            "cidade",
            "imagem",
        ]


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = [
            "titulo",
            "categoria",
            "descricao",
            "orcamento",
            "cidade",
            "prazo",
        ]
        widgets = {
            "prazo": forms.DateInput(attrs={"type": "date"}),
        }


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
