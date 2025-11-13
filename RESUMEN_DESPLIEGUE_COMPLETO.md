# 📋 Resumen: Despliegue Completo

## 🎯 Objetivo
Subir cambios a GitHub y desplegarlos en servidor Ubuntu.

---

## ⚡ Comandos Rápidos

### En Windows (Tu PC):

```bash
# Opción 1: Usar el script
subir_a_git.bat

# Opción 2: Manual
git add .
git commit -m "Fix: Variables de entorno Docker"
git push origin main
```

### En Ubuntu (Servidor):

```bash
# Conectar al servidor
ssh usuario@IP_SERVIDOR

# Ir al proyecto
cd /ruta/del/proyecto

# Traer cambios
git pull origin main

# Desplegar
chmod +x desplegar_servidor.sh
./desplegar_servidor.sh
```

---

## 📝 Checklist Completo

### Antes de Empezar

- [ ] Tienes acceso SSH al servidor Ubuntu
- [ ] El proyecto ya está clonado en Ubuntu
- [ ] Docker y Docker Compose están instalados en Ubuntu
- [ ] Tienes las credenciales de GitHub configuradas

### En Windows

- [ ] Verificar cambios: `git status`
- [ ] Agregar archivos: `git add .`
- [ ] Hacer commit: `git commit -m "mensaje"`
- [ ] Subir a GitHub: `git push origin main`

### En Ubuntu

- [ ] Conectar al servidor: `ssh usuario@IP`
- [ ] Ir al directorio: `cd /ruta/proyecto`
- [ ] Traer cambios: `git pull origin main`
- [ ] Crear `.env.prod` (si no existe)
- [ ] Dar permisos: `chmod +x desplegar_servidor.sh`
- [ ] Ejecutar script: `./desplegar_servidor.sh`
- [ ] Verificar logs: `docker compose logs`
- [ ] Ejecutar migraciones: `docker compose exec web python manage.py migrate`
- [ ] Crear superusuario (primera vez): `docker compose exec web python manage.py createsuperuser`
- [ ] Acceder a la app: `http://IP_SERVIDOR`

---

## 🔧 Archivos Importantes

### Nuevos archivos creados:

1. **desplegar_servidor.sh** - Script de despliegue automático
2. **FIX_DOCKER_ENV_VARIABLES.md** - Documentación del problema y solución
3. **COMANDOS_MANUALES_DESPLIEGUE.md** - Comandos paso a paso
4. **FLUJO_COMPLETO_GIT_A_UBUNTU.md** - Guía completa del flujo
5. **subir_a_git.bat** - Script para Windows (subir a Git)
6. **RESUMEN_DESPLIEGUE_COMPLETO.md** - Este archivo

### Archivos que debes crear en Ubuntu:

1. **.env.prod** - Variables de entorno (NO subir a Git)

---

## 🚨 Importante

### NO subir a GitHub:
- `.env.prod`
- `.env`
- Archivos con contraseñas
- Archivos de base de datos

### Verificar .gitignore:
```
.env
.env.prod
.env.local
*.pyc
__pycache__/
db.sqlite3
media/
staticfiles/
```

---

## 🎬 Ejemplo Completo

### Sesión en Windows:

```bash
C:\proyecto> git status
C:\proyecto> git add .
C:\proyecto> git commit -m "Fix: Docker env variables"
C:\proyecto> git push origin main
```

### Sesión en Ubuntu:

```bash
usuario@ubuntu:~$ ssh usuario@192.168.1.100
usuario@servidor:~$ cd /home/usuario/sistema_patrimonio_drtc
usuario@servidor:~/sistema_patrimonio_drtc$ git pull origin main
usuario@servidor:~/sistema_patrimonio_drtc$ chmod +x desplegar_servidor.sh
usuario@servidor:~/sistema_patrimonio_drtc$ ./desplegar_servidor.sh

🚀 Desplegando Sistema de Patrimonio en Ubuntu
==============================================
📋 Cargando variables de entorno...
✅ Variables cargadas
🛑 Deteniendo contenedores existentes...
🧹 Limpiando sistema Docker...
🔍 Verificando variables antes de iniciar...
✅ Variables verificadas correctamente
🚀 Iniciando servicios...
⏳ Esperando que los servicios estén listos (60 segundos)...
📊 Estado de los contenedores:
  ✅ PostgreSQL está listo
  ✅ Redis está listo
✅ Despliegue completado!
```

---

## 🔍 Verificación Final

### Verificar que todo funciona:

```bash
# Ver contenedores
docker compose -f docker-compose.simple.yml ps

# Probar PostgreSQL
docker compose -f docker-compose.simple.yml exec db pg_isready -U patrimonio_user -d patrimonio_db

# Probar Redis
docker compose -f docker-compose.simple.yml exec redis redis-cli -a tu_password ping

# Ver logs
docker compose -f docker-compose.simple.yml logs -f
```

### Acceder a la aplicación:

Abre en el navegador:
```
http://IP_DEL_SERVIDOR
```

---

## 📞 Soporte

Si algo falla:

1. **Ver logs detallados:**
   ```bash
   docker compose -f docker-compose.simple.yml logs --tail=100
   ```

2. **Verificar variables:**
   ```bash
   cat .env.prod
   docker compose -f docker-compose.simple.yml exec db env | grep POSTGRES
   ```

3. **Limpiar y reiniciar:**
   ```bash
   docker compose -f docker-compose.simple.yml down -v
   docker system prune -af
   ./desplegar_servidor.sh
   ```

---

## ✅ Próximos Pasos

Después del despliegue exitoso:

1. Configurar dominio
2. Instalar SSL/HTTPS
3. Configurar backups
4. Configurar monitoreo
5. Documentar credenciales de acceso

---

## 🎉 ¡Listo!

Tu aplicación debería estar funcionando en:
```
http://IP_DEL_SERVIDOR
```

Para actualizaciones futuras, solo repite:
1. `git push` en Windows
2. `git pull && ./desplegar_servidor.sh` en Ubuntu
