from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.bienes.models import BienPatrimonial
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina
from .models import ConfiguracionFiltro, ReporteGenerado


class FiltroAvanzadoForm(forms.Form):
    """Formulario para filtros avanzados de reportes"""
    
    # Filtros básicos
    oficinas = forms.ModelMultipleChoiceField(
        queryset=Oficina.obtener_activas(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Oficinas',
        help_text='Seleccione las oficinas a incluir en el reporte'
    )
    
    estados_bien = forms.MultipleChoiceField(
        choices=BienPatrimonial.ESTADOS_BIEN,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Estados del Bien',
        help_text='Seleccione los estados a incluir'
    )
    
    grupos_catalogo = forms.MultipleChoiceField(
        choices=[],  # Se llenarán dinámicamente
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Grupos de Catálogo',
        help_text='Seleccione los grupos del catálogo'
    )
    
    clases_catalogo = forms.MultipleChoiceField(
        choices=[],  # Se llenarán dinámicamente
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Clases de Catálogo',
        help_text='Seleccione las clases del catálogo'
    )
    
    # Filtros de texto con autocompletado
    marcas = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese marcas separadas por comas',
            'data-toggle': 'tooltip',
            'title': 'Puede ingresar múltiples marcas separadas por comas'
        }),
        label='Marcas',
        help_text='Ingrese las marcas a filtrar (separadas por comas)'
    )
    
    modelos = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese modelos separados por comas',
            'data-toggle': 'tooltip',
            'title': 'Puede ingresar múltiples modelos separados por comas'
        }),
        label='Modelos',
        help_text='Ingrese los modelos a filtrar (separados por comas)'
    )
    
    # Filtros de fechas
    fecha_adquisicion_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha Adquisición Desde',
        help_text='Fecha de inicio para filtro de adquisición'
    )
    
    fecha_adquisicion_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha Adquisición Hasta',
        help_text='Fecha de fin para filtro de adquisición'
    )
    
    fecha_registro_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha Registro Desde',
        help_text='Fecha de inicio para filtro de registro'
    )
    
    fecha_registro_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Fecha Registro Hasta',
        help_text='Fecha de fin para filtro de registro'
    )
    
    # Filtros de valor
    valor_minimo = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Valor Mínimo',
        help_text='Valor mínimo de adquisición'
    )
    
    valor_maximo = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Valor Máximo',
        help_text='Valor máximo de adquisición'
    )
    
    # Filtros de texto específicos
    codigo_patrimonial = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código patrimonial (búsqueda parcial)'
        }),
        label='Código Patrimonial',
        help_text='Filtro por código patrimonial (búsqueda parcial)'
    )
    
    denominacion = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Denominación del bien (búsqueda parcial)'
        }),
        label='Denominación',
        help_text='Filtro por denominación del bien (búsqueda parcial)'
    )
    
    serie = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de serie (búsqueda parcial)'
        }),
        label='Serie',
        help_text='Filtro por número de serie (búsqueda parcial)'
    )
    
    placa = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Placa del vehículo (búsqueda parcial)'
        }),
        label='Placa',
        help_text='Filtro por placa (búsqueda parcial)'
    )
    
    # Operador lógico
    operador_principal = forms.ChoiceField(
        choices=ConfiguracionFiltro.OPERADORES_LOGICOS,
        initial='AND',
        widget=forms.RadioSelect,
        label='Operador Lógico Principal',
        help_text='Cómo combinar los filtros aplicados'
    )
    
    # Opciones de guardado
    guardar_configuracion = forms.BooleanField(
        required=False,
        label='Guardar Configuración',
        help_text='Marque para guardar esta configuración de filtros'
    )
    
    nombre_configuracion = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre para la configuración'
        }),
        label='Nombre de la Configuración',
        help_text='Nombre para guardar esta configuración'
    )
    
    configuracion_publica = forms.BooleanField(
        required=False,
        label='Configuración Pública',
        help_text='Permitir que otros usuarios usen esta configuración'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Llenar opciones dinámicas
        self._llenar_grupos_catalogo()
        self._llenar_clases_catalogo()
        
        # Configurar widgets con clases CSS
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs.update({'class': 'form-check-input'})
    
    def _llenar_grupos_catalogo(self):
        """Llena las opciones de grupos de catálogo"""
        grupos = Catalogo.obtener_grupos()
        self.fields['grupos_catalogo'].choices = [
            (grupo, grupo) for grupo in grupos
        ]
    
    def _llenar_clases_catalogo(self):
        """Llena las opciones de clases de catálogo"""
        clases = Catalogo.objects.filter(
            estado='ACTIVO'
        ).values_list('clase', flat=True).distinct().order_by('clase')
        
        self.fields['clases_catalogo'].choices = [
            (clase, clase) for clase in clases
        ]
    
    def clean(self):
        """Validaciones personalizadas"""
        cleaned_data = super().clean()
        
        # Validar fechas de adquisición
        fecha_adq_desde = cleaned_data.get('fecha_adquisicion_desde')
        fecha_adq_hasta = cleaned_data.get('fecha_adquisicion_hasta')
        
        if fecha_adq_desde and fecha_adq_hasta and fecha_adq_desde > fecha_adq_hasta:
            raise ValidationError({
                'fecha_adquisicion_hasta': 'La fecha hasta debe ser mayor o igual a la fecha desde'
            })
        
        # Validar fechas de registro
        fecha_reg_desde = cleaned_data.get('fecha_registro_desde')
        fecha_reg_hasta = cleaned_data.get('fecha_registro_hasta')
        
        if fecha_reg_desde and fecha_reg_hasta and fecha_reg_desde > fecha_reg_hasta:
            raise ValidationError({
                'fecha_registro_hasta': 'La fecha hasta debe ser mayor o igual a la fecha desde'
            })
        
        # Validar valores
        valor_min = cleaned_data.get('valor_minimo')
        valor_max = cleaned_data.get('valor_maximo')
        
        if valor_min and valor_max and valor_min > valor_max:
            raise ValidationError({
                'valor_maximo': 'El valor máximo debe ser mayor o igual al valor mínimo'
            })
        
        # Validar configuración a guardar
        guardar = cleaned_data.get('guardar_configuracion')
        nombre = cleaned_data.get('nombre_configuracion')
        
        if guardar and not nombre:
            raise ValidationError({
                'nombre_configuracion': 'Debe proporcionar un nombre para guardar la configuración'
            })
        
        # Validar que el nombre no exista para el usuario
        if guardar and nombre and self.user:
            if ConfiguracionFiltro.objects.filter(
                usuario=self.user, 
                nombre=nombre
            ).exists():
                raise ValidationError({
                    'nombre_configuracion': 'Ya existe una configuración con este nombre'
                })
        
        return cleaned_data
    
    def procesar_marcas(self):
        """Procesa el campo de marcas separadas por comas"""
        marcas_texto = self.cleaned_data.get('marcas', '')
        if marcas_texto:
            return [marca.strip() for marca in marcas_texto.split(',') if marca.strip()]
        return []
    
    def procesar_modelos(self):
        """Procesa el campo de modelos separados por comas"""
        modelos_texto = self.cleaned_data.get('modelos', '')
        if modelos_texto:
            return [modelo.strip() for modelo in modelos_texto.split(',') if modelo.strip()]
        return []
    
    def guardar_configuracion_si_solicitado(self):
        """Guarda la configuración si fue solicitado"""
        if not self.cleaned_data.get('guardar_configuracion') or not self.user:
            return None
        
        configuracion = ConfiguracionFiltro(
            nombre=self.cleaned_data['nombre_configuracion'],
            usuario=self.user,
            es_publica=self.cleaned_data.get('configuracion_publica', False),
            oficinas=[str(oficina.id) for oficina in self.cleaned_data.get('oficinas', [])],
            estados_bien=self.cleaned_data.get('estados_bien', []),
            grupos_catalogo=self.cleaned_data.get('grupos_catalogo', []),
            clases_catalogo=self.cleaned_data.get('clases_catalogo', []),
            marcas=self.procesar_marcas(),
            modelos=self.procesar_modelos(),
            fecha_adquisicion_desde=self.cleaned_data.get('fecha_adquisicion_desde'),
            fecha_adquisicion_hasta=self.cleaned_data.get('fecha_adquisicion_hasta'),
            fecha_registro_desde=self.cleaned_data.get('fecha_registro_desde'),
            fecha_registro_hasta=self.cleaned_data.get('fecha_registro_hasta'),
            valor_minimo=self.cleaned_data.get('valor_minimo'),
            valor_maximo=self.cleaned_data.get('valor_maximo'),
            codigo_patrimonial=self.cleaned_data.get('codigo_patrimonial', ''),
            denominacion=self.cleaned_data.get('denominacion', ''),
            serie=self.cleaned_data.get('serie', ''),
            placa=self.cleaned_data.get('placa', ''),
            operador_principal=self.cleaned_data.get('operador_principal', 'AND'),
        )
        
        configuracion.save()
        return configuracion


class ConfiguracionFiltroForm(forms.ModelForm):
    """Formulario para crear/editar configuraciones de filtros"""
    
    class Meta:
        model = ConfiguracionFiltro
        fields = [
            'nombre', 'descripcion', 'es_publica',
            'oficinas', 'estados_bien', 'grupos_catalogo', 'clases_catalogo',
            'marcas', 'modelos', 'fecha_adquisicion_desde', 'fecha_adquisicion_hasta',
            'fecha_registro_desde', 'fecha_registro_hasta', 'valor_minimo', 'valor_maximo',
            'codigo_patrimonial', 'denominacion', 'serie', 'placa', 'operador_principal'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'es_publica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'fecha_adquisicion_desde': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_adquisicion_hasta': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_registro_desde': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_registro_hasta': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_minimo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'valor_maximo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'codigo_patrimonial': forms.TextInput(attrs={'class': 'form-control'}),
            'denominacion': forms.TextInput(attrs={'class': 'form-control'}),
            'serie': forms.TextInput(attrs={'class': 'form-control'}),
            'placa': forms.TextInput(attrs={'class': 'form-control'}),
            'operador_principal': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar el usuario si no está establecido
        if not self.instance.pk and self.user:
            self.instance.usuario = self.user


class CargarConfiguracionForm(forms.Form):
    """Formulario para cargar una configuración de filtros existente"""
    
    configuracion = forms.ModelChoiceField(
        queryset=ConfiguracionFiltro.objects.none(),
        empty_label="Seleccione una configuración...",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Configuración de Filtros',
        help_text='Seleccione una configuración guardada para aplicar'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Mostrar configuraciones disponibles para el usuario
            self.fields['configuracion'].queryset = (
                ConfiguracionFiltro.obtener_disponibles_para_usuario(self.user)
            )


class GenerarReporteForm(forms.Form):
    """Formulario para configurar la generación de reportes"""
    
    nombre_reporte = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del reporte'
        }),
        label='Nombre del Reporte',
        help_text='Nombre descriptivo para el reporte'
    )
    
    tipo_reporte = forms.ChoiceField(
        choices=ReporteGenerado.TIPOS_REPORTE,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Reporte',
        help_text='Seleccione el tipo de reporte a generar'
    )
    
    formato = forms.ChoiceField(
        choices=ReporteGenerado.FORMATOS_EXPORTACION,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Formato de Exportación',
        help_text='Formato del archivo a generar'
    )
    
    incluir_graficos = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir Gráficos',
        help_text='Incluir gráficos estadísticos en el reporte (solo PDF)'
    )
    
    incluir_historial = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Incluir Historial',
        help_text='Incluir historial de movimientos y cambios de estado'
    )
    
    agrupar_por = forms.ChoiceField(
        choices=[
            ('', 'Sin agrupación'),
            ('oficina', 'Por Oficina'),
            ('estado', 'Por Estado'),
            ('grupo', 'Por Grupo de Catálogo'),
            ('clase', 'Por Clase de Catálogo'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Agrupar Por',
        help_text='Cómo agrupar los datos en el reporte'
    )
    
    def clean(self):
        """Validaciones personalizadas"""
        cleaned_data = super().clean()
        
        formato = cleaned_data.get('formato')
        incluir_graficos = cleaned_data.get('incluir_graficos')
        
        # Los gráficos solo están disponibles en PDF
        if incluir_graficos and formato != 'PDF':
            raise ValidationError({
                'incluir_graficos': 'Los gráficos solo están disponibles en formato PDF'
            })
        
        return cleaned_data