from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.bienes.models import BienPatrimonial
from apps.bienes.utils import QRCodeGenerator


class Command(BaseCommand):
    help = 'Genera códigos QR para bienes patrimoniales que no los tienen'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerar QR codes para todos los bienes (incluso los que ya tienen)',
        )
        parser.add_argument(
            '--codigo',
            type=str,
            help='Generar QR code para un bien específico por código patrimonial',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin ejecutar los cambios',
        )
    
    def handle(self, *args, **options):
        generator = QRCodeGenerator()
        
        # Determinar qué bienes procesar
        if options['codigo']:
            # Bien específico
            try:
                queryset = BienPatrimonial.objects.filter(codigo_patrimonial=options['codigo'])
                if not queryset.exists():
                    self.stdout.write(
                        self.style.ERROR(f'No se encontró bien con código: {options["codigo"]}')
                    )
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error al buscar bien: {str(e)}')
                )
                return
        elif options['all']:
            # Todos los bienes
            queryset = BienPatrimonial.objects.all()
            self.stdout.write(
                self.style.WARNING('Regenerando QR codes para TODOS los bienes...')
            )
        else:
            # Solo bienes sin QR code o con QR inválido
            queryset = BienPatrimonial.objects.filter(
                Q(qr_code='') | Q(qr_code__isnull=True) |
                Q(url_qr='') | Q(url_qr__isnull=True)
            )
        
        total_bienes = queryset.count()
        
        if total_bienes == 0:
            self.stdout.write(
                self.style.SUCCESS('No hay bienes que requieran generación de QR codes.')
            )
            return
        
        self.stdout.write(f'Procesando {total_bienes} bienes...')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: No se realizarán cambios')
            )
            for bien in queryset[:10]:  # Mostrar solo los primeros 10
                self.stdout.write(f'  - {bien.codigo_patrimonial}: {bien.denominacion}')
            if total_bienes > 10:
                self.stdout.write(f'  ... y {total_bienes - 10} más')
            return
        
        # Procesar bienes
        contador_exitosos = 0
        contador_errores = 0
        
        for bien in queryset:
            try:
                qr_anterior = bien.qr_code
                url_anterior = bien.url_qr
                
                # Generar nuevo QR si es necesario
                if options['all'] or not bien.qr_code or not bien.url_qr:
                    generator.generar_qr_para_bien(bien)
                    bien.save(update_fields=['qr_code', 'url_qr'])
                    
                    self.stdout.write(
                        f'✓ {bien.codigo_patrimonial}: QR generado'
                    )
                    
                    if options['verbosity'] >= 2:
                        self.stdout.write(f'    QR: {bien.qr_code}')
                        self.stdout.write(f'    URL: {bien.url_qr}')
                    
                    contador_exitosos += 1
                else:
                    if options['verbosity'] >= 2:
                        self.stdout.write(f'- {bien.codigo_patrimonial}: Ya tiene QR válido')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ {bien.codigo_patrimonial}: Error - {str(e)}')
                )
                contador_errores += 1
        
        # Resumen
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'Proceso completado:')
        )
        self.stdout.write(f'  - QR codes generados: {contador_exitosos}')
        if contador_errores > 0:
            self.stdout.write(
                self.style.ERROR(f'  - Errores: {contador_errores}')
            )
        
        # Validar QR codes únicos
        self.stdout.write('\nValidando unicidad de QR codes...')
        duplicados = self._verificar_qr_duplicados()
        
        if duplicados:
            self.stdout.write(
                self.style.ERROR(f'¡ATENCIÓN! Se encontraron {len(duplicados)} QR codes duplicados:')
            )
            for qr_code, bienes in duplicados.items():
                self.stdout.write(f'  QR {qr_code}:')
                for bien in bienes:
                    self.stdout.write(f'    - {bien.codigo_patrimonial}')
        else:
            self.stdout.write(
                self.style.SUCCESS('✓ Todos los QR codes son únicos')
            )
    
    def _verificar_qr_duplicados(self):
        """Verifica si hay QR codes duplicados"""
        from collections import defaultdict
        
        duplicados = defaultdict(list)
        
        for bien in BienPatrimonial.objects.exclude(qr_code='').exclude(qr_code__isnull=True):
            duplicados[bien.qr_code].append(bien)
        
        # Filtrar solo los que tienen duplicados
        return {qr: bienes for qr, bienes in duplicados.items() if len(bienes) > 1}