#!/bin/bash
# Скрипт для проверки и настройки Vercel

set -e

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

RAILWAY_URL="https://aiassistant-production-7a4d.up.railway.app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WEB_UI_DIR="$PROJECT_ROOT/web-ui"

echo -e "${GREEN}🌐 Проверка и настройка Vercel${NC}\n"

# Проверка Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI не установлен${NC}"
    echo "Установите: npm install -g vercel"
    exit 1
fi

# Проверка авторизации
echo -e "${YELLOW}🔐 Проверка авторизации...${NC}"
USER=$(vercel whoami 2>&1 | tail -1 || echo "")
if [ -n "$USER" ] && [ "$USER" != "Vercel CLI" ]; then
    echo -e "${GREEN}✅ Залогинен как: $USER${NC}"
else
    echo -e "${RED}❌ Не залогинен в Vercel${NC}"
    echo "Выполните: vercel login"
    exit 1
fi

echo ""

# Переход в директорию web-ui
if [ ! -d "$WEB_UI_DIR" ]; then
    echo -e "${RED}❌ Директория web-ui не найдена в $PROJECT_ROOT${NC}"
    exit 1
fi

cd "$WEB_UI_DIR"

# Проверка проекта
echo -e "${YELLOW}📋 Информация о проекте:${NC}"
if [ -f ".vercel/project.json" ]; then
    PROJECT_ID=$(cat .vercel/project.json | grep -o '"projectId":"[^"]*' | cut -d'"' -f4)
    PROJECT_NAME=$(cat .vercel/project.json | grep -o '"projectName":"[^"]*' | cut -d'"' -f4)
    
    echo "  Project ID: $PROJECT_ID"
    echo "  Project Name: $PROJECT_NAME"
else
    echo -e "${YELLOW}⚠️  Проект не привязан${NC}"
    echo "Выполните: cd web-ui && vercel link"
fi

echo ""

# Проверка переменных окружения
echo -e "${YELLOW}🔑 Проверка переменных окружения:${NC}"
ENV_VARS=$(vercel env ls 2>&1 || echo "")

if echo "$ENV_VARS" | grep -q "NEXT_PUBLIC_API_URL"; then
    echo -e "${GREEN}✅ NEXT_PUBLIC_API_URL найдена${NC}"
    echo "$ENV_VARS" | grep "NEXT_PUBLIC_API_URL" || true
else
    echo -e "${RED}❌ NEXT_PUBLIC_API_URL не найдена${NC}"
    echo ""
    echo -e "${YELLOW}📝 Инструкции по добавлению:${NC}"
    echo ""
    echo "Вариант 1: Через Dashboard (Рекомендуется)"
    echo "  1. Откройте: https://vercel.com/dashboard"
    echo "  2. Выберите проект 'web-ui'"
    echo "  3. Settings → Environment Variables"
    echo "  4. Добавьте переменную:"
    echo "     Name: NEXT_PUBLIC_API_URL"
    echo "     Value: $RAILWAY_URL"
    echo "     Environment: Production (и Preview, Development при необходимости)"
    echo ""
    echo "Вариант 2: Через CLI"
    echo "  cd web-ui"
    echo "  vercel env add NEXT_PUBLIC_API_URL production"
    echo "  # При запросе введите: $RAILWAY_URL"
    echo ""
fi

echo ""

# Получение URL проекта
echo -e "${YELLOW}🌐 Проверка деплойментов...${NC}"
DEPLOYMENTS=$(vercel ls --yes 2>&1 || echo "")
VERCEL_URL=""

if echo "$DEPLOYMENTS" | grep -q "https://"; then
    VERCEL_URL=$(echo "$DEPLOYMENTS" | grep -o "https://[^ ]*\.vercel\.app" | head -1)
    if [ -n "$VERCEL_URL" ]; then
        echo -e "${GREEN}✅ Найден URL: $VERCEL_URL${NC}"
    fi
fi

if [ -z "$VERCEL_URL" ]; then
    echo -e "${YELLOW}⚠️  Деплойменты не найдены${NC}"
    echo ""
    echo "Проект может быть не задеплоен. Для деплоя:"
    echo "  cd web-ui"
    echo "  vercel --prod"
    echo ""
    echo "Или проверьте через Dashboard:"
    echo "  https://vercel.com/dashboard"
fi

echo ""

# Вывод финальных инструкций
echo -e "${BLUE}📝 Следующие шаги:${NC}\n"

if [ -z "$VERCEL_URL" ]; then
    echo "1. Получите Vercel URL:"
    echo "   - Задеплойте проект: cd web-ui && vercel --prod"
    echo "   - Или откройте: https://vercel.com/dashboard"
    echo ""
fi

echo "2. Добавьте переменную NEXT_PUBLIC_API_URL (если еще не добавлена):"
echo "   - Через Dashboard: https://vercel.com/dashboard → web-ui → Settings → Environment Variables"
echo "   - Значение: $RAILWAY_URL"
echo ""

if [ -n "$VERCEL_URL" ]; then
    echo "3. Обновите Railway переменные с Vercel URL:"
    echo "   ./scripts/update_railway_vars.sh"
    echo ""
    echo "   Или вручную:"
    echo "   railway variables set CORS_ORIGINS=\"$VERCEL_URL\""
    echo "   railway variables set FRONTEND_URL=\"$VERCEL_URL\""
    echo ""
fi

echo "4. Проверка конфигурации:"
echo "   ./scripts/check_production_config.sh"
echo ""

cd "$PROJECT_ROOT"

echo -e "${GREEN}✅ Проверка завершена${NC}"
