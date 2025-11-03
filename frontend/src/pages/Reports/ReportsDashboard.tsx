import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Alert,
  Snackbar,
  CircularProgress
} from '@mui/material'
import {
  Assessment as ReportsIcon,
  FilterList as FilterIcon,
  BarChart as ChartIcon,
  History as HistoryIcon
} from '@mui/icons-material'

import { 
  FilterParams, 
  ReportPreview, 
  ReportGenerationParams,
  GeneratedReport 
} from '../../types/reports'
import reportService from '../../services/reportService'
import AdvancedFilters from './AdvancedFilters'
import ReportPreviewComponent from './ReportPreview'
import ReportHistory from './ReportHistory'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`reports-tabpanel-${index}`}
      aria-labelledby={`reports-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

const ReportsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0)
  const [filters, setFilters] = useState<FilterParams>({})
  const [preview, setPreview] = useState<ReportPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [myReports, setMyReports] = useState<GeneratedReport[]>([])
  const [notification, setNotification] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error' | 'warning' | 'info'
  }>({
    open: false,
    message: '',
    severity: 'info'
  })

  useEffect(() => {
    loadMyReports()
  }, [])

  const loadMyReports = async () => {
    try {
      const reports = await reportService.getMyReports()
      setMyReports(reports)
    } catch (error) {
      console.error('Error loading reports:', error)
    }
  }

  const handleFiltersChange = (newFilters: FilterParams) => {
    setFilters(newFilters)
  }

  const handleApplyFilters = async () => {
    setLoading(true)
    try {
      const previewData = await reportService.getFilterPreview(filters)
      setPreview(previewData)
      
      if (previewData.success) {
        showNotification('Filtros aplicados correctamente', 'success')
      } else {
        showNotification('No se encontraron resultados con los filtros aplicados', 'warning')
      }
    } catch (error) {
      console.error('Error applying filters:', error)
      showNotification('Error al aplicar filtros', 'error')
      setPreview(null)
    } finally {
      setLoading(false)
    }
  }

  const handleClearFilters = () => {
    setFilters({})
    setPreview(null)
    showNotification('Filtros limpiados', 'info')
  }

  const handleGenerateReport = async (params: ReportGenerationParams) => {
    try {
      const report = await reportService.generateReport(params)
      setMyReports([report, ...myReports])
      showNotification(
        `Reporte "${params.nombre_reporte}" programado para generación. Recibirá una notificación cuando esté listo.`,
        'success'
      )
      
      // Switch to history tab to show the new report
      setActiveTab(2)
    } catch (error) {
      console.error('Error generating report:', error)
      showNotification('Error al generar el reporte', 'error')
    }
  }

  const handleDownloadReport = async (reportId: number) => {
    try {
      const blob = await reportService.downloadReport(reportId)
      const report = myReports.find(r => r.id === reportId)
      
      if (report) {
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        
        const extension = {
          'EXCEL': '.xlsx',
          'PDF': '.pdf',
          'CSV': '.csv',
          'ZPL': '.zpl'
        }[report.formato] || '.txt'
        
        link.download = `${report.nombre}_${new Date(report.fecha_inicio).toISOString().slice(0, 10)}${extension}`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        showNotification('Reporte descargado correctamente', 'success')
      }
    } catch (error) {
      console.error('Error downloading report:', error)
      showNotification('Error al descargar el reporte', 'error')
    }
  }

  const handleDeleteReport = async (reportId: number) => {
    try {
      await reportService.deleteReport(reportId)
      setMyReports(myReports.filter(r => r.id !== reportId))
      showNotification('Reporte eliminado correctamente', 'success')
    } catch (error) {
      console.error('Error deleting report:', error)
      showNotification('Error al eliminar el reporte', 'error')
    }
  }

  const showNotification = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setNotification({
      open: true,
      message,
      severity
    })
  }

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false })
  }

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue)
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom display="flex" alignItems="center">
        <ReportsIcon sx={{ mr: 1 }} />
        Módulo de Reportes
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Genere reportes personalizados con filtros avanzados y visualizaciones interactivas
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab 
            icon={<FilterIcon />} 
            label="Filtros Avanzados" 
            iconPosition="start"
          />
          <Tab 
            icon={<ChartIcon />} 
            label="Vista Previa y Gráficos" 
            iconPosition="start"
            disabled={!preview}
          />
          <Tab 
            icon={<HistoryIcon />} 
            label={`Mis Reportes (${myReports.length})`}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        <AdvancedFilters
          filters={filters}
          onFiltersChange={handleFiltersChange}
          onApplyFilters={handleApplyFilters}
          onClearFilters={handleClearFilters}
          loading={loading}
        />
        
        {preview && (
          <Alert severity="info" sx={{ mt: 2 }}>
            Se encontraron {preview.total_resultados.toLocaleString()} bienes. 
            Vaya a la pestaña "Vista Previa y Gráficos" para ver los resultados detallados.
          </Alert>
        )}
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <ReportPreviewComponent
          filters={filters}
          preview={preview}
          loading={loading}
          onGenerateReport={handleGenerateReport}
        />
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <ReportHistory
          reports={myReports}
          onDownload={handleDownloadReport}
          onDelete={handleDeleteReport}
          onRefresh={loadMyReports}
        />
      </TabPanel>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert 
          onClose={handleCloseNotification} 
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default ReportsDashboard