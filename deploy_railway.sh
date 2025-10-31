#!/bin/bash

# 🚀 Автоматический деплой на Railway
# Этот скрипт автоматизирует большую часть процесса

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         🚀 Railway Deployment Automation Script 🚀          ║"
echo "║                                                              ║"
echo "║              AI Development System v1.0                      ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Проверка наличия Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI не установлен!"
    echo "Установи: npm install -g @railway/cli"
    exit 1
fi

echo "✅ Railway CLI обнаружен"
echo ""

# Проверка авторизации
echo "📋 Шаг 1: Проверка авторизации..."
if ! railway whoami &> /dev/null; then
    echo "⚠️  Вы не авторизованы в Railway"
    echo "🔑 Запускаю railway login..."
    echo ""
    railway login
    echo ""
else
    echo "✅ Уже авторизован как: $(railway whoami)"
    echo ""
fi

# Проверка Procfile
echo "📋 Шаг 2: Проверка Procfile..."
if [ ! -f "Procfile" ]; then
    echo "⚠️  Procfile не найден, создаю..."
    echo "web: uvicorn api.server:app --host 0.0.0.0 --port \$PORT" > Procfile
    echo "✅ Procfile создан"
else
    echo "✅ Procfile найден"
fi
echo ""

# Инициализация проекта (если нужно)
echo "📋 Шаг 3: Инициализация проекта..."
if [ ! -f ".railway/config.json" ] && [ ! -f "railway.json" ]; then
    echo "⚠️  Проект не инициализирован"
    echo "🔧 Запускаю railway init..."
    echo ""
    echo "ВАЖНО: Выбери 'Create a new project' и придумай название!"
    echo ""
    railway init
    echo ""
else
    echo "✅ Проект уже инициализирован"
    echo ""
fi

# Настройка переменных окружения
echo "📋 Шаг 4: Настройка переменных окружения..."
echo ""
echo "Устанавливаю переменные из .env файла..."

# Читаем SECRET_KEY из .env
if [ -f ".env" ]; then
    SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d '=' -f2)
    GEMINI_KEY=$(grep "^GEMINI_API_KEY=" .env | cut -d '=' -f2)
    OPENROUTER_KEY=$(grep "^OPENROUTER_API_KEY=" .env | cut -d '=' -f2)
    ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" .env | cut -d '=' -f2)
    OPENAI_KEY=$(grep "^OPENAI_API_KEY=" .env | cut -d '=' -f2)

    if [ ! -z "$SECRET_KEY" ]; then
        echo "Setting SECRET_KEY..."
        railway variables set SECRET_KEY="$SECRET_KEY"
    fi

    if [ ! -z "$GEMINI_KEY" ]; then
        echo "Setting GEMINI_API_KEY..."
        railway variables set GEMINI_API_KEY="$GEMINI_KEY"
    fi

    if [ ! -z "$OPENROUTER_KEY" ]; then
        echo "Setting OPENROUTER_API_KEY..."
        railway variables set OPENROUTER_API_KEY="$OPENROUTER_KEY"
    fi

    if [ ! -z "$ANTHROPIC_KEY" ]; then
        echo "Setting ANTHROPIC_API_KEY..."
        railway variables set ANTHROPIC_API_KEY="$ANTHROPIC_KEY"
    fi

    if [ ! -z "$OPENAI_KEY" ]; then
        echo "Setting OPENAI_API_KEY..."
        railway variables set OPENAI_API_KEY="$OPENAI_KEY"
    fi
fi

# Дополнительные переменные
echo "Setting JWT_EXPIRATION_HOURS..."
railway variables set JWT_EXPIRATION_HOURS="24"

echo "Setting DATABASE_PATH..."
railway variables set DATABASE_PATH="./data/history.db"

echo ""
echo "✅ Переменные окружения настроены"
echo ""

# Проверка переменных
echo "📋 Проверка установленных переменных..."
railway variables | head -20
echo ""

# Деплой
echo "📋 Шаг 5: Деплой на Railway..."
echo ""
echo "🚀 Запускаю deployment..."
echo ""

railway up

echo ""
echo "✅ Deployment завершен!"
echo ""

# Получение URL
echo "📋 Шаг 6: Получение production URL..."
echo ""

DOMAIN=$(railway domain 2>&1 | grep -o 'https://[^ ]*' || echo "")

if [ -z "$DOMAIN" ]; then
    echo "⚠️  Домен еще не создан. Создаю..."
    railway domain
    sleep 2
    DOMAIN=$(railway domain 2>&1 | grep -o 'https://[^ ]*' || echo "")
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "🎉 DEPLOYMENT УСПЕШЕН! 🎉"
echo ""
if [ ! -z "$DOMAIN" ]; then
    echo "🌐 Production URL: $DOMAIN"
    echo ""
    echo "📊 Тестовые команды:"
    echo ""
    echo "  # Health check:"
    echo "  curl $DOMAIN/api/health"
    echo ""
    echo "  # API Docs:"
    echo "  open $DOMAIN/docs"
    echo ""
    echo "  # Test registration:"
    echo "  curl -X POST $DOMAIN/api/auth/register \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"email\":\"test@prod.com\",\"password\":\"testpass123\"}'"
else
    echo "🌐 Получи URL командой: railway domain"
fi
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📚 Полезные команды:"
echo ""
echo "  railway logs          # Просмотр логов"
echo "  railway status        # Статус deployment"
echo "  railway open          # Открыть в браузере"
echo "  railway variables     # Список переменных"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✨ Твоя AI Development System теперь в production! ✨"
echo ""
