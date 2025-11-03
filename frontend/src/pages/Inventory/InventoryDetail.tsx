import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Grid,
  Chip,
  Button,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Alert,
  CircularProgress,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material'
import {
  Edit as EditIcon,
  QrCode as QrCodeIcon,
  History as HistoryIcon,
  SwapHoriz as MoveIcon,
  Update as UpdateIcon,
  Business as BusinessIcon,
  Category as CategoryIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
} from '@mui/icons-material'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import FormField from '../../components/Common/FormField'
import inventoryService from '../../services/inventoryService'
import {
  BienPatrimonial,
  HistorialEstado,
  MovimientoBien,
  Oficina,
  ESTADOS_BIEN,
  ESTADOS_BIEN_OPTIONS
} from '../../types/inventory'

const InventoryDetail: React.FC = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()

  // State
  const [bien, setBien] = useState<BienPatrimonial | null>(null)
  const [historial, setHistorial] = useState<HistorialEstado[]>([])
  const [movimientos, setMovimientos] = useState<MovimientoBien[]>([])
  const [oficinas, setOficinas] = useState<Oficina[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Dialogs
  const [updateStateDialog, setUpdateStateDialog] = useState(false)
  const [moveDialog, setMoveDialog] = useState(false)

  // Forms
  const { control: updateControl, handleSubmit: handleUpdateSubmit, reset: resetUpdate } = useForm({
    defaultValues: {
      estado_bien: '',
      observaciones: '',
    }
  })

  const { control: moveControl, handleSubmit: handleMoveSubmit, reset: resetMove } = useForm({
    defaultValues: {
      oficina_destino: 0,
      motivo: '',
      observaciones: '',
    }
  })

  useEffect(() => {
    if (id) {
      loadBienDetail(parseInt(id))
      loadOficinas()
    }
  }, [id])

  const loadBienDetail = async (bienId: number) => {
    try {
      setLoading(true)
      setError(null)

      const [bienData, historialData, movimientosData] = await Promise.all([
        inventoryService.getBien(bienId),
        inventoryService.getHistorialEstado(bienId),
        inventoryService.getMovimientos(bienId),
      ])

      setBien(bienData)
      setHistorial(historialData)
      setMovimientos(movimientosData)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar el bien')
    } finally {
      setLoading(false)
    }
  }

  const loadOficinas = async () => {
    try {
      const data = await inventoryService.getOficinas()
      setOficinas(data)
    } catch (err) {
      console.error('Error loading oficinas:', err)
    }
  }

  const handleUpdateState = async (data: any) => {
    if (!bien) return

    try {
      await inventoryService.updateEstado(bien.id, {
        estado_bien: data.estado_bien,
        observaciones: data.observaciones,
      })

      setUpdateStateDialog(false)
      resetUpdate()
      loadBienDetail(bien.id)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al actualizar el estado')
    }
  }

  const handleMove = async (data: any) => {
    if (!bien) return

    try {
      await inventoryService.createMovimiento({
        bien: bien.id,
        oficina_destino: data.oficina_destino,
        motivo: data.motivo,
        observaciones: data.observaciones,
      })

      setMoveDialog(false)
      resetMove()
      loadBienDetail(bien.id)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al crear el movimiento')
    }
  }

  const getEstadoColor = (estado: string) => {
    const colors = {
      'N': 'success',
      'B': 'primary',
      'R': 'warning',
      'M': 'error',
      'E': 'secondary',
      'C': 'default'
    }
    return colors[estado as keyof typeof colors] as any
  }

  const oficinaOptions = oficinas
    .filter(ofi => ofi.id !== bien?.oficina.id)
    .map(ofi => ({
      value: ofi.id,
      label: `${ofi.codigo} - ${ofi.nombre}`
    }))

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error || !bien) {
    return (
      <Box>
        <Alert severity="error">
          {error || 'Bien no encontrado'}
        </Alert>
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <div>
          <Typography variant="h4" gutterBottom>
            {bien.codigo_patrimonial}
          </Typography>
          <Typography variant="h6" color="text.secondary">
            {bien.catalogo.denominacion}
          </Typography>
        </div>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<UpdateIcon />}
            onClick={() => setUpdateStateDialog(true)}
          >
            Actualizar Estado
          </Button>
          <Button
            variant="outlined"
            startIcon={<MoveIcon />}
            onClick={() => setMoveDialog(true)}
          >
            Mover Bien
          </Button>
          <Button
            variant="contained"
            startIcon={<EditIcon />}
            onClick={() => navigate(`/inventory/${bien.id}/edit`)}
          >
            Editar
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Información Principal */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader
              avatar={<CategoryIcon />}
              title="Información del Bien"
              action={
                <Chip
                  label={ESTADOS_BIEN[bien.estado_bien as keyof typeof ESTADOS_BIEN]}
                  color={getEstadoColor(bien.estado_bien)}
                />
              }
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Código Patrimonial
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 'medium' }}>
                    {bien.codigo_patrimonial}
                  </Typography>
                </Grid>
                {bien.codigo_interno && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Código Interno
                    </Typography>
                    <Typography variant="body1">
                      {bien.codigo_interno}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">
                    Denominación
                  </Typography>
                  <Typography variant="body1">
                    {bien.catalogo.denominacion}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Grupo
                  </Typography>
                  <Typography variant="body1">
                    {bien.catalogo.grupo}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Clase
                  </Typography>
                  <Typography variant="body1">
                    {bien.catalogo.clase}
                  </Typography>
                </Grid>
                {bien.marca && (
                  <Grid item xs={12} sm={4}>
                    <Typography variant="body2" color="text.secondary">
                      Marca
                    </Typography>
                    <Typography variant="body1">
                      {bien.marca}
                    </Typography>
                  </Grid>
                )}
                {bien.modelo && (
                  <Grid item xs={12} sm={4}>
                    <Typography variant="body2" color="text.secondary">
                      Modelo
                    </Typography>
                    <Typography variant="body1">
                      {bien.modelo}
                    </Typography>
                  </Grid>
                )}
                {bien.color && (
                  <Grid item xs={12} sm={4}>
                    <Typography variant="body2" color="text.secondary">
                      Color
                    </Typography>
                    <Typography variant="body1">
                      {bien.color}
                    </Typography>
                  </Grid>
                )}
                {bien.serie && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Serie
                    </Typography>
                    <Typography variant="body1">
                      {bien.serie}
                    </Typography>
                  </Grid>
                )}
                {bien.dimension && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Dimensión
                    </Typography>
                    <Typography variant="body1">
                      {bien.dimension}
                    </Typography>
                  </Grid>
                )}
                {(bien.placa || bien.matricula || bien.nro_motor || bien.nro_chasis) && (
                  <>
                    <Grid item xs={12}>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="subtitle2" color="primary">
                        Información de Vehículo
                      </Typography>
                    </Grid>
                    {bien.placa && (
                      <Grid item xs={12} sm={3}>
                        <Typography variant="body2" color="text.secondary">
                          Placa
                        </Typography>
                        <Chip label={bien.placa} variant="outlined" />
                      </Grid>
                    )}
                    {bien.matricula && (
                      <Grid item xs={12} sm={3}>
                        <Typography variant="body2" color="text.secondary">
                          Matrícula
                        </Typography>
                        <Typography variant="body1">
                          {bien.matricula}
                        </Typography>
                      </Grid>
                    )}
                    {bien.nro_motor && (
                      <Grid item xs={12} sm={3}>
                        <Typography variant="body2" color="text.secondary">
                          Nro. Motor
                        </Typography>
                        <Typography variant="body1">
                          {bien.nro_motor}
                        </Typography>
                      </Grid>
                    )}
                    {bien.nro_chasis && (
                      <Grid item xs={12} sm={3}>
                        <Typography variant="body2" color="text.secondary">
                          Nro. Chasis
                        </Typography>
                        <Typography variant="body1">
                          {bien.nro_chasis}
                        </Typography>
                      </Grid>
                    )}
                  </>
                )}
                {bien.observaciones && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Observaciones
                    </Typography>
                    <Typography variant="body1">
                      {bien.observaciones}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Información de Ubicación y QR */}
        <Grid item xs={12} md={4}>
          <Grid container spacing={2}>
            {/* Ubicación Actual */}
            <Grid item xs={12}>
              <Card>
                <CardHeader
                  avatar={<BusinessIcon />}
                  title="Ubicación Actual"
                />
                <CardContent>
                  <Typography variant="h6">
                    {bien.oficina.nombre}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {bien.oficina.codigo}
                  </Typography>
                  {bien.oficina.ubicacion && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {bien.oficina.ubicacion}
                    </Typography>
                  )}
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    <strong>Responsable:</strong> {bien.oficina.responsable}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Código QR */}
            {bien.qr_code && (
              <Grid item xs={12}>
                <Card>
                  <CardHeader
                    avatar={<QrCodeIcon />}
                    title="Código QR"
                  />
                  <CardContent sx={{ textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {bien.qr_code}
                    </Typography>
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => window.open(bien.url_qr, '_blank')}
                    >
                      Ver QR Público
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Información Adicional */}
            <Grid item xs={12}>
              <Card>
                <CardHeader
                  avatar={<InfoIcon />}
                  title="Información Adicional"
                />
                <CardContent>
                  <Typography variant="body2" color="text.secondary">
                    Fecha de Registro
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 1 }}>
                    {new Date(bien.created_at).toLocaleDateString()}
                  </Typography>
                  
                  {bien.fecha_adquisicion && (
                    <>
                      <Typography variant="body2" color="text.secondary">
                        Fecha de Adquisición
                      </Typography>
                      <Typography variant="body1" sx={{ mb: 1 }}>
                        {new Date(bien.fecha_adquisicion).toLocaleDateString()}
                      </Typography>
                    </>
                  )}
                  
                  {bien.valor_adquisicion && (
                    <>
                      <Typography variant="body2" color="text.secondary">
                        Valor de Adquisición
                      </Typography>
                      <Typography variant="body1">
                        S/ {parseFloat(bien.valor_adquisicion).toLocaleString()}
                      </Typography>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* Historial de Estados */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              avatar={<HistoryIcon />}
              title="Historial de Estados"
            />
            <CardContent>
              {historial.length > 0 ? (
                <List>
                  {historial.map((item, index) => (
                    <ListItem key={item.id} divider={index < historial.length - 1}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: getEstadoColor(item.estado_nuevo) + '.main' }}>
                          <UpdateIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Chip
                              label={ESTADOS_BIEN[item.estado_anterior as keyof typeof ESTADOS_BIEN]}
                              size="small"
                              color={getEstadoColor(item.estado_anterior)}
                            />
                            →
                            <Chip
                              label={ESTADOS_BIEN[item.estado_nuevo as keyof typeof ESTADOS_BIEN]}
                              size="small"
                              color={getEstadoColor(item.estado_nuevo)}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              {new Date(item.fecha_cambio).toLocaleString()}
                            </Typography>
                            <Typography variant="body2">
                              Por: {item.usuario.first_name} {item.usuario.last_name}
                            </Typography>
                            {item.observaciones && (
                              <Typography variant="body2" sx={{ mt: 0.5 }}>
                                {item.observaciones}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  No hay cambios de estado registrados
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Historial de Movimientos */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              avatar={<MoveIcon />}
              title="Historial de Movimientos"
            />
            <CardContent>
              {movimientos.length > 0 ? (
                <List>
                  {movimientos.map((item, index) => (
                    <ListItem key={item.id} divider={index < movimientos.length - 1}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: item.confirmado ? 'success.main' : 'warning.main' }}>
                          <MoveIcon />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box>
                            <Typography variant="body2">
                              {item.oficina_origen.nombre} → {item.oficina_destino.nombre}
                            </Typography>
                            <Chip
                              label={item.confirmado ? 'Confirmado' : 'Pendiente'}
                              size="small"
                              color={item.confirmado ? 'success' : 'warning'}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2">
                              {new Date(item.fecha_movimiento).toLocaleString()}
                            </Typography>
                            <Typography variant="body2">
                              Motivo: {item.motivo}
                            </Typography>
                            {item.observaciones && (
                              <Typography variant="body2">
                                {item.observaciones}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 2 }}>
                  No hay movimientos registrados
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Update State Dialog */}
      <Dialog open={updateStateDialog} onClose={() => setUpdateStateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Actualizar Estado del Bien</DialogTitle>
        <form onSubmit={handleUpdateSubmit(handleUpdateState)}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormField
                  name="estado_bien"
                  control={updateControl}
                  label="Nuevo Estado"
                  type="select"
                  options={ESTADOS_BIEN_OPTIONS}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <FormField
                  name="observaciones"
                  control={updateControl}
                  label="Observaciones"
                  type="textarea"
                  rows={3}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setUpdateStateDialog(false)}>
              Cancelar
            </Button>
            <Button type="submit" variant="contained">
              Actualizar
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Move Dialog */}
      <Dialog open={moveDialog} onClose={() => setMoveDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Mover Bien a Otra Oficina</DialogTitle>
        <form onSubmit={handleMoveSubmit(handleMove)}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormField
                  name="oficina_destino"
                  control={moveControl}
                  label="Oficina Destino"
                  type="autocomplete"
                  options={oficinaOptions}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <FormField
                  name="motivo"
                  control={moveControl}
                  label="Motivo del Movimiento"
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <FormField
                  name="observaciones"
                  control={moveControl}
                  label="Observaciones"
                  type="textarea"
                  rows={3}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setMoveDialog(false)}>
              Cancelar
            </Button>
            <Button type="submit" variant="contained">
              Crear Movimiento
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  )
}

export default InventoryDetail