from django.core.management.base import BaseCommand
from django.utils.text import slugify

from servconecta.models import Categoria, Subcategoria


class Command(BaseCommand):
    help = "Popula o banco de dados com categorias e subcategorias iniciais de serviços."

    def handle(self, *args, **options):
        dados = {
            "Assistência Técnica": [
                "Celulares e Tablets",
                "Notebooks e Computadores",
                "Eletrodomésticos",
                "Televisores e Áudio",
                "Videogames e Consoles",
            ],
            "Reformas e Reparos": [
                "Pintura",
                "Eletricista",
                "Encanador",
                "Pedreiro e Alvenaria",
                "Gesso e Drywall",
                "Marcenaria",
            ],
            "Design e Tecnologia": [
                "Desenvolvimento Web",
                "Design Gráfico e Logos",
                "Edição de Vídeo",
                "Marketing Digital",
                "Gestão de Redes Sociais",
            ],
            "Serviços Domésticos": [
                "Limpeza e Diária",
                "Passadeira",
                "Cozinheiro(a)",
                "Jardinagem",
                "Piscineiro",
            ],
            "Aulas e Consultoria": [
                "Aulas de Idiomas",
                "Reforço Escolar",
                "Personal Trainer",
                "Consultoria Financeira",
            ],
            "Eventos e Festas": [
                "Fotografia e Filmatória",
                "DJ e Som",
                "Buffet e Confeitaria",
                "Decoração de Eventos",
            ],
        }

        total_cat = 0
        total_sub = 0

        for cat_nome, sub_lista in dados.items():
            cat_slug = slugify(cat_nome)
            categoria, created_cat = Categoria.objects.get_or_create(
                slug=cat_slug,
                defaults={"nome": cat_nome},
            )
            if created_cat:
                total_cat += 1

            for sub_nome in sub_lista:
                sub_slug = slugify(sub_nome)
                _, created_sub = Subcategoria.objects.get_or_create(
                    categoria=categoria,
                    slug=sub_slug,
                    defaults={"nome": sub_nome},
                )
                if created_sub:
                    total_sub += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"População concluída com sucesso! Criadas {total_cat} categorias e {total_sub} subcategorias."
            )
        )
