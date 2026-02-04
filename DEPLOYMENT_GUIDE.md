# 🚀 CASINO PLATFORM - DEPLOYMENT GUIDE

## 📦 REQUIREMENTS.TXT (Backend)

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg2-binary==2.9.9
pydantic==2.5.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
redis==5.0.1
aiogram==3.3.0
APScheduler==3.10.4
python-dotenv==1.0.0
websockets==12.0
```

## 🗄 DATABASE SETUP

### 1. PostgreSQL Installation

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE casino_db;
CREATE USER casino_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE casino_db TO casino_user;
\q
```

### 2. Run Migrations

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## 🔧 BACKEND DEPLOYMENT

### 1. Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://casino_user:your_password@localhost:5432/casino_db

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=30

# Telegram Bot
BOT_TOKEN=your_telegram_bot_token
WEBAPP_URL=https://your-webapp-domain.com
CHANNEL_ID=@your_channel
ADMIN_IDS=123456789,987654321

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### 2. Systemd Service (Production)

Create `/etc/systemd/system/casino-api.service`:

```ini
[Unit]
Description=Casino Platform API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/casino/backend
Environment="PATH=/var/www/casino/venv/bin"
ExecStart=/var/www/casino/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable casino-api
sudo systemctl start casino-api
sudo systemctl status casino-api
```

### 3. Nginx Configuration

```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable SSL with Certbot:

```bash
sudo certbot --nginx -d api.your-domain.com
```

## 🤖 TELEGRAM BOT DEPLOYMENT

### 1. Systemd Service

Create `/etc/systemd/system/casino-bot.service`:

```ini
[Unit]
Description=Casino Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/casino/bot
Environment="PATH=/var/www/casino/venv/bin"
ExecStart=/var/www/casino/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable casino-bot
sudo systemctl start casino-bot
sudo systemctl status casino-bot
```

## 🌐 FRONTEND DEPLOYMENT

### 1. Build React App

```bash
cd webapp
npm install
npm run build
```

### 2. Nginx Configuration for WebApp

```nginx
server {
    listen 80;
    server_name casino.your-domain.com;

    root /var/www/casino/webapp/build;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

Enable SSL:

```bash
sudo certbot --nginx -d casino.your-domain.com
```

## 📊 REDIS SETUP

```bash
# Install Redis
sudo apt install redis-server

# Configure
sudo nano /etc/redis/redis.conf
# Set: supervised systemd

# Start
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

## 🔒 SECURITY CHECKLIST

- [ ] Change all default passwords
- [ ] Enable HTTPS (SSL certificates)
- [ ] Set up firewall (UFW)
- [ ] Configure rate limiting
- [ ] Enable database backups
- [ ] Set up monitoring (logs)
- [ ] Secure environment variables
- [ ] Enable CORS properly
- [ ] Set up fail2ban
- [ ] Regular security updates

### Firewall Setup

```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

## 📈 MONITORING

### 1. Logging Configuration

```python
# backend/app/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger("casino_platform")
    logger.setLevel(logging.INFO)
    
    handler = RotatingFileHandler(
        'logs/casino.log',
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

### 2. Health Check Endpoint

Already included in FastAPI backend:

```
GET /health
```

### 3. Database Backup

```bash
# Crontab for daily backups
0 2 * * * pg_dump casino_db > /backups/casino_db_$(date +\%Y\%m\%d).sql
```

## 🧪 TESTING

### Backend Tests

```bash
cd backend
pytest tests/
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host=http://localhost:8000
```

## 📱 TELEGRAM BOT WEBHOOK (Alternative)

Instead of polling, you can use webhooks:

```python
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

async def on_startup(bot: Bot):
    await bot.set_webhook(f"https://your-domain.com/webhook/{BOT_TOKEN}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

app = web.Application()
webhook_requests_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
)
webhook_requests_handler.register(app, path=f"/webhook/{BOT_TOKEN}")
setup_application(app, dp, bot=bot)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
```

## 🎮 GAME BALANCE SETTINGS

Recommended RTP (Return to Player) settings:

```python
# config/game_settings.py

GAME_SETTINGS = {
    'aviator': {
        'min_bet': 1000,
        'max_bet': 1000000,
        'house_edge': 0.03,  # 3%
        'max_multiplier': 1000,
    },
    'mines': {
        'min_bet': 1000,
        'max_bet': 500000,
        'house_edge': 0.04,  # 4%
        'min_mines': 1,
        'max_mines': 24,
    },
    'apple_of_fortune': {
        'min_bet': 1000,
        'max_bet': 500000,
        'house_edge': 0.05,  # 5%
        'total_levels': 8,
    }
}
```

## 🔄 UPDATING THE PLATFORM

```bash
# Pull latest code
cd /var/www/casino
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart casino-api

# Bot
sudo systemctl restart casino-bot

# Frontend
cd ../webapp
npm install
npm run build
```

## 📞 ADMIN CONTACTS & SUPPORT

Set up admin notification system:

```python
# utils/admin_notify.py
async def notify_admins(bot: Bot, message: str, admin_ids: list):
    """Send notification to all admins"""
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, message)
        except Exception as e:
            logging.error(f"Failed to notify admin {admin_id}: {e}")
```

## 🎯 PERFORMANCE OPTIMIZATION

1. **Database Indexes**:
```sql
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_game_sessions_user_id ON game_sessions(user_id);
```

2. **Redis Caching**:
```python
from redis import asyncio as aioredis

redis = aioredis.from_url("redis://localhost")

# Cache user balance
await redis.setex(f"balance:{user_id}", 60, str(balance))
```

3. **Connection Pooling**:
```python
# Already configured in SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

## 🚨 TROUBLESHOOTING

### Bot not responding
```bash
sudo systemctl status casino-bot
sudo journalctl -u casino-bot -f
```

### API errors
```bash
sudo systemctl status casino-api
tail -f /var/www/casino/backend/logs/casino.log
```

### Database connection issues
```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

## ✅ PRODUCTION CHECKLIST

- [ ] All services running
- [ ] SSL certificates installed
- [ ] Database backups configured
- [ ] Monitoring enabled
- [ ] Admin accounts set up
- [ ] Bot commands working
- [ ] Web app accessible
- [ ] Payment system tested
- [ ] RNG verified
- [ ] Security measures in place
- [ ] Rate limiting active
- [ ] Error logging configured

---

## 📝 NEXT STEPS

1. Test all game mechanics thoroughly
2. Perform security audit
3. Load test with expected user traffic
4. Set up customer support system
5. Create user documentation
6. Prepare marketing materials

---

**IMPORTANT**: Always test in development before deploying to production!
