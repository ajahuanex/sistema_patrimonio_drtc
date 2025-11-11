# 🚀 Guía para Subir el Proyecto a GitHub

## 📋 Pasos para Subir a GitHub

### Paso 1: Crear Repositorio en GitHub

1. Ve a https://github.com
2. Haz clic en el botón **"New"** o **"+"** → **"New repository"**
3. Completa los datos:
   - **Repository name**: `sistema-patrimonio-drtc-puno`
   - **Description**: `Sistema de Gestión de Patrimonio para DRTC Puno`
   - **Visibility**: 
     - ✅ **Public** (si quieres que sea público)
     - ✅ **Private** (si quieres que sea privado)
   - ❌ **NO marques** "Initialize this repository with a README"
   - ❌ **NO agregues** .gitignore ni license (ya los tenemos)
4. Haz clic en **"Create repository"**

---

### Paso 2: Preparar el Repositorio Local

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
# Inicializar git (si no está inicializado)
git init

# Agregar todos los archivos
git add .

# Hacer el primer commit
git commit -m "feat: initial commit - Sistema de Patrimonio DRTC Puno

- Sistema completo de gestión de patrimonio
- Módulos: Bienes, Catálogo, Oficinas, Reportes
- Sistema de papelera de reciclaje
- Estadísticas dinámicas en dashboard
- Importación/exportación Excel
- Códigos QR y etiquetas
- API REST para móvil
- Docker y Docker Compose
- Documentación completa"
```

---

### Paso 3: Conectar con GitHub

Copia la URL de tu repositorio de GitHub (aparece después de crearlo).

Luego ejecuta:

```bash
# Agregar el repositorio remoto
git remote add origin https://github.com/TU_USUARIO/sistema-patrimonio-drtc-puno.git

# Verificar que se agregó correctamente
git remote -v
```

**Deberías ver algo como:**
```
origin  https://github.com/TU_USUARIO/sistema-patrimonio-drtc-puno.git (fetch)
origin  https://github.com/TU_USUARIO/sistema-patrimonio-drtc-puno.git (push)
```

---

### Paso 4: Subir el Código

```bash
# Cambiar el nombre de la rama a main (si es necesario)
git branch -M main

# Subir el código a GitHub
git push -u origin main
```

**Si te pide autenticación:**

#### Opción A: Con Token de Acceso Personal (Recomendado)

1. Ve a GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Clic en "Generate new token (classic)"
3. Dale un nombre: "Sistema Patrimonio"
4. Selecciona permisos: `repo` (todos)
5. Clic en "Generate token"
6. **COPIA EL TOKEN** (solo se muestra una vez)
7. Cuando te pida password, pega el token

#### Opción B: Con SSH

```bash
# Generar clave SSH (si no tienes)
ssh-keygen -t ed25519 -C "tu_email@example.com"

# Copiar la clave pública
cat ~/.ssh/id_ed25519.pub

# Agregar la clave a GitHub:
# GitHub → Settings → SSH and GPG keys → New SSH key

# Cambiar la URL del remote a SSH
git remote set-url origin git@github.com:TU_USUARIO/sistema-patrimonio-drtc-puno.git

# Subir
git push -u origin main
```

---

### Paso 5: Verificar en GitHub

1. Ve a tu repositorio en GitHub
2. Deberías ver todos los archivos
3. El README.md se mostrará automáticamente

---

## 🔒 Archivos Sensibles (IMPORTANTE)

### ⚠️ ANTES de subir, verifica que estos archivos NO estén en el repositorio:

```bash
# Verificar qué archivos se van a subir
git status

# Verificar que estos archivos NO aparezcan:
# - .env
# - .env.local
# - .env.production
# - *.sql
# - backup_*.sql
# - secrets/
```

### Si accidentalmente subiste archivos sensibles:

```bash
# Eliminar del repositorio (pero mantener local)
git rm --cached .env
git rm --cached *.sql

# Commit y push
git commit -m "chore: remove sensitive files"
git push
```

---

## 📝 Crear .env.example

Crea un archivo de ejemplo sin datos sensibles:

```bash
# Crear .env.example
cat > .env.example << 'EOF'
# Base de datos
DB_PASSWORD=tu_password_aqui
DATABASE_URL=postgresql://user:password@db:5432/patrimonio_db

# Django
SECRET_KEY=tu_secret_key_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis
REDIS_URL=redis://redis:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

# URLs
BASE_URL=http://localhost:8000
EOF

# Agregar y subir
git add .env.example
git commit -m "docs: add .env.example file"
git push
```

---

## 🌿 Crear Ramas

### Rama de Desarrollo

```bash
# Crear rama develop
git checkout -b develop
git push -u origin develop

# Volver a main
git checkout main
```

### Proteger Rama Main

En GitHub:
1. Ve a Settings → Branches
2. Add rule
3. Branch name pattern: `main`
4. Marca:
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass before merging
5. Save changes

---

## 📊 Configurar GitHub Pages (Opcional)

Si quieres publicar la documentación:

1. Ve a Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` → `/docs`
4. Save

---

## 🏷️ Crear Release

### Primera Release

```bash
# Crear tag
git tag -a v1.0.0 -m "Release v1.0.0 - Sistema Patrimonio DRTC Puno

Características principales:
- Gestión completa de bienes patrimoniales
- Sistema de papelera de reciclaje
- Estadísticas dinámicas
- Importación/exportación Excel
- Códigos QR y etiquetas
- API REST móvil
- Docker deployment"

# Subir tag
git push origin v1.0.0
```

En GitHub:
1. Ve a Releases → Create a new release
2. Choose a tag: v1.0.0
3. Release title: `v1.0.0 - Primera Versión Estable`
4. Describe this release: (copia la descripción del tag)
5. Publish release

---

## 📋 Checklist Final

Antes de hacer público el repositorio:

- [ ] Archivo .gitignore configurado
- [ ] No hay archivos sensibles (.env, *.sql, secrets/)
- [ ] README.md completo y actualizado
- [ ] LICENSE agregado
- [ ] CONTRIBUTING.md agregado
- [ ] .env.example creado
- [ ] Código subido a GitHub
- [ ] Repositorio verificado en GitHub
- [ ] Documentación accesible
- [ ] Release v1.0.0 creada

---

## 🔄 Comandos Útiles

### Ver estado del repositorio
```bash
git status
git log --oneline
git remote -v
```

### Actualizar desde GitHub
```bash
git pull origin main
```

### Crear nueva rama
```bash
git checkout -b feature/nueva-funcionalidad
```

### Subir cambios
```bash
git add .
git commit -m "feat: descripción del cambio"
git push
```

### Ver diferencias
```bash
git diff
git diff --staged
```

---

## 🆘 Solución de Problemas

### Error: "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/TU_USUARIO/repo.git
```

### Error: "failed to push some refs"
```bash
# Traer cambios primero
git pull origin main --rebase
git push origin main
```

### Error: "Permission denied (publickey)"
```bash
# Verificar SSH
ssh -T git@github.com

# Si falla, usar HTTPS en lugar de SSH
git remote set-url origin https://github.com/TU_USUARIO/repo.git
```

### Deshacer último commit (sin perder cambios)
```bash
git reset --soft HEAD~1
```

### Deshacer cambios en un archivo
```bash
git checkout -- archivo.py
```

---

## 📞 Recursos

- **Documentación Git**: https://git-scm.com/doc
- **GitHub Docs**: https://docs.github.com
- **Git Cheat Sheet**: https://education.github.com/git-cheat-sheet-education.pdf

---

## ✅ ¡Listo!

Tu proyecto ahora está en GitHub. Puedes compartir la URL:

```
https://github.com/TU_USUARIO/sistema-patrimonio-drtc-puno
```

---

**Fecha**: 11/11/2025  
**Versión**: 1.0.0  
**Estado**: ✅ LISTO PARA GITHUB
