from django import forms
from django.core.exceptions import ValidationError
from .models import BienPatrimonial, MovimientoBien
from apps.catalogo.models import Catalogo
from apps.oficinas.models import Oficina


class BienPatrimonialForm(forms.ModelForm):
    """Formulario para crear/editar bienes patrimoniales"""
    
    class Meta:
        model = BienPatrimonial
        fields = [
            'codigo_patrimonial', 'codigo_interno', 'catalogo', 'oficina',
            'estado_bien', 'marca', 'modelo', 'color', 'serie', 'dimension',
            'placa', 'matricula', 'nro_motor', 'nro_chasis', 
            'fecha_adquisicion', 'valor_adquisicion', 'observaciones'
        ]
        
        widgets = {
            'codigo_patrimonial': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: CP-2024-001',
                'maxlength': 50
            }),
            'codigo_interno': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código interno (opcional)',
                'maxlength': 50
            }),
            'catalogo': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccione un catálogo...'
            }),
            'oficina': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccione una oficina...'
            }),
            'estado_bien': forms.Select(attrs={
                'class': 'form-control'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Marca del bien',
                'maxlength': 100
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Modelo del bien',
                'maxlength': 100
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Color del bien',
                'maxlength': 50
            }),
            'serie': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de serie',
                'maxlength': 100
            }),
            'dimension': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Dimensiones (Ej: 30x40x50 cm)',
                'maxlength': 100
            }),
            'placa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Placa del vehículo',
                'maxlength': 20
            }),
            'matricula': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de matrícula',
                'maxlength': 50
            }),
            'nro_motor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de motor',
                'maxlength': 50
            }),
            'nro_chasis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de chasis',
                'maxlength': 50
            }),
            'fecha_adquisicion': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'valor_adquisicion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observaciones adicionales...',
                'rows': 4
            })
        }
        
        labels = {
            'codigo_patrimonial': 'Código Patrimonial',
            'codigo_interno': 'Código Interno',
            'catalogo': 'Catálogo SBN',
            'oficina': 'Oficina Responsable',
            'estado_bien': 'Estado del Bien',
            'marca': 'Marca',
            'modelo': 'Modelo',
            'color': 'Color',
            'serie': 'Número de Serie',
            'dimension': 'Dimensiones',
            'placa': 'Placa',
            'matricula': 'Matrícula',
            'nro_motor': 'Número de Motor',
            'nro_chasis': 'Número de Chasis',
            'fecha_adquisicion': 'Fecha de Adquisición',
            'valor_adquisicion': 'Valor de Adquisición (S/)',
            'observaciones': 'Observaciones'
        }
        
        help_texts = {
            'codigo_patrimonial': 'Código único del bien patrimonial',
            'codigo_interno': 'Código interno de la institución (opcional)',
            'catalogo': 'Seleccione el catálogo SBN correspondiente',
            'oficina': 'Oficina donde se encuentra el bien',
            'estado_bien': 'Estado actual del bien',
            'marca': 'Marca o fabricante del bien',
            'modelo': 'Modelo específico del bien',
            'color': 'Color predominante del bien',
            'serie': 'Número de serie del fabricante',
            'dimension': 'Medidas del bien (largo x ancho x alto)',
            'placa': 'Solo para vehículos',
            'matricula': 'Solo para vehículos',
            'nro_motor': 'Solo para vehículos y maquinaria',
            'nro_chasis': 'Solo para vehículos',
            'fecha_adquisicion': 'Fecha en que se adquirió el bien',
            'valor_adquisicion': 'Valor de compra en soles peruanos',
            'observaciones': 'Información adicional relevante'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar catálogos activos
        self.fields['catalogo'].queryset = Catalogo.objects.filter(estado='ACTIVO').order_by('codigo')
        
        # Filtrar oficinas activas
        self.fields['oficina'].queryset = Oficina.objects.filter(estado=True).order_by('nombre')
        
        # Hacer campos requeridos más visibles
        for field_name in ['codigo_patrimonial', 'catalogo', 'oficina', 'estado_bien']:
            self.fields[field_name].required = True
    
    def clean_codigo_patrimonial(self):
        """Validar que el código patrimonial sea único"""
        codigo = self.cleaned_data.get('codigo_patrimonial')
        if codigo:
            # Verificar si existe otro bien con el mismo código
            qs = BienPatrimonial.objects.filter(codigo_patrimonial=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Ya existe un bien con este código patrimonial.')
        
        return codigo
    
    def clean_placa(self):
        """Validar que la placa sea única si se proporciona"""
        placa = self.cleaned_data.get('placa')
        if placa:
            # Verificar si existe otro bien con la misma placa
            qs = BienPatrimonial.objects.filter(placa=placa)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Ya existe un bien con esta placa.')
        
        return placa
    
    def clean_serie(self):
        """Validar que el número de serie sea único si se proporciona"""
        serie = self.cleaned_data.get('serie')
        if serie:
            # Verificar si existe otro bien con el mismo número de serie
            qs = BienPatrimonial.objects.filter(serie=serie)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError('Ya existe un bien con este número de serie.')
        
        return serie
    
    def clean(self):
        """Validaciones adicionales del formulario"""
        cleaned_data = super().clean()
        
        # Validar que si es un vehículo, tenga placa
        catalogo = cleaned_data.get('catalogo')
        placa = cleaned_data.get('placa')
        
        if catalogo and 'vehiculo' in catalogo.denominacion.lower() and not placa:
            self.add_error('placa', 'Los vehículos deben tener placa.')
        
        return cleaned_data


class MovimientoBienForm(forms.ModelForm):
    """Formulario para registrar movimientos de bienes"""
    
    class Meta:
        model = MovimientoBien
        fields = ['bien', 'oficina_origen', 'oficina_destino', 'motivo', 'observaciones']
        
        widgets = {
            'bien': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccione un bien...'
            }),
            'oficina_origen': forms.Select(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'oficina_destino': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Seleccione oficina destino...'
            }),
            'motivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Motivo del movimiento',
                'maxlength': 200
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Observaciones del movimiento...',
                'rows': 3
            })
        }
        
        labels = {
            'bien': 'Bien Patrimonial',
            'oficina_origen': 'Oficina de Origen',
            'oficina_destino': 'Oficina de Destino',
            'motivo': 'Motivo del Movimiento',
            'observaciones': 'Observaciones'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar oficinas activas
        self.fields['oficina_origen'].queryset = Oficina.objects.filter(estado=True).order_by('nombre')
        self.fields['oficina_destino'].queryset = Oficina.objects.filter(estado=True).order_by('nombre')
        
        # Si hay un bien seleccionado, establecer la oficina origen
        if self.instance.pk and self.instance.bien:
            self.fields['oficina_origen'].initial = self.instance.bien.oficina
            self.fields['oficina_origen'].widget.attrs['readonly'] = True
    
    def clean(self):
        """Validaciones del movimiento"""
        cleaned_data = super().clean()
        
        oficina_origen = cleaned_data.get('oficina_origen')
        oficina_destino = cleaned_data.get('oficina_destino')
        
        if oficina_origen and oficina_destino and oficina_origen == oficina_destino:
            raise ValidationError('La oficina de origen y destino no pueden ser la misma.')
        
        return cleaned_data


class BuscarBienForm(forms.Form):
    """Formulario para buscar bienes"""
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('N', 'Nuevo'),
        ('B', 'Bueno'),
        ('R', 'Regular'),
        ('M', 'Malo'),
        ('E', 'RAEE'),
        ('C', 'Chatarra'),
    ]
    
    busqueda = forms.CharField(
        label='Buscar',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código, marca, modelo, serie...'
        })
    )
    
    catalogo = forms.ModelChoiceField(
        label='Catálogo',
        queryset=Catalogo.objects.filter(estado='ACTIVO').order_by('codigo'),
        required=False,
        empty_label='Todos los catálogos',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    oficina = forms.ModelChoiceField(
        label='Oficina',
        queryset=Oficina.objects.filter(estado=True).order_by('nombre'),
        required=False,
        empty_label='Todas las oficinas',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    estado = forms.ChoiceField(
        label='Estado',
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class ImportarBienesForm(forms.Form):
    """Formulario para importar bienes desde Excel"""
    
    archivo_excel = forms.FileField(
        label='Archivo Excel',
        help_text='Selecciona un archivo Excel (.xlsx o .xls) con los bienes patrimoniales',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )
    
    actualizar_existentes = forms.BooleanField(
        label='Actualizar bienes existentes',
        help_text='Si está marcado, actualizará los bienes que ya existen',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    generar_qr = forms.BooleanField(
        label='Generar códigos QR automáticamente',
        help_text='Genera códigos QR para todos los bienes importados',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_archivo_excel(self):
        """Validar el archivo Excel"""
        archivo = self.cleaned_data.get('archivo_excel')
        
        if archivo:
            # Validar extensión
            if not archivo.name.lower().endswith(('.xlsx', '.xls')):
                raise ValidationError('El archivo debe ser un Excel (.xlsx o .xls)')
            
            # Validar tamaño (máximo 20MB)
            if archivo.size > 20 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 20MB')
        
        return archivo