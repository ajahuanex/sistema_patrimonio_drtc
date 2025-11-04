# Guía de Usuario para Administradores - Sistema de Registro de Patrimonio

## Introducción

Esta guía está dirigida a los administradores del Sistema de Registro de Patrimonio de la Dirección Regional de Transportes y Comunicaciones de Puno. Aquí encontrará instrucciones detalladas para gestionar el sistema, usuarios, y realizar las tareas administrativas principales.

## Acceso al Sistema

### Inicio de Sesión

1. Acceder a: `https://tu-dominio.com/admin/`
2. Ingresar credenciales de administrador
3. Hacer clic en "Iniciar Sesión"

### Cambio de Contraseña Inicial

**IMPORTANTE**: Cambiar la contraseña por defecto en el primer acceso.

1. Ir a **Usuarios** > **Usuarios**
2. Hacer clic en su usuario (admin)
3. Cambiar la contraseña en la sección "Contraseña"
4. Guardar cambios

## Gestión de Usuarios

### Crear Nuevo Usuario

1. Ir a **Core** > **Usuarios**
2. Hacer clic en **Agregar Usuario**
3. Completar información:
   - **Nombre de usuario**: Único, sin espacios
   - **Contraseña**: Mínimo 8 caracteres
   - **Email**: Email válido del usuario
   - **Nombre**: Nombre completo
   - **Apellidos**: Apellidos completos

4. Asignar **Grupos** según el rol:
   - **Administradores**: Acceso completo
   - **Funcionarios**: Gestión de inventario
   - **Auditores**: Solo lectura y reportes
   - **Consulta**: Solo consulta de información

5. Configurar **Permisos de usuario** si es necesario
6. Marcar **Activo** para habilitar la cuenta
7. Guardar

### Roles y Permisos

#### Administrador
- **Permisos**: Acceso completo al sistema
- **Funciones**:
  - Gestión de usuarios
  - Configuración del sistema
  - Importación masiva de datos
  - Generación de reportes
  - Gestión de catálogo y oficinas

#### Funcionario
- **Permisos**: Gestión de inventario
- **Funciones**:
  - Registro de bienes patrimoniales
  - Actualización de estados
  - Movimientos de bienes
  - Consulta de inventario
  - Generación de reportes básicos

#### Auditor
- **Permisos**: Lectura y reportes
- **Funciones**:
  - Consulta de inventario
  - Generación de reportes
  - Exportación de datos
  - Auditoría de movimientos

#### Consulta
- **Permisos**: Solo lectura
- **Funciones**:
  - Consulta de inventario
  - Visualización de información básica

### Desactivar Usuario

1. Ir a **Core** > **Usuarios**
2. Seleccionar el usuario
3. Desmarcar **Activo**
4. Guardar

**Nota**: No eliminar usuarios, solo desactivarlos para mantener el historial.

## Gestión del Catálogo Oficial

### Importar Catálogo desde Excel

1. Ir a **Catálogo** > **Importar Catálogo**
2. Descargar plantilla Excel si es necesario
3. Preparar archivo Excel con columnas:
   - **CATÁLOGO**: Código del catálogo
   - **Denominación**: Nombre del bien
   - **Grupo**: Grupo al que pertenece
   - **Clase**: Clase específica
   - **Resolución**: Resolución que lo respalda
   - **Estado**: ACTIVO o EXCLUIDO

4. Seleccionar archivo Excel
5. Hacer clic en **Importar**
6. Revisar reporte de importación
7. Corregir errores si los hay

### Gestión Manual del Catálogo

1. Ir a **Catálogo** > **Catálogos**
2. Para agregar nuevo:
   - Hacer clic en **Agregar Catálogo**
   - Completar información requerida
   - Guardar

3. Para editar existente:
   - Hacer clic en el catálogo deseado
   - Modificar información
   - Guardar

### Validaciones del Catálogo

- **Código único**: No puede haber códigos duplicados
- **Denominación única**: No puede haber denominaciones duplicadas
- **Estado EXCLUIDO**: No permite registro de nuevos bienes

## Gestión de Oficinas

### Importar Oficinas desde Excel

1. Ir a **Oficinas** > **Importar Oficinas**
2. Preparar archivo Excel con columnas:
   - **Código**: Código único de oficina
   - **Nombre**: Nombre de la oficina
   - **Descripción**: Descripción opcional
   - **Responsable**: Nombre del responsable
   - **Estado**: ACTIVO o INACTIVO

3. Seleccionar archivo Excel
4. Hacer clic en **Importar**
5. Revisar reporte de importación

### Gestión Manual de Oficinas

1. Ir a **Oficinas** > **Oficinas**
2. Para agregar nueva:
   - Hacer clic en **Agregar Oficina**
   - Completar información
   - Marcar **Estado** como activo
   - Guardar

3. Para editar existente:
   - Hacer clic en la oficina deseada
   - Modificar información
   - Guardar

### Desactivar Oficina

1. Ir a **Oficinas** > **Oficinas**
2. Seleccionar la oficina
3. Desmarcar **Estado**
4. Guardar

**Nota**: No se puede eliminar una oficina que tenga bienes asignados.

## Gestión de Inventario Patrimonial

### Importar Inventario desde Excel

1. Ir a **Bienes** > **Importar Inventario**
2. Preparar archivo Excel con columnas:
   - **CODIGO PATRIMONIAL**: Código único
   - **CODIGO INTERNO**: Código interno (opcional)
   - **DENOMINACION BIEN**: Debe existir en catálogo
   - **ESTADO BIEN**: N, B, R, M, E, C
   - **MARCA**: Marca del bien
   - **MODELO**: Modelo del bien
   - **COLOR**: Color del bien
   - **SERIE**: Número de serie
   - **DIMENSION**: Dimensiones
   - **PLACA**: Placa (vehículos)
   - **MATRICULAS**: Matrícula (vehículos)
   - **NRO MOTOR**: Número de motor
   - **NRO CHASIS**: Número de chasis
   - **OFICINA**: Código de oficina (debe existir)
   - **OBSERVACIONES**: Observaciones adicionales

3. Seleccionar archivo Excel
4. Hacer clic en **Importar**
5. Revisar reporte de importación
6. Los códigos QR se generan automáticamente

### Registro Manual de Bienes

1. Ir a **Bienes** > **Bienes Patrimoniales**
2. Hacer clic en **Agregar Bien Patrimonial**
3. Completar formulario:
   - **Código Patrimonial**: Único y obligatorio
   - **Catálogo**: Seleccionar de lista desplegable
   - **Oficina**: Seleccionar oficina responsable
   - **Estado del Bien**: Seleccionar estado actual
   - Completar campos adicionales según corresponda

4. Guardar
5. El sistema genera automáticamente:
   - Código QR único
   - URL específica para el bien

### Estados de Bienes

- **N - Nuevo**: Bien en estado nuevo
- **B - Bueno**: Bien en buen estado
- **R - Regular**: Bien en estado regular
- **M - Malo**: Bien en mal estado
- **E - RAEE**: Residuo de aparato eléctrico/electrónico
- **C - Chatarra**: Bien dado de baja

### Movimientos de Bienes

1. Ir a **Bienes** > **Movimientos de Bienes**
2. Hacer clic en **Agregar Movimiento**
3. Completar información:
   - **Bien**: Seleccionar bien a mover
   - **Oficina Origen**: Se completa automáticamente
   - **Oficina Destino**: Seleccionar nueva ubicación
   - **Motivo**: Razón del movimiento
   - **Observaciones**: Detalles adicionales

4. Guardar
5. El sistema actualiza automáticamente la ubicación del bien

## Generación de Reportes

### Reportes Básicos

1. Ir a **Reportes** > **Dashboard**
2. Seleccionar tipo de reporte:
   - **Inventario General**: Listado completo
   - **Por Oficina**: Bienes por ubicación
   - **Por Estado**: Bienes por condición
   - **Por Categoría**: Bienes por grupo/clase

### Filtros Avanzados

1. Ir a **Reportes** > **Filtros Avanzados**
2. Configurar filtros:
   - **Oficina**: Una o varias oficinas
   - **Estado**: Uno o varios estados
   - **Categoría**: Grupo y/o clase
   - **Fechas**: Rango de fechas
   - **Marca/Modelo**: Filtros específicos

3. Hacer clic en **Generar Reporte**
4. Revisar resultados
5. Exportar en formato deseado

### Exportación de Datos

#### Formatos Disponibles
- **Excel (.xlsx)**: Para análisis y respaldo
- **PDF**: Para presentaciones e informes
- **CSV**: Para importar en otros sistemas
- **ZPL**: Para impresión de stickers

#### Proceso de Exportación
1. Generar reporte con filtros deseados
2. Hacer clic en **Exportar**
3. Seleccionar formato
4. Descargar archivo generado

### Reportes Estadísticos

1. Ir a **Reportes** > **Estadísticas**
2. Seleccionar período de análisis
3. Revisar gráficos generados:
   - Distribución por estado
   - Distribución por oficina
   - Evolución temporal
   - Indicadores clave

4. Exportar gráficos si es necesario

## Gestión de Códigos QR y Stickers

### Generación de Stickers

1. Ir a **Reportes** > **Stickers**
2. Seleccionar bienes para imprimir:
   - Por filtros (oficina, estado, etc.)
   - Selección manual
   - Rango de códigos

3. Configurar plantilla:
   - **Tamaño de sticker**: Seleccionar tamaño
   - **Información a mostrar**: Código, denominación, etc.
   - **Posición del QR**: Ubicación en el sticker

4. Generar plantilla ZPL
5. Descargar archivo .zpl
6. Enviar a impresora Zebra

### Configuración de Impresora Zebra

#### Requisitos
- Impresora térmica Zebra compatible con ZPL
- Conexión USB o red
- Driver instalado

#### Proceso de Impresión
1. Abrir archivo .zpl generado
2. Enviar a impresora usando:
   - Software Zebra (ZebraDesigner)
   - Comando de sistema
   - Aplicación de terceros

### Verificación de QR Codes

1. Escanear código QR con dispositivo móvil
2. Verificar que redirija a URL correcta
3. Confirmar que muestra información del bien
4. Probar funcionalidades móviles si corresponde

## Configuración del Sistema

### Variables de Configuración

1. Ir a **Configuración** > **Configuración del Sistema**
2. Ajustar parámetros:
   - **URL Base**: URL principal del sistema
   - **Email de Notificaciones**: Email para alertas
   - **Retención de Backups**: Días de retención
   - **Configuración de Reportes**: Parámetros por defecto

### Notificaciones

#### Configurar Alertas Automáticas
1. Ir a **Notificaciones** > **Configuración**
2. Activar tipos de alerta:
   - **Mantenimiento**: Alertas de mantenimiento
   - **Depreciación**: Bienes próximos a depreciar
   - **Movimientos**: Notificaciones de transferencias

3. Configurar destinatarios
4. Establecer frecuencia de envío

#### Plantillas de Email
1. Ir a **Notificaciones** > **Plantillas**
2. Personalizar plantillas:
   - **Asunto**: Personalizar asunto
   - **Contenido**: Modificar mensaje
   - **Firma**: Agregar firma institucional

### Configuración de Backup

#### Backup Automático
- Se ejecuta diariamente a las 2:00 AM
- Retiene backups según configuración
- Incluye base de datos y archivos media

#### Backup Manual
1. Acceder al servidor
2. Ejecutar: `./scripts/backup.sh`
3. Verificar archivos generados en `./backups/`

## Monitoreo y Mantenimiento

### Dashboard de Monitoreo

1. Ir a **Sistema** > **Estado del Sistema**
2. Revisar indicadores:
   - **Estado de Servicios**: Verde/Rojo
   - **Uso de Recursos**: CPU, Memoria, Disco
   - **Conexiones**: Base de datos, Redis
   - **Certificados SSL**: Estado y expiración

### Logs del Sistema

1. Ir a **Sistema** > **Logs**
2. Revisar tipos de log:
   - **Aplicación**: Errores de Django
   - **Acceso**: Logs de nginx
   - **Base de Datos**: Logs de PostgreSQL
   - **Celery**: Tareas asíncronas

### Tareas de Mantenimiento

#### Diarias
- Verificar estado del sistema
- Revisar logs de errores
- Confirmar ejecución de backups

#### Semanales
- Limpiar logs antiguos
- Verificar certificados SSL
- Optimizar base de datos

#### Mensuales
- Actualizar sistema
- Auditoría de usuarios
- Limpieza de archivos temporales

## Solución de Problemas Comunes

### Usuario No Puede Acceder

1. Verificar que el usuario esté **Activo**
2. Confirmar credenciales correctas
3. Verificar permisos asignados
4. Revisar logs de autenticación

### Error al Importar Excel

1. Verificar formato del archivo
2. Confirmar que las columnas coincidan
3. Revisar datos duplicados
4. Verificar que catálogo/oficinas existan

### Código QR No Funciona

1. Verificar que la URL sea accesible
2. Confirmar que el bien existe
3. Revisar configuración de URL base
4. Probar desde diferentes dispositivos

### Reportes No Se Generan

1. Verificar filtros aplicados
2. Confirmar que hay datos que coincidan
3. Revisar logs de Celery
4. Verificar espacio en disco

### Sistema Lento

1. Verificar uso de recursos
2. Optimizar base de datos
3. Limpiar caché de Redis
4. Revisar consultas lentas

## Contacto y Soporte

### Información de Contacto

- **Soporte Técnico**: soporte@tu-dominio.com
- **Teléfono**: +51-XXX-XXXXXX
- **Horario**: Lunes a Viernes, 8:00 AM - 6:00 PM

### Recursos Adicionales

- **Manual Técnico**: `/docs/MAINTENANCE.md`
- **Guía de Instalación**: `/docs/INSTALLATION.md`
- **API Documentation**: `https://tu-dominio.com/api/docs/`
- **Repository**: `https://github.com/tu-organizacion/sistema-patrimonio`

### Escalación de Problemas

1. **Nivel 1**: Administrador del sistema
2. **Nivel 2**: Soporte técnico especializado
3. **Nivel 3**: Equipo de desarrollo

### Información para Reportar Problemas

Al reportar un problema, incluir:
- **Descripción detallada** del problema
- **Pasos para reproducir** el error
- **Mensajes de error** exactos
- **Navegador y versión** utilizada
- **Capturas de pantalla** si es relevante
- **Logs del sistema** si están disponibles