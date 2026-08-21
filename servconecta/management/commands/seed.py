import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from servconecta.models import Categoria, Oferta, Solicitacao

User = get_user_model()


CATEGORIAS = [
    "Tecnologia",
    "Jardinagem",
    "Reformas",
    "Limpeza",
    "Aulas",
    "Beleza",
    "Transporte",
    "Eventos",
]

USUARIOS = [
    {"username": "ana.silva", "first_name": "Ana", "last_name": "Silva", "email": "ana@exemplo.com"},
    {"username": "bruno.costa", "first_name": "Bruno", "last_name": "Costa", "email": "bruno@exemplo.com"},
    {"username": "carla.souza", "first_name": "Carla", "last_name": "Souza", "email": "carla@exemplo.com"},
    {"username": "diego.lima", "first_name": "Diego", "last_name": "Lima", "email": "diego@exemplo.com"},
]

OFERTAS = [
    {
        "titulo": "Formatação de computadores",
        "descricao": "Formatação de computadores com Windows 10, 11 e LINUX. Backup dos seus arquivos incluso e instalação dos programas essenciais.",
        "preco": Decimal("150.00"),
        "unidade": "SERVIÇO",
        "cidade": "Araguaína",
        "categoria": "Tecnologia",
        "verificado": True,
    },
    {
        "titulo": "Manutenção de jardins",
        "descricao": "Poda, corte de grama, adubação e limpeza completa de jardins residenciais e comerciais.",
        "preco": Decimal("120.00"),
        "unidade": "DIÁRIA",
        "cidade": "Palmas",
        "categoria": "Jardinagem",
        "verificado": True,
    },
    {
        "titulo": "Pintura residencial",
        "descricao": "Pintura interna e externa com acabamento profissional. Orçamento sem compromisso e materiais de qualidade.",
        "preco": Decimal("35.00"),
        "unidade": "M²",
        "cidade": "Araguaína",
        "categoria": "Reformas",
        "verificado": False,
    },
    {
        "titulo": "Limpeza pós-obra",
        "descricao": "Limpeza pesada pós-obra e pós-reforma. Removemos respingos de tinta, cimento e deixamos o ambiente pronto para uso.",
        "preco": Decimal("250.00"),
        "unidade": "SERVIÇO",
        "cidade": "Gurupi",
        "categoria": "Limpeza",
        "verificado": True,
    },
    {
        "titulo": "Aulas particulares de matemática",
        "descricao": "Reforço escolar para ensino fundamental e médio. Preparação para vestibular e ENEM com material próprio.",
        "preco": Decimal("60.00"),
        "unidade": "HORA",
        "cidade": "Palmas",
        "categoria": "Aulas",
        "verificado": False,
    },
    {
        "titulo": "Design de sobrancelhas",
        "descricao": "Design de sobrancelhas com henna e técnica fio a fio. Atendimento com hora marcada e ambiente climatizado.",
        "preco": Decimal("45.00"),
        "unidade": "SERVIÇO",
        "cidade": "Araguaína",
        "categoria": "Beleza",
        "verificado": True,
    },
]

SOLICITACOES = [
    {
        "titulo": "Serviços de jardinagem",
        "descricao": "Preciso de manutenção completa do jardim de casa: corte de grama, poda das árvores e limpeza dos canteiros.",
        "orcamento": Decimal("200.00"),
        "cidade": "Araguaína",
        "categoria": "Jardinagem",
        "prazo_dias": 10,
        "status": Solicitacao.Status.ABERTA,
    },
    {
        "titulo": "Instalação de ar-condicionado",
        "descricao": "Instalação de dois splits de 12.000 BTUs. Já tenho os aparelhos, preciso apenas da mão de obra e suportes.",
        "orcamento": Decimal("400.00"),
        "cidade": "Palmas",
        "categoria": "Reformas",
        "prazo_dias": 5,
        "status": Solicitacao.Status.ABERTA,
    },
    {
        "titulo": "Diarista para limpeza semanal",
        "descricao": "Procuro diarista para limpeza de apartamento de 2 quartos uma vez por semana, preferencialmente às quintas.",
        "orcamento": Decimal("150.00"),
        "cidade": "Gurupi",
        "categoria": "Limpeza",
        "prazo_dias": 15,
        "status": Solicitacao.Status.EM_ANDAMENTO,
    },
    {
        "titulo": "Fotógrafo para evento",
        "descricao": "Preciso de fotógrafo para cobertura de aniversário de 15 anos. Cerca de 4 horas de cobertura e entrega das fotos editadas.",
        "orcamento": None,
        "cidade": "Araguaína",
        "categoria": "Eventos",
        "prazo_dias": 20,
        "status": Solicitacao.Status.ABERTA,
    },
]


class Command(BaseCommand):
    help = "Popula o banco com categorias, usuários, ofertas e solicitações de exemplo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove os dados de exemplo antes de recriar.",
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Removendo dados de exemplo existentes...")
            Oferta.objects.all().delete()
            Solicitacao.objects.all().delete()
            Categoria.objects.all().delete()
            User.objects.filter(username__in=[u["username"] for u in USUARIOS]).delete()

        # Categorias
        categorias = {}
        for nome in CATEGORIAS:
            cat, _ = Categoria.objects.get_or_create(
                nome=nome, defaults={"slug": slugify(nome)}
            )
            categorias[nome] = cat
        self.stdout.write(self.style.SUCCESS(f"{len(categorias)} categorias prontas."))

        # Usuários (senha padrão: senha123)
        usuarios = []
        for dados in USUARIOS:
            user, criado = User.objects.get_or_create(
                username=dados["username"],
                defaults={
                    "first_name": dados["first_name"],
                    "last_name": dados["last_name"],
                    "email": dados["email"],
                },
            )
            if criado:
                user.set_password("senha123")
                user.save()
            usuarios.append(user)
        self.stdout.write(self.style.SUCCESS(f"{len(usuarios)} usuários prontos (senha: senha123)."))

        # Ofertas
        criadas = 0
        for i, dados in enumerate(OFERTAS):
            prestador = usuarios[i % len(usuarios)]
            _, criado = Oferta.objects.get_or_create(
                titulo=dados["titulo"],
                prestador=prestador,
                defaults={
                    "descricao": dados["descricao"],
                    "preco": dados["preco"],
                    "unidade": dados["unidade"],
                    "cidade": dados["cidade"],
                    "categoria": categorias.get(dados["categoria"]),
                    "prestador_verificado": dados["verificado"],
                },
            )
            criadas += int(criado)
        self.stdout.write(self.style.SUCCESS(f"{criadas} ofertas criadas."))

        # Solicitações
        hoje = timezone.now().date()
        criadas = 0
        for i, dados in enumerate(SOLICITACOES):
            cliente = usuarios[(i + 1) % len(usuarios)]
            _, criado = Solicitacao.objects.get_or_create(
                titulo=dados["titulo"],
                cliente=cliente,
                defaults={
                    "descricao": dados["descricao"],
                    "orcamento": dados["orcamento"],
                    "cidade": dados["cidade"],
                    "categoria": categorias.get(dados["categoria"]),
                    "prazo": hoje + datetime.timedelta(days=dados["prazo_dias"]),
                    "status": dados["status"],
                },
            )
            criadas += int(criado)
        self.stdout.write(self.style.SUCCESS(f"{criadas} solicitações criadas."))

        self.stdout.write(self.style.SUCCESS("Seed concluído com sucesso!"))
