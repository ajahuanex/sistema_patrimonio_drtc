# Guía de Uso: Reportes de Auditoría de Eliminaciones

## 📖 Introducción

El sistema de reportes de auditoría de eliminaciones proporciona una herramienta completa para monitorear, analizar y reportar todas las operaciones relacionadas con la eliminación y restauración de registros en el sistema.

## 🎯 Casos de Uso

### 1. Auditoría Mensual Completa

**Objetivo:** Generar un reporte mensual de todas las operaciones de eliminación.

**Pasos:**
1. Acceder a `/core/auditoria/eliminaciones/`
2. Establecer filtros de fecha:
   - Fecha desde: Primer día del mes anterior
   - Fecha hasta: Último día del mes anterior
3. Revisar estadísticas generales
4. Revisar patrones sospechosos (si los hay)
5. Click en "📄 Exportar a PDF"
6. Guardar el archivo con nombre descriptivo: `auditoria_eliminaciones_YYYY_MM.pdf`
7. Archivar el reporte

**Resultado:** Reporte PDF profesional con todas las operaciones del mes.

---

### 2. Investigación de Usuario Específico

**Objetivo:** Revisar todas las operaciones realizadas por un usuario específico.

**Pasos:**
1. Acceder a reportes de auditoría
2. En el filtro "Usuario", escribir el nombre del usuario
3. Click en "Aplicar Filtros"
4. Revisar la lista de operaciones
5. Para cada operación sospechosa:
   - Click en "Ver Detalle"
   - Revisar snapshot del objeto
   - Revisar contexto (IP, User Agent)
   - Revisar motivo
6. Si es necesario, exportar evidencia:
   - Volver a la lista
   - Click en "📊 Exportar a Excel"

**Resultado:** Análisis completo de la actividad del usuario con evidencia exportable.

---

### 3. Análisis de Seguridad Semanal

**Objetivo:** Detectar y responder a patrones sospechosos.

**Pasos:**
1. Ejecutar comando de detección:
   ```bash
   python manage.py check_suspicious_patterns --hours 168 --verbose
   ```
2. Revisar patrones detectados en la salida
3. Para cada patrón de alta severidad:
   - Acceder a reportes web
   - Filtrar por el usuario mencionado
   - Revisar detalles de las operaciones
   - Contactar al usuario si es necesario
4. Documentar acciones tomadas
5. Si se detectan problemas serios:
   - Exportar evidencia a PDF
   - Escalar a dirección

**Resultado:** Detección temprana y respuesta a comportamientos anómalos.

---

### 4. Reporte Ejecutivo Trimestral

**Objetivo:** Generar un reporte de alto nivel para dirección.

**Pasos:**
1. Acceder a reportes de auditoría
2. Establecer rango de fechas del trimestre
3. Tomar nota de estadísticas clave:
   - Total de operaciones
   - Operaciones exitosas vs fallidas
   - Distribución por módulo
   - Top usuarios más activos
4. Capturar screenshot del gráfico de tendencias
5. Revisar patrones sospechosos detectados
6. Exportar a PDF para anexar al reporte
7. Crear presentación ejecutiva con:
   - Resumen de estadísticas
   - Gráfico de tendencias
   - Patrones detectados y acciones tomadas
   - Recomendaciones

**Resultado:** Reporte ejecutivo completo con métricas y análisis.

---

### 5. Verificación de Eliminación Permanente

**Objetivo:** Auditar el uso del código de seguridad para eliminaciones permanentes.

**Pasos:**
1. Acceder a reportes
2. Filtrar por acción: "Eliminación Permanente"
3. Revisar cada operación:
   - Verificar que el código de seguridad fue usado
   - Verificar el usuario que realizó la operación
   - Revisar el motivo
   - Verificar el snapshot del objeto eliminado
4. Para operaciones sin justificación clara:
   - Contactar al usuario
   - Solicitar explicación
   - Documentar respuesta
5. Si se detecta uso indebido:
   - Exportar evidencia
   - Escalar a dirección
   - Considerar cambio de código de seguridad

**Resultado:** Verificación completa del uso del código de seguridad.

---

### 6. Análisis de Tendencias

**Objetivo:** Identificar patrones y tendencias en el uso del sistema.

**Pasos:**
1. Acceder a reportes de auditoría
2. Establecer rango de fechas amplio (ej: últimos 3 meses)
3. Analizar el gráfico de tendencias:
   - Identificar picos de actividad
   - Identificar días con actividad inusual
   - Comparar tipos de operaciones
4. Para cada pico identificado:
   - Filtrar por esa fecha específica
   - Revisar qué operaciones se realizaron
   - Identificar el motivo del pico
5. Documentar hallazgos:
   - Patrones normales (ej: fin de mes)
   - Patrones anómalos
   - Recomendaciones de mejora

**Resultado:** Comprensión profunda de patrones de uso del sistema.

---

### 7. Respuesta a Incidente de Seguridad

**Objetivo:** Investigar un posible incidente de seguridad.

**Pasos:**
1. Recibir alerta de patrón sospechoso
2. Acceder inmediatamente a reportes
3. Filtrar por:
   - Usuario mencionado en la alerta
   - Rango de fechas del incidente
4. Revisar cronológicamente todas las operaciones:
   - Anotar hora de cada operación
   - Anotar IP de origen
   - Anotar objetos afectados
5. Para cada operación:
   - Ver detalle completo
   - Revisar snapshot
   - Verificar si hay logs relacionados
6. Exportar toda la evidencia:
   - Excel con todas las operaciones
   - PDF con detalles
   - Screenshots relevantes
7. Crear línea de tiempo del incidente
8. Tomar acciones correctivas:
   - Bloquear usuario si es necesario
   - Cambiar código de seguridad
   - Restaurar objetos si es necesario
9. Documentar incidente completo
10. Implementar medidas preventivas

**Resultado:** Investigación completa y documentada del incidente.

---

## 🔧 Configuración de Alertas Automáticas

### Configuración Básica (Cada Hora)

```bash
# Editar crontab
crontab -e

# Agregar línea
0 * * * * cd /path/to/proyecto && /path/to/python manage.py check_suspicious_patterns --send-notifications >> /var/log/audit_alerts.log 2>&1
```

### Configuración Avanzada (Múltiples Horarios)

```bash
# Cada hora durante horario laboral (8am-6pm)
0 8-18 * * * cd /path/to/proyecto && /path/to/python manage.py check_suspicious_patterns --send-notifications

# Cada 4 horas fuera de horario laboral
0 */4 * * * cd /path/to/proyecto && /path/to/python manage.py check_suspicious_patterns --hours 4 --send-notifications

# Reporte diario completo a las 8am
0 8 * * * cd /path/to/proyecto && /path/to/python manage.py check_suspicious_patterns --hours 24 --send-notifications --verbose
```

### Verificar Configuración

```bash
# Ver crontab actual
crontab -l

# Ver logs de ejecución
tail -f /var/log/audit_alerts.log

# Ejecutar manualmente para probar
python manage.py check_suspicious_patterns --send-notifications --verbose
```

---

## 📊 Interpretación de Estadísticas

### Estadísticas Generales

**Total de Operaciones**
- Indica el volumen de actividad
- Comparar con períodos anteriores
- Picos pueden indicar actividad inusual

**Operaciones Exitosas vs Fallidas**
- Tasa de éxito normal: > 95%
- Muchos fallos pueden indicar:
  - Problemas de permisos
  - Intentos de acceso no autorizado
  - Problemas técnicos

### Estadísticas por Acción

**Eliminación Lógica (soft_delete)**
- Operación más común
- Debería ser la mayoría de las eliminaciones

**Restauración (restore)**
- Indica corrección de errores
- Muchas restauraciones pueden indicar:
  - Usuarios eliminando por error
  - Necesidad de más capacitación
  - Problemas en el flujo de trabajo

**Eliminación Permanente (permanent_delete)**
- Operación crítica
- Debería ser poco frecuente
- Cada una debe estar justificada

**Eliminación Automática (auto_delete)**
- Indica funcionamiento del sistema de limpieza
- Debería ser regular y predecible

### Estadísticas por Módulo

**Distribución Normal**
- Bienes: 60-70%
- Oficinas: 10-20%
- Catálogo: 10-20%

**Distribución Anómala**
- Un módulo con > 80% puede indicar problema
- Investigar causa del desbalance

### Top Usuarios

**Usuarios Activos**
- Administradores y funcionarios en el top es normal
- Usuarios de consulta no deberían aparecer
- Un usuario con actividad excesiva requiere revisión

---

## 🚨 Patrones Sospechosos - Guía de Respuesta

### ⚠️ Múltiples Eliminaciones Permanentes (Alta Severidad)

**Qué significa:**
Un usuario realizó 5 o más eliminaciones permanentes en 1 hora.

**Acciones:**
1. Contactar inmediatamente al usuario
2. Verificar que todas las eliminaciones fueron intencionales
3. Revisar los objetos eliminados
4. Si no hay justificación:
   - Bloquear temporalmente al usuario
   - Escalar a dirección
   - Considerar cambio de código de seguridad

**Prevención:**
- Capacitar sobre el uso correcto
- Establecer políticas claras
- Requerir aprobación para eliminaciones masivas

---

### ⚡ Múltiples Intentos Fallidos (Media Severidad)

**Qué significa:**
Un usuario tuvo 3 o más operaciones fallidas en 1 hora.

**Acciones:**
1. Revisar los errores específicos
2. Verificar si es problema de permisos
3. Contactar al usuario para ofrecer ayuda
4. Si son intentos de acceso no autorizado:
   - Bloquear usuario
   - Investigar más a fondo

**Prevención:**
- Mejorar mensajes de error
- Capacitar sobre permisos
- Revisar configuración de permisos

---

### 🔥 Eliminaciones Masivas (Alta Severidad)

**Qué significa:**
Un usuario eliminó 20 o más elementos de un módulo en 24 horas.

**Acciones:**
1. Verificar si es una operación planificada
2. Revisar los objetos eliminados
3. Confirmar que hay backup
4. Si no está planificado:
   - Detener al usuario
   - Investigar motivo
   - Considerar restauración masiva

**Prevención:**
- Requerir notificación previa para operaciones masivas
- Implementar confirmación adicional
- Establecer límites por día

---

### 🌙 Actividad Fuera de Horario (Baja Severidad)

**Qué significa:**
Un usuario realizó 5 o más operaciones entre 10pm y 6am.

**Acciones:**
1. Verificar si el usuario tiene autorización
2. Revisar las operaciones realizadas
3. Confirmar que son legítimas
4. Documentar si es actividad normal del usuario

**Prevención:**
- Establecer políticas de horario
- Requerir autorización para trabajo nocturno
- Implementar restricciones horarias si es necesario

---

### 🔄 Restaurar y Eliminar (Media Severidad)

**Qué significa:**
Un usuario restauró 3+ elementos y luego eliminó permanentemente 3+ en 24 horas.

**Acciones:**
1. Revisar la secuencia de operaciones
2. Verificar si hay un motivo legítimo
3. Contactar al usuario para explicación
4. Si no hay justificación:
   - Investigar más a fondo
   - Considerar restricción de permisos

**Prevención:**
- Capacitar sobre el flujo correcto
- Establecer procedimientos claros
- Requerir justificación para este patrón

---

## 📈 Mejores Prácticas

### Para Administradores

1. **Revisar Reportes Regularmente**
   - Diariamente: Patrones sospechosos
   - Semanalmente: Estadísticas generales
   - Mensualmente: Tendencias y reportes completos

2. **Configurar Alertas**
   - Implementar alertas automáticas
   - Revisar notificaciones inmediatamente
   - Documentar todas las respuestas

3. **Mantener Evidencia**
   - Exportar reportes regularmente
   - Archivar evidencia de incidentes
   - Mantener logs de acciones tomadas

4. **Capacitar Usuarios**
   - Entrenar en uso correcto del sistema
   - Explicar consecuencias de mal uso
   - Proporcionar guías y procedimientos

5. **Revisar Configuración**
   - Ajustar umbrales según necesidad
   - Actualizar políticas regularmente
   - Mejorar detección de patrones

### Para Auditores

1. **Análisis Sistemático**
   - Seguir checklist de auditoría
   - Documentar todos los hallazgos
   - Mantener objetividad

2. **Uso de Filtros**
   - Dominar todos los filtros disponibles
   - Combinar filtros para análisis profundo
   - Guardar configuraciones comunes

3. **Interpretación de Datos**
   - Entender el contexto del negocio
   - Identificar patrones normales vs anómalos
   - Correlacionar con otros eventos

4. **Reportes Efectivos**
   - Usar visualizaciones claras
   - Incluir recomendaciones accionables
   - Priorizar hallazgos por severidad

5. **Seguimiento**
   - Verificar implementación de recomendaciones
   - Medir mejoras en el tiempo
   - Actualizar procedimientos según aprendizajes

---

## 🎓 Capacitación de Usuarios

### Temas Clave

1. **Navegación Básica**
   - Cómo acceder a reportes
   - Cómo usar filtros
   - Cómo interpretar estadísticas

2. **Exportación**
   - Cuándo exportar a Excel vs PDF
   - Cómo aplicar filtros antes de exportar
   - Cómo usar los reportes exportados

3. **Interpretación**
   - Qué significan las estadísticas
   - Cómo identificar patrones
   - Cuándo escalar un hallazgo

4. **Mejores Prácticas**
   - Frecuencia de revisión
   - Documentación de hallazgos
   - Respuesta a alertas

### Material de Capacitación

- Esta guía de uso
- Guía rápida (TASK_22_QUICK_REFERENCE.md)
- Sesiones prácticas con datos de prueba
- Videos tutoriales (a crear)
- FAQ (a crear)

---

## 📞 Soporte y Ayuda

### Recursos Disponibles

1. **Documentación**
   - TASK_22_IMPLEMENTATION_SUMMARY.md - Documentación técnica completa
   - TASK_22_QUICK_REFERENCE.md - Referencia rápida
   - TASK_22_VERIFICATION.md - Verificación de implementación
   - Esta guía de uso

2. **Ayuda en Línea**
   - Tooltips en la interfaz
   - Mensajes de error descriptivos
   - Validaciones en tiempo real

3. **Soporte Técnico**
   - Equipo de desarrollo
   - Administradores del sistema
   - Documentación de código

### Problemas Comunes

**No puedo acceder a reportes**
- Verificar permisos de usuario
- Contactar a administrador

**Los filtros no funcionan**
- Verificar formato de fechas (YYYY-MM-DD)
- Limpiar caché del navegador
- Intentar con otro navegador

**La exportación falla**
- Verificar que las librerías están instaladas
- Reducir el rango de fechas
- Aplicar más filtros para reducir resultados

**No veo patrones sospechosos**
- Puede ser que no haya actividad anómala
- Verificar el período analizado
- Revisar umbrales de detección

---

## ✅ Checklist de Auditoría

### Auditoría Diaria
- [ ] Revisar patrones sospechosos
- [ ] Verificar alertas recibidas
- [ ] Revisar eliminaciones permanentes del día
- [ ] Documentar hallazgos

### Auditoría Semanal
- [ ] Revisar estadísticas de la semana
- [ ] Analizar tendencias
- [ ] Verificar top usuarios
- [ ] Exportar reporte semanal
- [ ] Actualizar documentación de incidentes

### Auditoría Mensual
- [ ] Generar reporte mensual completo
- [ ] Analizar tendencias del mes
- [ ] Comparar con mes anterior
- [ ] Identificar mejoras necesarias
- [ ] Actualizar políticas si es necesario
- [ ] Archivar reportes

### Auditoría Trimestral
- [ ] Generar reporte ejecutivo
- [ ] Analizar tendencias del trimestre
- [ ] Revisar efectividad de controles
- [ ] Actualizar procedimientos
- [ ] Capacitar usuarios según hallazgos
- [ ] Presentar a dirección

---

## 🎉 Conclusión

Este sistema de reportes de auditoría proporciona todas las herramientas necesarias para mantener un control completo sobre las operaciones de eliminación en el sistema. Úsalo regularmente, mantén la documentación actualizada, y responde proactivamente a los patrones detectados para mantener la seguridad e integridad del sistema.

Para más información, consulta la documentación técnica completa en TASK_22_IMPLEMENTATION_SUMMARY.md.
