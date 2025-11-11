# ⚡ Pasos Rápidos para Subir a GitHub

## 🚀 En 5 Minutos

### 1️⃣ Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre: `sistema-patrimonio-drtc-puno`
3. Descripción: `Sistema de Gestión de Patrimonio para DRTC Puno`
4. Privado o Público (tú eliges)
5. **NO marques** "Initialize with README"
6. Clic en "Create repository"

---

### 2️⃣ Ejecutar Comandos

Abre terminal en la carpeta del proyecto:

```bash
# 1. Inicializar git
git init

# 2. Agregar archivos
git add .

# 3. Primer commit
git commit -m "feat: initial commit - Sistema Patrimonio DRTC Puno"

# 4. Conectar con GitHub (reemplaza TU_USUARIO)
git remote add origin https://github.com/TU_USUARIO/sistema-patrimonio-drtc-puno.git

# 5. Cambiar a rama main
git branch -M main

# 6. Subir código
git push -u origin main
```

---

### 3️⃣ Autenticación

Si te pide usuario y contraseña:

**Opción A: Token (Recomendado)**
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Selecciona: `repo` (todos los permisos)
4. Copia el token
5. Úsalo como contraseña

**Opción B: SSH**
```bash
# Generar clave
ssh-keygen -t ed25519 -C "tu_email@example.com"

# Copiar clave pública
cat ~/.ssh/id_ed25519.pub

# Agregar en GitHub → Settings → SSH keys

# Cambiar URL
git remote set-url origin git@github.com:TU_USUARIO/sistema-patrimonio-drtc-puno.git

# Subir
git push -u origin main
```

---

## ✅ ¡Listo!

Tu código está en GitHub: `https://github.com/TU_USUARIO/sistema-patrimonio-drtc-puno`

---

## 🔒 Antes de Subir (IMPORTANTE)

Verifica que NO estés subiendo archivos sensibles:

```bash
# Ver qué se va a subir
git status

# Verificar que NO aparezcan:
# - .env
# - *.sql
# - secrets/
```

Si aparecen, agrégalos al `.gitignore`:

```bash
echo ".env" >> .gitignore
echo "*.sql" >> .gitignore
git add .gitignore
git commit -m "chore: update gitignore"
```

---

## 📝 Crear .env.example

```bash
# Copiar .env sin datos sensibles
cp .env .env.example

# Editar .env.example y reemplazar valores reales con placeholders
# Ejemplo:
# DB_PASSWORD=tu_password_aqui
# SECRET_KEY=tu_secret_key_aqui

# Agregar y subir
git add .env.example
git commit -m "docs: add .env.example"
git push
```

---

## 🔄 Comandos Diarios

```bash
# Ver cambios
git status

# Agregar cambios
git add .

# Commit
git commit -m "descripción del cambio"

# Subir
git push

# Bajar cambios
git pull
```

---

## 🆘 Problemas Comunes

### "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/TU_USUARIO/repo.git
```

### "failed to push"
```bash
git pull origin main --rebase
git push origin main
```

### "Permission denied"
```bash
# Usar HTTPS en lugar de SSH
git remote set-url origin https://github.com/TU_USUARIO/repo.git
```

---

## 📚 Documentación Completa

Para más detalles, lee: **`GUIA_SUBIR_A_GITHUB.md`**

---

**Tiempo estimado**: 5-10 minutos  
**Dificultad**: Fácil  
**Estado**: ✅ LISTO PARA USAR
