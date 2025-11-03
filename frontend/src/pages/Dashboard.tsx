import React from 'react'
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
} from '@mui/material'
import {
  Inventory as InventoryIcon,
  Category as CategoryIcon,
  Business as BusinessIcon,
  Assessment as ReportsIcon,
  TrendingUp,
  Warning,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'

const Dashboard: React.FC = () => {
  const navigate = useNavigate()

  const stats = [
    {
      title: 'Total Bienes',
      value: '1,234',
      icon: <InventoryIcon sx={{ fontSize: 40 }} />,
      color: '#1976d2',
      trend: '+5.2%',
    },
    {
      title: 'Bienes Nuevos',
      value: '456',
      icon: <TrendingUp sx={{ fontSize: 40 }} />,
      color: '#2e7d32',
      trend: '+12.1%',
    },
    {
      title: 'Requieren Atención',
      value: '23',
      icon: <Warning sx={{ fontSize: 40 }} />,
      color: '#ed6c02',
      trend: '-2.3%',
    },
    {
      title: 'Oficinas Activas',
      value: '45',
      icon: <BusinessIcon sx={{ fontSize: 40 }} />,
      color: '#9c27b0',
      trend: '0%',
    },
  ]

  const quickActions = [
    {
      title: 'Registrar Nuevo Bien',
      description: 'Agregar un nuevo bien patrimonial al inventario',
      action: () => navigate('/inventory/new'),
      color: 'primary',
    },
    {
      title: 'Importar Catálogo',
      description: 'Cargar catálogo oficial desde archivo Excel',
      action: () => navigate('/catalog/import'),
      color: 'secondary',
    },
    {
      title: 'Generar Reporte',
      description: 'Crear reportes personalizados del patrimonio',
      action: () => navigate('/reports'),
      color: 'success',
    },
    {
      title: 'Gestionar Oficinas',
      description: 'Administrar oficinas y responsables',
      action: () => navigate('/offices'),
      color: 'info',
    },
  ]

  const recentActivity = [
    {
      action: 'Bien registrado',
      item: 'Computadora HP ProDesk 400',
      time: 'Hace 2 horas',
      user: 'Juan Pérez',
    },
    {
      action: 'Estado actualizado',
      item: 'Impresora Canon LBP6030',
      time: 'Hace 4 horas',
      user: 'María García',
    },
    {
      action: 'Movimiento registrado',
      item: 'Escritorio de madera',
      time: 'Hace 6 horas',
      user: 'Carlos López',
    },
  ]

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Resumen general del sistema de patrimonio
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {stats.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Paper
              sx={{
                p: 2,
                display: 'flex',
                alignItems: 'center',
                height: 120,
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 60,
                  height: 60,
                  borderRadius: 2,
                  backgroundColor: stat.color + '20',
                  color: stat.color,
                  mr: 2,
                }}
              >
                {stat.icon}
              </Box>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  {stat.value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {stat.title}
                </Typography>
                <Chip
                  label={stat.trend}
                  size="small"
                  color={stat.trend.startsWith('+') ? 'success' : stat.trend.startsWith('-') ? 'error' : 'default'}
                  sx={{ mt: 0.5 }}
                />
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Quick Actions */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Acciones Rápidas
            </Typography>
            <Grid container spacing={2}>
              {quickActions.map((action, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <Card sx={{ height: '100%' }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {action.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {action.description}
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button
                        size="small"
                        color={action.color as any}
                        onClick={action.action}
                      >
                        Ir
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Actividad Reciente
            </Typography>
            <Box>
              {recentActivity.map((activity, index) => (
                <Box
                  key={index}
                  sx={{
                    py: 2,
                    borderBottom: index < recentActivity.length - 1 ? '1px solid' : 'none',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                    {activity.action}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {activity.item}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {activity.time} • {activity.user}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard