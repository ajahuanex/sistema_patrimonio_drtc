# 🔍 Verificación de Puertos - EJECUTAR ANTES DE DESPLEGAR

## ⚠️ MUY IMPORTANTE
Debes verificar que los puertos estén libres ANTES de iniciar Docker.

## 📊 Puertos que Necesita el Sistema

- **Puerto 80** (HTTP) - Nginx
- **Puerto 5432** (PostgreSQL) - Solo interno Docker
- **Puerto 6379** (Redis) - Solo interno Docker
- **Puerto 8000** (Django) - Solo interno Docker

Solo el puerto 80 se expone al exterior.

## ✅ Comando de Verificación Completa

```bash
echo "=== VERIFICANDO PUERTOS ==="
echo ""
echo "Puerto 80 (HTTP/Nginx):"
sudo lsof -i :80
echo ""
echo "Puerto 5432 (PostgreSQL):"
sudo lsof -i :5432
echo ""
echo "Puerto 6379 (Redis):"
sudo lsof -i :6379
echo ""
echo "Puerto 8000 (Django):"
sudo lsof -i :8000
```

## 🔴 Si Algún Puerto Está Ocupado

### Puerto 80 Ocupado (Nginx/Apache)
```bash
# Ver qué lo está usando
sudo lsof -i :80

# Detener nginx
sudo systemctl stop nginx
sudo systemctl disable nginx

# O detener apache
sudo systemctl stop apache2
sudo systemctl disable apache2

# Verificar que esté libre
sudo lsof -i :80
# No debe mostrar nada
```

### Puerto 5432 Ocupado (PostgreSQL)
```bash
# Detener PostgreSQL del sistema
sudo systemctl stop postgresql
sudo systemctl disable postgresql

# Verificar
sudo lsof -i :5432
```

### Puerto 6379 Ocupado (Redis)
```bash
# Detener Redis del sistema
sudo systemctl stop redis
sudo systemctl stop redis-server
sudo systemctl disable redis

# Verificar
sudo lsof -i :6379
```

### Puerto 8000 Ocupado
```bash
# Ver qué proceso lo usa
sudo lsof -i :8000

# Matar el proceso (reemplaza PID con el número que muestra)
sudo kill -9 PID
```

## ✅ Verificación Rápida (Un Solo Comando)

```bash
#!/bin/bash
echo "=== VERIFICACIÓN DE PUERTOS ==="
PUERTOS_OCUPADOS=0

for puerto in 80 5432 6379 8000; do
    if sudo lsof -i :$puerto > /dev/null 2>&1; then
        echo "❌ Puerto $puerto OCUPADO"
        sudo lsof -i :$puerto | grep LISTEN
        PUERTOS_OCUPADOS=$((PUERTOS_OCUPADOS + 1))
    else
        echo "✅ Puerto $puerto LIBRE"
    fi
done

echo ""
if [ $PUERTOS_OCUPADOS -eq 0 ]; then
    echo "✅ TODOS LOS PUERTOS ESTÁN LIBRES"
    echo "✅ PUEDES PROCEDER CON EL DESPLIEGUE"
else
    echo "❌ HAY $PUERTOS_OCUPADOS PUERTO(S) OCUPADO(S)"
    echo "❌ DEBES LIBERAR LOS PUERTOS ANTES DE CONTINUAR"
fi
```

## 🚀 Después de Liberar los Puertos

Una vez que todos los puertos estén libres, procede con:

```bash
# Continuar con el despliegue
docker compose -f docker-compose.simple.yml build
docker compose -f docker-compose.simple.yml up -d db redis
# ... resto de comandos
```

## 💡 Nota sobre Docker

Los puertos 5432, 6379 y 8000 son internos de Docker y normalmente no causan conflictos, pero es mejor verificar.

El puerto 80 es el CRÍTICO porque se expone al exterior y es donde Cloudflare/proxy se conectará.
