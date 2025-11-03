import React, { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Typography,
  Button,
  Paper,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
} from '@mui/material'
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  GetApp as ExportIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  QrCode as QrCodeIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { GridColDef, GridRowId } from '@mui/x-data-grid'
import DataTable from '../../components/Common/DataTable'
import inventoryService from '../../services/inventoryService'
import {
  BienPatrimonialList,
  InventoryFilters,
  Oficina,
  Catalogo,
  ESTADOS_BIEN,
  PaginatedResponse
} from '../../types/inventory'

const InventoryList: React.FC = () => {
  const navigate = useNavigate()
  
  // State
  const [bienes, setBienes] = useState<BienPatrimonialList[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  
  // Filters
  const [filters, setFilters] = useState<InventoryFilters>({})
  const [showFilters, setShowFilters] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  
  // Options for filters
  const [oficinas, setOficinas] = useState<Oficina[]>([])
  const [catalogos, setCatalogos] = useState<Catalogo[]>([])

  // Load initial data
  useEffect(() => {
    loadOficinas()
    loadCatalogos()
  }, [])

  // Load bienes when filters or pagination change
  useEffect(() => {
    loadBienes()
  }, [filters, page, pageSize])

  const loadBienes = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const response: PaginatedResponse<BienPatrimonialList> = await inventoryService.getBienes(
        filters,
        page,
        pageSize
      )
      
      setBienes(response.results)
      setTotalCount(response.count)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar los bienes')
      console.error('Error loading bienes:', err)
    } finally {
      setLoading(false)
    }
  }, [filters, page, pageSize])

  const loadOficinas = async () => {
    try {
      const data = await inventoryService.getOficinas()
      setOficinas(data)
    } catch (err) {
      console.error('Error loading oficinas:', err)
    }
  }

  const loadCatalogos = async () => {
    try {
      const data = await inventoryService.getCatalogos()
      setCatalogos(data)
    } catch (err) {
      console.error('Error loading catalogos:', err)
    }
  }

  const handleSearch = () => {
    setFilters(prev => ({ ...prev, search: searchTerm }))
    setPage(1)
  }

  const handleFilterChange = (key: keyof InventoryFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPage(1)
  }

  const clearFilters = () => {
    setFilters({})
    setSearchTerm('')
    setPage(1)
  }

  const handleView = (id: GridRowId) => {
    navigate(`/inventory/${id}`)
  }

  const handleEdit = (id: GridRowId) => {
    navigate(`/inventory/${id}/edit`)
  }

  const handleExport = async (format: 'excel' | 'pdf' | 'csv' = 'excel') => {
    try {
      const blob = await inventoryService.exportarBienes(filters, format)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `inventario_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : format}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Error exporting:', err)
    }
  }

  const columns: GridColDef[] = [
    {
      field: 'codigo_patrimonial',
      headerName: 'Código Patrimonial',
      width: 150,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
            {params.value}
          </Typography>
          {params.row.qr_code && (
            <Tooltip title="Tiene código QR">
              <QrCodeIcon fontSize="small" color="primary" />
            </Tooltip>
          )}
        </Box>
      ),
    },
    {
      field: 'catalogo_denominacion',
      headerName: 'Denominación',
      width: 300,
      renderCell: (params) => (
        <Tooltip title={params.value}>
          <Typography variant="body2" noWrap>
            {params.value}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'estado_bien',
      headerName: 'Estado',
      width: 120,
      renderCell: (params) => {
        const estado = params.value as keyof typeof ESTADOS_BIEN
        const color = {
          'N': 'success',
          'B': 'primary',
          'R': 'warning',
          'M': 'error',
          'E': 'secondary',
          'C': 'default'
        }[estado] as any
        
        return (
          <Chip
            label={ESTADOS_BIEN[estado]}
            color={color}
            size="small"
          />
        )
      },
    },
    {
      field: 'marca',
      headerName: 'Marca',
      width: 120,
    },
    {
      field: 'modelo',
      headerName: 'Modelo',
      width: 120,
    },
    {
      field: 'serie',
      headerName: 'Serie',
      width: 120,
    },
    {
      field: 'placa',
      headerName: 'Placa',
      width: 100,
      renderCell: (params) => (
        params.value ? (
          <Chip label={params.value} size="small" variant="outlined" />
        ) : null
      ),
    },
    {
      field: 'oficina_nombre',
      headerName: 'Oficina',
      width: 200,
      renderCell: (params) => (
        <Tooltip title={params.value}>
          <Typography variant="body2" noWrap>
            {params.value}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'created_at',
      headerName: 'Fecha Registro',
      width: 130,
      renderCell: (params) => (
        <Typography variant="body2">
          {new Date(params.value).toLocaleDateString()}
        </Typography>
      ),
    },
  ]

  const activeFiltersCount = Object.values(filters).filter(Boolean).length

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom>
            Inventario
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Gestión de bienes patrimoniales ({totalCount} bienes)
          </Typography>
        </div>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<ExportIcon />}
            onClick={() => handleExport('excel')}
          >
            Exportar
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/inventory/new')}
          >
            Nuevo Bien
          </Button>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Buscar por código, denominación, marca, modelo, serie, placa..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                endAdornment: (
                  <IconButton onClick={handleSearch}>
                    <SearchIcon />
                  </IconButton>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button
                variant={showFilters ? 'contained' : 'outlined'}
                startIcon={<FilterIcon />}
                onClick={() => setShowFilters(!showFilters)}
              >
                Filtros {activeFiltersCount > 0 && `(${activeFiltersCount})`}
              </Button>
              {activeFiltersCount > 0 && (
                <Button
                  variant="outlined"
                  startIcon={<ClearIcon />}
                  onClick={clearFilters}
                >
                  Limpiar
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>

        {/* Advanced Filters */}
        {showFilters && (
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Oficina</InputLabel>
                  <Select
                    value={filters.oficina || ''}
                    onChange={(e) => handleFilterChange('oficina', e.target.value || undefined)}
                    label="Oficina"
                  >
                    <MenuItem value="">Todas</MenuItem>
                    {oficinas.map((oficina) => (
                      <MenuItem key={oficina.id} value={oficina.id}>
                        {oficina.nombre}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Estado</InputLabel>
                  <Select
                    value={filters.estado_bien || ''}
                    onChange={(e) => handleFilterChange('estado_bien', e.target.value || undefined)}
                    label="Estado"
                  >
                    <MenuItem value="">Todos</MenuItem>
                    {Object.entries(ESTADOS_BIEN).map(([value, label]) => (
                      <MenuItem key={value} value={value}>
                        {label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  size="small"
                  label="Marca"
                  value={filters.marca || ''}
                  onChange={(e) => handleFilterChange('marca', e.target.value || undefined)}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  size="small"
                  label="Modelo"
                  value={filters.modelo || ''}
                  onChange={(e) => handleFilterChange('modelo', e.target.value || undefined)}
                />
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Data Table */}
      <DataTable
        rows={bienes}
        columns={columns}
        loading={loading}
        onView={handleView}
        onEdit={handleEdit}
        height={600}
      />
    </Box>
  )
}

export default InventoryList