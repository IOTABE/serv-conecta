# ServConecta

Plataforma que conecta profissionais e clientes: ofertas de serviços, solicitações de clientes, autenticação e painel administrativo. Interface em **Material Design (CSS puro)** com efeito **glassmorphism** (vidro fosco) em navbar, hero e cards.

## Tecnologias

- **Django 5.x** — backend, templates, admin
- **Pillow** — upload de imagens (`ImageField` das ofertas)
- **SQLite** — banco padrão de desenvolvimento
- **CSS puro** — Material Design + glassmorphism (Google Fonts: Roboto + Material Symbols via CDN)

## Estrutura do projeto

```
.
├── manage.py
├── requirements.txt
├── config/                     # Pacote de configuração do projeto
│   ├── __init__.py
│   ├── settings.py             # Apps, templates, banco, i18n, media, auth
│   ├── urls.py                 # Rotas raiz (admin + app + media em DEBUG)
│   ├── wsgi.py
│   └── asgi.py
├── servconecta/                # App principal
│   ├── __init__.py
│   ├── models.py               # Categoria, Oferta, Solicitacao
│   ├── forms.py                # CadastroForm, OfertaForm, SolicitacaoForm
│   ├── views.py                # Listagens, detalhes, criação, cadastro
│   ├── urls.py                 # Rotas nomeadas usadas nos templates
│   ├── admin.py                # Registro das models no Django Admin
│   └── migrations/
│       └── __init__.py
└── templates/servconecta/      # Templates de vidro (glassmorphism)
    ├── base.html               # CSS global, navbar, rodapé, ripple
    ├── home.html               # Hero + destaques + recentes
    ├── ofertas.html            # Listagem + busca/filtro + paginação
    ├── solicitacoes.html       # Listagem + busca/filtro + paginação
    ├── oferta_detalhe.html
    ├── solicitacao_detalhe.html
    ├── oferta_form.html        # Criar oferta (upload de imagem)
    ├── solicitacao_form.html   # Criar solicitação
    ├── login.html
    └── cadastro.html
```

## Como rodar

```bash
# 1. (Opcional) Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Crie as migrações e aplique no banco
python manage.py makemigrations
python manage.py migrate

# 4. Crie um superusuário (acesso ao /admin)
python manage.py createsuperuser

# 5. Rode o servidor de desenvolvimento
python manage.py runserver
```

Acesse:

- Aplicação: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Rotas

| Nome (`{% url %}`)      | Caminho                        | Descrição                                  |
| ----------------------- | ------------------------------ | ------------------------------------------ |
| `home`                  | `/`                            | Página inicial (hero + recentes)           |
| `ofertas`               | `/ofertas/`                    | Listagem de ofertas (busca `?q=`, `?cidade=`) |
| `oferta_detalhe`        | `/ofertas/<pk>/`               | Detalhe de uma oferta                      |
| `oferta_criar`          | `/ofertas/nova/`               | Criar oferta (requer login)                |
| `solicitacoes`          | `/solicitacoes/`               | Listagem de solicitações (busca/filtro)    |
| `solicitacao_detalhe`   | `/solicitacoes/<pk>/`          | Detalhe de uma solicitação                 |
| `solicitacao_criar`     | `/solicitacoes/nova/`          | Criar solicitação (requer login)           |
| `login`                 | `/entrar/`                     | Login                                      |
| `logout`                | `/sair/`                       | Logout                                     |
| `cadastro`              | `/cadastro/`                   | Cadastro de usuário (com auto-login)       |

> Os nomes das rotas correspondem exatamente aos usados nos templates com `{% url %}`.

## Upload de imagens

As imagens das ofertas são salvas em `MEDIA_ROOT` (pasta `media/`). Em desenvolvimento (`DEBUG=True`), o `config/urls.py` já serve esses arquivos. Em produção, configure seu servidor web (ou storage) para servir a pasta de mídia.

## Personalização visual

- **Cores / tema:** variáveis CSS no topo de `base.html` (dentro de `:root`).
- **Fontes e ícones:** Google Fonts (Roboto + Material Symbols) carregados no `<head>` do `base.html`.
- **Efeito de vidro:** classe utilitária `.glass` (usa `backdrop-filter: blur(...)`).
