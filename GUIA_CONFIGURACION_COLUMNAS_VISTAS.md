# 📊 Guía de Configuración de Columnas en Vistas

## 🎯 Dónde se Configuran las Columnas

Las columnas que se muestran en las listas/tablas se configuran en varios lugares:

---

## 1. 🔧 Admin de Django

**Archivo**: `apps/bienes/admin.py`

### Ver Configuración Actual

```python
@admin.register(BienPatrimonial)
class BienPatrimonialAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_patrimonial',
        'catalogo',
        'oficina',
        'estado_bien',
        'marca',
        'modelo',
        'serie'
    ]
    # ↑ Estas son las columnas que se muestran en el admin
```

### Agregar/Quitar Columnas

```python
list_display = [
    'codigo_patrimonial',  # Columna 1
    'catalogo',            # Columna 2
    'oficina',             # Columna 3
    'estado_bien',         # Columna 4
    'marca',               # Columna 5
    'modelo',              # Columna 6
    'serie',               # Columna 7
    'valor_adquisicion',   # ← AGREGAR nueva columna
    'fecha_adquisicion',   # ← AGREGAR nueva columna
]
```

### Columnas con Métodos Personalizados

```python
@admin.register(BienPatrimonial)
class BienPatrimonialAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_patrimonial',
        'get_denominacion',      # ← Método personalizado
        'get_ubicacion',         # ← Método personalizado
        'estado_bien_display',   # ← Método personalizado
    ]
    
    def get_denominacion(self, obj):
        return obj.catalogo.denominacion
    get_denominacion.short_description = 'Denominación'
    
    def get_ubicacion(self, obj):
        return obj.oficina.nombre
    get_ubicacion.short_description = 'Ubicación'
    
    def estado_bien_display(self, obj):
        return obj.get_estado_bien_display()
    estado_bien_display.short_description = 'Estado'
```

---

## 2. 📋 Vistas de Lista (Templates)

**Archivo**: `templates/bienes/list.html`

### Configurar Columnas en la Tabla

```html
<table class="table">
    <thead>
        <tr>
            <th>Código</th>
            <th>Denominación</th>
            <th>Oficina</th>
            <th>Estado</th>
            <th>Marca</th>
            <th>Modelo</th>
            <th>Acciones</th>
        </tr>
    </thead>
    <tbody>
        {% for bien in bienes %}
        <tr>
            <td>{{ bien.codigo_patrimonial }}</td>
            <td>{{ bien.catalogo.denominacion }}</td>
            <td>{{ bien.oficina.nombre }}</td>
            <td>{{ bien.get_estado_bien_display }}</td>
            <td>{{ bien.marca }}</td>
            <td>{{ bien.modelo }}</td>
            <td>
                <a href="{% url 'bienes:detail' bien.pk %}">Ver</a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Agregar Nueva Columna

```html
<thead>
    <tr>
        <th>Código</th>
        <th>Denominación</th>
        <th>Oficina</th>
        <th>Estado</th>
        <th>Valor</th>  <!-- ← NUEVA COLUMNA -->
        <th>Acciones</th>
    </tr>
</thead>
<tbody>
    {% for bien in bienes %}
    <tr>
        <td>{{ bien.codigo_patrimonial }}</td>
        <td>{{ bien.catalogo.denominacion }}</td>
        <td>{{ bien.oficina.nombre }}</td>
        <td>{{ bien.get_estado_bien_display }}</td>
        <td>S/ {{ bien.valor_adquisicion|floatformat:2 }}</td>  <!-- ← NUEVA COLUMNA -->
        <td>
            <a href="{% url 'bienes:detail' bien.pk %}">Ver</a>
        </td>
    </tr>
    {% endfor %}
</tbody>
```

---

## 3. 📊 Reportes y Exportaciones

**Archivo**: `apps/reportes/generadores.py`

### Configurar Columnas en Excel

```python
def generar_reporte_bienes(self, bienes):
    # Definir columnas
    columnas = [
        'Código Patrimonial',
        'Denominación',
        'Oficina',
        'Estado',
        'Marca',
        'Modelo',
        'Serie',
        'Valor',  # ← AGREGAR
    ]
    
    # Agregar datos
    for bien in bienes:
        fila = [
            bien.codigo_patrimonial,
            bien.catalogo.denominacion,
            bien.oficina.nombre,
            bien.get_estado_bien_display(),
            bien.marca,
            bien.modelo,
            bien.serie,
            bien.valor_adquisicion,  # ← AGREGAR
        ]
        worksheet.append(fila)
```

---

## 4. 🔍 Filtros y Búsqueda

**Archivo**: `apps/bienes/admin.py`

### Configurar Campos de Búsqueda

```python
@admin.register(BienPatrimonial)
class BienPatrimonialAdmin(admin.ModelAdmin):
    search_fields = [
        'codigo_patrimonial',
        'codigo_interno',
        'marca',
        'modelo',
        'serie',
        'placa',
        'catalogo__denominacion',  # Buscar en catálogo
        'oficina__nombre',         # Buscar en oficina
    ]
```

### Configurar Filtros Laterales

```python
@admin.register(BienPatrimonial)
class BienPatrimonialAdmin(admin.ModelAdmin):
    list_filter = [
        'estado_bien',
        'oficina',
        'catalogo__grupo',
        'fecha_adquisicion',
    ]
```

---

## 5. 📱 API REST (si usas)

**Archivo**: `apps/bienes/serializers.py`

### Configurar Campos en API

```python
class BienPatrimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = BienPatrimonial
        fields = [
            'id',
            'codigo_patrimonial',
            'catalogo',
            'oficina',
            'estado_bien',
            'marca',
            'modelo',
            'serie',
            'valor_adquisicion',  # ← AGREGAR
        ]
```

---

## 6. 🎨 Columnas Responsivas

### Ocultar Columnas en Móvil

```html
<table class="table">
    <thead>
        <tr>
            <th>Código</th>
            <th>Denominación</th>
            <th class="d-none d-md-table-cell">Marca</th>  <!-- Oculto en móvil -->
            <th class="d-none d-lg-table-cell">Modelo</th> <!-- Oculto en tablet -->
            <th>Acciones</th>
        </tr>
    </thead>
    <tbody>
        {% for bien in bienes %}
        <tr>
            <td>{{ bien.codigo_patrimonial }}</td>
            <td>{{ bien.catalogo.denominacion }}</td>
            <td class="d-none d-md-table-cell">{{ bien.marca }}</td>
            <td class="d-none d-lg-table-cell">{{ bien.modelo }}</td>
            <td>
                <a href="{% url 'bienes:detail' bien.pk %}">Ver</a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

**Clases Bootstrap**:
- `d-none` - Oculto por defecto
- `d-md-table-cell` - Visible en tablet y desktop
- `d-lg-table-cell` - Visible solo en desktop

---

## 7. 📊 Ejemplo Completo: Agregar Columna "Valor"

### Paso 1: Admin (`apps/bienes/admin.py`)

```python
list_display = [
    'codigo_patrimonial',
    'catalogo',
    'oficina',
    'estado_bien',
    'marca',
    'modelo',
    'get_valor_formateado',  # ← AGREGAR
]

def get_valor_formateado(self, obj):
    if obj.valor_adquisicion:
        return f"S/ {obj.valor_adquisicion:,.2f}"
    return "-"
get_valor_formateado.short_description = 'Valor'
get_valor_formateado.admin_order_field = 'valor_adquisicion'
```

### Paso 2: Template (`templates/bienes/list.html`)

```html
<thead>
    <tr>
        <th>Código</th>
        <th>Denominación</th>
        <th>Oficina</th>
        <th>Valor</th>  <!-- ← AGREGAR -->
        <th>Acciones</th>
    </tr>
</thead>
<tbody>
    {% for bien in bienes %}
    <tr>
        <td>{{ bien.codigo_patrimonial }}</td>
        <td>{{ bien.catalogo.denominacion }}</td>
        <td>{{ bien.oficina.nombre }}</td>
        <td>
            {% if bien.valor_adquisicion %}
                S/ {{ bien.valor_adquisicion|floatformat:2 }}
            {% else %}
                -
            {% endif %}
        </td>  <!-- ← AGREGAR -->
        <td>
            <a href="{% url 'bienes:detail' bien.pk %}">Ver</a>
        </td>
    </tr>
    {% endfor %}
</tbody>
```

### Paso 3: Reporte (`apps/reportes/generadores.py`)

```python
columnas = [
    'Código',
    'Denominación',
    'Oficina',
    'Valor',  # ← AGREGAR
]

for bien in bienes:
    fila = [
        bien.codigo_patrimonial,
        bien.catalogo.denominacion,
        bien.oficina.nombre,
        bien.valor_adquisicion or 0,  # ← AGREGAR
    ]
```

---

## 8. 🎯 Columnas Recomendadas

### Vista de Lista (Mínimo)
- ✅ Código Patrimonial
- ✅ Denominación
- ✅ Oficina
- ✅ Estado
- ✅ Acciones

### Vista de Lista (Completa)
- ✅ Código Patrimonial
- ✅ Código Interno
- ✅ Denominación
- ✅ Oficina
- ✅ Estado
- ✅ Marca
- ✅ Modelo
- ✅ Serie
- ✅ Valor
- ✅ Fecha Adquisición
- ✅ Acciones

### Vista de Reporte
- ✅ Todas las columnas disponibles
- ✅ Información de catálogo completa
- ✅ Información de oficina completa
- ✅ Fechas de auditoría

---

## 9. 📞 Comandos Útiles

### Ver Campos Disponibles

```bash
docker-compose exec web python manage.py shell
```

```python
from apps.bienes.models import BienPatrimonial

# Ver todos los campos
for field in BienPatrimonial._meta.fields:
    print(f"- {field.name}: {field.verbose_name}")
```

### Ver Configuración del Admin

```bash
docker-compose exec web python manage.py shell
```

```python
from apps.bienes.admin import BienPatrimonialAdmin

# Ver columnas configuradas
print(BienPatrimonialAdmin.list_display)

# Ver filtros configurados
print(BienPatrimonialAdmin.list_filter)

# Ver campos de búsqueda
print(BienPatrimonialAdmin.search_fields)
```

---

## 10. 🎨 Personalización Avanzada

### Columnas con Iconos

```python
def estado_con_icono(self, obj):
    iconos = {
        'N': '🟢',
        'B': '🔵',
        'R': '🟡',
        'M': '🔴',
    }
    icono = iconos.get(obj.estado_bien, '⚪')
    return f"{icono} {obj.get_estado_bien_display()}"
estado_con_icono.short_description = 'Estado'
```

### Columnas con Enlaces

```python
def ver_detalle(self, obj):
    from django.utils.html import format_html
    url = reverse('admin:bienes_bienpatrimonial_change', args=[obj.pk])
    return format_html('<a href="{}">Ver Detalle</a>', url)
ver_detalle.short_description = 'Acciones'
```

### Columnas con Colores

```python
def valor_con_color(self, obj):
    from django.utils.html import format_html
    if obj.valor_adquisicion:
        if obj.valor_adquisicion > 5000:
            color = 'red'
        elif obj.valor_adquisicion > 1000:
            color = 'orange'
        else:
            color = 'green'
        return format_html(
            '<span style="color: {};">S/ {:,.2f}</span>',
            color,
            obj.valor_adquisicion
        )
    return '-'
valor_con_color.short_description = 'Valor'
```

---

## 11. 📚 Archivos Relacionados

- **Admin**: `apps/bienes/admin.py`
- **Templates**: `templates/bienes/list.html`
- **Vistas**: `apps/bienes/views.py`
- **Reportes**: `apps/reportes/generadores.py`
- **Formularios**: `apps/bienes/forms.py`

---

## 12. ✅ Checklist de Configuración

- [ ] Configurar columnas en Admin
- [ ] Configurar columnas en Template
- [ ] Configurar columnas en Reportes
- [ ] Configurar filtros de búsqueda
- [ ] Configurar filtros laterales
- [ ] Hacer columnas responsivas
- [ ] Agregar iconos/colores si es necesario
- [ ] Probar en diferentes dispositivos

---

**Fecha**: 11/11/2025  
**Versión**: 1.0.0  
**Estado**: ✅ DOCUMENTADO
