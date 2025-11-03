import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material'
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  QrCode as QrCodeIcon,
} from '@mui/icons-material'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { yupResolver } from '@hookform/resolvers/yup'
import * as yup from 'yup'
import FormField from '../../components/Common/FormField'
import inventoryService from '../../services/inventoryService'
import {
  BienPatrimonialForm,
  BienPatrimonial,
  Catalogo,
  Oficina,
  ESTADOS_BIEN_OPTIONS
} from '../../types/inventory'

// Validation schema
const validationSchema = yup.object({
  codigo_patrimonial: yup
    .string()
    .required('El código patrimonial es requerido')
    .min(3, 'El código debe tener al menos 3 caracteres'),
  codigo_interno: yup.string(),
  catalogo: yup
    .number()
    .required('Debe seleccionar una denominación del catálogo')
    .positive('Debe seleccionar una denominación válida'),
  oficina: yup
    .number()
    .required('Debe seleccionar una oficina')
    .positive('Debe seleccionar una oficina válida'),
  estado_bien: yup
    .string()
    .required('Debe seleccionar el estado del bien')
    .oneOf(['N', 'B', 'R', 'M', 'E', 'C'], 'Estado inválido'),
  marca: yup.string(),
  modelo: yup.string(),
  color: yup.string(),
  serie: yup.string(),
  dimension: yup.string(),
  placa: yup.string(),
  matricula: yup.string(),
  nro_motor: yup.string(),
  nro_chasis: yup.string(),
  observaciones: yup.string(),
  fecha_adquisicion: yup.date().nullable(),
  valor_adquisicion: yup
    .number()
    .nullable()
    .positive('El valor debe ser positivo'),
})

const InventoryForm: React.FC = () => {
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const isEditing = Boolean(id)

  // State
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [catalogos, setCatalogos] = useState<Catalogo[]>([])
  const [oficinas, setOficinas] = useState<Oficina[]>([])
  const [loadingData, setLoadingData] = useState(isEditing)

  // Form
  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isDirty },
    reset,
  } = useForm<BienPatrimonialForm>({
    resolver: yupResolver(validationSchema),
    defaultValues: {
      codigo_patrimonial: '',
      codigo_interno: '',
      catalogo: 0,
      oficina: 0,
      estado_bien: 'B',
      marca: '',
      modelo: '',
      color: '',
      serie: '',
      dimension: '',
      placa: '',
      matricula: '',
      nro_motor: '',
      nro_chasis: '',
      observaciones: '',
      fecha_adquisicion: null,
      valor_adquisicion: null,
    },
  })

  const watchedCodigoPatrimonial = watch('codigo_patrimonial')

  // Load initial data
  useEffect(() => {
    loadCatalogos()
    loadOficinas()
    if (isEditing && id) {
      loadBien(parseInt(id))
    }
  }, [id, isEditing])

  // Validate codigo patrimonial on change
  useEffect(() => {
    if (watchedCodigoPatrimonial && watchedCodigoPatrimonial.length >= 3) {
      validateCodigoPatrimonial(watchedCodigoPatrimonial)
    }
  }, [watchedCodigoPatrimonial])

  const loadCatalogos = async () => {
    try {
      const data = await inventoryService.getCatalogos()
      setCatalogos(data)
    } catch (err) {
      console.error('Error loading catalogos:', err)
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

  const loadBien = async (bienId: number) => {
    try {
      setLoadingData(true)
      const bien = await inventoryService.getBien(bienId)
      
      // Populate form with existing data
      reset({
        codigo_patrimonial: bien.codigo_patrimonial,
        codigo_interno: bien.codigo_interno,
        catalogo: bien.catalogo.id,
        oficina: bien.oficina.id,
        estado_bien: bien.estado_bien,
        marca: bien.marca,
        modelo: bien.modelo,
        color: bien.color,
        serie: bien.serie,
        dimension: bien.dimension,
        placa: bien.placa,
        matricula: bien.matricula,
        nro_motor: bien.nro_motor,
        nro_chasis: bien.nro_chasis,
        observaciones: bien.observaciones,
        fecha_adquisicion: bien.fecha_adquisicion,
        valor_adquisicion: bien.valor_adquisicion,
      })
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al cargar el bien')
    } finally {
      setLoadingData(false)
    }
  }

  const validateCodigoPatrimonial = async (codigo: string) => {
    try {
      const result = await inventoryService.validarCodigoPatrimonial(
        codigo,
        isEditing ? parseInt(id!) : undefined
      )
      if (!result.disponible) {
        setError('El código patrimonial ya existe')
      } else {
        setError(null)
      }
    } catch (err) {
      console.error('Error validating codigo:', err)
    }
  }

  const onSubmit = async (data: BienPatrimonialForm) => {
    try {
      setLoading(true)
      setError(null)
      setSuccess(null)

      if (isEditing && id) {
        await inventoryService.updateBien(parseInt(id), data)
        setSuccess('Bien actualizado correctamente')
      } else {
        await inventoryService.createBien(data)
        setSuccess('Bien registrado correctamente')
      }

      // Redirect after success
      setTimeout(() => {
        navigate('/inventory')
      }, 2000)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Error al guardar el bien')
    } finally {
      setLoading(false)
    }
  }

  const handleCancel = () => {
    if (isDirty) {
      if (window.confirm('¿Está seguro de cancelar? Se perderán los cambios no guardados.')) {
        navigate('/inventory')
      }
    } else {
      navigate('/inventory')
    }
  }

  const catalogoOptions = catalogos.map(cat => ({
    value: cat.id,
    label: `${cat.codigo} - ${cat.denominacion}`
  }))

  const oficinaOptions = oficinas.map(ofi => ({
    value: ofi.id,
    label: `${ofi.codigo} - ${ofi.nombre}`
  }))

  if (loadingData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          {isEditing ? 'Editar Bien' : 'Registrar Nuevo Bien'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {isEditing 
            ? 'Modifique los datos del bien patrimonial'
            : 'Complete la información del nuevo bien patrimonial'
          }
        </Typography>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Form */}
      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={3}>
            {/* Información Principal */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Información Principal
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormField
                name="codigo_patrimonial"
                control={control}
                label="Código Patrimonial"
                error={errors.codigo_patrimonial}
                required
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormField
                name="codigo_interno"
                control={control}
                label="Código Interno"
                error={errors.codigo_interno}
              />
            </Grid>

            <Grid item xs={12}>
              <FormField
                name="catalogo"
                control={control}
                label="Denominación del Bien"
                type="autocomplete"
                options={catalogoOptions}
                error={errors.catalogo}
                required
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormField
                name="oficina"
                control={control}
                label="Oficina"
                type="autocomplete"
                options={oficinaOptions}
                error={errors.oficina}
                required
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormField
                name="estado_bien"
                control={control}
                label="Estado del Bien"
                type="select"
                options={ESTADOS_BIEN_OPTIONS}
                error={errors.estado_bien}
                required
              />
            </Grid>

            {/* Características */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Características
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormField
                name="marca"
                control={control}
                label="Marca"
                error={errors.marca}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormField
                name="modelo"
                control={control}
                label="Modelo"
                error={errors.modelo}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <FormField
                name="color"
                control={control}
                label="Color"
                error={errors.color}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormField
                name="serie"
                control={control}
                label="Número de Serie"
                error={errors.serie}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormField
                name="dimension"
                control={control}
                label="Dimensión"
                error={errors.dimension}
              />
            </Grid>

            {/* Información de Vehículos */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Información de Vehículos (si aplica)
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} md={3}>
              <FormField
                name="placa"
                control={control}
                label="Placa"
                error={errors.placa}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <FormField
                name="matricula"
                control={control}
                label="Matrícula"
                error={errors.matricula}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <FormField
                name="nro_motor"
                control={control}
                label="Número de Motor"
                error={errors.nro_motor}
              />
            </Grid>

            <Grid item xs={12} md={3}>
              <FormField
                name="nro_chasis"
                control={control}
                label="Número de Chasis"
                error={errors.nro_chasis}
              />
            </Grid>

            {/* Información Adicional */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Información Adicional
              </Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormField
                name="fecha_adquisicion"
                control={control}
                label="Fecha de Adquisición"
                type="date"
                error={errors.fecha_adquisicion}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormField
                name="valor_adquisicion"
                control={control}
                label="Valor de Adquisición (S/)"
                type="number"
                error={errors.valor_adquisicion}
              />
            </Grid>

            <Grid item xs={12}>
              <FormField
                name="observaciones"
                control={control}
                label="Observaciones"
                type="textarea"
                rows={3}
                error={errors.observaciones}
              />
            </Grid>

            {/* Actions */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 3 }}>
                <Button
                  variant="outlined"
                  onClick={handleCancel}
                  startIcon={<CancelIcon />}
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
                >
                  {loading ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Registrar')}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  )
}

export default InventoryForm