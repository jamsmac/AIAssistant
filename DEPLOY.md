# 🚀 Деплой на Production

## Вариант 1: Railway.app (Рекомендуется - Бесплатно)

### Шаг 1: Установка Railway CLI
```bash
npm install -g @railway/cli
railway login
```

### Шаг 2: Инициализация проекта
```bash
cd ~/autopilot-core
railway init
# Выбери: Create new project
```

### Шаг 3: Настройка переменных окружения
```bash
# Скопируй SECRET_KEY из .env
railway variables set SECRET_KEY="Zm5Y8QxE9vKL3wRt6DpN2hJ4Gc7Ua0Sf1Mb8Xe5Wq9Vr"

# Добавь API ключи
railway variables set GEMINI_API_KEY="твой-ключ"
railway variables set GROK_API_KEY="твой-ключ"
railway variables set OPENROUTER_API_KEY="твой-ключ"
railway variables set ANTHROPIC_API_KEY="твой-ключ"
railway variables set OPENAI_API_KEY="твой-ключ"
```

### Шаг 4: Создай Procfile
```bash
echo "web: uvicorn api.server:app --host 0.0.0.0 --port \$PORT" > Procfile
```

### Шаг 5: Деплой
```bash
railway up
```

### Шаг 6: Получи URL
```bash
railway domain
# Пример вывода: autopilot-production.up.railway.app
```

### Шаг 7: Тест
```bash
curl https://your-app.up.railway.app/api/health
```

---

## Вариант 2: DigitalOcean VPS ($5/мес)

### Шаг 1: Создай Droplet
1. Зайди на https://digitalocean.com
2. Create → Droplets
3. Выбери: Ubuntu 24.04 LTS, $5/month (1GB RAM)
4. Add SSH Key
5. Create Droplet

### Шаг 2: Подключись к серверу
```bash
ssh root@your-droplet-ip
```

### Шаг 3: Установи зависимости
```bash
apt update && apt upgrade -y
apt install -y python3.11 python3-pip git nginx certbot python3-certbot-nginx
```

### Шаг 4: Клонируй репозиторий
```bash
cd /opt
git clone https://github.com/yourusername/autopilot-core
cd autopilot-core
```

### Шаг 5: Настрой environment
```bash
cp .env.example .env
nano .env
# Добавь все API ключи и SECRET_KEY
```

### Шаг 6: Установи Python зависимости
```bash
pip3 install -r requirements.txt
```

### Шаг 7: Создай systemd service
```bash
cat > /etc/systemd/system/autopilot.service << 'SERVICE'
[Unit]
Description=Autopilot AI API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/autopilot-core
ExecStart=/usr/bin/python3 -m uvicorn api.server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

systemctl enable autopilot
systemctl start autopilot
systemctl status autopilot
```

### Шаг 8: Настрой Nginx
```bash
cat > /etc/nginx/sites-available/autopilot << 'NGINX'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -s /etc/nginx/sites-available/autopilot /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Шаг 9: Настрой SSL (Let's Encrypt)
```bash
certbot --nginx -d your-domain.com
```

### Шаг 10: Тест
```bash
curl https://your-domain.com/api/health
```

---

## Вариант 3: Docker (Универсальный)

### Шаг 1: Создай Dockerfile
```bash
cat > Dockerfile << 'DOCKER'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
DOCKER
```

### Шаг 2: Создай .dockerignore
```bash
cat > .dockerignore << 'IGNORE'
venv/
__pycache__/
*.pyc
.env
.git/
node_modules/
data/history.db
IGNORE
```

### Шаг 3: Build image
```bash
docker build -t autopilot-api .
```

### Шаг 4: Run container
```bash
docker run -d \
  --name autopilot \
  -p 8000:8000 \
  -e SECRET_KEY="your-secret-key" \
  -e GEMINI_API_KEY="your-key" \
  -e GROK_API_KEY="your-key" \
  -e OPENROUTER_API_KEY="your-key" \
  autopilot-api
```

### Шаг 5: Тест
```bash
curl http://localhost:8000/api/health
```

---

## 🔒 Финальный чеклист безопасности

### Перед деплоем убедись:
- [ ] SECRET_KEY уникальный и не в git
- [ ] Все API ключи в environment variables (не hardcoded)
- [ ] `.env` добавлен в `.gitignore`
- [ ] HTTPS настроен (для production)
- [ ] CORS настроен правильно (только нужные домены)
- [ ] Rate limiting включен
- [ ] Database backups настроены

---

## 📊 Мониторинг

### Логи Railway
```bash
railway logs
```

### Логи DigitalOcean
```bash
journalctl -u autopilot -f
```

### Логи Docker
```bash
docker logs -f autopilot
```

---

## 🆘 Troubleshooting

### Railway не запускается
- Проверь переменные: `railway variables`
- Проверь логи: `railway logs`
- Убедись что Procfile правильный

### VPS не отвечает
```bash
systemctl status autopilot
systemctl restart autopilot
journalctl -u autopilot -n 50
```

### Docker не работает
```bash
docker ps -a
docker logs autopilot
docker restart autopilot
```

---

## 💰 Стоимость

| Платформа | Цена | Лимиты |
|-----------|------|--------|
| Railway | $0 (500 часов/мес) | Бесплатно навсегда |
| DigitalOcean | $5/мес | 1GB RAM, 25GB SSD |
| Docker (local) | $0 | Только твой ПК |

---

## ✅ После деплоя

1. **Протестируй endpoints:**
```bash
curl https://your-app.com/api/health
curl https://your-app.com/api/models
```

2. **Создай первого пользователя:**
```bash
curl -X POST https://your-app.com/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@yourapp.com","password":"strong-password"}'
```

3. **Обнови frontend:**
В `web-ui/.env.local`:
```
NEXT_PUBLIC_API_URL=https://your-app.com
```

---

**Готово! Твоя AI система теперь в production! 🎉**
