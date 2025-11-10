# Fix: ImportObservation Migration Issue

## Problem

The `catalogo_importobservation` table doesn't exist in the database because the migration hasn't been applied.

Error message:
```
relation "catalogo_importobservation" does not exist
```

## Solution

You need to run the migration inside the Docker container where the database is accessible.

### Step 1: Run Migration in Docker

```bash
# Run the migration inside the Docker container
docker-compose exec web python manage.py migrate catalogo

# Or run all pending migrations
docker-compose exec web python manage.py migrate
```

### Step 2: Verify Migration

```bash
# Check if the table was created
docker-compose exec web python manage.py showmigrations catalogo
```

You should see:
```
catalogo
 [X] 0001_initial
 [X] 0002_auto_...
 [X] 0003_importobservation
```

### Step 3: Test Import Again

After running the migration, try importing the catalog again from the web interface:
- Go to http://localhost:8000/catalogo/importar/
- Upload your Excel file
- The import should now work without errors

## Alternative: Run Migration from Docker Compose

If the container is not running:

```bash
# Start the containers
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Check logs
docker-compose logs web
```

## Verification

After running the migration, you can verify the table exists:

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d patrimonio_db

# Check if table exists
\dt catalogo_importobservation

# Exit PostgreSQL
\q
```

## What This Migration Does

The `0003_importobservation.py` migration creates the `ImportObservation` model table with these fields:
- `modulo`: Module name (catalogo, bienes, oficinas)
- `tipo`: Observation type (advertencia, error, info)
- `fila`: Row number in Excel
- `columna`: Column name
- `valor_original`: Original value from Excel
- `valor_corregido`: Corrected value (if applicable)
- `mensaje`: Observation message
- `fecha_importacion`: Import timestamp
- `usuario`: User who performed the import
- `archivo_nombre`: Excel filename

This allows the system to track and display observations during the import process.

## Future Prevention

To avoid this issue in the future:

1. Always run migrations after pulling new code:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

2. Check for pending migrations:
   ```bash
   docker-compose exec web python manage.py showmigrations
   ```

3. Create migrations when models change:
   ```bash
   docker-compose exec web python manage.py makemigrations
   ```
