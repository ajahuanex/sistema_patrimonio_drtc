/**
 * Sistema de notificaciones en tiempo real para la papelera de reciclaje.
 * Actualiza contadores y muestra alertas de elementos próximos a eliminarse.
 */

(function() {
    'use strict';
    
    // Configuración
    const CONFIG = {
        updateInterval: 60000, // Actualizar cada 60 segundos
        apiEndpoint: '/api/recycle-bin/status/',
        enableNotifications: true,
        enableSound: false,
    };
    
    // Estado de la aplicación
    let state = {
        lastCount: 0,
        lastNearDeleteCount: 0,
        isInitialized: false,
    };
    
    /**
     * Inicializa el sistema de notificaciones
     */
    function init() {
        if (state.isInitialized) {
            return;
        }
        
        // Verificar si el usuario puede ver la papelera
        const canViewRecycleBin = document.querySelector('[data-recycle-bin-enabled]');
        if (!canViewRecycleBin) {
            return;
        }
        
        state.isInitialized = true;
        
        // Actualizar contadores inmediatamente
        updateCounters();
        
        // Configurar actualización periódica
        setInterval(updateCounters, CONFIG.updateInterval);
        
        console.log('Sistema de notificaciones de papelera inicializado');
    }
    
    /**
     * Actualiza los contadores de la papelera
     */
    function updateCounters() {
        fetch(CONFIG.apiEndpoint, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'same-origin',
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error al obtener estado de papelera');
            }
            return response.json();
        })
        .then(data => {
            handleCounterUpdate(data);
        })
        .catch(error => {
            console.error('Error actualizando contadores de papelera:', error);
        });
    }
    
    /**
     * Maneja la actualización de contadores
     */
    function handleCounterUpdate(data) {
        const { count, near_delete_count } = data;
        
        // Actualizar badges en navegación
        updateNavigationBadges(count, near_delete_count);
        
        // Mostrar notificación si hay nuevos elementos próximos a eliminarse
        if (near_delete_count > state.lastNearDeleteCount && state.lastNearDeleteCount > 0) {
            showNotification(
                'Elementos próximos a eliminarse',
                `Tienes ${near_delete_count} elementos que se eliminarán pronto`,
                'warning'
            );
        }
        
        // Actualizar estado
        state.lastCount = count;
        state.lastNearDeleteCount = near_delete_count;
    }
    
    /**
     * Actualiza los badges en la navegación
     */
    function updateNavigationBadges(count, nearDeleteCount) {
        // Actualizar badge de contador total
        const countBadge = document.querySelector('.recycle-bin-count-badge');
        if (countBadge) {
            if (count > 0) {
                countBadge.textContent = count;
                countBadge.style.display = 'inline';
            } else {
                countBadge.style.display = 'none';
            }
        }
        
        // Actualizar badge de elementos próximos a eliminarse
        const nearDeleteBadge = document.querySelector('.recycle-bin-near-delete-badge');
        if (nearDeleteBadge) {
            if (nearDeleteCount > 0) {
                nearDeleteBadge.textContent = nearDeleteCount;
                nearDeleteBadge.style.display = 'inline';
            } else {
                nearDeleteBadge.style.display = 'none';
            }
        }
    }
    
    /**
     * Muestra una notificación toast
     */
    function showNotification(title, message, type = 'info') {
        if (!CONFIG.enableNotifications) {
            return;
        }
        
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <strong>${title}</strong><br>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            notification.remove();
        }, 5000);
        
        // Reproducir sonido si está habilitado
        if (CONFIG.enableSound) {
            playNotificationSound();
        }
    }
    
    /**
     * Reproduce un sonido de notificación
     */
    function playNotificationSound() {
        // Crear un beep simple usando Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.error('Error reproduciendo sonido:', error);
        }
    }
    
    /**
     * Formatea tiempo relativo (ej: "hace 2 horas")
     */
    function formatRelativeTime(timestamp) {
        const now = new Date();
        const date = new Date(timestamp);
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) {
            return 'hace un momento';
        } else if (diffMins < 60) {
            return `hace ${diffMins} minuto${diffMins !== 1 ? 's' : ''}`;
        } else if (diffHours < 24) {
            return `hace ${diffHours} hora${diffHours !== 1 ? 's' : ''}`;
        } else {
            return `hace ${diffDays} día${diffDays !== 1 ? 's' : ''}`;
        }
    }
    
    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Exponer API pública
    window.RecycleBinNotifications = {
        updateCounters: updateCounters,
        showNotification: showNotification,
        config: CONFIG,
    };
})();
