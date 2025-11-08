#!/bin/bash
# Скрипт для обновления Railway переменных через правильный синтаксис

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

VERCEL_URL="https://aiassistant-omega.vercel.app"

echo -e "${GREEN}🚀 Обновление Railway переменных${NC}\n"

# Проверка Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI не установлен${NC}"
    exit 1
fi

# Проверка подключения
echo -e "${YELLOW}📋 Проверка подключения...${NC}"
STATUS=$(railway status 2>&1 || echo "")
echo "$STATUS"
echo ""

# Попытка обновить переменные
echo -e "${YELLOW}🔑 Обновление переменных...${NC}"

# Попытка 1: Без указания сервиса
echo "1. Обновление CORS_ORIGINS..."
if railway variables --set "CORS_ORIGINS=$VERCEL_URL" 2>&1 | grep -q "No service linked"; then
    echo -e "${YELLOW}⚠️  Сервис не привязан. Используйте Dashboard или привяжите сервис${NC}"
    echo ""
    echo "Вариант 1: Через Railway Dashboard (Рекомендуется)"
    echo "  1. Откройте: https://railway.app/dashboard"
    echo "  2. Выберите проект 'AIAssistant'"
    echo "  3. Перейдите в Variables"
    echo "  4. Добавьте/обновите:"
    echo "     CORS_ORIGINS=$VERCEL_URL"
    echo "     FRONTEND_URL=$VERCEL_URL"
    echo ""
    echo "Вариант 2: Привязать сервис через CLI"
    echo "  railway service"
    echo "  # Выберите нужный сервис"
    echo "  railway variables --set \"CORS_ORIGINS=$VERCEL_URL\""
    echo "  railway variables --set \"FRONTEND_URL=$VERCEL_URL\""
else
    echo -e "${GREEN}✅ CORS_ORIGINS обновлено${NC}"
fi

echo ""
echo "2. Обновление FRONTEND_URL..."
if railway variables --set "FRONTEND_URL=$VERCEL_URL" 2>&1 | grep -q "No service linked"; then
    echo -e "${YELLOW}⚠️  См. инструкции выше${NC}"
else
    echo -e "${GREEN}✅ FRONTEND_URL обновлено${NC}"
fi

echo ""
echo -e "${GREEN}✅ Обновление завершено${NC}"
echo ""
echo "Обновленные переменные:"
echo "  CORS_ORIGINS=$VERCEL_URL"
echo "  FRONTEND_URL=$VERCEL_URL"
echo ""
echo "Проверьте в Railway Dashboard:"
echo "  https://railway.app/dashboard"







