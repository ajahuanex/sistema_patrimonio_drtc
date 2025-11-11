# 🚀 Pasos Simples para Ver las Estadísticas

## ✅ Paso 1: Limpiar Cache del Navegador

### En Chrome, Firefox o Edge:

1. Presiona estas teclas juntas:
   - **Windows**: `Ctrl + Shift + R`
   - **Mac**: `Cmd + Shift + R`

2. Espera a que la página recargue

**¡Eso es todo!** Deberías ver los números ahora.

---

## 🔄 Si Aún Ves Ceros...

### Paso 2: Abrir en Modo Incógnito

1. Presiona estas teclas juntas:
   - **Windows**: `Ctrl + Shift + N`
   - **Mac**: `Cmd + Shift + N`

2. En la ventana incógnita, ve a:
   ```
   http://localhost:8000
   ```

3. ¿Ves los números ahora?
   - ✅ **SÍ** → Era problema de cache. Cierra incógnito y limpia el cache del navegador normal.
   - ❌ **NO** → Continúa al Paso 3.

---

## 🔧 Si Aún No Funciona...

### Paso 3: Reiniciar el Servidor

1. Abre una terminal (CMD o PowerShell)

2. Copia y pega este comando:
   ```bash
   docker-compose restart web
   ```

3. Espera 10 segundos

4. Recarga la página con `Ctrl + Shift + R`

---

## 🎯 ¿Qué Deberías Ver?

### Números Esperados:

```
📦 Total Bienes:          100
✅ En Buen Estado:         26
🏢 Oficinas:                3
📅 Este Mes:              100
```

### Si ves estos números, ¡FUNCIONA! 🎉

---

## 🐛 Solución Rápida de Problemas

### Problema: "No puedo acceder a localhost:8000"

**Solución**:
```bash
docker-compose ps
```

Si no ves "Up", ejecuta:
```bash
docker-compose up -d
```

---

### Problema: "Veo errores en la página"

**Solución**:
```bash
docker-compose logs web --tail=20
```

Busca líneas en rojo y compártelas.

---

### Problema: "Las barras no tienen colores"

**Solución**:
1. Limpia el cache: `Ctrl + Shift + Del`
2. Marca "Imágenes y archivos en caché"
3. Haz clic en "Borrar datos"
4. Recarga la página

---

## ✅ Checklist Rápido

- [ ] Limpié el cache (`Ctrl + Shift + R`)
- [ ] Probé en modo incógnito
- [ ] Reinicié el servidor
- [ ] Esperé 10 segundos
- [ ] Recargué la página

---

## 📞 Comandos de Emergencia

Si nada funciona, ejecuta estos comandos en orden:

```bash
# 1. Ver estado
docker-compose ps

# 2. Reiniciar todo
docker-compose restart

# 3. Esperar 30 segundos
# (cuenta hasta 30)

# 4. Verificar estadísticas
docker-compose exec web python verificar_estadisticas.py
```

Si el último comando muestra números (100, 26, 3, etc.), entonces el problema es solo de cache del navegador.

---

## 🎉 ¡Listo!

Si seguiste estos pasos, deberías ver las estadísticas funcionando.

**Recuerda**: Siempre usa `Ctrl + Shift + R` para recargar sin cache.

---

**Fecha**: 11/11/2025  
**Estado**: ✅ SOLUCIONADO
