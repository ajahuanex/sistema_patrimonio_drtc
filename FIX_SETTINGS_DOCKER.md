# ✅ Fix: Configuración de Settings en Docker

## Problema
El Docker estaba buscando `patrimonio.settings.production` pero el proyecto usa `patrimonio.settings`

## Solución Aplicada

### Archivos Modificados:

1. **docker-compose.simple.yml**
   - Cambiado: `DJANGO_SETTINGS_MODULE=patrimonio.settings.production`
   - A: `DJANGO_SETTINGS_MODULE=patrimonio.settings`

2. **Dockerfile.prod**
   - Cambiado: `--settings=patrimonio.settings.production`
   - A: `--settings=patrimonio.settings`

## Pasos para Aplicar

### En tu máquina local:

```bash
# Subir cambios a GitHub
git add docker-compose.simple.yml Dockerfile.prod
git commit -m "fix: usar patrimonio.settings en lugar de patrimonio.settings.production"
git push origin main
```

### En el servidor Ubuntu:

```bash
# Actualizar código
cd ~/dockers/sistema_patrimonio_drtc
git pull origin main

# Limpiar imágenes anteriores
docker compose -f docker-compose.simple.yml down
docker system prune -af

# Reconstruir y desplegar
docker compose -f docker-compose.simple.yml up -d --build

# Ver logs
docker compose -f docker-compose.simple.yml logs -f
```

## Verificación

```bash
# Ver estado de contenedores
docker compose -f docker-compose.simple.yml ps

# Ver logs específicos
docker compose -f docker-compose.simple.yml logs web
docker compose -f docker-compose.simple.yml logs celery
```

¡Ahora debería funcionar correctamente! 🚀
