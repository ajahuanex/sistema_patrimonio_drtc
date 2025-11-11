from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from datetime import datetime, timedelta
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Genera datos de prueba para el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--bienes',
            type=int,
            default=50,
            help='Número de bienes a crear (default: 50)'
        )

    def handle(self, *args, **options):
        self.stdout.write('Generando datos de prueba...')
        
        # Obtener catálogos y oficinas existentes
        catalogos = list(Catalogo.objects.filter(deleted_at__isnull=True))
        oficinas = list(Oficina.objects.filter(deleted_at__isnull=True))
        
        if not catalogos:
            self.stdout.write(self.style.ERROR('No hay catálogos disponibles'))
            return
        
        if not oficinas:
            self.stdout.write(self.style.ERROR('No hay oficinas disponibles'))
            return
        
        # Crear bienes de prueba
        bienes_creados = self.crear_bienes(options['bienes'], oficinas, catalogos)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Datos de prueba generados exitosamente:\n'
                f'- {bienes_creados} bienes patrimoniales'
            )
        )

    def crear_bienes(self, cantidad, oficinas, catalogos):
        estados = ['N', 'B', 'R', 'M']
        marcas = ['HP', 'DELL', 'LENOVO', 'SAMSUNG', 'LG', 'TOYOTA', 'NISSAN', 'STEELCASE']
        
        # Filtrar solo oficinas activas
        oficinas_activas = [o for o in oficinas if o.estado]
        if not oficinas_activas:
            self.stdout.write(self.style.WARNING('No hay oficinas activas, usando todas'))
            oficinas_activas = oficinas
        
        # Filtrar solo catálogos activos
        catalogos_activos = [c for c in catalogos if c.estado == 'ACTIVO']
        if not catalogos_activos:
            self.stdout.write(self.style.WARNING('No hay catálogos activos, usando todos'))
            catalogos_activos = catalogos
        
        bienes_creados = 0
        for i in range(cantidad):
            try:
                # Generar código único
                codigo = f'BP{datetime.now().year}{i+1:06d}'
                
                # Verificar que no exista
                if BienPatrimonial.objects.filter(codigo_patrimonial=codigo).exists():
                    continue
                
                oficina = random.choice(oficinas_activas)
                item_catalogo = random.choice(catalogos_activos)
                estado = random.choice(estados)
                marca = random.choice(marcas)
                
                # Fecha aleatoria en los últimos 2 años
                fecha_base = datetime.now() - timedelta(days=random.randint(1, 730))
                
                # Valor con solo 2 decimales usando Decimal
                valor = Decimal(str(round(random.uniform(100, 5000), 2)))
                
                bien = BienPatrimonial.objects.create(
                    codigo_patrimonial=codigo,
                    catalogo=item_catalogo,
                    marca=marca,
                    modelo=f'Modelo-{random.randint(100, 999)}',
                    serie=f'SN{random.randint(100000, 999999)}',
                    estado_bien=estado,
                    oficina=oficina,
                    fecha_adquisicion=fecha_base.date(),
                    valor_adquisicion=valor,
                    observaciones=f'Bien de prueba #{i+1}'
                )
                
                bienes_creados += 1
                if bienes_creados % 10 == 0:
                    self.stdout.write(f'Creados {bienes_creados} bienes...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creando bien #{i+1}: {str(e)}')
                )
        
        return bienes_creados
