# Documento de Requisitos - Sistema de Registro de Patrimonio

## Introducción

El Sistema de Registro de Patrimonio es una aplicación web diseñada para la Dirección Regional de Transportes y Comunicaciones de Puno que permitirá gestionar, registrar y controlar todos los bienes patrimoniales de la institución. El sistema facilitará el seguimiento de activos, su ubicación, estado, responsables y movimientos, proporcionando un control eficiente del patrimonio institucional.

## Requisitos

### Requisito 1

**Historia de Usuario:** Como administrador del patrimonio, quiero registrar nuevos bienes patrimoniales con códigos únicos, para que pueda mantener un inventario actualizado sin duplicados.

#### Criterios de Aceptación

1. CUANDO el administrador acceda al formulario de registro ENTONCES el sistema DEBERÁ mostrar campos para: Código Patrimonial, Código Interno, Denominación del Bien (seleccionable desde catálogo oficial), Estado del Bien, Marca, Modelo, Color, Serie, Dimensión, Placa, Matrícula, Nro Motor, Nro Chasis, Oficina (seleccionable desde maestro de oficinas) y Observaciones
2. CUANDO se ingrese un código patrimonial ENTONCES el sistema DEBERÁ validar que sea único en toda la base de datos y mostrar error si ya existe
3. CUANDO se complete el formulario correctamente ENTONCES el sistema DEBERÁ guardar el bien, generar un código QR único y crear una URL específica para ese bien
4. CUANDO se registre un bien ENTONCES el sistema DEBERÁ asignar automáticamente una URL única que contenga el código QR para acceso rápido

### Requisito 2

**Historia de Usuario:** Como funcionario responsable, quiero consultar los bienes bajo mi responsabilidad, para que pueda verificar el inventario asignado a mi área.

#### Criterios de Aceptación

1. CUANDO el funcionario inicie sesión ENTONCES el sistema DEBERÁ mostrar una lista de bienes asignados a su responsabilidad
2. CUANDO se seleccione un bien ENTONCES el sistema DEBERÁ mostrar todos los detalles del activo incluyendo historial de movimientos
3. CUANDO se apliquen filtros de búsqueda ENTONCES el sistema DEBERÁ mostrar resultados que coincidan con los criterios especificados
4. CUANDO se exporte la lista ENTONCES el sistema DEBERÁ generar un reporte en formato Excel o PDF

### Requisito 3

**Historia de Usuario:** Como administrador, quiero registrar movimientos de bienes patrimoniales, para que pueda mantener un historial de transferencias y cambios de ubicación.

#### Criterios de Aceptación

1. CUANDO se inicie un movimiento ENTONCES el sistema DEBERÁ registrar fecha, hora, responsable origen, responsable destino, motivo y observaciones
2. CUANDO se confirme un movimiento ENTONCES el sistema DEBERÁ actualizar automáticamente la ubicación y responsable del bien
3. CUANDO se registre un movimiento ENTONCES el sistema DEBERÁ enviar notificaciones a ambos responsables (origen y destino)
4. CUANDO se consulte el historial ENTONCES el sistema DEBERÁ mostrar todos los movimientos del bien en orden cronológico

### Requisito 4

**Historia de Usuario:** Como auditor, quiero generar reportes de inventario, para que pueda realizar auditorías y verificaciones del patrimonio institucional.

#### Criterios de Aceptación

1. CUANDO se solicite un reporte general ENTONCES el sistema DEBERÁ generar un listado completo de todos los bienes con sus datos actuales
2. CUANDO se apliquen filtros por fecha, ubicación o responsable ENTONCES el sistema DEBERÁ generar reportes específicos según los criterios
3. CUANDO se genere un reporte ENTONCES el sistema DEBERÁ incluir totales por categoría, estado y ubicación
4. CUANDO se exporte un reporte ENTONCES el sistema DEBERÁ permitir formatos Excel, PDF y CSV

### Requisito 5

**Historia de Usuario:** Como técnico de sistemas, quiero generar códigos QR con URLs específicas para cada bien, para que pueda imprimir etiquetas en impresora térmica Zebra y facilitar la identificación rápida.

#### Criterios de Aceptación

1. CUANDO se registre un nuevo bien ENTONCES el sistema DEBERÁ generar automáticamente un código QR que contenga una URL única del bien
2. CUANDO se escanee un código QR ENTONCES el sistema DEBERÁ redirigir a la URL específica mostrando toda la información del bien
3. CUANDO se solicite imprimir etiquetas ENTONCES el sistema DEBERÁ generar formato compatible con impresora térmica Zebra incluyendo código QR y datos básicos
4. CUANDO se genere una etiqueta ENTONCES el sistema DEBERÁ usar formato ZPL (Zebra Programming Language) para impresión directa en impresoras Zebra

### Requisito 6

**Historia de Usuario:** Como jefe de área, quiero recibir alertas sobre bienes que requieren mantenimiento o están próximos a depreciarse, para que pueda planificar acciones preventivas.

#### Criterios de Aceptación

1. CUANDO un bien cumpla el tiempo programado para mantenimiento ENTONCES el sistema DEBERÁ enviar una alerta automática
2. CUANDO un bien esté próximo a cumplir su vida útil ENTONCES el sistema DEBERÁ notificar con 6 meses de anticipación
3. CUANDO se configure una alerta ENTONCES el sistema DEBERÁ permitir personalizar los criterios y frecuencia
4. CUANDO se genere una alerta ENTONCES el sistema DEBERÁ registrar la notificación en el historial del bien

### Requisito 7

**Historia de Usuario:** Como administrador del sistema, quiero gestionar usuarios y permisos, para que pueda controlar el acceso y las funcionalidades disponibles según el rol de cada usuario.

#### Criterios de Aceptación

1. CUANDO se cree un usuario ENTONCES el sistema DEBERÁ asignar roles específicos (administrador, funcionario, auditor, consulta)
2. CUANDO un usuario intente acceder a una función ENTONCES el sistema DEBERÁ validar que tenga los permisos correspondientes
3. CUANDO se modifiquen permisos ENTONCES el sistema DEBERÁ aplicar los cambios inmediatamente en la siguiente sesión
4. CUANDO se desactive un usuario ENTONCES el sistema DEBERÁ mantener el historial pero impedir el acceso

### Requisito 8

**Historia de Usuario:** Como funcionario, quiero poder actualizar el estado de los bienes usando los códigos oficiales, para que pueda reportar cambios en las condiciones de los activos según la clasificación institucional.

#### Criterios de Aceptación

1. CUANDO se actualice el estado de un bien ENTONCES el sistema DEBERÁ mostrar las opciones: N-NUEVO, B-BUENO, R-REGULAR, M-MALO, E-RAEE, C-CHATARRA
2. CUANDO se cambie el estado a "M-MALO", "E-RAEE" o "C-CHATARRA" ENTONCES el sistema DEBERÁ solicitar observaciones obligatorias explicando el motivo
3. CUANDO se actualice el estado ENTONCES el sistema DEBERÁ registrar fecha, hora, usuario y notificar al administrador del patrimonio
4. CUANDO se consulte el historial ENTONCES el sistema DEBERÁ mostrar todos los cambios de estado con códigos y descripciones completas
### Requ
isito 9

**Historia de Usuario:** Como administrador, quiero importar datos de inventario desde archivos Excel, para que pueda migrar la información existente al nuevo sistema sin reingreso manual.

#### Criterios de Aceptación

1. CUANDO se seleccione un archivo Excel para importar ENTONCES el sistema DEBERÁ validar que contenga las columnas: CODIGO PATRIMONIAL, CODIGO INTERNO, DENOMINACION BIEN, ESTADO BIEN, MARCA, MODELO, COLOR, SERIE, DIMENSION, PLACA, MATRICULAS, NRO MOTOR, NRO CHASIS, OFICINA, OBSERVACIONES
2. CUANDO se procese la importación ENTONCES el sistema DEBERÁ verificar que no existan códigos patrimoniales duplicados
3. CUANDO se complete la importación ENTONCES el sistema DEBERÁ generar automáticamente códigos QR y URLs para todos los bienes importados
4. CUANDO ocurra un error en la importación ENTONCES el sistema DEBERÁ mostrar un reporte detallado de los registros con problemas

### Requisito 10

**Historia de Usuario:** Como administrador, quiero exportar el inventario completo a Excel, para que pueda generar respaldos y compartir información con otras dependencias.

#### Criterios de Aceptación

1. CUANDO se solicite exportar el inventario ENTONCES el sistema DEBERÁ generar un archivo Excel con las columnas: CODIGO PATRIMONIAL, CODIGO INTERNO, DENOMINACION BIEN, ESTADO BIEN, MARCA, MODELO, COLOR, SERIE, DIMENSION, PLACA, MATRICULAS, NRO MOTOR, NRO CHASIS, OFICINA, OBSERVACIONES
2. CUANDO se exporte la información ENTONCES el sistema DEBERÁ incluir las URLs generadas para cada código QR en una columna adicional
3. CUANDO se complete la exportación ENTONCES el sistema DEBERÁ permitir descargar el archivo con nombre que incluya fecha y hora
4. CUANDO se apliquen filtros antes de exportar ENTONCES el sistema DEBERÁ exportar solo los registros que cumplan los criterios especificados### 
Requisito 11

**Historia de Usuario:** Como funcionario, quiero buscar bienes por cualquier campo específico, para que pueda localizar rápidamente activos usando código patrimonial, placa, serie, matrícula u otros identificadores.

#### Criterios de Aceptación

1. CUANDO se ingrese un término de búsqueda ENTONCES el sistema DEBERÁ buscar en todos los campos: código patrimonial, código interno, denominación, marca, modelo, serie, placa, matrícula, número de motor y número de chasis
2. CUANDO se busque por código patrimonial ENTONCES el sistema DEBERÁ mostrar coincidencias exactas primero
3. CUANDO se busque por placa o matrícula ENTONCES el sistema DEBERÁ permitir búsquedas parciales y mostrar sugerencias
4. CUANDO se muestren resultados ENTONCES el sistema DEBERÁ resaltar los términos encontrados y mostrar el código QR correspondiente### Requi
sito 12

**Historia de Usuario:** Como administrador, quiero generar reportes estadísticos por estado de bienes, para que pueda conocer la distribución del patrimonio según su condición.

#### Criterios de Aceptación

1. CUANDO se genere un reporte estadístico ENTONCES el sistema DEBERÁ mostrar conteos por cada estado: N-NUEVO, B-BUENO, R-REGULAR, M-MALO, E-RAEE, C-CHATARRA
2. CUANDO se visualicen las estadísticas ENTONCES el sistema DEBERÁ mostrar gráficos de barras y circulares con porcentajes
3. CUANDO se filtre por fechas ENTONCES el sistema DEBERÁ mostrar la evolución de estados en el período seleccionado
4. CUANDO se exporte el reporte estadístico ENTONCES el sistema DEBERÁ incluir tanto los datos numéricos como los gráficos generados##
# Requisito 13

**Historia de Usuario:** Como administrador, quiero cargar y mantener actualizado el catálogo oficial de bienes, para que el sistema use las denominaciones y clasificaciones correctas según las normas del SBN.

#### Criterios de Aceptación

1. CUANDO se importe el catálogo desde Excel ENTONCES el sistema DEBERÁ validar las columnas: CATÁLOGO, Denominación, Grupo, Clase, Resolución, Estado
2. CUANDO se registre un nuevo bien ENTONCES el sistema DEBERÁ permitir seleccionar la denominación desde el catálogo oficial cargado
3. CUANDO se seleccione una denominación ENTONCES el sistema DEBERÁ autocompletar automáticamente el código de catálogo, grupo y clase correspondiente
4. CUANDO se actualice el catálogo ENTONCES el sistema DEBERÁ verificar que no existan códigos de catálogo duplicados y que las denominaciones sean únicas

### Requisito 14

**Historia de Usuario:** Como funcionario, quiero que el sistema valide que solo se registren bienes que existan en el catálogo oficial, para que se mantenga la consistencia con las normas del SBN.

#### Criterios de Aceptación

1. CUANDO se intente registrar un bien ENTONCES el sistema DEBERÁ validar que la denominación exista en el catálogo oficial
2. CUANDO se seleccione una denominación del catálogo ENTONCES el sistema DEBERÁ mostrar el código, grupo, clase y resolución correspondiente
3. CUANDO el catálogo tenga un bien con estado "EXCLUIDO" ENTONCES el sistema NO DEBERÁ permitir registrar nuevos bienes con esa denominación
4. CUANDO se busque una denominación ENTONCES el sistema DEBERÁ mostrar sugerencias basadas en el catálogo oficial con filtros por grupo y clase

### Requisito 15

**Historia de Usuario:** Como administrador, quiero generar reportes por grupo y clase de bienes según el catálogo oficial, para que pueda analizar el patrimonio por categorías normalizadas.

#### Criterios de Aceptación

1. CUANDO se genere un reporte por categorías ENTONCES el sistema DEBERÁ agrupar los bienes por Grupo (ej: 04-AGRÍCOLA Y PESQUERO) y Clase (ej: 22-EQUIPO)
2. CUANDO se visualice el reporte ENTONCES el sistema DEBERÁ mostrar totales por grupo, clase y estado de conservación
3. CUANDO se exporte el reporte ENTONCES el sistema DEBERÁ incluir los códigos de catálogo y resoluciones correspondientes
4. CUANDO se filtre por resolución ENTONCES el sistema DEBERÁ mostrar solo los bienes que correspondan a esa normativa específica### Re
quisito 16

**Historia de Usuario:** Como administrador, quiero mantener un maestro de oficinas actualizado, para que pueda asignar correctamente la ubicación de cada bien patrimonial.

#### Criterios de Aceptación

1. CUANDO acceda al módulo de oficinas ENTONCES el sistema DEBERÁ permitir crear, leer, actualizar y eliminar registros de oficinas
2. CUANDO se registre una nueva oficina ENTONCES el sistema DEBERÁ solicitar código de oficina, nombre, descripción, responsable y estado (activo/inactivo)
3. CUANDO se intente eliminar una oficina ENTONCES el sistema DEBERÁ validar que no tenga bienes asignados antes de permitir la eliminación
4. CUANDO se desactive una oficina ENTONCES el sistema DEBERÁ mantener el historial pero no permitir nuevas asignaciones

### Requisito 17

**Historia de Usuario:** Como administrador, quiero importar y actualizar el maestro de oficinas desde Excel, para que pueda mantener sincronizada la información con los sistemas administrativos de la institución.

#### Criterios de Aceptación

1. CUANDO se importe el archivo Excel de oficinas ENTONCES el sistema DEBERÁ validar la estructura de columnas requeridas
2. CUANDO se procese la importación ENTONCES el sistema DEBERÁ verificar que no existan códigos de oficina duplicados
3. CUANDO se actualice una oficina existente ENTONCES el sistema DEBERÁ mantener el historial de cambios y notificar a los responsables
4. CUANDO se complete la importación ENTONCES el sistema DEBERÁ generar un reporte de oficinas creadas, actualizadas y con errores

### Requisito 18

**Historia de Usuario:** Como funcionario, quiero generar reportes de inventario por oficina, para que pueda conocer qué bienes están asignados a cada dependencia.

#### Criterios de Aceptación

1. CUANDO se genere un reporte por oficina ENTONCES el sistema DEBERÁ mostrar todos los bienes asignados con sus detalles completos
2. CUANDO se seleccione una oficina específica ENTONCES el sistema DEBERÁ mostrar totales por estado de conservación y categoría de bienes
3. CUANDO se exporte el reporte ENTONCES el sistema DEBERÁ incluir información del responsable de la oficina y fecha de generación
4. CUANDO se apliquen filtros adicionales ENTONCES el sistema DEBERÁ combinar los criterios de oficina con otros filtros disponibles### Re
quisito 19

**Historia de Usuario:** Como usuario del sistema, quiero generar reportes con filtros avanzados, para que pueda obtener información específica según múltiples criterios de búsqueda.

#### Criterios de Aceptación

1. CUANDO acceda al módulo de reportes ENTONCES el sistema DEBERÁ permitir filtrar por: oficina, estado del bien, grupo/clase del catálogo, marca, modelo, rango de fechas, responsable
2. CUANDO se apliquen múltiples filtros ENTONCES el sistema DEBERÁ combinar todos los criterios usando operadores lógicos (Y/O)
3. CUANDO se genere el reporte filtrado ENTONCES el sistema DEBERÁ mostrar totales, subtotales y estadísticas de los resultados
4. CUANDO se guarde una configuración de filtros ENTONCES el sistema DEBERÁ permitir reutilizar esa configuración en futuras consultas

### Requisito 20

**Historia de Usuario:** Como técnico, quiero generar plantillas de stickers con códigos QR para impresión térmica, para que pueda imprimir etiquetas masivamente en impresoras Zebra.

#### Criterios de Aceptación

1. CUANDO se seleccionen bienes para imprimir ENTONCES el sistema DEBERÁ generar una plantilla con códigos QR, código patrimonial y denominación básica
2. CUANDO se configure la plantilla ENTONCES el sistema DEBERÁ permitir ajustar el tamaño del sticker, posición del QR y campos a mostrar
3. CUANDO se genere la plantilla ENTONCES el sistema DEBERÁ crear código ZPL (Zebra Programming Language) compatible con impresoras térmicas
4. CUANDO se descargue la plantilla ENTONCES el sistema DEBERÁ generar un archivo .zpl listo para enviar directamente a la impresora

### Requisito 21

**Historia de Usuario:** Como administrador, quiero generar reportes ejecutivos con gráficos y estadísticas, para que pueda presentar información resumida a la dirección.

#### Criterios de Aceptación

1. CUANDO se genere un reporte ejecutivo ENTONCES el sistema DEBERÁ incluir gráficos de distribución por estado, oficina y categoría
2. CUANDO se visualicen las estadísticas ENTONCES el sistema DEBERÁ mostrar indicadores clave como: total de bienes, valor estimado, bienes por depreciar
3. CUANDO se exporte el reporte ejecutivo ENTONCES el sistema DEBERÁ generar PDF con gráficos, tablas y análisis automático
4. CUANDO se programe un reporte ENTONCES el sistema DEBERÁ permitir generación automática y envío por correo electrónico

### Requisito 22

**Historia de Usuario:** Como usuario, quiero exportar reportes en múltiples formatos, para que pueda compartir la información según las necesidades específicas.

#### Criterios de Aceptación

1. CUANDO se complete un reporte ENTONCES el sistema DEBERÁ ofrecer exportación en formatos: Excel (.xlsx), PDF, CSV, y plantilla ZPL para stickers
2. CUANDO se exporte a Excel ENTONCES el sistema DEBERÁ mantener el formato, filtros aplicados y incluir gráficos si los hay
3. CUANDO se exporte a PDF ENTONCES el sistema DEBERÁ incluir encabezados institucionales, fecha de generación y firma digital
4. CUANDO se genere CSV ENTONCES el sistema DEBERÁ usar codificación UTF-8 para caracteres especiales y separadores configurables##
# Requisito 23

**Historia de Usuario:** Como usuario móvil, quiero escanear códigos QR desde mi celular para acceder rápidamente a la información de los bienes, para que pueda consultar y gestionar el patrimonio desde cualquier ubicación.

#### Criterios de Aceptación

1. CUANDO se escanee un código QR desde un dispositivo móvil ENTONCES el sistema DEBERÁ mostrar toda la información del bien en una interfaz optimizada para móviles
2. CUANDO el usuario esté logueado como administrador ENTONCES el sistema DEBERÁ mostrar botones de "Editar" y "Actualizar Estado" en la vista móvil
3. CUANDO se acceda sin estar logueado ENTONCES el sistema DEBERÁ mostrar solo información básica del bien (código, denominación, ubicación, estado)
4. CUANDO se edite desde móvil ENTONCES el sistema DEBERÁ permitir actualizar campos principales y registrar la ubicación GPS del dispositivo

### Requisito 24

**Historia de Usuario:** Como administrador móvil, quiero realizar inventarios de campo escaneando códigos QR, para que pueda verificar y actualizar el estado de los bienes directamente en su ubicación física.

#### Criterios de Aceptación

1. CUANDO se escanee un QR como administrador ENTONCES el sistema DEBERÁ permitir cambiar el estado del bien (N-NUEVO, B-BUENO, R-REGULAR, M-MALO, E-RAEE, C-CHATARRA)
2. CUANDO se actualice información desde móvil ENTONCES el sistema DEBERÁ registrar automáticamente la fecha, hora, usuario y coordenadas GPS
3. CUANDO se tome una foto del bien ENTONCES el sistema DEBERÁ permitir adjuntar la imagen al registro del bien
4. CUANDO se complete una actualización móvil ENTONCES el sistema DEBERÁ sincronizar inmediatamente con la base de datos central

### Requisito 25

**Historia de Usuario:** Como funcionario de campo, quiero que el sistema funcione offline en dispositivos móviles, para que pueda continuar trabajando aunque no tenga conexión a internet.

#### Criterios de Aceptación

1. CUANDO no haya conexión a internet ENTONCES el sistema DEBERÁ permitir consultar información de bienes previamente cargados
2. CUANDO se realicen cambios offline ENTONCES el sistema DEBERÁ almacenar las modificaciones localmente
3. CUANDO se recupere la conexión ENTONCES el sistema DEBERÁ sincronizar automáticamente todos los cambios pendientes
4. CUANDO ocurran conflictos de sincronización ENTONCES el sistema DEBERÁ mostrar las diferencias y permitir resolverlas manualmente