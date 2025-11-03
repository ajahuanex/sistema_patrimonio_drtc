export interface Catalogo {
  id: number
  codigo: string
  denominacion: string
  grupo: string
  clase: string
  resolucion: string
  estado: 'ACTIVO' | 'EXCLUIDO'
  created_at: string
  updated_at: string
}

export interface Oficina {
  id: number
  codigo: string
  nombre: string
  descripcion: string
  responsable: string
  cargo_responsable: string
  telefono: string
  email: string
  ubicacion: string
  estado: boolean
  created_at: string
  updated_at: string
}

export interface BienPatrimonial {
  id: number
  codigo_patrimonial: string
  codigo_interno: string
  catalogo: Catalogo
  oficina: Oficina
  estado_bien: 'N' | 'B' | 'R' | 'M' | 'E' | 'C'
  marca: string
  modelo: string
  color: string
  serie: string
  dimension: string
  placa: string
  matricula: string
  nro_motor: string
  nro_chasis: string
  observaciones: string
  qr_code: string
  url_qr: string
  fecha_adquisicion: string | null
  valor_adquisicion: string | null
  created_at: string
  updated_at: string
  created_by: number
}

export interface BienPatrimonialList {
  id: number
  codigo_patrimonial: string
  codigo_interno: string
  catalogo_denominacion: string
  oficina_nombre: string
  estado_bien: 'N' | 'B' | 'R' | 'M' | 'E' | 'C'
  marca: string
  modelo: string
  serie: string
  placa: string
  qr_code: string
  created_at: string
  updated_at: string
}

export interface HistorialEstado {
  id: number
  bien: number
  estado_anterior: 'N' | 'B' | 'R' | 'M' | 'E' | 'C'
  estado_nuevo: 'N' | 'B' | 'R' | 'M' | 'E' | 'C'
  observaciones: string
  fecha_cambio: string
  ubicacion_gps: string
  foto: string | null
  usuario: {
    id: number
    username: string
    first_name: string
    last_name: string
  }
}

export interface MovimientoBien {
  id: number
  bien: BienPatrimonial
  oficina_origen: Oficina
  oficina_destino: Oficina
  motivo: string
  observaciones: string
  fecha_movimiento: string
  confirmado: boolean
  fecha_confirmacion: string | null
  created_by: number
}

export interface BienPatrimonialForm {
  codigo_patrimonial: string
  codigo_interno: string
  catalogo: number
  oficina: number
  estado_bien: 'N' | 'B' | 'R' | 'M' | 'E' | 'C'
  marca: string
  modelo: string
  color: string
  serie: string
  dimension: string
  placa: string
  matricula: string
  nro_motor: string
  nro_chasis: string
  observaciones: string
  fecha_adquisicion: string | null
  valor_adquisicion: string | null
}

export interface InventoryFilters {
  search?: string
  oficina?: number
  estado_bien?: string
  catalogo?: number
  marca?: string
  modelo?: string
  fecha_desde?: string
  fecha_hasta?: string
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export const ESTADOS_BIEN = {
  'N': 'Nuevo',
  'B': 'Bueno', 
  'R': 'Regular',
  'M': 'Malo',
  'E': 'RAEE',
  'C': 'Chatarra'
} as const

export const ESTADOS_BIEN_OPTIONS = Object.entries(ESTADOS_BIEN).map(([value, label]) => ({
  value,
  label
}))