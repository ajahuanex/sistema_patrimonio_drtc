from django.db.models import Q, Count, Sum, Avg
from django.db.models.functions import Extract
from django.utils import timezone
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from .models import ConfiguracionFiltro
import logging

logger = logging.getLogger(__name__)


class FiltroAvanzado:
    """Clase para aplicar filtros avanzados a los bienes patrimoniales"""
    
    def __init__(self, configuracion=None, parametros=None):
        """
        Inicializa el filtro avanzado
        
        Args:
            configuracion: Instancia de ConfiguracionFiltro o dict con parámetros
            parametros: Dict adicional con parámetros de filtro
        """
        self.configuracion = configuracion
        self.parametros = parametros or {}
        
        if isinstance(configuracion, ConfiguracionFiltro):
            self.parametros.update(configuracion.to_dict())
        elif isinstance(configuracion, dict):
            self.parametros.update(configuracion)
    
    def aplicar_filtros(self, queryset=None):
        """
        Aplica los filtros al queryset de bienes patrimoniales
        
        Args:
            queryset: QuerySet base (opcional, por defecto todos los bienes)
            
        Returns:
            QuerySet filtrado
        """
        if queryset is None:
            queryset = BienPatrimonial.objects.all()
        
        # Obtener operador principal
        operador = self.parametros.get('operador_principal', 'AND')
        
        # Crear lista de condiciones Q
        condiciones = []
        
        # Filtros básicos
        condiciones.extend(self._filtros_oficinas())
        condiciones.extend(self._filtros_estados())
        condiciones.extend(self._filtros_catalogo())
        condiciones.extend(self._filtros_marcas_modelos())
        condiciones.extend(self._filtros_fechas())
        condiciones.extend(self._filtros_valores())
        condiciones.extend(self._filtros_texto())
        
        # Aplicar condiciones según el operador
        if condiciones:
            if operador == 'OR':
                # Combinar con OR
                filtro_final = condiciones[0]
                for condicion in condiciones[1:]:
                    filtro_final |= condicion
            else:
                # Combinar con AND (por defecto)
                filtro_final = condiciones[0]
                for condicion in condiciones[1:]:
                    filtro_final &= condicion
            
            queryset = queryset.filter(filtro_final)
        
        return queryset.distinct()
    
    def _filtros_oficinas(self):
        """Aplica filtros por oficinas"""
        condiciones = []
        oficinas = self.parametros.get('oficinas', [])
        
        if oficinas:
            # Convertir IDs de string a int si es necesario
            oficina_ids = []
            for oficina in oficinas:
                if isinstance(oficina, str) and oficina.isdigit():
                    oficina_ids.append(int(oficina))
                elif isinstance(oficina, int):
                    oficina_ids.append(oficina)
                elif hasattr(oficina, 'id'):
                    oficina_ids.append(oficina.id)
            
            if oficina_ids:
                condiciones.append(Q(oficina__id__in=oficina_ids))
        
        return condiciones
    
    def _filtros_estados(self):
        """Aplica filtros por estados del bien"""
        condiciones = []
        estados = self.parametros.get('estados_bien', [])
        
        if estados:
            condiciones.append(Q(estado_bien__in=estados))
        
        return condiciones
    
    def _filtros_catalogo(self):
        """Aplica filtros por catálogo (grupos y clases)"""
        condiciones = []
        
        # Filtros por grupos
        grupos = self.parametros.get('grupos_catalogo', [])
        if grupos:
            condiciones.append(Q(catalogo__grupo__in=grupos))
        
        # Filtros por clases
        clases = self.parametros.get('clases_catalogo', [])
        if clases:
            condiciones.append(Q(catalogo__clase__in=clases))
        
        return condiciones
    
    def _filtros_marcas_modelos(self):
        """Aplica filtros por marcas y modelos"""
        condiciones = []
        
        # Filtros por marcas
        marcas = self.parametros.get('marcas', [])
        if marcas:
            condicion_marcas = Q()
            for marca in marcas:
                condicion_marcas |= Q(marca__icontains=marca.strip())
            condiciones.append(condicion_marcas)
        
        # Filtros por modelos
        modelos = self.parametros.get('modelos', [])
        if modelos:
            condicion_modelos = Q()
            for modelo in modelos:
                condicion_modelos |= Q(modelo__icontains=modelo.strip())
            condiciones.append(condicion_modelos)
        
        return condiciones
    
    def _filtros_fechas(self):
        """Aplica filtros por fechas"""
        condiciones = []
        
        # Filtros por fecha de adquisición
        fecha_adq_desde = self.parametros.get('fecha_adquisicion_desde')
        fecha_adq_hasta = self.parametros.get('fecha_adquisicion_hasta')
        
        if fecha_adq_desde:
            condiciones.append(Q(fecha_adquisicion__gte=fecha_adq_desde))
        if fecha_adq_hasta:
            condiciones.append(Q(fecha_adquisicion__lte=fecha_adq_hasta))
        
        # Filtros por fecha de registro
        fecha_reg_desde = self.parametros.get('fecha_registro_desde')
        fecha_reg_hasta = self.parametros.get('fecha_registro_hasta')
        
        if fecha_reg_desde:
            condiciones.append(Q(created_at__date__gte=fecha_reg_desde))
        if fecha_reg_hasta:
            condiciones.append(Q(created_at__date__lte=fecha_reg_hasta))
        
        return condiciones
    
    def _filtros_valores(self):
        """Aplica filtros por valores de adquisición"""
        condiciones = []
        
        valor_min = self.parametros.get('valor_minimo')
        valor_max = self.parametros.get('valor_maximo')
        
        if valor_min:
            condiciones.append(Q(valor_adquisicion__gte=valor_min))
        if valor_max:
            condiciones.append(Q(valor_adquisicion__lte=valor_max))
        
        return condiciones
    
    def _filtros_texto(self):
        """Aplica filtros por campos de texto"""
        condiciones = []
        
        # Filtro por código patrimonial
        codigo = self.parametros.get('codigo_patrimonial', '').strip()
        if codigo:
            condiciones.append(Q(codigo_patrimonial__icontains=codigo))
        
        # Filtro por denominación
        denominacion = self.parametros.get('denominacion', '').strip()
        if denominacion:
            condiciones.append(Q(catalogo__denominacion__icontains=denominacion))
        
        # Filtro por serie
        serie = self.parametros.get('serie', '').strip()
        if serie:
            condiciones.append(Q(serie__icontains=serie))
        
        # Filtro por placa
        placa = self.parametros.get('placa', '').strip()
        if placa:
            condiciones.append(Q(placa__icontains=placa))
        
        return condiciones
    
    def obtener_estadisticas(self, queryset=None):
        """
        Obtiene estadísticas del queryset filtrado
        
        Args:
            queryset: QuerySet filtrado (opcional)
            
        Returns:
            Dict con estadísticas
        """
        if queryset is None:
            queryset = self.aplicar_filtros()
        
        estadisticas = {
            'total_bienes': queryset.count(),
            'por_estado': self._estadisticas_por_estado(queryset),
            'por_oficina': self._estadisticas_por_oficina(queryset),
            'por_grupo': self._estadisticas_por_grupo(queryset),
            'por_clase': self._estadisticas_por_clase(queryset),
            'valores': self._estadisticas_valores(queryset),
            'fechas': self._estadisticas_fechas(queryset),
        }
        
        return estadisticas
    
    def _estadisticas_por_estado(self, queryset):
        """Estadísticas por estado del bien"""
        return list(queryset.values('estado_bien').annotate(
            total=Count('id'),
            porcentaje=Count('id') * 100.0 / queryset.count() if queryset.count() > 0 else 0
        ).order_by('estado_bien'))
    
    def _estadisticas_por_oficina(self, queryset):
        """Estadísticas por oficina"""
        return list(queryset.values(
            'oficina__nombre', 'oficina__codigo'
        ).annotate(
            total=Count('id'),
            porcentaje=Count('id') * 100.0 / queryset.count() if queryset.count() > 0 else 0
        ).order_by('-total')[:10])  # Top 10 oficinas
    
    def _estadisticas_por_grupo(self, queryset):
        """Estadísticas por grupo de catálogo"""
        return list(queryset.values(
            'catalogo__grupo'
        ).annotate(
            total=Count('id'),
            porcentaje=Count('id') * 100.0 / queryset.count() if queryset.count() > 0 else 0
        ).order_by('-total')[:10])  # Top 10 grupos
    
    def _estadisticas_por_clase(self, queryset):
        """Estadísticas por clase de catálogo"""
        return list(queryset.values(
            'catalogo__clase'
        ).annotate(
            total=Count('id'),
            porcentaje=Count('id') * 100.0 / queryset.count() if queryset.count() > 0 else 0
        ).order_by('-total')[:10])  # Top 10 clases
    
    def _estadisticas_valores(self, queryset):
        """Estadísticas de valores"""
        valores_stats = queryset.aggregate(
            total_valor=Sum('valor_adquisicion'),
            valor_promedio=Avg('valor_adquisicion'),
            bienes_con_valor=Count('id', filter=Q(valor_adquisicion__isnull=False))
        )
        
        return {
            'total_valor': valores_stats['total_valor'] or 0,
            'valor_promedio': valores_stats['valor_promedio'] or 0,
            'bienes_con_valor': valores_stats['bienes_con_valor'],
            'bienes_sin_valor': queryset.count() - valores_stats['bienes_con_valor']
        }
    
    def _estadisticas_fechas(self, queryset):
        """Estadísticas de fechas"""
        fechas_stats = queryset.aggregate(
            fecha_mas_antigua=queryset.order_by('created_at').first().created_at if queryset.exists() else None,
            fecha_mas_reciente=queryset.order_by('-created_at').first().created_at if queryset.exists() else None
        )
        
        # Estadísticas por año de registro (compatible con SQLite)
        por_año = list(queryset.annotate(
            año=Extract('created_at', 'year')
        ).values('año').annotate(
            total=Count('id')
        ).order_by('-año')[:5])  # Últimos 5 años
        
        fechas_stats['por_año'] = por_año
        return fechas_stats


class GeneradorEstadisticas:
    """Clase para generar estadísticas avanzadas"""
    
    @staticmethod
    def generar_resumen_ejecutivo(queryset=None):
        """
        Genera un resumen ejecutivo con indicadores clave
        
        Args:
            queryset: QuerySet de bienes (opcional)
            
        Returns:
            Dict con resumen ejecutivo
        """
        if queryset is None:
            queryset = BienPatrimonial.objects.all()
        
        total_bienes = queryset.count()
        
        # Indicadores básicos
        indicadores = {
            'total_bienes': total_bienes,
            'total_oficinas': queryset.values('oficina').distinct().count(),
            'total_valor': queryset.aggregate(Sum('valor_adquisicion'))['valor_adquisicion__sum'] or 0,
            'valor_promedio': queryset.aggregate(Avg('valor_adquisicion'))['valor_adquisicion__avg'] or 0,
        }
        
        # Distribución por estado
        estados = queryset.values('estado_bien').annotate(
            total=Count('id'),
            porcentaje=Count('id') * 100.0 / total_bienes if total_bienes > 0 else 0
        )
        
        indicadores['distribucion_estados'] = {
            estado['estado_bien']: {
                'total': estado['total'],
                'porcentaje': round(estado['porcentaje'], 2)
            }
            for estado in estados
        }
        
        # Bienes que requieren atención
        bienes_atencion = queryset.filter(estado_bien__in=['M', 'E', 'C']).count()
        indicadores['bienes_requieren_atencion'] = bienes_atencion
        indicadores['porcentaje_atencion'] = round(
            (bienes_atencion * 100.0 / total_bienes) if total_bienes > 0 else 0, 2
        )
        
        # Top 5 oficinas con más bienes
        top_oficinas = list(queryset.values(
            'oficina__nombre', 'oficina__codigo'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:5])
        
        indicadores['top_oficinas'] = top_oficinas
        
        # Tendencias por año (compatible con SQLite)
        tendencias = list(queryset.annotate(
            año=Extract('created_at', 'year')
        ).values('año').annotate(
            total=Count('id')
        ).order_by('año'))
        
        indicadores['tendencias_registro'] = tendencias
        
        return indicadores
    
    @staticmethod
    def generar_alertas_mantenimiento(queryset=None):
        """
        Genera alertas de bienes que requieren mantenimiento
        
        Args:
            queryset: QuerySet de bienes (opcional)
            
        Returns:
            Dict con alertas
        """
        if queryset is None:
            queryset = BienPatrimonial.objects.all()
        
        alertas = {
            'bienes_malo_estado': queryset.filter(estado_bien='M').count(),
            'bienes_raee': queryset.filter(estado_bien='E').count(),
            'bienes_chatarra': queryset.filter(estado_bien='C').count(),
            'sin_valor_adquisicion': queryset.filter(valor_adquisicion__isnull=True).count(),
            'sin_fecha_adquisicion': queryset.filter(fecha_adquisicion__isnull=True).count(),
        }
        
        # Bienes antiguos (más de 10 años)
        fecha_limite = timezone.now().date().replace(year=timezone.now().year - 10)
        alertas['bienes_antiguos'] = queryset.filter(
            fecha_adquisicion__lt=fecha_limite
        ).count()
        
        return alertas


class ValidadorFiltros:
    """Clase para validar configuraciones de filtros"""
    
    @staticmethod
    def validar_configuracion(configuracion):
        """
        Valida una configuración de filtros
        
        Args:
            configuracion: Dict o ConfiguracionFiltro
            
        Returns:
            Tuple (es_valida, errores)
        """
        errores = []
        
        if isinstance(configuracion, ConfiguracionFiltro):
            config_dict = configuracion.to_dict()
        else:
            config_dict = configuracion
        
        # Validar oficinas
        oficinas = config_dict.get('oficinas', [])
        if oficinas:
            oficinas_validas = Oficina.objects.filter(
                id__in=[int(o) for o in oficinas if str(o).isdigit()]
            ).count()
            if oficinas_validas != len(oficinas):
                errores.append("Algunas oficinas seleccionadas no son válidas")
        
        # Validar estados
        estados = config_dict.get('estados_bien', [])
        estados_validos = [estado[0] for estado in BienPatrimonial.ESTADOS_BIEN]
        for estado in estados:
            if estado not in estados_validos:
                errores.append(f"Estado '{estado}' no es válido")
        
        # Validar fechas
        fecha_adq_desde = config_dict.get('fecha_adquisicion_desde')
        fecha_adq_hasta = config_dict.get('fecha_adquisicion_hasta')
        
        if fecha_adq_desde and fecha_adq_hasta and fecha_adq_desde > fecha_adq_hasta:
            errores.append("La fecha de adquisición 'hasta' debe ser mayor o igual a 'desde'")
        
        # Validar valores
        valor_min = config_dict.get('valor_minimo')
        valor_max = config_dict.get('valor_maximo')
        
        if valor_min and valor_max and valor_min > valor_max:
            errores.append("El valor máximo debe ser mayor o igual al valor mínimo")
        
        return len(errores) == 0, errores
    
    @staticmethod
    def optimizar_configuracion(configuracion):
        """
        Optimiza una configuración de filtros eliminando valores vacíos
        
        Args:
            configuracion: Dict con configuración
            
        Returns:
            Dict optimizado
        """
        config_optimizada = {}
        
        for clave, valor in configuracion.items():
            if valor is not None and valor != '' and valor != []:
                config_optimizada[clave] = valor
        
        return config_optimizada


def aplicar_filtros_desde_request(request, queryset=None):
    """
    Aplica filtros desde los parámetros de una request HTTP
    
    Args:
        request: HttpRequest con parámetros de filtro
        queryset: QuerySet base (opcional)
        
    Returns:
        QuerySet filtrado
    """
    parametros = {}
    
    # Extraer parámetros de la request
    if request.GET.get('oficinas'):
        parametros['oficinas'] = request.GET.getlist('oficinas')
    
    if request.GET.get('estados_bien'):
        parametros['estados_bien'] = request.GET.getlist('estados_bien')
    
    if request.GET.get('grupos_catalogo'):
        parametros['grupos_catalogo'] = request.GET.getlist('grupos_catalogo')
    
    if request.GET.get('clases_catalogo'):
        parametros['clases_catalogo'] = request.GET.getlist('clases_catalogo')
    
    # Filtros de texto
    for campo in ['codigo_patrimonial', 'denominacion', 'serie', 'placa']:
        valor = request.GET.get(campo, '').strip()
        if valor:
            parametros[campo] = valor
    
    # Filtros de fechas
    for campo in ['fecha_adquisicion_desde', 'fecha_adquisicion_hasta', 
                  'fecha_registro_desde', 'fecha_registro_hasta']:
        valor = request.GET.get(campo)
        if valor:
            try:
                from datetime import datetime
                parametros[campo] = datetime.strptime(valor, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"Fecha inválida para {campo}: {valor}")
    
    # Filtros de valores
    for campo in ['valor_minimo', 'valor_maximo']:
        valor = request.GET.get(campo)
        if valor:
            try:
                parametros[campo] = float(valor)
            except ValueError:
                logger.warning(f"Valor inválido para {campo}: {valor}")
    
    # Operador lógico
    parametros['operador_principal'] = request.GET.get('operador_principal', 'AND')
    
    # Aplicar filtros
    filtro = FiltroAvanzado(parametros=parametros)
    return filtro.aplicar_filtros(queryset)