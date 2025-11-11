// JavaScript básico para el Sistema de Patrimonio

document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema de Patrimonio - Frontend cargado');
    
    // Inicializar componentes básicos
    initializeBasicComponents();
    
    // Mostrar dashboard básico si no hay React
    if (document.getElementById('root')) {
        showBasicDashboard();
    }
});

function initializeBasicComponents() {
    // Agregar funcionalidad básica a botones
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Agregar efecto de ripple
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Mejorar formularios
    enhanceForms();
    
    // Agregar tooltips básicos
    addBasicTooltips();
}

function enhanceForms() {
    // Agregar validación visual a campos de formulario
    document.querySelectorAll('input, select, textarea').forEach(field => {
        field.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        field.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
            
            // Validación básica
            if (this.hasAttribute('required') && !this.value.trim()) {
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
                if (this.value.trim()) {
                    this.classList.add('is-valid');
                }
            }
        });
    });
}

function addBasicTooltips() {
    // Agregar tooltips básicos usando el atributo title
    document.querySelectorAll('[title]').forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            showTooltip(e.target, e.target.getAttribute('title'));
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 1000;
        pointer-events: none;
        white-space: nowrap;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
}

function hideTooltip() {
    const tooltip = document.querySelector('.custom-tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function showBasicDashboard() {
    const root = document.getElementById('root');
    if (!root) return;
    
    // Verificar si ya hay contenido React
    setTimeout(() => {
        if (root.innerHTML.includes('loading-container')) {
            // Mostrar dashboard básico
            root.innerHTML = createBasicDashboard();
            initializeDashboard();
        }
    }, 2000);
}

function createBasicDashboard() {
    const userData = window.USER_DATA || {};
    
    return `
        <div class="dashboard-container">
            <!-- Header -->
            <div class="dashboard-header">
                <div class="container">
                    <h1>Sistema de Patrimonio</h1>
                    <p>Dirección Regional de Transportes y Comunicaciones - Puno</p>
                    <p>Bienvenido, ${userData.firstName || userData.username || 'Usuario'}</p>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="container">
                <!-- Stats Grid -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="total-bienes">-</div>
                        <div class="stat-label">Bienes Registrados</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="total-oficinas">-</div>
                        <div class="stat-label">Oficinas</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="total-catalogos">-</div>
                        <div class="stat-label">Catálogos SBN</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="bienes-activos">-</div>
                        <div class="stat-label">Bienes Activos</div>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Acciones Rápidas</h2>
                    </div>
                    
                    <div class="quick-actions">
                        <a href="/bienes/crear/" class="action-card">
                            <div class="action-icon">📦</div>
                            <div class="action-title">Registrar Bien</div>
                            <div class="action-description">Agregar nuevo bien patrimonial</div>
                        </a>
                        
                        <a href="/bienes/" class="action-card">
                            <div class="action-icon">📋</div>
                            <div class="action-title">Ver Inventario</div>
                            <div class="action-description">Consultar bienes registrados</div>
                        </a>
                        
                        <a href="/catalogo/importar/" class="action-card">
                            <div class="action-icon">📥</div>
                            <div class="action-title">Importar Datos</div>
                            <div class="action-description">Cargar datos desde Excel</div>
                        </a>
                        
                        <a href="/reportes/" class="action-card">
                            <div class="action-icon">📊</div>
                            <div class="action-title">Generar Reportes</div>
                            <div class="action-description">Crear reportes y estadísticas</div>
                        </a>
                        
                        <a href="/admin/" class="action-card">
                            <div class="action-icon">⚙️</div>
                            <div class="action-title">Administración</div>
                            <div class="action-description">Panel de administración</div>
                        </a>
                        
                        <a href="/accounts/logout/" class="action-card">
                            <div class="action-icon">🚪</div>
                            <div class="action-title">Cerrar Sesión</div>
                            <div class="action-description">Salir del sistema</div>
                        </a>
                    </div>
                </div>
                
                <!-- Recent Activity -->
                <div class="card">
                    <div class="card-header">
                        <h2 class="card-title">Actividad Reciente</h2>
                    </div>
                    <div id="recent-activity">
                        <p class="text-center">Cargando actividad reciente...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function initializeDashboard() {
    // Cargar estadísticas básicas
    loadDashboardStats();
    
    // Cargar actividad reciente
    loadRecentActivity();
}

function loadDashboardStats() {
    // Simular carga de estadísticas
    // En una implementación real, esto haría llamadas AJAX a la API
    
    setTimeout(() => {
        document.getElementById('total-bienes').textContent = '0';
        document.getElementById('total-oficinas').textContent = '0';
        document.getElementById('total-catalogos').textContent = '0';
        document.getElementById('bienes-activos').textContent = '0';
    }, 1000);
}

function loadRecentActivity() {
    setTimeout(() => {
        const activityContainer = document.getElementById('recent-activity');
        activityContainer.innerHTML = `
            <div class="text-center">
                <p>No hay actividad reciente registrada.</p>
                <a href="/bienes/crear/" class="btn btn-primary">Registrar primer bien</a>
            </div>
        `;
    }, 1500);
}

// Utilidades globales
window.PatrimonioUtils = {
    showNotification: function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        switch(type) {
            case 'success':
                notification.style.backgroundColor = '#28a745';
                break;
            case 'error':
                notification.style.backgroundColor = '#dc3545';
                break;
            case 'warning':
                notification.style.backgroundColor = '#ffc107';
                notification.style.color = '#212529';
                break;
            default:
                notification.style.backgroundColor = '#17a2b8';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    },
    
    formatDate: function(date) {
        return new Date(date).toLocaleDateString('es-PE');
    },
    
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('es-PE', {
            style: 'currency',
            currency: 'PEN'
        }).format(amount);
    }
};

// Agregar estilos CSS adicionales
const additionalStyles = `
    <style>
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .ripple {
            position: absolute;
            border-radius: 50%;
            background: rgba(255,255,255,0.3);
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        }
        
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        .focused {
            transform: scale(1.02);
            transition: transform 0.2s ease;
        }
        
        .is-invalid {
            border-color: #dc3545 !important;
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25) !important;
        }
        
        .is-valid {
            border-color: #28a745 !important;
            box-shadow: 0 0 0 0.2rem rgba(40, 167, 69, 0.25) !important;
        }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', additionalStyles);