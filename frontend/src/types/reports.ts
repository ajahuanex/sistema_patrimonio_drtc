export interface FilterParams {
  oficinas?: string[]
  estados_bien?: string[]
  grupos?: string[]
  clases?: string[]
  marcas?: string[]
  modelos?: string[]
  fecha_registro_desde?: string
  fecha_registro_hasta?: string
  fecha_adquisicion_desde?: string
  fecha_adquisicion_hasta?: string
  valor_minimo?: number
  valor_maximo?: number
  buscar_texto?: string
}

export interface ChartData {
  name: string
  value: number
  percentage: number
  color?: string
}

export interface ReportStatistics {
  total_bienes: number
  por_estado: ChartData[]
  por_oficina: ChartData[]
  por_grupo: ChartData[]
  valor_total_estimado?: number
  bienes_sin_mantenimiento?: number
  alertas_depreciacion?: number
}

export interface ReportPreview {
  total_resultados: number
  estadisticas: ReportStatistics
  mensaje: string
  success: boolean
}

export interface SavedFilter {
  id: number
  nombre: string
  descripcion?: string
  parametros: FilterParams
  es_publico: boolean
  fecha_creacion: string
  veces_usado: number
  usuario?: string
}

export interface GeneratedReport {
  id: number
  nombre: string
  tipo_reporte: 'INVENTARIO' | 'ESTADISTICO' | 'EJECUTIVO' | 'STICKERS'
  formato: 'EXCEL' | 'PDF' | 'CSV' | 'ZPL'
  estado: 'PENDIENTE' | 'PROCESANDO' | 'COMPLETADO' | 'ERROR'
  fecha_inicio: string
  fecha_fin?: string
  total_registros?: number
  archivo_url?: string
  error_mensaje?: string
  progreso?: number
}

export interface ReportGenerationParams {
  nombre_reporte: string
  tipo_reporte: 'INVENTARIO' | 'ESTADISTICO' | 'EJECUTIVO' | 'STICKERS'
  formato: 'EXCEL' | 'PDF' | 'CSV' | 'ZPL'
  incluir_graficos?: boolean
  incluir_historial?: boolean
  agrupar_por?: string
  filtros: FilterParams
}

export interface FilterOption {
  value: string
  label: string
  count?: number
}

export interface FilterGroup {
  label: string
  options: FilterOption[]
}

export const ESTADOS_BIEN: FilterOption[] = [
  { value: 'N', label: 'Nuevo' },
  { value: 'B', label: 'Bueno' },
  { value: 'R', label: 'Regular' },
  { value: 'M', label: 'Malo' },
  { value: 'E', label: 'RAEE' },
  { value: 'C', label: 'Chatarra' }
]

export const TIPOS_REPORTE: FilterOption[] = [
  { value: 'INVENTARIO', label: 'Inventario General' },
  { value: 'ESTADISTICO', label: 'Reporte Estadístico' },
  { value: 'EJECUTIVO', label: 'Reporte Ejecutivo' },
  { value: 'STICKERS', label: 'Stickers ZPL' }
]

export const FORMATOS_EXPORTACION: FilterOption[] = [
  { value: 'EXCEL', label: 'Excel (.xlsx)' },
  { value: 'PDF', label: 'PDF' },
  { value: 'CSV', label: 'CSV' },
  { value: 'ZPL', label: 'ZPL (Stickers)' }
]

export const CHART_COLORS = [
  '#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00',
  '#ff0000', '#00ffff', '#ff00ff', '#ffff00', '#0000ff'
]