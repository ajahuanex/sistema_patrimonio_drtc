# 🔐 Crear Usuario Administrador

## Ejecuta este comando en tu terminal:

```cmd
docker-compose exec web python manage.py createsuperuser
```

## 📝 Datos que debes ingresar:

### 1. Username (Nombre de usuario)
Ejemplo: `admin`

### 2. Email address
Ejemplo: `admin@drtc.gob.pe`

### 3. Password
**Crea una contraseña segura**

Recomendaciones:
- Mínimo 8 caracteres
- Combinar mayúsculas y minúsculas
- Incluir números
- Incluir caracteres especiales

Ejemplo de contraseña segura: `Admin2025!DRTC`

### 4. Password (again)
Repite la misma contraseña para confirmar

## ✅ Después de crear el usuario:

Podrás acceder a:

- **Panel de Administración**: http://localhost:8000/admin
- **Aplicación Web**: http://localhost:8000

Con el usuario y contraseña que acabas de crear.

## 🚀 ¡Listo!

Una vez creado el usuario, el sistema estará completamente funcional.
