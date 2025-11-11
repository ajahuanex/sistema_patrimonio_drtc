# 🌐 Cómo Ver las Estadísticas en el Navegador

## 📋 Pasos Rápidos

### 1. Verificar que Docker esté corriendo

```bash
docker-compose ps
```

**Deberías ver algo como:**
```
NAME                              STATUS
sistema_patrimonio_drtc-db-1      Up (healthy)
sistema_patrimonio_drtc-nginx-1   Up
sistema_patrimonio_drtc-redis-1   Up (healthy)
sistema_patrimonio_drtc-web-1     Up
```

✅ Si todos están "Up", continúa al paso 2  
❌ Si no están corriendo, ejecuta: `docker-compose up -d`

---

### 2. Abrir el navegador

Abre tu navegador favorito (Chrome, Firefox, Edge, etc.) y ve a:

```
http://localhost:8000
```

O también puedes usar:

```
http://127.0.0.1:8000
```

---

### 3. Iniciar sesión (si es necesario)

Si te pide login, usa las credenciales de administrador que configuraste.

**Usuario por defecto**: admin  
**Contraseña**: (la que configuraste)

Si no tienes usuario, créalo con:

```bash
docker-compose exec web python manage.py createsuperuser
```

---

### 4. ¡Listo! Deberías ver el Dashboard

Verás algo como esto:

```
┌─────────────────────────────────────────────────────────────┐
│  Sistema de Registro de Patrimonio - DRTC Puno              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ 📦  100  │  │ ✅   26  │  │ 🏢    3  │  │ 📅  100  │   │
│  │  Bienes  │  │  Buenos  │  │ Oficinas │  │ Este Mes │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                                                              │
│  [Gráficos de distribución por estado]                      │
│  [Top 5 oficinas con más bienes]                            │
│  [Información del sistema]                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Qué Deberías Ver

### Tarjetas Principales (Arriba)

1. **Total Bienes**: 100
   - Muestra el total de bienes patrimoniales activos

2. **En Buen Estado**: 26
   - Bienes con estado "Bueno"

3. **Oficinas**: 3
   - Total de oficinas activas

4. **Este Mes**: 100
   - Bienes registrados en el mes actual

### Sección de Distribución por Estado

Un gráfico de barras mostrando:
- 🟢 Nuevo: 32 bienes (32%)
- 🔵 Bueno: 26 bienes (26%)
- 🟡 Regular: 18 bienes (18%)
- 🔴 Malo/RAEE/Chatarra: 24 bienes (24%)

### Información del Sistema

- 📋 Catálogo SBN: 4,755 elementos
- 👥 Usuarios Activos: 2
- 🗑️ En Papelera: 0
- 💰 Valor Total: S/ 246,661.84

### Top 5 Oficinas

1. Administración General: 52 bienes
2. Finanzas y Contabilidad2: 48 bienes

---

## 🎨 Colores y Diseño

Las estadísticas usan Bootstrap 5 con colores representativos:

- **Azul** (primary): Total de bienes
- **Verde** (success): Bienes en buen estado
- **Amarillo** (warning): Oficinas
- **Cyan** (info): Registros del mes

---

## 📱 Responsividad

El dashboard se adapta a tu pantalla:

### En Desktop (>992px)
- 4 tarjetas en una fila
- Gráficos lado a lado

### En Tablet (768-991px)
- 2 tarjetas por fila
- Gráficos apilados

### En Móvil (<768px)
- 1 tarjeta por fila
- Todo apilado verticalmente

**Prueba redimensionando la ventana del navegador!**

---

## 🔄 Actualizar las Estadísticas

Las estadísticas se actualizan automáticamente cada vez que:

1. Registras un nuevo bien
2. Modificas el estado de un bien
3. Asignas un bien a una oficina
4. Eliminas o restauras un bien

**Para ver los cambios**: Simplemente recarga la página (F5)

---

## 🧪 Probar con Más Datos

Si quieres ver más datos de prueba:

```bash
# Generar 50 bienes más
docker-compose exec web python manage.py generar_datos_prueba --bienes 50

# Luego recarga la página en el navegador
```

---

## 🐛 Solución de Problemas

### Problema: "No se puede conectar al servidor"

**Solución:**
```bash
# Verificar que Docker esté corriendo
docker-compose ps

# Si no está corriendo, iniciarlo
docker-compose up -d

# Esperar 30 segundos y volver a intentar
```

### Problema: "Página en blanco"

**Solución:**
```bash
# Ver los logs del contenedor web
docker-compose logs web

# Reiniciar el contenedor
docker-compose restart web
```

### Problema: "Error 500"

**Solución:**
```bash
# Ver los logs para más detalles
docker-compose logs web --tail=50

# Verificar que las migraciones estén aplicadas
docker-compose exec web python manage.py migrate
```

### Problema: "No veo estadísticas, todo en 0"

**Solución:**
```bash
# Generar datos de prueba
docker-compose exec web python manage.py generar_datos_prueba --bienes 100

# Recargar la página
```

---

## 📊 Verificar que Todo Funciona

Ejecuta el script de verificación:

```bash
docker-compose exec web python verificar_estadisticas.py
```

Deberías ver:

```
✅ Total de bienes activos: 100
✅ Bienes en estado NUEVO: 32
✅ Bienes en estado BUENO: 26
✅ Bienes en estado REGULAR: 18
✅ Bienes en estado MALO/RAEE/CHATARRA: 24
✅ Total de elementos en catálogo: 4755
✅ Total de oficinas activas: 3
✅ Todas las estadísticas están funcionando correctamente
```

---

## 🎯 Navegación Rápida

Una vez en el dashboard, puedes navegar a:

- **Bienes**: Ver lista completa de bienes
- **Catálogo**: Ver catálogo SBN
- **Oficinas**: Gestionar oficinas
- **Reportes**: Generar reportes
- **Usuarios**: Administrar usuarios (si eres admin)

---

## 📸 Captura de Pantalla

Si quieres compartir o documentar, puedes tomar una captura de pantalla:

- **Windows**: Win + Shift + S
- **Mac**: Cmd + Shift + 4
- **Linux**: PrtScn o Shift + PrtScn

---

## 🎉 ¡Disfruta tu Dashboard!

Ahora tienes un dashboard completamente funcional con:

✅ Estadísticas en tiempo real  
✅ Gráficos visuales  
✅ Información detallada  
✅ Diseño responsivo  
✅ Datos de prueba  

**¡Todo listo para usar!** 🚀

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs: `docker-compose logs web`
2. Verifica el estado: `docker-compose ps`
3. Ejecuta verificación: `docker-compose exec web python verificar_estadisticas.py`
4. Consulta la documentación completa en `VERIFICACION_ESTADISTICAS_COMPLETA.md`

---

**Última Actualización**: 11/11/2025  
**Versión**: 1.0.0  
**Estado**: ✅ FUNCIONANDO
