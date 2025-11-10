"""
Filtros avanzados para el sistema de papelera de reciclaje
"""
from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from .models import RecycleBin


class RecycleBinFilterForm(forms.Form):
    """
    Formulario de filtros avanzados para la papelera de reciclaje
    """
    
    # Filtro por módulo
    module = forms.ChoiceField(
        required=False,
        label='Módulo',
        choices=[('', 'Todos los módulos')] + [
            ('oficinas', 'Oficinas'),
            ('bienes', 'Bienes Patrimoniales'),
            ('catalogo', 'Catálogo'),
            ('core', 'Sistema'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'filter-module'
        })
    )
    
    # Búsqueda por texto
    search = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre o motivo...',
            'id': 'filter-search'
        })
    )
    
    # Filtro por rango de fechas de eliminación
    date_from = forms.DateField(
        required=False,
        label='Eliminado desde',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'filter-date-from'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        label='Eliminado hasta',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'filter-date-to'
        })
    )
    
    # Filtro por usuario que eliminó
    deleted_by = forms.CharField(
        required=False,
        label='Eliminado por',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario...',
            'id': 'filter-deleted-by'
        })
    )
    
    # Filtro por tiempo restante antes de eliminación automática
    TIME_REMAINING_CHOICES = [
        ('', 'Cualquier tiempo'),
        ('expired', 'Listos para eliminar (0 días)'),
        ('critical', 'Crítico (1-3 días)'),
        ('warning', 'Advertencia (4-7 días)'),
        ('normal', 'Normal (8-14 días)'),
        ('safe', 'Seguro (más de 14 días)'),
    ]
    
    time_remaining = forms.ChoiceField(
        required=False,
        label='Tiempo restante',
        choices=TIME_REMAINING_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'filter-time-remaining'
        })
    )
    
    # Filtro por estado de restauración
    STATUS_CHOICES = [
        ('', 'Todos los estados'),
        ('active', 'En papelera'),
        ('restored', 'Restaurados'),
    ]
    
    status = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'filter-status'
        })
    )
    
    def apply_filters(self, queryset, user):
        """
        Aplica los filtros al queryset de RecycleBin
        
        Args:
            queryset: QuerySet base de RecycleBin
            user: Usuario que realiza la consulta (para permisos)
            
        Returns:
            QuerySet filtrado
        """
        # Filtro por módulo
        if self.cleaned_data.get('module'):
            queryset = queryset.filter(module_name=self.cleaned_data['module'])
        
        # Búsqueda por texto
        if self.cleaned_data.get('search'):
            search_term = self.cleaned_data['search']
            queryset = queryset.filter(
                Q(object_repr__icontains=search_term) |
                Q(deletion_reason__icontains=search_term)
            )
        
        # Filtro por rango de fechas
        if self.cleaned_data.get('date_from'):
            queryset = queryset.filter(deleted_at__gte=self.cleaned_data['date_from'])
        
        if self.cleaned_data.get('date_to'):
            # Agregar un día para incluir todo el día seleccionado
            from datetime import datetime, timedelta
            date_to = datetime.combine(
                self.cleaned_data['date_to'], 
                datetime.max.time()
            )
            queryset = queryset.filter(deleted_at__lte=date_to)
        
        # Filtro por usuario que eliminó
        if self.cleaned_data.get('deleted_by'):
            deleted_by_term = self.cleaned_data['deleted_by']
            queryset = queryset.filter(
                Q(deleted_by__username__icontains=deleted_by_term) |
                Q(deleted_by__first_name__icontains=deleted_by_term) |
                Q(deleted_by__last_name__icontains=deleted_by_term)
            )
        
        # Filtro por tiempo restante
        if self.cleaned_data.get('time_remaining'):
            queryset = self._apply_time_remaining_filter(
                queryset, 
                self.cleaned_data['time_remaining']
            )
        
        # Filtro por estado
        if self.cleaned_data.get('status'):
            status = self.cleaned_data['status']
            if status == 'active':
                queryset = queryset.filter(restored_at__isnull=True)
            elif status == 'restored':
                queryset = queryset.filter(restored_at__isnull=False)
        
        return queryset
    
    def _apply_time_remaining_filter(self, queryset, time_filter):
        """
        Aplica filtro por tiempo restante antes de eliminación automática
        
        Args:
            queryset: QuerySet a filtrar
            time_filter: Tipo de filtro de tiempo
            
        Returns:
            QuerySet filtrado
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        
        # Solo elementos no restaurados
        queryset = queryset.filter(restored_at__isnull=True)
        
        if time_filter == 'expired':
            # Listos para eliminar (auto_delete_at <= now)
            queryset = queryset.filter(auto_delete_at__lte=now)
            
        elif time_filter == 'critical':
            # Crítico: 1-3 días restantes
            start_date = now
            end_date = now + timedelta(days=3)
            queryset = queryset.filter(
                auto_delete_at__gt=start_date,
                auto_delete_at__lte=end_date
            )
            
        elif time_filter == 'warning':
            # Advertencia: 4-7 días restantes
            start_date = now + timedelta(days=3)
            end_date = now + timedelta(days=7)
            queryset = queryset.filter(
                auto_delete_at__gt=start_date,
                auto_delete_at__lte=end_date
            )
            
        elif time_filter == 'normal':
            # Normal: 8-14 días restantes
            start_date = now + timedelta(days=7)
            end_date = now + timedelta(days=14)
            queryset = queryset.filter(
                auto_delete_at__gt=start_date,
                auto_delete_at__lte=end_date
            )
            
        elif time_filter == 'safe':
            # Seguro: más de 14 días restantes
            start_date = now + timedelta(days=14)
            queryset = queryset.filter(auto_delete_at__gt=start_date)
        
        return queryset
    
    def get_active_filters_count(self):
        """
        Cuenta cuántos filtros están activos
        
        Returns:
            int: Número de filtros activos
        """
        count = 0
        for field_name in self.fields:
            if self.cleaned_data.get(field_name):
                count += 1
        return count
    
    def get_active_filters_summary(self):
        """
        Genera un resumen de los filtros activos
        
        Returns:
            list: Lista de tuplas (nombre_filtro, valor_filtro)
        """
        summary = []
        
        if self.cleaned_data.get('module'):
            module_label = dict(self.fields['module'].choices).get(
                self.cleaned_data['module']
            )
            summary.append(('Módulo', module_label))
        
        if self.cleaned_data.get('search'):
            summary.append(('Búsqueda', self.cleaned_data['search']))
        
        if self.cleaned_data.get('date_from'):
            summary.append(('Desde', self.cleaned_data['date_from'].strftime('%d/%m/%Y')))
        
        if self.cleaned_data.get('date_to'):
            summary.append(('Hasta', self.cleaned_data['date_to'].strftime('%d/%m/%Y')))
        
        if self.cleaned_data.get('deleted_by'):
            summary.append(('Eliminado por', self.cleaned_data['deleted_by']))
        
        if self.cleaned_data.get('time_remaining'):
            time_label = dict(self.fields['time_remaining'].choices).get(
                self.cleaned_data['time_remaining']
            )
            summary.append(('Tiempo restante', time_label))
        
        if self.cleaned_data.get('status'):
            status_label = dict(self.fields['status'].choices).get(
                self.cleaned_data['status']
            )
            summary.append(('Estado', status_label))
        
        return summary


class RecycleBinQuickFilters:
    """
    Clase helper para filtros rápidos predefinidos
    """
    
    @staticmethod
    def get_expiring_soon(queryset):
        """
        Elementos que expiran en los próximos 7 días
        """
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        seven_days = now + timedelta(days=7)
        
        return queryset.filter(
            restored_at__isnull=True,
            auto_delete_at__lte=seven_days,
            auto_delete_at__gt=now
        )
    
    @staticmethod
    def get_expired(queryset):
        """
        Elementos listos para eliminación automática
        """
        from django.utils import timezone
        
        return queryset.filter(
            restored_at__isnull=True,
            auto_delete_at__lte=timezone.now()
        )
    
    @staticmethod
    def get_by_user(queryset, user):
        """
        Elementos eliminados por un usuario específico
        """
        return queryset.filter(deleted_by=user)
    
    @staticmethod
    def get_by_module(queryset, module_name):
        """
        Elementos de un módulo específico
        """
        return queryset.filter(module_name=module_name)
    
    @staticmethod
    def get_recently_deleted(queryset, days=7):
        """
        Elementos eliminados recientemente
        """
        from django.utils import timezone
        from datetime import timedelta
        
        since = timezone.now() - timedelta(days=days)
        return queryset.filter(deleted_at__gte=since)
    
    @staticmethod
    def get_restored(queryset):
        """
        Elementos que han sido restaurados
        """
        return queryset.filter(restored_at__isnull=False)
