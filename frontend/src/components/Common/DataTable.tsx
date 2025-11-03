import React from 'react'
import {
  DataGrid,
  GridColDef,
  GridRowsProp,
  GridToolbar,
  GridActionsCellItem,
  GridRowId,
} from '@mui/x-data-grid'
import {
  Paper,
  Box,
  Typography,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material'

interface DataTableProps {
  title?: string
  rows: GridRowsProp
  columns: GridColDef[]
  loading?: boolean
  onEdit?: (id: GridRowId) => void
  onDelete?: (id: GridRowId) => void
  onView?: (id: GridRowId) => void
  hideActions?: boolean
  height?: number
}

const DataTable: React.FC<DataTableProps> = ({
  title,
  rows,
  columns,
  loading = false,
  onEdit,
  onDelete,
  onView,
  hideActions = false,
  height = 600,
}) => {
  const actionsColumn: GridColDef = {
    field: 'actions',
    type: 'actions',
    headerName: 'Acciones',
    width: 120,
    getActions: (params) => {
      const actions = []
      
      if (onView) {
        actions.push(
          <GridActionsCellItem
            icon={
              <Tooltip title="Ver">
                <ViewIcon />
              </Tooltip>
            }
            label="Ver"
            onClick={() => onView(params.id)}
          />
        )
      }
      
      if (onEdit) {
        actions.push(
          <GridActionsCellItem
            icon={
              <Tooltip title="Editar">
                <EditIcon />
              </Tooltip>
            }
            label="Editar"
            onClick={() => onEdit(params.id)}
          />
        )
      }
      
      if (onDelete) {
        actions.push(
          <GridActionsCellItem
            icon={
              <Tooltip title="Eliminar">
                <DeleteIcon />
              </Tooltip>
            }
            label="Eliminar"
            onClick={() => onDelete(params.id)}
            showInMenu
          />
        )
      }
      
      return actions
    },
  }

  const finalColumns = hideActions ? columns : [...columns, actionsColumn]

  return (
    <Paper sx={{ p: 2 }}>
      {title && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="h6" component="h2">
            {title}
          </Typography>
        </Box>
      )}
      <Box sx={{ height, width: '100%' }}>
        <DataGrid
          rows={rows}
          columns={finalColumns}
          loading={loading}
          slots={{ toolbar: GridToolbar }}
          slotProps={{
            toolbar: {
              showQuickFilter: true,
              quickFilterProps: { debounceMs: 500 },
            },
          }}
          pageSizeOptions={[25, 50, 100]}
          initialState={{
            pagination: {
              paginationModel: { pageSize: 25 },
            },
          }}
          disableRowSelectionOnClick
          sx={{
            '& .MuiDataGrid-toolbarContainer': {
              borderBottom: '1px solid',
              borderColor: 'divider',
              mb: 1,
            },
          }}
        />
      </Box>
    </Paper>
  )
}

export default DataTable