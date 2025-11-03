import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import InventoryList from './pages/Inventory/InventoryList'
import InventoryDetail from './pages/Inventory/InventoryDetail'
import InventoryForm from './pages/Inventory/InventoryForm'
import CatalogList from './pages/Catalog/CatalogList'
import CatalogImport from './pages/Catalog/CatalogImport'
import OfficeList from './pages/Office/OfficeList'
import OfficeImport from './pages/Office/OfficeImport'
import ReportsDashboard from './pages/Reports/ReportsDashboard'
import { AuthProvider } from './contexts/AuthContext'

function App() {
  return (
    <AuthProvider>
      <Box sx={{ display: 'flex' }}>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            
            {/* Inventory Routes */}
            <Route path="/inventory" element={<InventoryList />} />
            <Route path="/inventory/new" element={<InventoryForm />} />
            <Route path="/inventory/:id" element={<InventoryDetail />} />
            <Route path="/inventory/:id/edit" element={<InventoryForm />} />
            
            {/* Catalog Routes */}
            <Route path="/catalog" element={<CatalogList />} />
            <Route path="/catalog/import" element={<CatalogImport />} />
            
            {/* Office Routes */}
            <Route path="/offices" element={<OfficeList />} />
            <Route path="/offices/import" element={<OfficeImport />} />
            
            {/* Reports Routes */}
            <Route path="/reports" element={<ReportsDashboard />} />
          </Routes>
        </Layout>
      </Box>
    </AuthProvider>
  )
}

export default App