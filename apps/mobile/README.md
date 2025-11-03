# API REST Móvil - Sistema de Patrimonio

Esta documentación describe la API REST implementada para aplicaciones móviles del Sistema de Registro de Patrimonio.

## Autenticación

La API utiliza JWT (JSON Web Tokens) para autenticación.

### Endpoints de Autenticación

#### POST /api/auth/login/
Iniciar sesión y obtener tokens JWT.

**Request:**
```json
{
    "username": "usuario",
    "password": "contraseña"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "usuario",
        "email": "usuario@example.com",
        "first_name": "Nombre",
        "last_name": "Apellido",
        "is_staff": true,
        "is_superuser": false
    }
}
```

#### POST /api/auth/token/refresh/
Refrescar token de acceso.

**Request:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### GET /api/auth/profile/
Obtener información del usuario autenticado.

**Headers:** `Authorization: Bearer <access_token>`

## Endpoints de Bienes Patrimoniales

### GET /api/bienes/
Listar bienes patrimoniales con filtros y paginación.

**Parámetros de consulta:**
- `estado_bien`: Filtrar por estado (N, B, R, M, E, C)
- `oficina`: ID de oficina
- `catalogo`: ID de catálogo
- `marca__icontains`: Buscar por marca
- `search`: Búsqueda general en múltiples campos
- `ordering`: Ordenar por campo (-created_at, codigo_patrimonial, etc.)
- `page`: Número de página
- `page_size`: Elementos por página

### GET /api/bienes/{id}/
Obtener detalles de un bien específico.

### POST /api/bienes/
Crear un nuevo bien patrimonial.

**Request:**
```json
{
    "codigo_patrimonial": "PAT001",
    "codigo_interno": "INT001",
    "catalogo_id": 1,
    "oficina_id": 1,
    "estado_bien": "B",
    "marca": "HP",
    "modelo": "EliteDesk",
    "color": "Negro",
    "serie": "ABC123",
    "observaciones": "Nuevo equipo"
}
```

### PUT /api/bienes/{id}/
Actualizar un bien patrimonial.

### GET /api/bienes/buscar-por-qr/{qr_code}/
Buscar un bien por su código QR.

### GET /api/bienes/{id}/historial/
Obtener el historial de estados de un bien.

### POST /api/bienes/{id}/actualizar_estado/
Actualizar el estado de un bien desde dispositivo móvil.

**Request:**
```json
{
    "estado_bien": "R",
    "observaciones": "Estado actualizado desde móvil",
    "ubicacion_gps": "-15.8402,-70.0219",
    "foto": "<archivo_imagen>"
}
```

### POST /api/bienes/{id}/capturar_foto/
Capturar y asociar una foto a un bien.

### GET /api/bienes/estadisticas/
Obtener estadísticas básicas de bienes.

## Endpoints Móviles Específicos

### POST /api/mobile/scan/
Procesar escaneo QR desde dispositivo móvil.

**Request:**
```json
{
    "qr_code": "QR123456"
}
```

**Response:**
```json
{
    "bien": { /* datos del bien */ },
    "puede_editar": true,
    "puede_actualizar_estado": true
}
```

### POST /api/mobile/inventario-rapido/
Inventario rápido escaneando múltiples códigos QR.

**Request:**
```json
{
    "codigos_qr": ["QR123", "QR456", "QR789"],
    "ubicacion_gps": "-15.8402,-70.0219",
    "observaciones": "Inventario rápido desde móvil"
}
```

### GET /api/mobile/dashboard/
Dashboard con información resumida para móvil.

## Sincronización Offline

### POST /api/sync/cambios/
Sincronizar cambios realizados offline.

**Request:**
```json
{
    "dispositivo_id": "DEVICE_001",
    "cambios": [
        {
            "tipo_cambio": "CAMBIAR_ESTADO",
            "timestamp_local": "2024-01-01T10:00:00Z",
            "bien_qr_code": "QR123",
            "datos_cambio": {
                "estado_bien": "M",
                "observaciones": "Cambio desde móvil"
            },
            "ubicacion_gps": "-15.8402,-70.0219"
        }
    ]
}
```

### GET /api/sync/estado/{sesion_id}/
Obtener el estado de una sesión de sincronización.

### POST /api/sync/resolver-conflicto/
Resolver un conflicto de sincronización.

**Request:**
```json
{
    "conflicto_id": 1,
    "resolucion": "CLIENTE",
    "datos_manuales": { /* datos opcionales para resolución manual */ }
}
```

### GET /api/sync/cambios-pendientes/
Obtener cambios pendientes de sincronización.

### POST /api/sync/reintentar/
Reintentar sincronización de cambios con error.

## Endpoints de Catálogo y Oficinas

### GET /api/catalogo/
Listar catálogo de bienes (solo lectura).

### GET /api/oficinas/
Listar oficinas activas (solo lectura).

## Códigos de Estado HTTP

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado exitosamente
- `202 Accepted`: Operación aceptada (procesamiento asíncrono)
- `400 Bad Request`: Datos inválidos
- `401 Unauthorized`: No autenticado
- `403 Forbidden`: Sin permisos
- `404 Not Found`: Recurso no encontrado
- `409 Conflict`: Conflicto (código duplicado)
- `500 Internal Server Error`: Error interno del servidor

## Tipos de Cambios Offline

- `CREAR`: Crear nuevo bien
- `ACTUALIZAR`: Actualizar bien existente
- `CAMBIAR_ESTADO`: Cambiar estado de bien
- `AGREGAR_FOTO`: Agregar foto a bien
- `INVENTARIO`: Registro de inventario

## Estados de Sincronización

- `PENDIENTE`: Pendiente de procesamiento
- `PROCESANDO`: En proceso
- `COMPLETADO`: Completado exitosamente
- `ERROR`: Error en procesamiento
- `CONFLICTO`: Conflicto que requiere resolución manual

## Tipos de Conflictos

- `BIEN_MODIFICADO`: Bien modificado en servidor
- `BIEN_ELIMINADO`: Bien eliminado en servidor
- `CODIGO_DUPLICADO`: Código patrimonial duplicado
- `DATOS_INCONSISTENTES`: Datos inconsistentes

## Notas de Implementación

1. Todos los endpoints requieren autenticación JWT excepto los de login.
2. Los filtros y búsquedas son case-insensitive.
3. La paginación está habilitada por defecto (50 elementos por página).
4. Los cambios offline se procesan de forma asíncrona usando Celery.
5. Las fotos se almacenan en el sistema de archivos del servidor.
6. Los conflictos de sincronización requieren resolución manual.