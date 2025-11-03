import axios from 'axios'
import { Oficina, PaginatedResponse } from '../types/inventory'

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

export interface OfficeFilters {
  search?: string
  estado?: boolean
  responsable?: string
}

export interface OfficeForm {
  codigo: string
  nombre: string
  descripcion: string
  responsable: string
  cargo_responsable: string
  telefono: string
  email: string
  ubicacion: string
  estado: boolean
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

export const officeService = {
  // CRUD Operations
  async getOficinas(filters?: OfficeFilters, page = 1, pageSize = 25): Promise<PaginatedResponse<Oficina>> {
    const params = new URLSearchParams()
    
    if (filters?.search) params.append('search', filters.search)
    if (filters?.estado !== undefined) params.append('estado', filters.estado.toString())
    if (filters?.responsable) params.append('responsable', filters.responsable)
    
    params.append('page', page.toString())
    params.append('page_size', pageSize.toString())
    
    const response = await api.get(`/oficinas/?${params.toString()}`)
    return response.data
  },

  async getOficina(id: number): Promise<Oficina> {
    const response = await api.get(`/oficinas/${id}/`)
    return response.data
  },

  async createOficina(data: OfficeForm): Promise<Oficina> {
    const response = await api.post('/oficinas/', data)
    return response.data
  },

  async updateOficina(id: number, data: Partial<OfficeForm>): Promise<Oficina> {
    const response = await api.patch(`/oficinas/${id}/`, data)
    return response.data
  },

  async deleteOficina(id: number): Promise<void> {
    await api.delete(`/oficinas/${id}/`)
  },

  // Search and validation
  async searchOficinas(query: string): Promise<Oficina[]> {
    const response = await api.get(`/oficinas/search/?q=${encodeURIComponent(query)}`)
    return response.data
  },

  async validarCodigo(codigo: string, excludeId?: number): Promise<{ disponible: boolean }> {
    const params = new URLSearchParams()
    params.append('codigo', codigo)
    if (excludeId) params.append('exclude_id', excludeId.toString())
    
    const response = await api.get(`/oficinas/validar-codigo/?${params.toString()}`)
    return response.data
  },

  // Import/Export
  async importarExcel(file: File): Promise<ImportResult> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await api.post('/oficinas/importar/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async exportarExcel(filters?: OfficeFilters): Promise<Blob> {
    const params = new URLSearchParams()
    
    if (filters?.search) params.append('search', filters.search)
    if (filters?.estado !== undefined) params.append('estado', filters.estado.toString())
    if (filters?.responsable) params.append('responsable', filters.responsable)
    
    const response = await api.get(`/oficinas/exportar/?${params.toString()}`, {
      responseType: 'blob'
    })
    
    return response.data
  },

  // Statistics
  async getEstadisticas(): Promise<{
    total: number
    activas: number
    inactivas: number
    con_bienes: number
    sin_bienes: number
  }> {
    const response = await api.get('/oficinas/estadisticas/')
    return response.data
  },

  // Check if office can be deleted (has no assigned assets)
  async puedeEliminar(id: number): Promise<{ puede_eliminar: boolean; bienes_asignados: number }> {
    const response = await api.get(`/oficinas/${id}/puede-eliminar/`)
    return response.data
  }
}

export default officeService