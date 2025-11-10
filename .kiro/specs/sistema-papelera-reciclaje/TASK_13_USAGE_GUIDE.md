# Task 13: Recycle Bin Templates - Usage Guide

## Overview
This guide explains how to use the recycle bin templates for managing deleted items in the system.

## Accessing the Recycle Bin

### For Administrators
1. Log in with an administrator account
2. Click on "Administración" in the navigation bar
3. Select "Papelera de Reciclaje"

### URL
Direct access: `/core/recycle-bin/`

## List View Features

### 1. Statistics Dashboard
At the top of the page, you'll see four statistics boxes:
- **Total en Papelera:** Total number of deleted items
- **Próximos a Eliminar:** Items that will be auto-deleted soon (7 days or less)
- **Listos para Eliminar:** Items ready for auto-deletion (0 days)
- **Módulos Activos:** Number of modules with deleted items

### 2. Quick Filters
Use these buttons for instant filtering:
- **Listos para eliminar (Red):** Items with 0 days remaining
- **Críticos (Yellow):** Items with 1-3 days remaining
- **Advertencia (Yellow):** Items with 4-7 days remaining
- **Mis eliminaciones (Blue):** Items you deleted
- **Limpiar filtros (Gray):** Remove all filters

### 3. Advanced Filters
Click "Filtros Avanzados" to expand more options:
- **Búsqueda:** Search by object name
- **Módulo:** Filter by module (Oficinas, Bienes, Catálogo)
- **Tiempo restante:** Filter by days remaining
- **Estado:** Filter by status
- **Fecha desde/hasta:** Date range filter
- **Eliminado por:** Filter by user (admin only)

### 4. Viewing Items
The table shows:
- **Checkbox:** Select items for bulk operations
- **Objeto:** Name and deletion reason
- **Módulo:** Which module the item belongs to
- **Eliminado Por:** User who deleted it
- **Fecha Eliminación:** When it was deleted
- **Días Restantes:** Days until auto-deletion (color-coded)
- **Estado:** Current status badge
- **Acciones:** View and restore buttons

**Row Colors:**
- **Red border:** Ready for auto-deletion (0 days)
- **Yellow border:** Near auto-deletion (1-7 days)
- **Green border:** Safe (8+ days)

### 5. Bulk Operations

#### Restoring Multiple Items
1. Check the boxes next to items you want to restore
2. Click "Restaurar Seleccionados" (green button)
3. Confirm in the dialog
4. Items will be restored to their original state

#### Permanent Delete (Admin Only)
1. Check the boxes next to items you want to permanently delete
2. Click "Eliminar Permanentemente" (red button)
3. In the modal:
   - Enter the security code
   - Add optional notes
4. Click "Eliminar Permanentemente"
5. Items will be permanently removed from the database

### 6. Individual Actions

#### View Details
Click the eye icon (👁️) to see full details of an item.

#### Quick Restore
Click the restore icon (↩️) to restore an item immediately.

## Detail View Features

### 1. Header
Shows:
- Item status with animated indicator
- Status message (color-coded)
- Back button to list

### 2. Information Cards

#### General Information
- Object name
- Module
- Type
- ID
- Current status

#### Deletion Information
- Who deleted it
- When it was deleted
- When it will be auto-deleted
- Days remaining
- Deletion reason

### 3. Data Preview
Complete table showing all fields and values of the deleted object.

### 4. Alerts
- **Yellow Alert:** Restoration conflicts that need resolution
- **Red Alert:** Object no longer available

### 5. Actions

#### Restore
1. Click "Restaurar Elemento" (green button)
2. Review the confirmation modal
3. Click "Confirmar Restauración"
4. Item will be restored

#### Permanent Delete (Admin Only)
1. Click "Eliminar Permanentemente" (red button)
2. In the modal:
   - Enter security code
   - Type "ELIMINAR" exactly
   - Provide a reason (minimum 20 characters)
3. Click "Eliminar Permanentemente"
4. Item will be permanently deleted

## Visual Indicators

### Status Badges
- **🟢 En papelera:** Item is safe (8+ days)
- **🟡 Próximo a eliminar:** Item will be deleted soon (1-7 days)
- **🔴 Listo para eliminar:** Item will be deleted today

### Icons
- **🗑️ fa-trash-restore:** Recycle bin
- **↩️ fa-undo:** Restore action
- **👁️ fa-eye:** View details
- **🗑️ fa-trash:** Delete action
- **🔍 fa-search:** Search
- **🔧 fa-filter:** Filters
- **✓ fa-check:** Success
- **⚠️ fa-exclamation-triangle:** Warning
- **❌ fa-times-circle:** Error

## Responsive Design

### Desktop (1200px+)
- Full statistics dashboard (4 columns)
- Complete table with all columns
- Side-by-side information cards

### Tablet (768px - 1199px)
- Statistics in 2 columns
- Scrollable table
- Stacked information cards

### Mobile (< 768px)
- Statistics in 1 column
- Horizontal scroll for table
- Vertical button layout
- Collapsible sections

## Keyboard Navigation

### List View
- **Tab:** Navigate between elements
- **Space:** Toggle checkboxes
- **Enter:** Activate buttons/links

### Modals
- **Tab:** Navigate form fields
- **Esc:** Close modal
- **Enter:** Submit form

## Tips and Best Practices

### For Regular Users
1. Use "Mis eliminaciones" filter to see only your deleted items
2. Restore items before they expire
3. Check the days remaining regularly
4. Provide deletion reasons for future reference

### For Administrators
1. Review items near auto-deletion regularly
2. Use advanced filters to find specific items
3. Always provide a reason for permanent deletions
4. Keep the security code confidential
5. Use bulk operations for efficiency

### Performance
1. Use filters to reduce the number of displayed items
2. The table is paginated for better performance
3. Refresh the page to see latest updates

## Troubleshooting

### Can't see deleted items
- Check if filters are applied
- Verify you have permission to view the recycle bin
- Ensure items haven't been permanently deleted

### Can't restore an item
- Check for restoration conflicts (shown in detail view)
- Verify you have permission to restore
- Ensure the original object still exists

### Permanent delete button disabled
- Verify you're logged in as an administrator
- Check that you've filled all required fields
- Ensure the security code is correct

## Security Features

### Security Code
- Required for permanent deletions
- Stored in environment variables
- Never displayed in the interface
- Logged on every attempt

### Audit Trail
- All operations are logged
- Includes user, timestamp, and IP
- Permanent record for compliance

### Permissions
- Regular users: View and restore own deletions
- Administrators: View all, restore all, permanent delete

## Next Steps
After restoring or permanently deleting items, you can:
1. Return to the list view
2. Apply different filters
3. Perform more operations
4. Check audit logs for verification

## Support
For issues or questions:
1. Check the system documentation
2. Contact your system administrator
3. Review audit logs for operation history
