# Módulo de Configuración del Sistema

## 📋 Descripción General

Se ha creado un módulo completo de configuración del sistema que permite personalizar diversos aspectos de la aplicación sin necesidad de modificar código.

## 🎯 Características Principales

### 1. **Configuración General del Sistema** (`SystemConfiguration`)

Modelo singleton que almacena la configuración global:

#### Información de la Institución
- Nombre de la institución
- Siglas
- RUC
- Dirección
- Teléfono
- Email
- Logo (imagen)

#### Configuración de Fecha y Hora
- **Formato de Fecha**: 
  - DD/MM/YYYY (31/12/2025)
  - MM/DD/YYYY (12/31/2025)
  - YYYY-MM-DD (2025-12-31)
  - DD-MM-YYYY (31-12-2025)
  - DD.MM.YYYY (31.12.2025)

- **Formato de Fecha y Hora**: Personalizable

- **Zona Horaria**:
  - Lima (UTC-5)
  - Bogotá (UTC-5)
  - Ciudad de México (UTC-6)
  - Buenos Aires (UTC-3)
  - Santiago (UTC-3/UTC-4)
  - Caracas (UTC-4)
  - Nueva York (UTC-5/UTC-4)
  - Madrid (UTC+1/UTC+2)
  - UTC (UTC+0)

#### Configuración de Paginación
- Registros por página en listas

#### Configuración de Códigos
- Longitud del código patrimonial
- Prefijo para códigos patrimoniales

#### Configuración de QR
- Tamaño del código QR (1-20)

#### Configuración de Reportes
- Incluir logo en reportes PDF
- Pie de página personalizado

#### Configuración de Notificaciones
- Habilitar/deshabilitar notificaciones por email
- Días de anticipación para avisos de mantenimiento

#### Configuración de Importación
- Permitir duplicados en denominación

### 2. **Configuración de Campos** (`FieldConfiguration`)

Permite configurar qué campos son visibles y requeridos por módulo:

#### Módulos Soportados
- Bienes Patrimoniales
- Catálogo
- Oficinas
- Reportes

#### Propiedades Configurables
- **Visible**: Si el campo se muestra en formularios y listas
- **Requerido**: Si el campo es obligatorio
- **Orden**: Orden de visualización
- **Etiqueta**: Texto visible para el usuario
- **Ayuda**: Texto de ayuda contextual

### 3. **Estados de Bienes** (`EstadoBienConfiguration`)

Configuración personalizable de estados de bienes patrimoniales:

#### Estados por Defecto
| Código | Nombre | Color | Icono |
|--------|--------|-------|-------|
| N | Nuevo | Verde (#28a745) | fa-star |
| B | Bueno | Azul (#17a2b8) | fa-check-circle |
| R | Regular | Amarillo (#ffc107) | fa-exclamation-circle |
| M | Malo | Rojo (#dc3545) | fa-times-circle |
| E | RAEE | Gris (#6c757d) | fa-recycle |
| C | Chatarra | Negro (#343a40) | fa-trash |

#### Propiedades
- **Código**: Código corto (1-5 caracteres)
- **Nombre**: Nombre completo
- **Descripción**: Descripción detallada
- **Color**: Color hexadecimal para UI
- **Icono**: Clase de icono FontAwesome
- **Activo**: Si está disponible para uso
- **Orden**: Orden de visualización
- **Es Sistema**: Protección contra eliminación

#### Funcionalidades
- Agregar estados personalizados
- Modificar estados existentes (excepto los del sistema)
- Activar/desactivar estados
- Reordenar estados

### 4. **Historial de Configuración** (`ConfigurationHistory`)

Auditoría completa de cambios en la configuración:

#### Información Registrada
- Usuario que realizó el cambio
- Fecha y hora del cambio
- Tipo de configuración modificada
- Campo modificado
- Valor anterior
- Valor nuevo
- Dirección IP

## 📁 Estructura de Archivos

```
apps/core/
├── models_config.py          # Modelos de configuración
├── forms_config.py           # Formularios de configuración
├── views_config.py           # Vistas de configuración
└── management/commands/
    └── init_config.py        # Comando para inicializar configuración

templates/core/
├── configuracion/
│   ├── sistema.html          # Configuración general
│   ├── campos.html           # Configuración de campos
│   ├── estados.html          # Configuración de estados
│   └── historial.html        # Historial de cambios
```

## 🚀 Uso del Sistema

### Acceso a la Configuración

```python
from apps.core.models_config import SystemConfiguration

# Obtener configuración
config = SystemConfiguration.get_config()

# Usar configuración
formato_fecha = config.formato_fecha
zona_horaria = config.zona_horaria
registros_por_pagina = config.registros_por_pagina
```

### Configuración de Campos

```python
from apps.core.models_config import FieldConfiguration

# Obtener campos visibles de un módulo
campos_bienes = FieldConfiguration.objects.filter(
    modulo='bienes',
    visible=True
).order_by('orden')

# Verificar si un campo es requerido
campo = FieldConfiguration.objects.get(
    modulo='bienes',
    campo_nombre='marca'
)
if campo.requerido:
    # Campo obligatorio
    pass
```

### Estados de Bienes

```python
from apps.core.models_config import EstadoBienConfiguration

# Obtener estados activos
estados = EstadoBienConfiguration.get_estados_activos()

# Obtener choices para formularios
choices = EstadoBienConfiguration.get_choices()

# Inicializar estados por defecto
EstadoBienConfiguration.inicializar_estados_default()
```

### Registrar Cambios

```python
from apps.core.models_config import ConfigurationHistory

# Registrar cambio
ConfigurationHistory.registrar_cambio(
    usuario=request.user,
    tipo_config='SystemConfiguration',
    campo='formato_fecha',
    valor_anterior='%d/%m/%Y',
    valor_nuevo='%Y-%m-%d',
    ip=request.META.get('REMOTE_ADDR')
)
```

## 🔧 Comando de Inicialización

```bash
# Inicializar configuración por defecto
python manage.py init_config

# Reinicializar (sobrescribir)
python manage.py init_config --force
```

## 📊 Admin de Django

Todos los modelos están registrados en el admin con interfaces personalizadas:

### SystemConfiguration Admin
- Formulario organizado en secciones
- Vista previa de formatos de fecha
- Validaciones personalizadas
- Solo un registro (singleton)

### FieldConfiguration Admin
- Filtros por módulo
- Búsqueda por nombre y etiqueta
- Acciones en lote (activar/desactivar)
- Ordenamiento drag-and-drop

### EstadoBienConfiguration Admin
- Vista con colores e iconos
- Protección de estados del sistema
- Ordenamiento personalizado
- Previsualización de colores

### ConfigurationHistory Admin
- Solo lectura
- Filtros por tipo y fecha
- Búsqueda por campo y usuario
- Exportación de historial

## 🎨 Integración con Templates

### Template Tag para Configuración

```python
# apps/core/templatetags/config_tags.py
from django import template
from apps.core.models_config import SystemConfiguration

register = template.Library()

@register.simple_tag
def get_config():
    return SystemConfiguration.get_config()

@register.filter
def format_date_config(date_value):
    config = SystemConfiguration.get_config()
    return date_value.strftime(config.formato_fecha)
```

### Uso en Templates

```django
{% load config_tags %}

{% get_config as config %}

<h1>{{ config.institucion_nombre }}</h1>
<p>{{ config.institucion_direccion }}</p>

<!-- Formatear fecha según configuración -->
{{ bien.created_at|format_date_config }}
```

## 🔐 Permisos

### Permisos Personalizados

```python
class Meta:
    permissions = [
        ("view_system_configuration", "Puede ver configuración del sistema"),
        ("change_system_configuration", "Puede modificar configuración del sistema"),
        ("view_field_configuration", "Puede ver configuración de campos"),
        ("change_field_configuration", "Puede modificar configuración de campos"),
        ("view_estado_configuration", "Puede ver configuración de estados"),
        ("change_estado_configuration", "Puede modificar configuración de estados"),
    ]
```

### Decoradores de Vista

```python
from django.contrib.auth.decorators import permission_required

@permission_required('core.change_system_configuration')
def configuracion_sistema(request):
    # Vista protegida
    pass
```

## 📱 API REST (Opcional)

```python
# apps/core/api_config.py
from rest_framework import viewsets
from .models_config import SystemConfiguration, EstadoBienConfiguration
from .serializers_config import SystemConfigSerializer, EstadoBienSerializer

class SystemConfigViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigSerializer
    
    def get_object(self):
        return SystemConfiguration.get_config()

class EstadoBienViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EstadoBienConfiguration.get_estados_activos()
    serializer_class = EstadoBienSerializer
```

## 🧪 Tests

```python
# tests/test_configuration.py
from django.test import TestCase
from apps.core.models_config import (
    SystemConfiguration,
    FieldConfiguration,
    EstadoBienConfiguration
)

class SystemConfigurationTest(TestCase):
    def test_singleton_pattern(self):
        """Test que solo existe un registro de configuración"""
        config1 = SystemConfiguration.get_config()
        config2 = SystemConfiguration.get_config()
        self.assertEqual(config1.pk, config2.pk)
    
    def test_formato_fecha(self):
        """Test de formato de fecha"""
        config = SystemConfiguration.get_config()
        config.formato_fecha = '%d/%m/%Y'
        config.save()
        
        ejemplo = config.get_formato_fecha_display_example()
        self.assertRegex(ejemplo, r'\d{2}/\d{2}/\d{4}')

class EstadoBienConfigurationTest(TestCase):
    def test_inicializar_estados(self):
        """Test de inicialización de estados"""
        EstadoBienConfiguration.inicializar_estados_default()
        
        estados = EstadoBienConfiguration.objects.all()
        self.assertEqual(estados.count(), 6)
        
        # Verificar que existen los estados básicos
        self.assertTrue(estados.filter(codigo='N').exists())
        self.assertTrue(estados.filter(codigo='B').exists())
    
    def test_no_eliminar_estado_sistema(self):
        """Test que no se pueden eliminar estados del sistema"""
        estado = EstadoBienConfiguration.objects.get(codigo='N')
        
        with self.assertRaises(ValidationError):
            estado.delete()
```

## 📖 Casos de Uso

### Caso 1: Cambiar Formato de Fecha

```python
# Vista
def cambiar_formato_fecha(request):
    config = SystemConfiguration.get_config()
    
    if request.method == 'POST':
        formato_anterior = config.formato_fecha
        config.formato_fecha = request.POST.get('formato_fecha')
        config.actualizado_por = request.user
        config.save()
        
        # Registrar cambio
        ConfigurationHistory.registrar_cambio(
            usuario=request.user,
            tipo_config='SystemConfiguration',
            campo='formato_fecha',
            valor_anterior=formato_anterior,
            valor_nuevo=config.formato_fecha,
            ip=request.META.get('REMOTE_ADDR')
        )
        
        messages.success(request, 'Formato de fecha actualizado')
    
    return render(request, 'config/formato_fecha.html', {'config': config})
```

### Caso 2: Agregar Estado Personalizado

```python
# Vista
def agregar_estado_bien(request):
    if request.method == 'POST':
        EstadoBienConfiguration.objects.create(
            codigo=request.POST.get('codigo'),
            nombre=request.POST.get('nombre'),
            descripcion=request.POST.get('descripcion'),
            color=request.POST.get('color'),
            icono=request.POST.get('icono'),
            orden=EstadoBienConfiguration.objects.count() + 1
        )
        
        messages.success(request, 'Estado agregado correctamente')
        return redirect('config:estados')
    
    return render(request, 'config/agregar_estado.html')
```

### Caso 3: Configurar Campos Visibles

```python
# Vista
def configurar_campos_bienes(request):
    campos = FieldConfiguration.objects.filter(modulo='bienes')
    
    if request.method == 'POST':
        for campo in campos:
            campo.visible = f'visible_{campo.id}' in request.POST
            campo.requerido = f'requerido_{campo.id}' in request.POST
            campo.save()
        
        messages.success(request, 'Configuración de campos actualizada')
    
    return render(request, 'config/campos_bienes.html', {'campos': campos})
```

## 🔄 Migración

```bash
# Crear migración
python manage.py makemigrations

# Aplicar migración
python manage.py migrate

# Inicializar configuración
python manage.py init_config
```

## 📝 Notas Importantes

1. **Singleton Pattern**: `SystemConfiguration` usa el patrón singleton (pk=1 siempre)
2. **Estados del Sistema**: Los estados marcados como `es_sistema=True` no se pueden eliminar
3. **Historial Automático**: Todos los cambios se registran automáticamente
4. **Caché**: Considerar implementar caché para `SystemConfiguration.get_config()`
5. **Validaciones**: Implementar validaciones personalizadas según necesidades

## 🎯 Próximos Pasos

1. Crear vistas y formularios completos
2. Implementar interfaz de usuario amigable
3. Agregar más opciones de configuración según necesidades
4. Implementar sistema de caché
5. Crear documentación de usuario final
6. Agregar más validaciones
7. Implementar importación/exportación de configuración

## ✅ Beneficios

- ✅ Configuración centralizada
- ✅ Sin necesidad de modificar código
- ✅ Auditoría completa de cambios
- ✅ Interfaz amigable en admin
- ✅ Extensible y personalizable
- ✅ Historial de cambios
- ✅ Validaciones automáticas
- ✅ Fácil de usar

---

**Fecha de Creación:** 2025-01-09  
**Versión:** 1.0  
**Estado:** ✅ Modelos Creados - Pendiente Vistas y Templates
