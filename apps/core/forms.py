"""
Formularios para el sistema de papelera de reciclaje
"""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import RecycleBin


class RestoreForm(forms.Form):
    """
    Formulario para restaurar un elemento desde la papelera.
    Incluye validación de conflictos y permisos.
    """
    entry_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    confirm = forms.BooleanField(
        label='Confirmo que deseo restaurar este elemento',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'confirmRestore'
        })
    )
    
    resolve_conflicts = forms.ChoiceField(
        label='Resolución de conflictos',
        required=False,
        choices=[
            ('', '-- Seleccione una opción --'),
            ('rename', 'Renombrar elemento restaurado'),
            ('replace', 'Reemplazar elemento existente'),
            ('cancel', 'Cancelar restauración'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'resolveConflicts'
        })
    )
    
    notes = forms.CharField(
        label='Notas de restauración (opcional)',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Agregue notas sobre por qué se restaura este elemento...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.entry = kwargs.pop('entry', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si no hay conflictos, ocultar el campo de resolución
        if self.entry:
            from .utils import RecycleBinService
            original_object = self.entry.content_object
            if original_object:
                conflicts = RecycleBinService._check_restore_conflicts(original_object)
                if not conflicts:
                    self.fields['resolve_conflicts'].widget = forms.HiddenInput()
                    self.fields['resolve_conflicts'].required = False
    
    def clean_entry_id(self):
        """Validar que el entry_id existe y es válido"""
        entry_id = self.cleaned_data.get('entry_id')
        
        try:
            entry = RecycleBin.objects.get(id=entry_id)
        except RecycleBin.DoesNotExist:
            raise ValidationError('El elemento no existe en la papelera')
        
        # Verificar que no ha sido restaurado
        if entry.restored_at:
            raise ValidationError('Este elemento ya ha sido restaurado')
        
        return entry_id
    
    def clean(self):
        """Validaciones adicionales del formulario"""
        cleaned_data = super().clean()
        entry_id = cleaned_data.get('entry_id')
        
        if not entry_id:
            return cleaned_data
        
        try:
            entry = RecycleBin.objects.get(id=entry_id)
        except RecycleBin.DoesNotExist:
            raise ValidationError('El elemento no existe')
        
        # Verificar permisos
        if self.user and not entry.can_be_restored_by(self.user):
            raise ValidationError('No tiene permisos para restaurar este elemento')
        
        # Verificar conflictos
        from .utils import RecycleBinService
        original_object = entry.content_object
        
        if not original_object:
            raise ValidationError('El objeto original ya no existe en la base de datos')
        
        conflicts = RecycleBinService._check_restore_conflicts(original_object)
        
        if conflicts:
            resolve_method = cleaned_data.get('resolve_conflicts')
            if not resolve_method or resolve_method == '':
                raise ValidationError(
                    f'Existe un conflicto de restauración: {conflicts}. '
                    'Debe seleccionar un método de resolución.'
                )
        
        return cleaned_data


class PermanentDeleteForm(forms.Form):
    """
    Formulario para eliminación permanente con código de seguridad.
    Incluye validación del código, confirmación explícita y sistema de bloqueo temporal.
    """
    entry_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    security_code = forms.CharField(
        label='Código de Seguridad',
        max_length=100,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'securityCode',
            'placeholder': 'Ingrese el código de seguridad',
            'autocomplete': 'off',
            'data-validate': 'security-code'
        })
    )
    
    confirm_text = forms.CharField(
        label='Escriba "ELIMINAR" para confirmar',
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'confirmText',
            'placeholder': 'Escriba ELIMINAR',
            'autocomplete': 'off',
            'data-validate': 'confirm-text'
        })
    )
    
    reason = forms.CharField(
        label='Motivo de eliminación permanente',
        required=True,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Explique por qué es necesario eliminar permanentemente este elemento...',
            'data-validate': 'required'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.entry = kwargs.pop('entry', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Verificar si el usuario está bloqueado
        if self.user:
            from .models import SecurityCodeAttempt
            is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(self.user)
            if is_locked:
                # Deshabilitar el formulario si está bloqueado
                for field in self.fields.values():
                    field.disabled = True
                self.fields['security_code'].help_text = (
                    f'Usuario bloqueado temporalmente. Intente nuevamente en {time_remaining} minutos.'
                )
    
    def clean_entry_id(self):
        """Validar que el entry_id existe"""
        entry_id = self.cleaned_data.get('entry_id')
        
        try:
            entry = RecycleBin.objects.get(id=entry_id)
        except RecycleBin.DoesNotExist:
            raise ValidationError('El elemento no existe en la papelera')
        
        return entry_id
    
    def clean_security_code(self):
        """Validar el código de seguridad contra la variable de entorno"""
        security_code = self.cleaned_data.get('security_code')
        
        if not security_code:
            raise ValidationError('El código de seguridad es requerido')
        
        # Obtener el código correcto de las variables de entorno
        correct_code = getattr(settings, 'PERMANENT_DELETE_CODE', None)
        
        if not correct_code:
            raise ValidationError(
                'El código de seguridad no está configurado en el sistema. '
                'Contacte al administrador.'
            )
        
        if security_code != correct_code:
            # Registrar intento fallido
            if self.user:
                from .models import AuditLog
                AuditLog.objects.create(
                    user=self.user,
                    action='security_violation',
                    model_name='RecycleBin',
                    object_id=str(self.cleaned_data.get('entry_id', '')),
                    object_repr='Intento de código incorrecto',
                    changes={'security_code_attempt': 'failed'}
                )
            
            raise ValidationError('Código de seguridad incorrecto')
        
        return security_code
    
    def clean_confirm_text(self):
        """Validar que el usuario escribió exactamente 'ELIMINAR'"""
        confirm_text = self.cleaned_data.get('confirm_text', '').strip().upper()
        
        if confirm_text != 'ELIMINAR':
            raise ValidationError('Debe escribir exactamente "ELIMINAR" para confirmar')
        
        return confirm_text
    
    def clean_reason(self):
        """Validar que el motivo tenga suficiente detalle"""
        reason = self.cleaned_data.get('reason', '').strip()
        
        if len(reason) < 20:
            raise ValidationError(
                'El motivo debe tener al menos 20 caracteres. '
                'Proporcione una explicación detallada.'
            )
        
        return reason
    
    def clean(self):
        """Validaciones adicionales del formulario"""
        cleaned_data = super().clean()
        
        # Verificar que el usuario sea administrador
        if self.user:
            if not (hasattr(self.user, 'profile') and self.user.profile.is_administrador):
                raise ValidationError(
                    'Solo los administradores pueden eliminar permanentemente elementos'
                )
            
            # Verificar si el usuario está bloqueado
            from .models import SecurityCodeAttempt
            is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(self.user)
            if is_locked:
                raise ValidationError(
                    f'Usuario bloqueado temporalmente por múltiples intentos fallidos. '
                    f'Intente nuevamente en {time_remaining} minutos.'
                )
        
        return cleaned_data


class BulkOperationForm(forms.Form):
    """
    Formulario para operaciones en lote (restaurar o eliminar múltiples elementos).
    Soporta validación de múltiples IDs y operaciones masivas.
    """
    OPERATION_CHOICES = [
        ('restore', 'Restaurar'),
        ('permanent_delete', 'Eliminar Permanentemente'),
    ]
    
    operation = forms.ChoiceField(
        label='Operación',
        choices=OPERATION_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'bulkOperation'
        })
    )
    
    entry_ids = forms.CharField(
        widget=forms.HiddenInput(),
        required=True
    )
    
    security_code = forms.CharField(
        label='Código de Seguridad (solo para eliminación permanente)',
        max_length=100,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'bulkSecurityCode',
            'placeholder': 'Requerido solo para eliminación permanente',
            'autocomplete': 'off'
        })
    )
    
    confirm = forms.BooleanField(
        label='Confirmo que deseo realizar esta operación en lote',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'confirmBulk'
        })
    )
    
    notes = forms.CharField(
        label='Notas (opcional)',
        required=False,
        max_length=500,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Agregue notas sobre esta operación en lote...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_entry_ids(self):
        """Validar y parsear los IDs de entrada"""
        entry_ids_str = self.cleaned_data.get('entry_ids', '')
        
        if not entry_ids_str:
            raise ValidationError('Debe seleccionar al menos un elemento')
        
        # Parsear IDs (pueden venir como "1,2,3" o como lista JSON)
        try:
            if ',' in entry_ids_str:
                entry_ids = [int(id.strip()) for id in entry_ids_str.split(',') if id.strip()]
            else:
                import json
                entry_ids = json.loads(entry_ids_str)
                entry_ids = [int(id) for id in entry_ids]
        except (ValueError, json.JSONDecodeError):
            raise ValidationError('Formato de IDs inválido')
        
        if not entry_ids:
            raise ValidationError('Debe seleccionar al menos un elemento')
        
        # Validar que todos los IDs existen
        existing_entries = RecycleBin.objects.filter(id__in=entry_ids)
        existing_ids = set(existing_entries.values_list('id', flat=True))
        
        invalid_ids = set(entry_ids) - existing_ids
        if invalid_ids:
            raise ValidationError(
                f'Los siguientes IDs no existen: {", ".join(map(str, invalid_ids))}'
            )
        
        # Limitar cantidad de elementos en operaciones en lote
        max_bulk_size = getattr(settings, 'RECYCLE_BIN_MAX_BULK_SIZE', 100)
        if len(entry_ids) > max_bulk_size:
            raise ValidationError(
                f'No puede procesar más de {max_bulk_size} elementos a la vez. '
                f'Seleccionó {len(entry_ids)} elementos.'
            )
        
        return entry_ids
    
    def clean(self):
        """Validaciones adicionales del formulario"""
        cleaned_data = super().clean()
        operation = cleaned_data.get('operation')
        entry_ids = cleaned_data.get('entry_ids', [])
        security_code = cleaned_data.get('security_code')
        
        if not entry_ids:
            return cleaned_data
        
        # Obtener las entradas
        entries = RecycleBin.objects.filter(id__in=entry_ids)
        
        # Validar permisos según la operación
        if operation == 'restore':
            # Verificar que el usuario puede restaurar todos los elementos
            for entry in entries:
                if not entry.can_be_restored_by(self.user):
                    raise ValidationError(
                        f'No tiene permisos para restaurar: {entry.object_repr}'
                    )
        
        elif operation == 'permanent_delete':
            # Verificar que sea administrador
            if not (hasattr(self.user, 'profile') and self.user.profile.is_administrador):
                raise ValidationError(
                    'Solo los administradores pueden eliminar permanentemente'
                )
            
            # Validar código de seguridad
            if not security_code:
                raise ValidationError(
                    'El código de seguridad es requerido para eliminación permanente'
                )
            
            correct_code = getattr(settings, 'PERMANENT_DELETE_CODE', None)
            if not correct_code:
                raise ValidationError(
                    'El código de seguridad no está configurado en el sistema'
                )
            
            if security_code != correct_code:
                # Registrar intento fallido
                if self.user:
                    from .models import AuditLog
                    AuditLog.objects.create(
                        user=self.user,
                        action='security_violation',
                        model_name='RecycleBin',
                        object_id='bulk_operation',
                        object_repr=f'Intento de eliminación en lote de {len(entry_ids)} elementos',
                        changes={'security_code_attempt': 'failed', 'entry_count': len(entry_ids)}
                    )
                
                raise ValidationError('Código de seguridad incorrecto')
        
        return cleaned_data
    
    def get_entries(self):
        """Obtener las entradas de RecycleBin para procesar"""
        entry_ids = self.cleaned_data.get('entry_ids', [])
        if entry_ids:
            return RecycleBin.objects.filter(id__in=entry_ids)
        return RecycleBin.objects.none()


class QuickRestoreForm(forms.Form):
    """
    Formulario simplificado para restauración rápida sin confirmaciones adicionales.
    Usado en acciones inline desde la lista.
    """
    entry_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_entry_id(self):
        """Validar que el entry_id existe y puede ser restaurado"""
        entry_id = self.cleaned_data.get('entry_id')
        
        try:
            entry = RecycleBin.objects.get(id=entry_id)
        except RecycleBin.DoesNotExist:
            raise ValidationError('El elemento no existe en la papelera')
        
        # Verificar que no ha sido restaurado
        if entry.restored_at:
            raise ValidationError('Este elemento ya ha sido restaurado')
        
        # Verificar permisos
        if self.user and not entry.can_be_restored_by(self.user):
            raise ValidationError('No tiene permisos para restaurar este elemento')
        
        # Verificar que no hay conflictos
        from .utils import RecycleBinService
        original_object = entry.content_object
        
        if not original_object:
            raise ValidationError('El objeto original ya no existe')
        
        conflicts = RecycleBinService._check_restore_conflicts(original_object)
        if conflicts:
            raise ValidationError(
                f'No se puede restaurar automáticamente debido a conflictos: {conflicts}. '
                'Use el formulario completo de restauración.'
            )
        
        return entry_id
