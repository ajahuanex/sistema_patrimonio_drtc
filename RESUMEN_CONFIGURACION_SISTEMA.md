# 📋 Resumen: Configuración del Sistema

## 🎯 Respuestas a tus 3 Preguntas

---

## 1. 🗑️ ¿Los Datos de Ejemplo se van a Borrar?

### Respuesta: NO, se quedan hasta que los borres manualmente

### ✅ Cómo Borrar Datos de Prueba

#### Opción A: Comando Rápido (Recomendado)

```bash
# Ver advertencia
docker-compose exec web python manage.py limpiar_datos_prueba

# Confirmar y eliminar
docker-compose exec web python manage.py limpiar_datos_prueba --confirmar
```

#### Opción B: Desde el Shell

```bash
docker-compose exec web python manage.py shell
```

```python
from apps.bienes.models import BienPatrimonial

# Borrar solo los de prueba (BP2025XXXXXX)
BienPatrimonial.objects.filter(
    codigo_patrimonial__startswith='BP2025'
).delete()

# O borrar TODOS
BienPatrimonial.objects.all().delete()
```

#### Opción C: Desde el Admin

1. Ve a http://localhost:8000/admin
2. Entra a "Bienes Patrimoniales"
3. Selecciona los bienes de prueba
4. Acción: "Eliminar elementos seleccionados"

---

## 2. 📋 ¿Dónde Configurar Campos Obligatorios?

### Respuesta: En el archivo `apps/bienes/models.py`

### 🔴 Campo OBLIGATORIO

```python
# SIN blank=True = OBLIGATORIO
marca = models.CharField(
    max_length=100,
    verbose_name='Marca'
)
```

### ⚪ Campo OPCIONAL

```python
# CON blank=True = OPCIONAL
marca = models.CharField(
    max_length=100,
    blank=True,  # ← Esto lo hace opcional
    verbose_name='Marca'
)
```

### 🔧 Pasos para Cambiar

1. **Editar** `apps/bienes/models.py`
2. **Agregar o quitar** `blank=True`
3. **Crear migración**: `docker-compose exec web python manage.py makemigrations`
4. **Aplicar migración**: `docker-compose exec web python manage.py migrate`

### 📊 Campos Actualmente Obligatorios

- ✅ `codigo_patrimonial`
- ✅ `catalogo`
- ✅ `oficina`
- ✅ `estado_bien` (con default='B')

### 📊 Campos Actualmente Opcionales

- ⚪ `marca`, `modelo`, `color`, `serie`
- ⚪ `placa`, `matricula`, `nro_motor`, `nro_chasis`
- ⚪ `fecha_adquisicion`, `valor_adquisicion`
- ⚪ `observaciones`

---

## 3. 📊 ¿Dónde Configurar Columnas en las Vistas?

### Respuesta: Depende de dónde quieras mostrarlas

### 🔧 Admin de Django

**Archivo**: `apps/bienes/admin.py`

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
        'serie',
        # Agregar más columnas aquí
    ]
```

### 📋 Templates (Vistas HTML)

**Archivo**: `templates/bienes/list.html`

```html
<table>
    <thead>
        <tr>
            <th>Código</th>
            <th>Denominación</th>
            <th>Oficina</th>
            <!-- Agregar más columnas aquí -->
        </tr>
    </thead>
    <tbody>
        {% for bien in bienes %}
        <tr>
            <td>{{ bien.codigo_patrimonial }}</td>
            <td>{{ bien.catalogo.denominacion }}</td>
            <td>{{ bien.oficina.nombre }}</td>
            <!-- Agregar más columnas aquí -->
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### 📊 Reportes Excel

**Archivo**: `apps/reportes/generadores.py`

```python
columnas = [
    'Código',
    'Denominación',
    'Oficina',
    # Agregar más columnas aquí
]
```

---

## 📚 Documentación Creada

He creado 3 guías completas para ti:

### 1. 🗑️ Limpieza de Datos
- **Archivo**: `apps/core/management/commands/limpiar_datos_prueba.py`
- **Comando**: `python manage.py limpiar_datos_prueba --confirmar`

### 2. 📋 Configuración de Campos
- **Guía**: `GUIA_CONFIGURACION_CAMPOS.md`
- **Archivo a editar**: `apps/bienes/models.py`

### 3. 📊 Configuración de Columnas
- **Guía**: `GUIA_CONFIGURACION_COLUMNAS_VISTAS.md`
- **Archivos a editar**: 
  - `apps/bienes/admin.py`
  - `templates/bienes/list.html`
  - `apps/reportes/generadores.py`

---

## 🎯 Acciones Rápidas

### Borrar Datos de Prueba

```bash
docker-compose exec web python manage.py limpiar_datos_prueba --confirmar
```

### Ver Campos del Modelo

```bash
docker-compose exec web python manage.py shell
```

```python
from apps.bienes.models import BienPatrimonial

for field in BienPatrimonial._meta.fields:
    obligatorio = "OBLIGATORIO" if not field.blank else "OPCIONAL"
    print(f"{field.name}: {obligatorio}")
```

### Ver Columnas del Admin

```bash
docker-compose exec web python manage.py shell
```

```python
from apps.bienes.admin import BienPatrimonialAdmin

print("Columnas:", BienPatrimonialAdmin.list_display)
print("Filtros:", BienPatrimonialAdmin.list_filter)
print("Búsqueda:", BienPatrimonialAdmin.search_fields)
```

---

## 📖 Guías Completas

1. **Limpieza de Datos**: Lee este documento (arriba)
2. **Campos Obligatorios**: Lee `GUIA_CONFIGURACION_CAMPOS.md`
3. **Columnas en Vistas**: Lee `GUIA_CONFIGURACION_COLUMNAS_VISTAS.md`

---

## ✅ Checklist de Configuración

### Datos de Prueba
- [ ] Decidir si borrar o mantener datos de prueba
- [ ] Si borrar: ejecutar comando de limpieza
- [ ] Verificar que se borraron correctamente

### Campos Obligatorios
- [ ] Revisar qué campos deben ser obligatorios
- [ ] Editar `apps/bienes/models.py`
- [ ] Crear y aplicar migraciones
- [ ] Probar en formularios

### Columnas en Vistas
- [ ] Decidir qué columnas mostrar
- [ ] Configurar en Admin
- [ ] Configurar en Templates
- [ ] Configurar en Reportes
- [ ] Probar en diferentes dispositivos

---

## 🎨 Ejemplo Completo

### Hacer "Marca" Obligatoria y Mostrarla

#### 1. Editar Modelo (`apps/bienes/models.py`)

```python
marca = models.CharField(
    max_length=100,
    # blank=True,  ← ELIMINAR esta línea
    verbose_name='Marca'
)
```

#### 2. Crear Migración

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

#### 3. Agregar a Admin (`apps/bienes/admin.py`)

```python
list_display = [
    'codigo_patrimonial',
    'catalogo',
    'marca',  # ← Ya está, pero asegúrate
    # ...
]
```

#### 4. Agregar a Template (`templates/bienes/list.html`)

```html
<th>Marca</th>  <!-- En thead -->
<td>{{ bien.marca }}</td>  <!-- En tbody -->
```

---

## 📞 Comandos de Referencia

```bash
# Borrar datos de prueba
docker-compose exec web python manage.py limpiar_datos_prueba --confirmar

# Ver modelo
docker-compose exec web python manage.py inspectdb BienPatrimonial

# Crear migración
docker-compose exec web python manage.py makemigrations

# Aplicar migración
docker-compose exec web python manage.py migrate

# Shell interactivo
docker-compose exec web python manage.py shell

# Ver admin
http://localhost:8000/admin
```

---

## 🎉 Resumen Final

### ✅ Datos de Prueba
- NO se borran automáticamente
- Usa el comando `limpiar_datos_prueba --confirmar`

### ✅ Campos Obligatorios
- Se configuran en `apps/bienes/models.py`
- Quitar `blank=True` = Obligatorio
- Agregar `blank=True` = Opcional

### ✅ Columnas en Vistas
- Admin: `apps/bienes/admin.py` → `list_display`
- Templates: `templates/bienes/list.html` → `<th>` y `<td>`
- Reportes: `apps/reportes/generadores.py` → `columnas`

---

**Fecha**: 11/11/2025  
**Versión**: 1.0.0  
**Estado**: ✅ DOCUMENTADO COMPLETAMENTE
