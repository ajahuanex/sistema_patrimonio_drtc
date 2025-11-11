# 📋 Guía de Configuración de Campos

## 🎯 Cómo Configurar Campos Obligatorios y Opcionales

### 📍 Ubicación

Los campos se configuran en: **`apps/bienes/models.py`**

---

## 1. 🔴 Campos OBLIGATORIOS

Un campo es **obligatorio** cuando NO tiene `blank=True` ni `null=True`.

### Ejemplo de Campo Obligatorio:

```python
codigo_patrimonial = models.CharField(
    max_length=50, 
    unique=True,                    # ← Debe ser único
    verbose_name='Código Patrimonial',
    help_text='Código único del bien patrimonial'
)
# ← NO tiene blank=True, por lo tanto es OBLIGATORIO
```

### Campos Actualmente Obligatorios:

1. ✅ `codigo_patrimonial` - Código único del bien
2. ✅ `catalogo` - Catálogo SBN (ForeignKey)
3. ✅ `oficina` - Oficina asignada (ForeignKey)
4. ✅ `estado_bien` - Estado del bien (tiene default='B')

---

## 2. ⚪ Campos OPCIONALES

Un campo es **opcional** cuando tiene `blank=True`.

### Ejemplo de Campo Opcional:

```python
marca = models.CharField(
    max_length=100, 
    blank=True,                     # ← Puede estar vacío
    verbose_name='Marca',
    help_text='Marca del bien'
)
```

### Campos Actualmente Opcionales:

1. ⚪ `codigo_interno`
2. ⚪ `marca`
3. ⚪ `modelo`
4. ⚪ `color`
5. ⚪ `serie`
6. ⚪ `dimension`
7. ⚪ `placa`
8. ⚪ `matricula`
9. ⚪ `nro_motor`
10. ⚪ `nro_chasis`
11. ⚪ `observaciones`
12. ⚪ `fecha_adquisicion`
13. ⚪ `valor_adquisicion`

---

## 3. 🔧 Cómo Hacer un Campo Obligatorio

### Paso 1: Editar el Modelo

Abre: `apps/bienes/models.py`

**Antes** (opcional):
```python
marca = models.CharField(
    max_length=100, 
    blank=True,        # ← Quitar esta línea
    verbose_name='Marca'
)
```

**Después** (obligatorio):
```python
marca = models.CharField(
    max_length=100, 
    # blank=True eliminado
    verbose_name='Marca'
)
```

### Paso 2: Crear Migración

```bash
docker-compose exec web python manage.py makemigrations
```

### Paso 3: Aplicar Migración

```bash
docker-compose exec web python manage.py migrate
```

---

## 4. 🔧 Cómo Hacer un Campo Opcional

### Paso 1: Editar el Modelo

**Antes** (obligatorio):
```python
codigo_interno = models.CharField(
    max_length=50,
    verbose_name='Código Interno'
)
```

**Después** (opcional):
```python
codigo_interno = models.CharField(
    max_length=50,
    blank=True,        # ← Agregar esta línea
    verbose_name='Código Interno'
)
```

### Paso 2: Crear y Aplicar Migración

```bash
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```

---

## 5. 📊 Tipos de Campos

### CharField (Texto corto)
```python
marca = models.CharField(
    max_length=100,      # Longitud máxima
    blank=True,          # Opcional
    verbose_name='Marca'
)
```

### TextField (Texto largo)
```python
observaciones = models.TextField(
    blank=True,
    verbose_name='Observaciones'
)
```

### DateField (Fecha)
```python
fecha_adquisicion = models.DateField(
    null=True,           # Permite NULL en BD
    blank=True,          # Permite vacío en formulario
    verbose_name='Fecha de Adquisición'
)
```

### DecimalField (Números con decimales)
```python
valor_adquisicion = models.DecimalField(
    max_digits=12,       # Total de dígitos
    decimal_places=2,    # Decimales
    null=True,
    blank=True,
    verbose_name='Valor de Adquisición'
)
```

### ForeignKey (Relación)
```python
catalogo = models.ForeignKey(
    Catalogo,
    on_delete=models.PROTECT,  # No permite borrar si hay bienes
    verbose_name='Catálogo'
)
# Sin blank=True = OBLIGATORIO
```

---

## 6. 🎨 Configuración de Formularios

Los formularios también se pueden configurar en: **`apps/bienes/forms.py`**

```python
class BienPatrimonialForm(forms.ModelForm):
    class Meta:
        model = BienPatrimonial
        fields = '__all__'  # Todos los campos
        
        # Campos obligatorios en el formulario
        required = ['codigo_patrimonial', 'catalogo', 'oficina']
        
        # Widgets personalizados
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}),
        }
```

---

## 7. 📝 Ejemplo Completo: Hacer "Marca" Obligatoria

### Paso 1: Editar `apps/bienes/models.py`

Busca la línea:
```python
marca = models.CharField(
    max_length=100, 
    blank=True,  # ← ELIMINAR ESTA LÍNEA
    verbose_name='Marca',
    help_text='Marca del bien'
)
```

Cambia a:
```python
marca = models.CharField(
    max_length=100, 
    verbose_name='Marca',
    help_text='Marca del bien'
)
```

### Paso 2: Crear Migración

```bash
docker-compose exec web python manage.py makemigrations
```

Te preguntará qué hacer con los registros existentes que no tienen marca:
- Opción 1: Proporcionar un valor por defecto (ej: "SIN MARCA")
- Opción 2: Cancelar y agregar valores manualmente

### Paso 3: Aplicar Migración

```bash
docker-compose exec web python manage.py migrate
```

---

## 8. ⚠️ Consideraciones Importantes

### Antes de Hacer un Campo Obligatorio:

1. **Verifica datos existentes**:
   ```bash
   docker-compose exec web python manage.py shell
   ```
   ```python
   from apps.bienes.models import BienPatrimonial
   
   # Ver cuántos bienes NO tienen marca
   sin_marca = BienPatrimonial.objects.filter(marca='').count()
   print(f"Bienes sin marca: {sin_marca}")
   ```

2. **Actualiza datos existentes** (si es necesario):
   ```python
   # Poner "SIN MARCA" a los que no tienen
   BienPatrimonial.objects.filter(marca='').update(marca='SIN MARCA')
   ```

3. **Luego haz el campo obligatorio**

---

## 9. 📋 Resumen de Parámetros

| Parámetro | Significado | Ejemplo |
|-----------|-------------|---------|
| `blank=True` | Puede estar vacío en formularios | Campo opcional |
| `null=True` | Puede ser NULL en base de datos | Para fechas, números |
| `default='X'` | Valor por defecto | `default='B'` |
| `unique=True` | Debe ser único | Código patrimonial |
| `max_length=50` | Longitud máxima | Para CharField |
| `choices=LISTA` | Lista de opciones | Estados del bien |

---

## 10. 🔍 Ver Configuración Actual

Para ver qué campos son obligatorios:

```bash
docker-compose exec web python manage.py shell
```

```python
from apps.bienes.models import BienPatrimonial

# Ver todos los campos
for field in BienPatrimonial._meta.fields:
    es_obligatorio = not field.blank and not field.null
    tipo = "OBLIGATORIO" if es_obligatorio else "OPCIONAL"
    print(f"{field.name}: {tipo}")
```

---

## 11. 📞 Comandos Útiles

```bash
# Ver modelo actual
docker-compose exec web python manage.py inspectdb BienPatrimonial

# Crear migración
docker-compose exec web python manage.py makemigrations

# Ver SQL de migración
docker-compose exec web python manage.py sqlmigrate bienes 0001

# Aplicar migración
docker-compose exec web python manage.py migrate

# Revertir migración
docker-compose exec web python manage.py migrate bienes 0001
```

---

## 12. 🎯 Recomendaciones

### Campos que DEBERÍAN ser Obligatorios:
- ✅ `codigo_patrimonial` (ya lo es)
- ✅ `catalogo` (ya lo es)
- ✅ `oficina` (ya lo es)
- ⚠️ `estado_bien` (ya lo es, con default)

### Campos que PUEDEN ser Opcionales:
- ⚪ `marca` - No todos los bienes tienen marca
- ⚪ `modelo` - No siempre se conoce
- ⚪ `serie` - No todos tienen
- ⚪ `placa` - Solo para vehículos
- ⚪ `valor_adquisicion` - Puede no conocerse

---

## 📚 Documentación Adicional

- **Modelo**: `apps/bienes/models.py`
- **Formulario**: `apps/bienes/forms.py`
- **Admin**: `apps/bienes/admin.py`
- **Migraciones**: `apps/bienes/migrations/`

---

**Fecha**: 11/11/2025  
**Versión**: 1.0.0  
**Estado**: ✅ DOCUMENTADO
