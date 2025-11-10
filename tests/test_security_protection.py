"""
Tests completos para protección contra ataques de seguridad
Incluye rate limiting, CAPTCHA, bloqueo progresivo y logging detallado
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from apps.core.models import SecurityCodeAttempt, RecycleBin, RecycleBinConfig
from apps.core.utils import RecycleBinService
from apps.oficinas.models import Oficina
from django.contrib.contenttypes.models import ContentType


class RateLimitingTest(TestCase):
    """Tests para rate limiting"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user.profile.role = 'administrador'
        self.user.profile.save()
    
    def test_rate_limit_not_exceeded(self):
        """Test usuario dentro del límite de rate"""
        # Crear 4 intentos (límite es 5)
        for i in range(4):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False,
                ip_address=f'192.168.1.{i}'
            )
        
        is_limited, count, time_reset = SecurityCodeAttempt.check_rate_limit(
            self.user, max_requests=5, time_window_minutes=10
        )
        
        self.assertFalse(is_limited)
        self.assertEqual(count, 4)
    
    def test_rate_limit_exceeded(self):
        """Test usuario excede el límite de rate"""
        # Crear 5 intentos (alcanza el límite)
        for i in range(5):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False,
                ip_address=f'192.168.1.{i}'
            )
        
        is_limited, count, time_reset = SecurityCodeAttempt.check_rate_limit(
            self.user, max_requests=5, time_window_minutes=10
        )
        
        self.assertTrue(is_limited)
        self.assertEqual(count, 5)
        self.assertGreater(time_reset, 0)
    
    def test_rate_limit_resets_after_time_window(self):
        """Test rate limit se resetea después de la ventana de tiempo"""
        # Crear 5 intentos antiguos
        for i in range(5):
            attempt = SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
            # Mover al pasado (fuera de ventana de 10 minutos)
            attempt.attempted_at = timezone.now() - timedelta(minutes=15)
            attempt.save()
        
        is_limited, count, time_reset = SecurityCodeAttempt.check_rate_limit(
            self.user, max_requests=5, time_window_minutes=10
        )
        
        # No debe estar limitado porque los intentos son antiguos
        self.assertFalse(is_limited)
        self.assertEqual(count, 0)
    
    def test_rate_limit_blocks_permanent_delete(self):
        """Test rate limiting bloquea eliminación permanente"""
        from django.conf import settings
        settings.PERMANENT_DELETE_CODE = 'TEST_CODE'
        
        # Crear oficina y entrada en papelera
        oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Test Office',
            direccion='Test Address',
            created_by=self.user
        )
        oficina.soft_delete(user=self.user)
        
        content_type = ContentType.objects.get_for_model(Oficina)
        recycle_entry = RecycleBin.objects.create(
            content_type=content_type,
            object_id=oficina.pk,
            object_repr=str(oficina),
            module_name='oficinas',
            deleted_by=self.user
        )
        
        # Exceder rate limit
        for i in range(5):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        # Intentar eliminación permanente
        success, message = RecycleBinService.permanent_delete(
            recycle_entry,
            self.user,
            'TEST_CODE',
            ip_address='127.0.0.1'
        )
        
        self.assertFalse(success)
        self.assertIn('Demasiados intentos', message)


class ProgressiveLockoutTest(TestCase):
    """Tests para sistema de bloqueo progresivo"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.profile.role = 'administrador'
        self.user.profile.save()
    
    def test_lockout_level_normal(self):
        """Test nivel de bloqueo normal (0-2 intentos)"""
        # Sin intentos fallidos
        level = SecurityCodeAttempt.get_lockout_level(self.user)
        
        self.assertEqual(level['level'], 0)
        self.assertEqual(level['name'], 'Normal')
        self.assertEqual(level['max_attempts'], 3)
        self.assertEqual(level['lockout_minutes'], 30)
        self.assertFalse(level['requires_admin_unlock'])
    
    def test_lockout_level_medium(self):
        """Test nivel de bloqueo medio (3-5 intentos)"""
        # Crear 4 intentos fallidos en últimas 24 horas
        for i in range(4):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        level = SecurityCodeAttempt.get_lockout_level(self.user)
        
        self.assertEqual(level['level'], 1)
        self.assertEqual(level['name'], 'Medio')
        self.assertEqual(level['max_attempts'], 3)
        self.assertEqual(level['lockout_minutes'], 30)
    
    def test_lockout_level_high(self):
        """Test nivel de bloqueo alto (6-9 intentos)"""
        # Crear 7 intentos fallidos en últimas 24 horas
        for i in range(7):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        level = SecurityCodeAttempt.get_lockout_level(self.user)
        
        self.assertEqual(level['level'], 2)
        self.assertEqual(level['name'], 'Alto')
        self.assertEqual(level['max_attempts'], 2)
        self.assertEqual(level['lockout_minutes'], 60)
        self.assertFalse(level['requires_admin_unlock'])
    
    def test_lockout_level_critical(self):
        """Test nivel de bloqueo crítico (10+ intentos)"""
        # Crear 11 intentos fallidos en últimas 24 horas
        for i in range(11):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        level = SecurityCodeAttempt.get_lockout_level(self.user)
        
        self.assertEqual(level['level'], 3)
        self.assertEqual(level['name'], 'Crítico')
        self.assertEqual(level['max_attempts'], 1)
        self.assertEqual(level['lockout_minutes'], 120)
        self.assertTrue(level['requires_admin_unlock'])
    
    def test_progressive_lockout_increases_duration(self):
        """Test bloqueo progresivo aumenta duración"""
        # Nivel medio: 3 intentos fallidos
        for i in range(3):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        level_medium = SecurityCodeAttempt.get_lockout_level(self.user)
        
        # Nivel alto: 4 intentos más (total 7)
        for i in range(4):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        level_high = SecurityCodeAttempt.get_lockout_level(self.user)
        
        # Verificar que el bloqueo es más largo en nivel alto
        self.assertGreater(
            level_high['lockout_minutes'],
            level_medium['lockout_minutes']
        )


class CaptchaValidationTest(TestCase):
    """Tests para validación CAPTCHA"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.profile.role = 'administrador'
        self.user.profile.save()
    
    def test_captcha_not_required_initially(self):
        """Test CAPTCHA no es requerido inicialmente"""
        requires_captcha = SecurityCodeAttempt.requires_captcha_validation(self.user)
        self.assertFalse(requires_captcha)
    
    def test_captcha_required_after_threshold(self):
        """Test CAPTCHA es requerido después del umbral"""
        # Crear 2 intentos fallidos (umbral por defecto)
        for i in range(2):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        requires_captcha = SecurityCodeAttempt.requires_captcha_validation(
            self.user, captcha_threshold=2
        )
        
        self.assertTrue(requires_captcha)
    
    @patch('apps.core.utils.requests.post')
    def test_captcha_validation_success(self, mock_post):
        """Test validación CAPTCHA exitosa"""
        # Mock respuesta exitosa de Google reCAPTCHA
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        from django.conf import settings
        settings.RECAPTCHA_SECRET_KEY = 'test_secret_key'
        
        is_valid = RecycleBinService._validate_captcha(
            'test_captcha_response',
            '127.0.0.1'
        )
        
        self.assertTrue(is_valid)
        mock_post.assert_called_once()
    
    @patch('apps.core.utils.requests.post')
    def test_captcha_validation_failure(self, mock_post):
        """Test validación CAPTCHA fallida"""
        # Mock respuesta fallida de Google reCAPTCHA
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': False}
        mock_post.return_value = mock_response
        
        from django.conf import settings
        settings.RECAPTCHA_SECRET_KEY = 'test_secret_key'
        
        is_valid = RecycleBinService._validate_captcha(
            'invalid_captcha_response',
            '127.0.0.1'
        )
        
        self.assertFalse(is_valid)
    
    def test_captcha_validation_without_secret_key(self):
        """Test validación CAPTCHA sin clave secreta configurada"""
        from django.conf import settings
        if hasattr(settings, 'RECAPTCHA_SECRET_KEY'):
            delattr(settings, 'RECAPTCHA_SECRET_KEY')
        
        # Sin clave secreta, debe permitir por defecto (modo desarrollo)
        is_valid = RecycleBinService._validate_captcha(
            'any_response',
            '127.0.0.1'
        )
        
        self.assertTrue(is_valid)


class UnauthorizedAccessLoggingTest(TestCase):
    """Tests para logging de intentos de acceso no autorizado"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Usuario sin permisos de administrador
        self.user.profile.role = 'consulta'
        self.user.profile.save()
    
    def test_log_unauthorized_access_attempt(self):
        """Test registrar intento de acceso no autorizado"""
        attempt = SecurityCodeAttempt.log_unauthorized_access_attempt(
            user=self.user,
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0',
            request_path='/core/recycle-bin/permanent-delete/1/',
            referer='/core/recycle-bin/detail/1/',
            reason='Usuario sin permisos de administrador'
        )
        
        self.assertIsNotNone(attempt)
        self.assertEqual(attempt.user, self.user)
        self.assertEqual(attempt.ip_address, '192.168.1.100')
        self.assertEqual(attempt.attempt_type, 'unauthorized_access')
        self.assertFalse(attempt.success)
    
    def test_unauthorized_access_creates_audit_log(self):
        """Test acceso no autorizado crea log de auditoría"""
        from apps.core.models import DeletionAuditLog
        
        SecurityCodeAttempt.log_unauthorized_access_attempt(
            user=self.user,
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0',
            request_path='/core/recycle-bin/permanent-delete/1/',
            reason='Usuario sin permisos'
        )
        
        # Verificar que se creó entrada en DeletionAuditLog
        audit_logs = DeletionAuditLog.objects.filter(
            action='unauthorized_access',
            user=self.user
        )
        
        self.assertEqual(audit_logs.count(), 1)


class SecuritySummaryTest(TestCase):
    """Tests para resumen de seguridad"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.profile.role = 'administrador'
        self.user.profile.save()
    
    def test_security_summary_basic(self):
        """Test resumen de seguridad básico"""
        # Crear varios intentos
        for i in range(3):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=True
        )
        
        summary = SecurityCodeAttempt.get_security_summary(self.user, hours=24)
        
        self.assertEqual(summary['total_attempts'], 4)
        self.assertEqual(summary['failed_attempts'], 3)
        self.assertEqual(summary['successful_attempts'], 1)
        self.assertIn('lockout_level', summary)
        self.assertIn('current_status', summary)
    
    def test_security_summary_includes_current_status(self):
        """Test resumen incluye estado actual"""
        # Crear intentos para activar bloqueo
        for i in range(3):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        summary = SecurityCodeAttempt.get_security_summary(self.user, hours=24)
        
        current_status = summary['current_status']
        self.assertIn('is_locked', current_status)
        self.assertIn('requires_captcha', current_status)
        self.assertIn('is_rate_limited', current_status)
        self.assertTrue(current_status['is_locked'])


class SuspiciousActivityReportTest(TestCase):
    """Tests para reporte de actividad sospechosa"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.user1.profile.role = 'administrador'
        self.user2.profile.role = 'administrador'
        self.user1.profile.save()
        self.user2.profile.save()
    
    def test_suspicious_activity_report_structure(self):
        """Test estructura del reporte de actividad sospechosa"""
        report = SecurityCodeAttempt.get_suspicious_activity_report(hours=24)
        
        self.assertIn('period_hours', report)
        self.assertIn('total_attempts', report)
        self.assertIn('failed_attempts', report)
        self.assertIn('successful_attempts', report)
        self.assertIn('rate_limited_attempts', report)
        self.assertIn('users_with_most_failures', report)
        self.assertIn('ips_with_most_failures', report)
        self.assertIn('currently_locked_users', report)
    
    def test_suspicious_activity_identifies_locked_users(self):
        """Test reporte identifica usuarios bloqueados"""
        # Bloquear user1
        for i in range(3):
            SecurityCodeAttempt.record_attempt(
                user=self.user1,
                success=False
            )
        
        report = SecurityCodeAttempt.get_suspicious_activity_report(hours=24)
        
        self.assertGreater(len(report['currently_locked_users']), 0)
        locked_user = report['currently_locked_users'][0]
        self.assertEqual(locked_user['username'], 'user1')
    
    def test_suspicious_activity_tracks_ips(self):
        """Test reporte rastrea IPs con más intentos"""
        # Crear intentos desde diferentes IPs
        for i in range(5):
            SecurityCodeAttempt.record_attempt(
                user=self.user1,
                success=False,
                ip_address='192.168.1.100'
            )
        
        for i in range(2):
            SecurityCodeAttempt.record_attempt(
                user=self.user2,
                success=False,
                ip_address='192.168.1.200'
            )
        
        report = SecurityCodeAttempt.get_suspicious_activity_report(hours=24)
        
        ips = report['ips_with_most_failures']
        self.assertGreater(len(ips), 0)
        # La IP con más intentos debe ser la primera
        self.assertEqual(ips[0]['ip_address'], '192.168.1.100')
        self.assertEqual(ips[0]['failure_count'], 5)


class DetailedLoggingTest(TestCase):
    """Tests para logging detallado"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.user.profile.role = 'administrador'
        self.user.profile.save()
    
    def test_attempt_records_all_metadata(self):
        """Test intento registra todos los metadatos"""
        attempt = SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=False,
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            entry_id=123,
            attempt_type='permanent_delete',
            blocked_by_rate_limit=False,
            requires_captcha=True,
            captcha_passed=False,
            session_id='abc123xyz',
            request_path='/core/recycle-bin/permanent-delete/123/',
            referer='/core/recycle-bin/detail/123/'
        )
        
        self.assertEqual(attempt.ip_address, '192.168.1.100')
        self.assertIn('Mozilla', attempt.user_agent)
        self.assertEqual(attempt.recycle_bin_entry_id, 123)
        self.assertEqual(attempt.attempt_type, 'permanent_delete')
        self.assertTrue(attempt.requires_captcha)
        self.assertFalse(attempt.captcha_passed)
        self.assertEqual(attempt.session_id, 'abc123xyz')
        self.assertIn('permanent-delete', attempt.request_path)
    
    def test_attempt_tracks_rate_limiting(self):
        """Test intento rastrea bloqueo por rate limiting"""
        attempt = SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=False,
            blocked_by_rate_limit=True
        )
        
        self.assertTrue(attempt.blocked_by_rate_limit)
    
    def test_attempt_tracks_captcha_requirement(self):
        """Test intento rastrea requerimiento de CAPTCHA"""
        attempt = SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=False,
            requires_captcha=True,
            captcha_passed=True
        )
        
        self.assertTrue(attempt.requires_captcha)
        self.assertTrue(attempt.captcha_passed)
