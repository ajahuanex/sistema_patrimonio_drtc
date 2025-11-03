import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Grid,
  Alert,
  CircularProgress,
  Divider,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination
} from '@mui/material'
import {
  Download as DownloadIcon,
  Visibility as PreviewIcon,
  FileDownload as ExportIcon,
  Print as PrintIcon
} from '@mui/icons-material'

import { 
  FilterParams, 
  ReportPreview as ReportPreviewType,
  ReportGenerationParams,
  TIPOS_REPORTE,
  FORMATOS_EXPORTACION
} from '../../types/reports'
import reportService from '../../services/reportService'
import InteractiveCharts from './InteractiveCharts'

interface ReportPreviewProps {
  filters: FilterParams
  preview: ReportPreviewType | null
  loading: boolean
  onGenerateReport: (params: ReportGenerationParams) => void
}

const ReportPreview: React.FC<ReportPreviewProps> = ({
  filters,
  preview,
  loading,
  onGenerateReport
}) => {
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false)
  const [exportDialogOpen, setExportDialogOpen] = useState(false)
  const [reportParams, setReportParams] = useState<Partial<ReportGenerationParams>>({
    nombre_reporte: '',
    tipo_reporte: 'INVENTARIO',
    formato: 'EXCEL',
    incluir_graficos: true,
    incluir_historial: false,
    agrupar_por: ''
  })
  const [exporting, setExporting] = useState(false)

  const handleGenerateReport = () => {
    if (!reportParams.nombre_reporte?.trim()) return

    const params: ReportGenerationParams = {
      nombre_reporte: reportParams.nombre_reporte,
      tipo_reporte: reportParams.tipo_reporte || 'INVENTARIO',
      formato: reportParams.formato || 'EXCEL',
      incluir_graficos: reportParams.incluir_graficos || false,
      incluir_historial: reportParams.incluir_historial || false,
      agrupar_por: reportParams.agrupar_por || '',
      filtros: filters
    }

    onGenerateReport(params)
    setGenerateDialogOpen(false)
    
    // Reset form
    setReportParams({
      nombre_reporte: '',
      tipo_reporte: 'INVENTARIO',
      formato: 'EXCEL',
      incluir_graficos: true,
      incluir_historial: false,
      agrupar_por: ''
    })
  }

  const handleDirectExport = async (format: 'EXCEL' | 'PDF' | 'CSV') => {
    setExporting(true)
    try {
      let blob: Blob
      let filename: string
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')

      switch (format) {
        case 'EXCEL':
          blob = await reportService.exportToExcel(filters)
          filename = `inventario_${timestamp}.xlsx`
          break
        case 'PDF':
          blob = await reportService.exportToPDF(filters)
          filename = `inventario_${timestamp}.pdf`
          break
        case 'CSV':
          blob = await reportService.exportToCSV(filters)
          filename = `inventario_${timestamp}.csv`
          break
        default:
          return
      }

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      setExportDialogOpen(false)
    } catch (error) {
      console.error('Error exporting:', error)
    } finally {
      setExporting(false)
    }
  }

  const getActiveFiltersCount = (): number => {
    return Object.values(filters).filter(value => {
      if (Array.isArray(value)) return value.length > 0
      return value !== undefined && value !== null && value !== ''
    }).length
  }

  const renderActiveFilters = () => {
    const activeFilters: string[] = []

    if (filters.buscar_texto) activeFilters.push(`Texto: "${filters.buscar_texto}"`)
    if (filters.estados_bien?.length) activeFilters.push(`Estados: ${filters.estados_bien.length}`)
    if (filters.oficinas?.length) activeFilters.push(`Oficinas: ${filters.oficinas.length}`)
    if (filters.grupos?.length) activeFilters.push(`Grupos: ${filters.grupos.length}`)
    if (filters.clases?.length) activeFilters.push(`Clases: ${filters.clases.length}`)
    if (filters.marcas?.length) activeFilters.push(`Marcas: ${filters.marcas.length}`)
    if (filters.modelos?.length) activeFilters.push(`Modelos: ${filters.modelos.length}`)
    if (filters.fecha_registro_desde) activeFilters.push(`Desde: ${filters.fecha_registro_desde}`)
    if (filters.fecha_registro_hasta) activeFilters.push(`Hasta: ${filters.fecha_registro_hasta}`)
    if (filters.valor_minimo) activeFilters.push(`Valor min: ${filters.valor_minimo}`)
    if (filters.valor_maximo) activeFilters.push(`Valor max: ${filters.valor_maximo}`)

    return (
      <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
        {activeFilters.map((filter, index) => (
          <Chip key={index} label={filter} size="small" variant="outlined" />
        ))}
      </Box>
    )
  }

  if (loading) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>
          Generando vista previa...
        </Typography>
      </Paper>
    )
  }

  if (!preview) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">
          Aplique filtros para ver la vista previa del reporte
        </Typography>
      </Paper>
    )
  }

  return (
    <Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Vista Previa del Reporte
          </Typography>
          
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<ExportIcon />}
              onClick={() => setExportDialogOpen(true)}
            >
              Exportar Directo
            </Button>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => setGenerateDialogOpen(true)}
            >
              Generar Reporte
            </Button>
          </Box>
        </Box>

        {/* Active Filters Summary */}
        {getActiveFiltersCount() > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" gutterBottom>
              Filtros Aplicados ({getActiveFiltersCount()}):
            </Typography>
            {renderActiveFilters()}
          </Box>
        )}

        {/* Results Summary */}
        <Alert severity={preview.success ? "success" : "warning"} sx={{ mb: 2 }}>
          {preview.mensaje}
        </Alert>

        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="primary">
                {preview.total_resultados.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Bienes Encontrados
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="secondary">
                {preview.estadisticas.por_estado?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Estados Diferentes
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <Paper sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="h4" color="info.main">
                {preview.estadisticas.por_oficina?.length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Oficinas Involucradas
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Paper>

      {/* Interactive Charts */}
      {preview.estadisticas && (
        <InteractiveCharts 
          statistics={preview.estadisticas}
          loading={false}
        />
      )}

      {/* Generate Report Dialog */}
      <Dialog 
        open={generateDialogOpen} 
        onClose={() => setGenerateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Generar Reporte Personalizado</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Nombre del Reporte"
                value={reportParams.nombre_reporte || ''}
                onChange={(e) => setReportParams({
                  ...reportParams,
                  nombre_reporte: e.target.value
                })}
                required
              />
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Reporte</InputLabel>
                <Select
                  value={reportParams.tipo_reporte || 'INVENTARIO'}
                  onChange={(e) => setReportParams({
                    ...reportParams,
                    tipo_reporte: e.target.value as any
                  })}
                >
                  {TIPOS_REPORTE.map((tipo) => (
                    <MenuItem key={tipo.value} value={tipo.value}>
                      {tipo.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Formato</InputLabel>
                <Select
                  value={reportParams.formato || 'EXCEL'}
                  onChange={(e) => setReportParams({
                    ...reportParams,
                    formato: e.target.value as any
                  })}
                >
                  {FORMATOS_EXPORTACION.map((formato) => (
                    <MenuItem key={formato.value} value={formato.value}>
                      {formato.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={reportParams.incluir_graficos || false}
                    onChange={(e) => setReportParams({
                      ...reportParams,
                      incluir_graficos: e.target.checked
                    })}
                  />
                }
                label="Incluir gráficos en el reporte"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={reportParams.incluir_historial || false}
                    onChange={(e) => setReportParams({
                      ...reportParams,
                      incluir_historial: e.target.checked
                    })}
                  />
                }
                label="Incluir historial de movimientos"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Agrupar por (opcional)"
                value={reportParams.agrupar_por || ''}
                onChange={(e) => setReportParams({
                  ...reportParams,
                  agrupar_por: e.target.value
                })}
                placeholder="oficina, estado, grupo, etc."
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGenerateDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleGenerateReport}
            variant="contained"
            disabled={!reportParams.nombre_reporte?.trim()}
          >
            Generar Reporte
          </Button>
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog 
        open={exportDialogOpen} 
        onClose={() => setExportDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Exportación Directa</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Exporte los resultados actuales directamente sin generar un reporte personalizado.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Se exportarán {preview.total_resultados.toLocaleString()} bienes con los filtros aplicados.
          </Typography>
          
          <Box display="flex" flexDirection="column" gap={2}>
            <Button
              variant="outlined"
              startIcon={exporting ? <CircularProgress size={16} /> : <DownloadIcon />}
              onClick={() => handleDirectExport('EXCEL')}
              disabled={exporting}
              fullWidth
            >
              Descargar Excel (.xlsx)
            </Button>
            <Button
              variant="outlined"
              startIcon={exporting ? <CircularProgress size={16} /> : <DownloadIcon />}
              onClick={() => handleDirectExport('PDF')}
              disabled={exporting}
              fullWidth
            >
              Descargar PDF
            </Button>
            <Button
              variant="outlined"
              startIcon={exporting ? <CircularProgress size={16} /> : <DownloadIcon />}
              onClick={() => handleDirectExport('CSV')}
              disabled={exporting}
              fullWidth
            >
              Descargar CSV
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ReportPreview