import React from 'react'
import {
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Autocomplete,
  Box,
  CircularProgress,
  InputAdornment
} from '@mui/material'
import { Controller, Control, FieldError } from 'react-hook-form'

interface Option {
  value: string | number
  label: string
}

interface FormFieldProps {
  // React Hook Form props
  name?: string
  control?: Control<any>
  error?: FieldError
  
  // Direct props (for non-react-hook-form usage)
  label: string
  value?: any
  onChange?: (value: any) => void
  
  // Common props
  type?: 'text' | 'email' | 'password' | 'number' | 'date' | 'select' | 'autocomplete' | 'textarea'
  options?: Option[]
  required?: boolean
  disabled?: boolean
  multiline?: boolean
  rows?: number
  fullWidth?: boolean
  size?: 'small' | 'medium'
  
  // Real-time validation props
  isValidating?: boolean
  validationError?: string | null
  onValidate?: (value: any) => void
}

const FormField: React.FC<FormFieldProps> = ({
  // React Hook Form props
  name,
  control,
  error,
  
  // Direct props
  label,
  value,
  onChange,
  
  // Common props
  type = 'text',
  options = [],
  required = false,
  disabled = false,
  multiline = false,
  rows = 4,
  fullWidth = true,
  size = 'medium',
  
  // Real-time validation props
  isValidating = false,
  validationError = null,
  onValidate,
}) => {
  // Determine if we're using React Hook Form or direct props
  const useDirectProps = !name || !control

  // Get the effective error (validation error takes precedence)
  const effectiveError = validationError || error?.message

  const handleChange = (newValue: any) => {
    if (onChange) {
      onChange(newValue)
    }
    if (onValidate) {
      onValidate(newValue)
    }
  }

  const renderEndAdornment = () => {
    if (isValidating) {
      return (
        <InputAdornment position="end">
          <CircularProgress size={20} />
        </InputAdornment>
      )
    }
    return undefined
  }

  const renderField = () => {
    switch (type) {
      case 'select':
        if (useDirectProps) {
          return (
            <FormControl fullWidth={fullWidth} error={!!effectiveError} size={size}>
              <InputLabel required={required}>{label}</InputLabel>
              <Select
                value={value || ''}
                onChange={(e) => handleChange(e.target.value)}
                label={label}
                disabled={disabled}
              >
                {options.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
              {effectiveError && <FormHelperText>{effectiveError}</FormHelperText>}
            </FormControl>
          )
        }
        
        return (
          <Controller
            name={name!}
            control={control!}
            render={({ field }) => (
              <FormControl fullWidth={fullWidth} error={!!effectiveError} size={size}>
                <InputLabel required={required}>{label}</InputLabel>
                <Select
                  {...field}
                  label={label}
                  disabled={disabled}
                  onChange={(e) => {
                    field.onChange(e)
                    handleChange(e.target.value)
                  }}
                >
                  {options.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
                {effectiveError && <FormHelperText>{effectiveError}</FormHelperText>}
              </FormControl>
            )}
          />
        )

      case 'autocomplete':
        if (useDirectProps) {
          return (
            <Autocomplete
              options={options}
              getOptionLabel={(option) => 
                typeof option === 'string' ? option : option.label
              }
              value={options.find(option => option.value === value) || null}
              onChange={(_, newValue) => handleChange(newValue?.value || '')}
              disabled={disabled}
              size={size}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={label}
                  required={required}
                  error={!!effectiveError}
                  helperText={effectiveError}
                  fullWidth={fullWidth}
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {renderEndAdornment()}
                        {params.InputProps.endAdornment}
                      </>
                    )
                  }}
                />
              )}
            />
          )
        }

        return (
          <Controller
            name={name!}
            control={control!}
            render={({ field: { onChange: fieldOnChange, value: fieldValue, ...field } }) => (
              <Autocomplete
                {...field}
                options={options}
                getOptionLabel={(option) => 
                  typeof option === 'string' ? option : option.label
                }
                value={options.find(option => option.value === fieldValue) || null}
                onChange={(_, newValue) => {
                  const newVal = newValue?.value || ''
                  fieldOnChange(newVal)
                  handleChange(newVal)
                }}
                disabled={disabled}
                size={size}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label={label}
                    required={required}
                    error={!!effectiveError}
                    helperText={effectiveError}
                    fullWidth={fullWidth}
                    InputProps={{
                      ...params.InputProps,
                      endAdornment: (
                        <>
                          {renderEndAdornment()}
                          {params.InputProps.endAdornment}
                        </>
                      )
                    }}
                  />
                )}
              />
            )}
          />
        )

      default:
        if (useDirectProps) {
          return (
            <TextField
              label={label}
              type={type}
              value={value || ''}
              onChange={(e) => handleChange(e.target.value)}
              multiline={multiline || type === 'textarea'}
              rows={multiline || type === 'textarea' ? rows : undefined}
              required={required}
              disabled={disabled}
              error={!!effectiveError}
              helperText={effectiveError}
              fullWidth={fullWidth}
              size={size}
              InputProps={{
                endAdornment: renderEndAdornment()
              }}
            />
          )
        }

        return (
          <Controller
            name={name!}
            control={control!}
            render={({ field }) => (
              <TextField
                {...field}
                label={label}
                type={type}
                multiline={multiline || type === 'textarea'}
                rows={multiline || type === 'textarea' ? rows : undefined}
                required={required}
                disabled={disabled}
                error={!!effectiveError}
                helperText={effectiveError}
                fullWidth={fullWidth}
                size={size}
                onChange={(e) => {
                  field.onChange(e)
                  handleChange(e.target.value)
                }}
                InputProps={{
                  endAdornment: renderEndAdornment()
                }}
              />
            )}
          />
        )
    }
  }

  return <Box sx={{ mb: 2 }}>{renderField()}</Box>
}

export default FormField