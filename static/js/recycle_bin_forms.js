/**
 * Validaciones en tiempo real para formularios de papelera de reciclaje
 */

(function() {
    'use strict';

    // Configuración de validación
    const VALIDATION_CONFIG = {
        securityCode: {
            minLength: 1,
            message: 'El código de seguridad es requerido'
        },
        confirmText: {
            expectedValue: 'ELIMINAR',
            message: 'Debe escribir exactamente "ELIMINAR"'
        },
        reason: {
            minLength: 20,
            message: 'El motivo debe tener al menos 20 caracteres'
        }
    };

    /**
     * Inicializar validaciones cuando el DOM esté listo
     */
    document.addEventListener('DOMContentLoaded', function() {
        initRestoreFormValidation();
        initPermanentDeleteFormValidation();
        initBulkOperationFormValidation();
        initSecurityCodeStrength();
    });

    /**
     * Validación del formulario de restauración
     */
    function initRestoreFormValidation() {
        const restoreForm = document.getElementById('restoreForm');
        if (!restoreForm) return;

        const confirmCheckbox = document.getElementById('confirmRestore');
        const resolveConflicts = document.getElementById('resolveConflicts');
        const submitButton = restoreForm.querySelector('button[type="submit"]');

        // Validar checkbox de confirmación
        if (confirmCheckbox) {
            confirmCheckbox.addEventListener('change', function() {
                validateRestoreForm(restoreForm, submitButton);
            });
        }

        // Validar selección de resolución de conflictos
        if (resolveConflicts && resolveConflicts.type !== 'hidden') {
            resolveConflicts.addEventListener('change', function() {
                validateRestoreForm(restoreForm, submitButton);
                
                // Mostrar mensaje según la opción seleccionada
                const selectedOption = this.value;
                const messageDiv = document.getElementById('conflictResolutionMessage');
                
                if (messageDiv) {
                    if (selectedOption === 'rename') {
                        messageDiv.innerHTML = '<div class="alert alert-info"><i class="fas fa-info-circle"></i> El elemento será restaurado con un nuevo nombre para evitar conflictos.</div>';
                    } else if (selectedOption === 'replace') {
                        messageDiv.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> El elemento existente será reemplazado. Esta acción no se puede deshacer.</div>';
                    } else if (selectedOption === 'cancel') {
                        messageDiv.innerHTML = '<div class="alert alert-secondary"><i class="fas fa-times"></i> La restauración será cancelada.</div>';
                    } else {
                        messageDiv.innerHTML = '';
                    }
                }
            });
        }

        // Validación inicial
        validateRestoreForm(restoreForm, submitButton);
    }

    /**
     * Validar formulario de restauración completo
     */
    function validateRestoreForm(form, submitButton) {
        const confirmCheckbox = document.getElementById('confirmRestore');
        const resolveConflicts = document.getElementById('resolveConflicts');
        
        let isValid = true;

        // Verificar confirmación
        if (confirmCheckbox && !confirmCheckbox.checked) {
            isValid = false;
        }

        // Verificar resolución de conflictos si es visible
        if (resolveConflicts && resolveConflicts.type !== 'hidden') {
            if (!resolveConflicts.value || resolveConflicts.value === '') {
                isValid = false;
                showFieldError(resolveConflicts, 'Debe seleccionar un método de resolución');
            } else {
                clearFieldError(resolveConflicts);
            }
        }

        // Habilitar/deshabilitar botón de submit
        if (submitButton) {
            submitButton.disabled = !isValid;
        }

        return isValid;
    }

    /**
     * Validación del formulario de eliminación permanente
     */
    function initPermanentDeleteFormValidation() {
        const deleteForm = document.getElementById('permanentDeleteForm');
        if (!deleteForm) return;

        const securityCodeInput = document.getElementById('securityCode');
        const confirmTextInput = document.getElementById('confirmText');
        const reasonTextarea = deleteForm.querySelector('textarea[name="reason"]');
        const submitButton = deleteForm.querySelector('button[type="submit"]');

        // Validar código de seguridad en tiempo real
        if (securityCodeInput) {
            securityCodeInput.addEventListener('input', function() {
                validateSecurityCode(this);
                validatePermanentDeleteForm(deleteForm, submitButton);
            });

            securityCodeInput.addEventListener('blur', function() {
                validateSecurityCode(this);
            });
        }

        // Validar texto de confirmación en tiempo real
        if (confirmTextInput) {
            confirmTextInput.addEventListener('input', function() {
                validateConfirmText(this);
                validatePermanentDeleteForm(deleteForm, submitButton);
            });

            confirmTextInput.addEventListener('blur', function() {
                validateConfirmText(this);
            });
        }

        // Validar motivo en tiempo real
        if (reasonTextarea) {
            reasonTextarea.addEventListener('input', function() {
                validateReason(this);
                validatePermanentDeleteForm(deleteForm, submitButton);
            });

            reasonTextarea.addEventListener('blur', function() {
                validateReason(this);
            });
        }

        // Validación inicial
        validatePermanentDeleteForm(deleteForm, submitButton);
    }

    /**
     * Validar código de seguridad
     */
    function validateSecurityCode(input) {
        const value = input.value.trim();
        
        if (value.length === 0) {
            showFieldError(input, VALIDATION_CONFIG.securityCode.message);
            return false;
        }
        
        clearFieldError(input);
        return true;
    }

    /**
     * Validar texto de confirmación
     */
    function validateConfirmText(input) {
        const value = input.value.trim().toUpperCase();
        const expected = VALIDATION_CONFIG.confirmText.expectedValue;
        
        if (value !== expected) {
            showFieldError(input, VALIDATION_CONFIG.confirmText.message);
            return false;
        }
        
        clearFieldError(input);
        showFieldSuccess(input, '✓ Confirmación correcta');
        return true;
    }

    /**
     * Validar motivo de eliminación
     */
    function validateReason(textarea) {
        const value = textarea.value.trim();
        const minLength = VALIDATION_CONFIG.reason.minLength;
        const currentLength = value.length;
        
        // Actualizar contador de caracteres
        updateCharacterCount(textarea, currentLength, minLength);
        
        if (currentLength < minLength) {
            showFieldError(textarea, `${VALIDATION_CONFIG.reason.message} (${currentLength}/${minLength})`);
            return false;
        }
        
        clearFieldError(textarea);
        showFieldSuccess(textarea, `✓ Motivo válido (${currentLength} caracteres)`);
        return true;
    }

    /**
     * Actualizar contador de caracteres
     */
    function updateCharacterCount(textarea, current, min) {
        let counter = textarea.parentElement.querySelector('.character-count');
        
        if (!counter) {
            counter = document.createElement('small');
            counter.className = 'character-count form-text';
            textarea.parentElement.appendChild(counter);
        }
        
        const remaining = min - current;
        if (remaining > 0) {
            counter.textContent = `Faltan ${remaining} caracteres`;
            counter.className = 'character-count form-text text-warning';
        } else {
            counter.textContent = `${current} caracteres`;
            counter.className = 'character-count form-text text-success';
        }
    }

    /**
     * Validar formulario de eliminación permanente completo
     */
    function validatePermanentDeleteForm(form, submitButton) {
        const securityCodeInput = document.getElementById('securityCode');
        const confirmTextInput = document.getElementById('confirmText');
        const reasonTextarea = form.querySelector('textarea[name="reason"]');
        
        let isValid = true;

        if (securityCodeInput && !validateSecurityCode(securityCodeInput)) {
            isValid = false;
        }

        if (confirmTextInput && !validateConfirmText(confirmTextInput)) {
            isValid = false;
        }

        if (reasonTextarea && !validateReason(reasonTextarea)) {
            isValid = false;
        }

        // Habilitar/deshabilitar botón de submit
        if (submitButton) {
            submitButton.disabled = !isValid;
            
            if (isValid) {
                submitButton.classList.remove('btn-secondary');
                submitButton.classList.add('btn-danger');
            } else {
                submitButton.classList.remove('btn-danger');
                submitButton.classList.add('btn-secondary');
            }
        }

        return isValid;
    }

    /**
     * Validación del formulario de operaciones en lote
     */
    function initBulkOperationFormValidation() {
        const bulkForm = document.getElementById('bulkOperationForm');
        if (!bulkForm) return;

        const operationSelect = document.getElementById('bulkOperation');
        const securityCodeInput = document.getElementById('bulkSecurityCode');
        const confirmCheckbox = document.getElementById('confirmBulk');
        const submitButton = bulkForm.querySelector('button[type="submit"]');

        // Mostrar/ocultar código de seguridad según operación
        if (operationSelect) {
            operationSelect.addEventListener('change', function() {
                const securityCodeGroup = securityCodeInput ? securityCodeInput.closest('.form-group') : null;
                
                if (this.value === 'permanent_delete') {
                    if (securityCodeGroup) {
                        securityCodeGroup.style.display = 'block';
                        securityCodeInput.required = true;
                    }
                } else {
                    if (securityCodeGroup) {
                        securityCodeGroup.style.display = 'none';
                        securityCodeInput.required = false;
                    }
                }
                
                validateBulkOperationForm(bulkForm, submitButton);
            });
        }

        // Validar código de seguridad
        if (securityCodeInput) {
            securityCodeInput.addEventListener('input', function() {
                validateBulkOperationForm(bulkForm, submitButton);
            });
        }

        // Validar checkbox de confirmación
        if (confirmCheckbox) {
            confirmCheckbox.addEventListener('change', function() {
                validateBulkOperationForm(bulkForm, submitButton);
            });
        }

        // Validación inicial
        validateBulkOperationForm(bulkForm, submitButton);
    }

    /**
     * Validar formulario de operaciones en lote completo
     */
    function validateBulkOperationForm(form, submitButton) {
        const operationSelect = document.getElementById('bulkOperation');
        const securityCodeInput = document.getElementById('bulkSecurityCode');
        const confirmCheckbox = document.getElementById('confirmBulk');
        const entryIdsInput = form.querySelector('input[name="entry_ids"]');
        
        let isValid = true;

        // Verificar que hay elementos seleccionados
        if (entryIdsInput && !entryIdsInput.value) {
            isValid = false;
        }

        // Verificar operación seleccionada
        if (operationSelect && !operationSelect.value) {
            isValid = false;
        }

        // Verificar código de seguridad si es eliminación permanente
        if (operationSelect && operationSelect.value === 'permanent_delete') {
            if (!securityCodeInput || !securityCodeInput.value.trim()) {
                isValid = false;
            }
        }

        // Verificar confirmación
        if (confirmCheckbox && !confirmCheckbox.checked) {
            isValid = false;
        }

        // Habilitar/deshabilitar botón de submit
        if (submitButton) {
            submitButton.disabled = !isValid;
        }

        return isValid;
    }

    /**
     * Indicador de fortaleza del código de seguridad
     */
    function initSecurityCodeStrength() {
        const securityCodeInputs = document.querySelectorAll('input[data-validate="security-code"]');
        
        securityCodeInputs.forEach(function(input) {
            input.addEventListener('input', function() {
                showSecurityCodeStrength(this);
            });
        });
    }

    /**
     * Mostrar indicador de fortaleza del código
     */
    function showSecurityCodeStrength(input) {
        const value = input.value;
        let strength = 0;
        let strengthText = '';
        let strengthClass = '';
        
        if (value.length >= 8) strength++;
        if (value.length >= 12) strength++;
        if (/[a-z]/.test(value) && /[A-Z]/.test(value)) strength++;
        if (/\d/.test(value)) strength++;
        if (/[^a-zA-Z0-9]/.test(value)) strength++;
        
        if (strength <= 1) {
            strengthText = 'Débil';
            strengthClass = 'text-danger';
        } else if (strength <= 3) {
            strengthText = 'Medio';
            strengthClass = 'text-warning';
        } else {
            strengthText = 'Fuerte';
            strengthClass = 'text-success';
        }
        
        let strengthIndicator = input.parentElement.querySelector('.security-strength');
        
        if (!strengthIndicator) {
            strengthIndicator = document.createElement('small');
            strengthIndicator.className = 'security-strength form-text';
            input.parentElement.appendChild(strengthIndicator);
        }
        
        if (value.length > 0) {
            strengthIndicator.innerHTML = `Fortaleza: <span class="${strengthClass}">${strengthText}</span>`;
        } else {
            strengthIndicator.innerHTML = '';
        }
    }

    /**
     * Mostrar error en un campo
     */
    function showFieldError(field, message) {
        clearFieldError(field);
        
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        errorDiv.setAttribute('data-validation-error', 'true');
        
        field.parentElement.appendChild(errorDiv);
    }

    /**
     * Mostrar éxito en un campo
     */
    function showFieldSuccess(field, message) {
        clearFieldError(field);
        
        field.classList.add('is-valid');
        field.classList.remove('is-invalid');
        
        if (message) {
            const successDiv = document.createElement('div');
            successDiv.className = 'valid-feedback';
            successDiv.textContent = message;
            successDiv.setAttribute('data-validation-success', 'true');
            
            field.parentElement.appendChild(successDiv);
        }
    }

    /**
     * Limpiar mensajes de error/éxito de un campo
     */
    function clearFieldError(field) {
        field.classList.remove('is-invalid', 'is-valid');
        
        const parent = field.parentElement;
        const errorDiv = parent.querySelector('[data-validation-error]');
        const successDiv = parent.querySelector('[data-validation-success]');
        
        if (errorDiv) errorDiv.remove();
        if (successDiv) successDiv.remove();
    }

    /**
     * Prevenir envío de formulario si hay errores
     */
    document.addEventListener('submit', function(e) {
        const form = e.target;
        
        if (form.id === 'restoreForm') {
            if (!validateRestoreForm(form, form.querySelector('button[type="submit"]'))) {
                e.preventDefault();
                alert('Por favor corrija los errores en el formulario antes de continuar.');
            }
        } else if (form.id === 'permanentDeleteForm') {
            if (!validatePermanentDeleteForm(form, form.querySelector('button[type="submit"]'))) {
                e.preventDefault();
                alert('Por favor corrija los errores en el formulario antes de continuar.');
            }
        } else if (form.id === 'bulkOperationForm') {
            if (!validateBulkOperationForm(form, form.querySelector('button[type="submit"]'))) {
                e.preventDefault();
                alert('Por favor corrija los errores en el formulario antes de continuar.');
            }
        }
    });

})();
