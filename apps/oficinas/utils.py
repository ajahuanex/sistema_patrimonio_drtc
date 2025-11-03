import openpyxl
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Oficina


class OficinaImporter:
    """Clase para importar oficinas desde archivos Excel"""
    
    COLUMNAS_REQUERIDAS = [
        'CODIGO',
        'NOMBRE',
        'RESPONSABLE'
    ]
    
    COLUMNAS_OPCIONALES = [
        'DESCRIPCION',
        'CARGO_RESPONSABLE',
        'TELEFONO',
        'EMAIL',
        'UBICACION',
        'ESTADO'
    ]
    
    COLUMNAS_ALTERNATIVAS = {
        'CODIGO': ['CÓDIGO', 'COD_OFICINA', 'CODIGO_OFICINA'],
        'NOMBRE': ['NOMBRE_OFICINA', 'OFICINA', 'DENOMINACION'],
        'RESPONSABLE': ['RESPONSABLE_OFICINA', 'ENCARGADO', 'JEFE'],
        'DESCRIPCION': ['DESCRIPCIÓN', 'DESC', 'DETALLE'],
        'CARGO_RESPONSABLE': ['CARGO', 'PUESTO', 'CARGO_ENCARGADO'],
        'TELEFONO': ['TELÉFONO', 'TEL', 'CELULAR'],
        'EMAIL': ['CORREO', 'CORREO_ELECTRONICO', 'E-MAIL'],
        'UBICACION': ['UBICACIÓN', 'DIRECCION', 'DIRECCIÓN'],
        'ESTADO': ['ACTIVO', 'VIGENTE', 'STATUS']
    }
    
    def __init__(self):
        self.errores = []
        self.warnings = []
        self.registros_procesados = 0
        self.registros_creados = 0
        self.registros_actualizados = 0
    
    def validar_archivo(self, archivo_path):
        """Valida que el archivo Excel tenga la estructura correcta"""
        try:
            workbook = openpyxl.load_workbook(archivo_path)
            sheet = workbook.active
            
            # Obtener la primera fila (encabezados)
            headers = []
            for cell in sheet[1]:
                if cell.value:
                    headers.append(str(cell.value).strip())
            
            # Verificar columnas requeridas
            columnas_encontradas = {}
            
            # Buscar columnas requeridas
            for col_requerida in self.COLUMNAS_REQUERIDAS:
                encontrada = False
                
                # Buscar columna exacta
                for header in headers:
                    if header.upper() == col_requerida.upper():
                        columnas_encontradas[col_requerida] = header
                        encontrada = True
                        break
                
                # Buscar alternativas
                if not encontrada and col_requerida in self.COLUMNAS_ALTERNATIVAS:
                    for alternativa in self.COLUMNAS_ALTERNATIVAS[col_requerida]:
                        for header in headers:
                            if header.upper() == alternativa.upper():
                                columnas_encontradas[col_requerida] = header
                                encontrada = True
                                break
                        if encontrada:
                            break
                
                if not encontrada:
                    self.errores.append(f"Columna requerida no encontrada: {col_requerida}")
            
            # Buscar columnas opcionales
            for col_opcional in self.COLUMNAS_OPCIONALES:
                encontrada = False
                
                # Buscar columna exacta
                for header in headers:
                    if header.upper() == col_opcional.upper():
                        columnas_encontradas[col_opcional] = header
                        encontrada = True
                        break
                
                # Buscar alternativas
                if not encontrada and col_opcional in self.COLUMNAS_ALTERNATIVAS:
                    for alternativa in self.COLUMNAS_ALTERNATIVAS[col_opcional]:
                        for header in headers:
                            if header.upper() == alternativa.upper():
                                columnas_encontradas[col_opcional] = header
                                encontrada = True
                                break
                        if encontrada:
                            break
            
            if self.errores:
                return False, columnas_encontradas
            
            return True, columnas_encontradas
            
        except Exception as e:
            self.errores.append(f"Error al leer el archivo: {str(e)}")
            return False, {}
    
    def procesar_archivo(self, archivo_path, actualizar_existentes=False):
        """Procesa el archivo Excel e importa los datos"""
        # Validar archivo
        es_valido, columnas_map = self.validar_archivo(archivo_path)
        if not es_valido:
            return self.generar_reporte()
        
        try:
            workbook = openpyxl.load_workbook(archivo_path)
            sheet = workbook.active
            
            # Obtener índices de columnas
            headers = [str(cell.value).strip() if cell.value else '' for cell in sheet[1]]
            indices_columnas = {}
            
            for col_name, header_encontrado in columnas_map.items():
                try:
                    indices_columnas[col_name] = headers.index(header_encontrado)
                except ValueError:
                    # Columna opcional no encontrada
                    if col_name not in self.COLUMNAS_REQUERIDAS:
                        continue
                    self.errores.append(f"Error al encontrar índice de columna: {header_encontrado}")
                    return self.generar_reporte()
            
            # Procesar filas de datos
            with transaction.atomic():
                for row_num, row in enumerate(sheet.iter_rows(min_row=2), start=2):
                    try:
                        self.procesar_fila(row, indices_columnas, row_num, actualizar_existentes)
                    except Exception as e:
                        self.errores.append(f"Error en fila {row_num}: {str(e)}")
                        continue
            
        except Exception as e:
            self.errores.append(f"Error general al procesar archivo: {str(e)}")
        
        return self.generar_reporte()
    
    def procesar_fila(self, row, indices_columnas, row_num, actualizar_existentes):
        """Procesa una fila individual del Excel"""
        # Extraer datos de la fila
        datos = {}
        for col_name, col_index in indices_columnas.items():
            if col_index < len(row):
                cell_value = row[col_index].value
                datos[col_name] = str(cell_value).strip() if cell_value else ''
            else:
                datos[col_name] = ''
        
        # Validar datos requeridos
        if not datos.get('CODIGO') or not datos.get('NOMBRE') or not datos.get('RESPONSABLE'):
            self.warnings.append(f"Fila {row_num}: Código, nombre o responsable vacíos, omitida")
            return
        
        # Normalizar datos
        codigo = datos['CODIGO'].upper()
        nombre = datos['NOMBRE'].strip()
        responsable = datos['RESPONSABLE'].strip()
        descripcion = datos.get('DESCRIPCION', '')
        cargo_responsable = datos.get('CARGO_RESPONSABLE', '')
        telefono = datos.get('TELEFONO', '')
        email = datos.get('EMAIL', '')
        ubicacion = datos.get('UBICACION', '')
        
        # Procesar estado
        estado_texto = datos.get('ESTADO', 'ACTIVO').upper()
        estado = True  # Default activo
        if estado_texto in ['INACTIVO', 'INACTIVA', 'FALSE', '0', 'NO']:
            estado = False
        
        # Verificar si ya existe
        oficina_existente = None
        try:
            oficina_existente = Oficina.objects.get(codigo=codigo)
        except Oficina.DoesNotExist:
            pass
        
        if oficina_existente:
            if actualizar_existentes:
                # Actualizar existente
                oficina_existente.nombre = nombre
                oficina_existente.descripcion = descripcion
                oficina_existente.responsable = responsable
                oficina_existente.cargo_responsable = cargo_responsable
                oficina_existente.telefono = telefono
                oficina_existente.email = email
                oficina_existente.ubicacion = ubicacion
                oficina_existente.estado = estado
                oficina_existente.save()
                self.registros_actualizados += 1
            else:
                self.warnings.append(f"Fila {row_num}: Código {codigo} ya existe, omitido")
        else:
            # Crear nuevo
            try:
                Oficina.objects.create(
                    codigo=codigo,
                    nombre=nombre,
                    descripcion=descripcion,
                    responsable=responsable,
                    cargo_responsable=cargo_responsable,
                    telefono=telefono,
                    email=email,
                    ubicacion=ubicacion,
                    estado=estado
                )
                self.registros_creados += 1
            except Exception as e:
                self.errores.append(f"Fila {row_num}: Error al crear registro: {str(e)}")
                return
        
        self.registros_procesados += 1
    
    def generar_reporte(self):
        """Genera un reporte del proceso de importación"""
        return {
            'exito': len(self.errores) == 0,
            'registros_procesados': self.registros_procesados,
            'registros_creados': self.registros_creados,
            'registros_actualizados': self.registros_actualizados,
            'errores': self.errores,
            'warnings': self.warnings,
            'resumen': f"Procesados: {self.registros_procesados}, "
                      f"Creados: {self.registros_creados}, "
                      f"Actualizados: {self.registros_actualizados}, "
                      f"Errores: {len(self.errores)}, "
                      f"Advertencias: {len(self.warnings)}"
        }


def importar_oficinas_desde_excel(archivo_path, actualizar_existentes=False):
    """Función helper para importar oficinas"""
    importer = OficinaImporter()
    return importer.procesar_archivo(archivo_path, actualizar_existentes)


def validar_estructura_oficinas(archivo_path):
    """Función helper para validar estructura del archivo"""
    importer = OficinaImporter()
    es_valido, columnas_map = importer.validar_archivo(archivo_path)
    return {
        'es_valido': es_valido,
        'columnas_encontradas': columnas_map,
        'errores': importer.errores
    }