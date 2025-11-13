# 🚀 Comandos Exactos para Despliegue en Ubuntu

## 📌 Copia y Pega Estos Comandos en Orden

---

## PASO 1: Conectar al Servidor

```bash
# Reemplaza con tu información
ssh usuario@ip-del-servidor

# Ejemplo:
# ssh admin@192.168.1.100
```

---

## PASO 2: Clonar Repositorio

```bash
git clone https://github.com/ajahuanex/sistema_patrimonio_drtc.git
cd sistema_patrimonio_drtc
```

---

## PASO 3: Preparar Servidor (Solo Primera Vez)

```bash
chmod +x scripts/prepare-ubuntu-server.sh
sudo ./scripts/prepare-ubuntu-server.sh
```

⏱️ **Espera 5-10 minutos**

---

## PASO 4: Cerrar Sesión y Reconectar

```bash
exit
```

Luego vuelve a conectar:

```bash
# Reemplaza con tu información
ssh usuario@ip-del-servidor
cd sistema_patrimonio_drtc
```

Verifica que Docker funciona:

```bash
docker --version
docker-compose --version
```

---

## PASO 5: Configurar Variables de Entorno

```bash
chmod +x scripts/configure-env.sh

# Reemplaza con tu dominio y email
./scripts/configure-env.sh --domain tu-dominio.com --email tu-email@ejemplo.com

# Ejemplo real:
# ./scripts/configure-env.sh --domain patrimonio.drtcpuno.gob.pe --email admin@drtcpuno.gob.pe
```

**El script te pedirá**:
1. reCAPTCHA Public Key
2. reCAPTCHA Private Key
3. Servidor SMTP (ejemplo: smtp.gmail.com)
4. Puerto SMTP (ejemplo: 587)
5. Usuario SMTP
6. Contraseña SMTP
7. Código de eliminación permanente
8. Usuario administrador
9. Contraseña administrador
10. Email administrador

---

## PASO 6: Desplegar el Sistema

```bash
chmod +x scripts/deploy-ubuntu.sh

# Reemplaza con tu dominio y email
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com

# Ejemplo real:
# ./scripts/deploy-ubuntu.sh --domain patrimonio.drtcpuno.gob.pe --email admin@drtcpuno.gob.pe
```

⏱️ **Espera 10-15 minutos**

---

## PASO 7: Verificar Servicios

```bash
docker-compose -f docker-compose.prod.yml ps
```

**Todos deben estar "Up"**:
- db
- redis
- web
- celery-worker
- celery-beat
- nginx

---

## PASO 8: Ver Logs

```bash
# Ver últimos 50 logs
docker-compose -f docker-compose.prod.yml logs --tail=50

# Ver logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f

# Ver logs de un servicio específico
docker-compose -f docker-compose.prod.yml logs -f web
```

---

## PASO 9: Verificar SSL

```bash
# Reemplaza con tu dominio
echo | openssl s_client -connect tu-dominio.com:443 -servername tu-dominio.com 2>/dev/null | openssl x509 -noout -dates
```

---

## PASO 10: Verificar Backups

```bash
# Ver cron job de backups
crontab -l | grep backup

# Ver directorios de backup
ls -la backups/

# Crear backup manual de prueba
./scripts/backup.sh
```

---

## 🎉 ¡LISTO!

Ahora accede desde tu navegador:

- **Sistema**: https://tu-dominio.com
- **Admin**: https://tu-dominio.com/admin/
- **Health**: https://tu-dominio.com/health/

---

## 📊 COMANDOS ÚTILES

### Ver Estado de Servicios
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Reiniciar Todos los Servicios
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Reiniciar un Servicio Específico
```bash
docker-compose -f docker-compose.prod.yml restart web
```

### Ver Uso de Recursos
```bash
docker stats
```

### Ver Espacio en Disco
```bash
df -h
```

### Acceder a la Base de Datos
```bash
docker-compose -f docker-compose.prod.yml exec db psql -U patrimonio -d patrimonio
```

### Acceder a Shell de Django
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
```

### Crear Superusuario Adicional
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## 🔄 ACTUALIZAR EL SISTEMA

```bash
cd sistema_patrimonio_drtc
git pull origin main
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Docker no instalado
```bash
sudo ./scripts/prepare-ubuntu-server.sh
```

### Permission denied con Docker
```bash
sudo usermod -aG docker $USER
exit
# Reconectar
```

### PostgreSQL no responde
```bash
docker-compose -f docker-compose.prod.yml restart db
docker-compose -f docker-compose.prod.yml logs db
```

### Ver todos los logs para debugging
```bash
docker-compose -f docker-compose.prod.yml logs
```

### Reconstruir todo desde cero
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
./scripts/deploy-ubuntu.sh --domain tu-dominio.com --email tu-email@ejemplo.com
```

---

## 📝 INFORMACIÓN IMPORTANTE

**Ubicación de Logs**:
- `/var/log/patrimonio-deploy.log` - Logs de despliegue
- `/var/log/patrimonio-backup.log` - Logs de backups

**Backups Automáticos**:
- Se ejecutan todos los días a las 3:00 AM
- Ubicación: `backups/db/` y `backups/media/`

**Archivos de Configuración**:
- `.env.prod` - Variables de entorno (NO compartir)
- `docker-compose.prod.yml` - Configuración de Docker

---

## ✅ VERIFICACIÓN RÁPIDA

```bash
# Todo en un comando
echo "=== ESTADO DE SERVICIOS ===" && \
docker-compose -f docker-compose.prod.yml ps && \
echo "" && \
echo "=== ESPACIO EN DISCO ===" && \
df -h | grep -E "Filesystem|/$" && \
echo "" && \
echo "=== BACKUPS ===" && \
ls -lh backups/db/ | tail -5 && \
echo "" && \
echo "=== HEALTH CHECK ===" && \
curl -s https://tu-dominio.com/health/ | python3 -m json.tool
```

Reemplaza `tu-dominio.com` con tu dominio real.
