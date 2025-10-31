#!/bin/bash

# 🚀 Автоматический деплой на Railway (Updated for Railway CLI v4.8+)

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         🚀 Railway Deployment (CLI v4.8+)                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Проект уже инициализирован!
echo "✅ Проект AIAssistant уже создан"
echo ""

# Настройка переменных окружения
echo "📋 Настройка переменных окружения..."
echo ""

# Читаем из .env
if [ -f ".env" ]; then
    SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d '=' -f2)
    GEMINI_KEY=$(grep "^GEMINI_API_KEY=" .env | cut -d '=' -f2)
    OPENROUTER_KEY=$(grep "^OPENROUTER_API_KEY=" .env | cut -d '=' -f2)
    ANTHROPIC_KEY=$(grep "^ANTHROPIC_API_KEY=" .env | cut -d '=' -f2)
    OPENAI_KEY=$(grep "^OPENAI_API_KEY=" .env | cut -d '=' -f2)

    echo "Устанавливаю переменные..."
    
    if [ ! -z "$SECRET_KEY" ]; then
        railway variables --set "SECRET_KEY=$SECRET_KEY"
    fi

    if [ ! -z "$GEMINI_KEY" ]; then
        railway variables --set "GEMINI_API_KEY=$GEMINI_KEY"
    fi

    if [ ! -z "$OPENROUTER_KEY" ]; then
        railway variables --set "OPENROUTER_API_KEY=$OPENROUTER_KEY"
    fi

    if [ ! -z "$ANTHROPIC_KEY" ]; then
        railway variables --set "ANTHROPIC_API_KEY=$ANTHROPIC_KEY"
    fi

    if [ ! -z "$OPENAI_KEY" ]; then
        railway variables --set "OPENAI_API_KEY=$OPENAI_KEY"
    fi
    
    railway variables --set "JWT_EXPIRATION_HOURS=24"
    railway variables --set "DATABASE_PATH=./data/history.db"
fi

echo ""
echo "✅ Переменные настроены"
echo ""

# Деплой
echo "📋 Запускаю deployment..."
echo ""

railway up

echo ""
echo "✅ Deployment завершен!"
echo ""

# Получение URL
echo "📋 Получение URL..."
railway domain 2>&1 || railway domain

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🎉 DEPLOYMENT УСПЕШЕН!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Полезные команды:"
echo ""
echo "  railway logs          # Просмотр логов"
echo "  railway status        # Статус deployment"
echo "  railway open          # Открыть в браузере"
echo "  railway variables     # Список переменных"
echo ""
echo "✨ Твоя AI система в production! ✨"
echo ""
