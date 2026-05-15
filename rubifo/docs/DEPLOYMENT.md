# Rubifo Deployment Guide

## Overview

Rubifo is a Rubika auto-forward bot built with Python, PostgreSQL, and FastAPI. This guide covers production deployment on Linux servers.

**Deployment Options:**
1. Docker Compose (recommended for cloud environments)
2. Systemd Service (recommended for dedicated servers)
3. Manual installation

---

## Prerequisites

- Ubuntu 20.04 LTS or CentOS 8+
- 2+ CPU cores
- 2GB+ RAM
- 10GB+ disk space
- PostgreSQL 12+
- Python 3.10+

### Ports Required
- 80 (HTTP)
- 443 (HTTPS)
- 5432 (PostgreSQL, internal only)
- 6379 (Redis, internal only)
- 8000 (Application, internal only)
- 9090 (Prometheus, internal only)
- 3000 (Grafana, internal only)

---

## Option 1: Docker Compose Deployment (Recommended)

### Step 1: Install Docker & Docker Compose

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Clone and Setup

```bash
git clone https://github.com/yourusername/rubifo.git /opt/rubifo
cd /opt/rubifo

# Create environment file
cp .env.example .env

# Edit with production values
nano .env
```

### Step 3: Configure Environment

```env
# Bot Configuration
BOT_TOKEN=your_rubika_bot_token
ZARINPAL_MERCHANT_ID=your_merchant_id
ZARINPAL_SANDBOX=false

# Database
DB_USER=rubifo
DB_PASSWORD=your_secure_password

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=your_bcrypt_hash
JWT_SECRET=your_jwt_secret

# System
LOG_LEVEL=INFO
```

### Step 4: Generate Secure Values

```bash
# Generate bcrypt password hash
python3 -c "import bcrypt; print(bcrypt.hashpw(b'password', bcrypt.gensalt()).decode())"

# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Start Services

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f rubifo
```

### Step 6: SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --standalone -d rubifo.ir -d www.rubifo.ir

# Auto-renewal (cron)
0 2 * * * certbot renew --quiet
```

---

## Option 2: Systemd Service Deployment

### Step 1: Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip postgresql postgresql-contrib nginx

# Install pip packages globally or in venv
cd /opt/rubifo
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Setup Database

```bash
sudo -u postgres psql

CREATE DATABASE rubifo;
CREATE USER rubifo WITH PASSWORD 'secure_password';
ALTER ROLE rubifo SET client_encoding TO 'utf8';
ALTER ROLE rubifo SET default_transaction_isolation TO 'read committed';
ALTER ROLE rubifo SET default_transaction_deferrable TO on;
ALTER ROLE rubifo SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE rubifo TO rubifo;

\q
```

### Step 3: Run Migrations

```bash
cd /opt/rubifo
source venv/bin/activate
python -m migrations.run_migrations
```

### Step 4: Install Systemd Service

```bash
sudo cp rubifo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rubifo
sudo systemctl start rubifo

# Check status
sudo systemctl status rubifo
```

### Step 5: Configure Nginx

```bash
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: Setup Monitoring

```bash
# Install Prometheus and Grafana
# See monitoring section below
```

---

## Monitoring & Logging

### Prometheus Configuration

Create `/opt/rubifo/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'rubifo'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

### Grafana Dashboards

1. Access Grafana: http://your-server:3000
2. Login: admin / admin
3. Add Prometheus data source
4. Import dashboards:
   - Rubika Bot Metrics
   - Database Performance
   - System Health

### Log Monitoring

```bash
# View logs with journalctl
sudo journalctl -u rubifo -f

# Log rotation
sudo tee /etc/logrotate.d/rubifo << EOF
/var/log/rubifo/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 rubifo rubifo
    sharedscripts
    postrotate
        systemctl reload rubifo > /dev/null 2>&1 || true
    endscript
}
EOF
```

---

## Health Checks

### Application Health

```bash
# Check application health
curl -s http://localhost:8000/health | jq .

# Database connectivity
psql postgresql://rubifo:password@localhost/rubifo -c "SELECT 1"
```

### Automated Health Checks

Add to crontab:

```bash
*/5 * * * * curl -f http://localhost:8000/health || systemctl restart rubifo
*/15 * * * * psql -U rubifo -h localhost -d rubifo -c "SELECT 1" || systemctl restart postgresql
```

---

## Backup & Recovery

### Database Backup

```bash
# Daily backup
0 2 * * * pg_dump -U rubifo rubifo > /backups/rubifo_$(date +\%Y\%m\%d).sql

# Weekly backup to S3
0 3 * * 0 pg_dump -U rubifo rubifo | gzip | aws s3 cp - s3://my-bucket/backups/rubifo_$(date +\%Y\%m\%d).sql.gz
```

### Disaster Recovery

```bash
# Restore from backup
psql -U rubifo rubifo < /backups/rubifo_YYYYMMDD.sql

# Point-in-time recovery
pg_basebackup -U rubifo -Ft -z -P -D ./backup
```

---

## Performance Tuning

### PostgreSQL

```sql
-- In postgresql.conf or ALTER DATABASE
ALTER DATABASE rubifo SET shared_buffers = '256MB';
ALTER DATABASE rubifo SET effective_cache_size = '1GB';
ALTER DATABASE rubifo SET maintenance_work_mem = '64MB';
ALTER DATABASE rubifo SET work_mem = '16MB';
```

### Application

```env
# In .env
DATABASE_POOL_MIN=10
DATABASE_POOL_MAX=20
DATABASE_TIMEOUT=30
API_RATE_LIMIT_DELAY=0.1
```

---

## Security Hardening

### Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### SSL/TLS

- Use HSTS headers (configured in nginx.conf)
- Minimum TLS 1.2
- Strong cipher suites
- Certificate pinning for API calls

### Database

- Separate user for application
- No root login for application
- Connection pooling
- SSL connections required

### Application

- Environment variables for secrets
- JWT token rotation
- Rate limiting on all endpoints
- Input validation and sanitization

---

## Scaling

### Horizontal Scaling

For multiple bot instances:

```yaml
# docker-compose.prod.yml
services:
  rubifo-bot-1:
    # Instance 1
  rubifo-bot-2:
    # Instance 2
  load-balancer:
    # Nginx upstream
```

### Vertical Scaling

Increase for higher load:

```bash
# Database pool
DATABASE_POOL_MAX=50

# Worker processes
WORKER_PROCESSES=4
```

---

## Troubleshooting

### Bot Not Starting

```bash
# Check logs
journalctl -u rubifo -n 100

# Verify configuration
source venv/bin/activate
python -c "from src.config import *; print('Config OK')"

# Test database
psql -U rubifo -h localhost -d rubifo
```

### Payment Gateway Issues

```bash
# Check Zarinpal connectivity
curl https://api.zarinpal.com/pg/v4/payment/verify.json

# Verify credentials
grep ZARINPAL_MERCHANT_ID .env
```

### Performance Issues

```bash
# Check database connections
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;

# Monitor CPU/Memory
top -p $(pgrep -f "python -m src.bot.main")

# Check queue depth
psql -U rubifo -d rubifo -c "SELECT COUNT(*) FROM post_queue WHERE status = 'pending';"
```

---

## Updates & Maintenance

### Rolling Updates

```bash
# Test on staging first
docker-compose -f docker-compose.staging.yml pull
docker-compose -f docker-compose.staging.yml up -d

# Production deployment
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --no-deps -d rubifo
```

### Database Migrations

```bash
# Backup first
pg_dump -U rubifo rubifo > /backups/pre-migration.sql

# Run migrations
python -m migrations.run_migrations

# Verify
psql -U rubifo -d rubifo -c "\dt"
```

---

## Support & Resources

- **Documentation**: https://rubifo.ir/docs
- **Issues**: https://github.com/yourusername/rubifo/issues
- **Monitoring Dashboard**: http://your-server:3000
- **Admin Panel**: https://your-server/admin

---

**Version**: 1.0.0  
**Last Updated**: 2026-05-15
