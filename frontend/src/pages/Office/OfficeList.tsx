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
import { officeService, OfficeFilters, OfficeForm } from '../../services/officeService'
import { Oficina } from '../../types/inventory'

const OfficeList: React.FC = () => {
  const [oficinas, setOficinas] = useState<Oficina[]>([])
  const [loading, setLoading] = useState(true)
  const [totalCount, setTotalCount] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  const [filters, setFilters] = useState<OfficeFilters>({})
  
  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingOffice, setEditingOffice] = useState<Oficina | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [officeToDelete, setOfficeToDelete] = useState<Oficina | null>(null)
  
  // Form state
  const [formData, setFormData] = useState<OfficeForm>({
    codigo: '',
    nombre: '',
    descripcion: '',
    responsable: '',
    cargo_responsable: '',
    telefono: '',
    email: '',
    ubicacion: '',
    estado: true
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
    loadOficinas()
  }, [page, pageSize, filters])

  const loadOficinas = async () => {
    try {
      setLoading(true)
      const response = await officeService.getOficinas(filters, page, pageSize)
      setOficinas(response.results)
      setTotalCount(response.count)
    } catch (error) {
      showNotification('Error al cargar las oficinas', 'error')
    } finally {
      setLoading(false)
    }
  }

  const showNotification = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setNotification({ open: true, message, severity })
  }

  const handleFilterChange = (field: keyof OfficeFilters, value: any) => {
    setFilters(prev => ({ ...prev, [field]: value }))
    setPage(1)
  }

  const clearFilters = () => {
    setFilters({})
    setPage(1)
  }

  const openCreateDialog = () => {
    setEditingOffice(null)
    setFormData({
      codigo: '',
      nombre: '',
      descripcion: '',
      responsable: '',
      cargo_responsable: '',
      telefono: '',
      email: '',
      ubicacion: '',
      estado: true
    })
    setFormErrors({})
    setDialogOpen(true)
  }

  const openEditDialog = (office: Oficina) => {
    setEditingOffice(office)
    setFormData({
      codigo: office.codigo,
      nombre: office.nombre,
      descripcion: office.descripcion,
      responsable: office.responsable,
      cargo_responsable: office.cargo_responsable,
      telefono: office.telefono,
      email: office.email,
      ubicacion: office.ubicacion,
      estado: office.estado
    })
    setFormErrors({})
    setDialogOpen(true)
  }

  const closeDialog = () => {
    setDialogOpen(false)
    setEditingOffice(null)
    setFormData({
      codigo: '',
      nombre: '',
      descripcion: '',
      responsable: '',
      cargo_responsable: '',
      telefono: '',
      email: '',
      ubicacion: '',
      estado: true
    })
    setFormErrors({})
  }

  const validateForm = async (): Promise<boolean> => {
    const errors: Record<string, string> = {}

    if (!formData.codigo.trim()) {
      errors.codigo = 'El código es requerido'
    }

    if (!formData.nombre.trim()) {
      errors.nombre = 'El nombre es requerido'
    }

    if (!formData.responsable.trim()) {
      errors.responsable = 'El responsable es requerido'
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'El email no es válido'
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

      if (editingOffice) {
        await officeService.updateOficina(editingOffice.id, formData)
        showNotification('Oficina actualizada exitosamente', 'success')
      } else {
        await officeService.createOficina(formData)
        showNotification('Oficina creada exitosamente', 'success')
      }

      closeDialog()
      loadOficinas()
    } catch (error: any) {
      showNotification(
        error.response?.data?.message || 'Error al guardar la oficina',
        'error'
      )
    } finally {
      setSubmitting(false)
    }
  }

  const openDeleteDialog = async (office: Oficina) => {
    try {
      const result = await officeService.puedeEliminar(office.id)
      if (!result.puede_eliminar) {
        showNotification(
          `No se puede eliminar la oficina porque tiene ${result.bienes_asignados} bienes asignados`,
          'warning'
        )
        return
      }
      setOfficeToDelete(office)
      setDeleteDialogOpen(true)
    } catch (error) {
      showNotification('Error al verificar si se puede eliminar la oficina', 'error')
    }
  }

  const handleDelete = async () => {
    if (!officeToDelete) return

    try {
      await officeService.deleteOficina(officeToDelete.id)
      showNotification('Oficina eliminada exitosamente', 'success')
      setDeleteDialogOpen(false)
      setOfficeToDelete(null)
      loadOficinas()
    } catch (error: any) {
      showNotification(
        error.response?.data?.message || 'Error al eliminar la oficina',
        'error'
      )
    }
  }

  const handleExport = async () => {
    try {
      const blob = await officeService.exportarExcel(filters)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `oficinas_${new Date().toISOString().split('T')[0]}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      showNotification('Oficinas exportadas exitosamente', 'success')
    } catch (error) {
      showNotification('Error al exportar las oficinas', 'error')
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
      field: 'nombre',
      headerName: 'Nombre',
      width: 200,
      sortable: true
    },
    {
      field: 'responsable',
      headerName: 'Responsable',
      width: 180,
      sortable: true
    },
    {
      field: 'cargo_responsable',
      headerName: 'Cargo',
      width: 150,
      sortable: true
    },
    {
      field: 'telefono',
      headerName: 'Teléfono',
      width: 120,
      sortable: false
    },
    {
      field: 'email',
      headerName: 'Email',
      width: 180,
      sortable: false
    },
    {
      field: 'ubicacion',
      headerName: 'Ubicación',
      width: 150,
      sortable: false
    },
    {
      field: 'estado',
      headerName: 'Estado',
      width: 100,
      sortable: true,
      renderCell: (params: any) => (
        <Chip
          label={params.value ? 'Activa' : 'Inactiva'}
          color={params.value ? 'success' : 'default'}
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
          Gestión de Oficinas
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<ImportIcon />}
            href="/offices/import"
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
            Nueva Oficina
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
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
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              select
              label="Estado"
              value={filters.estado !== undefined ? filters.estado.toString() : ''}
              onChange={(e) => handleFilterChange('estado', e.target.value === '' ? undefined : e.target.value === 'true')}
            >
              <MenuItem value="">Todos</MenuItem>
              <MenuItem value="true">Activas</MenuItem>
              <MenuItem value="false">Inactivas</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              label="Responsable"
              value={filters.responsable || ''}
              onChange={(e) => handleFilterChange('responsable', e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
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
                onClick={loadOficinas}
              >
                Actualizar
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Data Table */}
      <DataTable
        title="Gestión de Oficinas"
        rows={oficinas}
        columns={columns}
        loading={loading}
        hideActions={true}
      />

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={closeDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingOffice ? 'Editar Oficina' : 'Nueva Oficina'}
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
                      const result = await officeService.validarCodigo(value.trim(), editingOffice?.id)
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
                onChange={(e) => setFormData(prev => ({ ...prev, estado: e.target.value === 'true' }))}
                required
              >
                <MenuItem value="true">Activa</MenuItem>
                <MenuItem value="false">Inactiva</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <FormField
                label="Nombre"
                value={formData.nombre}
                onChange={(value) => setFormData(prev => ({ ...prev, nombre: value }))}
                error={formErrors.nombre}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormField
                label="Descripción"
                value={formData.descripcion}
                onChange={(value) => setFormData(prev => ({ ...prev, descripcion: value }))}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormField
                label="Responsable"
                value={formData.responsable}
                onChange={(value) => setFormData(prev => ({ ...prev, responsable: value }))}
                error={formErrors.responsable}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormField
                label="Cargo del Responsable"
                value={formData.cargo_responsable}
                onChange={(value) => setFormData(prev => ({ ...prev, cargo_responsable: value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormField
                label="Teléfono"
                value={formData.telefono}
                onChange={(value) => setFormData(prev => ({ ...prev, telefono: value }))}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormField
                label="Email"
                value={formData.email}
                onChange={(value) => setFormData(prev => ({ ...prev, email: value }))}
                validationError={formErrors.email}
                onValidate={async (value) => {
                  if (value && value.trim()) {
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
                    if (!emailRegex.test(value.trim())) {
                      setFormErrors(prev => ({ ...prev, email: 'El email no es válido' }))
                    } else {
                      setFormErrors(prev => ({ ...prev, email: '' }))
                    }
                  } else {
                    setFormErrors(prev => ({ ...prev, email: '' }))
                  }
                }}
                type="email"
              />
            </Grid>
            <Grid item xs={12}>
              <FormField
                label="Ubicación"
                value={formData.ubicacion}
                onChange={(value) => setFormData(prev => ({ ...prev, ubicacion: value }))}
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
            {submitting ? <CircularProgress size={20} /> : (editingOffice ? 'Actualizar' : 'Crear')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirmar Eliminación</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Está seguro que desea eliminar la oficina "{officeToDelete?.nombre}"?
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

export default OfficeList