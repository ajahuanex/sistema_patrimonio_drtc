from django import forms
from .models import Catalogo


class CatalogoForm(forms.ModelForm):
    """Formulario para crear/editar catálogos"""
    
    class Meta:
        model = Catalogo
        fields = ['codigo', 'denominacion', 'grupo', 'clase', 'resolucion', 'estado']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 5.1.01.01.001',
                'maxlength': 20
            }),
            'denominacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Denominación del bien',
                'maxlength': 200
            }),
            'grupo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Grupo del catálogo',
                'maxlength': 100
            }),
            'clase': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Clase del catálogo',
                'maxlength': 100
            }),
            'resolucion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Resolución que respalda',
                'maxlength': 100
            }),
            'estado': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'codigo': 'Código del Catálogo',
            'denominacion': 'Denominación',
            'grupo': 'Grupo',
            'clase': 'Clase',
            'resolucion': 'Resolución',
            'estado': 'Estado'
        }
        help_texts = {
            'codigo': 'Código único del catálogo SBN',
            'denominacion': 'Nombre descriptivo del bien',
            'grupo': 'Grupo al que pertenece el catálogo',
            'clase': 'Clase específica del catálogo',
            'resolucion': 'Resolución que respalda la inclusión/exclusión',
            'estado': 'Estado actual del catálogo'
        }
    
    def clean_codigo(self):
        """Validar que el código sea único"""
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            # Verificar si existe otro catálogo con el mismo código
            qs = Catalogo.objects.filter(codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError('Ya existe un catálogo con este código.')
        
        return codigo
    
    def clean_denominacion(self):
        """Validar que la denominación sea única"""
        denominacion = self.cleaned_data.get('denominacion')
        if denominacion:
            # Verificar si existe otro catálogo con la misma denominación
            qs = Catalogo.objects.filter(denominacion__iexact=denominacion)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise forms.ValidationError('Ya existe un catálogo con esta denominación.')
        
        return denominacion


class ImportarCatalogoForm(forms.Form):
    """Formulario para importar catálogo desde Excel"""
    
    archivo_excel = forms.FileField(
        label='Archivo Excel',
        help_text='Selecciona un archivo Excel (.xlsx o .xls) con el catálogo SBN',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )
    
    actualizar_existentes = forms.BooleanField(
        label='Actualizar registros existentes',
        help_text='Si está marcado, actualizará los catálogos que ya existen',
        required=False,
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
                raise forms.ValidationError('El archivo debe ser un Excel (.xlsx o .xls)')
            
            # Validar tamaño (máximo 10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB')
        
        return archivo


class FiltrarCatalogoForm(forms.Form):
    """Formulario para filtrar catálogos"""
    
    ESTADO_CHOICES = [
        ('', 'Todos los estados'),
        ('ACTIVO', 'Activo'),
        ('EXCLUIDO', 'Excluido'),
    ]
    
    busqueda = forms.CharField(
        label='Buscar',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código o denominación...'
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
    
    grupo = forms.CharField(
        label='Grupo',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrar por grupo...'
        })
    )