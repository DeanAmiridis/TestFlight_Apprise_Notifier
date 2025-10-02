# Docker Deployment Guide

This document explains how to deploy the TestFlight Apprise Notifier using Docker.

## Quick Start

### Using Docker Compose (Recommended)

1. Make sure you have a `.env` file configured with your settings
2. Build and start the container:

```bash
docker-compose up -d
```

3. View logs:

```bash
docker-compose logs -f
```

4. Stop the container:

```bash
docker-compose down
```

### Using Docker CLI

1. Build the image:

```bash
docker build -t testflight-notifier .
```

2. Run the container:

```bash
docker run -d \
  --name testflight-notifier \
  -p 8080:8080 \
  --env-file .env \
  --restart unless-stopped \
  testflight-notifier
```

3. View logs:

```bash
docker logs -f testflight-notifier
```

4. Stop and remove:

```bash
docker stop testflight-notifier
docker rm testflight-notifier
```

## Configuration

### Environment Variables

All configuration is done through the `.env` file. Create one in the same directory as your `docker-compose.yml`:

```ini
# Required
ID_LIST=abc123,def456,ghi789
APPRISE_URL=discord://webhook_id/webhook_token

# Optional
INTERVAL_CHECK=10000
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8080
```

### Volumes

The `docker-compose.yml` includes optional volume mounts:

- `./.env:/app/.env:ro` - Mount your .env file (read-only)
- `./data:/app/data` - Persistent data directory (for future use)

### Networking

By default, the web dashboard is exposed on port 8080. To change:

```yaml
ports:
  - "9000:8080"  # Access on host port 9000
```

## Health Checks

The container includes health checks that verify the application is running:

- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts before marking unhealthy
- **Start Period**: 10 seconds grace period on startup

Check health status:

```bash
docker ps  # Look for "(healthy)" in the STATUS column
```

## Updating

To update to a new version:

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

## Logs

### View Logs

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Log Rotation

Logs are automatically rotated with:
- Maximum file size: 10MB
- Maximum files kept: 3

## Troubleshooting

### Container Won't Start

1. Check logs:
```bash
docker-compose logs
```

2. Verify .env file exists and is valid

3. Check port availability:
```bash
lsof -i :8080  # On macOS/Linux
netstat -ano | findstr :8080  # On Windows
```

### Can't Access Web Dashboard

1. Verify container is running:
```bash
docker ps
```

2. Check container IP:
```bash
docker inspect testflight-notifier | grep IPAddress
```

3. Test from inside container:
```bash
docker exec testflight-notifier curl http://localhost:8080/api/health
```

### Permission Issues

If you encounter permission issues with volumes:

```bash
# Linux: Fix permissions
sudo chown -R $USER:$USER ./data
```

## Advanced Configuration

### Custom Network

To use a custom Docker network:

```yaml
services:
  testflight-notifier:
    networks:
      - my-network

networks:
  my-network:
    driver: bridge
```

### Resource Limits

To limit container resources:

```yaml
services:
  testflight-notifier:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Multiple Instances

To run multiple instances (for different configurations):

```bash
# Instance 1
docker-compose -p notifier1 -f docker-compose.yml up -d

# Instance 2 (different port)
docker-compose -p notifier2 -f docker-compose.yml up -d
# Edit docker-compose.yml to use different ports first
```

## Production Deployment

### Using with Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name testflight.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Using with Docker Swarm

Deploy as a service:

```bash
docker service create \
  --name testflight-notifier \
  --replicas 1 \
  --publish published=8080,target=8080 \
  --env-file .env \
  testflight-notifier:latest
```

### Backup and Restore

To backup configuration:

```bash
# Backup .env file
cp .env .env.backup

# Backup data directory (if using)
tar -czf data-backup.tar.gz ./data
```

To restore:

```bash
# Restore .env
cp .env.backup .env

# Restore data
tar -xzf data-backup.tar.gz
```

## Security Considerations

1. **Never commit `.env`** to version control
2. **Use strong passwords** in Apprise URLs
3. **Keep Docker updated** for security patches
4. **Use read-only volumes** where possible
5. **Limit container resources** to prevent DoS
6. **Run behind reverse proxy** for HTTPS support

## Monitoring

### Integration with Monitoring Tools

The `/api/health` endpoint can be used with monitoring tools:

- **Uptime Kuma**: HTTP endpoint monitoring
- **Prometheus**: Can scrape health endpoint
- **Datadog**: Docker integration
- **Grafana**: Via Prometheus or Loki

### Metrics Export

Future versions will include Prometheus metrics at `/metrics`.

## Uninstall

To completely remove the application:

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi testflight-notifier

# Remove volumes (if any)
docker volume prune

# Remove data directory (optional)
rm -rf ./data
```

## Support

For issues related to Docker deployment:
1. Check the logs first
2. Verify your .env configuration
3. Try rebuilding the image
4. Check GitHub issues for known problems
