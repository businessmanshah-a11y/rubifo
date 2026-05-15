# Rubifo Launch Guide - Staging & Production

## Deployment Timeline

- **Week 1**: Staging Environment Setup
- **Week 2**: QA & Testing
- **Week 3**: Production Deployment
- **Week 4**: Monitoring & Optimization

---

## Phase 1: Staging Environment (T75 Part 1)

### 1.1 Staging Infrastructure

```bash
# Create staging directory
mkdir /opt/rubifo-staging
cd /opt/rubifo-staging

# Clone repository
git clone https://github.com/yourusername/rubifo.git .

# Create staging environment
cp .env.example .env.staging
nano .env.staging
```

### 1.2 Staging Configuration

```env
# .env.staging

# Rubika Bot
BOT_TOKEN=your_staging_bot_token
BOT_MODE=staging

# Database (staging DB)
DATABASE_URL=postgresql://rubifo_staging:password@staging-db.internal:5432/rubifo_staging

# Payment Gateway (sandbox)
ZARINPAL_MERCHANT_ID=your_sandbox_merchant_id
ZARINPAL_SANDBOX=true
ZARINPAL_CALLBACK_URL=https://staging.rubifo.ir/payment/callback

# Admin Panel
ADMIN_USERNAME=staging-admin
ADMIN_PASSWORD_HASH=...
JWT_SECRET=...

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=/var/log/rubifo-staging/app.log
```

### 1.3 Deploy to Staging

```bash
# Using Docker Compose
docker-compose -f docker-compose.staging.yml up -d

# OR using Systemd
sudo systemctl start rubifo-staging
```

### 1.4 Staging Health Checks

```bash
# Check services
curl https://staging.rubifo.ir/health

# Check database
psql -U rubifo_staging -h staging-db.internal -d rubifo_staging

# View logs
tail -f /var/log/rubifo-staging/app.log

# Test Zarinpal integration
curl -X POST https://api.zarinpal.com/pg/v4/payment/request.json \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "STAGING_MERCHANT",
    "amount": 50000,
    "description": "Test",
    "callback_url": "https://staging.rubifo.ir/callback"
  }'
```

---

## Phase 2: QA & Testing

### 2.1 Testing Checklist

- [ ] User registration and trial
- [ ] Subscription purchase (sandbox)
- [ ] Route creation and management
- [ ] Message queue and forwarding
- [ ] Schedule creation (interval and daily)
- [ ] Admin dashboard access
- [ ] Payment verification
- [ ] Error handling and recovery
- [ ] Performance under load
- [ ] SSL certificate validity

### 2.2 Load Testing

```bash
# Install load testing tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=https://staging.rubifo.ir -u 100 -r 10
```

### 2.3 Security Audit

```bash
# SSL/TLS check
nmap --script ssl-cert,ssl-enum-ciphers -p 443 staging.rubifo.ir

# OWASP Top 10 scan
# Use OWASP ZAP or similar

# Dependency vulnerabilities
pip install safety
safety check
```

### 2.4 Database Backup Test

```bash
# Backup staging database
pg_dump -U rubifo_staging rubifo_staging > staging_backup_$(date +%Y%m%d).sql

# Test restore
psql -U rubifo_staging -d rubifo_staging_test < staging_backup_*.sql
```

---

## Phase 3: Production Deployment

### 3.1 Production Infrastructure Preparation

```bash
# Create production directory
mkdir /opt/rubifo
cd /opt/rubifo

# Clone production branch
git clone -b main https://github.com/yourusername/rubifo.git .

# Set restrictive permissions
chmod 750 /opt/rubifo
```

### 3.2 Production Configuration

```bash
# Create production environment
cp .env.example .env
nano .env
```

```env
# .env (production)

# Rubika Bot
BOT_TOKEN=your_production_bot_token
BOT_MODE=production

# Database (production DB)
DATABASE_URL=postgresql://rubifo:secure_password@prod-db.internal:5432/rubifo
DATABASE_POOL_MIN=10
DATABASE_POOL_MAX=20
DATABASE_TIMEOUT=30

# Payment Gateway (production)
ZARINPAL_MERCHANT_ID=your_production_merchant_id
ZARINPAL_SANDBOX=false
ZARINPAL_CALLBACK_URL=https://rubifo.ir/payment/callback

# Admin Panel
ADMIN_USERNAME=prod-admin
ADMIN_PASSWORD_HASH=...
JWT_SECRET=...

# SSL/TLS
SSL_CERT_PATH=/etc/letsencrypt/live/rubifo.ir/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/rubifo.ir/privkey.pem

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_URL=https://grafana.rubifo.ir
```

### 3.3 Database Migration

```bash
# Backup production before migration
pg_basebackup -U rubifo -Ft -z -P -D ./backup/pre-migration

# Apply migrations
python -m migrations.run_migrations

# Verify schema
psql -U rubifo -d rubifo -c "\dt"
```

### 3.4 SSL Certificate Setup

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d rubifo.ir -d www.rubifo.ir

# Verify
sudo certbot certificates
```

### 3.5 Deploy to Production

```bash
# Using Docker Compose (recommended)
docker-compose -f docker-compose.prod.yml up -d

# Verify services
docker-compose -f docker-compose.prod.yml ps

# OR using Systemd
sudo systemctl start rubifo
sudo systemctl status rubifo
```

### 3.6 Production Verification

```bash
# Health check
curl -I https://rubifo.ir/health

# Admin panel access
curl -I https://rubifo.ir/admin/

# Database connectivity
psql -U rubifo -h localhost -d rubifo -c "SELECT version();"

# Check logs
sudo journalctl -u rubifo -n 50

# Monitor services
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Phase 4: Monitoring & Optimization

### 4.1 Monitoring Setup

```bash
# Access Prometheus
curl http://localhost:9090/metrics

# Access Grafana
open https://grafana.rubifo.ir

# Create dashboards for:
# - Application metrics
# - Database performance
# - System resources
# - Payment processing
# - Queue depth
```

### 4.2 Performance Monitoring

```bash
# Check application response times
curl -w '@curl-format.txt' -o /dev/null -s https://rubifo.ir/health

# Monitor database slow queries
tail -f /var/log/postgresql/postgresql.log | grep "duration:"

# Check queue depth
psql -U rubifo -d rubifo -c \
  "SELECT status, COUNT(*) FROM post_queue GROUP BY status;"
```

### 4.3 Alert Configuration

```yaml
# prometheus.yml rules
- alert: HighQueueDepth
  expr: queue_depth > 1000
  for: 5m
  annotations:
    summary: "High queue depth detected"

- alert: DatabaseConnectionPoolExhausted
  expr: db_connections > 18
  for: 5m
  annotations:
    summary: "Database connection pool nearly full"

- alert: PaymentGatewayDown
  expr: zarinpal_api_health == 0
  for: 1m
  annotations:
    summary: "Zarinpal payment gateway is down"
```

### 4.4 Logging & Observability

```bash
# Centralize logs (using ELK stack or similar)
filebeat -c /etc/filebeat/filebeat.yml -e

# Trace requests
curl -H "X-Trace-ID: $(uuidgen)" https://rubifo.ir/api/users

# Performance profiling
py-spy record -o profile.svg -- python -m src.bot.main
```

---

## Rollback Plan

If issues occur in production:

### 4.1 Immediate Actions

```bash
# 1. Check what went wrong
docker-compose -f docker-compose.prod.yml logs --tail=100

# 2. Stop problematic service
docker-compose -f docker-compose.prod.yml stop rubifo

# 3. Switch to previous version
git checkout HEAD~1
docker-compose -f docker-compose.prod.yml up -d rubifo
```

### 4.2 Database Rollback

```bash
# If database migration failed:
# 1. Restore from backup
psql -U rubifo rubifo < ./backup/pre-migration.sql

# 2. Verify
psql -U rubifo -d rubifo -c "SELECT COUNT(*) FROM users;"
```

### 4.3 Notification

```bash
# Notify stakeholders
# - Post-mortem meeting
# - Document incident
# - Implement preventive measures
```

---

## Launch Checklist

### Pre-Launch
- [ ] Staging tests all passing
- [ ] Security audit complete
- [ ] SSL certificate valid
- [ ] Database backups tested
- [ ] Monitoring configured
- [ ] Runbooks prepared
- [ ] Team training complete

### Launch Day
- [ ] Database migration in non-peak hours
- [ ] Health checks passing
- [ ] Admin dashboard accessible
- [ ] Payment gateway working
- [ ] Monitoring active
- [ ] On-call support ready

### Post-Launch (First 24 Hours)
- [ ] Monitor queue depth
- [ ] Check error rates
- [ ] Review payment processing
- [ ] Verify user registrations
- [ ] Monitor resource usage
- [ ] Check performance metrics

### Post-Launch (First Week)
- [ ] Analyze usage patterns
- [ ] Optimize database queries
- [ ] Fine-tune cache settings
- [ ] Review logs for issues
- [ ] Gather user feedback
- [ ] Plan improvements

---

## Support Contacts

- **On-Call**: team@rubifo.ir
- **Escalation**: admin@rubifo.ir
- **Emergency**: +98-XXX-XXX-XXXX

---

**Version**: 1.0.0  
**Last Updated**: 2026-05-15  
**Status**: Ready for Production
