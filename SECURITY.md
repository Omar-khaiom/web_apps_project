# 🔐 Security Guide & Production Deployment

This document outlines security best practices and production deployment recommendations for the SmartRecipes web application.

## 🚨 **CRITICAL SECURITY FIXES NEEDED**

### 1. **Environment Variable Security**
```bash
# ❌ NEVER commit these files
rm .env  # Remove from git if accidentally committed
git rm --cached .env

# ✅ Use environment-specific configurations
cp .env.example .env.production
# Edit with production values
```

### 2. **Secret Key Generation**
```python
# Generate a proper secret key
import secrets
print(secrets.token_hex(32))
# Use this output in your .env file
```

### 3. **Database Security**
```bash
# Set proper file permissions
chmod 600 users.db
chmod 600 .env
chmod -R 700 logs/
```

## 🛡️ **Production Security Checklist**

### Environment Configuration
- [ ] Set `DEBUG = False` in production
- [ ] Use strong, unique `SECRET_KEY`
- [ ] Configure proper `SESSION_COOKIE_SECURE = True`
- [ ] Set up HTTPS with SSL certificates
- [ ] Use environment variables for all secrets
- [ ] Enable `CSRF` protection
- [ ] Configure secure headers

### Database Security
- [ ] Use production-grade database (PostgreSQL/MySQL)
- [ ] Enable database connection encryption
- [ ] Set up database user with minimal privileges
- [ ] Enable database audit logging
- [ ] Regular database backups
- [ ] Database connection pooling

### Authentication & Authorization
- [ ] Implement account lockout after failed attempts
- [ ] Add two-factor authentication (2FA)
- [ ] Implement password complexity requirements
- [ ] Add password reset functionality
- [ ] Session timeout configuration
- [ ] Secure session storage (Redis/Database)

### API Security
- [ ] Implement API key rotation
- [ ] Add request signing/validation
- [ ] Monitor API usage and costs
- [ ] Implement circuit breakers for external APIs
- [ ] Add API response caching

### Monitoring & Logging
- [ ] Centralized logging (ELK stack/Splunk)
- [ ] Security event monitoring
- [ ] Performance monitoring (APM)
- [ ] Error tracking (Sentry)
- [ ] Log rotation and retention policies

## 🚀 **Production Deployment Guide**

### 1. **Server Configuration**

#### Using Gunicorn + Nginx
```bash
# Install production dependencies
pip install gunicorn psycopg2-binary redis

# Create gunicorn configuration
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
EOF

# Run with Gunicorn
gunicorn -c gunicorn.conf.py app:app
```

#### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/your/cert.pem;
    ssl_certificate_key /path/to/your/key.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. **Docker Deployment** (Recommended)

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/smartrecipes
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: smartrecipes
      POSTGRES_USER: your_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

### 3. **Environment Configuration**

#### Production .env
```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-super-secret-production-key-here
DEBUG=False

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql://username:password@localhost/smartrecipes

# Redis for caching and sessions
REDIS_URL=redis://localhost:6379/0

# API Keys
SPOONACULAR_API_KEY=your-production-api-key

# Email Configuration
MAIL_SERVER=smtp.your-provider.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-app-specific-password

# Security
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
PERMANENT_SESSION_LIFETIME=3600

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
```

## 🔒 **Security Enhancements to Implement**

### 1. **Enhanced Password Policy**
```python
def validate_password_strength(password):
    """Enhanced password validation"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    checks = [
        (r'[A-Z]', "uppercase letter"),
        (r'[a-z]', "lowercase letter"),
        (r'[0-9]', "number"),
        (r'[!@#$%^&*(),.?":{}|<>]', "special character")
    ]
    
    for pattern, name in checks:
        if not re.search(pattern, password):
            return False, f"Password must contain at least one {name}"
    
    return True, "Password is strong"
```

### 2. **Rate Limiting Enhancement**
```python
# Add Redis-based rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per day", "20 per hour"],
    storage_uri="redis://localhost:6379",
    strategy="fixed-window-elastic-expiry"
)
```

### 3. **CSRF Protection**
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
```

### 4. **Content Security Policy**
```python
@app.after_request
def after_request(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' cdnjs.cloudflare.com;"
    )
    return response
```

## 📊 **Monitoring & Maintenance**

### 1. **Health Check Endpoint**
```python
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })
```

### 2. **Automated Backups**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump smartrecipes > "backup_${DATE}.sql"
aws s3 cp "backup_${DATE}.sql" s3://your-backup-bucket/
```

### 3. **Log Monitoring**
```python
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler

# Email alerts for critical errors
if not app.debug:
    mail_handler = SMTPHandler(
        mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        fromaddr=app.config['MAIL_USERNAME'],
        toaddrs=['admin@yourdomain.com'],
        subject='SmartRecipes Application Error'
    )
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)
```

## 🚨 **Security Incident Response**

### Immediate Actions
1. **Isolate** - Take affected systems offline
2. **Assess** - Determine scope of breach
3. **Contain** - Prevent further damage
4. **Notify** - Alert users and authorities if required
5. **Recover** - Restore from clean backups
6. **Review** - Conduct post-incident analysis

### Regular Security Tasks
- [ ] Weekly security updates
- [ ] Monthly penetration testing
- [ ] Quarterly security audits
- [ ] Annual disaster recovery testing
- [ ] Continuous vulnerability scanning

---

**Remember**: Security is an ongoing process, not a one-time setup. Regularly review and update your security measures.
