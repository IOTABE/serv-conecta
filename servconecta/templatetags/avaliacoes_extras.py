from django import template

register = template.Library()


@register.filter
def estrela_cheia(indice, nota):
    """True se a estrela `indice` (1..5) deve aparecer preenchida para a nota."""
    try:
        return int(indice) <= float(nota)
    except (TypeError, ValueError):
        return False


@register.filter
def separar(valor, sep=","):
    """Divide a string de tags em lista."""
    if not valor:
        return []
    return [parte.strip() for parte in str(valor).split(sep) if parte.strip()]


@register.filter
def campo_do_formulario(formulario, nome):
    """Acessa um BoundField pelo nome dinamicamente (form|campo_do_formulario:'nota')."""
    try:
        return formulario[nome]
    except (KeyError, TypeError):
        return None


@register.simple_tag
def srcset_oferta(oferta):
    """Monta o atributo srcset para imagem responsiva da oferta."""
    partes = []
    if getattr(oferta, "imagem_celular", None):
        partes.append(f"{oferta.imagem_celular.url} 480w")
    if getattr(oferta, "imagem_tablet", None):
        partes.append(f"{oferta.imagem_tablet.url} 768w")
    if getattr(oferta, "imagem", None):
        partes.append(f"{oferta.imagem.url} 1280w")
    return ", ".join(partes) if partes else ""


@register.filter
def dicionario(dicionario_, chave):
    """Acessa uma chave de dict no template."""
    try:
        return dicionario_.get(chave)
    except AttributeError:
        return None


@register.filter
def atributo(objeto, nome):
    """Lê um atributo do objeto pelo nome (ex.: nota_qualidade_servico)."""
    return getattr(objeto, nome, None)
