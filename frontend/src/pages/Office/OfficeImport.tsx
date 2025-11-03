import React, { useState, useRef } from 'react'
import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material'
import {
  CloudUpload as UploadIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ArrowBack as BackIcon,
  Download as DownloadIcon
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { officeService, ImportResult } from '../../services/officeService'

const OfficeImport: React.FC = () => {
  const navigate = useNavigate()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [activeStep, setActiveStep] = useState(0)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)

  const steps = ['Seleccionar Archivo', 'Procesar Importación', 'Resultados']

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      setActiveStep(1)
    }
  }

  const handleImport = async () => {
    if (!selectedFile) return

    setImporting(true)
    try {
      const result = await officeService.importarExcel(selectedFile)
      setImportResult(result)
      setActiveStep(2)
    } catch (error: any) {
      setImportResult({
        success: false,
        message: error.response?.data?.message || 'Error al procesar el archivo',
        created: 0,
        updated: 0,
        errors: []
      })
      setActiveStep(2)
    } finally {
      setImporting(false)
    }
  }

  const handleReset = () => {
    setActiveStep(0)
    setSelectedFile(null)
    setImportResult(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const downloadTemplate = () => {
    // Create a sample Excel template
    const csvContent = `Código,Nombre,Descripción,Responsable,Cargo Responsable,Teléfono,Email,Ubicación,Estado
001,Dirección General,Oficina principal de la dirección,Juan Pérez,Director General,051-123456,director@drtc.gob.pe,Primer Piso,true
002,Oficina de Administración,Gestión administrativa y financiera,María García,Jefe de Administración,051-123457,admin@drtc.gob.pe,Segundo Piso,true`
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'plantilla_oficinas.csv')
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Instrucciones para la Importación
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <InfoIcon color="info" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Formato de Archivo"
                      secondary="El archivo debe ser Excel (.xlsx) o CSV con las columnas requeridas"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <InfoIcon color="info" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Columnas Requeridas"
                      secondary="Código, Nombre, Descripción, Responsable, Cargo Responsable, Teléfono, Email, Ubicación, Estado"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <WarningIcon color="warning" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Códigos Únicos"
                      secondary="Los códigos de oficina deben ser únicos"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <InfoIcon color="info" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Estados Válidos"
                      secondary="true (activa) o false (inactiva)"
                    />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <InfoIcon color="info" />
                    </ListItemIcon>
                    <ListItemText
                      primary="Actualización"
                      secondary="Si el código ya existe, se actualizará la información"
                    />
                  </ListItem>
                </List>
                
                <Box display="flex" gap={2} mt={2}>
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={downloadTemplate}
                  >
                    Descargar Plantilla
                  </Button>
                </Box>
              </CardContent>
            </Card>

            <Paper
              sx={{
                p: 4,
                textAlign: 'center',
                border: '2px dashed',
                borderColor: 'primary.main',
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: 'action.hover'
                }
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Seleccionar Archivo de Oficinas
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Haga clic aquí o arrastre el archivo Excel/CSV
              </Typography>
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
            </Paper>
          </Box>
        )

      case 1:
        return (
          <Box>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Archivo Seleccionado
                </Typography>
                <Typography variant="body1">
                  <strong>Nombre:</strong> {selectedFile?.name}
                </Typography>
                <Typography variant="body1">
                  <strong>Tamaño:</strong> {selectedFile ? (selectedFile.size / 1024).toFixed(2) : 0} KB
                </Typography>
                <Typography variant="body1">
                  <strong>Tipo:</strong> {selectedFile?.type}
                </Typography>
              </CardContent>
            </Card>

            {importing && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="body1" gutterBottom>
                  Procesando archivo...
                </Typography>
                <LinearProgress />
              </Box>
            )}

            <Box display="flex" gap={2}>
              <Button
                variant="outlined"
                onClick={handleReset}
                disabled={importing}
              >
                Cambiar Archivo
              </Button>
              <Button
                variant="contained"
                onClick={handleImport}
                disabled={importing}
              >
                {importing ? 'Procesando...' : 'Importar Oficinas'}
              </Button>
            </Box>
          </Box>
        )

      case 2:
        return (
          <Box>
            {importResult && (
              <>
                <Alert
                  severity={importResult.success ? 'success' : 'error'}
                  sx={{ mb: 3 }}
                >
                  {importResult.message}
                </Alert>

                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Resumen de Importación
                    </Typography>
                    <Box display="flex" gap={4}>
                      <Box>
                        <Typography variant="h4" color="success.main">
                          {importResult.created}
                        </Typography>
                        <Typography variant="body2">
                          Oficinas Creadas
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="h4" color="info.main">
                          {importResult.updated}
                        </Typography>
                        <Typography variant="body2">
                          Oficinas Actualizadas
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="h4" color="error.main">
                          {importResult.errors.length}
                        </Typography>
                        <Typography variant="body2">
                          Errores
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>

                {importResult.errors.length > 0 && (
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Errores Encontrados
                      </Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Fila</TableCell>
                              <TableCell>Campo</TableCell>
                              <TableCell>Error</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {importResult.errors.map((error, index) => (
                              <TableRow key={index}>
                                <TableCell>{error.row}</TableCell>
                                <TableCell>
                                  <Chip label={error.field} size="small" />
                                </TableCell>
                                <TableCell>{error.message}</TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </CardContent>
                  </Card>
                )}

                <Box display="flex" gap={2} mt={3}>
                  <Button
                    variant="outlined"
                    onClick={handleReset}
                  >
                    Importar Otro Archivo
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => navigate('/offices')}
                  >
                    Ver Oficinas
                  </Button>
                </Box>
              </>
            )}
          </Box>
        )

      default:
        return null
    }
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/offices')}
          sx={{ mr: 2 }}
        >
          Volver
        </Button>
        <Typography variant="h4">
          Importar Oficinas
        </Typography>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {renderStepContent()}
      </Paper>
    </Box>
  )
}

export default OfficeImport