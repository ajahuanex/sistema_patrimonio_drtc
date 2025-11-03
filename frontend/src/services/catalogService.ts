import axios from 'axios'
import { Catalogo, PaginatedResponse } from '../types/inventory'

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

export interface CatalogFilters {
  search?: string
  grupo?: string
  clase?: string
  estado?: 'ACTIVO' | 'EXCLUIDO'
}

export interface CatalogForm {
  codigo: string
  denominacion: string
  grupo: string
  clase: string
  resolucion: string
  estado: 'ACTIVO' | 'EXCLUIDO'
}

export interface ImportResult {
  success: boolean
  message: string
  created: number
  updated: number
  errors: Array<{
    row: number
    field: string
    message: string
  }>
}

export const catalogService = {
  // CRUD Operations
  async getCatalogos(filters?: CatalogFilters, page = 1, pageSize = 25): Promise<PaginatedResponse<Catalogo>> {
    const params = new URLSearchParams()
    
    if (filters?.search) params.append('search', filters.search)
    if (filters?.grupo) params.append('grupo', filters.grupo)
    if (filters?.clase) params.append('clase', filters.clase)
    if (filters?.estado) params.append('estado', filters.estado)
    
    params.append('page', page.toString())
    params.append('page_size', pageSize.toString())
    
    const response = await api.get(`/catalogos/?${params.toString()}`)
    return response.data
  },

  async getCatalogo(id: number): Promise<Catalogo> {
    const response = await api.get(`/catalogos/${id}/`)
    return response.data
  },

  async createCatalogo(data: CatalogForm): Promise<Catalogo> {
    const response = await api.post('/catalogos/', data)
    return response.data
  },

  async updateCatalogo(id: number, data: Partial<CatalogForm>): Promise<Catalogo> {
    const response = await api.patch(`/catalogos/${id}/`, data)
    return response.data
  },

  async deleteCatalogo(id: number): Promise<void> {
    await api.delete(`/catalogos/${id}/`)
  },

  // Search and validation
  async searchCatalogos(query: string): Promise<Catalogo[]> {
    const response = await api.get(`/catalogos/search/?q=${encodeURIComponent(query)}`)
    return response.data
  },

  async validarCodigo(codigo: string, excludeId?: number): Promise<{ disponible: boolean }> {
    const params = new URLSearchParams()
    params.append('codigo', codigo)
    if (excludeId) params.append('exclude_id', excludeId.toString())
    
    const response = await api.get(`/catalogos/validar-codigo/?${params.toString()}`)
    return response.data
  },

  async validarDenominacion(denominacion: string, excludeId?: number): Promise<{ disponible: boolean }> {
    const params = new URLSearchParams()
    params.append('denominacion', denominacion)
    if (excludeId) params.append('exclude_id', excludeId.toString())
    
    const response = await api.get(`/catalogos/validar-denominacion/?${params.toString()}`)
    return response.data
  },

  // Import/Export
  async importarExcel(file: File): Promise<ImportResult> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/catalogos/importar/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async exportarExcel(filters?: CatalogFilters): Promise<Blob> {
    const params = new URLSearchParams()
    
    if (filters?.search) params.append('search', filters.search)
    if (filters?.grupo) params.append('grupo', filters.grupo)
    if (filters?.clase) params.append('clase', filters.clase)
    if (filters?.estado) params.append('estado', filters.estado)
    
    const response = await api.get(`/catalogos/exportar/?${params.toString()}`, {
      responseType: 'blob'
    })
    
    return response.data
  },

  // Statistics
  async getEstadisticas(): Promise<{
    total: number
    activos: number
    excluidos: number
    por_grupo: Array<{ grupo: string; total: number }>
    por_clase: Array<{ clase: string; total: number }>
  }> {
    const response = await api.get('/catalogos/estadisticas/')
    return response.data
  },

  // Get unique values for filters
  async getGrupos(): Promise<string[]> {
    const response = await api.get('/catalogos/grupos/')
    return response.data
  },

  async getClases(grupo?: string): Promise<string[]> {
    const params = grupo ? `?grupo=${encodeURIComponent(grupo)}` : ''
    const response = await api.get(`/catalogos/clases/${params}`)
    return response.data
  }
}

export default catalogService