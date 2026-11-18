from django.core.management.base import BaseCommand, CommandError

from central.servicos import ia, kb


class Command(BaseCommand):
    help = "Gera embeddings (modelo EMB100) dos artigos ativos. Opcional: a busca textual funciona sem isso."

    def handle(self, *args, **opts):
        try:
            n = kb.indexar_embeddings()
        except ia.IAIndisponivel as e:
            raise CommandError(f"IA indisponível ({e}). Defina SATELA_API_KEY.")
        self.stdout.write(self.style.SUCCESS(f"{n} artigos indexados. Habilite com KB_EMBEDDINGS=1."))
