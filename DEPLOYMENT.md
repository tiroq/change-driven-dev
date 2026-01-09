# Deployment Guide

Production deployment instructions for Change-Driven Development.

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.11+
- Node.js 18+
- Nginx (for reverse proxy)
- Git
- Domain name (optional, for HTTPS)

## Architecture

```
┌─────────────┐
│   Nginx     │  :80/:443 (reverse proxy)
└──────┬──────┘
       │
       ├─────────────────┬──────────────────┐
       │                 │                  │
┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
│  Frontend   │   │   Backend   │   │  WebSocket  │
│  (Static)   │   │  (FastAPI)  │   │   (FastAPI) │
│   :5173     │   │    :8000    │   │  ws://8000  │
└─────────────┘   └──────┬──────┘   └─────────────┘
                         │
                  ┌──────▼──────┐
                  │   SQLite    │
                  │  (per proj) │
                  └─────────────┘
```

## Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3.11 python3-pip nodejs npm nginx
```

### 2. Create User

```bash
sudo useradd -m -s /bin/bash cdd
sudo usermod -aG sudo cdd
sudo su - cdd
```

### 3. Clone Repository

```bash
cd ~
git clone <repository-url> change-driven-dev
cd change-driven-dev
```

## Backend Deployment

### 1. Install Dependencies

```bash
cd ~/change-driven-dev/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### 2. Configure Environment

Create `.env` file:
```bash
cat > .env <<EOF
# Application
APP_ENV=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://yourdomain.com

# Database
DATA_DIR=/var/lib/cdd/data
ARTIFACTS_DIR=/var/lib/cdd/artifacts

# Security
SECRET_KEY=$(openssl rand -hex 32)
EOF
```

### 3. Create Data Directories

```bash
sudo mkdir -p /var/lib/cdd/{data,artifacts}
sudo chown -R cdd:cdd /var/lib/cdd
```

### 4. Create Systemd Service

```bash
sudo tee /etc/systemd/system/cdd-backend.service > /dev/null <<EOF
[Unit]
Description=Change-Driven Development Backend
After=network.target

[Service]
Type=notify
User=cdd
Group=cdd
WorkingDirectory=/home/cdd/change-driven-dev/backend
Environment="PATH=/home/cdd/change-driven-dev/backend/venv/bin"
ExecStart=/home/cdd/change-driven-dev/backend/venv/bin/gunicorn \
    app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --access-logfile /var/log/cdd/access.log \
    --error-logfile /var/log/cdd/error.log \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 5. Create Log Directory

```bash
sudo mkdir -p /var/log/cdd
sudo chown -R cdd:cdd /var/log/cdd
```

### 6. Start Backend Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable cdd-backend
sudo systemctl start cdd-backend
sudo systemctl status cdd-backend
```

## Frontend Deployment

### 1. Build Frontend

```bash
cd ~/change-driven-dev/frontend
npm install
npm run build
```

### 2. Configure Production API

Edit `vite.config.js`:
```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  },
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify('https://yourdomain.com/api'),
    'import.meta.env.VITE_WS_URL': JSON.stringify('wss://yourdomain.com/ws')
  }
})
```

Rebuild:
```bash
npm run build
```

### 3. Copy to Nginx

```bash
sudo mkdir -p /var/www/cdd
sudo cp -r dist/* /var/www/cdd/
sudo chown -R www-data:www-data /var/www/cdd
```

## Nginx Configuration

### 1. Create Nginx Config

```bash
sudo tee /etc/nginx/sites-available/cdd > /dev/null <<'EOF'
# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        root /var/www/cdd;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
EOF
```

### 2. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/cdd /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
sudo systemctl reload nginx
```

Auto-renewal:
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## Firewall

```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

## Monitoring

### 1. Log Rotation

```bash
sudo tee /etc/logrotate.d/cdd > /dev/null <<EOF
/var/log/cdd/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 cdd cdd
    sharedscripts
    postrotate
        systemctl reload cdd-backend
    endscript
}
EOF
```

### 2. Health Check Script

```bash
cat > ~/check-health.sh <<'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "Health check failed: HTTP $RESPONSE"
    systemctl restart cdd-backend
fi
EOF

chmod +x ~/check-health.sh
```

Add to crontab:
```bash
crontab -e
# Add:
*/5 * * * * /home/cdd/check-health.sh
```

## Backup

### 1. Database Backup Script

```bash
cat > ~/backup-databases.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/cdd"
DATA_DIR="/var/lib/cdd/data"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/databases_$DATE.tar.gz $DATA_DIR/*.db
find $BACKUP_DIR -name "databases_*.tar.gz" -mtime +30 -delete
EOF

chmod +x ~/backup-databases.sh
```

Add to crontab:
```bash
crontab -e
# Add:
0 2 * * * /home/cdd/backup-databases.sh
```

## Updates

### Backend Update

```bash
cd ~/change-driven-dev
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart cdd-backend
```

### Frontend Update

```bash
cd ~/change-driven-dev/frontend
git pull
npm install
npm run build
sudo cp -r dist/* /var/www/cdd/
sudo systemctl reload nginx
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
sudo journalctl -u cdd-backend -n 50
tail -f /var/log/cdd/error.log

# Check port
sudo netstat -tulpn | grep 8000

# Test manually
cd ~/change-driven-dev/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Database Issues

```bash
# Check permissions
ls -la /var/lib/cdd/data/

# Fix permissions
sudo chown -R cdd:cdd /var/lib/cdd/

# Check disk space
df -h /var/lib/cdd
```

### WebSocket Not Working

```bash
# Check Nginx WebSocket config
sudo nginx -t

# Test WebSocket
wscat -c ws://localhost:8000/ws/1

# Check firewall
sudo ufw status
```

## Performance Tuning

### Gunicorn Workers

Adjust workers based on CPU cores:
```bash
# Rule: (2 x CPU cores) + 1
workers = (2 x $(nproc)) + 1
```

Edit `/etc/systemd/system/cdd-backend.service`:
```
ExecStart=... --workers 9  # For 4 cores
```

### Nginx Caching

Add to Nginx config:
```nginx
# Cache static assets
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Security Checklist

- ✅ Use HTTPS with valid SSL certificate
- ✅ Firewall configured (only 22, 80, 443 open)
- ✅ Backend runs as non-root user
- ✅ Environment variables for secrets
- ✅ Regular backups configured
- ✅ Log rotation enabled
- ✅ Fail2ban for SSH (optional)
- ✅ Keep system and dependencies updated

## Production Environment Variables

```bash
# /home/cdd/change-driven-dev/backend/.env
APP_ENV=production
LOG_LEVEL=INFO
DATA_DIR=/var/lib/cdd/data
ARTIFACTS_DIR=/var/lib/cdd/artifacts
SECRET_KEY=<generated-secret>
CORS_ORIGINS=https://yourdomain.com
MAX_WORKERS=4
DB_POOL_SIZE=20
```

## Scaling

For high load:
1. Use PostgreSQL instead of SQLite
2. Add load balancer (HAProxy, Nginx)
3. Separate backend workers (multiple servers)
4. Use Redis for session/cache
5. CDN for static assets
6. Database replication

## Support

For deployment issues, check:
- Logs: `/var/log/cdd/`
- Service status: `systemctl status cdd-backend`
- Nginx errors: `/var/log/nginx/error.log`
- System resources: `htop`, `df -h`
