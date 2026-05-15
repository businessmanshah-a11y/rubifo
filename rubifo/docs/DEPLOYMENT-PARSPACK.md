# 🚀 Deployment Guide - Parspack Integration
**تاریخ**: ۱۴۰۵/۰۲/۲۵ | ۲۰۲۶/۰۵/۱۵  
**هدف**: Rubifo را روی سرورهای ایران با پارس‌پک دیپلوی کنیم

---

## 1. درباره Parspack

**Parspack** = خدمات ابری ایرانی (PaaS + هاستینگ + DevOps)

### خصوصیات برای Rubifo:
- ✅ PaaS برای Python apps
- ✅ PostgreSQL managed database
- ✅ SSL/TLS رایگان
- ✅ Auto-scaling
- ✅ VSCode extension برای سهل‌تر دیپلوی
- ✅ نت ملی / تانل اتصال

---

## 2. Parspack VSCode Extension

### نصب

1. **VSCode Extensions** (Ctrl+Shift+X یا Cmd+Shift+X)
2. جستجو: `Parspack`
3. نصب: "Parspack Web Hosting VSCode Extension"
4. یا دانلود از: https://marketplace.visualstudio.com/items?itemName=parspack.parspack

### تنظیمات اولیه

```
1. VSCode میں Parspack icon کلیک کنید (سایڈ بار)
2. "Login" یا "Register" اختیار کنید
3. اکاؤنٹ بنائیں یا داخل ہوں
4. Authorization token VSCode میں ذخیرہ ہوگا
```

### VSCode میں Commands

```
Cmd+Shift+P (یا Ctrl+Shift+P Windows میں):

- "Parspack: Create Project"
- "Parspack: Deploy"
- "Parspack: View Logs"
- "Parspack: Set Environment Variables"
- "Parspack: Database Management"
- "Parspack: Domain Settings"
```

---

## 3. Parspack Project Setup

### Step 1: VSCode میں Project بنائیں

```
1. Parspack icon → "Create Project"
2. Project Name: rubifo-bot
3. Type: Python (Django/FastAPI)
4. Framework: FastAPI / Custom Python
5. Database: PostgreSQL
6. Create
```

### Step 2: Auto-generated Files

Parspack یہ فائلیں خود بنائے گا:

```
.parspack/
├── config.yml          # Parspack configuration
├── runtime.txt         # Python version
└── procfile            # Startup commands
```

### Step 3: ترمیم config.yml

```yaml
# .parspack/config.yml

name: rubifo-bot
language: python
framework: fastapi

runtime:
  python: "3.10"

dependencies:
  pip: requirements.txt

env:
  DATABASE_URL: postgresql://...
  BOT_TOKEN: ${BOT_TOKEN}
  ZARINPAL_MERCHANT_ID: ${ZARINPAL_MERCHANT_ID}

build:
  command: "pip install -r requirements.txt"

run:
  web: "python -m src.bot.main"
  admin: "python -m src.admin.main"
  worker: "python -m src.core.execution_engine"

processes:
  - type: web
    quantity: 1
    size: small

services:
  - type: postgresql
    name: rubifo-db
    version: "13"
    storage: "10Gi"

healthcheck:
  path: /admin/health
  interval: 30s
  timeout: 10s
```

---

## 4. Environment Variables در Parspack

### VSCode میں تنظیم کریں

```
Cmd+Shift+P → "Parspack: Set Environment Variables"

یہ variables شامل کریں:

BOT_TOKEN = [your_rubika_bot_token]
DATABASE_URL = postgresql://...
ZARINPAL_MERCHANT_ID = [your_zarinpal_id]
ADMIN_USERNAME = admin
ADMIN_PASSWORD_HASH = [bcrypted_hash]
DEBUG = false
ENVIRONMENT = production
```

---

## 5. Database Setup

### Parspack میں PostgreSQL

```
1. VSCode → Parspack icon
2. "Database Management"
3. یا:
   - Parspack Dashboard میں login کنید
   - "Services" → "PostgreSQL"
   - Database بنائیں "rubifo"
```

### Connection String

Parspack خود یہ فراہم کرے گا:

```
postgresql://user:password@db.parspack.ir:5432/rubifo
```

اس کو `.env` میں ڈالیں:

```bash
DATABASE_URL=postgresql://user:password@db.parspack.ir:5432/rubifo
```

### Migrations

Deployment سے پہلے:

```bash
# Local میں:
python -m alembic upgrade head

# یا manual SQL:
psql -U user -h db.parspack.ir rubifo < migrations/001_init_schema.sql
```

---

## 6. Docker Alternative (اگر VSCode Extension نہ چلے)

### Parspack Docker Support

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.bot.main"]
```

### .parspack/docker.yml

```yaml
version: "3.8"
services:
  bot:
    build: .
    environment:
      DATABASE_URL: ${DATABASE_URL}
      BOT_TOKEN: ${BOT_TOKEN}
    ports:
      - "8000:8000"
    depends_on:
      - db
  
  admin:
    build: .
    command: python -m src.admin.main
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: ${DATABASE_URL}
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: rubifo
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

---

## 7. Deployment Process

### Option A: VSCode Extension (سب سے آسان)

```
1. Project تیار کریں (اوپر دیکھیں)
2. .env تیار کریں
3. requirements.txt تیار کریں
4. VSCode میں: Cmd+Shift+P
5. "Parspack: Deploy"
6. Branch منتخب کریں (main)
7. Deploy ہو جائے گا خود بخود
```

### Option B: Git Integration

```bash
# Parspack git remote شامل کریں:
git remote add parspack https://git.parspack.ir/youruser/rubifo.git

# Deploy کریں:
git push parspack main

# Parspack خود deploy کرے گا
```

### Option C: CLI (اگر Parspack CLI ہو)

```bash
# Install CLI
pip install parspack-cli

# Login
parspack login

# Deploy
parspack deploy --app rubifo-bot

# Check status
parspack logs --app rubifo-bot
```

---

## 8. Post-Deployment Checks

### Health Check

```bash
# Bot status check
curl https://rubifo-bot.parspack.ir/admin/health

# Expected response:
{
  "status": "ok",
  "database": "connected",
  "bot": "running"
}
```

### Logs

VSCode میں:
```
Cmd+Shift+P → "Parspack: View Logs"
```

یا Parspack Dashboard میں:
```
Logs → Filter: rubifo-bot
```

### Database Check

```bash
# Connect to Parspack PostgreSQL
psql -U user -h db.parspack.ir -d rubifo

# Check tables
\dt

# Check users table
SELECT COUNT(*) FROM users;
```

---

## 9. Monitoring & Scaling

### Auto-Scaling Setup

```yaml
# .parspack/config.yml میں:

processes:
  - type: web
    quantity: 1
    size: small
    autoscale:
      min: 1
      max: 5
      cpu_threshold: 80
      memory_threshold: 80
```

### Metrics Dashboard

```
Parspack Dashboard:
1. Select App: rubifo-bot
2. Metrics Tab
3. View: CPU, Memory, Requests, Errors
```

---

## 10. Custom Domain

### DNS Setup

```
1. Parspack Dashboard → "Domains"
2. "Add Domain"
3. Domain: rubifo.ir (یا subdomain)
4. Parspack یہ NS records دے گا:
   ns1.parspack.ir
   ns2.parspack.ir
5. اپنے Domain Registrar میں NS update کریں
```

### SSL Certificate

```
Parspack خود SSL دے گا (Let's Encrypt)
Auto-renew ہوگا
HTTPS automatically enabled
```

---

## 11. Backup & Recovery

### Automatic Backups

```
Parspack automatically backups:
- Database (daily)
- Application files (on deploy)
- Retention: 30 days
```

### Manual Backup

```
Parspack Dashboard:
1. Database → Select rubifo
2. "Backup" → "Create Backup"
3. Save locally
```

### Restore

```
1. Dashboard → Backups
2. Select backup
3. "Restore"
4. Confirm
```

---

## 12. Environment-Specific Configs

### Staging Setup

```yaml
# .parspack/config-staging.yml
name: rubifo-staging
environment: staging

services:
  - type: postgresql
    name: rubifo-db-staging
```

### Production Setup

```yaml
# .parspack/config-production.yml
name: rubifo-prod
environment: production
sso: true  # Single Sign-On

processes:
  - type: web
    quantity: 2
    size: medium
```

### Deploy to Different Environments

```bash
# VSCode میں:
Cmd+Shift+P → "Parspack: Deploy to Environment"
Select: production یا staging
```

---

## 13. Parspack Features Special untuk Iran

### نت ملی Support

```
✅ Parspack نت ملی support دیتا ہے
✅ Automatic DNS resolution
✅ No VPN needed for Iranian users
✅ Fast local hosting
```

### Performance in Iran

```
- Database latency: < 50ms
- Bot response time: < 100ms
- Asset serving: CDN via parspack.ir
```

---

## 14. Cost Estimation

### Parspack Pricing

| Component | Size | Cost (Monthly) |
|-----------|------|-----------|
| Web Process | Small | 50K تومان |
| PostgreSQL | 10GB | 100K تومان |
| Storage | 20GB | 30K تومان |
| Bandwidth | 100GB | 50K تومان |
| **Total** | - | **~230K تومان** |

**نوٹ**: قیمتیں تقریبی ہیں. Parspack کی موجودہ فی دیکھیں.

---

## 15. Troubleshooting

### Bot Not Responding

```
1. Check logs:
   Parspack: View Logs → Filter "error"

2. Restart process:
   Dashboard → App → Restart

3. Check database:
   psql connection test

4. Check bot token:
   Verify .env BOT_TOKEN is correct
```

### Database Connection Error

```
1. Verify DATABASE_URL in .env
2. Test connection locally:
   psql -c "SELECT 1"
3. Check Parspack PostgreSQL is running
4. Check firewall/IP whitelist
```

### Memory Issues

```
1. Check process size
2. Increase: small → medium
3. Monitor: Dashboard → Metrics
4. Optimize code if needed
```

### Domain Not Working

```
1. Check NS records propagation (24-48 hours)
2. Verify DNS in Domain Registrar
3. Check Parspack DNS settings
4. SSL certificate auto-generated?
5. CNAME fallback if NS not working:
   rubifo.ir CNAME rubifo-bot.parspack.ir
```

---

## 16. Deployment Checklist

### Before First Deploy

- [ ] requirements.txt complete
- [ ] .env.example created
- [ ] All environment variables identified
- [ ] Database migrations ready
- [ ] Health check endpoint working
- [ ] Logging configured
- [ ] Error handling complete
- [ ] Tests passing
- [ ] Docker builds locally
- [ ] Parspack account created
- [ ] PostgreSQL database exists
- [ ] Domain registered (if custom)
- [ ] Backups planned

### Deployment Day

- [ ] Final code commit
- [ ] All tests pass
- [ ] Database backed up
- [ ] Deploy via VSCode Extension
- [ ] Verify health check
- [ ] Check logs for errors
- [ ] Test bot with real message
- [ ] Test admin dashboard
- [ ] Monitor for 1 hour
- [ ] Document any issues

### Post-Deployment

- [ ] Set up monitoring/alerts
- [ ] Configure auto-backups
- [ ] Set up daily health checks
- [ ] Document deployment process
- [ ] Update deployment docs
- [ ] Share access with team

---

## 17. خلاصہ Parspack Workflow

```
1. Parspack اکاؤنٹ بنائیں
2. VSCode extension انسٹال کریں
3. "Create Project" کریں
4. config.yml ترمیم کریں
5. .env variables سیٹ کریں
6. Database migrations چلائیں
7. "Deploy" کریں VSCode سے
8. Health check verify کریں
9. Logs میں چیک کریں
10. جیتے رہیں! 🎉
```

---

## 18. مفید لنکس

- **Parspack وبسائٹ**: https://parspack.ir
- **VSCode Extension**: Marketplace میں Parspack تلاش کریں
- **Documentation**: https://docs.parspack.ir
- **Support**: support@parspack.ir
- **Community**: Parspack Telegram

---

## 19. Alternative: Self-Hosted (اگر نہ چاہیں)

```bash
# اگر Parspack استعمال نہیں کرنا:

# Ubuntu/Debian سرور:
1. Python 3.10 انسٹال کریں
2. PostgreSQL انسٹال کریں
3. systemd service بنائیں
4. Nginx reverse proxy سیٹ اپ کریں
5. SSL (Let's Encrypt) سیٹ اپ کریں
6. Supervisor یا systemd کے ذریعے manage کریں
```

---

**نوٹ**: اگر Parspack VSCode extension کام نہ کرے تو Docker یا CLI استعمال کریں.

**آخری اپڈیٹ**: ۱۴۰۵/۰۲/۲۵

