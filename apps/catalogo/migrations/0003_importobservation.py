# Generated migration for ImportObservation model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('catalogo', '0002_catalogo_deleted_at_catalogo_deleted_by_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportObservation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('modulo', models.CharField(choices=[('catalogo', 'Catálogo'), ('bienes', 'Bienes Patrimoniales'), ('oficinas', 'Oficinas')], help_text='Módulo donde se generó la observación', max_length=50, verbose_name='Módulo')),
                ('tipo', models.CharField(choices=[('duplicado_denominacion', 'Denominación Duplicada'), ('dato_incompleto', 'Dato Incompleto'), ('formato_invalido', 'Formato Inválido'), ('referencia_faltante', 'Referencia Faltante'), ('otro', 'Otro')], help_text='Tipo de problema detectado', max_length=50, verbose_name='Tipo de Observación')),
                ('severidad', models.CharField(choices=[('info', 'Información'), ('warning', 'Advertencia'), ('error', 'Error')], default='warning', help_text='Nivel de severidad de la observación', max_length=20, verbose_name='Severidad')),
                ('fila_excel', models.IntegerField(help_text='Número de fila en el archivo Excel', verbose_name='Fila en Excel')),
                ('campo', models.CharField(help_text='Campo que generó la observación', max_length=100, verbose_name='Campo')),
                ('valor_original', models.TextField(blank=True, help_text='Valor original del campo', verbose_name='Valor Original')),
                ('valor_procesado', models.TextField(blank=True, help_text='Valor después del procesamiento', verbose_name='Valor Procesado')),
                ('mensaje', models.TextField(help_text='Descripción detallada de la observación', verbose_name='Mensaje')),
                ('datos_adicionales', models.JSONField(blank=True, default=dict, help_text='Información adicional en formato JSON', verbose_name='Datos Adicionales')),
                ('fecha_importacion', models.DateTimeField(auto_now_add=True, help_text='Fecha y hora de la importación', verbose_name='Fecha de Importación')),
                ('archivo_nombre', models.CharField(blank=True, help_text='Nombre del archivo importado', max_length=255, verbose_name='Nombre del Archivo')),
                ('resuelto', models.BooleanField(default=False, help_text='Indica si la observación fue revisada y resuelta', verbose_name='Resuelto')),
                ('fecha_resolucion', models.DateTimeField(blank=True, help_text='Fecha y hora en que se resolvió', null=True, verbose_name='Fecha de Resolución')),
                ('notas_resolucion', models.TextField(blank=True, help_text='Notas sobre cómo se resolvió la observación', verbose_name='Notas de Resolución')),
                ('resuelto_por', models.ForeignKey(blank=True, help_text='Usuario que resolvió la observación', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='observaciones_resueltas', to=settings.AUTH_USER_MODEL, verbose_name='Resuelto Por')),
                ('usuario', models.ForeignKey(blank=True, help_text='Usuario que realizó la importación', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Observación de Importación',
                'verbose_name_plural': 'Observaciones de Importación',
                'ordering': ['-fecha_importacion', 'fila_excel'],
                'indexes': [
                    models.Index(fields=['modulo', 'fecha_importacion'], name='catalogo_im_modulo_f8e9c5_idx'),
                    models.Index(fields=['tipo', 'severidad'], name='catalogo_im_tipo_se_4a2b1c_idx'),
                    models.Index(fields=['resuelto'], name='catalogo_im_resuelto_3d4e2f_idx'),
                    models.Index(fields=['usuario'], name='catalogo_im_usuario_5f6g3h_idx'),
                ],
            },
        ),
    ]
