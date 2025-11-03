import React, { useState, useEffect } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Autocomplete,
  FormControlLabel,
  Switch,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress
} from '@mui/material'
import {
  ExpandMore as ExpandMoreIcon,
  FilterList as FilterIcon,
  Save as SaveIcon,
  Clear as ClearIcon,
  Search as SearchIcon
} from '@mui/icons-material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { es } from 'date-fns/locale'

import { FilterParams, SavedFilter, ESTADOS_BIEN } from '../../types/reports'
import reportService from '../../services/reportService'
import { catalogService } from '../../services/catalogService'
import { officeService } from '../../services/officeService'

interface AdvancedFiltersProps {
  filters: FilterParams
  onFiltersChange: (filters: FilterParams) => void
  onApplyFilters: () => void
  onClearFilters: () => void
  loading?: boolean
}

const AdvancedFilters: React.FC<AdvancedFiltersProps> = ({
  filters,
  onFiltersChange,
  onApplyFilters,
  onClearFilters,
  loading = false
}) => {
  // State for options
  const [offices, setOffices] = useState<Array<{id: string, nombre: string}>>([])
  const [catalogGroups, setCatalogGroups] = useState<string[]>([])
  const [catalogClasses, setCatalogClasses] = useState<string[]>([])
  const [brandSuggestions, setBrandSuggestions] = useState<string[]>([])
  const [modelSuggestions, setModelSuggestions] = useState<string[]>([])
  
  // State for saved filters
  const [savedFilters, setSavedFilters] = useState<SavedFilter[]>([])
  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [filterName, setFilterName] = useState('')
  const [filterDescription, setFilterDescription] = useState('')
  const [isPublic, setIsPublic] = useState(false)

  // Load initial data
  useEffect(() => {
    loadInitialData()
    loadSavedFilters()
  }, [])

  // Load classes when groups change
  useEffect(() => {
    if (filters.grupos && filters.grupos.length > 0) {
      loadClassesByGroups(filters.grupos)
    } else {
      setCatalogClasses([])
    }
  }, [filters.grupos])

  const loadInitialData = async () => {
    try {
      const [officesData, catalogData] = await Promise.all([
        officeService.getOffices(),
        catalogService.getCatalog()
      ])
      
      setOffices(officesData)
      
      // Extract unique groups from catalog
      const groups = [...new Set(catalogData.map(item => item.grupo))].filter(Boolean)
      setCatalogGroups(groups)
    } catch (error) {
      console.error('Error loading initial data:', error)
    }
  }

  const loadSavedFilters = async () => {
    try {
      const filters = await reportService.getSavedFilters()
      setSavedFilters(filters)
    } catch (error) {
      console.error('Error loading saved filters:', error)
    }
  }

  const loadClassesByGroups = async (groups: string[]) => {
    try {
      const allClasses = await Promise.all(
        groups.map(group => reportService.getClassesByGroup(group))
      )
      const uniqueClasses = [...new Set(allClasses.flat())]
      setCatalogClasses(uniqueClasses)
    } catch (error) {
      console.error('Error loading classes:', error)
    }
  }

  const handleFilterChange = (field: keyof FilterParams, value: any) => {
    onFiltersChange({
      ...filters,
      [field]: value
    })
  }

  const handleBrandSearch = async (query: string) => {
    if (query.length >= 2) {
      try {
        const suggestions = await reportService.getBrandSuggestions(query)
        setBrandSuggestions(suggestions)
      } catch (error) {
        console.error('Error loading brand suggestions:', error)
      }
    }
  }

  const handleModelSearch = async (query: string) => {
    if (query.length >= 2) {
      try {
        const suggestions = await reportService.getModelSuggestions(
          query, 
          filters.marcas?.[0]
        )
        setModelSuggestions(suggestions)
      } catch (error) {
        console.error('Error loading model suggestions:', error)
      }
    }
  }

  const handleSaveFilter = async () => {
    if (!filterName.trim()) return

    try {
      const savedFilter = await reportService.saveFilter({
        nombre: filterName,
        descripcion: filterDescription,
        parametros: filters,
        es_publico: isPublic
      })
      
      setSavedFilters([...savedFilters, savedFilter])
      setSaveDialogOpen(false)
      setFilterName('')
      setFilterDescription('')
      setIsPublic(false)
    } catch (error) {
      console.error('Error saving filter:', error)
    }
  }

  const handleLoadFilter = async (filterId: number) => {
    try {
      const savedFilter = await reportService.loadFilter(filterId)
      onFiltersChange(savedFilter.parametros)
    } catch (error) {
      console.error('Error loading filter:', error)
    }
  }

  const hasActiveFilters = Object.values(filters).some(value => {
    if (Array.isArray(value)) return value.length > 0
    return value !== undefined && value !== null && value !== ''
  })

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={es}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Typography variant="h6" display="flex" alignItems="center">
            <FilterIcon sx={{ mr: 1 }} />
            Filtros Avanzados
          </Typography>
          
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<SaveIcon />}
              onClick={() => setSaveDialogOpen(true)}
              disabled={!hasActiveFilters}
            >
              Guardar Filtros
            </Button>
            <Button
              variant="outlined"
              startIcon={<ClearIcon />}
              onClick={onClearFilters}
              disabled={!hasActiveFilters}
            >
              Limpiar
            </Button>
            <Button
              variant="contained"
              startIcon={loading ? <CircularProgress size={16} /> : <SearchIcon />}
              onClick={onApplyFilters}
              disabled={loading}
            >
              Aplicar Filtros
            </Button>
          </Box>
        </Box>

        {/* Saved Filters */}
        {savedFilters.length > 0 && (
          <Accordion sx={{ mb: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>Filtros Guardados ({savedFilters.length})</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {savedFilters.map((savedFilter) => (
                  <Chip
                    key={savedFilter.id}
                    label={`${savedFilter.nombre} (${savedFilter.veces_usado})`}
                    onClick={() => handleLoadFilter(savedFilter.id)}
                    variant="outlined"
                    color={savedFilter.es_publico ? "primary" : "default"}
                  />
                ))}
              </Box>
            </AccordionDetails>
          </Accordion>
        )}

        <Grid container spacing={3}>
          {/* Basic Filters */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Buscar texto"
              placeholder="Código, denominación, marca, modelo..."
              value={filters.buscar_texto || ''}
              onChange={(e) => handleFilterChange('buscar_texto', e.target.value)}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Estados del Bien</InputLabel>
              <Select
                multiple
                value={filters.estados_bien || []}
                onChange={(e) => handleFilterChange('estados_bien', e.target.value)}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => {
                      const estado = ESTADOS_BIEN.find(e => e.value === value)
                      return <Chip key={value} label={estado?.label || value} size="small" />
                    })}
                  </Box>
                )}
              >
                {ESTADOS_BIEN.map((estado) => (
                  <MenuItem key={estado.value} value={estado.value}>
                    {estado.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Office Filter */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Oficinas</InputLabel>
              <Select
                multiple
                value={filters.oficinas || []}
                onChange={(e) => handleFilterChange('oficinas', e.target.value)}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => {
                      const office = offices.find(o => o.id === value)
                      return <Chip key={value} label={office?.nombre || value} size="small" />
                    })}
                  </Box>
                )}
              >
                {offices.map((office) => (
                  <MenuItem key={office.id} value={office.id}>
                    {office.nombre}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Catalog Groups */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Grupos de Catálogo</InputLabel>
              <Select
                multiple
                value={filters.grupos || []}
                onChange={(e) => handleFilterChange('grupos', e.target.value)}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {(selected as string[]).map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {catalogGroups.map((group) => (
                  <MenuItem key={group} value={group}>
                    {group}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Catalog Classes */}
          {catalogClasses.length > 0 && (
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Clases de Catálogo</InputLabel>
                <Select
                  multiple
                  value={filters.clases || []}
                  onChange={(e) => handleFilterChange('clases', e.target.value)}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {(selected as string[]).map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {catalogClasses.map((clase) => (
                    <MenuItem key={clase} value={clase}>
                      {clase}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          )}

          {/* Brand and Model */}
          <Grid item xs={12} md={6}>
            <Autocomplete
              multiple
              freeSolo
              options={brandSuggestions}
              value={filters.marcas || []}
              onChange={(_, value) => handleFilterChange('marcas', value)}
              onInputChange={(_, value) => handleBrandSearch(value)}
              renderInput={(params) => (
                <TextField {...params} label="Marcas" placeholder="Escriba para buscar..." />
              )}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip {...getTagProps({ index })} key={option} label={option} size="small" />
                ))
              }
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <Autocomplete
              multiple
              freeSolo
              options={modelSuggestions}
              value={filters.modelos || []}
              onChange={(_, value) => handleFilterChange('modelos', value)}
              onInputChange={(_, value) => handleModelSearch(value)}
              renderInput={(params) => (
                <TextField {...params} label="Modelos" placeholder="Escriba para buscar..." />
              )}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip {...getTagProps({ index })} key={option} label={option} size="small" />
                ))
              }
            />
          </Grid>

          {/* Date Filters */}
          <Grid item xs={12} md={6}>
            <DatePicker
              label="Fecha Registro Desde"
              value={filters.fecha_registro_desde ? new Date(filters.fecha_registro_desde) : null}
              onChange={(date) => handleFilterChange('fecha_registro_desde', date?.toISOString().split('T')[0])}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <DatePicker
              label="Fecha Registro Hasta"
              value={filters.fecha_registro_hasta ? new Date(filters.fecha_registro_hasta) : null}
              onChange={(date) => handleFilterChange('fecha_registro_hasta', date?.toISOString().split('T')[0])}
              slotProps={{ textField: { fullWidth: true } }}
            />
          </Grid>

          {/* Value Range */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Valor Mínimo"
              value={filters.valor_minimo || ''}
              onChange={(e) => handleFilterChange('valor_minimo', e.target.value ? parseFloat(e.target.value) : undefined)}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Valor Máximo"
              value={filters.valor_maximo || ''}
              onChange={(e) => handleFilterChange('valor_maximo', e.target.value ? parseFloat(e.target.value) : undefined)}
            />
          </Grid>
        </Grid>

        {/* Save Filter Dialog */}
        <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Guardar Configuración de Filtros</DialogTitle>
          <DialogContent>
            <TextField
              fullWidth
              label="Nombre del filtro"
              value={filterName}
              onChange={(e) => setFilterName(e.target.value)}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Descripción (opcional)"
              value={filterDescription}
              onChange={(e) => setFilterDescription(e.target.value)}
              margin="normal"
              multiline
              rows={2}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                />
              }
              label="Hacer público (otros usuarios pueden usar este filtro)"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSaveDialogOpen(false)}>Cancelar</Button>
            <Button onClick={handleSaveFilter} variant="contained" disabled={!filterName.trim()}>
              Guardar
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </LocalizationProvider>
  )
}

export default AdvancedFilters