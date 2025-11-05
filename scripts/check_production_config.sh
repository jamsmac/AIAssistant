#!/bin/bash
# Скрипт для проверки и обновления переменных окружения для production

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# URLs
RAILWAY_URL="https://aiassistant-production-7a4d.up.railway.app"
VERCEL_URL=""  # Нужно получить из Vercel

echo -e "${GREEN}🔍 Проверка конфигурации Production${NC}\n"

# Функция для проверки переменных Railway
check_railway_vars() {
    echo -e "${YELLOW}📋 Проверка переменных Railway...${NC}"
    
    if command -v railway &> /dev/null; then
        echo "Railway CLI найден"
        railway variables list 2>/dev/null || echo "⚠️  Не удалось получить список переменных. Проверьте railway login"
    else
        echo "⚠️  Railway CLI не установлен. Установите: npm install -g @railway/cli"
    fi
    
    echo ""
}

# Функция для получения Vercel URL
get_vercel_url() {
    echo -e "${YELLOW}🌐 Получение Vercel URL...${NC}"
    
    if command -v vercel &> /dev/null; then
        cd web-ui 2>/dev/null || return
        VERCEL_URL=$(vercel ls --json 2>/dev/null | jq -r '.[0].url' 2>/dev/null || echo "")
        if [ -n "$VERCEL_URL" ]; then
            echo "✅ Vercel URL найден: $VERCEL_URL"
            cd ..
        else
            echo "⚠️  Не удалось получить Vercel URL автоматически"
            echo "   Проверьте вручную: https://vercel.com/dashboard"
        fi
    else
        echo "⚠️  Vercel CLI не установлен. Установите: npm install -g vercel"
    fi
    
    echo ""
}

# Функция для проверки health check
check_health() {
    echo -e "${YELLOW}🏥 Проверка health check...${NC}"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/api/health" || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ API работает правильно${NC}"
        curl -s "$RAILWAY_URL/api/health" | jq '.' 2>/dev/null || curl -s "$RAILWAY_URL/api/health"
    else
        echo -e "${RED}❌ API не отвечает (HTTP $response)${NC}"
    fi
    
    echo ""
}

# Функция для проверки CORS
check_cors() {
    echo -e "${YELLOW}🔒 Проверка CORS...${NC}"
    
    if [ -z "$VERCEL_URL" ]; then
        echo "⚠️  Vercel URL не найден. Пропускаем проверку CORS"
        return
    fi
    
    headers=$(curl -s -I -H "Origin: $VERCEL_URL" \
        -H "Access-Control-Request-Method: GET" \
        -X OPTIONS \
        "$RAILWAY_URL/api/health" 2>/dev/null)
    
    if echo "$headers" | grep -q "Access-Control-Allow-Origin"; then
        echo -e "${GREEN}✅ CORS настроен правильно${NC}"
        echo "$headers" | grep -i "access-control"
    else
        echo -e "${RED}❌ CORS не настроен для $VERCEL_URL${NC}"
        echo ""
        echo "Добавьте в Railway переменные:"
        echo "  CORS_ORIGINS=$VERCEL_URL"
        echo "  FRONTEND_URL=$VERCEL_URL"
    fi
    
    echo ""
}

# Функция для вывода инструкций по обновлению переменных
show_update_instructions() {
    echo -e "${YELLOW}📝 Инструкции по обновлению переменных окружения:${NC}\n"
    
    echo "Railway (Backend):"
    echo "  1. Откройте: https://railway.app/dashboard"
    echo "  2. Выберите проект 'AI Assistant Platform'"
    echo "  3. Перейдите в Variables"
    echo "  4. Добавьте/обновите следующие переменные:"
    echo ""
    
    if [ -n "$VERCEL_URL" ]; then
        echo "     CORS_ORIGINS=$VERCEL_URL"
        echo "     FRONTEND_URL=$VERCEL_URL"
    else
        echo "     CORS_ORIGINS=https://your-app.vercel.app"
        echo "     FRONTEND_URL=https://your-app.vercel.app"
    fi
    
    echo "     ENVIRONMENT=production"
    echo ""
    
    echo "Vercel (Frontend):"
    echo "  1. Откройте: https://vercel.com/dashboard"
    echo "  2. Выберите ваш проект"
    echo "  3. Settings → Environment Variables"
    echo "  4. Убедитесь что установлено:"
    echo ""
    echo "     NEXT_PUBLIC_API_URL=$RAILWAY_URL"
    echo ""
    
    echo "Или используйте CLI:"
    echo ""
    
    if [ -n "$VERCEL_URL" ]; then
        echo "Railway:"
        echo "  railway variables set CORS_ORIGINS=\"$VERCEL_URL\""
        echo "  railway variables set FRONTEND_URL=\"$VERCEL_URL\""
        echo "  railway variables set ENVIRONMENT=production"
        echo ""
    fi
    
    echo "Vercel:"
    echo "  cd web-ui"
    echo "  vercel env add NEXT_PUBLIC_API_URL production"
    echo "  # Введите: $RAILWAY_URL"
    echo ""
}

# Функция для проверки API version headers
check_api_headers() {
    echo -e "${YELLOW}📡 Проверка API headers...${NC}"
    
    headers=$(curl -s -I "$RAILWAY_URL/api/health" 2>/dev/null)
    
    if echo "$headers" | grep -q "X-API-Version"; then
        echo -e "${GREEN}✅ API Version headers присутствуют${NC}"
        echo "$headers" | grep -i "x-api"
    else
        echo -e "${RED}❌ API Version headers отсутствуют${NC}"
    fi
    
    echo ""
}

# Основная логика
main() {
    echo "Railway URL: $RAILWAY_URL"
    get_vercel_url
    
    check_railway_vars
    check_health
    check_api_headers
    
    if [ -n "$VERCEL_URL" ]; then
        check_cors
    fi
    
    show_update_instructions
    
    echo -e "${GREEN}✅ Проверка завершена${NC}"
}

# Запуск
main


