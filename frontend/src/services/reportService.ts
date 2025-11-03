import api from './api'

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

export interface ReportStatistics {
  total_bienes: number
  por_estado: Array<{
    estado_bien: string
    total: number
    porcentaje: number
  }>
  por_oficina: Array<{
    oficina__nombre: string
    total: number
    porcentaje: number
  }>
  por_grupo: Array<{
    catalogo__grupo: string
    total: number
    porcentaje: number
  }>
  valor_total_estimado?: number
  bienes_sin_mantenimiento?: number
  alertas_depreciacion?: number
}

export interface ReportPreview {
  total_resultados: number
  estadisticas: ReportStatistics
  mensaje: string
}

export interface SavedFilter {
  id: number
  nombre: string
  descripcion?: string
  parametros: FilterParams
  es_publico: boolean
  fecha_creacion: string
  veces_usado: number
}

export interface GeneratedReport {
  id: number
  nombre: string
  tipo_reporte: string
  formato: string
  estado: 'PENDIENTE' | 'PROCESANDO' | 'COMPLETADO' | 'ERROR'
  fecha_inicio: string
  fecha_fin?: string
  total_registros?: number
  archivo_url?: string
  error_mensaje?: string
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

class ReportService {
  // Filtros y vista previa
  async getFilterPreview(filters: FilterParams): Promise<ReportPreview> {
    const response = await api.post('/api/reportes/vista-previa/', filters)
    return response.data
  }

  async getStatistics(filters?: FilterParams): Promise<ReportStatistics> {
    const response = await api.get('/api/reportes/estadisticas/', {
      params: filters
    })
    return response.data
  }

  // Configuraciones de filtros guardadas
  async getSavedFilters(): Promise<SavedFilter[]> {
    const response = await api.get('/api/reportes/configuraciones/')
    return response.data
  }

  async saveFilter(filter: Omit<SavedFilter, 'id' | 'fecha_creacion' | 'veces_usado'>): Promise<SavedFilter> {
    const response = await api.post('/api/reportes/configuraciones/', filter)
    return response.data
  }

  async updateFilter(id: number, filter: Partial<SavedFilter>): Promise<SavedFilter> {
    const response = await api.put(`/api/reportes/configuraciones/${id}/`, filter)
    return response.data
  }

  async deleteFilter(id: number): Promise<void> {
    await api.delete(`/api/reportes/configuraciones/${id}/`)
  }

  async loadFilter(id: number): Promise<SavedFilter> {
    const response = await api.get(`/api/reportes/configuraciones/${id}/`)
    return response.data
  }

  // Generación de reportes
  async generateReport(params: ReportGenerationParams): Promise<GeneratedReport> {
    const response = await api.post('/api/reportes/generar/', params)
    return response.data
  }

  async getMyReports(): Promise<GeneratedReport[]> {
    const response = await api.get('/api/reportes/mis-reportes/')
    return response.data
  }

  async downloadReport(reportId: number): Promise<Blob> {
    const response = await api.get(`/api/reportes/descargar/${reportId}/`, {
      responseType: 'blob'
    })
    return response.data
  }

  async deleteReport(reportId: number): Promise<void> {
    await api.delete(`/api/reportes/${reportId}/`)
  }

  // APIs de autocompletado
  async getBrandSuggestions(query: string): Promise<string[]> {
    const response = await api.get('/api/reportes/marcas-autocomplete/', {
      params: { q: query }
    })
    return response.data.results.map((item: any) => item.text)
  }

  async getModelSuggestions(query: string, brand?: string): Promise<string[]> {
    const response = await api.get('/api/reportes/modelos-autocomplete/', {
      params: { q: query, marca: brand }
    })
    return response.data.results.map((item: any) => item.text)
  }

  async getClassesByGroup(group: string): Promise<string[]> {
    const response = await api.get('/api/reportes/clases-por-grupo/', {
      params: { grupo: group }
    })
    return response.data.clases.map((item: any) => item.text)
  }

  // Exportación directa
  async exportToExcel(filters: FilterParams): Promise<Blob> {
    const response = await api.post('/api/reportes/exportar-excel/', filters, {
      responseType: 'blob'
    })
    return response.data
  }

  async exportToPDF(filters: FilterParams): Promise<Blob> {
    const response = await api.post('/api/reportes/exportar-pdf/', filters, {
      responseType: 'blob'
    })
    return response.data
  }

  async exportToCSV(filters: FilterParams): Promise<Blob> {
    const response = await api.post('/api/reportes/exportar-csv/', filters, {
      responseType: 'blob'
    })
    return response.data
  }

  // Stickers ZPL
  async generateStickers(bienIds: number[], config: any): Promise<Blob> {
    const response = await api.post('/api/reportes/generar-stickers/', {
      bienes_seleccionados: bienIds,
      configuracion: config
    }, {
      responseType: 'blob'
    })
    return response.data
  }
}

export const reportService = new ReportService()
export default reportService