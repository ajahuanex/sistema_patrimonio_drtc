import { useState, useEffect, useCallback } from 'react'

// Simple debounce function
const debounce = (func: Function, wait: number) => {
  let timeout: NodeJS.Timeout
  return (...args: any[]) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => func.apply(null, args), wait)
  }
}

export interface ValidationRule {
  field: string
  validator: (value: any, formData?: any) => Promise<string | null>
  debounceMs?: number
}

export interface ValidationState {
  [field: string]: {
    isValidating: boolean
    error: string | null
    isValid: boolean
  }
}

export const useRealTimeValidation = (rules: ValidationRule[]) => {
  const [validationState, setValidationState] = useState<ValidationState>({})

  // Initialize validation state
  useEffect(() => {
    const initialState: ValidationState = {}
    rules.forEach(rule => {
      initialState[rule.field] = {
        isValidating: false,
        error: null,
        isValid: true
      }
    })
    setValidationState(initialState)
  }, [rules])

  // Create debounced validators
  const debouncedValidators = useCallback(() => {
    const validators: { [field: string]: any } = {}
    
    rules.forEach(rule => {
      validators[rule.field] = debounce(
        async (value: any, formData?: any) => {
          setValidationState(prev => ({
            ...prev,
            [rule.field]: {
              ...prev[rule.field],
              isValidating: true
            }
          }))

          try {
            const error = await rule.validator(value, formData)
            setValidationState(prev => ({
              ...prev,
              [rule.field]: {
                isValidating: false,
                error,
                isValid: !error
              }
            }))
          } catch (err) {
            setValidationState(prev => ({
              ...prev,
              [rule.field]: {
                isValidating: false,
                error: 'Error de validación',
                isValid: false
              }
            }))
          }
        },
        rule.debounceMs || 500
      )
    })

    return validators
  }, [rules])

  const validators = debouncedValidators()

  const validateField = useCallback((field: string, value: any, formData?: any) => {
    if (validators[field]) {
      validators[field](value, formData)
    }
  }, [validators])

  const validateAllFields = useCallback(async (formData: any): Promise<boolean> => {
    const validationPromises = rules.map(async rule => {
      const error = await rule.validator(formData[rule.field], formData)
      return { field: rule.field, error }
    })

    const results = await Promise.all(validationPromises)
    
    const newState: ValidationState = {}
    let allValid = true

    results.forEach(({ field, error }) => {
      newState[field] = {
        isValidating: false,
        error,
        isValid: !error
      }
      if (error) allValid = false
    })

    setValidationState(prev => ({ ...prev, ...newState }))
    return allValid
  }, [rules])

  const clearValidation = useCallback((field?: string) => {
    if (field) {
      setValidationState(prev => ({
        ...prev,
        [field]: {
          isValidating: false,
          error: null,
          isValid: true
        }
      }))
    } else {
      const clearedState: ValidationState = {}
      rules.forEach(rule => {
        clearedState[rule.field] = {
          isValidating: false,
          error: null,
          isValid: true
        }
      })
      setValidationState(clearedState)
    }
  }, [rules])

  const isFormValid = useCallback(() => {
    return Object.values(validationState).every(state => state.isValid && !state.isValidating)
  }, [validationState])

  const hasValidationErrors = useCallback(() => {
    return Object.values(validationState).some(state => state.error !== null)
  }, [validationState])

  const isValidating = useCallback((field?: string) => {
    if (field) {
      return validationState[field]?.isValidating || false
    }
    return Object.values(validationState).some(state => state.isValidating)
  }, [validationState])

  return {
    validationState,
    validateField,
    validateAllFields,
    clearValidation,
    isFormValid,
    hasValidationErrors,
    isValidating
  }
}

// Common validation functions
export const createUniqueValidator = (
  checkFunction: (value: string, excludeId?: number) => Promise<{ disponible: boolean }>,
  excludeId?: number,
  errorMessage = 'Este valor ya existe'
) => {
  return async (value: string): Promise<string | null> => {
    if (!value || !value.trim()) {
      return null // Let required validation handle empty values
    }

    try {
      const result = await checkFunction(value.trim(), excludeId)
      return result.disponible ? null : errorMessage
    } catch (error) {
      return 'Error al validar'
    }
  }
}

export const createRequiredValidator = (errorMessage = 'Este campo es requerido') => {
  return async (value: any): Promise<string | null> => {
    if (value === null || value === undefined || (typeof value === 'string' && !value.trim())) {
      return errorMessage
    }
    return null
  }
}

export const createEmailValidator = (errorMessage = 'Email no válido') => {
  return async (value: string): Promise<string | null> => {
    if (!value || !value.trim()) {
      return null // Let required validation handle empty values
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(value.trim()) ? null : errorMessage
  }
}

export const createMinLengthValidator = (minLength: number, errorMessage?: string) => {
  return async (value: string): Promise<string | null> => {
    if (!value || !value.trim()) {
      return null // Let required validation handle empty values
    }

    return value.trim().length >= minLength 
      ? null 
      : errorMessage || `Debe tener al menos ${minLength} caracteres`
  }
}

export const createMaxLengthValidator = (maxLength: number, errorMessage?: string) => {
  return async (value: string): Promise<string | null> => {
    if (!value) {
      return null
    }

    return value.length <= maxLength 
      ? null 
      : errorMessage || `No puede exceder ${maxLength} caracteres`
  }
}