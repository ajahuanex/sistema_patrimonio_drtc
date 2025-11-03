import React, { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Chip
} from '@mui/material'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  AreaChart,
  Area,
  ResponsiveContainer
} from 'recharts'

import { ReportStatistics, ChartData, CHART_COLORS } from '../../types/reports'

interface InteractiveChartsProps {
  statistics: ReportStatistics
  loading?: boolean
}

type ChartType = 'bar' | 'pie' | 'line' | 'area'
type DataType = 'estado' | 'oficina' | 'grupo'

const InteractiveCharts: React.FC<InteractiveChartsProps> = ({
  statistics,
  loading = false
}) => {
  const [chartType, setChartType] = useState<ChartType>('bar')
  const [dataType, setDataType] = useState<DataType>('estado')

  const getChartData = (): ChartData[] => {
    switch (dataType) {
      case 'estado':
        return statistics.por_estado || []
      case 'oficina':
        return statistics.por_oficina || []
      case 'grupo':
        return statistics.por_grupo || []
      default:
        return []
    }
  }

  const getDataTypeLabel = (): string => {
    switch (dataType) {
      case 'estado':
        return 'Estados de Bienes'
      case 'oficina':
        return 'Oficinas'
      case 'grupo':
        return 'Grupos de Catálogo'
      default:
        return ''
    }
  }

  const chartData = getChartData()

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="name" 
          angle={-45}
          textAnchor="end"
          height={100}
          interval={0}
        />
        <YAxis />
        <RechartsTooltip 
          formatter={(value, name) => [value, 'Cantidad']}
          labelFormatter={(label) => `${getDataTypeLabel()}: ${label}`}
        />
        <Legend />
        <Bar 
          dataKey="value" 
          fill="#8884d8"
          name="Cantidad de Bienes"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percentage }) => `${name}: ${percentage}%`}
          outerRadius={120}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
          ))}
        </Pie>
        <RechartsTooltip formatter={(value) => [value, 'Cantidad']} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )

  const renderLineChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="name"
          angle={-45}
          textAnchor="end"
          height={100}
          interval={0}
        />
        <YAxis />
        <RechartsTooltip 
          formatter={(value) => [value, 'Cantidad']}
          labelFormatter={(label) => `${getDataTypeLabel()}: ${label}`}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="value" 
          stroke="#8884d8" 
          strokeWidth={3}
          name="Cantidad de Bienes"
        />
      </LineChart>
    </ResponsiveContainer>
  )

  const renderAreaChart = () => (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="name"
          angle={-45}
          textAnchor="end"
          height={100}
          interval={0}
        />
        <YAxis />
        <RechartsTooltip 
          formatter={(value) => [value, 'Cantidad']}
          labelFormatter={(label) => `${getDataTypeLabel()}: ${label}`}
        />
        <Legend />
        <Area 
          type="monotone" 
          dataKey="value" 
          stroke="#8884d8" 
          fill="#8884d8"
          fillOpacity={0.6}
          name="Cantidad de Bienes"
        />
      </AreaChart>
    </ResponsiveContainer>
  )

  const renderChart = () => {
    if (loading) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={400}>
          <Typography>Cargando datos...</Typography>
        </Box>
      )
    }

    if (!chartData || chartData.length === 0) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height={400}>
          <Typography color="text.secondary">
            No hay datos disponibles para mostrar
          </Typography>
        </Box>
      )
    }

    switch (chartType) {
      case 'bar':
        return renderBarChart()
      case 'pie':
        return renderPieChart()
      case 'line':
        return renderLineChart()
      case 'area':
        return renderAreaChart()
      default:
        return renderBarChart()
    }
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">
          Visualizaciones Interactivas
        </Typography>
        
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Datos a mostrar</InputLabel>
            <Select
              value={dataType}
              onChange={(e) => setDataType(e.target.value as DataType)}
              label="Datos a mostrar"
            >
              <MenuItem value="estado">Por Estado</MenuItem>
              <MenuItem value="oficina">Por Oficina</MenuItem>
              <MenuItem value="grupo">Por Grupo</MenuItem>
            </Select>
          </FormControl>

          <ToggleButtonGroup
            value={chartType}
            exclusive
            onChange={(_, newType) => newType && setChartType(newType)}
            size="small"
          >
            <ToggleButton value="bar">
              <Tooltip title="Gráfico de Barras">
                <span>📊</span>
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="pie">
              <Tooltip title="Gráfico Circular">
                <span>🥧</span>
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="line">
              <Tooltip title="Gráfico de Líneas">
                <span>📈</span>
              </Tooltip>
            </ToggleButton>
            <ToggleButton value="area">
              <Tooltip title="Gráfico de Área">
                <span>📉</span>
              </Tooltip>
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Total de Bienes
              </Typography>
              <Typography variant="h4">
                {statistics.total_bienes?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {statistics.valor_total_estimado && (
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Valor Total Estimado
                </Typography>
                <Typography variant="h6">
                  S/ {statistics.valor_total_estimado.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        
        {statistics.bienes_sin_mantenimiento && (
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Sin Mantenimiento
                </Typography>
                <Typography variant="h6" color="warning.main">
                  {statistics.bienes_sin_mantenimiento}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
        
        {statistics.alertas_depreciacion && (
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Alertas Depreciación
                </Typography>
                <Typography variant="h6" color="error.main">
                  {statistics.alertas_depreciacion}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Main Chart */}
      <Box sx={{ mb: 3 }}>
        {renderChart()}
      </Box>

      {/* Data Summary */}
      {chartData && chartData.length > 0 && (
        <Box>
          <Typography variant="subtitle1" gutterBottom>
            Resumen de {getDataTypeLabel()}
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={1}>
            {chartData.map((item, index) => (
              <Chip
                key={item.name}
                label={`${item.name}: ${item.value} (${item.percentage}%)`}
                sx={{
                  backgroundColor: CHART_COLORS[index % CHART_COLORS.length],
                  color: 'white'
                }}
              />
            ))}
          </Box>
        </Box>
      )}
    </Paper>
  )
}

export default InteractiveCharts