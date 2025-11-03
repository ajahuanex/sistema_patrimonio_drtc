# Frontend - Sistema de Registro de Patrimonio

Este es el frontend React del Sistema de Registro de Patrimonio para la Dirección Regional de Transportes y Comunicaciones de Puno.

## Tecnologías Utilizadas

- **React 18** - Biblioteca de interfaz de usuario
- **TypeScript** - Tipado estático
- **Material-UI (MUI)** - Componentes de interfaz
- **React Router** - Enrutamiento
- **React Query** - Gestión de estado del servidor
- **React Hook Form** - Manejo de formularios
- **Axios** - Cliente HTTP
- **Vite** - Herramienta de construcción

## Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/          # Componentes reutilizables
│   │   ├── Common/         # Componentes comunes
│   │   └── Layout/         # Componentes de layout
│   ├── contexts/           # Contextos de React
│   ├── pages/              # Páginas de la aplicación
│   │   ├── Inventory/      # Módulo de inventario
│   │   ├── Catalog/        # Módulo de catálogo
│   │   ├── Office/         # Módulo de oficinas
│   │   └── Reports/        # Módulo de reportes
│   ├── services/           # Servicios de API
│   ├── App.tsx            # Componente principal
│   ├── main.tsx           # Punto de entrada
│   └── theme.ts           # Configuración del tema
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Instalación y Configuración

### Prerrequisitos

- Node.js 18 o superior
- npm o yarn

### Instalación

1. Navegar al directorio frontend:
```bash
cd frontend
```

2. Instalar dependencias:
```bash
npm install
```

### Desarrollo

Para ejecutar el servidor de desarrollo:

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

### Construcción para Producción

Para construir la aplicación para producción:

```bash
npm run build
```

Los archivos construidos se generarán en `../static/frontend/`

## Características Implementadas

### ✅ Tarea 7.1 - Componentes Base y Layout Principal

- **Layout Responsivo**: Navegación lateral que se adapta a dispositivos móviles
- **Material-UI**: Configuración completa con tema personalizado
- **Componentes Reutilizables**:
  - `DataTable`: Tabla de datos con filtros y acciones
  - `FormField`: Campo de formulario con validación
  - `LoadingSpinner`: Indicador de carga
  - `ConfirmDialog`: Diálogo de confirmación
- **Navegación**: Menú lateral con rutas principales
- **Autenticación**: Contexto y servicios de autenticación
- **Dashboard**: Página principal con estadísticas y acciones rápidas

### Funcionalidades del Layout

1. **Navegación Responsiva**:
   - Menú lateral fijo en desktop
   - Menú desplegable en móviles
   - Indicadores visuales de página activa

2. **Barra Superior**:
   - Título de la aplicación
   - Menú de usuario con opciones
   - Botón de menú para móviles

3. **Dashboard**:
   - Tarjetas de estadísticas
   - Acciones rápidas
   - Actividad reciente

## Próximas Tareas

- **Tarea 7.2**: Implementar módulo de gestión de inventario
- **Tarea 7.3**: Desarrollar módulo de gestión de catálogo y oficinas  
- **Tarea 7.4**: Crear módulo de reportes con interfaz gráfica

## Configuración del Proxy

El archivo `vite.config.ts` está configurado para hacer proxy de las peticiones API al backend Django en `http://localhost:8000`.

## Integración con Django

Los archivos construidos se generan en `../static/frontend/` para ser servidos por Django en producción.

## Scripts Disponibles

- `npm run dev` - Servidor de desarrollo
- `npm run build` - Construcción para producción
- `npm run preview` - Vista previa de la construcción
- `npm run lint` - Linter de código