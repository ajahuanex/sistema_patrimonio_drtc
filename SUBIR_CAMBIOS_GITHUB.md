# 🚀 Subir Cambios a GitHub

## Paso 1: Preparar Cambios

```bash
# Ver qué archivos cambiaron
git status

# Agregar todos los cambios
git add .

# O agregar archivos específicos
git add verificar_puertos.sh docker-compose.simple.yml nginx/nginx.simple.conf
```

## Paso 2: Hacer Commit

```bash
git commit -m "feat: agregar configuración de despliegue con Docker Compose

- Agregar docker-compose.simple.yml para despliegue simplificado
- Agregar nginx/nginx.simple.conf con configuración Nginx
- Agregar verificar_puertos.sh para verificación de puertos
- Actualizar documentación de despliegue
- Usar 'docker compose' (sin guion) en scripts"
```

## Paso 3: Subir a GitHub

```bash
# Subir cambios a la rama actual
git push origin main

# O si tu rama se llama master
git push origin master
```

## Paso 4: Verificar en GitHub

Abre tu repositorio en GitHub y verifica que los cambios estén ahí.

---

## 📥 Traer Cambios al Servidor Ubuntu

### En el Servidor Ubuntu:

```bash
# 1. Clonar el repositorio (primera vez)
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd TU_REPO

# O si ya existe, actualizar
cd /ruta/a/tu/proyecto
git pull origin main
```

### Luego Desplegar:

```bash
# 1. Verificar puertos
chmod +x verificar_puertos.sh
./verificar_puertos.sh

# 2. Crear .env.prod (copiar de .env.example y editar)
cp .env.example .env.prod
nano .env.prod

# 3. Desplegar
docker compose -f docker-compose.simple.yml up -d

# 4. Ver logs
docker compose -f docker-compose.simple.yml logs -f
```

---

## ⚡ Comandos Rápidos

```bash
# Ver estado de Git
git status

# Ver cambios
git diff

# Ver historial
git log --oneline

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Actualizar desde GitHub
git pull
```

## 🔄 Flujo Completo

```bash
# En tu máquina local (Windows)
git add .
git commit -m "tu mensaje"
git push origin main

# En el servidor Ubuntu
cd /ruta/proyecto
git pull origin main
docker compose -f docker-compose.simple.yml up -d --build
```
