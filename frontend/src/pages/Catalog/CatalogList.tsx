import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  Grid,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  FileUpload as ImportIcon,
  FileDownload as ExportIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material'
import DataTable from '../../components/Common/DataTable'
import FormField from '../../components/Common/FormField'
import { catalogService, CatalogFilters, CatalogForm } from '../../services/catalogService'
import { Catalogo } from '../../types/inventory'

const CatalogList: React.FC = () => {
  const [catalogos, setCatalogos] = useState<Catalogo[]>([])
  const [loading, setLoading] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [filters, setFilters] = useState<CatalogFilters>({})
  const [grupos, setGrupos] = useState<string[]>([])
  const [clases, setClases] = useState<string[]>([])
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingCatalog, setEditingCatalog] = useState<Catalogo | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [catalogToDelete, setCatalogToDelete] = useState<Catalogo | null>(null)
  
  // Form state
  const [formData, setFormData] = useState<CatalogForm>({
    codigo: '',
    denominacion: '',
    grupo: '',
    clase: '',
    resolucion: '',
    estado: 'ACTIVO'
  })
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  
  // Notification state
  const [notification, setNotification] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error' | 'warning' | 'info'
  }>({
    open: false,
    message: '',
    severity: 'success'
  })

  // Load data
  useEffect(() => {
    loadCatalogos()
    loadGrupos()
  }, [page, pageSize, filters])

  useEffect(() => {
    if (filters.grupo) {
      loadClases(filters.grupo)
    } else {
      setClases([])
    }
  }, [filters.grupo])

  const loadCatalogos = async () => {
    try {
      setLoading(true)
      const response = await catalogService.getCatalogos(filters, page, pageSize)
      setCatalogos(response.results)
      setTotalCount(response.count)
    } catch (error) {
      showNotification('Error al cargar el catálogo', 'error')
    } finally {
      setLoading(false)
    }
  }

  const loadGrupos = async () => {
    try {
      const grupos = await catalogService.getGrupos()
      setGrupos(grupos)
    } catch (error) {
      console.error('Error loading grupos:', error)
    }
  }

  const loadClases = async (grupo: string) => {
    try {
      const clases = await catalogService.getClases(grupo)
      setClases(clases)
    } catch (error) {
      console.error('Error loading clases:', error)
    }
  }

  const showNotification = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setNotification({ open: true, message, severity })
  }

  const handleFilterChange = (field: keyof CatalogFilters, value: any) => {
    setFilters(prev => ({ ...prev, [field]: value }))
    setPage(1)
  }

  const clearFilters = () => {
    setFilters({})
    setPage(1)
  }

  const openCreateDialog = () => {
    setEditingCatalog(null)
    setFormData({
      codigo: '',
      denominacion: '',
      grupo: '',
      clase: '',
      resolucion: '',
      estado: 'ACTIVO'
    })
    setFormErrors({})
    setDialogOpen(true)
  }

  const openEditDialog = (catalog: Catalogo) => {
    setEditingCatalog(catalog)
    setFormData({
      codigo: catalog.codigo,
      denominacion: catalog.denominacion,
      grupo: catalog.grupo,
      clase: catalog.clase,
      resolucion: catalog.resolucion,
      estado: catalog.estado
    })
    setFormErrors({})
    setDialogOpen(true)
  }

  const closeDialog = () => {
    setDialogOpen(false)
    setEditingCatalog(null)
    setFormData({
      codigo: '',
      denominacion: '',
      grupo: '',
      clase: '',
      resolucion: '',
      estado: 'ACTIVO'
    })
    setFormErrors({})
  }

  const validateForm = async (): Promise<boolean> => {
    const errors: Record<string, string> = {}

    if (!formData.codigo.trim()) {
      errors.codigo = 'El código es requerido'
    }

    if (!formData.denominacion.trim()) {
      errors.denominacion = 'La denominación es requerida'
    }

    if (!formData.grupo.trim()) {
      errors.grupo = 'El grupo es requerido'
    }

    if (!formData.clase.trim()) {
      errors.clase = 'La clase es requerida'
    }

    if (!formData.resolucion.trim()) {
      errors.resolucion = 'La resolución es requerida'
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async () => {
    if (submitting) return

    setSubmitting(true)
    try {
      const isValid = await validateForm()
      if (!isValid) {
        setSubmitting(false)
        return
      }

      if (editingCatalog) {
        await catalogService.updateCatalogo(editingCatalog.id, formData)
        showNotification('Catálogo actualizado exitosamente', 'success')
      } else {
        await catalogService.createCatalogo(formData)
        showNotification('Catálogo creado exitosamente', 'success')
      }

      closeDialog()
      loadCatalogos()
    } catch (error: any) {
      showNotification(
        error.response?.data?.message || 'Error al guardar el catálogo',
        'error'
      )
    } finally {
      setSubmitting(false)
    }
  }

  const openDeleteDialog = (catalog: Catalogo) => {
    setCatalogToDelete(catalog)
    setDeleteDialogOpen(true)
  }

  const handleDelete = async () => {
    if (!catalogToDelete) return

    try {
      await catalogService.deleteCatalogo(catalogToDelete.id)
      showNotification('Catálogo eliminado exitosamente', 'success')
      setDeleteDialogOpen(false)
      setCatalogToDelete(null)
      loadCatalogos()
    } catch (error: any) {
      showNotification(
        error.response?.data?.message || 'Error al eliminar el catálogo',
        'error'
      )
    }
  }

  const handleExport = async () => {
    try {
      const blob = await catalogService.exportarExcel(filters)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `catalogo_${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      showNotification('Catálogo exportado exitosamente', 'success')
    } catch (error) {
      showNotification('Error al exportar el catálogo', 'error')
    }
  }

  const columns = [
    {
      field: 'codigo',
      headerName: 'Código',
      width: 120,
      sortable: true
    },
    {
      field: 'denominacion',
      headerName: 'Denominación',
      width: 300,
      sortable: true
    },
    {
      field: 'grupo',
      headerName: 'Grupo',
      width: 150,
      sortable: true
    },
    {
      field: 'clase',
      headerName: 'Clase',
      width: 150,
      sortable: true
    },
    {
      field: 'resolucion',
      headerName: 'Resolución',
      width: 150,
      sortable: true
    },
    {
      field: 'estado',
      headerName: 'Estado',
      width: 100,
      sortable: true,
      renderCell: (params: any) => (
        <Chip
          label={params.value}
          color={params.value === 'ACTIVO' ? 'success' : 'default'}
          size="small"
        />
      )
    },
    {
      field: 'actions',
      headerName: 'Acciones',
      width: 120,
      sortable: false,
      renderCell: (params: any) => (
        <Box>
          <Tooltip title="Editar">
            <IconButton
              size="small"
              onClick={() => openEditDialog(params.row)}
            >
              <EditIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Eliminar">
            <IconButton
              size="small"
              onClick={() => openDeleteDialog(params.row)}
              color="error"
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      )
    }
  ]

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          Catálogo de Bienes
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<ImportIcon />}
            href="/catalog/import"
          >
            Importar
          </Button>
          <Button
            variant="outlined"
            startIcon={<ExportIcon />}
            onClick={handleExport}
          >
            Exportar
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={openCreateDialog}
          >
            Nuevo Catálogo
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Buscar"
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField
              fullWidth
              select
              label="Grupo"
              value={filters.grupo || ''}
              onChange={(e) => handleFilterChange('grupo', e.target.value)}
            >
              <MenuItem value="">Todos</MenuItem>
              {grupos.map((grupo) => (
                <MenuItem key={grupo} value={grupo}>
                  {grupo}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField
              fullWidth
              select
              label="Clase"
              value={filters.clase || ''}
              onChange={(e) => handleFilterChange('clase', e.target.value)}
              disabled={!filters.grupo}
            >
              <MenuItem value="">Todas</MenuItem>
              {clases.map((clase) => (
                <MenuItem key={clase} value={clase}>
                  {clase}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <TextField
              fullWidth
              select
              label="Estado"
              value={filters.estado || ''}
              onChange={(e) => handleFilterChange('estado', e.target.value)}
            >
              <MenuItem value="">Todos</MenuItem>
              <MenuItem value="ACTIVO">Activo</MenuItem>
              <MenuItem value="EXCLUIDO">Excluido</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box display="flex" gap={1}>
              <Button
                variant="outlined"
                onClick={clearFilters}
                disabled={Object.keys(filters).length === 0}
              >
                Limpiar
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadCatalogos}
              >
                Actualizar
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Data Table */}
      <DataTable
        title="Catálogo de Bienes"
        rows={catalogos}
        columns={columns}
        loading={loading}
        hideActions={true}
      />

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={closeDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingCatalog ? 'Editar Catálogo' : 'Nuevo Catálogo'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <FormField
                label="Código"
                value={formData.codigo}
                onChange={(value) => setFormData(prev => ({ ...prev, codigo: value }))}
                validationError={formErrors.codigo}
                onValidate={async (value) => {
                  if (value && value.trim()) {
                    try {
                      const result = await catalogService.validarCodigo(value.trim(), editingCatalog?.id)
                      if (!result.disponible) {
                        setFormErrors(prev => ({ ...prev, codigo: 'Este código ya existe' }))
                      } else {
                        setFormErrors(prev => ({ ...prev, codigo: '' }))
                      }
                    } catch (error) {
                      setFormErrors(prev => ({ ...prev, codigo: 'Error al validar el código' }))
                    }
                  }
                }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                select
                label="Estado"
                value={formData.estado}
                onChange={(e) => setFormData(prev => ({ ...prev, estado: e.target.value as 'ACTIVO' | 'EXCLUIDO' }))}
                required
              >
                <MenuItem value="ACTIVO">Activo</MenuItem>
                <MenuItem value="EXCLUIDO">Excluido</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <FormField
                label="Denominación"
                value={formData.denominacion}
                onChange={(value) => setFormData(prev => ({ ...prev, denominacion: value }))}
                validationError={formErrors.denominacion}
                onValidate={async (value) => {
                  if (value && value.trim()) {
                    try {
                      const result = await catalogService.validarDenominacion(value.trim(), editingCatalog?.id)
                      if (!result.disponible) {
                        setFormErrors(prev => ({ ...prev, denominacion: 'Esta denominación ya existe' }))
                      } else {
                        setFormErrors(prev => ({ ...prev, denominacion: '' }))
                      }
                    } catch (error) {
                      setFormErrors(prev => ({ ...prev, denominacion: 'Error al validar la denominación' }))
                    }
                  }
                }}
                required
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormField
                label="Grupo"
                value={formData.grupo}
                onChange={(value) => setFormData(prev => ({ ...prev, grupo: value }))}
                error={formErrors.grupo}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormField
                label="Clase"
                value={formData.clase}
                onChange={(value) => setFormData(prev => ({ ...prev, clase: value }))}
                error={formErrors.clase}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormField
                label="Resolución"
                value={formData.resolucion}
                onChange={(value) => setFormData(prev => ({ ...prev, resolucion: value }))}
                error={formErrors.resolucion}
                required
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog}>
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={submitting}
          >
            {submitting ? <CircularProgress size={20} /> : (editingCatalog ? 'Actualizar' : 'Crear')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirmar Eliminación</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Está seguro que desea eliminar el catálogo "{catalogToDelete?.denominacion}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Esta acción no se puede deshacer.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Eliminar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={() => setNotification(prev => ({ ...prev, open: false }))}
      >
        <Alert
          onClose={() => setNotification(prev => ({ ...prev, open: false }))}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default CatalogList