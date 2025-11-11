from django.core.management.base import BaseCommand
from apps.bienes.models import BienPatrimonial

class Command(BaseCommand):
    help = 'Elimina todos los datos de prueba generados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma que quieres eliminar los datos de prueba'
        )

    def handle(self, *args, **options):
        if not options['confirmar']:
            self.stdout.write(
                self.style.WARNING(
                    'ADVERTENCIA: Este comando eliminará TODOS los bienes de prueba.\n'
                    'Para confirmar, ejecuta: python manage.py limpiar_datos_prueba --confirmar'
                )
            )
            return
        
        # Contar bienes de prueba (los que empiezan con BP2025)
        bienes_prueba = BienPatrimonial.objects.filter(
            codigo_patrimonial__startswith='BP2025'
        )
        cantidad = bienes_prueba.count()
        
        if cantidad == 0:
            self.stdout.write(self.style.SUCCESS('No hay bienes de prueba para eliminar'))
            return
        
        # Eliminar
        bienes_prueba.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Se eliminaron {cantidad} bienes de prueba correctamente'
            )
        )
