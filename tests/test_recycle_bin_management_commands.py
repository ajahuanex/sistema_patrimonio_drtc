"""
Tests para los comandos de management de la papelera de reciclaje
"""
import pytest
from django.core.management import call_command
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from io import StringIO
import json
import os
import tempfile

from apps.core.models import RecycleBin, RecycleBinConfig, AuditLog
from apps.oficinas.models import Oficina


@pytest.mark.django_db
class TestRestoreFromBackupCommand:
    """Tests para el comando restore_from_backup"""

    def test_list_available_backups(self, admin_user, oficina_eliminada):
        """Debe listar elementos disponibles para restaurar"""
        # Crear log de auditoría
        AuditLog.objects.create(
            user=admin_user,
            action='delete',
            model_name='Oficina',
            object_id=str(oficina_eliminada.id),
            object_repr=str(oficina_eliminada),
            changes={
                'module_name': 'oficinas',
                'deleted_by': admin_user.username,
                'tipo': 'eliminacion_manual',
                'snapshot': {'nombre': oficina_eliminada.nombre}
            }
        )

        out = StringIO()
        call_command('restore_from_backup', '--list-only', stdout=out)
        
        output = out.getvalue()
        assert 'ELEMENTOS DISPONIBLES PARA RESTAURAR' in output
        assert str(oficina_eliminada) in output

    def test_restore_by_audit_log_id(self, admin_user, oficina_eliminada):
        """Debe restaurar un elemento específico por ID de audit log"""
        # Crear log de auditoría
        audit_log = AuditLog.objects.create(
            user=admin_user,
            action='delete',
            model_name='Oficina',
            object_id=str(oficina_eliminada.id),
            object_repr=str(oficina_eliminada),
            changes={
                'module_name': 'oficinas',
                'deleted_by': admin_user.username,
                'snapshot': {'nombre': oficina_eliminada.nombre}
            }
        )

        # Verificar que está eliminado
        assert oficina_eliminada.is_deleted

        out = StringIO()
        call_command(
            'restore_from_backup',
            f'--audit-log-id={audit_log.id}',
            '--force',
            stdout=out
        )

        # Verificar restauración
        oficina_eliminada.refresh_from_db()
        assert not oficina_eliminada.is_deleted

    def test_filter_by_date_range(self, admin_user, oficina_eliminada):
        """Debe filtrar por rango de fechas"""
        # Crear logs de diferentes fechas
        yesterday = timezone.now() - timedelta(days=1)
        AuditLog.objects.create(
            user=admin_user,
            action='delete',
            model_name='Oficina',
            object_id=str(oficina_eliminada.id),
            object_repr=str(oficina_eliminada),
            timestamp=yesterday,
            changes={'module_name': 'oficinas'}
        )

        today = timezone.now().date().strftime('%Y-%m-%d')
        out = StringIO()
        call_command(
            'restore_from_backup',
            f'--date-from={today}',
            '--list-only',
            stdout=out
        )

        output = out.getvalue()
        # No debería encontrar el log de ayer
        assert 'encontraron 0' in output.lower() or 'no se encontraron' in output.lower()

    def test_filter_by_module(self, admin_user, oficina_eliminada):
        """Debe filtrar por módulo"""
        AuditLog.objects.create(
            user=admin_user,
            action='delete',
            model_name='Oficina',
            object_id=str(oficina_eliminada.id),
            object_repr=str(oficina_eliminada),
            changes={'module_name': 'oficinas'}
        )

        out = StringIO()
        call_command(
            'restore_from_backup',
            '--module=bienes',
            '--list-only',
            stdout=out
        )

        output = out.getvalue()
        # No debería encontrar logs de oficinas
        assert 'encontraron 0' in output.lower() or 'no se encontraron' in output.lower()

    def test_recreate_recycle_entry(self, admin_user, oficina_eliminada):
        """Debe recrear entrada en RecycleBin al restaurar"""
        audit_log = AuditLog.objects.create(
            user=admin_user,
            action='delete',
            model_name='Oficina',
            object_id=str(oficina_eliminada.id),
            object_repr=str(oficina_eliminada),
            changes={
                'module_name': 'oficinas',
                'deleted_by': admin_user.username,
                'snapshot': {}
            }
        )

        initial_count = RecycleBin.objects.count()

        call_command(
            'restore_from_backup',
            f'--audit-log-id={audit_log.id}',
            '--force',
            '--recreate-recycle-entry',
            stdout=StringIO()
        )

        # Verificar que se creó entrada en RecycleBin
        assert RecycleBin.objects.count() > initial_count


@pytest.mark.django_db
class TestGenerateRecycleReportCommand:
    """Tests para el comando generate_recycle_report"""

    def test_generate_txt_report(self, admin_user, recycle_bin_item):
        """Debe generar reporte en formato texto"""
        out = StringIO()
        call_command('generate_recycle_report', '--format=txt', stdout=out)
        
        output = out.getvalue()
        assert 'REPORTE DE PAPELERA DE RECICLAJE' in output
        assert 'ESTADÍSTICAS GENERALES' in output
        assert 'Total de elementos:' in output

    def test_generate_json_report(self, admin_user, recycle_bin_item):
        """Debe generar reporte en formato JSON"""
        out = StringIO()
        call_command('generate_recycle_report', '--format=json', stdout=out)
        
        output = out.getvalue()
        # Verificar que es JSON válido
        data = json.loads(output.split('='*70)[1].strip())
        assert 'metadata' in data
        assert 'estadisticas' in data
        assert 'total_elementos' in data['estadisticas']

    def test_generate_csv_report(self, admin_user, recycle_bin_item):
        """Debe generar reporte en formato CSV"""
        out = StringIO()
        call_command('generate_recycle_report', '--format=csv', stdout=out)
        
        output = out.getvalue()
        assert 'ESTADÍSTICAS GENERALES' in output
        assert 'Métrica,Valor' in output

    def test_save_report_to_file(self, admin_user, recycle_bin_item):
        """Debe guardar reporte en archivo"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name

        try:
            call_command(
                'generate_recycle_report',
                '--format=txt',
                f'--output={temp_file}',
                stdout=StringIO()
            )

            # Verificar que el archivo existe y tiene contenido
            assert os.path.exists(temp_file)
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'REPORTE DE PAPELERA' in content
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_filter_by_date_range(self, admin_user, recycle_bin_item):
        """Debe filtrar por rango de fechas"""
        today = timezone.now().date().strftime('%Y-%m-%d')
        tomorrow = (timezone.now() + timedelta(days=1)).date().strftime('%Y-%m-%d')

        out = StringIO()
        call_command(
            'generate_recycle_report',
            '--format=txt',
            f'--date-from={today}',
            f'--date-to={tomorrow}',
            stdout=out
        )

        output = out.getvalue()
        assert 'Período:' in output

    def test_filter_by_module(self, admin_user, recycle_bin_item):
        """Debe filtrar por módulo"""
        out = StringIO()
        call_command(
            'generate_recycle_report',
            '--format=txt',
            '--module=oficinas',
            stdout=out
        )

        output = out.getvalue()
        assert 'REPORTE DE PAPELERA' in output

    def test_statistics_only(self, admin_user, recycle_bin_item):
        """Debe generar solo estadísticas sin detalles"""
        out = StringIO()
        call_command(
            'generate_recycle_report',
            '--format=json',
            '--statistics-only',
            stdout=out
        )

        output = out.getvalue()
        data = json.loads(output.split('='*70)[1].strip())
        assert 'estadisticas' in data
        assert 'elementos' not in data

    def test_include_audit_logs(self, admin_user, recycle_bin_item):
        """Debe incluir logs de auditoría"""
        # Crear algunos logs de auditoría
        AuditLog.objects.create(
            user=admin_user,
            action='delete',
            model_name='Oficina',
            object_id='1',
            object_repr='Test',
            changes={}
        )

        out = StringIO()
        call_command(
            'generate_recycle_report',
            '--format=json',
            '--audit-logs',
            stdout=out
        )

        output = out.getvalue()
        data = json.loads(output.split('='*70)[1].strip())
        assert 'audit_logs' in data

    def test_include_restored_items(self, admin_user, recycle_bin_item_restaurado):
        """Debe incluir elementos restaurados"""
        out = StringIO()
        call_command(
            'generate_recycle_report',
            '--format=txt',
            '--include-restored',
            stdout=out
        )

        output = out.getvalue()
        assert 'Elementos restaurados:' in output


@pytest.mark.django_db
class TestUpdateRetentionPoliciesCommand:
    """Tests para el comando update_retention_policies"""

    def test_show_current_configurations(self, recycle_bin_config):
        """Debe mostrar configuraciones actuales"""
        out = StringIO()
        call_command('update_retention_policies', '--show-current', stdout=out)
        
        output = out.getvalue()
        assert 'CONFIGURACIONES ACTUALES' in output
        assert 'oficinas' in output
        assert 'Días de retención:' in output

    def test_update_retention_days(self, recycle_bin_config):
        """Debe actualizar días de retención"""
        call_command(
            'update_retention_policies',
            '--module=oficinas',
            '--retention-days=60',
            '--force',
            stdout=StringIO()
        )

        recycle_bin_config.refresh_from_db()
        assert recycle_bin_config.retention_days == 60

    def test_update_warning_days(self, recycle_bin_config):
        """Debe actualizar días de advertencia"""
        call_command(
            'update_retention_policies',
            '--module=oficinas',
            '--warning-days=14',
            '--force',
            stdout=StringIO()
        )

        recycle_bin_config.refresh_from_db()
        assert recycle_bin_config.warning_days_before == 14

    def test_enable_auto_delete(self, recycle_bin_config):
        """Debe habilitar eliminación automática"""
        recycle_bin_config.auto_delete_enabled = False
        recycle_bin_config.save()

        call_command(
            'update_retention_policies',
            '--module=oficinas',
            '--enable-auto-delete',
            '--force',
            stdout=StringIO()
        )

        recycle_bin_config.refresh_from_db()
        assert recycle_bin_config.auto_delete_enabled is True

    def test_disable_auto_delete(self, recycle_bin_config):
        """Debe deshabilitar eliminación automática"""
        recycle_bin_config.auto_delete_enabled = True
        recycle_bin_config.save()

        call_command(
            'update_retention_policies',
            '--module=oficinas',
            '--disable-auto-delete',
            '--force',
            stdout=StringIO()
        )

        recycle_bin_config.refresh_from_db()
        assert recycle_bin_config.auto_delete_enabled is False

    def test_update_all_modules(self):
        """Debe actualizar todos los módulos"""
        # Crear configuraciones para múltiples módulos
        for module in ['oficinas', 'bienes', 'catalogo']:
            RecycleBinConfig.objects.create(
                module_name=module,
                retention_days=30
            )

        call_command(
            'update_retention_policies',
            '--module=all',
            '--retention-days=45',
            '--force',
            stdout=StringIO()
        )

        # Verificar que todos se actualizaron
        for config in RecycleBinConfig.objects.all():
            assert config.retention_days == 45

    def test_dry_run_mode(self, recycle_bin_config):
        """Debe mostrar cambios sin aplicarlos en modo dry-run"""
        original_days = recycle_bin_config.retention_days

        out = StringIO()
        call_command(
            'update_retention_policies',
            '--module=oficinas',
            '--retention-days=90',
            '--dry-run',
            stdout=out
        )

        output = out.getvalue()
        assert 'DRY-RUN' in output

        # Verificar que no se aplicaron cambios
        recycle_bin_config.refresh_from_db()
        assert recycle_bin_config.retention_days == original_days

    def test_update_existing_items(self, recycle_bin_config, recycle_bin_item):
        """Debe actualizar fechas de elementos existentes"""
        original_auto_delete = recycle_bin_item.auto_delete_at

        call_command(
            'update_retention_policies',
            '--module=oficinas',
            '--retention-days=60',
            '--update-existing-items',
            '--force',
            stdout=StringIO()
        )

        recycle_bin_item.refresh_from_db()
        # La fecha debería haber cambiado
        assert recycle_bin_item.auto_delete_at != original_auto_delete

    def test_validation_retention_days_positive(self):
        """Debe validar que días de retención sean positivos"""
        with pytest.raises(Exception):
            call_command(
                'update_retention_policies',
                '--module=oficinas',
                '--retention-days=0',
                '--force',
                stdout=StringIO()
            )

    def test_validation_conflicting_flags(self):
        """Debe validar flags conflictivos"""
        with pytest.raises(Exception):
            call_command(
                'update_retention_policies',
                '--module=oficinas',
                '--enable-auto-delete',
                '--disable-auto-delete',
                '--force',
                stdout=StringIO()
            )

    def test_audit_log_creation(self, recycle_bin_config):
        """Debe crear log de auditoría al actualizar"""
        initial_count = AuditLog.objects.count()

        call_command(
            'update_retention_policies',
            '--module=oficinas',
            '--retention-days=45',
            '--force',
            stdout=StringIO()
        )

        # Verificar que se creó log de auditoría
        assert AuditLog.objects.count() > initial_count
        
        latest_log = AuditLog.objects.latest('timestamp')
        assert latest_log.action == 'update'
        assert latest_log.model_name == 'RecycleBinConfig'

    def test_enable_restore_permissions(self, recycle_bin_config):
        """Debe actualizar permisos de restauración"""
        call_command(
            'update_retention_policies',
            '--module=oficinas',
            '--enable-restore-others',
            '--force',
            stdout=StringIO()
        )

        recycle_bin_config.refresh_from_db()
        assert recycle_bin_config.can_restore_others is True

    def test_requires_at_least_one_parameter(self):
        """Debe requerir al menos un parámetro"""
        with pytest.raises(Exception):
            call_command(
                'update_retention_policies',
                '--module=oficinas',
                '--force',
                stdout=StringIO()
            )


# Fixtures adicionales para los tests
@pytest.fixture
def oficina_eliminada(admin_user):
    """Crea una oficina eliminada"""
    oficina = Oficina.objects.create(
        codigo='TEST001',
        nombre='Oficina Test',
        direccion='Test Address',
        telefono='123456789',
        created_by=admin_user
    )
    oficina.soft_delete(user=admin_user, reason='Test')
    return oficina


@pytest.fixture
def recycle_bin_item(admin_user, oficina_eliminada):
    """Crea un item en la papelera"""
    from django.contrib.contenttypes.models import ContentType
    
    content_type = ContentType.objects.get_for_model(Oficina)
    return RecycleBin.objects.create(
        content_type=content_type,
        object_id=oficina_eliminada.id,
        object_repr=str(oficina_eliminada),
        module_name='oficinas',
        deleted_by=admin_user,
        deletion_reason='Test deletion',
        auto_delete_at=timezone.now() + timedelta(days=30)
    )


@pytest.fixture
def recycle_bin_item_restaurado(admin_user, oficina_eliminada):
    """Crea un item restaurado en la papelera"""
    from django.contrib.contenttypes.models import ContentType
    
    content_type = ContentType.objects.get_for_model(Oficina)
    item = RecycleBin.objects.create(
        content_type=content_type,
        object_id=oficina_eliminada.id,
        object_repr=str(oficina_eliminada),
        module_name='oficinas',
        deleted_by=admin_user,
        deletion_reason='Test deletion',
        auto_delete_at=timezone.now() + timedelta(days=30),
        restored_at=timezone.now(),
        restored_by=admin_user
    )
    return item


@pytest.fixture
def recycle_bin_config():
    """Crea una configuración de papelera"""
    return RecycleBinConfig.objects.create(
        module_name='oficinas',
        retention_days=30,
        auto_delete_enabled=True,
        warning_days_before=7,
        final_warning_days_before=1,
        can_restore_own=True,
        can_restore_others=False
    )
