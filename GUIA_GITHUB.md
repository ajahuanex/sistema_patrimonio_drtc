# 🚀 Guía para Subir el Proyecto a GitHub

## ✅ Archivos Preparados

He preparado los siguientes archivos para GitHub:

- ✅ `.gitignore` - Actualizado con exclusiones apropiadas
- ✅ `README.md` - Documentación completa del proyecto
- ✅ `LICENSE` - Licencia MIT
- ✅ `CONTRIBUTING.md` - Guía de contribución

---

## 📋 Pasos para Subir a GitHub

### 1. Inicializar Git (si no está inicializado)

```bash
git init
```

### 2. Agregar Archivos al Staging

```bash
# Agregar todos los archivos
git add .

# O agregar archivos específicos
git add README.md LICENSE CONTRIBUTING.md .gitignore
git add apps/ templates/ static/ patrimonio/
git add docker-compose.yml Dockerfile requirements.txt
```

### 3. Hacer el Primer Commit

```bash
git commit -m "feat: initial commit - Sistema de Registro de Patrimonio DRTC Puno

- Sistema completo de gestión patrimonial
- Importación/exportación Excel
- Códigos QR y etiquetas Zebra
- Sistema de papelera de reciclaje
- API REST para móviles
- Dashboard con estadísticas dinámicas
- Documentación completa"
```

### 4. Crear Repositorio en GitHub

1. Ve a https://github.com
2. Haz clic en "New repository"
3. Nombre: `sistema-patrimonio-drtc-puno`
4. Descripción: "Sistema de Gestión de Patrimonio para DRTC Puno"
5. **NO** marques "Initialize with README" (ya tienes uno)
6. Haz clic en "Create repository"

### 5. Conectar con GitHub

```bash
# Agregar el repositorio remoto
git remote add origin https://github.com/TU_USUARIO/sistema-patrimonio-drtc-puno.git

# Verificar
git remote -v
```

### 6. Subir el Código

```bash
# Renombrar rama a main (si es necesario)
git branch -M main

# Push inicial
git push -u origin main
```

---

## 🔐 Configurar Secrets (Importante)

**NO subas archivos con contraseñas o secrets**. Usa GitHub Secrets:

### Archivos que NO deben subirse:

- ❌ `.env` con contraseñas reales
- ❌ `db.sqlite3` con datos reales
- ❌ Archivos en `media/` con información sensible
- ❌ Backups de base de datos (*.sql)

### Crear archivo .env.example

```bash
# Crear plantilla sin datos sensibles
cat > .env.example << 'EOF'
# Base de datos
DB_PASSWORD=tu_password_aqui
DATABASE_URL=postgresql://user:password@db:5432/dbname

# Django
SECRET_KEY=tu_secret_key_aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com

# Redis
REDIS_URL=redis://redis:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

# URLs
BASE_URL=https://tu-dominio.com
EOF

# Agregar al repositorio
git add .env.example
git commit -m "docs: add .env.example template"
git push
```

---

## 📝 Verificar antes de Subir

### Checklist de Seguridad

```bash
# Verificar que .env no esté en el repo
git ls-files | grep .env

# Si aparece .env, eliminarlo del tracking
git rm --cached .env
git commit -m "chore: remove .env from tracking"

# Verificar archivos que se subirán
git status

# Ver qué archivos están siendo ignorados
git status --ignored
```

### Archivos que DEBEN subirse:

- ✅ Código fuente (apps/, templates/, static/)
- ✅ Configuración (settings.py, urls.py)
- ✅ Docker (Dockerfile, docker-compose.yml)
- ✅ Dependencias (requirements.txt, package.json)
- ✅ Documentación (README.md, docs/)
- ✅ Tests (tests/)
- ✅ Scripts (scripts/)

### Archivos que NO deben subirse:

- ❌ `.env` (con secrets reales)
- ❌ `db.sqlite3` (base de datos)
- ❌ `media/` (archivos subidos)
- ❌ `*.pyc`, `__pycache__/`
- ❌ `node_modules/`
- ❌ `.vscode/`, `.idea/`
- ❌ Backups (*.sql, *.dump)

---

## 🏷️ Crear Tags y Releases

### Crear un Tag

```bash
# Tag para la versión inicial
git tag -a v1.0.0 -m "Release v1.0.0 - Sistema Completo

Características:
- Gestión de bienes patrimoniales
- Importación/exportación Excel
- Códigos QR y etiquetas
- Sistema de papelera de reciclaje
- Dashboard con estadísticas
- API REST móvil"

# Subir el tag
git push origin v1.0.0
```

### Crear Release en GitHub

1. Ve a tu repositorio en GitHub
2. Haz clic en "Releases"
3. Haz clic en "Create a new release"
4. Selecciona el tag `v1.0.0`
5. Título: "v1.0.0 - Sistema Completo"
6. Descripción: Copia del mensaje del tag
7. Haz clic en "Publish release"

---

## 📊 Configurar GitHub Pages (Opcional)

Si quieres publicar la documentación:

```bash
# Crear rama gh-pages
git checkout -b gh-pages

# Copiar documentación
mkdir -p docs
cp README.md docs/index.md
cp CONTRIBUTING.md docs/
cp docs/*.md docs/

# Commit y push
git add docs/
git commit -m "docs: setup GitHub Pages"
git push origin gh-pages

# Volver a main
git checkout main
```

Luego en GitHub:
1. Settings > Pages
2. Source: Deploy from branch
3. Branch: gh-pages / docs
4. Save

---

## 🔄 Workflow de Desarrollo

### Trabajar en una Nueva Feature

```bash
# Actualizar main
git checkout main
git pull origin main

# Crear rama para feature
git checkout -b feature/nueva-funcionalidad

# Hacer cambios y commits
git add .
git commit -m "feat: descripción del cambio"

# Push de la rama
git push origin feature/nueva-funcionalidad

# Crear Pull Request en GitHub
```

### Actualizar desde Main

```bash
# En tu rama de feature
git checkout feature/mi-feature

# Traer cambios de main
git fetch origin
git rebase origin/main

# O merge si prefieres
git merge origin/main

# Resolver conflictos si hay
# Luego push
git push origin feature/mi-feature --force-with-lease
```

---

## 🛡️ Proteger la Rama Main

En GitHub, configura protecciones:

1. Settings > Branches
2. Add rule para `main`
3. Marca:
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
   - ✅ Include administrators

---

## 📦 GitHub Actions (CI/CD)

Crea `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python manage.py test
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
```

---

## 📞 Comandos Útiles

```bash
# Ver estado
git status

# Ver historial
git log --oneline --graph --all

# Ver diferencias
git diff

# Ver ramas
git branch -a

# Cambiar de rama
git checkout nombre-rama

# Crear y cambiar a nueva rama
git checkout -b nueva-rama

# Eliminar rama local
git branch -d nombre-rama

# Eliminar rama remota
git push origin --delete nombre-rama

# Deshacer último commit (mantener cambios)
git reset --soft HEAD~1

# Deshacer cambios en archivo
git checkout -- archivo.py

# Ver archivos ignorados
git status --ignored

# Limpiar archivos no trackeados
git clean -fd
```

---

## ✅ Checklist Final

Antes de hacer público el repositorio:

- [ ] `.gitignore` configurado correctamente
- [ ] No hay archivos con contraseñas o secrets
- [ ] README.md completo y actualizado
- [ ] LICENSE agregado
- [ ] CONTRIBUTING.md creado
- [ ] .env.example como plantilla
- [ ] Documentación en docs/ actualizada
- [ ] Tests funcionando
- [ ] Docker compose funcional
- [ ] Scripts de deployment probados

---

## 🎉 ¡Listo!

Tu proyecto está listo para GitHub. Comandos finales:

```bash
# Verificar todo
git status

# Último commit si hay cambios
git add .
git commit -m "docs: prepare for GitHub"

# Push final
git push origin main

# Crear tag de release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## 📚 Recursos

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)

---

**Fecha**: 11/11/2025  
**Versión**: 1.0.0  
**Estado**: ✅ LISTO PARA GITHUB
