#!/bin/bash
# Скрипт для автоматического обновления переменных окружения в Railway

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

RAILWAY_URL="https://aiassistant-production-7a4d.up.railway.app"

echo -e "${GREEN}🚀 Обновление переменных окружения Railway${NC}\n"

# Проверка Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI не установлен${NC}"
    echo "Установите: npm install -g @railway/cli"
    exit 1
fi

# Получение Vercel URL
echo -e "${YELLOW}📡 Получение Vercel URL...${NC}"
VERCEL_URL=""

if command -v vercel &> /dev/null; then
    cd web-ui 2>/dev/null || true
    VERCEL_URL=$(vercel ls --json 2>/dev/null | jq -r '.[0].url' 2>/dev/null || echo "")
    cd .. 2>/dev/null || true
    
    if [ -n "$VERCEL_URL" ] && [ "$VERCEL_URL" != "null" ]; then
        echo -e "${GREEN}✅ Найден Vercel URL: $VERCEL_URL${NC}"
        # Добавляем https:// если его нет
        if [[ ! "$VERCEL_URL" =~ ^https?:// ]]; then
            VERCEL_URL="https://$VERCEL_URL"
        fi
    fi
fi

# Если Vercel URL не найден автоматически, запрашиваем у пользователя
if [ -z "$VERCEL_URL" ] || [ "$VERCEL_URL" = "null" ]; then
    echo -e "${YELLOW}⚠️  Vercel URL не найден автоматически${NC}"
    echo "Введите ваш Vercel URL (например: https://your-app.vercel.app):"
    read -r VERCEL_URL
    
    if [ -z "$VERCEL_URL" ]; then
        echo -e "${RED}❌ Vercel URL обязателен для настройки CORS${NC}"
        exit 1
    fi
    
    # Добавляем https:// если его нет
    if [[ ! "$VERCEL_URL" =~ ^https?:// ]]; then
        VERCEL_URL="https://$VERCEL_URL"
    fi
fi

echo ""
echo -e "${YELLOW}📋 Обновление переменных окружения...${NC}"
echo ""

# Обновление CORS_ORIGINS
echo "1. Обновление CORS_ORIGINS..."
if railway variables set "CORS_ORIGINS=$VERCEL_URL" 2>/dev/null; then
    echo -e "${GREEN}✅ CORS_ORIGINS обновлен${NC}"
else
    echo -e "${RED}❌ Ошибка при обновлении CORS_ORIGINS${NC}"
    echo "Попробуйте вручную: railway variables set CORS_ORIGINS=\"$VERCEL_URL\""
fi

# Обновление FRONTEND_URL
echo "2. Обновление FRONTEND_URL..."
if railway variables set "FRONTEND_URL=$VERCEL_URL" 2>/dev/null; then
    echo -e "${GREEN}✅ FRONTEND_URL обновлен${NC}"
else
    echo -e "${RED}❌ Ошибка при обновлении FRONTEND_URL${NC}"
    echo "Попробуйте вручную: railway variables set FRONTEND_URL=\"$VERCEL_URL\""
fi

# Проверка ENVIRONMENT
echo "3. Проверка ENVIRONMENT..."
ENV_VALUE=$(railway variables 2>/dev/null | grep "^ENVIRONMENT" | awk '{print $2}' || echo "")
if [ "$ENV_VALUE" != "production" ]; then
    echo "   Установка ENVIRONMENT=production..."
    if railway variables set "ENVIRONMENT=production" 2>/dev/null; then
        echo -e "${GREEN}✅ ENVIRONMENT установлен в production${NC}"
    else
        echo -e "${YELLOW}⚠️  Не удалось установить ENVIRONMENT автоматически${NC}"
    fi
else
    echo -e "${GREEN}✅ ENVIRONMENT уже установлен в production${NC}"
fi

echo ""
echo -e "${GREEN}✅ Обновление завершено!${NC}"
echo ""
echo "Обновленные переменные:"
echo "  CORS_ORIGINS=$VERCEL_URL"
echo "  FRONTEND_URL=$VERCEL_URL"
echo "  ENVIRONMENT=production"
echo ""
echo -e "${YELLOW}⚠️  Важно:${NC}"
echo "1. Railway автоматически перезапустит сервис после обновления переменных"
echo "2. Проверьте что все работает:"
echo "   curl $RAILWAY_URL/api/health"
echo ""
echo "3. Обновите OAuth callback URLs в провайдерах:"
echo "   - Google: $VERCEL_URL/api/auth/callback/google"
echo "   - GitHub: $VERCEL_URL/api/auth/callback/github"
echo "   - Microsoft: $VERCEL_URL/api/auth/callback/microsoft"
echo ""







