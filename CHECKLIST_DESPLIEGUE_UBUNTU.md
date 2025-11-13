# ✅ Checklist de Despliegue en Ubuntu - Sistema de Patrimonio DRTC

## 📋 ANTES DE EMPEZAR - Preparación

### ☑️ Paso 0: Información que Necesitas Tener Lista

Antes de comenzar, asegúrate de tener esta información:

- [ ] **IP del servidor Ubuntu**: ___________________
- [ ] **Usuario SSH**: ___________________
- [ ] **Contraseña o clave SSH**: ___________________
- [ ] **Dominio**: ___________________ (ejemplo: patrimonio.drtcpuno.gob.pe)
- [ ] **Email para notificaciones**: ___________________
- [ ] **Claves de reCAPTCHA**:
  - [ ] Public Key: ___________________
  - [ ] Private Key: ___________________
  - [ ] Obtener en: https://www.google.com/recaptcha/admin
- [ ] **Configuración de Email SMTP**:
  - [ ] Servidor SMTP: ___________________ (ejemplo: smtp.gmail.com)
  - [ ] Puerto: ___________________ (ejemplo: 587)
  - [ ] Usuario: ___________________
  - [ ] Contraseña: ___________________
- [ ] **Código de seguridad** para eliminaciones permanentes: ___________________

### ☑️ Verificar DNS

- [ ] El dominio apunta a la IP del servidor
- [ ] Comando para verificar: `nslookup tu-dominio.com`
- [ ] Debe mostrar la IP de tu servidor

---

## 🚀 FASE 1: Conectarse al Servidor

### ☑️ Paso 1: Conectar por SSH

```bash
ssh usuario@ip-del-servidor
```

**Ejemplo**:
```bash
ssh admin@192.168.1.100
```

- [ ] Conexión exitosa
- [ ] Puedes ejecutar comandos

---

## 📦 FASE 2: Clonar el Repositorio

### ☑️ Paso 2: Clonar desde GitHub

```bash
git clone https://github.com/ajahuanex/sistema_patrimonio_drtc.git
cd sistema_patrimonio_drtc
```

- [ ] Repositorio clonado
- [ ] Estás dentro del directorio `sistema_patrimonio_drtc`

**Verificar**:
```bash
pwd
# Debe mostrar: /home/usuario/sistema_patrimonio_drtc
```

---

## 🔧 FASE 3: Preparar el Servidor (Solo Primera Vez)

### ☑️ Paso 3: Ejecutar Script de Preparación

```bash
chmod +x scripts/prepare-ubuntu-server.sh
sudo ./scripts/prepare-ubuntu-server.sh
```

**Este script instalará**:
- [ ] Docker Engine
- [ ] Docker Compose
- [ ] Configurará el firewall (UFW)
- [ ] Configurará límites del sistema

**Tiempo estimado**: 5-10 minutos

### ☑️ Paso 4: Cerrar Sesión y Reconectar

⚠️ **MUY IMPORTANTE**: Debes cerrar sesión y volver a conectarte

```bash
exit
```

Luego vuelve a conectar:
```bash
ssh usuario@ip-del-servidor
cd sistema_patrimonio_drtc
```

- [ ] Sesión cerrada
- [ ] Reconectado exitosamente
- [ ] De vuelta en el directorio del proyecto

**Verificar que Docker funciona**:
```bash
docker --version
docker-compose --version
```

- [ ] Docker instalado correctamente
- [ ] Docker Compose instalado correctamente

---

## ⚙️ FASE 4: Configurar Variables de Entorno

### ☑️ Paso 5: Ejecutar Script de Configuración

```bash
chmod +x scripts/configure-env.sh
./scripts/configure-env.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

**Ejemplo real**:
```bash
./scripts/configure-env.sh --domain patrimonio.drtcpuno.gob.pe --email admin@drtcpuno.gob.pe
```

### ☑️ Paso 6: Responder las Preguntas del Script

El script te pedirá:

1. **reCAPTCHA Public Key**:
   - [ ] Ingresado correctamente

2. **reCAPTCHA Private Key**:
   - [ ] Ingresado correctamente

3. **Servidor SMTP**:
   - [ ] Ingresado (ejemplo: smtp.gmail.com)

4. **Puerto SMTP**:
   - [ ] Ingresado (ejemplo: 587)

5. **Usuario SMTP**:
   - [ ] Ingresado

6. **Contraseña SMTP**:
   - [ ] Ingresada

7. **Código de eliminación permanente**:
   - [ ] Ingresado (mínimo 8 caracteres)

8. **Usuario administrador**:
   - [ ] Ingresado (default: admin)

9. **Contraseña administrador**:
   - [ ] Ingresada (mínimo 8 caracteres)

10. **Email administrador**:
    - [ ] Ingresado

### ☑️ Paso 7: Verificar Archivo .env.prod

```bash
ls -la .env.prod
```

- [ ] Archivo `.env.prod` creado
- [ ] Tiene permisos 600 (solo lectura para el usuario)

**Opcional - Ver contenido** (sin mostrar contraseñas):
```bash
cat .env.prod | grep -v PASSWORD | grep -v SECRET
```

---

## 🚀 FASE 5: Desplegar el Sistema

### ☑️ Paso 8: Ejecutar Script de Despliegue

```bash
chmod +x scripts/deploy-ubuntu.sh
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

**Ejemplo real**:
```bash
./scripts/deploy-ubuntu.sh --domain patrimonio.drtcpuno.gob.pe --email admin@drtcpuno.gob.pe
```

**⏱️ Tiempo estimado**: 10-15 minutos

### ☑️ Paso 9: Monitorear el Proceso

El script mostrará el progreso. Verifica que cada paso se complete:

- [ ] ✅ Validación de pre-requisitos
- [ ] ✅ Actualización del código fuente
- [ ] ✅ Carga de variables de entorno
- [ ] ✅ Construcción de imágenes Docker
- [ ] ✅ Inicio de servicios de base de datos
- [ ] ✅ Espera de disponibilidad de PostgreSQL
- [ ] ✅ Ejecución de migraciones
- [ ] ✅ Creación de superusuario
- [ ] ✅ Configuración de papelera de reciclaje
- [ ] ✅ Recolección de archivos estáticos
- [ ] ✅ Configuración de SSL/TLS
- [ ] ✅ Inicio de todos los servicios
- [ ] ✅ Health checks post-despliegue
- [ ] ✅ Configuración de backups automáticos

---

## ✔️ FASE 6: Verificar el Despliegue

### ☑️ Paso 10: Verificar Servicios Docker

```bash
docker-compose -f docker-compose.prod.yml ps
```

**Todos los servicios deben estar "Up"**:
- [ ] `db` (PostgreSQL) - Up
- [ ] `redis` - Up
- [ ] `web` (Django + Gunicorn) - Up
- [ ] `celery-worker` - Up
- [ ] `celery-beat` - Up
- [ ] `nginx` - Up

### ☑️ Paso 11: Verificar Logs

```bash
docker-compose -f docker-compose.prod.yml logs --tail=50
```

- [ ] No hay errores críticos en los logs
- [ ] Los servicios iniciaron correctamente

### ☑️ Paso 12: Verificar Acceso Web

Abre tu navegador y accede a:

1. **Página principal**:
   - [ ] URL: `https://tu-dominio.com`
   - [ ] Carga correctamente
   - [ ] Certificado SSL válido (candado verde)

2. **Panel de administración**:
   - [ ] URL: `https://tu-dominio.com/admin/`
   - [ ] Muestra la página de login
   - [ ] Puedes iniciar sesión con las credenciales configuradas

3. **Health check**:
   - [ ] URL: `https://tu-dominio.com/health/`
   - [ ] Muestra: `{"status": "healthy"}`

4. **Health check detallado**:
   - [ ] URL: `https://tu-dominio.com/health/detailed/`
   - [ ] Muestra estado de todos los servicios

### ☑️ Paso 13: Verificar SSL

```bash
echo | openssl s_client -connect tu-dominio.com:443 -servername tu-dominio.com 2>/dev/null | openssl x509 -noout -dates
```

- [ ] Muestra fechas de validez del certificado
- [ ] Certificado válido y no expirado

---

## 🎉 FASE 7: Configuración Post-Despliegue

### ☑️ Paso 14: Iniciar Sesión como Administrador

1. Ve a: `https://tu-dominio.com/admin/`
2. Inicia sesión con:
   - Usuario: (el que configuraste)
   - Contraseña: (la que configuraste)

- [ ] Inicio de sesión exitoso
- [ ] Puedes ver el panel de administración

### ☑️ Paso 15: Verificar Backups Automáticos

```bash
crontab -l | grep backup
```

- [ ] Muestra el cron job de backups
- [ ] Configurado para ejecutarse a las 3:00 AM

**Verificar directorios de backup**:
```bash
ls -la backups/
```

- [ ] Directorio `backups/db/` existe
- [ ] Directorio `backups/media/` existe

### ☑️ Paso 16: Crear Backup Manual de Prueba

```bash
./scripts/backup.sh
```

- [ ] Backup creado exitosamente
- [ ] Archivos en `backups/db/` y `backups/media/`

---

## 📊 FASE 8: Monitoreo y Mantenimiento

### ☑️ Comandos Útiles para Recordar

**Ver logs en tiempo real**:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

**Ver logs de un servicio específico**:
```bash
docker-compose -f docker-compose.prod.yml logs -f web
```

**Reiniciar todos los servicios**:
```bash
docker-compose -f docker-compose.prod.yml restart
```

**Reiniciar un servicio específico**:
```bash
docker-compose -f docker-compose.prod.yml restart web
```

**Ver uso de recursos**:
```bash
docker stats
```

**Ver espacio en disco**:
```bash
df -h
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### ❌ Problema: Docker no está instalado

**Solución**:
```bash
sudo ./scripts/prepare-ubuntu-server.sh
```

### ❌ Problema: Permission denied con Docker

**Solución**:
```bash
sudo usermod -aG docker $USER
exit
# Reconectar
```

### ❌ Problema: PostgreSQL no responde

**Solución**:
```bash
docker-compose -f docker-compose.prod.yml restart db
docker-compose -f docker-compose.prod.yml logs db
```

### ❌ Problema: SSL no se configura

**Verificar DNS**:
```bash
nslookup tu-dominio.com
```

**Verificar firewall**:
```bash
sudo ufw status
```

**Puertos 80 y 443 deben estar abiertos**

### ❌ Problema: Servicios no inician

**Ver logs**:
```bash
docker-compose -f docker-compose.prod.yml logs
```

**Reconstruir imágenes**:
```bash
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📝 NOTAS FINALES

### Información Importante

**URLs del Sistema**:
- Sistema: `https://tu-dominio.com`
- Admin: `https://tu-dominio.com/admin/`
- Health: `https://tu-dominio.com/health/`

**Ubicación de Logs**:
- Logs de despliegue: `/var/log/patrimonio-deploy.log`
- Logs de backups: `/var/log/patrimonio-backup.log`
- Logs de Docker: `docker-compose -f docker-compose.prod.yml logs`

**Backups**:
- Automáticos: Todos los días a las 3:00 AM
- Ubicación: `backups/db/` y `backups/media/`
- Manual: `./scripts/backup.sh`

**Actualizar el Sistema**:
```bash
cd sistema_patrimonio_drtc
git pull origin main
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

---

## ✅ CHECKLIST FINAL

- [ ] Servidor preparado e instalado
- [ ] Variables de entorno configuradas
- [ ] Sistema desplegado exitosamente
- [ ] Todos los servicios funcionando
- [ ] SSL configurado correctamente
- [ ] Acceso web verificado
- [ ] Panel de administración accesible
- [ ] Backups automáticos configurados
- [ ] Backup manual de prueba creado
- [ ] Documentación revisada

---

## 🎉 ¡DESPLIEGUE COMPLETADO!

Tu Sistema de Patrimonio DRTC está ahora funcionando en producción.

**Próximos pasos**:
1. Configurar usuarios adicionales
2. Importar datos iniciales
3. Configurar permisos de usuarios
4. Realizar pruebas de funcionalidad

**Soporte**:
- Documentación completa: `docs/DEPLOYMENT_UBUNTU.md`
- Guía rápida: `GUIA_DESPLIEGUE_RAPIDO.md`
- Logs del sistema: `/var/log/patrimonio-*.log`
