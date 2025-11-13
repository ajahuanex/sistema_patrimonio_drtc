# Health Checks System

## Overview

The Sistema de Registro de Patrimonio DRTC Puno includes a comprehensive health check system to monitor the status of all critical services in production. This system provides both basic and detailed health check endpoints, along with automatic service restart capabilities.

## Health Check Endpoints

### Basic Health Check: `/health/`

A lightweight endpoint for quick health verification.

**Response Format:**
```json
{
    "status": "healthy",
    "timestamp": "2024-11-12T10:30:00.000000Z",
    "version": "1.0.0"
}
```

**HTTP Status Codes:**
- `200 OK`: Service is healthy

**Use Cases:**
- Docker health checks
- Load balancer health probes
- Quick availability checks

**Example:**
```bash
curl http://localhost:8000/health/
```

### Detailed Health Check: `/health/detailed/`

A comprehensive endpoint that verifies all critical services.

**Response Format:**
```json
{
    "status": "healthy",
    "timestamp": "2024-11-12T10:30:00.000000Z",
    "version": "1.0.0",
    "services": {
        "database": {
            "status": "healthy",
            "response_time_ms": 5,
            "message": "Database connection successful"
        },
        "redis": {
            "status": "healthy",
            "response_time_ms": 2,
            "message": "Redis connection successful"
        },
        "celery": {
            "status": "healthy",
            "response_time_ms": 150,
            "active_workers": 4,
            "active_tasks": 12,
            "message": "4 worker(s) active"
        }
    }
}
```

**HTTP Status Codes:**
- `200 OK`: All services are healthy
- `503 Service Unavailable`: One or more services are unhealthy

**Service Checks:**

1. **Database (PostgreSQL)**
   - Executes a simple query with 5-second timeout
   - Measures response time
   - Verifies connection is active

2. **Redis**
   - Performs set/get/delete operations
   - Measures response time
   - Verifies cache functionality

3. **Celery**
   - Checks for active workers
   - Counts active tasks
   - Verifies task queue is operational
   - 5-second timeout for worker inspection

**Example:**
```bash
curl http://localhost:8000/health/detailed/
```

## Docker Health Checks

All services in `docker-compose.prod.yml` are configured with health checks:

### Database (PostgreSQL)
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Redis
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 20s
```

### Web (Django)
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Celery Worker
```yaml
healthcheck:
  test: ["CMD-SHELL", "celery -A patrimonio inspect ping -d celery@$$HOSTNAME"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Celery Beat
```yaml
healthcheck:
  test: ["CMD-SHELL", "pgrep -f 'celery beat' || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Nginx
```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/health/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## Health Check Parameters

- **interval**: Time between health checks (30 seconds)
- **timeout**: Maximum time for health check to complete (10 seconds)
- **retries**: Number of consecutive failures before marking unhealthy (3 times)
- **start_period**: Grace period during container startup (varies by service)

## Automatic Restart Behavior

When a service fails its health check 3 consecutive times:

1. Docker marks the container as `unhealthy`
2. The `restart: unless-stopped` policy triggers
3. Docker automatically restarts the container
4. The service enters the `start_period` grace period
5. Health checks resume after the grace period

## Monitoring Health Checks

### Check Service Status
```bash
# View all service health status
docker-compose -f docker-compose.prod.yml ps

# Check specific service health
docker inspect --format='{{.State.Health.Status}}' patrimonio_web_1
```

### View Health Check Logs
```bash
# View last 5 health check results
docker inspect --format='{{json .State.Health}}' patrimonio_web_1 | jq

# Monitor health checks in real-time
watch -n 5 'docker-compose -f docker-compose.prod.yml ps'
```

### Manual Health Check Testing
```bash
# Test basic health check
curl -f http://localhost/health/

# Test detailed health check
curl -f http://localhost/health/detailed/ | jq

# Test with HTTPS
curl -f https://your-domain.com/health/detailed/ | jq
```

## Troubleshooting

### Service Marked as Unhealthy

1. **Check service logs:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs [service-name]
   ```

2. **Check health check output:**
   ```bash
   docker inspect --format='{{json .State.Health}}' [container-name] | jq
   ```

3. **Manually test the health check command:**
   ```bash
   docker-compose -f docker-compose.prod.yml exec [service-name] [health-check-command]
   ```

### Database Health Check Failing

**Possible causes:**
- Database not fully initialized
- Connection pool exhausted
- Disk space full
- Network issues

**Solutions:**
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Verify database is accepting connections
docker-compose -f docker-compose.prod.yml exec db pg_isready -U ${POSTGRES_USER}

# Check active connections
docker-compose -f docker-compose.prod.yml exec db psql -U ${POSTGRES_USER} -c "SELECT count(*) FROM pg_stat_activity;"
```

### Redis Health Check Failing

**Possible causes:**
- Redis password mismatch
- Memory limit reached
- Network issues

**Solutions:**
```bash
# Check Redis logs
docker-compose -f docker-compose.prod.yml logs redis

# Test Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} ping

# Check Redis memory usage
docker-compose -f docker-compose.prod.yml exec redis redis-cli -a ${REDIS_PASSWORD} info memory
```

### Celery Health Check Failing

**Possible causes:**
- No workers started
- Workers crashed
- Redis connection issues
- Task queue blocked

**Solutions:**
```bash
# Check Celery logs
docker-compose -f docker-compose.prod.yml logs celery

# Inspect active workers
docker-compose -f docker-compose.prod.yml exec celery celery -A patrimonio inspect active

# Check worker stats
docker-compose -f docker-compose.prod.yml exec celery celery -A patrimonio inspect stats
```

### Web Service Health Check Failing

**Possible causes:**
- Application startup errors
- Database migration pending
- Static files not collected
- Port already in use

**Solutions:**
```bash
# Check web logs
docker-compose -f docker-compose.prod.yml logs web

# Test health endpoint directly
docker-compose -f docker-compose.prod.yml exec web curl -f http://localhost:8000/health/

# Check if port is listening
docker-compose -f docker-compose.prod.yml exec web netstat -tlnp | grep 8000
```

## Integration with Monitoring Tools

### Prometheus

Add the following to your Prometheus configuration:

```yaml
scrape_configs:
  - job_name: 'patrimonio-health'
    metrics_path: '/health/detailed/'
    static_configs:
      - targets: ['your-domain.com']
```

### Uptime Robot

Configure HTTP(s) monitor:
- **URL**: `https://your-domain.com/health/`
- **Interval**: 5 minutes
- **Alert**: Email/SMS on failure

### Grafana

Create dashboard with health check metrics:
- Response time per service
- Service availability percentage
- Alert on consecutive failures

## Best Practices

1. **Monitor both endpoints**: Use `/health/` for quick checks and `/health/detailed/` for diagnostics

2. **Set appropriate timeouts**: Ensure health check timeouts are shorter than the interval

3. **Use start_period wisely**: Give services enough time to initialize before health checks begin

4. **Log health check failures**: Review logs regularly to identify patterns

5. **Test health checks**: Verify health checks work correctly before deploying to production

6. **External monitoring**: Use external services (Uptime Robot, Pingdom) to monitor from outside your infrastructure

7. **Alert on repeated failures**: Set up alerts when services fail health checks multiple times

## Configuration

### Environment Variables

Add to `.env.prod`:
```bash
# Application version for health checks
APP_VERSION=1.0.0
```

### Customizing Health Checks

To modify health check behavior, edit `patrimonio/health.py`:

```python
# Adjust database timeout
cursor.execute("SET statement_timeout = 5000")  # 5 seconds

# Adjust Celery inspection timeout
inspect = app.control.inspect(timeout=5.0)  # 5 seconds
```

## Security Considerations

1. **No authentication required**: Health check endpoints are public for monitoring purposes

2. **Limited information exposure**: Detailed endpoint only shows service status, not sensitive data

3. **Rate limiting**: Consider adding rate limiting to prevent abuse

4. **Internal vs External**: Use `/health/` for external monitoring, `/health/detailed/` for internal diagnostics

## Performance Impact

- **Basic health check**: < 5ms response time
- **Detailed health check**: 50-200ms response time (depends on service response times)
- **Resource usage**: Minimal CPU and memory impact
- **Network overhead**: Negligible

## Version History

- **v1.0.0**: Initial implementation with PostgreSQL, Redis, and Celery checks
