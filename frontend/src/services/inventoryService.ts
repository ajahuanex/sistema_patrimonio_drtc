import axios from 'axios'
import {
  BienPatrimonial,
  BienPatrimonialList,
  BienPatrimonialForm,
  HistorialEstado,
  MovimientoBien,
  Catalogo,
  Oficina,
  InventoryFilters,
  PaginatedResponse
} from '../types/inventory'

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api'

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken
          })
          const newToken = response.data.access
          localStorage.setItem('access_token', newToken)
          
          // Retry original request
          error.config.headers.Authorization = `Bearer ${newToken}`
          return api.request(error.config)
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export const inventoryService = {
  // Bienes Patrimoniales
  async getBienes(filters?: InventoryFilters, page = 1, pageSize = 25): Promise<PaginatedResponse<BienPatrimonialList>> {
    const params = new URLSearchParams()
    
    if (filters?.search) params.append('search', filters.search)
    if (filters?.oficina) params.append('oficina', filters.oficina.toString())
    if (filters?.estado_bien) params.append('estado_bien', filters.estado_bien)
    if (filters?.catalogo) params.append('catalogo', filters.catalogo.toString())
    if (filters?.marca) params.append('marca', filters.marca)
    if (filters?.modelo) params.append('modelo', filters.modelo)
    if (filters?.fecha_desde) params.append('fecha_desde', filters.fecha_desde)
    if (filters?.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta)
    
    params.append('page', page.toString())
    params.append('page_size', pageSize.toString())
    
    const response = await api.get(`/bienes/?${params.toString()}`)
    return response.data
  },

  async getBien(id: number): Promise<BienPatrimonial> {
    const response = await api.get(`/bienes/${id}/`)
    return response.data
  },

  async createBien(data: BienPatrimonialForm): Promise<BienPatrimonial> {
    const response = await api.post('/bienes/', data)
    return response.data
  },

  async updateBien(id: number, data: Partial<BienPatrimonialForm>): Promise<BienPatrimonial> {
    const response = await api.patch(`/bienes/${id}/`, data)
    return response.data
  },

  async deleteBien(id: number): Promise<void> {
    await api.delete(`/bienes/${id}/`)
  },

  async getBienByQR(qrCode: string): Promise<BienPatrimonial> {
    const response = await api.get(`/bienes/qr/${qrCode}/`)
    return response.data
  },

  // Historial de Estados
  async getHistorialEstado(bienId: number): Promise<HistorialEstado[]> {
    const response = await api.get(`/bienes/${bienId}/historial-estado/`)
    return response.data
  },

  async updateEstado(bienId: number, data: {
    estado_bien: string
    observaciones?: string
    ubicacion_gps?: string
    foto?: File
  }): Promise<HistorialEstado> {
    const formData = new FormData()
    formData.append('estado_bien', data.estado_bien)
    if (data.observaciones) formData.append('observaciones', data.observaciones)
    if (data.ubicacion_gps) formData.append('ubicacion_gps', data.ubicacion_gps)
    if (data.foto) formData.append('foto', data.foto)

    const response = await api.post(`/bienes/${bienId}/actualizar-estado/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Movimientos
  async getMovimientos(bienId: number): Promise<MovimientoBien[]> {
    const response = await api.get(`/bienes/${bienId}/movimientos/`)
    return response.data
  },

  async createMovimiento(data: {
    bien: number
    oficina_destino: number
    motivo: string
    observaciones?: string
  }): Promise<MovimientoBien> {
    const response = await api.post('/movimientos/', data)
    return response.data
  },

  async confirmarMovimiento(movimientoId: number): Promise<MovimientoBien> {
    const response = await api.post(`/movimientos/${movimientoId}/confirmar/`)
    return response.data
  },

  // Catálogo
  async getCatalogos(search?: string): Promise<Catalogo[]> {
    const params = search ? `?search=${encodeURIComponent(search)}` : ''
    const response = await api.get(`/catalogos/${params}`)
    return response.data.results || response.data
  },

  async getCatalogo(id: number): Promise<Catalogo> {
    const response = await api.get(`/catalogos/${id}/`)
    return response.data
  },

  // Oficinas
  async getOficinas(search?: string): Promise<Oficina[]> {
    const params = search ? `?search=${encodeURIComponent(search)}` : ''
    const response = await api.get(`/oficinas/${params}`)
    return response.data.results || response.data
  },

  async getOficina(id: number): Promise<Oficina> {
    const response = await api.get(`/oficinas/${id}/`)
    return response.data
  },

  // Búsqueda avanzada
  async buscarBienes(query: string): Promise<BienPatrimonialList[]> {
    const response = await api.get(`/bienes/buscar/?q=${encodeURIComponent(query)}`)
    return response.data
  },

  // Estadísticas
  async getEstadisticas(): Promise<{
    total_bienes: number
    por_estado: Array<{ estado: string; total: number }>
    por_oficina: Array<{ oficina: string; total: number }>
    bienes_nuevos_mes: number
    requieren_atencion: number
  }> {
    const response = await api.get('/bienes/estadisticas/')
    return response.data
  },

  // Validaciones
  async validarCodigoPatrimonial(codigo: string, excludeId?: number): Promise<{ disponible: boolean }> {
    const params = new URLSearchParams()
    params.append('codigo', codigo)
    if (excludeId) params.append('exclude_id', excludeId.toString())
    
    const response = await api.get(`/bienes/validar-codigo/?${params.toString()}`)
    return response.data
  },

  // Exportar
  async exportarBienes(filters?: InventoryFilters, formato: 'excel' | 'pdf' | 'csv' = 'excel'): Promise<Blob> {
    const params = new URLSearchParams()
    
    if (filters?.search) params.append('search', filters.search)
    if (filters?.oficina) params.append('oficina', filters.oficina.toString())
    if (filters?.estado_bien) params.append('estado_bien', filters.estado_bien)
    if (filters?.catalogo) params.append('catalogo', filters.catalogo.toString())
    if (filters?.marca) params.append('marca', filters.marca)
    if (filters?.modelo) params.append('modelo', filters.modelo)
    if (filters?.fecha_desde) params.append('fecha_desde', filters.fecha_desde)
    if (filters?.fecha_hasta) params.append('fecha_hasta', filters.fecha_hasta)
    
    params.append('formato', formato)
    
    const response = await api.get(`/bienes/exportar/?${params.toString()}`, {
      responseType: 'blob'
    })
    
    return response.data
  }
}

export default inventoryService