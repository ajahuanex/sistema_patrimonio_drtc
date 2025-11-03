import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Chip,
  Alert,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Divider
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Share as ShareIcon,
  FileCopy as CopyIcon,
  MoreVert as MoreIcon,
  Public as PublicIcon,
  Lock as PrivateIcon,
  Star as StarIcon,
  StarBorder as StarBorderIcon
} from '@mui/icons-material'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

import { SavedFilter, FilterParams } from '../../types/reports'
import reportService from '../../services/reportService'

interface FilterConfigurationsProps {
  onLoadFilter: (filter: SavedFilter) => void
}

const FilterConfigurations: React.FC<FilterConfigurationsProps> = ({
  onLoadFilter
}) => {
  const [filters, setFilters] = useState<SavedFilter[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingFilter, setEditingFilter] = useState<SavedFilter | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [filterToDelete, setFilterToDelete] = useState<SavedFilter | null>(null)
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null)
  const [selectedFilter, setSelectedFilter] = useState<SavedFilter | null>(null)
  
  // Form state
  const [formData, setFormData] = useState({
    nombre: '',
    descripcion: '',
    es_publico: false
  })

  useEffect(() => {
    loadFilters()
  }, [])

  const loadFilters = async () => {
    setLoading(true)
    try {
      const data = await reportService.getSavedFilters()
      setFilters(data)
    } catch (error) {
      console.error('Error loading filters:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateNew = () => {
    setEditingFilter(null)
    setFormData({
      nombre: '',
      descripcion: '',
      es_publico: false
    })
    setDialogOpen(true)
  }

  const handleEdit = (filter: SavedFilter) => {
    setEditingFilter(filter)
    setFormData({
      nombre: filter.nombre,
      descripcion: filter.descripcion || '',
      es_publico: filter.es_publico
    })
    setDialogOpen(true)
    handleCloseMenu()
  }

  const handleSave = async () => {
    try {
      if (editingFilter) {
        // Update existing filter
        const updated = await reportService.updateFilter(editingFilter.id, {
          ...editingFilter,
          ...formData
        })
        setFilters(filters.map(f => f.id === updated.id ? updated : f))
      } else {
        // Create new filter - this would need current filter params
        // For now, we'll show a message that this should be done from the main filters
        alert('Para crear un nuevo filtro, configure los filtros en la pestaña principal y use "Guardar Filtros"')
        setDialogOpen(false)
        return
      }
      
      setDialogOpen(false)
      setEditingFilter(null)
    } catch (error) {
      console.error('Error saving filter:', error)
    }
  }

  const handleDelete = async () => {
    if (!filterToDelete) return
    
    try {
      await reportService.deleteFilter(filterToDelete.id)
      setFilters(filters.filter(f => f.id !== filterToDelete.id))
      setDeleteDialogOpen(false)
      setFilterToDelete(null)
    } catch (error) {
      console.error('Error deleting filter:', error)
    }
  }

  const handleDuplicate = async (filter: SavedFilter) => {
    try {
      const duplicated = await reportService.saveFilter({
        nombre: `${filter.nombre} (Copia)`,
        descripcion: filter.descripcion,
        parametros: filter.parametros,
        es_publico: false
      })
      setFilters([duplicated, ...filters])
    } catch (error) {
      console.error('Error duplicating filter:', error)
    }
    handleCloseMenu()
  }

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, filter: SavedFilter) => {
    setMenuAnchor(event.currentTarget)
    setSelectedFilter(filter)
  }

  const handleCloseMenu = () => {
    setMenuAnchor(null)
    setSelectedFilter(null)
  }

  const formatDate = (dateString: string): string => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy', { locale: es })
    } catch {
      return dateString
    }
  }

  const getFilterSummary = (parametros: FilterParams): string[] => {
    const summary: string[] = []
    
    if (parametros.buscar_texto) summary.push(`Texto: "${parametros.buscar_texto}"`)
    if (parametros.estados_bien?.length) summary.push(`${parametros.estados_bien.length} estados`)
    if (parametros.oficinas?.length) summary.push(`${parametros.oficinas.length} oficinas`)
    if (parametros.grupos?.length) summary.push(`${parametros.grupos.length} grupos`)
    if (parametros.marcas?.length) summary.push(`${parametros.marcas.length} marcas`)
    if (parametros.fecha_registro_desde || parametros.fecha_registro_hasta) {
      summary.push('Filtro de fechas')
    }
    if (parametros.valor_minimo || parametros.valor_maximo) {
      summary.push('Filtro de valores')
    }
    
    return summary.slice(0, 3) // Show only first 3 items
  }

  const myFilters = filters.filter(f => f.usuario === 'current_user') // This should be dynamic
  const publicFilters = filters.filter(f => f.es_publico && f.usuario !== 'current_user')

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">
          Configuraciones de Filtros Guardadas
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateNew}
        >
          Nueva Configuración
        </Button>
      </Box>

      {/* My Filters */}
      <Typography variant="h6" gutterBottom>
        Mis Filtros ({myFilters.length})
      </Typography>
      
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {myFilters.map((filter) => (
          <Grid item xs={12} sm={6} md={4} key={filter.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                  <Typography variant="h6" component="div" noWrap>
                    {filter.nombre}
                  </Typography>
                  <Box display="flex" alignItems="center">
                    {filter.es_publico ? (
                      <Tooltip title="Público">
                        <PublicIcon fontSize="small" color="primary" />
                      </Tooltip>
                    ) : (
                      <Tooltip title="Privado">
                        <PrivateIcon fontSize="small" color="action" />
                      </Tooltip>
                    )}
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuClick(e, filter)}
                    >
                      <MoreIcon />
                    </IconButton>
                  </Box>
                </Box>
                
                {filter.descripcion && (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {filter.descripcion}
                  </Typography>
                )}
                
                <Box display="flex" flexWrap="wrap" gap={0.5} sx={{ mb: 2 }}>
                  {getFilterSummary(filter.parametros).map((item, index) => (
                    <Chip key={index} label={item} size="small" variant="outlined" />
                  ))}
                </Box>
                
                <Typography variant="caption" color="text.secondary">
                  Creado: {formatDate(filter.fecha_creacion)}
                </Typography>
                <br />
                <Typography variant="caption" color="text.secondary">
                  Usado {filter.veces_usado} veces
                </Typography>
              </CardContent>
              
              <CardActions>
                <Button
                  size="small"
                  onClick={() => onLoadFilter(filter)}
                  color="primary"
                >
                  Cargar
                </Button>
                <Button
                  size="small"
                  onClick={() => handleEdit(filter)}
                >
                  Editar
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
        
        {myFilters.length === 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No tienes filtros guardados
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Configura filtros en la pestaña principal y guárdalos para reutilizarlos
              </Typography>
            </Paper>
          </Grid>
        )}
      </Grid>

      {/* Public Filters */}
      {publicFilters.length > 0 && (
        <>
          <Divider sx={{ my: 3 }} />
          <Typography variant="h6" gutterBottom>
            Filtros Públicos ({publicFilters.length})
          </Typography>
          
          <Grid container spacing={2}>
            {publicFilters.map((filter) => (
              <Grid item xs={12} sm={6} md={4} key={filter.id}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Typography variant="h6" component="div" noWrap>
                        {filter.nombre}
                      </Typography>
                      <PublicIcon fontSize="small" color="primary" />
                    </Box>
                    
                    {filter.descripcion && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {filter.descripcion}
                      </Typography>
                    )}
                    
                    <Box display="flex" flexWrap="wrap" gap={0.5} sx={{ mb: 2 }}>
                      {getFilterSummary(filter.parametros).map((item, index) => (
                        <Chip key={index} label={item} size="small" variant="outlined" />
                      ))}
                    </Box>
                    
                    <Typography variant="caption" color="text.secondary">
                      Por: {filter.usuario || 'Usuario'}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="text.secondary">
                      Usado {filter.veces_usado} veces
                    </Typography>
                  </CardContent>
                  
                  <CardActions>
                    <Button
                      size="small"
                      onClick={() => onLoadFilter(filter)}
                      color="primary"
                    >
                      Cargar
                    </Button>
                    <Button
                      size="small"
                      onClick={() => handleDuplicate(filter)}
                    >
                      Duplicar
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleCloseMenu}
      >
        <MenuItem onClick={() => selectedFilter && onLoadFilter(selectedFilter)}>
          <ListItemIcon>
            <StarIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Cargar Filtro</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => selectedFilter && handleEdit(selectedFilter)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Editar</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => selectedFilter && handleDuplicate(selectedFilter)}>
          <ListItemIcon>
            <CopyIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Duplicar</ListItemText>
        </MenuItem>
        
        <MenuItem 
          onClick={() => {
            setFilterToDelete(selectedFilter)
            setDeleteDialogOpen(true)
            handleCloseMenu()
          }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Eliminar</ListItemText>
        </MenuItem>
      </Menu>

      {/* Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingFilter ? 'Editar Configuración' : 'Nueva Configuración'}
        </DialogTitle>
        <DialogContent>
          {!editingFilter && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Para crear una nueva configuración, primero configure los filtros en la pestaña principal
              y use el botón "Guardar Filtros".
            </Alert>
          )}
          
          <TextField
            fullWidth
            label="Nombre"
            value={formData.nombre}
            onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
            margin="normal"
            required
          />
          
          <TextField
            fullWidth
            label="Descripción"
            value={formData.descripcion}
            onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
            margin="normal"
            multiline
            rows={2}
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={formData.es_publico}
                onChange={(e) => setFormData({ ...formData, es_publico: e.target.checked })}
              />
            }
            label="Hacer público (otros usuarios pueden usar esta configuración)"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button 
            onClick={handleSave}
            variant="contained"
            disabled={!formData.nombre.trim() || !editingFilter}
          >
            {editingFilter ? 'Actualizar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirmar Eliminación</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Esta acción no se puede deshacer
          </Alert>
          <Typography>
            ¿Está seguro que desea eliminar la configuración "{filterToDelete?.nombre}"?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancelar</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Eliminar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default FilterConfigurations