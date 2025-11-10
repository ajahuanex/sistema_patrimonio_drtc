"""
Tests para el modelo SecurityCodeAttempt y sistema de bloqueo temporal
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from apps.core.models import SecurityCodeAttempt, RecycleBin, RecycleBinConfig
from apps.oficinas.models import Oficina
from django.contrib.contenttypes.models import ContentType


class SecurityCodeAttemptModelTest(TestCase):
    """Tests para el modelo SecurityCodeAttempt"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.user.profile.role = 'administrador'
        self.user.profile.save()
    
    def test_create_security_code_attempt(self):
        """Test crear registro de intento de código de seguridad"""
        attempt = SecurityCodeAttempt.objects.create(
            user=self.user,
            success=False,
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0',
            recycle_bin_entry_id=1
        )
        
        self.assertIsNotNone(attempt.id)
        self.assertEqual(attempt.user, self.user)
        self.assertFalse(attempt.success)
        self.assertEqual(attempt.ip_address, '192.168.1.1')
        self.assertIsNotNone(attempt.attempted_at)
    
    def test_record_attempt_method(self):
        """Test método record_attempt"""
        attempt = SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=True,
            ip_address='10.0.0.1',
            user_agent='Chrome',
            entry_id=5
        )
        
        self.assertIsNotNone(attempt)
        self.assertTrue(attempt.success)
        self.assertEqual(attempt.ip_address, '10.0.0.1')
        self.assertEqual(attempt.recycle_bin_entry_id, 5)
    
    def test_get_recent_failed_attempts(self):
        """Test obtener intentos fallidos recientes"""
        # Crear varios intentos fallidos
        for i in range(3):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False,
                ip_address=f'192.168.1.{i}'
            )
        
        # Crear un intento exitoso
        SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=True,
            ip_address='192.168.1.100'
        )
        
        # Obtener intentos fallidos recientes
        recent_failures = SecurityCodeAttempt.get_recent_failed_attempts(self.user, minutes=30)
        
        self.assertEqual(recent_failures.count(), 3)
        for attempt in recent_failures:
            self.assertFalse(attempt.success)
    
    def test_get_recent_failed_attempts_time_window(self):
        """Test ventana de tiempo para intentos fallidos"""
        # Crear intento antiguo (fuera de ventana)
        old_attempt = SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=False
        )
        old_attempt.attempted_at = timezone.now() - timedelta(minutes=35)
        old_attempt.save()
        
        # Crear intento reciente
        SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=False
        )
        
        # Obtener intentos en ventana de 30 minutos
        recent_failures = SecurityCodeAttempt.get_recent_failed_attempts(self.user, minutes=30)
        
        # Solo debe contar el intento reciente
        self.assertEqual(recent_failures.count(), 1)
    
    def test_is_user_locked_out_no_attempts(self):
        """Test usuario sin intentos no está bloqueado"""
        is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(self.user)
        
        self.assertFalse(is_locked)
        self.assertEqual(attempts, 0)
        self.assertEqual(time_remaining, 0)
    
    def test_is_user_locked_out_below_threshold(self):
        """Test usuario con intentos por debajo del umbral"""
        # Crear 2 intentos fallidos (umbral es 3)
        for i in range(2):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(
            self.user, max_attempts=3
        )
        
        self.assertFalse(is_locked)
        self.assertEqual(attempts, 2)
    
    def test_is_user_locked_out_at_threshold(self):
        """Test usuario bloqueado al alcanzar umbral"""
        # Crear 3 intentos fallidos
        for i in range(3):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(
            self.user, max_attempts=3, lockout_minutes=30
        )
        
        self.assertTrue(is_locked)
        self.assertEqual(attempts, 3)
        self.assertGreater(time_remaining, 0)
        self.assertLessEqual(time_remaining, 30)
    
    def test_lockout_expires_after_time(self):
        """Test bloqueo expira después del tiempo configurado"""
        # Crear 3 intentos fallidos antiguos
        for i in range(3):
            attempt = SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
            # Mover al pasado (más de 30 minutos)
            attempt.attempted_at = timezone.now() - timedelta(minutes=35)
            attempt.save()
        
        is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(
            self.user, max_attempts=3, lockout_minutes=30
        )
        
        # No debe estar bloqueado porque los intentos son antiguos
        self.assertFalse(is_locked)
        self.assertEqual(attempts, 0)
    
    def test_successful_attempt_does_not_count_for_lockout(self):
        """Test intentos exitosos no cuentan para bloqueo"""
        # Crear 2 intentos fallidos
        for i in range(2):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        # Crear 1 intento exitoso
        SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=True
        )
        
        is_locked, attempts, time_remaining = SecurityCodeAttempt.is_user_locked_out(
            self.user, max_attempts=3
        )
        
        # Solo debe contar los 2 fallidos
        self.assertFalse(is_locked)
        self.assertEqual(attempts, 2)
    
    def test_multiple_users_independent_lockouts(self):
        """Test bloqueos son independientes por usuario"""
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        
        # Bloquear user1
        for i in range(3):
            SecurityCodeAttempt.record_attempt(
                user=self.user,
                success=False
            )
        
        # user2 sin intentos
        is_locked1, _, _ = SecurityCodeAttempt.is_user_locked_out(self.user, max_attempts=3)
        is_locked2, _, _ = SecurityCodeAttempt.is_user_locked_out(user2, max_attempts=3)
        
        self.assertTrue(is_locked1)
        self.assertFalse(is_locked2)
    
    def test_str_representation(self):
        """Test representación en string"""
        attempt = SecurityCodeAttempt.record_attempt(
            user=self.user,
            success=False
        )
        
        str_repr = str(attempt)
        self.assertIn(self.user.username, str_repr)
        self.assertIn('Fallido', str_repr)
    
    def test_ordering(self):
        """Test ordenamiento por fecha descendente"""
        # Crear varios intentos
        attempt1 = SecurityCodeAttempt.record_attempt(user=self.user, success=False)
        attempt2 = SecurityCodeAttempt.record_attempt(user=self.user, success=False)
        attempt3 = SecurityCodeAttempt.record_attempt(user=self.user, success=True)
        
        attempts = SecurityCodeAttempt.objects.all()
        
        # Debe estar ordenado por fecha descendente (más reciente primero)
        self.assertEqual(attempts[0].id, attempt3.id)
        self.assertEqual(attempts[1].id, attempt2.id)
        self.assertEqual(attempts[2].id, attempt1.id)


class SecurityCodeIntegrationTest(TestCase):
    """Tests de integración con RecycleBinService"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        from django.conf import settings
        settings.PERMANENT_DELETE_CODE = 'TEST_CODE_123'
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )
        self.admin_user.profile.role = 'administrador'
        self.admin_user.profile.save()
        
        # Crear oficina y entrada en papelera
        self.oficina = Oficina.objects.create(
            codigo='OF001',
            nombre='Oficina Test',
            direccion='Test Address',
            created_by=self.admin_user
        )
        self.oficina.soft_delete(user=self.admin_user, reason='Test deletion')
        
        content_type = ContentType.objects.get_for_model(Oficina)
        self.recycle_entry = RecycleBin.objects.create(
            content_type=content_type,
            object_id=self.oficina.pk,
            object_repr=str(self.oficina),
            module_name='oficinas',
            deleted_by=self.admin_user
        )
    
    def test_permanent_delete_with_correct_code(self):
        """Test eliminación permanente con código correcto"""
        from apps.core.utils import RecycleBinService
        
        success, message = RecycleBinService.permanent_delete(
            self.recycle_entry,
            self.admin_user,
            'TEST_CODE_123',
            reason='Test permanent deletion',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
        
        self.assertTrue(success)
        self.assertIn('permanentemente', message.lower())
        
        # Verificar que se registró intento exitoso
        attempts = SecurityCodeAttempt.objects.filter(user=self.admin_user, success=True)
        self.assertEqual(attempts.count(), 1)
    
    def test_permanent_delete_with_incorrect_code(self):
        """Test eliminación permanente con código incorrecto"""
        from apps.core.utils import RecycleBinService
        
        success, message = RecycleBinService.permanent_delete(
            self.recycle_entry,
            self.admin_user,
            'WRONG_CODE',
            reason='Test',
            ip_address='127.0.0.1'
        )
        
        self.assertFalse(success)
        self.assertIn('incorrecto', message.lower())
        
        # Verificar que se registró intento fallido
        attempts = SecurityCodeAttempt.objects.filter(user=self.admin_user, success=False)
        self.assertEqual(attempts.count(), 1)
    
    def test_permanent_delete_lockout_after_multiple_failures(self):
        """Test bloqueo después de múltiples intentos fallidos"""
        from apps.core.utils import RecycleBinService
        
        # Realizar 3 intentos fallidos
        for i in range(3):
            success, message = RecycleBinService.permanent_delete(
                self.recycle_entry,
                self.admin_user,
                'WRONG_CODE',
                reason='Test',
                ip_address='127.0.0.1'
            )
            self.assertFalse(success)
        
        # Cuarto intento debe estar bloqueado
        success, message = RecycleBinService.permanent_delete(
            self.recycle_entry,
            self.admin_user,
            'TEST_CODE_123',  # Incluso con código correcto
            reason='Test',
            ip_address='127.0.0.1'
        )
        
        self.assertFalse(success)
        self.assertIn('bloqueado', message.lower())
    
    def test_permanent_delete_shows_remaining_attempts(self):
        """Test mensaje muestra intentos restantes"""
        from apps.core.utils import RecycleBinService
        
        # Primer intento fallido
        success, message = RecycleBinService.permanent_delete(
            self.recycle_entry,
            self.admin_user,
            'WRONG_CODE',
            reason='Test',
            ip_address='127.0.0.1'
        )
        
        self.assertFalse(success)
        self.assertIn('2', message)  # Debe mostrar 2 intentos restantes
        self.assertIn('intento', message.lower())

