# Admin Edit/Delete — Ofertas e Solicitacoes

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add admin-only edit and delete views for Ofertas and Solicitacoes, with confirmation pages and buttons on detail pages.

**Architecture:** Reuse existing `OfertaForm`/`SolicitacaoForm`, add `@staff_member_required` views for edit/delete, create confirmation template, add admin buttons to detail pages.

**Tech Stack:** Django 5.x, SQLite, Material Design + Glassmorphism templates.

---

### Task 1: Create reusable delete confirmation template

**Files:**
- Create: `templates/servconecta/confirm_delete.html`

A generic confirmation template that shows the object title and asks "Tem certeza que deseja excluir?". Uses the same glass card styling as the form templates. Two buttons: "Cancelar" (link back) and "Excluir" (red submit button).

```html
{% extends "servconecta/base.html" %}
{% block title %}Excluir {{ object.titulo }} · ServConecta{% endblock %}
{% block extra_head %}
<style>
  .confirm-shell { max-width: 720px; margin: 32px auto; padding-bottom: 32px; }
  .confirm-card { padding: 32px; border-radius: 20px; }
  .confirm-card h1 { font-size: 1.5rem; font-weight: 700; color: var(--md-on-surface); margin-bottom: 12px; }
  .confirm-card p { color: var(--md-on-surface-variant); margin-bottom: 24px; }
  .confirm-actions { display: flex; gap: 12px; justify-content: flex-end; }
  .btn--danger { background: #dc2626; color: #fff; }
  @media (max-width: 640px) {
    .confirm-card { padding: 24px; }
    .confirm-actions { flex-direction: column-reverse; }
    .confirm-actions .btn { width: 100%; justify-content: center; }
  }
</style>
{% endblock %}
{% block content %}
<div class="confirm-shell">
  <div class="glass confirm-card">
    <h1>Excluir {{ object.titulo }}</h1>
    <p>Tem certeza que deseja excluir esta {{ type_name }}? Esta ação não pode ser desfeita.</p>
    <div class="confirm-actions">
      <a class="btn btn--outline" href="{{ object.get_absolute_url }}">
        <span class="material-symbols-rounded">close</span>
        Cancelar
      </a>
      <form method="post">
        {% csrf_token %}
        <button class="btn btn--danger" type="submit">
          <span class="material-symbols-rounded">delete</span>
          Excluir
        </button>
      </form>
    </div>
  </div>
</div>
{% endblock %}
```

---

### Task 2: Add edit and delete views to views.py

**Files:**
- Modify: `servconecta/views.py` (add 4 new views at the end)

Use `@staff_member_required` from `django.contrib.admin.views.decorators`. Reuse existing forms. On successful edit, redirect to detail. On delete, redirect to listing.

```python
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

@staff_member_required
def oferta_editar(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    if request.method == "POST":
        form = OfertaForm(request.POST, request.FILES, instance=oferta)
        if form.is_valid():
            form.save()
            messages.success(request, "Oferta atualizada com sucesso.")
            return redirect(oferta)
    else:
        form = OfertaForm(instance=oferta)
    return render(request, "servconecta/oferta_form.html", {"form": form, "editando": True})

@staff_member_required
def oferta_excluir(request, pk):
    oferta = get_object_or_404(Oferta, pk=pk)
    if request.method == "POST":
        oferta.delete()
        messages.success(request, "Oferta excluída com sucesso.")
        return redirect("ofertas")
    return render(request, "servconecta/confirm_delete.html", {"object": oferta, "type_name": "oferta"})

@staff_member_required
def solicitacao_editar(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if request.method == "POST":
        form = SolicitacaoForm(request.POST, instance=solicitacao)
        if form.is_valid():
            form.save()
            messages.success(request, "Solicitação atualizada com sucesso.")
            return redirect(solicitacao)
    else:
        form = SolicitacaoForm(instance=solicitacao)
    return render(request, "servconecta/solicitacao_form.html", {"form": form, "editando": True})

@staff_member_required
def solicitacao_excluir(request, pk):
    solicitacao = get_object_or_404(Solicitacao, pk=pk)
    if request.method == "POST":
        solicitacao.delete()
        messages.success(request, "Solicitação excluída com sucesso.")
        return redirect("solicitacoes")
    return render(request, "servconecta/confirm_delete.html", {"object": solicitacao, "type_name": "solicitação"})
```

---

### Task 3: Add URL routes

**Files:**
- Modify: `servconecta/urls.py` (add 4 new paths)

```python
path("ofertas/<int:pk>/editar/", views.oferta_editar, name="oferta_editar"),
path("ofertas/<int:pk>/excluir/", views.oferta_excluir, name="oferta_excluir"),
path("solicitacoes/<int:pk>/editar/", views.solicitacao_editar, name="solicitacao_editar"),
path("solicitacoes/<int:pk>/excluir/", views.solicitacao_excluir, name="solicitacao_excluir"),
```

---

### Task 4: Update form templates to support edit mode

**Files:**
- Modify: `templates/servconecta/oferta_form.html` (change h1 and button text)
- Modify: `templates/servconecta/solicitacao_form.html` (change h1 and button text)

When `editando` is in context, show "Editar oferta" / "Editar solicitação" as title and "Salvar alterações" as button text.

In both form templates, change:
- `<h1>Nova oferta</h1>` → `{% if editando %}<h1>Editar oferta</h1>{% else %}<h1>Nova oferta</h1>{% endif %}`
- `<h1>Nova solicitação</h1>` → `{% if editando %}<h1>Editar solicitação</h1>{% else %}<h1>Nova solicitação</h1>{% endif %}`
- Button text: `{% if editando %}Salvar alterações{% else %}Publicar oferta{% endif %}` / `{% if editando %}Salvar alterações{% else %}Publicar solicitação{% endif %}`

---

### Task 5: Add admin buttons on detail pages

**Files:**
- Modify: `templates/servconecta/oferta_detalhe.html` (add edit/delete buttons)
- Modify: `templates/servconecta/solicitacao_detalhe.html` (add edit/delete buttons)

After the existing action buttons, add a conditional block `{% if user.is_staff %}` with edit and delete links styled as small ghost buttons.

---

### Task 6: Run and verify

- Start server: `uv run manage.py runserver 0.0.0.0:8001`
- Test as admin: login with staff user, verify edit/delete buttons appear on detail pages
- Test edit: fill form, submit, verify redirect to detail with updated data
- Test delete: confirm delete, verify redirect to listing with success message
- Test as non-admin: verify edit/delete buttons are hidden and direct URLs return 403
