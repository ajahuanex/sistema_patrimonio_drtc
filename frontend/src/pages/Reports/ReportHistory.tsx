import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Tooltip,
  Alert,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText
} from '@mui/material'
import {
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreIcon,
  Visibility as ViewIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CompleteIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon
} from '@mui/icons-material'
import { format } from 'date-fns'
import { es } from 'date-fns/locale'

import { GeneratedReport } from '../../types/reports'

interface ReportHistoryProps {
  reports: GeneratedReport[]
  onDownload: (reportId: number) => void
  onDelete: (reportId: number) => void
  onRefresh: () => void
}

const ReportHistory: React.FC<ReportHistoryProps> = ({
  reports,
  onDownload,
  onDelete,
  onRefresh
}) => {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [reportToDelete, setReportToDelete] = useState<GeneratedReport | null>(null)
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null)
  const [selectedReport, setSelectedReport] = useState<GeneratedReport | null>(null)

  const handleChangePage = (_: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleDeleteClick = (report: GeneratedReport) => {
    setReportToDelete(report)
    setDeleteDialogOpen(true)
    handleCloseMenu()
  }

  const handleConfirmDelete = () => {
    if (reportToDelete) {
      onDelete(reportToDelete.id)
      setDeleteDialogOpen(false)
      setReportToDelete(null)
    }
  }

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, report: GeneratedReport) => {
    setMenuAnchor(event.currentTarget)
    setSelectedReport(report)
  }

  const handleCloseMenu = () => {
    setMenuAnchor(null)
    setSelectedReport(null)
  }

  const getStatusIcon = (estado: GeneratedReport['estado']) => {
    switch (estado) {
      case 'COMPLETADO':
        return <CompleteIcon color="success" />
      case 'PROCESANDO':
        return <ScheduleIcon color="warning" />
      case 'ERROR':
        return <ErrorIcon color="error" />
      case 'PENDIENTE':
      default:
        return <PendingIcon color="info" />
    }
  }

  const getStatusColor = (estado: GeneratedReport['estado']): "success" | "warning" | "error" | "info" => {
    switch (estado) {
      case 'COMPLETADO':
        return 'success'
      case 'PROCESANDO':
        return 'warning'
      case 'ERROR':
        return 'error'
      case 'PENDIENTE':
      default:
        return 'info'
    }
  }

  const getStatusLabel = (estado: GeneratedReport['estado']): string => {
    switch (estado) {
      case 'COMPLETADO':
        return 'Completado'
      case 'PROCESANDO':
        return 'Procesando'
      case 'ERROR':
        return 'Error'
      case 'PENDIENTE':
      default:
        return 'Pendiente'
    }
  }

  const formatDate = (dateString: string): string => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: es })
    } catch {
      return dateString
    }
  }

  const canDownload = (report: GeneratedReport): boolean => {
    return report.estado === 'COMPLETADO' && !!report.archivo_url
  }

  const paginatedReports = reports.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)

  if (reports.length === 0) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No hay reportes generados
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Los reportes que genere aparecerán aquí
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onRefresh}
        >
          Actualizar
        </Button>
      </Paper>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">
          Historial de Reportes ({reports.length})
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={onRefresh}
        >
          Actualizar
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Estado</TableCell>
              <TableCell>Nombre</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell>Formato</TableCell>
              <TableCell>Fecha Inicio</TableCell>
              <TableCell>Registros</TableCell>
              <TableCell>Progreso</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedReports.map((report) => (
              <TableRow key={report.id} hover>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getStatusIcon(report.estado)}
                    <Chip
                      label={getStatusLabel(report.estado)}
                      color={getStatusColor(report.estado)}
                      size="small"
                    />
                  </Box>
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {report.nombre}
                  </Typography>
                  {report.error_mensaje && (
                    <Typography variant="caption" color="error">
                      {report.error_mensaje}
                    </Typography>
                  )}
                </TableCell>
                
                <TableCell>
                  <Chip label={report.tipo_reporte} variant="outlined" size="small" />
                </TableCell>
                
                <TableCell>
                  <Chip label={report.formato} variant="outlined" size="small" />
                </TableCell>
                
                <TableCell>
                  <Typography variant="body2">
                    {formatDate(report.fecha_inicio)}
                  </Typography>
                  {report.fecha_fin && (
                    <Typography variant="caption" color="text.secondary">
                      Fin: {formatDate(report.fecha_fin)}
                    </Typography>
                  )}
                </TableCell>
                
                <TableCell>
                  {report.total_registros ? (
                    <Typography variant="body2">
                      {report.total_registros.toLocaleString()}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      -
                    </Typography>
                  )}
                </TableCell>
                
                <TableCell>
                  {report.estado === 'PROCESANDO' && report.progreso !== undefined ? (
                    <Box sx={{ width: '100%' }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={report.progreso} 
                        sx={{ mb: 0.5 }}
                      />
                      <Typography variant="caption">
                        {report.progreso}%
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      {report.estado === 'COMPLETADO' ? '100%' : '-'}
                    </Typography>
                  )}
                </TableCell>
                
                <TableCell align="right">
                  <Box display="flex" justifyContent="flex-end" gap={1}>
                    {canDownload(report) && (
                      <Tooltip title="Descargar">
                        <IconButton
                          size="small"
                          onClick={() => onDownload(report.id)}
                          color="primary"
                        >
                          <DownloadIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    
                    <IconButton
                      size="small"
                      onClick={(e) => handleMenuClick(e, report)}
                    >
                      <MoreIcon />
                    </IconButton>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={reports.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Filas por página:"
          labelDisplayedRows={({ from, to, count }) => 
            `${from}-${to} de ${count !== -1 ? count : `más de ${to}`}`
          }
        />
      </TableContainer>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleCloseMenu}
      >
        {selectedReport && canDownload(selectedReport) && (
          <MenuItem onClick={() => {
            onDownload(selectedReport.id)
            handleCloseMenu()
          }}>
            <ListItemIcon>
              <DownloadIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Descargar</ListItemText>
          </MenuItem>
        )}
        
        <MenuItem onClick={() => selectedReport && handleDeleteClick(selectedReport)}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Eliminar</ListItemText>
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Confirmar Eliminación</DialogTitle>
        <DialogContent>
          {reportToDelete && (
            <Box>
              <Alert severity="warning" sx={{ mb: 2 }}>
                Esta acción no se puede deshacer
              </Alert>
              <Typography>
                ¿Está seguro que desea eliminar el reporte "{reportToDelete.nombre}"?
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Generado el {formatDate(reportToDelete.fecha_inicio)}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            Cancelar
          </Button>
          <Button 
            onClick={handleConfirmDelete}
            color="error"
            variant="contained"
          >
            Eliminar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default ReportHistory